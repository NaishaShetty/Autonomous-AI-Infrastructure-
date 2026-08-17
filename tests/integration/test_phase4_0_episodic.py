"""Integration test wrapper: runs the actual Phase 4.0 leakage-audit
checks (not a re-description of them) and asserts every check passes,
plus end-to-end structural assertions about the generated stream.
Mirrors tests/integration/test_phase3_6_leakage.py's pattern."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.data.episodic import generate_episode_stream, load_protocol
from src.evaluation.decision_policy import RiskTier

from benchmarks.phase4_0_leakage_audit import (
    check_chronological_no_future_leakage,
    check_determinism,
    check_no_duplicate_rows_within_combo,
    check_novel_combos_absent_from_train_and_validation,
    check_novel_combos_have_zero_known_history,
    check_regime2_thresholds_never_score_test_stream_rows,
    check_split_boundary_matches_protocol,
)

ROOT = Path(__file__).resolve().parents[2]


def _records():
    protocol = load_protocol()
    return generate_episode_stream(protocol).to_records(), protocol


def test_determinism():
    protocol = load_protocol()
    assert check_determinism(protocol)["passed"]


def test_no_duplicate_rows_within_combo():
    records, _ = _records()
    assert check_no_duplicate_rows_within_combo(records)["passed"]


def test_novel_combos_absent_from_train_and_validation():
    records, _ = _records()
    assert check_novel_combos_absent_from_train_and_validation(records)["passed"]


def test_novel_combos_have_zero_known_history():
    records, _ = _records()
    assert check_novel_combos_have_zero_known_history(records)["passed"]


def test_split_boundary_matches_protocol():
    records, protocol = _records()
    assert check_split_boundary_matches_protocol(records, protocol)["passed"]


def test_chronological_no_future_leakage():
    records, _ = _records()
    assert check_chronological_no_future_leakage(records)["passed"]


def test_no_regime_0_1_2_row_ever_emitted():
    records, _ = _records()
    assert check_regime2_thresholds_never_score_test_stream_rows(records)["passed"]


def test_full_audit_all_passed():
    """End-to-end: the actual audit script's own run, all checks."""
    report_path = ROOT / "experiments" / "results" / "phase4_0" / "leakage_audit.json"
    if not report_path.exists():
        subprocess.run(["python", "benchmarks/phase4_0_leakage_audit.py"], cwd=ROOT, check=True)
    report = json.loads(report_path.read_text())
    assert report["all_passed"] is True


def test_expected_combo_and_split_counts():
    records, protocol = _records()
    n_known = len(protocol["workloads"]) * len(protocol["conditions"]) - len(protocol["novel_combos"])
    n_novel = len(protocol["novel_combos"])
    batch = protocol["recurrence"]["batch_size"]
    known_occ = protocol["recurrence"]["known_combo_occurrences"]
    novel_occ = protocol["recurrence"]["novel_combo_occurrences"]

    expected_total = n_known * known_occ * batch + n_novel * novel_occ * batch
    assert len(records) == expected_total

    expected_train = n_known * (known_occ - 2) * batch
    expected_validation = n_known * batch
    expected_test = n_known * batch + n_novel * novel_occ * batch

    by_split = {"train": 0, "validation": 0, "test": 0}
    for r in records:
        by_split[r["split"]] += 1
    assert by_split["train"] == expected_train
    assert by_split["validation"] == expected_validation
    assert by_split["test"] == expected_test


def test_every_context_has_all_feature_names():
    from src.data.synthetic import FEATURE_NAMES

    records, _ = _records()
    for r in records[:50]:
        assert set(r["context"].keys()) == set(FEATURE_NAMES)


def test_decision_matches_tier_via_frozen_mapping():
    from src.evaluation.decision_policy import TIER_ACTION

    records, _ = _records()
    for r in records:
        assert r["decision"] == TIER_ACTION[RiskTier(r["tier"])].value


def test_recovery_only_attempted_for_critical_tier():
    records, _ = _records()
    for r in records:
        if r["tier"] == RiskTier.CRITICAL.value:
            assert r["recovery_attempted"] is True
        else:
            assert r["recovery_attempted"] is False
            assert r["recovery_action"] is None


def test_outcome_matches_prediction_vs_true_label():
    records, _ = _records()
    for r in records:
        expected = "INCORRECT" if r["predicted_label"] != r["true_label"] else "CORRECT"
        assert r["outcome"] == expected
        assert r["is_failure"] == (expected == "INCORRECT")
