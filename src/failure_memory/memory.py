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

import numpy as np
from sklearn.cluster import KMeans

from src.schema.events import ReliabilityEvent
from src.storage.repository import EventRepository

from .embedding import FailureEmbedder


class FailureMemory:
    def __init__(
        self,
        feature_names: list[str],
        n_clusters: int = 3,
        sigma: float = 1.0,
        random_state: int = 42,
    ):
        self.embedder = FailureEmbedder(feature_names, n_components=2, random_state=random_state)
        self.n_clusters = n_clusters
        self.sigma = sigma
        self.random_state = random_state
        self._kmeans: KMeans | None = None
        self._fitted = False
        self._failure_embeddings: np.ndarray | None = None
        self._failure_events: list[ReliabilityEvent] = []

    # -- persistence -----------------------------------------------------
    def store(self, event: ReliabilityEvent, repository: EventRepository) -> None:
        """Persist an event. Only events with ``is_failure=True`` are
        retained in the failure-memory's own view (retrieve/risk), but all
        events are written through to the shared event store so the
        reliability engine and failure memory always agree on history."""
        repository.save(event)
        if event.is_failure:
            self._failure_events.append(event)
            self._fitted = False  # cached clustering is now stale

    def load_from_repository(
        self, repository: EventRepository, workload_id: str | None = None
    ) -> "FailureMemory":
        self._failure_events = repository.get_failures(workload_id=workload_id)
        self._fitted = False
        return self

    # -- clustering --------------------------------------------------------
    def fit(self) -> "FailureMemory":
        if not self._failure_events:
            self._fitted = False
            return self
        contexts = [e.context for e in self._failure_events]
        confidences = [e.confidence for e in self._failure_events]
        self.embedder.fit(contexts)
        embeddings = self.embedder.embed_batch(contexts, confidences)
        k = min(self.n_clusters, len(self._failure_events))
        self._kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        self._kmeans.fit(embeddings)
        self._failure_embeddings = embeddings
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    @property
    def n_failures(self) -> int:
        return len(self._failure_events)

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

    def retrieve(
        self, context: dict[str, float], confidence: float, k: int = 5
    ) -> list[tuple[ReliabilityEvent, float]]:
        """Return the k most similar historical failures and their squared
        distance in embedding space (ascending = more similar)."""
        if not self._fitted or self._failure_embeddings is None or not self._failure_events:
            return []
        emb = self.embedder.embed(context, confidence)
        d2 = np.sum((self._failure_embeddings - emb) ** 2, axis=1)
        order = np.argsort(d2)[:k]
        return [(self._failure_events[i], float(d2[i])) for i in order]

    def cluster_of(self, context: dict[str, float], confidence: float) -> int | None:
        if not self._fitted or self._kmeans is None:
            return None
        emb = self.embedder.embed(context, confidence)
        return int(self._kmeans.predict(emb.reshape(1, -1))[0])
