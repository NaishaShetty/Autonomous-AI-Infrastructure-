"""Unit tests for src/patterns/discovery.py and metrics.py: tier
assignment logic, candidacy rule, row-level metrics, empty-input
handling."""
from __future__ import annotations

import dataclasses

from src.patterns.discovery import assign_tier, discover_candidates, temporal_clustering_report
from src.patterns.metrics import evaluate_rows, tier_level_true_structure_rate
from src.patterns.schema import EvidenceTier, PatternCandidate, PatternQuery

THRESHOLDS = {
    "MIN_OBSERVATIONS_FOR_TRUSTED_PURITY": 3,
    "CONFIRMED_MIN_N": 6,
    "TAU_INFERRED": 0.6,
    "TAU_CONFIRMED": 0.8,
    "TAU_CONFIRMED_VALIDATION": 0.5,
}


def _row(workload_id, diagnosed_cause, condition_id, split, is_failure=True, recovery_attempted=False, recovery_outcome=None, recovery_correct=None, step=0, occurrence_ordinal=0, is_novel_combo=False):
    return {
        "workload_id": workload_id, "diagnosed_cause": diagnosed_cause, "condition_id": condition_id,
        "split": split, "is_failure": is_failure, "recovery_attempted": recovery_attempted,
        "recovery_outcome": recovery_outcome, "recovery_correct": recovery_correct,
        "step": step, "occurrence_ordinal": occurrence_ordinal, "is_novel_combo": is_novel_combo,
    }


def test_pattern_query_has_no_ground_truth_or_outcome_fields():
    field_names = {f.name for f in dataclasses.fields(PatternQuery)}
    forbidden = {"condition_id", "true_label", "outcome", "is_failure", "recovery_action", "recovery_outcome", "recovery_correct"}
    assert field_names.isdisjoint(forbidden)


def test_assign_tier_confirmed_requires_validation_replication():
    tier = assign_tier(n_train=6, purity_train=0.9, n_validation=1, purity_validation=0.9, thresholds=THRESHOLDS)
    assert tier == EvidenceTier.CONFIRMED


def test_assign_tier_confirmed_fails_without_validation_data():
    tier = assign_tier(n_train=6, purity_train=0.9, n_validation=0, purity_validation=None, thresholds=THRESHOLDS)
    assert tier != EvidenceTier.CONFIRMED
    assert tier == EvidenceTier.INFERRED  # purity still clears TAU_INFERRED


def test_assign_tier_confirmed_fails_if_validation_does_not_replicate():
    tier = assign_tier(n_train=6, purity_train=0.9, n_validation=2, purity_validation=0.2, thresholds=THRESHOLDS)
    assert tier == EvidenceTier.INFERRED


def test_assign_tier_uncertain_for_small_n_and_low_purity():
    tier = assign_tier(n_train=2, purity_train=0.5, n_validation=0, purity_validation=None, thresholds=THRESHOLDS)
    assert tier == EvidenceTier.UNCERTAIN


def test_assign_tier_observed_for_trusted_n_but_low_purity():
    tier = assign_tier(n_train=4, purity_train=0.5, n_validation=0, purity_validation=None, thresholds=THRESHOLDS)
    assert tier == EvidenceTier.OBSERVED


def test_candidacy_rule_excludes_singletons():
    train = [_row("w1", "clean", "clean", "train")]  # n_train == 1
    val = []
    candidates = discover_candidates(train, val, THRESHOLDS, "v1", "hash")
    assert candidates == []


def test_discover_candidates_is_deterministic():
    train = [
        _row("w1", "clean", "clean", "train"),
        _row("w1", "clean", "clean", "train"),
        _row("w1", "clean", "feature_noise_mild", "train"),
    ]
    val = [_row("w1", "clean", "clean", "validation")]
    a = discover_candidates(train, val, THRESHOLDS, "v1", "hash")
    b = discover_candidates(train, val, THRESHOLDS, "v1", "hash")
    assert [(c.workload_id, c.diagnosed_cause, c.tier) for c in a] == [(c.workload_id, c.diagnosed_cause, c.tier) for c in b]


def test_discover_candidates_computes_correct_mode_and_purity():
    train = [
        _row("w1", "clean", "clean", "train"),
        _row("w1", "clean", "clean", "train"),
        _row("w1", "clean", "feature_noise_mild", "train"),
    ]
    candidates = discover_candidates(train, [], THRESHOLDS, "v1", "hash")
    assert len(candidates) == 1
    c = candidates[0]
    assert c.n_train == 3
    assert c.mode_condition_train == "clean"
    assert abs(c.purity_train - (2 / 3)) < 1e-9


def test_evaluate_rows_empty_candidates_returns_none_metrics():
    result = evaluate_rows([], {}, lambda c: True)
    assert result["n_covered"] == 0
    assert result["precision"] is None
    assert result["recall"] is None


def test_evaluate_rows_precision_and_recall():
    candidate = PatternCandidate(
        workload_id="w1", diagnosed_cause="clean", n_train=5, mode_condition_train="clean",
        purity_train=0.8, n_validation=1, purity_validation=1.0, tier=EvidenceTier.CONFIRMED,
        protocol_version="v1", dataset_content_hash="hash",
    )
    by_key = {("w1", "clean"): candidate}
    test_rows = [
        _row("w1", "clean", "clean", "test"),  # true structure
        _row("w1", "clean", "feature_noise_mild", "test"),  # not true structure
    ]
    result = evaluate_rows(test_rows, by_key, lambda c: True)
    assert result["n_covered"] == 2
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0


def test_evaluate_rows_uncovered_rows_excluded():
    test_rows = [_row("w_unknown", "clean", "clean", "test")]
    result = evaluate_rows(test_rows, {}, lambda c: True)
    assert result["n_covered"] == 0
    assert result["coverage_rate"] == 0.0


def test_tier_level_true_structure_rate_reports_all_four_tiers():
    candidate = PatternCandidate(
        workload_id="w1", diagnosed_cause="clean", n_train=5, mode_condition_train="clean",
        purity_train=0.8, n_validation=1, purity_validation=1.0, tier=EvidenceTier.INFERRED,
        protocol_version="v1", dataset_content_hash="hash",
    )
    by_key = {("w1", "clean"): candidate}
    test_rows = [_row("w1", "clean", "clean", "test")]
    out = tier_level_true_structure_rate(test_rows, by_key)
    assert set(out.keys()) == {"OBSERVED", "INFERRED", "CONFIRMED", "UNCERTAIN"}
    assert out["INFERRED"]["n"] == 1
    assert out["INFERRED"]["true_structure_rate"] == 1.0
    assert out["CONFIRMED"]["n"] == 0
    assert out["CONFIRMED"]["true_structure_rate"] is None


def test_temporal_clustering_report_computes_gaps():
    records = [
        _row("w1", None, "clean", "train", step=0, occurrence_ordinal=0, is_novel_combo=False),
        _row("w1", None, "clean", "train", step=10, occurrence_ordinal=1, is_novel_combo=False),
        _row("w1", None, "clean", "test", step=20, occurrence_ordinal=2, is_novel_combo=False),
    ]
    # temporal_clustering_report groups by (workload_id, condition_id), records' own condition_id used as key
    for r in records:
        r["condition_id"] = "clean"
    report = temporal_clustering_report(records, {})
    assert "w1|clean" in report
    assert report["w1|clean"]["gaps"] == [10, 10]
    assert report["w1|clean"]["gap_variance"] == 0.0
