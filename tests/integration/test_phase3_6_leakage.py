"""Integration test wrapper: runs the actual Phase 3.6 leakage-audit
checks (not a re-description of them) and asserts every check passes.
Mirrors the pattern used for Phase 3.1/3.5's leakage audits."""
from __future__ import annotations

from src.evaluation.protocol import Phase31Protocol
from src.pipeline_builder import build_system

from benchmarks.phase3_3_generalization import _fit_frozen_candidate, _reconstruct_regime2_with_confidences
from benchmarks.phase3_6_complementarity import _fit_combined
from benchmarks.phase3_6_leakage_audit import (
    check_cost_model_matches_frozen_protocol,
    check_diagnosis_is_deterministic_and_unfit,
    check_diagnosis_precedes_outcome_check_in_recovery,
    check_duplicate_samples_regime2_vs_test,
    check_recovery_policy_no_fit_calls,
    check_seeds_unchanged,
    check_threshold_and_complementarity_fit_only_on_regime2,
    check_tier_assignment_does_not_use_ground_truth,
)

SEED = 1
SMALL_REGIME_SIZES = (300, 150, 150, 150, 150)


def _built():
    protocol = Phase31Protocol.load()
    protocol.regime_sizes = SMALL_REGIME_SIZES
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=SEED)
    regime2 = _reconstruct_regime2_with_confidences(SEED, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, SEED)
    combined = _fit_combined(regime2, candidate_f, SEED)
    return system, regime2, candidate_f, combined


def test_threshold_and_complementarity_fit_only_on_regime2():
    system, regime2, candidate_f, combined = _built()
    assert check_threshold_and_complementarity_fit_only_on_regime2(system, regime2, candidate_f, combined)["passed"]


def test_cost_model_matches_frozen_protocol():
    assert check_cost_model_matches_frozen_protocol()["passed"]


def test_tier_assignment_does_not_use_ground_truth():
    assert check_tier_assignment_does_not_use_ground_truth()["passed"]


def test_diagnosis_is_deterministic_and_unfit():
    assert check_diagnosis_is_deterministic_and_unfit()["passed"]


def test_recovery_policy_no_fit_calls():
    assert check_recovery_policy_no_fit_calls()["passed"]


def test_diagnosis_precedes_outcome_check_in_recovery():
    assert check_diagnosis_precedes_outcome_check_in_recovery()["passed"]


def test_seeds_unchanged():
    assert check_seeds_unchanged()["passed"]


def test_duplicate_samples_regime2_vs_test():
    system, regime2, _, _ = _built()
    assert check_duplicate_samples_regime2_vs_test(system, regime2)["passed"]


def test_full_audit_all_passed_on_primary_seed():
    """End-to-end: the actual audit script's own seed-42 run, all checks."""
    import json
    from pathlib import Path
    report_path = Path(__file__).resolve().parents[2] / "experiments" / "results" / "phase3_6" / "leakage_audit.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(["python", "benchmarks/phase3_6_leakage_audit.py"], cwd=Path(__file__).resolve().parents[2], check=True)
    report = json.loads(report_path.read_text())
    assert report["all_passed"] is True
