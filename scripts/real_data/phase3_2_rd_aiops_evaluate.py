"""
Phase 3.2-RD -- AIOps Challenge 2020 representation-robustness evaluation.

Reuses, unmodified, the Phase 3.1-RD window loading / feature extraction /
leave-one-entity-out (LOEO) structure from
scripts/real_data/phase3_1_rd_aiops_evaluate.py (same 226 windows, same 43
entities, same PRE-FAILURE 20-minute window, same platform-telemetry-only
feature source). Only the feature REPRESENTATION varies per the pre-
registered matrix in configs/phase3_2_rd_representation_matrix.json.
Classifier (LogisticRegression, max_iter=2000, random_state=42) held fixed.

EXPLORATORY ONLY -- unchanged from Phase 3.1-RD classification.
"""
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, average_precision_score

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "phase3_1_rd_aiops_evaluate", "scripts/real_data/phase3_1_rd_aiops_evaluate.py"
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
LOG1P_COLS = MATRIX["representation_matrix"]["R1_log_transformed"]["aiops_log1p_columns"]
RAW_COLS = [c for c in NUMERIC_COLS if c not in LOG1P_COLS]


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
        ("num_raw", raw_numeric, RAW_COLS),
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


def leave_one_entity_out(df, make_pipe):
    entities = sorted(df["entity"].unique())
    oos_score = np.full(len(df), np.nan)
    for ent in entities:
        train_mask = df["entity"] != ent
        test_mask = df["entity"] == ent
        train_df = df[train_mask]
        if train_df["label"].nunique() < 2:
            continue
        pipe = make_pipe()
        pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
        oos_score[test_mask.values] = pipe.predict_proba(df.loc[test_mask, NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
    return oos_score


def cluster_bootstrap_ci(y_true, y_score, entities, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    entities = np.asarray(entities)
    unique_entities = np.unique(entities)
    stats = []
    for _ in range(n):
        sampled_entities = unique_entities[rng.randint(0, len(unique_entities), len(unique_entities))]
        idx = np.concatenate([np.where(entities == e)[0] for e in sampled_entities])
        yt, ys = y_true[idx], y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        stats.append(metric_fn(yt, ys))
    stats = np.array(stats)
    lo, hi = np.percentile(stats, [(1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100])
    return {"point": float(np.mean(stats)), "ci_lo": float(lo), "ci_hi": float(hi), "n_valid_resamples": int(len(stats))}


def main():
    windows = p1.load_windows()
    df = p1.extract_window_features(windows)
    valid = df.dropna(subset=["mean_value"]).copy()
    n_dropped = len(df) - len(valid)

    global_prevalence = float(valid["label"].mean())
    baseline_score = np.full(len(valid), global_prevalence)
    a_auroc = cluster_bootstrap_ci(valid["label"], baseline_score, valid["entity"], roc_auc_score)
    a_auprc = cluster_bootstrap_ci(valid["label"], baseline_score, valid["entity"], average_precision_score)

    rep_results = {}
    for rep_name, make_pipe in REPRESENTATIONS.items():
        oos_score = leave_one_entity_out(valid, make_pipe)
        keep = ~np.isnan(oos_score)
        yv = valid[keep]
        sv = oos_score[keep]
        rep_results[rep_name] = {
            "n_windows_evaluated_loeo": int(keep.sum()),
            "auroc": cluster_bootstrap_ci(yv["label"], sv, yv["entity"], roc_auc_score),
            "auprc": cluster_bootstrap_ci(yv["label"], sv, yv["entity"], average_precision_score),
        }

    out = {
        "phase": "3.2-RD",
        "protocol_version": "1.0",
        "dataset": "aiops_2020",
        "status": "EXPLORATORY",
        "representation_matrix_source": "configs/phase3_2_rd_representation_matrix.json",
        "n_windows_total": int(len(df)),
        "n_windows_with_telemetry": int(len(valid)),
        "n_windows_dropped_no_telemetry_in_window": int(n_dropped),
        "n_entities_total": int(df["entity"].nunique()),
        "n_entities_positive": int(df[df["label"] == 1]["entity"].nunique()),
        "n_entities_negative_only": int(df["entity"].nunique() - df[df["label"] == 1]["entity"].nunique()),
        "n_positive_windows": int((df["label"] == 1).sum()),
        "n_negative_windows": int((df["label"] == 0).sum()),
        "feature_source": "platform telemetry only, identical to Phase 3.1-RD",
        "cv_method": "leave-one-entity-out (LOEO), no hyperparameter tuning",
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL,
                      "unit": "entity (cluster bootstrap over entities, not windows)"},
        "results": {
            "baseline_A_no_signal_global_prevalence": {"auroc": a_auroc, "auprc": a_auprc},
            "representations": rep_results,
        },
    }
    out_path = "experiments/results/phase3_real_data/phase3_2/aiops_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out["results"], indent=2))


if __name__ == "__main__":
    main()
