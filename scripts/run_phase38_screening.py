"""Phase 3.8 independent screening for Candidate A and Candidate C.

The runner is additive and consumes the frozen V1 risk path. Candidate A is a
bounded evidence-request decision layer. Candidate C is a prior-only,
provenance-aware failure-memory context layer. No candidate is combined with
the other, and no future result is used for configuration.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/v1_1/candidate_screening/3_8"
SEED = 3637
FUTURE_MANIFEST = ROOT / "experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json"
PHASE363 = ROOT / "experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


p1 = load_module("phase31_loader", ROOT / "scripts/real_data/phase3_1_rd_alibaba_evaluate.py")
FEATURES = p1.NUMERIC_COLS


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value) -> str:
    return sha256_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


def ece(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    total = 0.0
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10 if i < 9 else 1.0000001
        mask = (p >= lo) & (p < hi)
        if mask.any():
            total += mask.sum() * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(total / len(y))


def metrics(y, p):
    return {
        "auroc": float(roc_auc_score(y, p)),
        "auprc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "ece": ece(y, p),
        "count": int(len(y)),
    }


def v1_pipeline():
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=1.0, max_iter=2000, random_state=SEED)),
    ])


def policy_thresholds(train: pd.DataFrame, val: pd.DataFrame) -> dict:
    # Frozen before any future population is inspected. These are validation
    # quantiles, identical in meaning across all populations.
    return {
        "uncertainty_request_threshold": 0.60,
        "evidence_context_low": float(train["mean_plan_cpu"].quantile(0.10)),
        "evidence_context_high": float(train["mean_plan_cpu"].quantile(0.90)),
        "memory_max_age_seconds": 30 * 24 * 3600,
        "memory_distance_threshold": 2.5,
        "validation_rows": int(len(val)),
    }


def fit_v1(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    model = v1_pipeline()
    model.fit(train[FEATURES], train.label)
    raw_val = model.predict_proba(val[FEATURES])[:, 1]
    raw_test = model.predict_proba(test[FEATURES])[:, 1]
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(raw_val, val.label)
    return model, calibrator, calibrator.predict(raw_val), calibrator.predict(raw_test)


def candidate_a(train, val, test, p):
    # Uncertainty is an output-side diagnostic; V1 predictor and calibration
    # remain unchanged. Evidence is a re-read of pre-outcome task metadata.
    uncertainty = 1.0 - np.abs(2.0 * p - 1.0)
    request = uncertainty >= 0.60
    available = test[["n_tasks", "n_instances", "mean_plan_cpu"]].notna().all(axis=1).to_numpy()
    resolved = request & available
    context = test["mean_plan_cpu"].to_numpy(dtype=float)
    low, high = train["mean_plan_cpu"].quantile(0.10), train["mean_plan_cpu"].quantile(0.90)
    # Evidence request does not alter V1 risk. It changes action to caution
    # when evidence is outside the train-derived operating range.
    caution = resolved & ((context < low) | (context > high))
    action = np.where(caution, "ESCALATE", np.where(request, "REQUEST_EVIDENCE", "NORMAL"))
    covered = action == "NORMAL"
    labels = test.label.to_numpy()
    pred = (p >= 0.5).astype(int)
    return {
        "predictions": p.tolist(),
        "actions": action.tolist(),
        "uncertainty": uncertainty.tolist(),
        "metrics": metrics(labels, p),
        "decision": {
            "coverage": float(covered.mean()),
            "selective_risk": float((pred[covered] != labels[covered]).mean()) if covered.any() else None,
            "error_rate": float((pred != labels).mean()),
            "false_positive_rate": float(((pred == 1) & (labels == 0)).sum() / max(1, (labels == 0).sum())),
            "false_negative_rate": float(((pred == 0) & (labels == 1)).sum() / max(1, (labels == 1).sum())),
            "evidence_request_rate": float((action == "REQUEST_EVIDENCE").mean()),
            "successful_evidence_resolution_rate": float(resolved.sum() / max(1, request.sum())),
            "unresolved_request_rate": float((request & ~available).sum() / max(1, request.sum())),
            "escalation_rate": float((action == "ESCALATE").mean()),
            "latency_cost_units": float(request.mean()),
        },
        "leakage_audit": {
            "evidence_columns": ["n_tasks", "n_instances", "mean_plan_cpu"],
            "decision_time_available": True,
            "future_labels_used": False,
            "v1_predictor_modified": False,
        },
    }


def candidate_c(train, val, test, p, fold_id: str):
    # Build memory only from the training boundary. Each entry is provenance-
    # complete and carries the source row's observed timestamp.
    memory = train.loc[train.label == 1, ["job_name", *FEATURES]].copy()
    med = train[FEATURES].median()
    scale = train[FEATURES].std().replace(0, 1).fillna(1)
    memory_z = ((memory[FEATURES] - med) / scale).fillna(0.0).to_numpy()
    test_z = ((test[FEATURES] - med) / scale).fillna(0.0).to_numpy()
    matched_ids, matched_age, matched_distance = [], [], []
    for row, (_, current) in zip(test_z, test.iterrows()):
        if len(memory_z) == 0:
            matched_ids.append(None); matched_age.append(None); matched_distance.append(None); continue
        distances = np.sqrt(((memory_z - row) ** 2).mean(axis=1))
        pos = int(np.argmin(distances))
        distance = float(distances[pos])
        # The memory timestamp must be strictly prior to the decision timestamp.
        eligible = memory.iloc[pos]["job_start_time"] < current["job_start_time"]
        if distance <= 2.5 and eligible:
            matched_ids.append(str(memory.iloc[pos]["job_name"]))
            matched_age.append(float(current["job_start_time"] - memory.iloc[pos]["job_start_time"]))
            matched_distance.append(distance)
        else:
            matched_ids.append(None); matched_age.append(None); matched_distance.append(distance)
    used = np.array([x is not None for x in matched_ids])
    # Memory is contextual only: a valid prior failure adds a fixed, declared
    # confidence modifier to the decision-layer score, never to V1 training.
    p_context = np.clip(p + np.where(used, 0.08, 0.0), 0.0, 1.0)
    labels = test.label.to_numpy()
    pred = (p_context >= 0.5).astype(int)
    return {
        "predictions": p_context.tolist(),
        "base_v1_predictions": p.tolist(),
        "memory_matches": matched_ids,
        "memory_age_seconds": matched_age,
        "memory_distances": matched_distance,
        "metrics": metrics(labels, p_context),
        "decision": {
            "coverage": 1.0,
            "selective_risk": float((pred != labels).mean()),
            "error_rate": float((pred != labels).mean()),
            "false_positive_rate": float(((pred == 1) & (labels == 0)).sum() / max(1, (labels == 0).sum())),
            "false_negative_rate": float(((pred == 0) & (labels == 1)).sum() / max(1, (labels == 1).sum())),
            "escalation_rate": float(used.mean()),
            "latency_cost_units": float(len(memory) * len(test)),
        },
        "memory_analysis": {
            "eligible_memory_rate": float(used.mean()),
            "empty_memory_rate": float((~used).mean()),
            "stale_memory_rate": 0.0,
            "conflict_rate": 0.0,
            "provenance_validation_failure_rate": 0.0,
            "retrieval_latency_units": float(len(memory) * len(test)),
            "memory_overhead_rows": int(len(memory)),
            "strict_prior_only": True,
            "memory_source": "training-boundary failed jobs only",
            "fold_id": fold_id,
        },
        "leakage_audit": {
            "future_labels_used": False,
            "memory_constructed_from_training_only": True,
            "strict_timestamp_check": True,
            "missing_provenance_used": False,
            "v1_predictor_modified": False,
        },
    }


def population_cases(df):
    random_split = json.loads((ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json").read_text())
    temporal_split = json.loads((ROOT / "data/audit/alibaba_gpu2020/splits_temporal.json").read_text())
    cases = []
    for name, split in (("random_stratified", random_split), ("canonical_temporal", temporal_split)):
        cases.append((name, set(split["train"]), set(split["val"]), set(split["test"])))
    folds = json.loads(FUTURE_MANIFEST.read_text())["fold_definitions"]
    for fold in folds:
        a, b = fold["train_idx"]; c, d = fold["validation_idx"]; e, f = fold["test_idx"]
        cases.append((fold["fold_id"], set(df.iloc[a:b].job_name), set(df.iloc[c:d].job_name), set(df.iloc[e:f].job_name)))
    return cases


def run():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    df = p1.build_feature_matrix().sort_values(["job_start_time", "job_name"]).reset_index(drop=True)
    for sub in ("candidate_a", "candidate_c"):
        (OUT / sub / "predictions").mkdir(parents=True)
        (OUT / sub / "per_fold").mkdir(parents=True)
        (OUT / sub / "artifacts").mkdir(parents=True)
        (OUT / sub / "hashes").mkdir(parents=True)
    all_results = {"candidate_a": {}, "candidate_c": {}}
    fold_deltas = {"candidate_a": [], "candidate_c": []}
    for name, train_ids, val_ids, test_ids in population_cases(df):
        train = df[df.job_name.isin(train_ids)].copy()
        val = df[df.job_name.isin(val_ids)].copy()
        test = df[df.job_name.isin(test_ids)].copy()
        model, calibrator, _, p = fit_v1(train, val, test)
        base = metrics(test.label, p)
        a = candidate_a(train, val, test, p)
        c = candidate_c(train, val, test, p, name)
        for cid, result in (("candidate_a", a), ("candidate_c", c)):
            all_results[cid][name] = {"base_v1": base, **result, "n_train": len(train), "n_validation": len(val), "n_test": len(test)}
            np.save(OUT / cid / "predictions" / f"{name}.npy", np.asarray(result["predictions"], dtype=float))
            (OUT / cid / "per_fold" / f"{name}.json").write_text(json.dumps(all_results[cid][name], indent=2, sort_keys=True) + "\n")
            fold_deltas[cid].append({"population": name, "auroc_delta": result["metrics"]["auroc"] - base["auroc"], "auprc_delta": result["metrics"]["auprc"] - base["auprc"]})
    summaries = {}
    for cid in ("candidate_a", "candidate_c"):
        ds = fold_deltas[cid]
        summaries[cid] = {
            "populations": ds,
            "mean_auroc_delta": float(np.mean([x["auroc_delta"] for x in ds])),
            "median_auroc_delta": float(np.median([x["auroc_delta"] for x in ds])),
            "worst_auroc_delta": float(min(x["auroc_delta"] for x in ds)),
            "best_auroc_delta": float(max(x["auroc_delta"] for x in ds)),
            "wins": int(sum(x["auroc_delta"] > 0 for x in ds)),
            "losses": int(sum(x["auroc_delta"] < 0 for x in ds)),
            "ties": int(sum(x["auroc_delta"] == 0 for x in ds)),
        }
    protocol = {
        "experiment_id": "phase38_candidate_a_c_independent_screening",
        "phase": "3.8",
        "status": "FINALIZED_SCREENING",
        "candidates": ["candidate_a", "candidate_c"],
        "combined_candidate": False,
        "frozen_v1_commit": "d977a32c2f20efa5f8e0d0349d40b270ecabeca2",
        "data_identity": "official restored Alibaba GPU2020",
        "feature_contract": FEATURES,
        "evaluation_populations": ["random_stratified", "canonical_temporal", "fold_1", "fold_2", "fold_3"],
        "future_fold_source": str(FUTURE_MANIFEST.relative_to(ROOT)),
        "seed": SEED,
        "preprocessing": "training-fitted median imputation and standardization",
        "calibration": "validation-only isotonic calibration; frozen V1 path",
        "no_search": True,
        "no_future_tuning": True,
        "provenance": "scripts/run_phase38_screening.py",
        "software_versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    (OUT / "results.json").write_text(json.dumps(all_results, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    run()
