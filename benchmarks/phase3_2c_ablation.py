"""Phase 3.2 follow-up: Candidate C ablation study.

Decomposes Candidate C's Phase 3.2 result (rich k-NN failure-history
features -> logistic regression) into its two simultaneous changes from
the Phase 2 control (KMeans + Gaussian-kernel risk on a PCA embedding):
representation (coarse centroids -> rich failure-history features) and
learning mechanism (fixed similarity kernel -> supervised logistic
regression). Does NOT modify ``configs/phase3_1_protocol.json``,
``src/evaluation/{metrics,bootstrap,protocol}.py``,
``benchmarks/phase3_1_evaluate.py``, ``src/pipeline_builder.py``, or
``src/failure_memory/``. Reuses the frozen Phase 3.1 protocol and the
Phase 3.1/3.2 baselines as fixed historical reference points (not
rerun) -- see docs/PHASE3_2C_CANDIDATE_ABLATION.md.

Ablation matrix (see module docstrings in
``src/evaluation/representations.py`` for full definitions):
  Experiment A -- FixedRuleFailureHistoryRisk: rich representation,
                  fixed/unlearned scoring rule.
  Experiment B -- Phase2RepresentationSupervisedRisk: existing Phase 2
                  (PCA) representation, supervised logistic regression.
  Experiment C -- FailureHistoryRiskModel, reproduced UNCHANGED from
                  Phase 3.2 (rich representation + supervised learning).
                  Positive control for this ablation.

Run: python benchmarks/phase3_2c_ablation.py
Writes:
  experiments/results/phase3_2c/per_seed_results.json
  experiments/results/phase3_2c/per_seed_results.csv
  experiments/results/phase3_2c/aggregate_results.json
  experiments/results/phase3_2c/bootstrap_ci_primary_seed.json
"""
from __future__ import annotations

import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES, StreamSample, generate_regime_stream  # noqa: E402
from src.evaluation.bootstrap import bootstrap_ci  # noqa: E402
from src.evaluation.metrics import (  # noqa: E402
    auprc,
    aurc,
    auroc,
    expected_calibration_error,
    precision_recall_at_coverage,
)
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.evaluation.representations import (  # noqa: E402
    FailureHistoryRiskModel,
    FixedRuleFailureHistoryRisk,
    Phase2RepresentationSupervisedRisk,
)
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402  -- reused, not reimplemented

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_2c"

EXPERIMENTS = ["experiment_A_fixed_rule", "experiment_B_old_repr_supervised", "experiment_C_control"]

# Fixed historical reference points -- NOT rerun by this script. Copied
# verbatim from Phase 3.1/3.2 results (docs/PHASE3_1_EVALUATION_PROTOCOL.md,
# docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md) for reporting/comparison only.
HISTORICAL_REFERENCE = {
    "no_signal": {"auroc_mean": 0.5000},
    "phase2_failure_memory_control": {"auroc_mean": 0.5141, "auroc_ci": [0.4914, 0.5368]},
    "raw_feature_kmeans_candidate_B": {"auroc_mean": 0.5308, "auroc_ci": [0.5018, 0.5598]},
    "candidate_C_original": {"auroc_mean": 0.5809, "auroc_ci": [0.5472, 0.6146]},
    "calibrated_confidence": {"auroc_mean": 0.6599},
}


def _reconstruct_regime2_with_confidences(seed: int, protocol: Phase31Protocol, system) -> dict:
    """Regenerates regime 2 (all samples) via the exact same deterministic
    call ``src.pipeline_builder.build_system`` makes internally (same
    function, same seed -> byte-identical samples; NOT new data, and does
    NOT touch regimes 3/4). Additionally computes, for EVERY regime-2
    sample (not just the logged failures), the calibrated confidence and
    failure label -- Experiment B's embedding needs a confidence value for
    every sample it embeds, which ``build_system``'s own logging pass does
    not retain for successes."""
    stream = generate_regime_stream(regime_sizes=protocol.regime_sizes, seed=seed)
    regime2 = [s for s in stream if s.regime == 2]
    assert len(regime2) == protocol.regime_sizes[2]

    failure_contexts, failure_confidences = [], []
    regime2_contexts, regime2_confidences, regime2_is_failure = [], [], []

    for s in regime2:
        x = np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)
        is_wrong = int(pred.predicted_label != s.label)

        regime2_contexts.append(s.context)
        regime2_confidences.append(calib_result.calibrated_confidence)
        regime2_is_failure.append(is_wrong)
        if is_wrong:
            failure_contexts.append(s.context)
            failure_confidences.append(calib_result.calibrated_confidence)

    assert len(failure_contexts) == system.n_logged_failures, (
        "Reconstructed regime-2 failure count does not match build_system's own count -- "
        "the deterministic regeneration is inconsistent with the control condition."
    )

    return {
        "failure_contexts": failure_contexts,
        "failure_confidences": failure_confidences,
        "regime2_contexts": regime2_contexts,
        "regime2_confidences": regime2_confidences,
        "regime2_is_failure": regime2_is_failure,
    }


def _fit_experiments(system, regime2: dict, seed: int) -> dict:
    """Fits all three ablation experiments on regime-2 data only, using the
    SAME frozen workload model + calibrator ``system`` already has (no
    retraining of the workload model or calibrator happens here). k=5,
    same feature definitions and classifier configuration as Phase 3.2's
    Candidate C throughout -- no hyperparameter is swept here."""
    experiment_a = FixedRuleFailureHistoryRisk(FEATURE_NAMES, k_neighbors=5).fit(
        regime2["failure_contexts"], regime2["failure_confidences"], regime2["regime2_contexts"]
    )
    experiment_b = Phase2RepresentationSupervisedRisk(FEATURE_NAMES, random_state=seed).fit(
        regime2["failure_contexts"], regime2["regime2_contexts"], regime2["regime2_confidences"], regime2["regime2_is_failure"]
    )
    experiment_c = FailureHistoryRiskModel(FEATURE_NAMES, k_neighbors=5, random_state=seed).fit(
        regime2["failure_contexts"], regime2["failure_confidences"], regime2["regime2_contexts"], regime2["regime2_is_failure"]
    )
    return {
        "experiment_A_fixed_rule": experiment_a,
        "experiment_B_old_repr_supervised": experiment_b,
        "experiment_C_control": experiment_c,
    }


def _compute_test_arrays(system, experiments: dict) -> dict:
    y_fail, correct = [], []
    scores = {name: [] for name in EXPERIMENTS}

    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)

        is_wrong = int(pred.predicted_label != s.label)
        y_fail.append(is_wrong)
        correct.append(1 - is_wrong)

        scores["experiment_A_fixed_rule"].append(experiments["experiment_A_fixed_rule"].risk(s.context))
        scores["experiment_B_old_repr_supervised"].append(
            experiments["experiment_B_old_repr_supervised"].risk(s.context, calib_result.calibrated_confidence)
        )
        scores["experiment_C_control"].append(experiments["experiment_C_control"].risk(s.context))

    return {
        "y_fail": np.array(y_fail),
        "correct": np.array(correct),
        "scores": {k: np.array(v) for k, v in scores.items()},
    }


def _is_probability_flag(name: str, experiments: dict) -> bool:
    return experiments[name].is_probability


def _evaluate_one(y_fail, correct, score, coverage_points, n_bins, report_ece: bool) -> dict:
    trust_score = 1.0 - score
    result = {
        "auroc": auroc(y_fail, score),
        "auprc": auprc(y_fail, score),
        "aurc": aurc(trust_score, correct)["aurc"],
        "precision_recall_at_coverage": [precision_recall_at_coverage(y_fail, score, c) for c in coverage_points],
    }
    if report_ece:
        prob = np.clip(score, 0.0, 1.0)
        result["ece"] = expected_calibration_error(y_fail, prob, n_bins=n_bins)["ece"]
    else:
        result["ece"] = None  # not a probability -- see representations.py is_probability
    return result


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    experiments = _fit_experiments(system, regime2, seed)
    arrays = _compute_test_arrays(system, experiments)

    results = {}
    for name in EXPERIMENTS:
        results[name] = _evaluate_one(
            arrays["y_fail"], arrays["correct"], arrays["scores"][name],
            protocol.coverage_operating_points, protocol.calibration_bins,
            report_ece=_is_probability_flag(name, experiments),
        )

    return {
        "seed": seed,
        "n_test_samples": int(len(arrays["y_fail"])),
        "test_failure_prevalence": float(arrays["y_fail"].mean()),
        "n_logged_failures_regime2": system.n_logged_failures,
        "experiment_A_fitted": experiments["experiment_A_fixed_rule"].is_fitted,
        "experiment_B_fitted": experiments["experiment_B_old_repr_supervised"].is_fitted,
        "experiment_C_fitted": experiments["experiment_C_control"].is_fitted,
        "results": results,
        "_arrays": arrays,
    }


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {}
    for name in EXPERIMENTS:
        agg[name] = {}
        for m in ["auroc", "auprc", "aurc"]:
            agg[name][m] = _t_interval([row["results"][name][m] for row in per_seed], 0.95)
        ece_values = [row["results"][name]["ece"] for row in per_seed]
        agg[name]["ece"] = _t_interval(ece_values, 0.95) if all(v is not None for v in ece_values) else {
            "mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0,
            "note": "ECE not meaningful for this experiment -- see is_probability flag",
        }
        agg[name]["precision_recall_at_coverage"] = []
        for i, cov in enumerate(protocol.coverage_operating_points):
            precisions = [row["results"][name]["precision_recall_at_coverage"][i]["precision"] for row in per_seed]
            recalls = [row["results"][name]["precision_recall_at_coverage"][i]["recall"] for row in per_seed]
            agg[name]["precision_recall_at_coverage"].append(
                {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
            )
    return agg


def run_bootstrap_for_primary_seed(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    row = next(r for r in per_seed if r["seed"] == protocol.primary_seed)
    arrays = row["_arrays"]
    y_fail = arrays["y_fail"]

    result = {}
    for name in EXPERIMENTS:
        score = arrays["scores"][name]
        result[name] = {
            "auroc": bootstrap_ci(auroc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
            "auprc": bootstrap_ci(auprc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
        }
    return {"primary_seed": protocol.primary_seed, "results": result}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()  # frozen, unmodified

    per_seed = [run_one_seed(seed, protocol) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    bootstrap_report = run_bootstrap_for_primary_seed(per_seed, protocol)

    clean_per_seed = [{k: v for k, v in row.items() if k != "_arrays"} for row in per_seed]

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_config": protocol.raw,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "historical_reference": HISTORICAL_REFERENCE,
        "note": "Phase 3.1 protocol reused unmodified. Decomposes Phase 3.2 Candidate C via a fixed ablation matrix (A/B/C); no new seeds, representations, or hyperparameter sweeps.",
    }

    (RESULTS_DIR / "per_seed_results.json").write_text(json.dumps({"meta": meta, "per_seed": clean_per_seed}, indent=2))
    (RESULTS_DIR / "aggregate_results.json").write_text(json.dumps({"meta": meta, "aggregate": aggregate}, indent=2))
    (RESULTS_DIR / "bootstrap_ci_primary_seed.json").write_text(json.dumps({"meta": meta, **bootstrap_report}, indent=2))

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "experiment", "auroc", "auprc", "ece", "aurc", "n_test_samples"])
        for row in clean_per_seed:
            for name in EXPERIMENTS:
                r = row["results"][name]
                writer.writerow([row["seed"], name, r["auroc"], r["auprc"], r["ece"], r["aurc"], row["n_test_samples"]])

    print(f"Phase 3.2 Candidate C ablation -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    print(f"{'Experiment':<34} {'Seed':>6} {'AUROC':>8} {'AUPRC':>8} {'ECE':>8} {'AURC':>8}")
    for row in clean_per_seed:
        for name in EXPERIMENTS:
            r = row["results"][name]
            auroc_s = f"{r['auroc']:.4f}" if r["auroc"] is not None else "n/a"
            auprc_s = f"{r['auprc']:.4f}" if r["auprc"] is not None else "n/a"
            ece_s = f"{r['ece']:.4f}" if r["ece"] is not None else "n/a"
            print(f"{name:<34} {row['seed']:>6} {auroc_s:>8} {auprc_s:>8} {ece_s:>8} {r['aurc']:>8.4f}")

    print()
    print(f"{'Experiment':<34} {'AUROC (mean, 95% CI)':<28}")
    for name in EXPERIMENTS:
        a = aggregate[name]["auroc"]
        a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
        print(f"{name:<34} {a_s:<28}")

    print(f"\nHistorical reference (not rerun): {json.dumps(HISTORICAL_REFERENCE, indent=2)}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
