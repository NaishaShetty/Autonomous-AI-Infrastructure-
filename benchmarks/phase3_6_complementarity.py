"""Phase 3.6.1: complementarity experiment.

Does F (Supervised Failure Risk) add incremental predictive information
beyond B (calibrated confidence)? Fits a simple, pre-specified 2-input
logistic regression (``src.evaluation.complementarity.CombinedRisk``) on
regime-2 data only, per seed, and compares B alone / F alone / B+F on the
held-out test stream under the frozen Phase 3.1 protocol.

Reuses ``benchmarks.phase3_3_generalization``'s
``_reconstruct_regime2_with_confidences`` and ``_fit_frozen_candidate``
verbatim -- F here is the exact Phase 3.3 frozen candidate, not a
reimplementation.

Run: python benchmarks/phase3_6_complementarity.py
Writes: experiments/results/phase3_6/complementarity.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.bootstrap import bootstrap_ci  # noqa: E402
from src.evaluation.complementarity import CombinedRisk  # noqa: E402
from src.evaluation.metrics import (  # noqa: E402
    auprc,
    aurc,
    auroc,
    expected_calibration_error,
    precision_recall_at_coverage,
)
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402
from benchmarks.phase3_3_generalization import (  # noqa: E402
    _fit_frozen_candidate,
    _reconstruct_regime2_with_confidences,
)

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_6"
CANDIDATES = ["B_calibrated_confidence", "F_supervised_failure_risk", "BF_combined"]


def _fit_combined(regime2: dict, candidate_f, seed: int) -> CombinedRisk:
    b_scores = [1.0 - c for c in regime2["regime2_confidences"]]
    f_scores = [candidate_f.risk(ctx, conf) for ctx, conf in zip(regime2["regime2_contexts"], regime2["regime2_confidences"])]
    return CombinedRisk(random_state=seed).fit(b_scores, f_scores, regime2["regime2_is_failure"])


def _compute_test_arrays(system, candidate_f, combined) -> dict:
    y_fail, correct = [], []
    scores = {name: [] for name in CANDIDATES}
    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)
        is_wrong = int(pred.predicted_label != s.label)
        y_fail.append(is_wrong)
        correct.append(1 - is_wrong)

        b_score = 1.0 - calib_result.calibrated_confidence
        f_score = candidate_f.risk(s.context, calib_result.calibrated_confidence)
        scores["B_calibrated_confidence"].append(b_score)
        scores["F_supervised_failure_risk"].append(f_score)
        scores["BF_combined"].append(combined.risk(b_score, f_score))

    return {"y_fail": np.array(y_fail), "correct": np.array(correct), "scores": {k: np.array(v) for k, v in scores.items()}}


def _evaluate_one(y_fail, correct, score, coverage_points, n_bins) -> dict:
    trust_score = 1.0 - score
    prob = np.clip(score, 0.0, 1.0)
    return {
        "auroc": auroc(y_fail, score),
        "auprc": auprc(y_fail, score),
        "aurc": aurc(trust_score, correct)["aurc"],
        "ece": expected_calibration_error(y_fail, prob, n_bins=n_bins)["ece"],
        "precision_recall_at_coverage": [precision_recall_at_coverage(y_fail, score, c) for c in coverage_points],
    }


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, seed)
    combined = _fit_combined(regime2, candidate_f, seed)
    arrays = _compute_test_arrays(system, candidate_f, combined)

    results = {
        name: _evaluate_one(arrays["y_fail"], arrays["correct"], arrays["scores"][name], protocol.coverage_operating_points, protocol.calibration_bins)
        for name in CANDIDATES
    }
    return {
        "seed": seed,
        "n_test_samples": int(len(arrays["y_fail"])),
        "combined_fitted": combined.is_fitted,
        "results": results,
        "_arrays": arrays,
    }


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {}
    for name in CANDIDATES:
        agg[name] = {m: _t_interval([row["results"][name][m] for row in per_seed], 0.95) for m in ["auroc", "auprc", "aurc", "ece"]}
        agg[name]["precision_recall_at_coverage"] = []
        for i, cov in enumerate(protocol.coverage_operating_points):
            precisions = [row["results"][name]["precision_recall_at_coverage"][i]["precision"] for row in per_seed]
            recalls = [row["results"][name]["precision_recall_at_coverage"][i]["recall"] for row in per_seed]
            agg[name]["precision_recall_at_coverage"].append(
                {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
            )
    return agg


def paired_comparison(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    diffs = [row["results"]["BF_combined"]["auroc"] - row["results"]["B_calibrated_confidence"]["auroc"] for row in per_seed]
    wins = sum(1 for d in diffs if d > 0)
    return {
        "bf_minus_b_auroc": _t_interval(diffs, 0.95),
        "bf_beats_b_seed_count": wins,
        "n_seeds": len(diffs),
        "caveat": "n=6 paired differences -- descriptive interval only, no significance test performed.",
    }


def run_bootstrap_for_primary_seed(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    row = next(r for r in per_seed if r["seed"] == protocol.primary_seed)
    arrays = row["_arrays"]
    y_fail = arrays["y_fail"]
    result = {}
    for name in CANDIDATES:
        score = arrays["scores"][name]
        result[name] = {
            "auroc": bootstrap_ci(auroc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
            "auprc": bootstrap_ci(auprc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
        }
    return {"primary_seed": protocol.primary_seed, "results": result}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()

    per_seed = [run_one_seed(seed, protocol) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    paired = paired_comparison(per_seed, protocol)
    bootstrap_report = run_bootstrap_for_primary_seed(per_seed, protocol)

    clean_per_seed = [{k: v for k, v in row.items() if k != "_arrays"} for row in per_seed]
    output = {
        "meta": {"protocol": protocol.raw, "note": "BF_combined fit once per seed on regime-2 data only. No refitting on test data."},
        "per_seed": clean_per_seed,
        "aggregate": aggregate,
        "paired_comparison_bf_vs_b": paired,
        "bootstrap_primary_seed": bootstrap_report,
    }
    (RESULTS_DIR / "complementarity.json").write_text(json.dumps(output, indent=2))

    print("Phase 3.6.1 complementarity\n")
    for name in CANDIDATES:
        a = aggregate[name]["auroc"]
        print(f"{name:<28} AUROC {a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]")
    print(f"\nBF - B paired AUROC diff: {paired['bf_minus_b_auroc']['mean']:.4f}, wins {paired['bf_beats_b_seed_count']}/{paired['n_seeds']}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
