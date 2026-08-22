"""Phase 3.1 model-only reliability experiment.

The frozen V1 feature builder, splits, calibration data boundary, and evaluation
metrics are reused. The only intervention is replacing V1 logistic regression
with a deterministic GradientBoostingClassifier over the same 14 numeric
features. Outputs are written only to experiments/results/v1_1/.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.reliability.evaluation import calibration_metrics, abstention_metrics

OUT = ROOT / "experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1"
SEED = 42
ACCEPT_RISK_THRESHOLD = 0.1
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 314159


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric_bundle(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "count": int(len(y)),
        "auroc": float(roc_auc_score(y, p)),
        "auprc": float(average_precision_score(y, p)),
        "brier_score": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-7, 1 - 1e-7), labels=[0, 1])),
        "calibration": calibration_metrics(y, p),
        "abstention": abstention_metrics(y, p, accept_risk_threshold=ACCEPT_RISK_THRESHOLD),
    }


def bootstrap_ci(y: np.ndarray, p: np.ndarray, fn) -> dict:
    rng = np.random.RandomState(BOOTSTRAP_SEED)
    values = []
    for _ in range(BOOTSTRAP_N):
        idx = rng.randint(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            values.append(float(fn(y[idx], p[idx])))
    return {"mean": float(np.mean(values)), "ci_lo": float(np.percentile(values, 2.5)), "ci_hi": float(np.percentile(values, 97.5)), "n_valid": len(values)}


def prep_model(model):
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", model)])


def calibrated_scores(model, calibrator, frame):
    raw = model.predict_proba(frame[NUMERIC_COLS])[:, 1]
    return raw, np.asarray(calibrator.predict(raw), dtype=float)


def run_split(df, split_name, split):
    train_ids, val_ids, test_ids = (set(split[k]) for k in ("train", "val", "test"))
    assert not (train_ids & val_ids or train_ids & test_ids or val_ids & test_ids)
    train = df[df.job_name.isin(train_ids)].copy()
    val = df[df.job_name.isin(val_ids)].copy()
    test = df[df.job_name.isin(test_ids)].copy()
    candidate = prep_model(GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=2, random_state=SEED))
    candidate.fit(train[NUMERIC_COLS], train.label.astype(int))
    val_raw = candidate.predict_proba(val[NUMERIC_COLS])[:, 1]
    test_raw = candidate.predict_proba(test[NUMERIC_COLS])[:, 1]
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    calibrator.fit(val_raw, val.label.astype(int))
    test_cal = np.asarray(calibrator.predict(test_raw), dtype=float)
    y = test.label.astype(int).to_numpy()
    candidate_result = metric_bundle(y, test_cal)
    candidate_result["raw"] = metric_bundle(y, test_raw)
    candidate_result["bootstrap"] = {"auroc": bootstrap_ci(y, test_cal, roc_auc_score), "auprc": bootstrap_ci(y, test_cal, average_precision_score)}
    candidate_result["calibration_parameters"] = {"method": "isotonic_regression", "fit_split": "validation", "n_validation": len(val), "threshold": ACCEPT_RISK_THRESHOLD}
    baseline = json.loads((ROOT / "experiments/results/reliability_runtime_v2/results.json").read_text())["results"][split_name]
    model_path = OUT / "artifacts" / f"{split_name}_candidate.joblib"
    cal_path = OUT / "artifacts" / f"{split_name}_calibrator.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(candidate, model_path)
    joblib.dump(calibrator, cal_path)
    reloaded = joblib.load(model_path)
    reloaded_cal = joblib.load(cal_path)
    reload_score = np.asarray(reloaded_cal.predict(reloaded.predict_proba(test[NUMERIC_COLS])[:, 1]), dtype=float)
    return {
        "split": split_name,
        "counts": {"train": len(train), "validation": len(val), "evaluation": len(test)},
        "train_failed_rate": float(train.label.mean()), "validation_failed_rate": float(val.label.mean()), "evaluation_failed_rate": float(y.mean()),
        "feature_columns": list(NUMERIC_COLS), "feature_space_unchanged": True,
        "candidate": {"model": "GradientBoostingClassifier", "hyperparameters": {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 2, "random_state": SEED}, "metrics": candidate_result},
        "v1_control": {"metrics": baseline["model"]["B2_logistic_regression_calibrated"], "threshold": baseline["model"]["abstention"]["accept_risk_threshold"], "artifact": baseline.get("artifact", {})},
        "reproducibility": {"model_sha256": sha256(model_path), "calibrator_sha256": sha256(cal_path), "reload_same_output": bool(np.array_equal(test_cal, reload_score)), "runtime_training": False},
    }


def main():
    if (OUT / ".finalized").exists():
        raise RuntimeError(f"experiment is finalized and immutable: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix()
    splits = {k: json.loads((ROOT / "data/audit/alibaba_gpu2020" / f"splits_{k}.json").read_text()) for k in ("random_stratified", "temporal")}
    results = {k: run_split(df, k, v) for k, v in splits.items()}
    protocol = {
        "experiment_id": "phase31_reliability_gradient_boosting_same_features_v1",
        "research_question": "Can a model-only GradientBoostingClassifier improve workload-failure reliability over frozen V1 without unacceptable calibration, safety, or cost regression?",
        "null_hypothesis": "The candidate provides no meaningful improvement over V1 under the locked protocol.",
        "alternative_hypothesis": "The candidate improves discrimination without unacceptable calibration, safety, or decision-time regression.",
        "baseline": {"freeze_commit": "d977a32c2f20efa5f8e0d0349d40b270ecabeca2", "model": "EncodedWorkloadRiskModel logistic regression", "artifact": "experiments/results/reliability_runtime_v2/artifacts/"},
        "intervention": "GradientBoostingClassifier only; same 14 numeric pre-outcome features, same data, same splits, same validation-fitted isotonic calibration, locked threshold 0.1.",
        "dataset": {"id": "alibaba_gpu2020", "manifest": "data/audit/alibaba_gpu2020/dataset_manifest.json", "data_verification": "data/audit/alibaba_gpu2020/restored_data_verification.json", "sample_seed": 42},
        "features": list(NUMERIC_COLS), "feature_set": "v1 request-scheduling numeric feature space; no new features",
        "random_seeds": [SEED], "evaluation_protocol": "experiments/results/reliability_runtime_v2/protocol.json",
        "metrics": ["AUROC", "AUPRC", "Brier", "ECE", "coverage", "selective risk", "unsafe proposal rate", "unsafe execution rate", "artifact size", "reload consistency"],
        "calibration": {"method": "isotonic_regression", "fit_data": "validation only", "test_locked": True},
        "decision_rule": "ACCEPT only for meaningful multi-metric improvement with no unacceptable safety/calibration/cost regression; otherwise REJECT or HOLD.",
        "software": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__},
    }
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    (OUT / "results.json").write_text(json.dumps({"experiment_id": protocol["experiment_id"], "results": results}, indent=2, sort_keys=True) + "\n")
    summary = {"experiment_id": protocol["experiment_id"], "decision": "PENDING_REPORT", "results": {k: {"v1": v["v1_control"]["metrics"], "candidate": v["candidate"]["metrics"]} for k, v in results.items()}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    manifest = {"experiment_id": protocol["experiment_id"], "status": "completed", "protocol_sha256": sha256(OUT / "protocol.json"), "results_sha256": sha256(OUT / "results.json"), "summary_sha256": sha256(OUT / "summary.json"), "repository_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "immutable": True}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    final_files = [OUT / n for n in ("protocol.json", "results.json", "summary.json", "manifest.json")]
    final_hashes = {p.name: sha256(p) for p in final_files}
    (OUT / "finalized.json").write_text(json.dumps({"immutable": True, "files": final_hashes}, indent=2, sort_keys=True) + "\n")
    (OUT / ".finalized").write_text(json.dumps(final_hashes, sort_keys=True) + "\n")
    print(json.dumps({"experiment_id": protocol["experiment_id"], "status": "completed", "output": str(OUT), "splits": list(results), "immutable": True}, indent=2))


if __name__ == "__main__":
    main()
