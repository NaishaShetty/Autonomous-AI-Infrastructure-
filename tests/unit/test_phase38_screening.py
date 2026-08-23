import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/results/v1_1/candidate_screening/3_8"


def test_phase38_artifacts_and_independent_candidate_dirs_exist():
    assert (OUT / "protocol.json").exists()
    assert (OUT / "results.json").exists()
    assert (OUT / "summary.json").exists()
    assert (OUT / "PHASE3_8_SYNTHESIS.md").exists()
    assert (OUT / "candidate_a/report.md").exists()
    assert (OUT / "candidate_c/report.md").exists()
    assert (OUT / ".finalized").exists()


def test_protocol_freezes_v1_and_disallows_combination_and_search():
    protocol = json.loads((OUT / "protocol.json").read_text())
    assert protocol["frozen_v1_commit"] == "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
    assert protocol["candidates"] == ["candidate_a", "candidate_c"]
    assert protocol["combined_candidate"] is False
    assert protocol["no_search"] is True
    assert protocol["no_future_tuning"] is True
    assert protocol["feature_contract"] == [
        "job_start_time", "n_tasks", "n_distinct_task_names", "sum_inst_num",
        "mean_plan_cpu", "max_plan_cpu", "mean_plan_mem", "max_plan_mem",
        "mean_plan_gpu", "max_plan_gpu", "n_distinct_gpu_types", "n_instances",
        "n_distinct_machines", "mean_instance_start_time",
    ]


def test_both_candidates_use_all_registered_populations():
    results = json.loads((OUT / "results.json").read_text())
    expected = {"random_stratified", "canonical_temporal", "fold_1", "fold_2", "fold_3"}
    assert set(results["candidate_a"]) == expected
    assert set(results["candidate_c"]) == expected


def test_candidate_a_preserves_predictive_v1_outputs_and_records_actions():
    results = json.loads((OUT / "results.json").read_text())
    for value in results["candidate_a"].values():
        assert value["metrics"]["auroc"] == value["base_v1"]["auroc"]
        assert value["metrics"]["auprc"] == value["base_v1"]["auprc"]
        assert set(value["actions"]).issubset({"NORMAL", "REQUEST_EVIDENCE", "ESCALATE"})
        assert value["leakage_audit"]["future_labels_used"] is False
        assert value["leakage_audit"]["v1_predictor_modified"] is False


def test_candidate_c_is_prior_only_and_provenance_safe():
    results = json.loads((OUT / "results.json").read_text())
    for value in results["candidate_c"].values():
        audit = value["leakage_audit"]
        memory = value["memory_analysis"]
        assert audit["future_labels_used"] is False
        assert audit["memory_constructed_from_training_only"] is True
        assert audit["strict_timestamp_check"] is True
        assert audit["missing_provenance_used"] is False
        assert memory["strict_prior_only"] is True
        assert memory["empty_memory_rate"] >= 0.0


def test_required_metrics_and_multi_temporal_summary_exist():
    results = json.loads((OUT / "results.json").read_text())
    for cid in ("candidate_a", "candidate_c"):
        for value in results[cid].values():
            assert {"auroc", "auprc", "brier", "ece"}.issubset(value["metrics"])
            assert {"coverage", "selective_risk", "error_rate", "false_positive_rate", "false_negative_rate"}.issubset(value["decision"])
        summary = json.loads((OUT / "summary.json").read_text())[cid]
        assert {"mean_auroc_delta", "median_auroc_delta", "worst_auroc_delta", "best_auroc_delta", "wins", "losses", "ties"}.issubset(summary)


def test_final_decision_and_no_integration_are_explicit():
    text = (OUT / "PHASE3_8_SYNTHESIS.md").read_text()
    assert "BOTH CANDIDATES REQUIRE FURTHER STUDY" in text
    assert "V1 remains frozen" in text
    assert "Candidate A" in text and "Candidate C" in text
    assert "no integration is authorized" in text


def test_finalized_sha256_manifest_matches_all_files():
    hashes = json.loads((OUT / ".finalized").read_text())
    for rel, expected in hashes.items():
        path = OUT / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
