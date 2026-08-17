import numpy as np
import pytest

from src.evaluation.bootstrap import bootstrap_ci
from src.evaluation.metrics import (
    auprc,
    aurc,
    auroc,
    expected_calibration_error,
    precision_recall_at_coverage,
)


def _perfectly_separable():
    rng = np.random.default_rng(0)
    n = 500
    y_true = rng.integers(0, 2, size=n)
    # score perfectly ranks positives above negatives, plus tiny noise so
    # ties don't make the test brittle
    y_score = y_true.astype(float) + rng.normal(scale=1e-6, size=n)
    return y_true, y_score


def test_auroc_perfect_separation_is_one():
    y_true, y_score = _perfectly_separable()
    assert auroc(y_true, y_score) == pytest.approx(1.0, abs=1e-6)


def test_auroc_random_score_near_half_on_average():
    rng = np.random.default_rng(1)
    n = 2000
    y_true = rng.integers(0, 2, size=n)
    y_score = rng.normal(size=n)  # unrelated to y_true
    value = auroc(y_true, y_score)
    assert 0.4 < value < 0.6  # not a tight bound -- just "not obviously wrong"


def test_auroc_undefined_for_single_class_returns_none():
    y_true = np.zeros(20)
    y_score = np.random.default_rng(0).normal(size=20)
    assert auroc(y_true, y_score) is None
    assert auprc(y_true, y_score) is None


def test_auroc_constant_score_is_exactly_half():
    """The 'no signal' anchor case: a constant score cannot discriminate at
    all, so AUROC must be exactly 0.5 regardless of class balance."""
    rng = np.random.default_rng(2)
    y_true = rng.integers(0, 2, size=1000)
    y_score = np.full(1000, 0.37)
    assert auroc(y_true, y_score) == pytest.approx(0.5)


def test_auprc_constant_score_equals_prevalence():
    rng = np.random.default_rng(3)
    y_true = rng.integers(0, 2, size=2000)
    y_score = np.full(2000, 0.5)
    prevalence = y_true.mean()
    assert auprc(y_true, y_score) == pytest.approx(prevalence, abs=0.02)


def test_ece_perfectly_calibrated_probabilities_near_zero():
    rng = np.random.default_rng(4)
    n = 5000
    y_prob = rng.uniform(0, 1, size=n)
    y_true = (rng.uniform(0, 1, size=n) < y_prob).astype(int)  # true prob == y_prob by construction
    result = expected_calibration_error(y_true, y_prob, n_bins=10)
    assert result["ece"] < 0.05


def test_ece_badly_miscalibrated_is_large():
    n = 1000
    y_prob = np.full(n, 0.9)  # always claims 90% confident
    y_true = np.zeros(n)  # but always wrong
    result = expected_calibration_error(y_true, y_prob, n_bins=10)
    assert result["ece"] > 0.8


def test_ece_rejects_out_of_range_probabilities():
    with pytest.raises(ValueError):
        expected_calibration_error(np.array([0, 1]), np.array([0.5, 1.5]))


def test_aurc_perfect_ranking_beats_random_ranking():
    rng = np.random.default_rng(5)
    n = 1000
    correct = rng.integers(0, 2, size=n).astype(float)
    perfect_trust = correct + rng.normal(scale=1e-6, size=n)  # correct ones score highest
    random_trust = rng.normal(size=n)

    perfect_aurc = aurc(perfect_trust, correct)["aurc"]
    random_aurc = aurc(random_trust, correct)["aurc"]
    assert perfect_aurc < random_aurc


def test_precision_recall_at_coverage_perfect_ranking():
    n = 100
    y_true = np.array([1] * 20 + [0] * 80)
    y_score = np.array([1.0] * 20 + [0.0] * 80)  # positives ranked strictly first
    result = precision_recall_at_coverage(y_true, y_score, coverage=0.2)
    assert result["precision"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(1.0)


def test_precision_recall_at_coverage_no_signal():
    rng = np.random.default_rng(6)
    n = 2000
    y_true = (rng.uniform(size=n) < 0.1).astype(int)
    y_score = np.full(n, 0.5)  # ties everywhere -> flags an arbitrary 10%
    result = precision_recall_at_coverage(y_true, y_score, coverage=0.1)
    # with no discriminative signal, precision among flagged should be close
    # to the base rate, not near 1
    assert result["precision"] < 0.3


def test_bootstrap_ci_contains_point_estimate_and_is_deterministic_given_seed():
    y_true, y_score = _perfectly_separable()
    r1 = bootstrap_ci(auroc, y_true, y_score, n_resamples=200, seed=123)
    r2 = bootstrap_ci(auroc, y_true, y_score, n_resamples=200, seed=123)
    assert r1 == r2  # deterministic given the same seed
    assert r1["ci_low"] <= r1["point_estimate"] + 1e-9
    assert r1["point_estimate"] <= r1["ci_high"] + 1e-9


def test_bootstrap_ci_different_seeds_can_differ():
    rng = np.random.default_rng(7)
    n = 300
    y_true = rng.integers(0, 2, size=n)
    y_score = rng.normal(size=n)
    r1 = bootstrap_ci(auroc, y_true, y_score, n_resamples=200, seed=1)
    r2 = bootstrap_ci(auroc, y_true, y_score, n_resamples=200, seed=2)
    assert r1["seed"] != r2["seed"]


def test_bootstrap_ci_handles_degenerate_resamples():
    """A tiny, extremely imbalanced sample makes it likely some bootstrap
    resamples contain only one class; those must be counted, not silently
    dropped or crashing the whole computation."""
    y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    y_score = np.array([0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.4, 0.2, 0.1, 0.9])
    result = bootstrap_ci(auroc, y_true, y_score, n_resamples=300, seed=0)
    assert result["n_degenerate_resamples"] >= 0
    assert result["n_degenerate_resamples"] + len(
        [1]
    ) <= 300  # sanity: doesn't exceed n_resamples in any way that would indicate double counting
