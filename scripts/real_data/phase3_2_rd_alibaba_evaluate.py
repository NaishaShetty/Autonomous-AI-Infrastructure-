"""
Phase 3.2-RD -- Alibaba GPU2020 representation-robustness evaluation.

Reuses, unmodified, the Phase 3.1-RD feature-extraction and leakage-exclusion
logic from scripts/real_data/phase3_1_rd_alibaba_evaluate.py (same sampled
records, same allowed pre-outcome fields, same splits, same excluded
tables/fields). Only the feature REPRESENTATION varies, per the pre-registered
matrix in configs/phase3_2_rd_representation_matrix.json (R0 raw/scaled --
identical to Phase 3.1-RD's Candidate F; R1 log1p-transformed counts/resource
fields; R2 PCA(2)-reduced numeric block). The classifier
(LogisticRegression, max_iter=2000, random_state=42) is held fixed across all
three representations.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, average_precision_score

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "phase3_1_rd_alibaba_evaluate", "scripts/real_data/phase3_1_rd_alibaba_evaluate.py"
)
p1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p1)

SEED = 42
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 0
CI_LEVEL = 0.95

with open("configs/phase3_2_rd_representation_matrix.json") as f:
    MATRIX = json.load(f)

NUMERIC_COLS = p1.NUMERIC_COLS
CATEGORICAL_COLS = p1.CATEGORICAL_COLS
LOG1P_COLS = MATRIX["representation_matrix"]["R1_log_transformed"]["alibaba_log1p_columns"]
RAW_TIME_COLS = [c for c in NUMERIC_COLS if c not in LOG1P_COLS]


def categorical_step():
    return Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])


def make_pipeline_R0():
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    pre = ColumnTransformer([("num", numeric, NUMERIC_COLS), ("cat", categorical_step(), CATEGORICAL_COLS)])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000, random_state=SEED))])


def make_pipeline_R1():
    log_numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])
    raw_numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    pre = ColumnTransformer([
        ("num_log", log_numeric, LOG1P_COLS),
        ("num_raw", raw_numeric, RAW_TIME_COLS),
        ("cat", categorical_step(), CATEGORICAL_COLS),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000, random_state=SEED))])


def make_pipeline_R2():
    numeric_pca = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("pca", PCA(n_components=2, random_state=SEED)),
    ])
    pre = ColumnTransformer([("num_pca", numeric_pca, NUMERIC_COLS), ("cat", categorical_step(), CATEGORICAL_COLS)])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000, random_state=SEED))])


REPRESENTATIONS = {
    "R0_raw_scaled": make_pipeline_R0,
    "R1_log_transformed": make_pipeline_R1,
    "R2_pca_reduced": make_pipeline_R2,
}


def bootstrap_ci(y_true, y_score, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n_rows = len(y_true)
    stats = []
    for _ in range(n):
        idx = rng.randint(0, n_rows, n_rows)
        yt, ys = y_true[idx], y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        stats.append(metric_fn(yt, ys))
    stats = np.array(stats)
    lo, hi = np.percentile(stats, [(1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100])
    return {"point": float(np.mean(stats)), "ci_lo": float(lo), "ci_hi": float(hi), "n_valid_resamples": int(len(stats))}


def evaluate_split(df, split_name, train_ids, test_ids):
    train_df = df[df["job_name"].isin(train_ids)]
    test_df = df[df["job_name"].isin(test_ids)]
    out = {"split": split_name, "n_train": int(len(train_df)), "n_test": int(len(test_df)),
           "train_failed_rate": float(train_df["label"].mean()), "test_failed_rate": float(test_df["label"].mean()),
           "representations": {}}
    for rep_name, make_pipe in REPRESENTATIONS.items():
        pipe = make_pipe()
        pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
        score = pipe.predict_proba(test_df[NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
        out["representations"][rep_name] = {
            "auroc": bootstrap_ci(test_df["label"], score, roc_auc_score),
            "auprc": bootstrap_ci(test_df["label"], score, average_precision_score),
        }
    return out


def main():
    df = p1.build_feature_matrix()
    p1.assert_no_excluded_columns(df)

    with open("data/audit/alibaba_gpu2020/splits_random_stratified.json") as f:
        rs = json.load(f)
    with open("data/audit/alibaba_gpu2020/splits_temporal.json") as f:
        ts = json.load(f)

    random_result = evaluate_split(df, "random_stratified", set(rs["train"]), set(rs["test"]))
    temporal_result = evaluate_split(df, "temporal", set(ts["train"]), set(ts["test"]))

    out = {
        "phase": "3.2-RD",
        "protocol_version": "1.0",
        "dataset": "alibaba_gpu2020",
        "sample_tier": "main",
        "n_sampled_jobs": int(len(df)),
        "representation_matrix_source": "configs/phase3_2_rd_representation_matrix.json",
        "excluded_tables": sorted(p1.EXCLUDED_TABLES),
        "excluded_fields": sorted(p1.EXCLUDED_FIELDS),
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL, "unit": "job (test-set rows)"},
        "results": {"random_stratified": random_result, "temporal": temporal_result},
    }
    out_path = "experiments/results/phase3_real_data/phase3_2/alibaba_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out["results"], indent=2))


if __name__ == "__main__":
    main()
