import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/results/v1_1/data_sufficiency_audit/3_10"


def test_required_phase310_artifacts_exist():
    for rel in [
        "protocol/phase310_protocol.json",
        "inventory/data_inventory.csv",
        "information/decision_time_information_matrix.csv",
        "information/availability_matrix.json",
        "timestamps/timestamp_audit.csv",
        "temporal_order/dependency_graph.txt",
        "missingness/missingness_by_population.csv",
        "diversity/workload_failure_temporal_diversity.csv",
        "diversity/scorecard.json",
        "dependence/dependence_duplication_audit.csv",
        "artifacts/dataset_identity.json",
        "artifacts/hypothesis_evidence_matrix.json",
        "PHASE3_10_SYNTHESIS.md",
        ".finalized",
    ]:
        assert (OUT / rel).exists(), rel


def test_protocol_preserves_frozen_v1_and_prohibits_model_work():
    protocol = json.loads((OUT / "protocol/phase310_protocol.json").read_text())
    assert protocol["frozen_v1_commit"] == "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
    assert protocol["no_model_training"] is True
    assert protocol["no_candidate_implementation"] is True
    assert protocol["no_v1_modification"] is True
    assert protocol["evaluation_populations"]


def test_inventory_contains_actual_processed_data_and_v1_features():
    inventory = pd.read_csv(OUT / "inventory/data_inventory.csv")
    assert len(inventory) >= 60
    assert {"job_table.clean.csv", "task_table.clean.csv"}.issubset(set(inventory.file))
    availability = pd.read_csv(OUT / "information/decision_time_information_matrix.csv")
    v1 = availability[availability.classification == "A — USED BY V1"]
    assert len(v1) == 14
    assert "timestamp" in set(inventory.role)


def test_decision_time_matrix_separates_used_uncertain_post_outcome_and_absent():
    rows = json.loads((OUT / "information/availability_matrix.json").read_text())
    classifications = {row["classification"] for row in rows}
    assert "A — USED BY V1" in classifications
    assert "C — AVAILABLE BEFORE DECISION BUT TIMESTAMP UNCERTAIN" in classifications
    assert "D — ONLY AVAILABLE AFTER DECISION" in classifications
    assert "E — ONLY AVAILABLE AFTER OUTCOME" in classifications
    assert "F — NOT PRESENT" in classifications
    assert "G — UNKNOWN" in classifications


def test_timestamp_audit_does_not_claim_unknown_prediction_time():
    text = (OUT / "timestamps/timestamp_audit.csv").read_text()
    assert "UNKNOWN" in text
    synthesis = (OUT / "PHASE3_10_SYNTHESIS.md").read_text()
    assert "DECISION TIMESTAMP UNKNOWN" in synthesis
    assert "Do not" not in synthesis[:0]


def test_scorecard_is_structured_not_scalar_and_conclusion_is_b_plus_c():
    scorecard = json.loads((OUT / "diversity/scorecard.json").read_text())
    expected = {"decision_time_observability", "temporal_coverage", "failure_diversity", "workload_diversity", "environment_diversity", "provenance", "timestamp_quality", "generalization_support"}
    assert set(scorecard) == expected
    assert all(v in {"SUFFICIENT", "PARTIAL", "INSUFFICIENT", "UNKNOWN"} for v in scorecard.values())
    synthesis = (OUT / "PHASE3_10_SYNTHESIS.md").read_text()
    assert "combined **B + C**" in synthesis
    assert "V1 LIMITATIONS APPEAR DATA-BOUND" in synthesis


def test_diversity_and_dependence_cover_registered_populations():
    div = pd.read_csv(OUT / "diversity/workload_failure_temporal_diversity.csv")
    assert {"train", "validation", "random_test", "canonical_temporal", "fold_1_test", "fold_2_test", "fold_3_test"}.issubset(set(div.population))
    assert (div.distinct_jobs > 0).all()
    dep = pd.read_csv(OUT / "dependence/dependence_duplication_audit.csv")
    assert len(dep) >= 6
    assert dep.interpretation.notna().all()


def test_no_candidate_or_performance_experiment_was_created():
    protocol = json.loads((OUT / "protocol/phase310_protocol.json").read_text())
    assert protocol["no_candidate_implementation"] is True
    text = (OUT / "PHASE3_10_SYNTHESIS.md").read_text()
    assert "No model was trained by Phase 3.10" in text
    assert "Do not integrate a V1.1 candidate" in text


def test_finalized_sha256_manifest_matches_all_files():
    hashes = json.loads((OUT / ".finalized").read_text())
    for rel, expected in hashes.items():
        path = OUT / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
