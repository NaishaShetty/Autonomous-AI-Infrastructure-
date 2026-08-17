import numpy as np
import pytest

from src.evaluation.representations import FailureHistoryRiskModel, RawFeatureFailureRisk

FEATURES = ["f1", "f2"]


def _failures(n, cx=5.0, cy=5.0, seed=0):
    rng = np.random.default_rng(seed)
    return (
        [{"f1": cx + rng.normal(scale=0.1), "f2": cy + rng.normal(scale=0.1)} for _ in range(n)],
        [0.2] * n,
    )


# -- RawFeatureFailureRisk (Candidate B) --------------------------------


def test_raw_risk_zero_before_fit():
    model = RawFeatureFailureRisk(FEATURES, n_clusters=2)
    assert model.risk({"f1": 1.0, "f2": 1.0}, confidence=0.5) == 0.0
    assert not model.is_fitted


def test_raw_risk_empty_failures_stays_unfitted():
    model = RawFeatureFailureRisk(FEATURES, n_clusters=2)
    model.fit([], [])
    assert not model.is_fitted


def test_raw_risk_higher_near_known_failures():
    contexts, confs = _failures(20)
    model = RawFeatureFailureRisk(FEATURES, n_clusters=1).fit(contexts, confs)
    near = model.risk({"f1": 5.0, "f2": 5.0}, confidence=0.2)
    far = model.risk({"f1": -500.0, "f2": -500.0}, confidence=0.2)
    assert near > far
    assert 0.0 <= far <= near <= 1.0


def test_raw_risk_is_not_a_probability():
    model = RawFeatureFailureRisk(FEATURES)
    assert model.is_probability is False


def test_raw_risk_deterministic_given_seed():
    contexts, confs = _failures(30)
    m1 = RawFeatureFailureRisk(FEATURES, n_clusters=2, random_state=7).fit(contexts, confs)
    m2 = RawFeatureFailureRisk(FEATURES, n_clusters=2, random_state=7).fit(contexts, confs)
    query = {"f1": 3.0, "f2": 4.0}
    assert m1.risk(query, 0.3) == pytest.approx(m2.risk(query, 0.3))


def test_raw_risk_uses_full_feature_dimensionality_not_pca():
    """Confirms no dimensionality reduction happens -- the fitted KMeans
    centroids must have shape (k, len(features) + 2), not any PCA-reduced
    dimension."""
    contexts, confs = _failures(15)
    model = RawFeatureFailureRisk(FEATURES, n_clusters=2).fit(contexts, confs)
    assert model._kmeans.cluster_centers_.shape[1] == len(FEATURES) + 2


# -- FailureHistoryRiskModel (Candidate C) -------------------------------


def _regime_samples(n, failure_ratio=0.3, seed=1):
    rng = np.random.default_rng(seed)
    contexts, is_failure = [], []
    for _ in range(n):
        fail = rng.random() < failure_ratio
        base = (5.0, 5.0) if fail else (-5.0, -5.0)
        contexts.append({"f1": base[0] + rng.normal(scale=0.5), "f2": base[1] + rng.normal(scale=0.5)})
        is_failure.append(int(fail))
    return contexts, is_failure


def test_history_model_zero_before_fit():
    model = FailureHistoryRiskModel(FEATURES, k_neighbors=3)
    assert model.risk({"f1": 0.0, "f2": 0.0}) == 0.0
    assert not model.is_fitted


def test_history_model_empty_failures_stays_unfitted():
    model = FailureHistoryRiskModel(FEATURES, k_neighbors=3)
    model.fit([], [], [{"f1": 0.0, "f2": 0.0}], [0])
    assert not model.is_fitted


def test_history_model_degenerate_single_class_stays_unfitted():
    """If regime 2 happened to log zero successes (or zero failures), a
    2-class logistic regression cannot be fit -- must report unfitted, not
    fabricate a model."""
    failure_contexts, failure_confs = _failures(10)
    all_failure_regime = [{"f1": 5.0, "f2": 5.0}] * 10
    all_failure_labels = [1] * 10
    model = FailureHistoryRiskModel(FEATURES, k_neighbors=3)
    model.fit(failure_contexts, failure_confs, all_failure_regime, all_failure_labels)
    assert not model.is_fitted


def test_history_model_fits_and_predicts_probability_in_unit_interval():
    failure_contexts, failure_confs = _failures(30)
    regime_contexts, regime_labels = _regime_samples(200)
    model = FailureHistoryRiskModel(FEATURES, k_neighbors=5).fit(
        failure_contexts, failure_confs, regime_contexts, regime_labels
    )
    assert model.is_fitted
    assert model.is_probability is True
    r = model.risk({"f1": 5.0, "f2": 5.0})
    assert 0.0 <= r <= 1.0


def test_history_model_discriminates_failure_like_region_from_safe_region():
    failure_contexts, failure_confs = _failures(40)
    regime_contexts, regime_labels = _regime_samples(400)
    model = FailureHistoryRiskModel(FEATURES, k_neighbors=5).fit(
        failure_contexts, failure_confs, regime_contexts, regime_labels
    )
    near_failure_risk = model.risk({"f1": 5.0, "f2": 5.0})
    far_from_failure_risk = model.risk({"f1": -5.0, "f2": -5.0})
    assert near_failure_risk > far_from_failure_risk


def test_history_model_deterministic_given_seed():
    failure_contexts, failure_confs = _failures(30)
    regime_contexts, regime_labels = _regime_samples(200)
    m1 = FailureHistoryRiskModel(FEATURES, k_neighbors=5, random_state=3).fit(
        failure_contexts, failure_confs, regime_contexts, regime_labels
    )
    m2 = FailureHistoryRiskModel(FEATURES, k_neighbors=5, random_state=3).fit(
        failure_contexts, failure_confs, regime_contexts, regime_labels
    )
    query = {"f1": 1.0, "f2": 2.0}
    assert m1.risk(query) == pytest.approx(m2.risk(query))


def test_history_model_features_only_reference_failure_data_passed_in():
    """The k-NN reference set for the 3 engineered features must be built
    exclusively from the failure_contexts argument -- not from
    regime_contexts. Verified by fitting with two DIFFERENT failure sets
    but the SAME regime_contexts/labels, and confirming predictions
    differ."""
    regime_contexts, regime_labels = _regime_samples(200)
    failures_a, confs_a = _failures(20, cx=5.0, cy=5.0)
    failures_b, confs_b = _failures(20, cx=-5.0, cy=-5.0)

    model_a = FailureHistoryRiskModel(FEATURES, k_neighbors=5).fit(failures_a, confs_a, regime_contexts, regime_labels)
    model_b = FailureHistoryRiskModel(FEATURES, k_neighbors=5).fit(failures_b, confs_b, regime_contexts, regime_labels)

    query = {"f1": 5.0, "f2": 5.0}
    assert model_a.risk(query) != pytest.approx(model_b.risk(query))
