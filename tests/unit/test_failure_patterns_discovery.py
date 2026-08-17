import pytest

from src.failure_patterns import discovery_alibaba as da
from src.failure_patterns import metrics as pm
from src.failure_patterns.schema import EvidenceTier, AlibabaTestOutcome

PROTOCOL = {
    "minimum_evidence_thresholds": {"N_MIN_CANDIDATE": 5, "N_MIN_TRUSTED": 20},
    "rate_elevation_criterion": {
        "MARGIN_TRAIN": 0.10,
        "MARGIN_VALIDATION": 0.05,
        "N_MIN_VALIDATION": 5,
    },
}


def _rows(task_name, gpu_type, split, n, n_failed):
    n_terminated = n - n_failed
    return (
        [{"task_name": task_name, "gpu_type": gpu_type, "status": "Failed", "split": split} for _ in range(n_failed)]
        + [{"task_name": task_name, "gpu_type": gpu_type, "status": "Terminated", "split": split} for _ in range(n_terminated)]
    )


def test_candidacy_floor_excludes_below_n_min_candidate():
    rows = _rows("t", "g", "train", n=4, n_failed=1)  # below N_MIN_CANDIDATE=5
    discovered = da.discover(rows, PROTOCOL)
    assert ("t", "g") not in discovered


def test_uncertain_tier_below_n_min_trusted():
    # n=10, above candidacy(5) but below trusted(20)
    rows = _rows("t", "g", "train", n=10, n_failed=5)  # rate 0.5, elevated but too few to trust
    discovered = da.discover(rows, PROTOCOL)
    assert discovered[("t", "g")]["provisional_tier"] == EvidenceTier.UNCERTAIN


def test_observed_tier_trusted_n_no_elevation():
    # baseline is computed over all rows in this call; build population so
    # this context's rate ~= baseline, no elevation.
    rows = _rows("t", "g", "train", n=30, n_failed=6)  # rate 0.2
    rows += _rows("other", "g2", "train", n=30, n_failed=6)  # same rate, pool baseline = 0.2
    discovered = da.discover(rows, PROTOCOL)
    assert discovered[("t", "g")]["provisional_tier"] == EvidenceTier.OBSERVED


def test_inferred_tier_when_elevation_clears_margin():
    rows = _rows("hot", "g", "train", n=30, n_failed=15)  # rate 0.5
    rows += _rows("cold", "g2", "train", n=30, n_failed=3)  # rate 0.1 -- pulls baseline down
    discovered = da.discover(rows, PROTOCOL)
    baseline = discovered[("hot", "g")]["train_baseline_rate"]
    assert baseline == pytest.approx(18 / 60)
    assert discovered[("hot", "g")]["provisional_tier"] == EvidenceTier.INFERRED


def test_confirm_upgrades_inferred_to_confirmed_on_replication():
    rows = _rows("hot", "g", "train", n=30, n_failed=15)
    rows += _rows("cold", "g2", "train", n=30, n_failed=3)
    discovered = da.discover(rows, PROTOCOL)

    val_rows = _rows("hot", "g", "val", n=10, n_failed=6)  # rate 0.6
    val_rows += _rows("cold", "g2", "val", n=10, n_failed=1)  # baseline ~0.05
    confirmed = da.confirm(discovered, val_rows, PROTOCOL)
    assert confirmed[("hot", "g")]["tier"] == EvidenceTier.CONFIRMED


def test_confirm_keeps_inferred_when_validation_insufficient():
    rows = _rows("hot", "g", "train", n=30, n_failed=15)
    rows += _rows("cold", "g2", "train", n=30, n_failed=3)
    discovered = da.discover(rows, PROTOCOL)

    val_rows = _rows("hot", "g", "val", n=2, n_failed=1)  # below N_MIN_VALIDATION=5
    val_rows += _rows("cold", "g2", "val", n=10, n_failed=1)
    confirmed = da.confirm(discovered, val_rows, PROTOCOL)
    assert confirmed[("hot", "g")]["tier"] == EvidenceTier.INFERRED


def test_confirm_keeps_inferred_when_validation_does_not_replicate():
    rows = _rows("hot", "g", "train", n=30, n_failed=15)
    rows += _rows("cold", "g2", "train", n=30, n_failed=3)
    discovered = da.discover(rows, PROTOCOL)

    # validation rate == validation baseline -> no elevation
    val_rows = _rows("hot", "g", "val", n=10, n_failed=2)
    val_rows += _rows("cold", "g2", "val", n=10, n_failed=2)
    confirmed = da.confirm(discovered, val_rows, PROTOCOL)
    assert confirmed[("hot", "g")]["tier"] == EvidenceTier.INFERRED


def test_discover_rejects_non_train_split_rows():
    rows = _rows("t", "g", "test", n=10, n_failed=5)
    with pytest.raises(AssertionError):
        da.discover(rows, PROTOCOL)


def test_confirm_rejects_non_validation_split_rows():
    with pytest.raises(AssertionError):
        da.confirm({}, [{"task_name": "t", "gpu_type": "g", "status": "Failed", "split": "train"}], PROTOCOL)


def test_baseline_b_flags_purely_on_train_count():
    from src.failure_patterns.schema import PatternCandidate

    low_n = PatternCandidate(
        task_name="a", gpu_type="x", n_train=10, train_rate=0.9, train_baseline_rate=0.2,
        n_validation=0, validation_rate=None, validation_baseline_rate=None,
        tier=EvidenceTier.UNCERTAIN, protocol_version="t", dataset_content_hash="h", split_name="temporal",
    )
    high_n = PatternCandidate(
        task_name="b", gpu_type="y", n_train=25, train_rate=0.2, train_baseline_rate=0.2,
        n_validation=0, validation_rate=None, validation_baseline_rate=None,
        tier=EvidenceTier.OBSERVED, protocol_version="t", dataset_content_hash="h", split_name="temporal",
    )
    flagged = pm.flag_baseline_b([low_n, high_n], n_min_trusted=20)
    assert flagged == {("b", "y")}


def test_rate_elevation_metrics_precision_recall():
    outcomes = {
        ("a", "x"): AlibabaTestOutcome(task_name="a", gpu_type="x", n_test=10, test_rate=0.5, test_baseline_rate=0.2),
        ("b", "y"): AlibabaTestOutcome(task_name="b", gpu_type="y", n_test=10, test_rate=0.21, test_baseline_rate=0.2),
    }
    all_test = dict(outcomes)
    flagged = {("a", "x"), ("b", "y")}
    m = pm.rate_elevation_metrics(flagged, outcomes, all_test, margin_train=0.10)
    assert m["precision"] == pytest.approx(0.5)
    assert m["recall"] == pytest.approx(1.0)
    assert m["false_pattern_rate"] == pytest.approx(0.5)
