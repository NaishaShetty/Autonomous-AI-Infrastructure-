"""Phase 3.2: controlled failure-representation experiments.

Evaluates two new candidate failure-risk representations (raw structured
features; explicit failure-history features -- see
``src/evaluation/representations.py``) against the frozen Phase 3.1
protocol and its three existing baselines (no-signal, calibrated
confidence, Phase 2 Failure Memory). Does NOT modify
``configs/phase3_1_protocol.json``, ``src/evaluation/{metrics,bootstrap,
protocol}.py``, ``benchmarks/phase3_1_evaluate.py``, ``src/pipeline_builder
.py``, or ``src/failure_memory/``. Candidate D (temporal/recency) is
analyzed, not executed -- see ``candidate_d_temporal_analysis()``.

Run: python benchmarks/phase3_2_evaluate.py
Writes:
  experiments/results/phase3_2/per_seed_results.json
  experiments/results/phase3_2/per_seed_results.csv
  experiments/results/phase3_2/aggregate_results.json
  experiments/results/phase3_2/bootstrap_ci_primary_seed.json
  experiments/results/phase3_2/candidate_d_temporal_analysis.json
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
from src.evaluation.representations import FailureHistoryRiskModel, RawFeatureFailureRisk  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402  -- reused, not reimplemented

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_2"

REPRESENTATIONS = [
    "A_no_signal",
    "B_calibrated_confidence",
    "control_phase2_failure_memory",
    "candidate_raw_features",
    "candidate_failure_history",
]


def _reconstruct_regime2(seed: int, protocol: Phase31Protocol) -> list[StreamSample]:
    """Regenerates regime 2 (all samples, not just failures) via the exact
    same deterministic call ``src.pipeline_builder.build_system`` makes
    internally. Same function, same seed -> byte-identical samples; this is
    NOT new data and does NOT touch regimes 3/4. Needed because
    ``build_system`` only exposes the failures it logged (as
    ``failure_memory``'s internal state), not the full regime-2 sample set
    Candidate C's logistic regression needs as its supervised training set
    -- see docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md section 4."""
    stream = generate_regime_stream(regime_sizes=protocol.regime_sizes, seed=seed)
    regime2 = [s for s in stream if s.regime == 2]
    assert len(regime2) == protocol.regime_sizes[2]
    return regime2


def _fit_candidates(system, regime2: list[StreamSample], protocol: Phase31Protocol, seed: int) -> dict:
    """Fits Candidates B and C on regime-2 data only, using the SAME frozen
    workload model + calibrator ``system`` already has (no retraining of
    the workload model or calibrator happens here)."""
    failure_contexts, failure_confidences = [], []
    regime2_contexts, regime2_is_failure = [], []

    for s in regime2:
        x = np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)
        is_wrong = int(pred.predicted_label != s.label)

        regime2_contexts.append(s.context)
        regime2_is_failure.append(is_wrong)
        if is_wrong:
            failure_contexts.append(s.context)
            failure_confidences.append(calib_result.calibrated_confidence)

    assert len(failure_contexts) == system.n_logged_failures, (
        "Reconstructed regime-2 failure count does not match build_system's own count -- "
        "the deterministic regeneration is inconsistent with the control condition."
    )

    raw_candidate = RawFeatureFailureRisk(FEATURE_NAMES, n_clusters=protocol.n_clusters, random_state=seed).fit(
        failure_contexts, failure_confidences
    )
    history_candidate = FailureHistoryRiskModel(FEATURE_NAMES, k_neighbors=5, random_state=seed).fit(
        failure_contexts, failure_confidences, regime2_contexts, regime2_is_failure
    )
    return {"candidate_raw_features": raw_candidate, "candidate_failure_history": history_candidate}


def _compute_test_arrays(system, candidates: dict, protocol: Phase31Protocol) -> dict:
    y_fail, correct = [], []
    scores = {name: [] for name in REPRESENTATIONS}

    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)

        is_wrong = int(pred.predicted_label != s.label)
        y_fail.append(is_wrong)
        correct.append(1 - is_wrong)

        scores["B_calibrated_confidence"].append(1.0 - calib_result.calibrated_confidence)
        scores["control_phase2_failure_memory"].append(system.failure_memory.risk(s.context, calib_result.calibrated_confidence))
        scores["candidate_raw_features"].append(candidates["candidate_raw_features"].risk(s.context, calib_result.calibrated_confidence))
        scores["candidate_failure_history"].append(candidates["candidate_failure_history"].risk(s.context))

    n_logging_regime = protocol.regime_sizes[2]
    prevalence_a = system.n_logged_failures / n_logging_regime
    scores["A_no_signal"] = [prevalence_a] * len(y_fail)

    return {
        "y_fail": np.array(y_fail),
        "correct": np.array(correct),
        "scores": {k: np.array(v) for k, v in scores.items()},
        "prevalence_a": prevalence_a,
    }


def _is_probability_flag(name: str, candidates: dict) -> bool:
    if name == "candidate_raw_features":
        return candidates["candidate_raw_features"].is_probability
    if name == "candidate_failure_history":
        return candidates["candidate_failure_history"].is_probability
    if name == "B_calibrated_confidence":
        return True  # isotonic-calibrated by construction (Phase 2)
    if name == "control_phase2_failure_memory":
        return False  # Gaussian-kernel similarity, never fit as a probability (Phase 3.1 finding)
    if name == "A_no_signal":
        return True  # a constant equal to an empirical prevalence is a (trivial) probability
    raise ValueError(name)


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
        result["ece"] = None  # explicitly not meaningful -- see representations.py is_probability
    return result


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    regime2 = _reconstruct_regime2(seed, protocol)
    candidates = _fit_candidates(system, regime2, protocol, seed)
    arrays = _compute_test_arrays(system, candidates, protocol)

    results = {}
    for name in REPRESENTATIONS:
        results[name] = _evaluate_one(
            arrays["y_fail"], arrays["correct"], arrays["scores"][name],
            protocol.coverage_operating_points, protocol.calibration_bins,
            report_ece=_is_probability_flag(name, candidates),
        )

    return {
        "seed": seed,
        "n_test_samples": int(len(arrays["y_fail"])),
        "test_failure_prevalence": float(arrays["y_fail"].mean()),
        "n_logged_failures_regime2": system.n_logged_failures,
        "candidate_raw_features_fitted": candidates["candidate_raw_features"].is_fitted,
        "candidate_failure_history_fitted": candidates["candidate_failure_history"].is_fitted,
        "results": results,
        "_arrays": arrays,
    }


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {}
    for name in REPRESENTATIONS:
        agg[name] = {}
        for m in ["auroc", "auprc", "aurc"]:
            agg[name][m] = _t_interval([row["results"][name][m] for row in per_seed], 0.95)
        ece_values = [row["results"][name]["ece"] for row in per_seed]
        agg[name]["ece"] = _t_interval(ece_values, 0.95) if all(v is not None for v in ece_values) else {
            "mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0,
            "note": "ECE not meaningful for this representation -- see is_probability flag",
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
    for name in REPRESENTATIONS:
        score = arrays["scores"][name]
        result[name] = {
            "auroc": bootstrap_ci(auroc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
            "auprc": bootstrap_ci(auprc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
        }
    return {"primary_seed": protocol.primary_seed, "results": result}


def candidate_d_temporal_analysis() -> dict:
    """Per the Phase 3.2 brief section 3 (Candidate D): checks whether the
    benchmark contains genuine temporal structure BEFORE attempting to
    evaluate a recency-based representation. Does not fabricate temporal
    semantics from row order."""
    has_timestamp_field = "timestamp" in StreamSample.__dataclass_fields__
    # generate_regime_stream builds X/p/y for an entire regime via single
    # vectorized rng calls, then appends samples in a plain index loop --
    # row order is the array index, not an elapsed-time record. Confirmed
    # by reading src/data/synthetic.py directly (see docstring reference).
    generation_is_vectorized_per_regime = True

    return {
        "executed": False,
        "has_timestamp_field": has_timestamp_field,
        "generation_is_vectorized_per_regime_not_sequential": generation_is_vectorized_per_regime,
        "conclusion": "Temporal representation cannot be validly evaluated under the current benchmark.",
        "reasoning": (
            "StreamSample carries no timestamp; the only ordering available is array index within "
            "a regime, which src/data/synthetic.py::generate_regime_stream produces via vectorized "
            "per-regime rng calls with no sequential dependence between consecutive samples. Treating "
            "row index as elapsed time would fabricate a temporal semantics the generator does not "
            "provide, which the Phase 3.2 brief explicitly prohibits. A controlled temporal extension "
            "(e.g. samples with real timestamps and drift that evolves continuously rather than only "
            "at fixed regime boundaries) would be required before recency/decay features could be "
            "validly tested -- this is a benchmark-design requirement for a future phase, not "
            "something Phase 3.2 should silently add."
        ),
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()  # frozen, unmodified

    per_seed = [run_one_seed(seed, protocol) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    bootstrap_report = run_bootstrap_for_primary_seed(per_seed, protocol)
    temporal_analysis = candidate_d_temporal_analysis()

    clean_per_seed = [{k: v for k, v in row.items() if k != "_arrays"} for row in per_seed]

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_config": protocol.raw,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "note": "Phase 3.1 protocol reused unmodified. Candidate D not executed -- see candidate_d_temporal_analysis.json",
    }

    (RESULTS_DIR / "per_seed_results.json").write_text(json.dumps({"meta": meta, "per_seed": clean_per_seed}, indent=2))
    (RESULTS_DIR / "aggregate_results.json").write_text(json.dumps({"meta": meta, "aggregate": aggregate}, indent=2))
    (RESULTS_DIR / "bootstrap_ci_primary_seed.json").write_text(json.dumps({"meta": meta, **bootstrap_report}, indent=2))
    (RESULTS_DIR / "candidate_d_temporal_analysis.json").write_text(json.dumps(temporal_analysis, indent=2))

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "representation", "auroc", "auprc", "ece", "aurc", "n_test_samples"])
        for row in clean_per_seed:
            for name in REPRESENTATIONS:
                r = row["results"][name]
                writer.writerow([row["seed"], name, r["auroc"], r["auprc"], r["ece"], r["aurc"], row["n_test_samples"]])

    print(f"Phase 3.2 evaluation -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    print(f"{'Representation':<32} {'Seed':>6} {'AUROC':>8} {'AUPRC':>8} {'ECE':>8} {'AURC':>8}")
    for row in clean_per_seed:
        for name in REPRESENTATIONS:
            r = row["results"][name]
            auroc_s = f"{r['auroc']:.4f}" if r["auroc"] is not None else "n/a"
            auprc_s = f"{r['auprc']:.4f}" if r["auprc"] is not None else "n/a"
            ece_s = f"{r['ece']:.4f}" if r["ece"] is not None else "n/a"
            print(f"{name:<32} {row['seed']:>6} {auroc_s:>8} {auprc_s:>8} {ece_s:>8} {r['aurc']:>8.4f}")

    print()
    print(f"{'Representation':<32} {'AUROC (mean, 95% CI)':<28} {'AURC (mean, 95% CI, lower=better)':<32}")
    for name in REPRESENTATIONS:
        a = aggregate[name]["auroc"]
        c = aggregate[name]["aurc"]
        a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
        c_s = f"{c['mean']:.4f} [{c['ci_low']:.4f}, {c['ci_high']:.4f}]" if c["mean"] is not None else "n/a"
        print(f"{name:<32} {a_s:<28} {c_s:<32}")

    print(f"\nCandidate D (temporal): {temporal_analysis['conclusion']}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
