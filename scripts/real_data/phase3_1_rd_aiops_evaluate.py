"""
Phase 3.1-RD -- AIOps Challenge 2020 real-data baseline/signal evaluation.

EXPLORATORY ONLY (per docs/PHASE3_REAL_DATA_PROTOCOL.md sections 5, 12, 17, 18).
226 windows (81 positive + 145 negative), 43 entities (16 positive-bearing,
27 negative-only). The 226 windows are NOT treated as 226 independent
observations -- evaluation uses leave-one-entity-out (LOEO) cross-validation
to produce out-of-sample predictions, then a cluster (entity-level) bootstrap
for the confidence interval. This choice is an implementation decision made
within protocol bounds: the frozen protocol specifies cluster-bootstrap
inference for AIOps (section 14) but does not itself prescribe a train/test
split procedure (unlike Alibaba, where the split is a frozen upstream
artifact). LOEO avoids in-sample optimism at this very small entity count and
requires no hyperparameter tuning (fixed LogisticRegression, no search),
so it does not touch any frozen test set (none exists for AIOps).

Uses ONLY PRE-FAILURE window telemetry (platform metrics: dcos_docker,
dcos_container, db_oracle_11g, os_linux -- the families matching the 43
fault-eligible entities). Business (esb.csv) and trace-window telemetry are
NOT included in this minimal baseline (feature-completeness limitation,
documented, not a leakage issue -- see report). Fault-log descriptive/timing
fields are never used as features, only to define window boundaries
(already baked into the frozen window manifests).
"""
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score

SEED = 42
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 0
CI_LEVEL = 0.95
TZ_UTC8 = timezone(timedelta(hours=8))

FAMILY_FILES = {
    "docker": ["dcos_docker", "dcos_container"],
    "db": ["db_oracle_11g"],
    "os": ["os_linux"],
}


def local_iso_to_epoch_ms(iso_str):
    dt = datetime.fromisoformat(iso_str).replace(tzinfo=TZ_UTC8)
    return int(dt.astimezone(timezone.utc).timestamp() * 1000)


def load_windows():
    with open("data/audit/aiops_kpi/positive_window_validation.json") as f:
        pos = [r for r in json.load(f)["results"] if r["VALID"]]
    with open("data/audit/aiops_kpi/negative_window_validation.json") as f:
        neg = [r for r in json.load(f)["results"] if r["VALID"]]

    windows = []
    for r in pos:
        onset_ms = local_iso_to_epoch_ms(r["onset"])
        start_ms = onset_ms - 20 * 60 * 1000
        end_ms = onset_ms
        family = r["entity"].split("_")[0]
        windows.append({
            "entity": r["entity"], "object": family, "label": 1,
            "start_ms": start_ms, "end_ms": end_ms,
            "day": r["onset"][:10],
        })
    for r in neg:
        start_ms = local_iso_to_epoch_ms(r["window_start"])
        end_ms = local_iso_to_epoch_ms(r["window_end"])
        family = r["entity"].split("_")[0]
        windows.append({
            "entity": r["entity"], "object": family, "label": 0,
            "start_ms": start_ms, "end_ms": end_ms,
            "day": r["day"],
        })
    return windows


def load_family_day_cache():
    # Lazily loaded {(day, family_file): dataframe}
    return {}


def get_family_df(cache, day, family_file):
    key = (day, family_file)
    if key not in cache:
        path = f"data/processed/aiops_kpi/platform/{day}__{family_file}.csv"
        try:
            df = pd.read_csv(path, usecols=["cmdb_id", "itemid", "timestamp", "value"])
        except FileNotFoundError:
            df = pd.DataFrame(columns=["cmdb_id", "itemid", "timestamp", "value"])
        cache[key] = df
    return cache[key]


def extract_window_features(windows):
    cache = load_family_day_cache()
    rows = []
    for w in windows:
        family_files = FAMILY_FILES[w["object"]]
        parts = []
        for ff in family_files:
            df = get_family_df(cache, w["day"], ff)
            sub = df[(df["cmdb_id"] == w["entity"]) & (df["timestamp"] >= w["start_ms"]) & (df["timestamp"] < w["end_ms"])]
            parts.append(sub)
        combined = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        if len(combined) == 0:
            feat = dict(n_observations=0, n_distinct_metrics=0, mean_value=np.nan,
                        std_value=np.nan, min_value=np.nan, max_value=np.nan)
        else:
            vals = combined["value"].astype(float)
            feat = dict(
                n_observations=int(len(combined)),
                n_distinct_metrics=int(combined["itemid"].nunique()),
                mean_value=float(vals.mean()),
                std_value=float(vals.std()) if len(vals) > 1 else 0.0,
                min_value=float(vals.min()),
                max_value=float(vals.max()),
            )
        row = {**w, **feat}
        rows.append(row)
    return pd.DataFrame(rows)


NUMERIC_COLS = ["n_observations", "n_distinct_metrics", "mean_value", "std_value", "min_value", "max_value"]
CATEGORICAL_COLS = ["object"]


def make_pipeline():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([("num", numeric, NUMERIC_COLS), ("cat", categorical, CATEGORICAL_COLS)])
    clf = LogisticRegression(max_iter=2000, random_state=SEED)
    return Pipeline([("pre", pre), ("clf", clf)])


def leave_one_entity_out(df):
    entities = sorted(df["entity"].unique())
    oos_score = np.full(len(df), np.nan)
    # Baseline A (no-signal) is a single FIXED constant equal to the overall
    # pool prevalence, applied identically to every window -- matching the
    # Alibaba baseline A design (a fixed pre-computed constant, not a value
    # that varies by held-out fold). A per-fold "prevalence of the remaining
    # data" baseline was tried first and rejected: because entities differ
    # sharply in how many positive windows they contribute, excluding a
    # heavily-positive entity measurably lowers the remaining pool's
    # prevalence, which spuriously anti-correlates the per-fold baseline
    # with the true label (observed AUROC 0.17 for a baseline that should be
    # indistinguishable from 0.5 by construction). Documented as an
    # implementation correction made before any candidate-model result was
    # inspected; it does not alter the candidate model's LOEO evaluation.
    global_prevalence = float(df["label"].mean())
    oos_baseline = np.full(len(df), global_prevalence)
    for ent in entities:
        train_mask = df["entity"] != ent
        test_mask = df["entity"] == ent
        train_df = df[train_mask]
        if train_df["label"].nunique() < 2:
            continue  # cannot fit a meaningful classifier without both classes in training fold
        pipe = make_pipeline()
        pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
        oos_score[test_mask.values] = pipe.predict_proba(df.loc[test_mask, NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
    return oos_score, oos_baseline


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
    return float(np.mean(stats)), float(lo), float(hi), int(len(stats))


def main():
    windows = load_windows()
    df = extract_window_features(windows)

    valid = df.dropna(subset=["mean_value"]).copy()
    n_dropped = len(df) - len(valid)

    oos_score, oos_baseline = leave_one_entity_out(valid)
    keep = ~np.isnan(oos_score)
    valid_eval = valid[keep].copy()
    oos_score = oos_score[keep]
    oos_baseline = oos_baseline[keep]

    a_auroc = cluster_bootstrap_ci(valid_eval["label"], oos_baseline, valid_eval["entity"], roc_auc_score)
    a_auprc = cluster_bootstrap_ci(valid_eval["label"], oos_baseline, valid_eval["entity"], average_precision_score)
    f_auroc = cluster_bootstrap_ci(valid_eval["label"], oos_score, valid_eval["entity"], roc_auc_score)
    f_auprc = cluster_bootstrap_ci(valid_eval["label"], oos_score, valid_eval["entity"], average_precision_score)

    out = {
        "protocol_version": "1.0",
        "dataset": "aiops_2020",
        "status": "EXPLORATORY",
        "n_windows_total": int(len(df)),
        "n_windows_with_telemetry": int(len(valid)),
        "n_windows_dropped_no_telemetry_in_window": int(n_dropped),
        "n_windows_evaluated_loeo": int(len(valid_eval)),
        "n_entities_total": int(df["entity"].nunique()),
        "n_entities_positive": int(df[df["label"] == 1]["entity"].nunique()),
        "n_entities_negative_only": int(df["entity"].nunique() - df[df["label"] == 1]["entity"].nunique()),
        "n_positive_windows": int((df["label"] == 1).sum()),
        "n_negative_windows": int((df["label"] == 0).sum()),
        "feature_source": "platform telemetry only (dcos_docker, dcos_container, db_oracle_11g, os_linux); business/trace telemetry not included in this minimal baseline",
        "cv_method": "leave-one-entity-out (LOEO), no hyperparameter tuning",
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL,
                      "unit": "entity (cluster bootstrap over entities, not windows)"},
        "results": {
            "baseline_A_no_signal_global_prevalence": {
                "auroc": {"point": a_auroc[0], "ci_lo": a_auroc[1], "ci_hi": a_auroc[2], "n_valid_resamples": a_auroc[3]},
                "auprc": {"point": a_auprc[0], "ci_lo": a_auprc[1], "ci_hi": a_auprc[2], "n_valid_resamples": a_auprc[3]},
            },
            "candidate_F_supervised_risk_loeo": {
                "auroc": {"point": f_auroc[0], "ci_lo": f_auroc[1], "ci_hi": f_auroc[2], "n_valid_resamples": f_auroc[3]},
                "auprc": {"point": f_auprc[0], "ci_lo": f_auprc[1], "ci_hi": f_auprc[2], "n_valid_resamples": f_auprc[3]},
            },
        },
    }

    out_path = "experiments/results/phase3_real_data/phase3_1/aiops_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
