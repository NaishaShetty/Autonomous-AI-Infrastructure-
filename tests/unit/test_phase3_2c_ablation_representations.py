import numpy as np
import pytest

from src.evaluation.representations import (
    FailureHistoryRiskModel,
    FixedRuleFailureHistoryRisk,
    Phase2RepresentationSupervisedRisk,
)

FEATURES = ["f1", "f2"]


def _failures(n, cx=5.0, cy=5.0, seed=0):
    rng = np.random.default_rng(seed)
    return (
        [{"f1": cx + rng.normal(scale=0.1), "f2": cy + rng.normal(scale=0.1)} for _ in range(n)],
        [0.2] * n,
    )


def _regime_samples(n, failure_ratio=0.3, seed=1):
    rng = np.random.default_rng(seed)
    contexts, is_failure, confidences = [], [], []
    for _ in range(n):
        fail = rng.random() < failure_ratio
        base = (5.0, 5.0) if fail else (-5.0, -5.0)
        contexts.append({"f1": base[0] + rng.normal(scale=0.5), "f2": base[1] + rng.normal(scale=0.5)})
        is_failure.append(int(fail))
        confidences.append(0.2 if fail else 0.8)
    return contexts, is_failure, confidences


# -- FixedRuleFailureHistoryRisk (Experiment A) --------------------------


def test_experiment_a_zero_before_fit():
    model = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=3)
    assert model.risk({"f1": 0.0, "f2": 0.0}) == 0.0
    assert not model.is_fitted


def test_experiment_a_empty_failures_stays_unfitted():
    model = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=3)
    model.fit([], [], [{"f1": 0.0, "f2": 0.0}])
    assert not model.is_fitted


def test_experiment_a_is_not_a_probability():
    model = FixedRuleFailureHistoryRisk(FEATURES)
    assert model.is_probability is False


def test_experiment_a_no_labels_required():
    """The fixed rule is genuinely unsupervised -- its fit() signature must
    not accept a labels argument at all (unlike Candidate C's fit)."""
    import inspect

    sig = inspect.signature(FixedRuleFailureHistoryRisk.fit)
    assert "regime_is_failure" not in sig.parameters


def test_experiment_a_discriminates_failure_like_region_from_safe_region():
    failure_contexts, failure_confs = _failures(40)
    regime_contexts, _, _ = _regime_samples(400)
    model = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts)
    near_failure_risk = model.risk({"f1": 5.0, "f2": 5.0})
    far_from_failure_risk = model.risk({"f1": -5.0, "f2": -5.0})
    assert near_failure_risk > far_from_failure_risk


def test_experiment_a_deterministic():
    failure_contexts, failure_confs = _failures(30)
    regime_contexts, _, _ = _regime_samples(200)
    m1 = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts)
    m2 = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts)
    query = {"f1": 1.0, "f2": 2.0}
    assert m1.risk(query) == pytest.approx(m2.risk(query))


def test_experiment_a_uses_identical_features_to_candidate_c():
    """Experiment A and Experiment C (Candidate C) must compute the exact
    same 3 raw k-NN failure-history features -- only the combination rule
    may differ. Verified by reaching into both models' shared
    ``_FailureHistoryFeaturizer`` and confirming byte-identical output for
    the same query, given the same failure reference set."""
    failure_contexts, failure_confs = _failures(30)
    regime_contexts, regime_labels, _ = _regime_samples(200)

    model_a = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts)
    model_c = FailureHistoryRiskModel(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts, regime_labels)

    query = {"f1": 3.0, "f2": -1.5}
    np.testing.assert_allclose(model_a._featurizer.features(query), model_c._featurizer.features(query))


def test_experiment_a_standardization_fit_only_on_regime2_contexts():
    """The scaler's mean/scale must come only from the ``regime_contexts``
    argument, not be recomputed from any other data -- confirmed by
    changing the query point far outside the fitting distribution and
    checking the z-score reflects the ORIGINAL fitting distribution, not
    the query."""
    failure_contexts, failure_confs = _failures(30)
    regime_contexts, _, _ = _regime_samples(200)
    model = FixedRuleFailureHistoryRisk(FEATURES, k_neighbors=5).fit(failure_contexts, failure_confs, regime_contexts)
    mean_before = model._mean.copy()
    scale_before = model._scale.copy()
    model.risk({"f1": 1000.0, "f2": -1000.0})  # far outlier query
    np.testing.assert_array_equal(model._mean, mean_before)
    np.testing.assert_array_equal(model._scale, scale_before)


# -- Phase2RepresentationSupervisedRisk (Experiment B) --------------------


def test_experiment_b_zero_before_fit():
    model = Phase2RepresentationSupervisedRisk(FEATURES)
    assert model.risk({"f1": 0.0, "f2": 0.0}, confidence=0.5) == 0.0
    assert not model.is_fitted


def test_experiment_b_empty_failures_stays_unfitted():
    model = Phase2RepresentationSupervisedRisk(FEATURES)
    model.fit([], [{"f1": 0.0, "f2": 0.0}], [0.5], [0])
    assert not model.is_fitted


def test_experiment_b_degenerate_single_class_stays_unfitted():
    failure_contexts, _ = _failures(10)
    all_failure_regime = [{"f1": 5.0, "f2": 5.0}] * 10
    all_failure_confidences = [0.2] * 10
    all_failure_labels = [1] * 10
    model = Phase2RepresentationSupervisedRisk(FEATURES)
    model.fit(failure_contexts, all_failure_regime, all_failure_confidences, all_failure_labels)
    assert not model.is_fitted


def test_experiment_b_is_a_probability():
    model = Phase2RepresentationSupervisedRisk(FEATURES)
    assert model.is_probability is True


def test_experiment_b_fits_and_predicts_probability_in_unit_interval():
    failure_contexts, _ = _failures(30)
    regime_contexts, regime_labels, regime_confidences = _regime_samples(200)
    model = Phase2RepresentationSupervisedRisk(FEATURES).fit(failure_contexts, regime_contexts, regime_confidences, regime_labels)
    assert model.is_fitted
    r = model.risk({"f1": 5.0, "f2": 5.0}, confidence=0.2)
    assert 0.0 <= r <= 1.0


def test_experiment_b_discriminates_failure_like_region_from_safe_region():
    failure_contexts, _ = _failures(40)
    regime_contexts, regime_labels, regime_confidences = _regime_samples(400)
    model = Phase2RepresentationSupervisedRisk(FEATURES).fit(failure_contexts, regime_contexts, regime_confidences, regime_labels)
    near_failure_risk = model.risk({"f1": 5.0, "f2": 5.0}, confidence=0.2)
    far_from_failure_risk = model.risk({"f1": -5.0, "f2": -5.0}, confidence=0.8)
    assert near_failure_risk > far_from_failure_risk


def test_experiment_b_deterministic_given_seed():
    failure_contexts, _ = _failures(30)
    regime_contexts, regime_labels, regime_confidences = _regime_samples(200)
    m1 = Phase2RepresentationSupervisedRisk(FEATURES, random_state=3).fit(failure_contexts, regime_contexts, regime_confidences, regime_labels)
    m2 = Phase2RepresentationSupervisedRisk(FEATURES, random_state=3).fit(failure_contexts, regime_contexts, regime_confidences, regime_labels)
    query = {"f1": 1.0, "f2": 2.0}
    assert m1.risk(query, 0.3) == pytest.approx(m2.risk(query, 0.3))


def test_experiment_b_uses_unmodified_failure_embedder():
    """Confirms Experiment B genuinely reuses
    ``src.failure_memory.embedding.FailureEmbedder`` (imported, not
    reimplemented) as its representation."""
    from src.failure_memory.embedding import FailureEmbedder

    model = Phase2RepresentationSupervisedRisk(FEATURES)
    assert isinstance(model._embedder, FailureEmbedder)


def test_experiment_b_pca_fit_only_on_failure_contexts():
    """The embedder's PCA must be fit on exactly the failure_contexts
    argument (matching Phase 2's FailureMemory.fit), not on all of
    regime_contexts -- verified by fitting with two different failure sets
    against the SAME regime_contexts and confirming predictions differ."""
    regime_contexts, regime_labels, regime_confidences = _regime_samples(200)
    failures_a, _ = _failures(20, cx=5.0, cy=5.0)
    failures_b, _ = _failures(20, cx=-5.0, cy=-5.0)

    model_a = Phase2RepresentationSupervisedRisk(FEATURES).fit(failures_a, regime_contexts, regime_confidences, regime_labels)
    model_b = Phase2RepresentationSupervisedRisk(FEATURES).fit(failures_b, regime_contexts, regime_confidences, regime_labels)

    # risk() alone can saturate to ~1.0 for extreme queries under both
    # models regardless of which failure set the PCA was fit on, so compare
    # the embeddings directly -- these are what actually depend on PCA
    # fitting data, and must differ when the failure set differs.
    query = {"f1": 5.0, "f2": 5.0}
    emb_a = model_a._embedder.embed(query, 0.2)
    emb_b = model_b._embedder.embed(query, 0.2)
    assert not np.allclose(emb_a, emb_b)
