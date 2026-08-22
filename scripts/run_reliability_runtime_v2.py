"""Train and evaluate the registered Alibaba GPU2020 v2 reliability artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.reliability.artifact_model import EncodedWorkloadRiskModel
from src.reliability.artifacts import save_reliability_artifact, load_reliability_artifact
from src.reliability.evaluation import evaluate_predictions, calibration_metrics, abstention_metrics
from src.reliability.risk_calibrator import IsotonicRiskCalibrator

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/reliability_runtime_v2"
SEED = 42


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def created_at() -> str:
    return subprocess.check_output(["git", "show", "-s", "--format=%cI", commit()], cwd=ROOT, text=True).strip()


def baseline(labels: np.ndarray, score: np.ndarray) -> dict:
    return evaluate_predictions(labels.tolist(), score.tolist())


def run_split(df, split_name: str, split: dict, artifact_dir: Path) -> dict:
    train_ids, val_ids, test_ids = (set(split[key]) for key in ("train", "val", "test"))
    if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
        raise RuntimeError("job identities overlap across split boundaries")
    train, val, test = (df[df.job_name.isin(ids)].copy() for ids in (train_ids, val_ids, test_ids))
    model = EncodedWorkloadRiskModel(list(NUMERIC_COLS), random_state=SEED).fit(train[NUMERIC_COLS].to_numpy(), train.label.to_numpy())
    val_raw = np.asarray([model.predict_failure_risk(row) for row in val[NUMERIC_COLS].to_numpy()])
    test_raw = np.asarray([model.predict_failure_risk(row) for row in test[NUMERIC_COLS].to_numpy()])
    calibrator = IsotonicRiskCalibrator(random_state=SEED).fit_validation(val_raw.tolist(), val.label.astype(int).tolist())
    val_cal = np.asarray([calibrator.calibrate_risk(x) for x in val_raw])
    test_cal = np.asarray([calibrator.calibrate_risk(x) for x in test_raw])
    candidates = np.linspace(0.05, 0.50, 10)
    threshold = min(candidates, key=lambda t: ((abstention_metrics(val.label, val_cal, accept_risk_threshold=float(t))["selective_risk"] or 1.0), -abstention_metrics(val.label, val_cal, accept_risk_threshold=float(t))["coverage"]))
    labels = test.label.astype(int).to_numpy()
    model_metrics = {"raw": baseline(labels, test_raw), "calibrated": baseline(labels, test_cal), "calibration": calibration_metrics(labels, test_cal), "abstention": abstention_metrics(labels, test_cal, accept_risk_threshold=float(threshold))}
    b0 = baseline(labels, np.full(len(labels), train.label.mean()))
    b1_cut = float(train.max_plan_gpu.median())
    b1 = baseline(labels, (test.max_plan_gpu.fillna(b1_cut).to_numpy() >= b1_cut).astype(float))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest = save_reliability_artifact(artifact_dir, model, calibrator, artifact_version="reliability-runtime-v2-artifact-1", model_id="alibaba-gpu2020-job-risk-logistic", model_version="v2.0.0", calibrator_version="isotonic-v2.0.0", feature_schema_version="alibaba-gpu2020-request-scheduling-v1", feature_names=list(NUMERIC_COLS), training_dataset_id=f"alibaba_gpu2020_main_{split_name}_train", validation_dataset_id=f"alibaba_gpu2020_main_{split_name}_validation", evaluation_dataset_id=f"alibaba_gpu2020_main_{split_name}_evaluation", training_timestamp=created_at(), repository_commit=commit(), protocol_version="reliability-runtime-v2", protocol_hash=sha256(OUT / "protocol.json"), evaluation_metrics=model_metrics["calibrated"], calibration_metrics=model_metrics["calibration"], created_at=created_at())
    loaded = load_reliability_artifact(artifact_dir, expected_feature_names=list(NUMERIC_COLS), expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0")
    sample = test[NUMERIC_COLS].iloc[0].to_numpy(dtype=float)
    before = model.predict(sample)
    after = loaded.model.predict(sample)
    same_output = before == after
    return {"split": split_name, "counts": {"train": len(train), "validation": len(val), "evaluation": len(test)}, "train_failed_rate": float(train.label.mean()), "validation_failed_rate": float(val.label.mean()), "evaluation_failed_rate": float(labels.mean()), "feature_names": list(NUMERIC_COLS), "excluded_tables": ["pai_sensor_table", "pai_machine_metric"], "excluded_fields": ["status", "end_time", "max_mem", "max_gpu_wrk_mem"], "baselines": {"B0_base_rate": b0, "B1_single_threshold": {**b1, "threshold": b1_cut}}, "model": {"B2_logistic_regression_raw": model_metrics["raw"], "B2_logistic_regression_calibrated": model_metrics["calibrated"], "calibration": model_metrics["calibration"], "abstention": model_metrics["abstention"]}, "artifact": {"manifest": manifest.to_dict(), "reload_verified": loaded.manifest.artifact_sha256 == manifest.artifact_sha256, "same_input_same_output": same_output}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix()
    with (ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json").open() as f:
        random_split = json.load(f)
    with (ROOT / "data/audit/alibaba_gpu2020/splits_temporal.json").open() as f:
        temporal_split = json.load(f)
    results = {"experiment_id": "reliability_runtime_v2", "dataset": "alibaba_gpu2020", "repository_commit": commit(), "protocol_sha256": sha256(OUT / "protocol.json"), "dataset_manifest_sha256": sha256(ROOT / "data/audit/alibaba_gpu2020/dataset_manifest.json"), "results": {"random_stratified": run_split(df, "random_stratified", random_split, OUT / "artifacts/random"), "temporal": run_split(df, "temporal", temporal_split, OUT / "artifacts/temporal")}}
    for name in ("results.json", "summary.json"):
        (OUT / name).write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (OUT / "manifest.json").write_text(json.dumps({"experiment_id": "reliability_runtime_v2", "repository_commit": commit(), "protocol_sha256": results["protocol_sha256"], "dataset_manifest_sha256": results["dataset_manifest_sha256"], "status": "completed", "seed": SEED}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "completed", "protocol_sha256": results["protocol_sha256"], "repository_commit": commit()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
