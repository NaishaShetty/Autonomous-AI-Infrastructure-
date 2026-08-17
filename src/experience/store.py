"""Phase 4.1.3: the experience store.

In-memory primary structure (this is an offline synthetic benchmark, same
scale as Phase 3's benchmarks -- no case for a database in the hot
retrieval path). Optional pass-through persistence of the ReliabilityEvent
half via the existing, frozen ``EventRepository`` is provided
(``ExperienceStore.persist``) so the store composes with the project's
existing storage layer rather than reimplementing it -- see module
docstring limitation below.

Deliberately smallest research-valid mechanism first (4.1.9): plain
similarity retrieval via the existing, frozen ``FailureEmbedder``. Recency
handling is a documented, OPT-IN secondary scoring term
(``decay_lambda``), not the default -- see docs/PHASE4_1_FAILURE_MEMORY.md
section on staleness/decay for why and how it was evaluated.
"""
from __future__ import annotations

import hashlib
from typing import Optional

import numpy as np

from src.failure_memory.embedding import FailureEmbedder
from src.storage.repository import EventRepository

from .schema import DecisionTimeQuery, Experience, experience_from_episode_record


class ExperienceStore:
    def __init__(self, feature_names: list[str], random_state: int = 42):
        self.feature_names = list(feature_names)
        self._experiences: list[Experience] = []
        self._embedder = FailureEmbedder(feature_names, n_components=2, random_state=random_state)
        self._embedder_fitted = False
        self._embeddings: Optional[np.ndarray] = None

    def __len__(self) -> int:
        return len(self._experiences)

    @property
    def experiences(self) -> list[Experience]:
        return list(self._experiences)

    def add(self, experience: Experience) -> None:
        self._experiences.append(experience)
        self._embedder_fitted = False  # any cached embedding matrix is now stale

    def add_many(self, experiences: list[Experience]) -> None:
        for e in experiences:
            self.add(e)

    def fit_embedder(self) -> "ExperienceStore":
        """Fits the (frozen, reused) FailureEmbedder on the store's OWN
        contents only. Callers are responsible for having populated the
        store from the train split only before calling this (see
        docs/PHASE4_1_FAILURE_MEMORY.md section 4.1.4) -- the store itself
        has no notion of "split", it only knows what was added to it."""
        if not self._experiences:
            self._embedder_fitted = False
            return self
        contexts = [e.event.context for e in self._experiences]
        confidences = [e.event.confidence for e in self._experiences]
        self._embedder.fit(contexts)
        self._embeddings = self._embedder.embed_batch(contexts, confidences)
        self._embedder_fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._embedder_fitted

    # -- retrieval mechanisms (Phase 4.1.6) --------------------------------

    def retrieve_random(self, query: DecisionTimeQuery, k: int, seed: int) -> list[Experience]:
        """Baseline A: no-memory / uniform-random retrieval. Deterministic
        given ``seed`` -- does NOT use ``query`` at all (by definition of
        this baseline)."""
        if not self._experiences:
            return []
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(self._experiences), size=min(k, len(self._experiences)), replace=False)
        return [self._experiences[i] for i in idx]

    def retrieve_recency(self, query: DecisionTimeQuery, k: int) -> list[Experience]:
        """Baseline B: recency-only retrieval -- the k most recent stored
        experiences (highest ``provenance.step``), no similarity
        computation. Ties broken by insertion order (stable sort)."""
        ordered = sorted(self._experiences, key=lambda e: e.provenance.step, reverse=True)
        return ordered[:k]

    def retrieve_similarity(
        self, query: DecisionTimeQuery, k: int, decay_lambda: float = 0.0,
    ) -> list[Experience]:
        """Proposed Phase 4.1 method: k-nearest stored experiences by
        embedding distance (context + confidence, via the frozen
        FailureEmbedder -- identical embedding formula to
        src.failure_memory.memory.FailureMemory.retrieve, reused rather
        than reimplemented).

        ``decay_lambda`` (>= 0.0, default 0.0 = no recency weighting):
        when > 0, score = squared_distance + decay_lambda * age, where
        age = query.step - experience.step (only meaningful when
        query.step is provided; raises if decay_lambda > 0 and query.step
        is None, rather than silently ignoring the parameter)."""
        if not self._embedder_fitted or self._embeddings is None or not self._experiences:
            return []
        if decay_lambda > 0.0 and query.step is None:
            raise ValueError("decay_lambda > 0 requires query.step to be set")

        query_embedding = self._embedder.embed(query.context, query.confidence)
        d2 = np.sum((self._embeddings - query_embedding) ** 2, axis=1)

        score = d2
        if decay_lambda > 0.0:
            age = np.array([max(0, query.step - e.provenance.step) for e in self._experiences], dtype=float)
            score = d2 + decay_lambda * age

        order = np.argsort(score)[: min(k, len(self._experiences))]
        return [self._experiences[i] for i in order]

    # -- persistence (optional pass-through to the existing, frozen storage layer) --

    def persist(self, repository: EventRepository) -> None:
        """Writes the ReliabilityEvent half of every stored experience
        through the existing EventRepository. LIMITATION: this persists
        only what ReliabilityEvent.metadata carries (the
        EpisodeProvenance mirror, see schema.py) -- reloading via
        EventRepository.get_failures() reconstructs ReliabilityEvent
        objects with that metadata dict, but NOT typed EpisodeProvenance
        objects; a caller wanting a fully-typed reloaded ExperienceStore
        must reconstruct EpisodeProvenance from event.metadata itself.
        Out of scope for Phase 4.1 (no experiment here needs a reloaded
        store) -- documented, not silently incomplete."""
        repository.save_many([e.event for e in self._experiences])

    def content_hash(self) -> str:
        """Reproducible version identifier for this store's contents
        (Phase 4.1.8 / docs/PHASE4_PLAN.md section 3's learned-state
        versioning requirement). Order-independent (sorted by event_id)
        so two stores built from the same records in a different add()
        order still hash identically."""
        ids = sorted(e.event.event_id for e in self._experiences)
        payload = "|".join(ids).encode()
        return hashlib.sha256(payload).hexdigest()


def build_store_from_episode_records(
    records: list[dict],
    feature_names: list[str],
    protocol_version: str,
    dataset_content_hash: str,
    split: str = "train",
    random_state: int = 42,
) -> ExperienceStore:
    """Populates a store from Phase 4.0 episode records, restricted to
    ``split`` (default "train" -- Phase 4.1.4: the store may only be
    populated from the train split) AND ``is_failure == True`` (the
    population of interest for a FAILURE experience store, matching
    src.failure_memory.memory.FailureMemory's existing store-only-failures
    convention -- not a new scope decision invented here)."""
    store = ExperienceStore(feature_names, random_state=random_state)
    selected = [r for r in records if r["split"] == split and r["is_failure"]]
    experiences = [experience_from_episode_record(r, protocol_version, dataset_content_hash) for r in selected]
    store.add_many(experiences)
    store.fit_embedder()
    return store
