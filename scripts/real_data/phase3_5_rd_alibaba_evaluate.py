"""
Phase 3.5-RD -- Alibaba unseen-GPU-type (T4) generalization evaluation.

Per configs/phase3_5_rd_generalization_protocol.json: train population =
all main-tier jobs with dominant_gpu_type != 'T4' (n=7,938); test
population = all main-tier jobs with dominant_gpu_type == 'T4' (n=2,062,
entirely absent from training). This is a genuine unseen-workload-category
test, distinct from Phase 3.3-RD's temporal shift analysis. Only imports
pipeline-construction helpers (build_feature_matrix,
assert_no_excluded_columns, REPRESENTATIONS) from the frozen Phase
3.1-RD/3.2-RD modules -- does not execute those scripts' __main__ blocks
and never writes to their output paths.
"""
import json
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


p1 = _load("phase3_1_rd_alibaba_evaluate", "scripts/real_data/phase3_1_rd_alibaba_evaluate.py")
p2 = _load("phase3_2_rd_alibaba_evaluate", "scripts/real_data/phase3_2_rd_alibaba_evaluate.py")

BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 0
CI_LEVEL = 0.95
HELD_OUT_CATEGORY = "T4"

NUMERIC_COLS = p1.NUMERIC_COLS
CATEGORICAL_COLS = p1.CATEGORICAL_COLS


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


def paired_bootstrap_diff(y_true, score_a, score_b, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    score_a = np.asarray(score_a)
    score_b = np.asarray(score_b)
    n_rows = len(y_true)
    diffs = []
    for _ in range(n):
        idx = rng.randint(0, n_rows, n_rows)
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        diffs.append(metric_fn(yt, score_b[idx]) - metric_fn(yt, score_a[idx]))
    diffs = np.array(diffs)
    lo, hi = np.percentile(diffs, [(1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100])
    return {"mean_diff": float(np.mean(diffs)), "ci_lo": float(lo), "ci_hi": float(hi), "n_valid_resamples": int(len(diffs))}


def main():
    df = p1.build_feature_matrix()
    p1.assert_no_excluded_columns(df)

    train_df = df[df["dominant_gpu_type"] != HELD_OUT_CATEGORY]
    test_df = df[df["dominant_gpu_type"] == HELD_OUT_CATEGORY]
    assert len(test_df) > 0, "held-out category produced an empty test population"
    assert HELD_OUT_CATEGORY not in set(train_df["dominant_gpu_type"]), "held-out category leaked into training population"

    train_prevalence = float(train_df["label"].mean())
    baseline_score = np.full(len(test_df), train_prevalence)
    y_true = test_df["label"].to_numpy()

    baseline_result = {
        "auroc": bootstrap_ci(y_true, baseline_score, roc_auc_score),
        "auprc": bootstrap_ci(y_true, baseline_score, average_precision_score),
    }

    candidates = {}
    for rep_name, make_pipe in p2.REPRESENTATIONS.items():
        pipe = make_pipe()
        pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
        score = pipe.predict_proba(test_df[NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
        candidates[rep_name] = {
            "auroc": bootstrap_ci(y_true, score, roc_auc_score),
            "auprc": bootstrap_ci(y_true, score, average_precision_score),
            "paired_auroc_diff_vs_baseline": paired_bootstrap_diff(y_true, baseline_score, score, roc_auc_score),
            "paired_auprc_diff_vs_baseline": paired_bootstrap_diff(y_true, baseline_score, score, average_precision_score),
        }

    out = {
        "phase": "3.5-RD",
        "protocol_version": "1.0",
        "dataset": "alibaba_gpu2020",
        "generalization_condition": f"unseen_gpu_type_holdout_{HELD_OUT_CATEGORY}",
        "protocol_source": "configs/phase3_5_rd_generalization_protocol.json",
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "train_failed_rate": train_prevalence,
        "test_failed_rate": float(y_true.mean()),
        "held_out_category_present_in_train": bool(HELD_OUT_CATEGORY in set(train_df["dominant_gpu_type"])),
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL, "unit": "job"},
        "results": {"baseline_A_no_signal": baseline_result, "candidates": candidates},
    }
    out_path = "experiments/results/phase3_real_data/phase3_5/alibaba_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
