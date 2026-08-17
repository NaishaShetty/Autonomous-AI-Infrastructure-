"""Phase 3.2 candidate failure-risk representations.

EXPERIMENTAL. Nothing in this module is imported by ``src/decision``,
``src/api``, or ``src/pipeline_builder`` -- these candidates are evaluation
artifacts only, per the Phase 3.2 brief's explicit instruction not to
integrate a candidate into autonomous decision-making. Candidate A (the
Phase 2 control) is NOT reimplemented here; it is the actual, unmodified
``src.failure_memory.memory.FailureMemory`` used exactly as Phase 3.1 used
it -- see ``benchmarks/phase3_2_evaluate.py``.

Both candidates below are fit EXCLUSIVELY on regime-2 (Phase 3.1's
"validation / failure logging" split) data, per the same data-boundary the
Phase 2/3.1 control condition uses -- see each class's ``fit`` docstring for
exactly which regime-2 subset it consumes. Neither candidate is ever fit on,
or has any parameter selected against, the regime-3/4 test stream.

Candidate B -- raw structured features
---------------------------------------
Tests whether Phase 2's PCA projection step is *destroying* information the
KMeans/Gaussian-kernel mechanism could otherwise use. Identical downstream
mechanism to Candidate A (KMeans, same n_clusters, same Gaussian-kernel
risk formula, same sigma), the ONLY change is skipping the PCA step and
clustering directly on the raw feature+confidence vector. No additional
normalization is introduced: ``src/data/synthetic.py`` generates
``f1..f5 ~ N(0, I)`` in every regime (independently confirmed in the Phase
3.1 leakage audit's "regime identifiability" check), so raw features are
already unit-scale -- there is no justified reason to add a scaler, and the
Phase 3.2 brief instructs against introducing "arbitrary transformations".

Candidate C -- explicit failure-history features
--------------------------------------------------
Tests whether a small, explicitly-justified set of failure-history
statistics (not just "distance to 3 coarse cluster centroids") carries
transferable signal. Three features, each satisfying "would genuinely be
available at prediction time":

  1. ``knn_distance_failure`` -- Euclidean distance (raw feature space) to
     the k-th nearest logged historical failure. Smaller = this input
     resembles known failures more closely than Candidate A/B's
     3-centroid summary can represent.
  2. ``local_failure_density`` -- count of logged failures within a fixed
     radius (the median k-NN distance among the failure set itself,
     computed once at fit time from failures only). A density estimate,
     not a single nearest-neighbor distance.
  3. ``confidence_of_nearest_failures`` -- mean calibrated confidence of
     the k nearest logged failures. Tests whether the *confidence profile*
     of nearby historical failures (not just their spatial location) adds
     information.

These 3 features (not more) are fed into a `LogisticRegression` fit on ALL
of regime 2 (successes AND failures, unlike Candidate A/B which cluster
only the failures) with target = the sample's own true failure/success
outcome. This is a deliberate, documented methodological difference from
Candidate A/B (see docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md section 4)
-- regime 2 is legitimately available train-side data for both framings,
using its non-failure examples too is not leakage, just a different (and
more supervised) use of the same permitted data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

from src.failure_memory.embedding import FailureEmbedder


def _vectorize(context: dict[str, float], feature_names: list[str]) -> np.ndarray:
    return np.array([context.get(f, 0.0) for f in feature_names], dtype=float)


def _confidence_derived(confidence: float) -> tuple[float, float]:
    return 2.0 * abs(confidence - 0.5), abs(confidence - 0.5)


@dataclass
class RawFeatureFailureRisk:
    """Candidate B: same KMeans + Gaussian-kernel mechanism as Phase 2's
    FailureMemory, applied to the raw (non-PCA) feature+confidence vector."""

    feature_names: list[str]
    n_clusters: int = 3
    sigma: float = 1.0
    random_state: int = 42
    is_probability: bool = field(default=False, init=False)

    def __post_init__(self):
        self._kmeans: KMeans | None = None
        self._fitted = False

    def fit(self, failure_contexts: list[dict[str, float]], failure_confidences: list[float]) -> "RawFeatureFailureRisk":
        """Fits on exactly the failures passed in -- callers are
        responsible for ensuring this is the regime-2 failure set only (see
        ``benchmarks/phase3_2_evaluate.py::_fit_candidates``)."""
        if not failure_contexts:
            self._fitted = False
            return self
        vectors = []
        for ctx, conf in zip(failure_contexts, failure_confidences):
            raw = _vectorize(ctx, self.feature_names)
            derived = _confidence_derived(conf)
            vectors.append(np.concatenate([raw, derived]))
        X = np.stack(vectors)
        k = min(self.n_clusters, len(failure_contexts))
        self._kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        self._kmeans.fit(X)
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def risk(self, context: dict[str, float], confidence: float) -> float:
        if not self._fitted or self._kmeans is None:
            return 0.0
        raw = _vectorize(context, self.feature_names)
        derived = _confidence_derived(confidence)
        emb = np.concatenate([raw, derived])
        centroids = self._kmeans.cluster_centers_
        d2 = np.sum((centroids - emb) ** 2, axis=1)
        similarities = np.exp(-d2 / (self.sigma**2))
        return float(np.clip(np.max(similarities), 0.0, 1.0))


class _FailureHistoryFeaturizer:
    """Shared k-NN failure-history feature extraction: distance to the k-th
    nearest logged failure, local failure density, and mean confidence of
    the k nearest logged failures -- exactly the 3 features Candidate C
    (Phase 3.2) defines (see module docstring). Factored out so that
    ``FailureHistoryRiskModel`` (the frozen Candidate C reproduction, used
    unmodified as Experiment C's positive control) and
    ``FixedRuleFailureHistoryRisk`` (Experiment A, the follow-up ablation's
    unlearned scoring rule) are PROVABLY computing the identical
    representation -- the only thing that may differ between A and C is
    how the 3 numbers are combined into a risk score, never how they are
    computed. This class changes no formula that existed in Candidate C
    before this follow-up study; it only moves the existing computation
    into one place both callers share.

    Fit exclusively on the failure_contexts/failure_confidences passed in
    -- callers are responsible for ensuring this is the regime-2 failure
    set only.
    """

    def __init__(self, feature_names: list[str], k_neighbors: int = 5):
        self.feature_names = feature_names
        self.k_neighbors = k_neighbors
        self._nn: NearestNeighbors | None = None
        self._failure_confidences: np.ndarray | None = None
        self._density_radius: float | None = None
        self._fitted = False

    def fit(self, failure_contexts: list[dict[str, float]], failure_confidences: list[float]) -> "_FailureHistoryFeaturizer":
        if not failure_contexts:
            self._fitted = False
            return self

        failure_X = np.stack([_vectorize(c, self.feature_names) for c in failure_contexts])
        self._failure_confidences = np.array(failure_confidences, dtype=float)
        k = min(self.k_neighbors, len(failure_contexts))
        self._nn = NearestNeighbors(n_neighbors=k).fit(failure_X)

        # Density radius: median distance-to-k-th-neighbor among the
        # failures themselves (leave-one-out via k+1 neighbors, dropping
        # the self-match at distance 0), computed only from failure data.
        if len(failure_contexts) > 1:
            self_k = min(k + 1, len(failure_contexts))
            self_distances, _ = self._nn.kneighbors(failure_X, n_neighbors=self_k)
            self._density_radius = float(np.median(self_distances[:, -1]))
        else:
            self._density_radius = 0.0

        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def features(self, context: dict[str, float]) -> np.ndarray:
        """Returns ``[knn_distance_failure, local_failure_density,
        confidence_of_nearest_failures]``."""
        x = _vectorize(context, self.feature_names).reshape(1, -1)
        k = min(self.k_neighbors, self._nn.n_samples_fit_)
        distances, indices = self._nn.kneighbors(x, n_neighbors=k)
        distances = distances[0]
        indices = indices[0]

        knn_distance_failure = float(distances[-1])  # distance to k-th nearest failure
        local_failure_density = float(np.sum(distances <= self._density_radius))
        confidence_of_nearest_failures = float(self._failure_confidences[indices].mean())
        return np.array([knn_distance_failure, local_failure_density, confidence_of_nearest_failures])


@dataclass
class FailureHistoryRiskModel:
    """Candidate C: 3 explicit failure-history features -> logistic
    regression, fit on all of regime 2 (not just its failures).

    Reproduced UNCHANGED for the Phase 3.2 follow-up ablation (Experiment
    C, the positive control) -- same k=5, same feature definitions (now
    delegated to ``_FailureHistoryFeaturizer``, which computes exactly the
    formulas this class computed inline before the follow-up study; see
    that class's docstring), same fitting data, same classifier
    configuration, same preprocessing. No behavior here differs from the
    Phase 3.2 result being decomposed."""

    feature_names: list[str]
    k_neighbors: int = 5
    random_state: int = 42
    is_probability: bool = field(default=True, init=False)

    def __post_init__(self):
        self._featurizer = _FailureHistoryFeaturizer(self.feature_names, self.k_neighbors)
        self._clf: LogisticRegression | None = None
        self._fitted = False

    def fit(
        self,
        failure_contexts: list[dict[str, float]],
        failure_confidences: list[float],
        regime_contexts: list[dict[str, float]],
        regime_is_failure: list[int],
    ) -> "FailureHistoryRiskModel":
        """``failure_contexts``/``failure_confidences``: the regime-2
        failure set only (used as the k-NN reference set for the 3
        features). ``regime_contexts``/``regime_is_failure``: ALL of
        regime 2 (successes and failures), used as the supervised training
        set for the logistic regression -- see module docstring for why
        this is a legitimate, documented difference from Candidate A/B."""
        self._featurizer.fit(failure_contexts, failure_confidences)
        if not self._featurizer.is_fitted:
            self._fitted = False
            return self

        feature_rows = [self._featurizer.features(c) for c in regime_contexts]
        X = np.stack(feature_rows)
        y = np.array(regime_is_failure, dtype=int)

        if len(np.unique(y)) < 2:
            # Degenerate regime (no failures or no successes logged) --
            # cannot fit a 2-class classifier; report honestly rather than
            # fabricate a model.
            self._fitted = False
            return self

        self._clf = LogisticRegression(max_iter=1000, random_state=self.random_state)
        self._clf.fit(X, y)
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def risk(self, context: dict[str, float], confidence: float | None = None) -> float:
        """``confidence`` is accepted for interface compatibility with the
        other candidates but is NOT used -- Candidate C deliberately tests
        failure-history features in isolation from the calibrator's own
        confidence signal (see module docstring)."""
        if not self._fitted or self._clf is None:
            return 0.0
        features = self._featurizer.features(context).reshape(1, -1)
        return float(self._clf.predict_proba(features)[0, 1])


@dataclass
class FixedRuleFailureHistoryRisk:
    """Ablation Experiment A (Phase 3.2 follow-up): Candidate C's rich
    k-NN failure-history representation (identical features, via the same
    ``_FailureHistoryFeaturizer`` Experiment C's ``FailureHistoryRiskModel``
    uses -- see that class's docstring), combined with a SIMPLE,
    PREDETERMINED, non-trained scoring rule instead of logistic regression.

    Rule (fixed before any test-set evaluation, never tuned against test
    performance): standardize each of the 3 features using a StandardScaler
    fit on regime-2 data only (all of regime 2, matching the fitting data
    Candidate C's classifier trains on), then combine with equal (1/3)
    weight and a fixed sign chosen from the feature's own definition, not
    from data:

      - ``knn_distance_failure``: SMALLER distance to a known failure means
        MORE risk -> sign = -1 (negated after standardization).
      - ``local_failure_density``: MORE nearby historical failures means
        MORE risk -> sign = +1.
      - ``confidence_of_nearest_failures``: historical failures nearby that
        occurred at HIGH calibrated confidence indicate this region fools
        the calibrator even when it is confident -> MORE risk -> sign = +1.

    score = mean(sign_i * standardized_feature_i). This is a ranking score,
    not a probability (no distributional assumption ties it to [0, 1]) --
    ``is_probability`` is False and ECE is not reported, matching the
    calibration-discipline rule the frozen protocol already applies to
    Candidate A/B's similarity scores.

    No weight, sign, or scaling parameter here was chosen by looking at
    AUROC on any held-out split; they are fixed by the semantic direction
    of each feature's definition alone.
    """

    feature_names: list[str]
    k_neighbors: int = 5
    is_probability: bool = field(default=False, init=False)
    _SIGNS = np.array([-1.0, 1.0, 1.0])  # [knn_distance, density, confidence_of_nearest]

    def __post_init__(self):
        self._featurizer = _FailureHistoryFeaturizer(self.feature_names, self.k_neighbors)
        self._mean: np.ndarray | None = None
        self._scale: np.ndarray | None = None
        self._fitted = False

    def fit(
        self,
        failure_contexts: list[dict[str, float]],
        failure_confidences: list[float],
        regime_contexts: list[dict[str, float]],
    ) -> "FixedRuleFailureHistoryRisk":
        """``regime_contexts``: ALL of regime 2 (successes and failures) --
        used only to fit the standardization (mean/std), never to choose a
        weight, sign, or threshold. No labels (``regime_is_failure``) are
        needed or accepted; this rule is genuinely unsupervised."""
        self._featurizer.fit(failure_contexts, failure_confidences)
        if not self._featurizer.is_fitted:
            self._fitted = False
            return self

        X = np.stack([self._featurizer.features(c) for c in regime_contexts])
        self._mean = X.mean(axis=0)
        std = X.std(axis=0)
        self._scale = np.where(std > 1e-12, std, 1.0)  # guard constant columns, not a tuned epsilon
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def risk(self, context: dict[str, float]) -> float:
        if not self._fitted:
            return 0.0
        raw = self._featurizer.features(context)
        z = (raw - self._mean) / self._scale
        return float(np.mean(self._SIGNS * z))


@dataclass
class Phase2RepresentationSupervisedRisk:
    """Ablation Experiment B (Phase 3.2 follow-up): the EXISTING Phase 2
    representation (``src.failure_memory.embedding.FailureEmbedder`` --
    imported and used exactly as ``FailureMemory.fit`` uses it, not
    modified or redesigned) combined with a supervised classifier, using
    the same ``LogisticRegression`` configuration Candidate C uses. Isolates
    "old representation + supervised learning" from "new representation +
    supervised learning".

    The embedder's PCA is fit on the regime-2 FAILURE contexts only --
    identical fitting data to ``FailureMemory.fit`` (Phase 2's own
    control), which calls ``self.embedder.fit(contexts)`` with
    ``contexts = [e.context for e in self._failure_events]``, i.e. failures
    only. The logistic regression is then fit on the resulting embedding
    for ALL of regime 2 (successes and failures), matching Candidate C's
    supervised-fitting convention (see ``FailureHistoryRiskModel``
    docstring) so the only difference between Experiment B and Experiment
    C is the representation, not the training-data convention.
    """

    feature_names: list[str]
    random_state: int = 42
    is_probability: bool = field(default=True, init=False)

    def __post_init__(self):
        self._embedder = FailureEmbedder(self.feature_names, n_components=2, random_state=self.random_state)
        self._clf: LogisticRegression | None = None
        self._fitted = False

    def fit(
        self,
        failure_contexts: list[dict[str, float]],
        regime_contexts: list[dict[str, float]],
        regime_confidences: list[float],
        regime_is_failure: list[int],
    ) -> "Phase2RepresentationSupervisedRisk":
        """``failure_contexts``: regime-2 failures only (PCA fitting data,
        matching Phase 2's ``FailureMemory.fit``). ``regime_contexts`` /
        ``regime_confidences`` / ``regime_is_failure``: ALL of regime 2,
        aligned row-for-row -- every regime-2 sample needs its own
        calibrated confidence to be embedded (the embedder's derived
        features depend on confidence), not just the failures'."""
        if not failure_contexts:
            self._fitted = False
            return self

        self._embedder.fit(failure_contexts)
        X = self._embedder.embed_batch(regime_contexts, regime_confidences)
        y = np.array(regime_is_failure, dtype=int)

        if len(np.unique(y)) < 2:
            self._fitted = False
            return self

        self._clf = LogisticRegression(max_iter=1000, random_state=self.random_state)
        self._clf.fit(X, y)
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def risk(self, context: dict[str, float], confidence: float) -> float:
        if not self._fitted or self._clf is None:
            return 0.0
        emb = self._embedder.embed(context, confidence).reshape(1, -1)
        return float(self._clf.predict_proba(emb)[0, 1])
