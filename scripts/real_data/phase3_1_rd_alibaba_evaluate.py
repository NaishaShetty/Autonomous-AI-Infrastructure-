"""
Phase 3.1-RD -- Alibaba GPU2020 real-data baseline/signal evaluation.

Executes under the frozen protocol:
  docs/PHASE3_REAL_DATA_PROTOCOL.md
  configs/phase3_real_data_protocol.json  (protocol_version 1.0)

Scope (Phase 3.1-RD only, matching the minimal baseline/signal-evaluation
scope of the original Phase 3.1): does a supervised failure-risk signal
exist above a no-signal baseline, using ONLY pre-outcome (request/
scheduling-time) fields, on the frozen main-tier sample and the frozen
random and temporal splits. No hyperparameter tuning against test data.
No new sampling, no rebalancing, no pooling.

Leakage exclusions enforced (never read/used as features):
  pai_sensor_table, pai_machine_metric, max_mem, max_gpu_wrk_mem

Feature-availability note (documented, not a leakage issue): the
processed-data extraction under scripts/real_data/ never materialized a
sampled/linked pai_group_tag_table or pai_machine_spec for the main tier
(only raw .tar.gz archives exist for those two tables). Both are on the
protocol's ALLOWED list but are unavailable in processed form, so this
evaluation uses a conservative subset of the allowed fields: job_table
(user excluded as a high-cardinality identifier -- see report),
task_table, and instance_table pre-outcome fields only. This narrows
feature completeness; it does not violate the leakage ceiling (using
fewer allowed fields is always leakage-safe).
"""
import json
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

EXCLUDED_TABLES = {"pai_sensor_table", "pai_machine_metric"}
EXCLUDED_FIELDS = {"max_mem", "max_gpu_wrk_mem"}


def load_sample_ids():
    with open("data/audit/alibaba_gpu2020/sample_job_ids_main.txt") as f:
        return set(line.strip() for line in f if line.strip())


def build_job_features(sample_ids):
    jt = pd.read_csv(
        "data/processed/alibaba_gpu2020/job_table.clean.csv",
        usecols=["job_name", "user", "status", "start_time"],
    )
    jt = jt[jt["job_name"].isin(sample_ids)].copy()
    assert jt["status"].isin(["Terminated", "Failed"]).all(), (
        "main-tier sample must be terminal jobs only per frozen population definition"
    )
    jt["label"] = (jt["status"] == "Failed").astype(int)
    # `user` is an allowed pre-outcome field but is a very high-cardinality
    # identifier; a raw one-hot/target encoding would either explode
    # dimensionality or require its own leakage-prevention design (train-only
    # target encoding) that is out of scope for a minimal Phase 3.1-RD
    # baseline. Documented exclusion, not a silent one.
    jt = jt.rename(columns={"start_time": "job_start_time"})
    return jt[["job_name", "label", "job_start_time"]]


def build_task_features(sample_ids):
    tt = pd.read_csv("data/processed/alibaba_gpu2020/task_table.main_sample.csv")
    tt = tt[tt["job_name"].isin(sample_ids)].copy()
    agg = tt.groupby("job_name").agg(
        n_tasks=("task_name", "count"),
        n_distinct_task_names=("task_name", "nunique"),
        sum_inst_num=("inst_num", "sum"),
        mean_plan_cpu=("plan_cpu", "mean"),
        max_plan_cpu=("plan_cpu", "max"),
        mean_plan_mem=("plan_mem", "mean"),
        max_plan_mem=("plan_mem", "max"),
        mean_plan_gpu=("plan_gpu", "mean"),
        max_plan_gpu=("plan_gpu", "max"),
        n_distinct_gpu_types=("gpu_type", "nunique"),
    ).reset_index()
    dominant = (
        tt.dropna(subset=["gpu_type"])
        .groupby(["job_name", "gpu_type"]).size()
        .reset_index(name="cnt")
        .sort_values(["job_name", "cnt"], ascending=[True, False])
        .drop_duplicates("job_name")[["job_name", "gpu_type"]]
        .rename(columns={"gpu_type": "dominant_gpu_type"})
    )
    agg = agg.merge(dominant, on="job_name", how="left")
    agg["dominant_gpu_type"] = agg["dominant_gpu_type"].fillna("UNKNOWN")
    return agg


def build_instance_features(sample_ids):
    it = pd.read_csv(
        "data/processed/alibaba_gpu2020/instance_table.main_sample.csv",
        usecols=["job_name", "machine", "start_time"],
    )
    it = it[it["job_name"].isin(sample_ids)].copy()
    agg = it.groupby("job_name").agg(
        n_instances=("machine", "count"),
        n_distinct_machines=("machine", "nunique"),
        mean_instance_start_time=("start_time", "mean"),
    ).reset_index()
    return agg


def assert_no_excluded_columns(df):
    for col in df.columns:
        assert col not in EXCLUDED_FIELDS, f"excluded field {col} present in feature frame"


def build_feature_matrix():
    sample_ids = load_sample_ids()
    jobs = build_job_features(sample_ids)
    tasks = build_task_features(sample_ids)
    insts = build_instance_features(sample_ids)
    df = jobs.merge(tasks, on="job_name", how="left").merge(insts, on="job_name", how="left")
    assert_no_excluded_columns(df)
    return df


NUMERIC_COLS = [
    "job_start_time", "n_tasks", "n_distinct_task_names", "sum_inst_num",
    "mean_plan_cpu", "max_plan_cpu", "mean_plan_mem", "max_plan_mem",
    "mean_plan_gpu", "max_plan_gpu", "n_distinct_gpu_types",
    "n_instances", "n_distinct_machines", "mean_instance_start_time",
]
CATEGORICAL_COLS = ["dominant_gpu_type"]


def make_pipeline():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([
        ("num", numeric, NUMERIC_COLS),
        ("cat", categorical, CATEGORICAL_COLS),
    ])
    clf = LogisticRegression(max_iter=2000, random_state=SEED)
    return Pipeline([("pre", pre), ("clf", clf)])


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
    return float(np.mean(stats)), float(lo), float(hi), int(len(stats))


def evaluate_split(df, split_name, train_ids, val_ids, test_ids):
    train_df = df[df["job_name"].isin(train_ids)]
    test_df = df[df["job_name"].isin(test_ids)]

    train_prevalence = train_df["label"].mean()

    # Baseline A: no-signal, constant score = train-set prevalence
    baseline_a_score = np.full(len(test_df), train_prevalence)
    a_auroc = bootstrap_ci(test_df["label"], baseline_a_score, roc_auc_score)
    a_auprc = bootstrap_ci(test_df["label"], baseline_a_score, average_precision_score)

    # Candidate F-analogue: supervised LogisticRegression on allowed
    # pre-outcome fields, fit on train only, evaluated on test.
    pipe = make_pipeline()
    pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
    test_score = pipe.predict_proba(test_df[NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
    f_auroc = bootstrap_ci(test_df["label"], test_score, roc_auc_score)
    f_auprc = bootstrap_ci(test_df["label"], test_score, average_precision_score)

    # calibrated-confidence baseline (B in the original protocol) has no
    # real-data analogue for Alibaba: there is no pre-existing upstream
    # classifier whose confidence output could be measured. Not computed.
    # This is documented, not silently omitted -- see report section 15.

    return {
        "split": split_name,
        "n_train": int(len(train_df)),
        "n_val": int(len(val_ids & set(df["job_name"]))) if val_ids else None,
        "n_test": int(len(test_df)),
        "train_failed_rate": float(train_prevalence),
        "test_failed_rate": float(test_df["label"].mean()),
        "baseline_A_no_signal": {
            "auroc": {"point": a_auroc[0], "ci_lo": a_auroc[1], "ci_hi": a_auroc[2], "n_valid_resamples": a_auroc[3]},
            "auprc": {"point": a_auprc[0], "ci_lo": a_auprc[1], "ci_hi": a_auprc[2], "n_valid_resamples": a_auprc[3]},
        },
        "candidate_F_supervised_risk": {
            "auroc": {"point": f_auroc[0], "ci_lo": f_auroc[1], "ci_hi": f_auroc[2], "n_valid_resamples": f_auroc[3]},
            "auprc": {"point": f_auprc[0], "ci_lo": f_auprc[1], "ci_hi": f_auprc[2], "n_valid_resamples": f_auprc[3]},
        },
    }


def main():
    df = build_feature_matrix()

    with open("data/audit/alibaba_gpu2020/splits_random_stratified.json") as f:
        rs = json.load(f)
    with open("data/audit/alibaba_gpu2020/splits_temporal.json") as f:
        ts = json.load(f)

    random_result = evaluate_split(
        df, "random_stratified",
        set(rs["train"]), set(rs["val"]), set(rs["test"]),
    )
    temporal_result = evaluate_split(
        df, "temporal",
        set(ts["train"]), set(ts["val"]), set(ts["test"]),
    )

    out = {
        "protocol_version": "1.0",
        "dataset": "alibaba_gpu2020",
        "sample_tier": "main",
        "n_sampled_jobs": int(len(df)),
        "feature_columns_used": NUMERIC_COLS + CATEGORICAL_COLS,
        "excluded_tables": sorted(EXCLUDED_TABLES),
        "excluded_fields": sorted(EXCLUDED_FIELDS),
        "features_unavailable_not_used": ["pai_group_tag_table.*", "pai_machine_spec.*", "job_table.user"],
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL,
                      "unit": "job (test-set rows)"},
        "results": {
            "random_stratified": random_result,
            "temporal": temporal_result,
        },
    }

    out_path = "experiments/results/phase3_real_data/phase3_1/alibaba_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out["results"], indent=2))


if __name__ == "__main__":
    main()
