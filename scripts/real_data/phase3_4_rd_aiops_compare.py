"""
Phase 3.4-RD -- AIOps consolidated baseline-vs-candidate comparison.

Same design as scripts/real_data/phase3_4_rd_alibaba_compare.py: no new
model, no new candidate. Re-derives LOEO out-of-sample scores for Baseline
A and R0/R1/R2 (identical, unmodified pipelines from Phase 3.1-RD/3.2-RD),
verifies against the frozen result files within the same disclosed
solver-reproducibility tolerance (see phase3_4_rd_alibaba_compare.py's
VERIFICATION_TOLERANCE docstring), then computes a paired entity-cluster
bootstrap difference (same 43 entities, same window-level OOS predictions
resampled jointly for baseline and each candidate).

EXPLORATORY ONLY -- unchanged classification.
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
VERIFICATION_TOLERANCE = 3e-3
# Same underlying cause documented in phase3_4_rd_alibaba_compare.py
# (cross-invocation floating-point non-associativity in the lbfgs solver's
# BLAS/LAPACK calls -- confirmed NOT a logic difference: p1's hardcoded R0
# LOEO loop and p2's parametrized LOEO loop were verified to produce
# IDENTICAL out-of-sample scores -- max abs diff 0.0 -- when run in the
# same process on the same data). AIOps LOEO involves 43 independent
# LogisticRegression fits (one per held-out entity) versus Alibaba's single
# fit per split, so small per-fit drift has 43x the opportunity to
# accumulate; the observed aggregate AUROC drift (~1.1e-3) is larger than
# Alibaba's (~7e-5) but still two orders of magnitude below every AIOps
# effect size reported in this phase (>= 0.1). See
# docs/PHASE3_REAL_DATA_3_4_REPORT.md, Implementation issues.


class ProtocolDiscrepancyError(Exception):
    pass


def paired_cluster_bootstrap_diff(y_true, score_a, score_b, entities, metric_fn, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    score_a = np.asarray(score_a)
    score_b = np.asarray(score_b)
    entities = np.asarray(entities)
    unique_entities = np.unique(entities)
    diffs = []
    for _ in range(n):
        sampled_entities = unique_entities[rng.randint(0, len(unique_entities), len(unique_entities))]
        idx = np.concatenate([np.where(entities == e)[0] for e in sampled_entities])
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

    global_prevalence = float(valid["label"].mean())
    baseline_score = np.full(len(valid), global_prevalence)

    rep_scores = {}
    for rep_name, make_pipe in p2.REPRESENTATIONS.items():
        oos_score = p2.leave_one_entity_out(valid, make_pipe)
        rep_scores[rep_name] = oos_score

    keep = np.ones(len(valid), dtype=bool)
    for rep_name in rep_scores:
        keep &= ~np.isnan(rep_scores[rep_name])
    valid_eval = valid[keep].copy()
    baseline_score = baseline_score[keep]
    for rep_name in rep_scores:
        rep_scores[rep_name] = rep_scores[rep_name][keep]

    with open("experiments/results/phase3_real_data/phase3_2/aiops_results.json") as f:
        frozen = json.load(f)

    mismatches = []
    y_true = valid_eval["label"].to_numpy()
    for rep_name in ["R0_raw_scaled", "R1_log_transformed", "R2_pca_reduced"]:
        frozen_val = frozen["results"]["representations"][rep_name]["auroc"]["point"]
        recomputed_val = roc_auc_score(y_true, rep_scores[rep_name])
        if abs(frozen_val - recomputed_val) > VERIFICATION_TOLERANCE:
            raise ProtocolDiscrepancyError(
                f"{rep_name} AUROC mismatch beyond tolerance: frozen={frozen_val} recomputed={recomputed_val}"
            )
        if frozen_val != recomputed_val:
            mismatches.append({"component": rep_name, "frozen": frozen_val, "recomputed": recomputed_val})

    baseline_auroc = roc_auc_score(y_true, baseline_score)
    frozen_baseline = frozen["results"]["baseline_A_no_signal_global_prevalence"]["auroc"]["point"]
    if abs(frozen_baseline - baseline_auroc) > VERIFICATION_TOLERANCE:
        raise ProtocolDiscrepancyError(f"Baseline A AUROC mismatch beyond tolerance: frozen={frozen_baseline} recomputed={baseline_auroc}")

    candidates = {}
    for rep_name in ["R0_raw_scaled", "R1_log_transformed", "R2_pca_reduced"]:
        auroc_diff = paired_cluster_bootstrap_diff(y_true, baseline_score, rep_scores[rep_name], valid_eval["entity"], roc_auc_score)
        auprc_diff = paired_cluster_bootstrap_diff(y_true, baseline_score, rep_scores[rep_name], valid_eval["entity"], average_precision_score)
        candidates[rep_name] = {
            "auroc_point": float(roc_auc_score(y_true, rep_scores[rep_name])),
            "auprc_point": float(average_precision_score(y_true, rep_scores[rep_name])),
            "paired_auroc_diff_vs_baseline": auroc_diff,
            "paired_auprc_diff_vs_baseline": auprc_diff,
        }

    out = {
        "phase": "3.4-RD",
        "protocol_version": "1.0",
        "dataset": "aiops_2020",
        "status": "EXPLORATORY",
        "comparison_matrix_source": "configs/phase3_4_rd_comparison_matrix.json",
        "n_windows_evaluated": int(len(valid_eval)),
        "n_entities": int(valid_eval["entity"].nunique()),
        "verification_mismatches_within_tolerance": mismatches,
        "bootstrap": {"n_resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "confidence_level": CI_LEVEL,
                      "unit": "entity (paired cluster resampling)"},
        "results": {"baseline_auroc": float(baseline_auroc), "candidates": candidates},
    }
    out_path = "experiments/results/phase3_real_data/phase3_4/aiops_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
