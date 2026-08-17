"""
Phase 3.5-RD -- AIOps unseen-object-family (db) generalization evaluation.

Per configs/phase3_5_rd_generalization_protocol.json: train population =
all docker+os entities' windows (30 entities, 170 windows); test
population = all db entities' windows (13 entities, 56 windows, entirely
absent from training). A single fit on the train population, scored once
on the held-out db population -- NOT leave-one-entity-out (that question
is already answered by Phase 3.1-RD/3.2-RD/3.4-RD's LOEO structure; this
is a category-level, not entity-level, generalization test).

EXPLORATORY, per the frozen protocol's classification of AIOps overall,
made more so here by the small held-out population (13 entities, 12
positive windows).
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


p1 = _load("phase3_1_rd_aiops_evaluate", "scripts/real_data/phase3_1_rd_aiops_evaluate.py")
p2 = _load("phase3_2_rd_aiops_evaluate", "scripts/real_data/phase3_2_rd_aiops_evaluate.py")

BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 0
CI_LEVEL = 0.95
HELD_OUT_FAMILY = "db"

NUMERIC_COLS = p1.NUMERIC_COLS
CATEGORICAL_COLS = p1.CATEGORICAL_COLS


def cluster_bootstrap_ci(y_true, y_score, entities, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    entities = np.asarray(entities)
    unique_entities = np.unique(entities)
    stats = []
    for _ in range(n):
        sampled = unique_entities[rng.randint(0, len(unique_entities), len(unique_entities))]
        idx = np.concatenate([np.where(entities == e)[0] for e in sampled])
        yt, ys = y_true[idx], y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        stats.append(metric_fn(yt, ys))
    stats = np.array(stats)
    lo, hi = np.percentile(stats, [(1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100])
    return {"point": float(np.mean(stats)), "ci_lo": float(lo), "ci_hi": float(hi), "n_valid_resamples": int(len(stats))}


def paired_cluster_bootstrap_diff(y_true, score_a, score_b, entities, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    score_a = np.asarray(score_a)
    score_b = np.asarray(score_b)
    entities = np.asarray(entities)
    unique_entities = np.unique(entities)
    diffs = []
    for _ in range(n):
        sampled = unique_entities[rng.randint(0, len(unique_entities), len(unique_entities))]
        idx = np.concatenate([np.where(entities == e)[0] for e in sampled])
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        diffs.append(metric_fn(yt, score_b[idx]) - metric_fn(yt, score_a[idx]))
    diffs = np.array(diffs)
    lo, hi = np.percentile(diffs, [(1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100])
    return {"mean_diff": float(np.mean(diffs)), "ci_lo": float(lo), "ci_hi": float(hi), "n_valid_resamples": int(len(diffs))}


def main():
    windows = p1.load_windows()
    df = p1.extract_window_features(windows)
    valid = df.dropna(subset=["mean_value"]).copy()

    train_df = valid[valid["object"] != HELD_OUT_FAMILY]
    test_df = valid[valid["object"] == HELD_OUT_FAMILY]
    assert len(test_df) > 0
    assert HELD_OUT_FAMILY not in set(train_df["object"]), "held-out family leaked into training population"

    train_prevalence = float(train_df["label"].mean())
    y_true = test_df["label"].to_numpy()
    baseline_score = np.full(len(test_df), train_prevalence)

    baseline_result = {
        "auroc": cluster_bootstrap_ci(y_true, baseline_score, test_df["entity"], roc_auc_score),
        "auprc": cluster_bootstrap_ci(y_true, baseline_score, test_df["entity"], average_precision_score),
    }

    candidates = {}
    for rep_name, make_pipe in p2.REPRESENTATIONS.items():
        pipe = make_pipe()
        pipe.fit(train_df[NUMERIC_COLS + CATEGORICAL_COLS], train_df["label"])
        score = pipe.predict_proba(test_df[NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
        candidates[rep_name] = {
            "auroc": cluster_bootstrap_ci(y_true, score, test_df["entity"], roc_auc_score),
            "auprc": cluster_bootstrap_ci(y_true, score, test_df["entity"], average_precision_score),
            "paired_auroc_diff_vs_baseline": paired_cluster_bootstrap_diff(y_true, baseline_score, score, test_df["entity"], roc_auc_score),
            "paired_auprc_diff_vs_baseline": paired_cluster_bootstrap_diff(y_true, baseline_score, score, test_df["entity"], average_precision_score),
        }

    out = {
        "phase": "3.5-RD",
        "protocol_version": "1.0",
        "dataset": "aiops_2020",
        "status": "EXPLORATORY",
        "generalization_condition": f"unseen_object_family_holdout_{HELD_OUT_FAMILY}",
        "protocol_source": "configs/phase3_5_rd_generalization_protocol.json",
        "n_train_windows": int(len(train_df)),
        "n_train_entities": int(train_df["entity"].nunique()),
        "n_test_windows": int(len(test_df)),
        "n_test_entities": int(test_df["entity"].nunique()),
        "train_positive_rate": train_prevalence,
        "test_positive_rate": float(y_true.mean()),
        "held_out_family_present_in_train": bool(HELD_OUT_FAMILY in set(train_df["object"])),
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL,
                      "unit": "entity (cluster bootstrap over the held-out db entities)"},
        "results": {"baseline_A_no_signal": baseline_result, "candidates": candidates},
    }
    out_path = "experiments/results/phase3_real_data/phase3_5/aiops_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
