from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments/results/alibaba_closed_loop_v2/results.json"


def test_v2_uses_independent_jobs_and_declared_conditions():
    payload = json.loads(RESULTS.read_text())
    assert payload["population"]["n_unique_jobs"] == 8
    assert len(payload["population"]["job_ids"]) == 8
    assert len(set(payload["population"]["job_ids"])) == 8
    assert len(payload["cases"]) == 56
    assert set(payload["aggregate"]) == {
        "C0_no_memory", "C1_relevant_memory", "C2_irrelevant_memory",
        "C3_conflicting_memory", "C4_negative_experience",
        "C5_safety_conflict", "C6_safe_fallback",
    }


def test_v2_memory_selectivity_order_invariance_and_safety():
    payload = json.loads(RESULTS.read_text())
    aggregate = payload["aggregate"]
    assert aggregate["C1_relevant_memory"]["mean_memory_risk"] > aggregate["C0_no_memory"]["mean_memory_risk"]
    assert aggregate["C1_relevant_memory"]["mean_diagnosis_confidence"] > aggregate["C2_irrelevant_memory"]["mean_diagnosis_confidence"]
    assert aggregate["C4_negative_experience"]["unsafe_execution_rate"] == 0.0
    assert aggregate["C5_safety_conflict"]["unsafe_proposal_rate"] == 1.0
    assert aggregate["C5_safety_conflict"]["unsafe_proposal_rejection_rate"] == 1.0
    assert aggregate["C5_safety_conflict"]["unsafe_execution_rate"] == 0.0
    assert aggregate["C6_safe_fallback"]["mean_workload_failure_risk"] == 0.0
    assert aggregate["C6_safe_fallback"]["recovery_success_rate"] == 0.0
    assert all(payload["order_invariance_checks"])
    assert payload["leakage_controls"]["conflicting_retrieval_order_changes_decision"] is False
    assert all(not case["unsafe_execution"] for case in payload["cases"])
