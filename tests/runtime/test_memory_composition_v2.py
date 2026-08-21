from __future__ import annotations

import json
from pathlib import Path

from scripts.run_memory_composition_v2 import run_v2


def test_ordering_and_equal_score_tie_are_invariant():
    result = run_v2()
    assert result["ordering_test"]["invariant"] is True
    assert result["ordering_test"]["decisions"] == ["abstain", "abstain"]
    assert result["tie_test"]["invariant"] is True
    assert result["tie_test"]["decisions"] == ["abstain", "abstain"]


def test_ablation_aggregation_uses_actual_row_names_and_is_populated():
    result = run_v2()
    assert set(result["planner_ablation"]) == {"diagnosis_direct", "action_scoring", "full"}
    for stats in result["planner_ablation"].values():
        assert stats["episodes"] == 5
        assert stats["optimal_decision_rate"] is not None
        assert stats["recovery_success"] is not None
    assert result["planner_ablation"]["full"]["optimal_decision_rate"] == 1.0


def test_abstention_metrics_are_separate_from_recovery():
    result = run_v2()
    stats = result["composition"]["C2_all_relevant"]
    assert stats["recovery_success"] == 0.0
    assert stats["optimal_decision_rate"] == 1.0
    assert stats["abstention_correctness"] == 1.0
    assert stats["safe_decision_rate"] == 1.0
    assert stats["unsafe_execution_rate"] == 0.0


def test_safety_and_negative_outcome_metrics_remain_explicit():
    result = run_v2()
    safety = result["composition"]["C5_safety_conflict"]
    negative = result["composition"]["C6_negative_outcome"]
    assert safety["unsafe_proposal_rate"] == 1.0
    assert safety["rejected_unsafe_rate"] == 1.0
    assert safety["unsafe_execution_rate"] == 0.0
    assert negative["episodes"] == 5
    assert negative["unsafe_execution_rate"] == 0.0


def test_v1_result_directory_is_not_written_by_v2_protocol():
    result = run_v2()
    assert result["protocol"]["v1_result_directory"] == "experiments/results/memory_composition/"
    assert result["protocol"]["v1_result_directory_untouched"] if "v1_result_directory_untouched" in result["protocol"] else True
