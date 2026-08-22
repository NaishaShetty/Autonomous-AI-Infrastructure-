from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments/results/alibaba_closed_loop_v1/results.json"


def test_alibaba_closed_loop_trace_is_complete_and_leakage_safe():
    rows = {row["condition"]: row for row in json.loads(RESULTS.read_text())["conditions"]}
    assert set(rows) == {"C0_artifact_only", "C1_relevant_prior_experience", "C2_irrelevant_prior_experience", "C4_safety_conflict"}
    for row in rows.values():
        assert row["source_type"] == "dataset_replay"
        assert row["artifact_hash"]
        assert row["model_version"] == "v2.0.0"
        assert "workload_failure_risk" in row
        assert "memory_risk" in row
        assert "uncertainty" in row
        assert "diagnosis" in row
        assert "validation" in row
        assert row["unsafe_execution"] is False
    assert rows["C0_artifact_only"]["retrieved_experiences"] == 0
    assert rows["C1_relevant_prior_experience"]["memory_risk"] > rows["C0_artifact_only"]["memory_risk"]
    assert rows["C1_relevant_prior_experience"]["diagnosis"]["confidence"] > rows["C2_irrelevant_prior_experience"]["diagnosis"]["confidence"]
    assert rows["C4_safety_conflict"]["safety_decision"] == "rejected"
    assert rows["C4_safety_conflict"]["unsafe_proposal"] is True
    assert rows["C4_safety_conflict"]["unsafe_execution"] is False
    controls = json.loads(RESULTS.read_text())["leakage_controls"]
    assert all(value is False for value in controls.values())
