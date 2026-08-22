"""Persistent failure memory: store, cluster, and retrieve historical
failures, and compute a similarity-based risk signal for new inputs.

Migrates the concepts Phase 1 validated as reusable from
Introspective-Failure-Memory-Model (clustering, similarity/risk calculation,
historical failure retrieval -- PHASE1_AUDIT_REPORT.md section 7) while
fixing the two problems the audit flagged as blocking real use:

  1. "In-memory-only storage ... cannot support multiple workers/replicas"
     -- ``store()`` here persists through ``src.storage.EventRepository``,
     backed by a real database, and survives process restart (see
     ``tests/integration/test_persistence_pipeline.py``).
  2. "Fixed n_clusters=3 hardcoded everywhere ... duplicated across 5+
     files" -- clustering config lives in one place (this class's
     constructor), not re-declared per script.

The similarity/risk formula (Gaussian kernel over distance to cluster
centroids) is the one part of the source ``anticipatory_confidence.py`` that
*is* migrated here, because it requires no temporal/"activity" assumptions --
the recency-weighted "anticipatory" extension is deliberately NOT migrated
into this class; see ``src/failure_memory/anticipatory.py`` for why.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sklearn.cluster import KMeans

from src.schema.events import ReliabilityEvent
from src.storage.repository import EventRepository

from .embedding import FailureEmbedder


@dataclass(frozen=True)
class MemoryMatch:
    event: ReliabilityEvent
    distance: float
    similarity: float
    relevant: bool
    memory_version: int


class FailureMemory:
    """Lifecycle: INITIALIZATION -> LOAD PERSISTED MEMORY -> FIT -> SERVE ->
    (new failure -> MARK DIRTY) -> REBUILD -> VALIDATE -> ATOMICALLY PROMOTE
    -> SERVE.

    ``store()`` never mutates the currently-served (fitted) clustering
    state -- it only appends the new failure and marks the memory dirty.
    A separate ``rebuild()``/``maybe_rebuild()`` call (invoked explicitly by
    the caller, e.g. once per request in ``src/api/pipeline.py``) fits a
    *new* embedder/kmeans out-of-place and only promotes it into
    ``self.embedder``/``self._kmeans`` if fitting and validation both
    succeed. If a rebuild fails, the previously-promoted, still-valid model
    keeps serving ``risk()``/``retrieve()``/``cluster_of()`` -- the active
    model is never left silently unusable because of a bad rebuild. This is
    the fix for the bug where ``store()`` set ``_fitted = False`` with
    nothing to reliably set it back to ``True`` before the next request."""

    def __init__(
        self,
        feature_names: list[str],
        n_clusters: int = 3,
        sigma: float = 1.0,
        random_state: int = 42,
    ):
        self.feature_names = list(feature_names)
        self.embedder = FailureEmbedder(feature_names, n_components=2, random_state=random_state)
        self.n_clusters = n_clusters
        self.sigma = sigma
        self.random_state = random_state
        self._kmeans: KMeans | None = None
        self._fitted = False
        self._dirty = False
        self._version = 0
        self._last_rebuild_error: str | None = None
        self._failure_embeddings: np.ndarray | None = None
        self._failure_events: list[ReliabilityEvent] = []
        self._dirty = False
        self._memory_version = 0
        self._last_fit_event_count = 0
        self._last_fit_timestamp: datetime | None = None
        self._pending_update_count = 0

    # -- persistence -----------------------------------------------------
    def store(self, event: ReliabilityEvent, repository: EventRepository | None, *, persist: bool = True, rebuild: bool = True) -> None:
        """Ingest a failure and synchronously rebuild the learned view.

        ``persist`` defaults to true for backward compatibility, but the
        canonical runtime uses one authoritative repository write and passes
        ``persist=False``. A failure is never exposed as current learned state
        between ingestion and the configured rebuild: it is marked dirty first,
        then rebuilt synchronously by default.
        """
        if persist:
            if repository is None:
                raise ValueError("repository is required when persist=True")
            repository.save(event)
        if event.is_failure:
            self._failure_events.append(event)
            self._dirty = True
            self._pending_update_count += 1
            self._fitted = False
            if rebuild:
                self.rebuild()

    def ingest(self, event: ReliabilityEvent, *, rebuild: bool = True) -> None:
        """Ingest an already-persisted event without taking persistence ownership."""
        self.store(event, repository=None, persist=False, rebuild=rebuild)

    def rebuild(self) -> "FailureMemory":
        """Apply the deterministic synchronous update policy."""
        self.fit()
        return self

    def load_from_repository(
        self, repository: EventRepository, workload_id: str | None = None
    ) -> "FailureMemory":
        """Replace this memory's failure history with exactly what the
        repository holds (used to reconstruct a fresh instance, e.g. in
        tests simulating a new process). Caller must ``fit()``/``rebuild()``
        afterward -- this method only loads data, it does not fit."""
        self._failure_events = repository.get_failures(workload_id=workload_id)
        self._fitted = False
        self._dirty = bool(self._failure_events)
        self._pending_update_count = len(self._failure_events)
        return self

    def merge_from_repository(
        self, repository: EventRepository, workload_id: str | None = None
    ) -> int:
        """Additive reload: fetch persisted failures for ``workload_id`` and
        append any not already present in this instance (by ``event_id``),
        without discarding failures already loaded (e.g. from a synthetic
        training pass). Returns the number of newly-added events and marks
        the memory dirty if any were added. Used on API startup to
        reconstruct live memory state from persisted evidence -- see
        ``src/api/train.py``."""
        existing_ids = {e.event_id for e in self._failure_events}
        persisted = repository.get_failures(workload_id=workload_id)
        added = [e for e in persisted if e.event_id not in existing_ids]
        if added:
            self._failure_events.extend(added)
            self._dirty = True
        return len(added)

    # -- clustering --------------------------------------------------------
    def _fit_new_state(
        self, failure_events: list[ReliabilityEvent]
    ) -> tuple[FailureEmbedder, KMeans, np.ndarray]:
        """Fit a brand-new embedder/kmeans out-of-place. Raises on failure;
        never mutates ``self``."""
        embedder = FailureEmbedder(self.feature_names, n_components=2, random_state=self.random_state)
        contexts = [e.context for e in failure_events]
        confidences = [e.confidence for e in failure_events]
        embedder.fit(contexts)
        embeddings = embedder.embed_batch(contexts, confidences)
        k = min(self.n_clusters, len(failure_events))
        kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        kmeans.fit(embeddings)
        return embedder, kmeans, embeddings

    @staticmethod
    def _validate_new_state(kmeans: KMeans, embeddings: np.ndarray) -> None:
        """Minimal sanity checks before promoting a freshly-fit state.
        Raises ValueError if the fit is unusable."""
        if kmeans.cluster_centers_.shape[0] < 1:
            raise ValueError("rebuild produced zero cluster centers")
        if not np.all(np.isfinite(embeddings)):
            raise ValueError("rebuild produced non-finite embeddings")
        if not np.all(np.isfinite(kmeans.cluster_centers_)):
            raise ValueError("rebuild produced non-finite cluster centers")

    def rebuild(self) -> bool:
        """Fit a new clustering state from the current ``_failure_events``
        and, only if fitting and validation both succeed, atomically
        promote it to be the active (served) state. On failure, the
        previously-promoted state (if any) is left untouched and still
        serves ``risk()``/``retrieve()``/``cluster_of()`` -- the memory is
        marked dirty so a later rebuild can retry. Returns True iff the
        active state was promoted."""
        if not self._failure_events:
            self._dirty = False
            return False
        try:
            embedder, kmeans, embeddings = self._fit_new_state(self._failure_events)
            self._validate_new_state(kmeans, embeddings)
        except Exception as exc:  # noqa: BLE001 -- deliberately broad: any
            # fit/validation failure must fall back to "keep serving the
            # previous valid model," not crash the caller.
            self._last_rebuild_error = str(exc)
            return False

        # Atomic promotion: only reached after a fully successful fit+validate.
        self.embedder = embedder
        self._kmeans = kmeans
        self._failure_embeddings = embeddings
        self._fitted = True
        self._dirty = False
        self._version += 1
        self._last_rebuild_error = None
        return True

    def maybe_rebuild(self) -> bool:
        """Rebuild only if the memory is dirty (new failures since the last
        promoted state). No-op, returns False, if already up to date."""
        if not self._dirty:
            return False
        return self.rebuild()

    def fit(self) -> "FailureMemory":
        """Synchronous, unconditional fit -- used for initial/offline
        training (e.g. ``src/pipeline_builder.py``'s synthetic logging pass)
        where there is no previous state to protect. For the live,
        request-serving path where a bad rebuild must not destroy a good
        previous state, use ``rebuild()``/``maybe_rebuild()`` instead."""
        if not self._failure_events:
            self._fitted = False
            self._dirty = False
            return self
        embedder, kmeans, embeddings = self._fit_new_state(self._failure_events)
        self._validate_new_state(kmeans, embeddings)
        self.embedder = embedder
        self._kmeans = kmeans
        self._failure_embeddings = embeddings
        self._fitted = True
        self._dirty = False
        self._version += 1
        self._memory_version = self._version
        self._last_rebuild_error = None
        self._last_fit_event_count = len(self._failure_events)
        self._last_fit_timestamp = datetime.now(timezone.utc)
        self._pending_update_count = 0
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted and not self._dirty

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def memory_version(self) -> int:
        return self._memory_version

    @property
    def last_fit_event_count(self) -> int:
        return self._last_fit_event_count

    @property
    def last_fit_timestamp(self) -> datetime | None:
        return self._last_fit_timestamp

    @property
    def pending_update_count(self) -> int:
        return self._pending_update_count

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def n_failures(self) -> int:
        return len(self._failure_events)

    @property
    def failure_events(self) -> tuple[ReliabilityEvent, ...]:
        """Read-only view used by controlled, explicitly seeded experiments."""
        return tuple(self._failure_events)

    def seed_events(self, events: list[ReliabilityEvent]) -> "FailureMemory":
        """Load a declared training/experience set and rebuild it.

        This method is intentionally separate from runtime ingestion so an
        experiment can make the control-versus-learned boundary explicit.
        """
        self._failure_events = list(events)
        self._dirty = bool(self._failure_events)
        self._fitted = False
        self._pending_update_count = len(self._failure_events)
        return self.rebuild()
    def status(self) -> dict:
        """Observable memory state -- see docs/PHASE... memory status
        requirements. Every field here is read directly off live state,
        never fabricated."""
        return {
            "fitted": self._fitted,
            "dirty": self._dirty,
            "n_failure_events": len(self._failure_events),
            "version": self._version,
            "n_clusters_configured": self.n_clusters,
            "last_rebuild_error": self._last_rebuild_error,
        }

    # -- query -------------------------------------------------------------
    def risk(self, context: dict[str, float], confidence: float) -> float:
        """Similarity-based risk in [0, 1]: how close is this input to a
        historically observed failure cluster? 0.0 if failure memory has no
        data yet (honest "no signal" rather than a fabricated value -- see
        PHASE1_AUDIT_REPORT.md section 2.11 on not fabricating metrics)."""
        if not self._fitted or self._kmeans is None:
            return 0.0
        emb = self.embedder.embed(context, confidence)
        centroids = self._kmeans.cluster_centers_
        d2 = np.sum((centroids - emb) ** 2, axis=1)
        similarities = np.exp(-d2 / (self.sigma**2))
        return float(np.clip(np.max(similarities), 0.0, 1.0))

    def retrieve_matches(
        self, context: dict[str, float], confidence: float, k: int = 5, min_similarity: float = 0.5
    ) -> list[MemoryMatch]:
        """Return scored historical matches with explicit relevance semantics."""
        if not self._fitted or self._failure_embeddings is None or not self._failure_events:
            return []
        emb = self.embedder.embed(context, confidence)
        d2 = np.sum((self._failure_embeddings - emb) ** 2, axis=1)
        order = np.argsort(d2)[:k]
        return [
            MemoryMatch(
                event=self._failure_events[i],
                distance=float(d2[i]),
                similarity=float(np.exp(-d2[i] / (self.sigma**2))),
                relevant=bool(np.exp(-d2[i] / (self.sigma**2)) >= min_similarity),
                memory_version=self._memory_version,
            )
            for i in order
        ]

    def retrieve(
        self, context: dict[str, float], confidence: float, k: int = 5
    ) -> list[tuple[ReliabilityEvent, float]]:
        """Backward-compatible tuple view over ``retrieve_matches``."""
        return [(match.event, match.distance) for match in self.retrieve_matches(context, confidence, k=k, min_similarity=0.0)]

    def cluster_of(self, context: dict[str, float], confidence: float) -> int | None:
        if not self._fitted or self._kmeans is None:
            return None
        emb = self.embedder.embed(context, confidence)
        return int(self._kmeans.predict(emb.reshape(1, -1))[0])
