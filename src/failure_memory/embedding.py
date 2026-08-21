"""Failure representation.

Migrates the concept validated as reusable in Phase 1 (input features +
confidence -> low-dimensional embedding, PHASE1_AUDIT_REPORT.md section 7:
"failure_embedding.py ... Refactor -- sound minimal concept, but PCA-only
and single-sample-only API won't generalize or scale").

Two changes from the source implementation:
  1. Accepts the canonical ``context: dict[str, float]`` from
     ``src/schema/events.py`` instead of a hardcoded 5-dim numpy array, so it
     is not coupled to the old repo's synthetic dataset shape.
  2. Adds a batch API (``embed_batch``) -- the source implementation only
     exposed a single-sample ``embed()``, which Phase 1 found forced every
     call site into unvectorized Python loops (the audit's specific example:
     ``evaluate_cluster_specialists.py`` recomputing embeddings twice per
     sample in nested loops, the slowest script in either repo).
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


class FailureEmbedder:
    """Projects a structured context + confidence into a fixed-size vector
    used for clustering and similarity retrieval."""

    def __init__(self, feature_names: list[str], n_components: int = 2, random_state: int = 42):
        self.feature_names = list(feature_names)
        self.n_components = n_components
        self._pca = PCA(n_components=n_components, random_state=random_state)
        self._fitted = False
        self._small_sample = False
        self._zero_variance = False
        self._fit_mean: np.ndarray | None = None
        self._fit_components = n_components

    def _vectorize(self, context: dict[str, float]) -> np.ndarray:
        return np.array([context.get(name, 0.0) for name in self.feature_names], dtype=float)

    def fit(self, contexts: list[dict[str, float]]) -> "FailureEmbedder":
        if not contexts:
            raise ValueError("FailureEmbedder.fit requires at least one context")
        X = np.stack([self._vectorize(c) for c in contexts])
        n_components = max(1, min(self.n_components, X.shape[0], X.shape[1]))
        self._fit_components = n_components
        self._fit_mean = X.mean(axis=0)
        self._small_sample = X.shape[0] < 2
        self._zero_variance = bool(np.all(np.ptp(X, axis=0) == 0.0))
        if self._small_sample or self._zero_variance:
            self._fitted = True
            return self
        if n_components != self.n_components:
            self._pca = PCA(n_components=n_components, random_state=self._pca.random_state)
        self._pca.fit(X)
        self._fit_components = self._pca.n_components_
        self._fitted = True
        return self

    def embed(self, context: dict[str, float], confidence: float) -> np.ndarray:
        return self.embed_batch([context], [confidence])[0]

    def embed_batch(
        self, contexts: list[dict[str, float]], confidences: list[float]
    ) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FailureEmbedder must be fit() before embed()")
        X = np.stack([self._vectorize(c) for c in contexts])
        if self._small_sample or self._zero_variance:
            if self._fit_mean is None:
                raise RuntimeError("FailureEmbedder fit state is incomplete")
            centered = X - self._fit_mean
            projected = np.zeros((X.shape[0], self._fit_components), dtype=float)
            width = min(self._fit_components, centered.shape[1])
            projected[:, :width] = centered[:, :width]
        else:
            projected = self._pca.transform(X)
        conf = np.asarray(confidences, dtype=float)
        derived = np.stack(
            [2.0 * np.abs(conf - 0.5), np.abs(conf - 0.5)], axis=1
        )  # [confidence_signal, margin]
        return np.concatenate([projected, derived], axis=1)

    @property
    def output_dim(self) -> int:
        return self._fit_components + 2
