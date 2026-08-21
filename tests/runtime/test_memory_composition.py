from __future__ import annotations

import hashlib
import json

from scripts.run_memory_composition import PROTOCOL, discrimination_check, run_all, write_outputs


def test_protocol_declares_partial_training_and_unseen_composition():
    assert {"X_resource_pressure", "Y_latency_congestion", "Z_configuration_drift"} <= set(PROTOCOL["latent_factors"])
    assert set(PROTOCOL["conditions"]["C2_all_relevant"]) == {"E1_X_only", "E3_Z_only"}
    assert PROTOCOL["evaluation_cases"]["COMP_XZ_unseen"]["factors"] == ["X_resource_pressure", "Z_configuration_drift"]
    assert PROTOCOL["max_recovery_attempts"] == 1


def test_discrimination_check_passes_before_evaluation():
    check = discrimination_check()
    assert check["passed"] is True
    assert check["checks"]["nearest_only_is_insufficient"] is True
    assert check["checks"]["combined_b2_is_sufficient"] is True
    assert check["checks"]["latent_factors_hidden"] is True
    assert check["checks"]["optimal_action_hidden"] is True


def test_composition_changes_decision_and_measures_b1_b2_separately():
    result = run_all()
    c1 = result["composition"]["C1_nearest_only"]
    c2 = result["composition"]["C2_all_relevant"]
    assert c1["optimal_action_rate"] == 0.0
    assert c2["optimal_action_rate"] == 1.0
    assert c2["action_disagreement_rate"] == 1.0
    assert result["planner_advantage"]["optimal_action_delta"] == 1.0


def test_evidence_ablation_contains_none_single_and_combined():
    result = run_all()
    assert set(result["evidence_ablation"]) == {"E1_only", "E3_only", "E1_plus_E3", "none"}
    assert result["evidence_ablation"]["E1_plus_E3"]["optimal_action_rate"] == 1.0
    assert result["evidence_ablation"]["E1_only"]["optimal_action_rate"] == 0.0
    assert result["evidence_ablation"]["E3_only"]["optimal_action_rate"] == 0.0


def test_safety_separates_proposed_rejected_and_executed_unsafe_actions():
    result = run_all()
    safety = result["composition"]["C5_safety_conflict"]
    assert safety["proposed_unsafe_actions"] == 1.0
    assert safety["rejected_unsafe_actions"] == 1.0
    assert safety["executed_unsafe_actions"] == 0.0
    assert safety["abstention_rate"] == 1.0


def test_ordering_robustness_is_measured_after_runtime_fix():
    result = run_all()
    ordering = result["ordering_test"]
    assert ordering["decisions"]
    assert ordering["invariant"] is True
    assert set(ordering["decisions"]) == {"abstain"}


def test_negative_transfer_and_conflict_are_reported_without_hidden_labels():
    result = run_all()
    negative = result["composition"]["C6_negative_outcome"]
    conflict = result["composition"]["C4_conflicting"]
    assert negative["episodes"] == len(PROTOCOL["seed_list"])
    assert conflict["episodes"] == len(PROTOCOL["seed_list"])
    for row in result["records"]:
        assert row["latent_factors_exposed_to_runtime"] is False
        assert row["optimal_action_exposed_to_runtime"] is False


def test_per_seed_summary_is_condition_specific():
    result = run_all()
    for seed in map(str, PROTOCOL["seed_list"]):
        assert set(result["per_seed_summary"][seed]) >= {"C0_no_memory", "C1_nearest_only", "C2_all_relevant"}
        assert result["per_seed_summary"][seed]["C2_all_relevant"]["episodes"] == 4


def test_deterministic_ids_and_byte_reproducibility(tmp_path):
    result = run_all()
    import scripts.run_memory_composition as experiment
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir(); second.mkdir()
    old = experiment.RESULTS
    try:
        experiment.RESULTS = first
        write_outputs(result)
        experiment.RESULTS = second
        write_outputs(run_all())
    finally:
        experiment.RESULTS = old
    for filename in ("protocol.json", "manifest.json", "results.json", "summary.json", "report.md"):
        assert hashlib.sha256((first / filename).read_bytes()).digest() == hashlib.sha256((second / filename).read_bytes()).digest()
    assert sorted(path.name for path in (first / "per_seed").iterdir()) == sorted(f"seed_{seed}.json" for seed in PROTOCOL["seed_list"])


def test_result_rows_do_not_include_hidden_ground_truth():
    result = run_all()
    forbidden = {"latent_mechanism", "latent_factors", "action_score", "simulator_probability"}
    for row in result["records"]:
        assert not (forbidden & set(row["features"]))
        assert row["latent_factors_exposed_to_runtime"] is False
        assert row["optimal_action_exposed_to_runtime"] is False
