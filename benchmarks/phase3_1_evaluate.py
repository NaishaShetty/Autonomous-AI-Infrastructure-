"""Phase 3.1 evaluation: reproduce the Phase 2 Failure Memory baseline (and
Baselines A/B) under a frozen, scientifically-defensible protocol.

This script does NOT modify ``src/pipeline_builder.build_system`` or
``src/failure_memory``/``src/reliability`` -- it calls them exactly as
Phase 2 did, across multiple predetermined seeds, and evaluates the result
with new metrics (AUROC/AUPRC/ECE/AURC/precision&recall@coverage) that
Phase 2 did not compute. See docs/PHASE3_1_EVALUATION_PROTOCOL.md for the
full protocol this implements.

Run: python benchmarks/phase3_1_evaluate.py
Writes:
  experiments/results/phase3_1/per_seed_results.json
  experiments/results/phase3_1/per_seed_results.csv
  experiments/results/phase3_1/aggregate_results.json
  experiments/results/phase3_1/bootstrap_ci_primary_seed.json
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
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.bootstrap import bootstrap_ci  # noqa: E402
from src.evaluation.metrics import (  # noqa: E402
    auprc,
    aurc,
    auroc,
    expected_calibration_error,
    precision_recall_at_coverage,
)
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_1"

BASELINES = ["A_no_signal", "B_calibrated_confidence", "C_failure_memory"]


def _compute_test_arrays(system, regime_sizes: tuple[int, ...]) -> dict:
    """Runs the frozen, already-fitted system over its own (unmodified)
    held-out test_stream. Returns y_fail (1 = workload prediction wrong)
    and each baseline's failure-risk score (higher = judged more likely to
    fail), all as numpy arrays aligned to the same sample order."""
    y_fail, correct = [], []
    score_b, score_c = [], []

    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {
            **s.context,
            "predicted_proba": pred.predicted_proba,
            "margin": pred.margin,
            "entropy": pred.entropy,
        }
        calib_result = system.calibrator.predict(calib_features)
        risk = system.failure_memory.risk(s.context, calib_result.calibrated_confidence)

        is_wrong = int(pred.predicted_label != s.label)
        y_fail.append(is_wrong)
        correct.append(1 - is_wrong)
        score_b.append(1.0 - calib_result.calibrated_confidence)
        score_c.append(risk)

    n_logging_regime = regime_sizes[2]
    prevalence_a = system.n_logged_failures / n_logging_regime
    score_a = np.full(len(y_fail), prevalence_a)

    return {
        "y_fail": np.array(y_fail),
        "correct": np.array(correct),
        "scores": {"A_no_signal": score_a, "B_calibrated_confidence": np.array(score_b), "C_failure_memory": np.array(score_c)},
        "prevalence_a": prevalence_a,
    }


def _evaluate_one_baseline(y_fail: np.ndarray, correct: np.ndarray, failure_score: np.ndarray, coverage_points: list[float], n_bins: int) -> dict:
    trust_score = 1.0 - failure_score  # AURC/risk-coverage convention: higher = more trustworthy
    prob = np.clip(failure_score, 0.0, 1.0)  # for ECE -- see metrics.expected_calibration_error docstring

    return {
        "auroc": auroc(y_fail, failure_score),
        "auprc": auprc(y_fail, failure_score),
        "ece": expected_calibration_error(y_fail, prob, n_bins=n_bins)["ece"],
        "aurc": aurc(trust_score, correct)["aurc"],
        "precision_recall_at_coverage": [
            precision_recall_at_coverage(y_fail, failure_score, cov) for cov in coverage_points
        ],
    }


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    arrays = _compute_test_arrays(system, protocol.regime_sizes)

    baseline_results = {}
    for name in BASELINES:
        baseline_results[name] = _evaluate_one_baseline(
            arrays["y_fail"], arrays["correct"], arrays["scores"][name],
            protocol.coverage_operating_points, protocol.calibration_bins,
        )

    return {
        "seed": seed,
        "n_test_samples": int(len(arrays["y_fail"])),
        "test_failure_prevalence": float(arrays["y_fail"].mean()),
        "logging_regime_failure_prevalence_used_for_baseline_A": arrays["prevalence_a"],
        "n_logged_failures": system.n_logged_failures,
        "failure_memory_fitted": system.failure_memory.is_fitted,
        "baselines": baseline_results,
        "_arrays": arrays,  # kept only for the primary-seed bootstrap step, stripped before JSON write
    }


def _t_interval(values: list[float], confidence_level: float) -> dict:
    values = [v for v in values if v is not None]
    n = len(values)
    if n == 0:
        return {"mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0}
    mean = float(np.mean(values))
    if n == 1:
        return {"mean": mean, "std": 0.0, "ci_low": mean, "ci_high": mean, "n": 1}
    std = float(np.std(values, ddof=1))
    sem = std / np.sqrt(n)
    t_crit = float(stats.t.ppf(1 - (1 - confidence_level) / 2, df=n - 1))
    return {"mean": mean, "std": std, "ci_low": mean - t_crit * sem, "ci_high": mean + t_crit * sem, "n": n}


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {}
    for name in BASELINES:
        scalar_metrics = ["auroc", "auprc", "ece", "aurc"]
        agg[name] = {m: _t_interval([row["baselines"][name][m] for row in per_seed], 0.95) for m in scalar_metrics}
        agg[name]["precision_recall_at_coverage"] = []
        for i, cov in enumerate(protocol.coverage_operating_points):
            precisions = [row["baselines"][name]["precision_recall_at_coverage"][i]["precision"] for row in per_seed]
            recalls = [row["baselines"][name]["precision_recall_at_coverage"][i]["recall"] for row in per_seed]
            agg[name]["precision_recall_at_coverage"].append(
                {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
            )
    return agg


def run_bootstrap_for_primary_seed(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    row = next(r for r in per_seed if r["seed"] == protocol.primary_seed)
    arrays = row["_arrays"]
    y_fail = arrays["y_fail"]
    correct = arrays["correct"]

    result = {}
    for name in BASELINES:
        failure_score = arrays["scores"][name]
        result[name] = {
            "auroc": bootstrap_ci(auroc, y_fail, failure_score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
            "auprc": bootstrap_ci(auprc, y_fail, failure_score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
        }
        for cov in protocol.coverage_operating_points:
            def metric_fn(yt, ys, _cov=cov):
                return precision_recall_at_coverage(yt, ys, _cov)["precision"]

            result[name][f"precision_at_coverage_{cov}"] = bootstrap_ci(
                metric_fn, y_fail, failure_score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level
            )
    return {"primary_seed": protocol.primary_seed, "results": result}


def _strip_arrays(per_seed: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "_arrays"} for row in per_seed]


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()

    per_seed = [run_one_seed(seed, protocol) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    bootstrap_report = run_bootstrap_for_primary_seed(per_seed, protocol)

    clean_per_seed = _strip_arrays(per_seed)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_config": protocol.raw,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
    }

    (RESULTS_DIR / "per_seed_results.json").write_text(json.dumps({"meta": meta, "per_seed": clean_per_seed}, indent=2))
    (RESULTS_DIR / "aggregate_results.json").write_text(json.dumps({"meta": meta, "aggregate": aggregate}, indent=2))
    (RESULTS_DIR / "bootstrap_ci_primary_seed.json").write_text(json.dumps({"meta": meta, **bootstrap_report}, indent=2))

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "baseline", "auroc", "auprc", "ece", "aurc", "n_test_samples", "test_failure_prevalence"])
        for row in clean_per_seed:
            for name in BASELINES:
                b = row["baselines"][name]
                writer.writerow([row["seed"], name, b["auroc"], b["auprc"], b["ece"], b["aurc"], row["n_test_samples"], row["test_failure_prevalence"]])

    # -- console summary --------------------------------------------------
    print(f"Phase 3.1 evaluation -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    print(f"{'Baseline':<26} {'Seed':>6} {'AUROC':>8} {'AUPRC':>8} {'ECE':>8} {'AURC':>8}")
    for row in clean_per_seed:
        for name in BASELINES:
            b = row["baselines"][name]
            auroc_s = f"{b['auroc']:.4f}" if b["auroc"] is not None else "n/a"
            auprc_s = f"{b['auprc']:.4f}" if b["auprc"] is not None else "n/a"
            print(f"{name:<26} {row['seed']:>6} {auroc_s:>8} {auprc_s:>8} {b['ece']:>8.4f} {b['aurc']:>8.4f}")
    print()
    print(f"{'Baseline':<26} {'AUROC (mean, 95% CI)':<28} {'AUPRC (mean, 95% CI)':<28}")
    for name in BASELINES:
        a = aggregate[name]["auroc"]
        p = aggregate[name]["auprc"]
        a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
        p_s = f"{p['mean']:.4f} [{p['ci_low']:.4f}, {p['ci_high']:.4f}]" if p["mean"] is not None else "n/a"
        print(f"{name:<26} {a_s:<28} {p_s:<28}")

    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
