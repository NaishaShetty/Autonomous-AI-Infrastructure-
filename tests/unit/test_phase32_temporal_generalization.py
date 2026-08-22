import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "experiments/results/v1_1/temporal_generalization/stage_a_audit.json"
INTERVENTION = ROOT / "experiments/results/v1_1/temporal_generalization/stable_feature_filtering_time_features"


def test_stage_audit_covers_all_locked_features_and_populations():
    data = json.loads(AUDIT.read_text())
    assert len(data["feature_set"]) == 14
    assert "temporal_future_test" in data["populations"]
    assert set(data["feature_distribution_shift_train_to_future"]) == set(data["feature_set"])
    assert set(data["feature_target_drift_train_to_future"]) == set(data["feature_set"])


def test_stage_audit_records_phase31_negative_control():
    data = json.loads(AUDIT.read_text())
    assert data["phase31_reference"]["decision"] == "REJECT"
    assert data["phase31_reference"]["candidate"] == "GradientBoostingClassifier"


def test_intervention_is_finalized_and_rejected():
    data = json.loads((INTERVENTION / "summary.json").read_text())
    marker = json.loads((INTERVENTION / ".finalized").read_text())
    assert data["decision"] == "REJECT"
    assert "job_start_time" not in data["results"]["temporal"]["feature_set"]
    assert "mean_instance_start_time" not in data["results"]["temporal"]["feature_set"]
    for name, expected in marker.items():
        assert hashlib.sha256((INTERVENTION / name).read_bytes()).hexdigest() == expected


def test_intervention_temporal_result_is_not_accepted_as_improvement():
    data = json.loads((INTERVENTION / "results.json").read_text())["results"]["temporal"]
    assert data["candidate"]["metrics"]["auroc"] < data["v1_control"]["auroc"]
    assert data["candidate"]["metrics"]["brier_score"] > data["v1_control"]["brier_score"]
