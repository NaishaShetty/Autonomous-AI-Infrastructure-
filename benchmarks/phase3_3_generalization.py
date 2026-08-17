"""Phase 3.3: generalization and robustness validation of the Supervised
Failure-Risk candidate (Phase 3.2C's Experiment B: the existing Phase 2 PCA
representation + logistic regression).

Tests whether the failure-risk signal discovered in Phase 3.2C survives
evaluation on genuinely unseen conditions, WITHOUT retuning the candidate.
Does NOT modify ``configs/phase3_1_protocol.json``,
``src/evaluation/{metrics,bootstrap,protocol}.py``,
``benchmarks/phase3_1_evaluate.py``, ``src/pipeline_builder.py``,
``src/failure_memory/``, ``src/decision/``, or
``src/evaluation/representations.py`` (the candidate class, Phase2Represent
ationSupervisedRisk, is reused exactly as Phase 3.2C defined it).

Generator property this study relies on (verified empirically, not assumed
-- see docs/PHASE3_3_GENERALIZATION.md section 1): for a fixed seed and
regime_sizes, ``generate_regime_stream``'s per-sample FEATURES (X) are
IDENTICAL across different ``drift_scale`` values -- only the labels (y)
differ, because drift only perturbs the label-generating weight vector, not
the feature draw. Regime 0 (training) is fully drift_scale-invariant
(regime_idx=0 -> drift=0 regardless of drift_scale). This means varying
drift_scale for regimes 3+4 produces a genuinely unseen failure-generating
relationship while leaving the input feature distribution fixed -- a
concept-drift generalization test, not a covariate-shift test (documented
explicitly, not overclaimed).

``src.pipeline_builder.build_system`` never exposes ``drift_scale`` (it
always uses ``generate_regime_stream``'s default 0.35) -- so calling it
already produces the exact frozen Phase 3.1/3.2/3.2C training condition
with no changes needed here.

Run: python benchmarks/phase3_3_generalization.py
Writes:
  experiments/results/phase3_3/per_seed_results.json
  experiments/results/phase3_3/per_seed_results.csv
  experiments/results/phase3_3/aggregate_results.json
  experiments/results/phase3_3/bootstrap_ci_primary_seed.json
"""
from __future__ import annotations

import csv
import json
import platform
import sys
from dataclasses import dataclass
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
from src.evaluation.representations import Phase2RepresentationSupervisedRisk  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402  -- reused, not reimplemented

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_3"

BASELINES = ["A_no_signal", "B_calibrated_confidence", "C_original_failure_memory", "D_supervised_failure_risk"]

BASELINE_DRIFT_SCALE = 0.35  # src.data.synthetic.generate_regime_stream's own default -- the training condition


@dataclass(frozen=True)
class Condition:
    id: str
    kind: str  # "in_distribution_reference" | "unseen"
    drift_scale: float
    description: str


# Predetermined BEFORE any generalization result was computed. Weaker/
# stronger are fixed multiplicative factors of the training drift_scale
# (0.5x, 2x) -- chosen for interpretability, not because they were observed
# to favor the candidate. "original_benchmark" reuses system.test_stream
# verbatim (the unmodified Phase 3.1/3.2C reference), not a regeneration.
CONDITIONS = [
    Condition(
        id="original_benchmark",
        kind="in_distribution_reference",
        drift_scale=BASELINE_DRIFT_SCALE,
        description="Phase 3.1/3.2C reference: system.test_stream (regimes 3+4) at the training drift_scale, unmodified.",
    ),
    Condition(
        id="unseen_weaker_drift",
        kind="unseen",
        drift_scale=BASELINE_DRIFT_SCALE * 0.5,
        description="0.5x training drift_scale -- decision boundary at test regimes rotated LESS from the training boundary than the model ever fit on.",
    ),
    Condition(
        id="unseen_stronger_drift",
        kind="unseen",
        drift_scale=BASELINE_DRIFT_SCALE * 2.0,
        description="2x training drift_scale -- decision boundary at test regimes rotated MORE from the training boundary than the model ever fit on.",
    ),
]


def _reconstruct_regime2_with_confidences(seed: int, protocol: Phase31Protocol, system) -> dict:
    """Regenerates regime 2 at the BASELINE (training) drift_scale via the
    exact same deterministic call ``build_system`` makes internally -- same
    function, same seed, same (default) drift_scale -> byte-identical
    samples; NOT new data. Used only to fit the Supervised Failure-Risk
    candidate (D), exactly as Phase 3.2C's Experiment B did. Never touches
    any of the generalization conditions' regime-3/4 data."""
    stream = generate_regime_stream(regime_sizes=protocol.regime_sizes, seed=seed)  # default drift_scale, same as build_system
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
        "the deterministic regeneration is inconsistent with the frozen training condition."
    )

    return {
        "failure_contexts": failure_contexts,
        "failure_confidences": failure_confidences,
        "regime2_contexts": regime2_contexts,
        "regime2_confidences": regime2_confidences,
        "regime2_is_failure": regime2_is_failure,
    }


def _fit_frozen_candidate(regime2: dict, seed: int) -> Phase2RepresentationSupervisedRisk:
    """Fits the Supervised Failure-Risk candidate EXACTLY as Phase 3.2C's
    Experiment B did: same class, same config (n_components=2 inside
    FailureEmbedder, random_state=seed, LogisticRegression(max_iter=1000)),
    same fitting-data convention (PCA on regime-2 failures, LR on all of
    regime 2). Called exactly ONCE per seed, before any generalization
    condition is evaluated -- the returned object is then reused,
    unmodified, across every condition (see ``run_one_seed``)."""
    return Phase2RepresentationSupervisedRisk(FEATURE_NAMES, random_state=seed).fit(
        regime2["failure_contexts"], regime2["regime2_contexts"], regime2["regime2_confidences"], regime2["regime2_is_failure"]
    )


def _condition_test_samples(condition: Condition, seed: int, protocol: Phase31Protocol, system) -> list[StreamSample]:
    """Returns the regime-3/4 samples for one evaluation condition. The
    in-distribution reference reuses ``system.test_stream`` verbatim (no
    regeneration -- this IS the Phase 3.1/3.2C benchmark, must remain
    visible unmodified). Every "unseen" condition independently calls
    ``generate_regime_stream`` with a different ``drift_scale`` -- this
    changes ONLY the label-generating relationship at regimes 3+4 (verified
    empirically: features are byte-identical across drift_scale for a fixed
    seed/regime_sizes; see module docstring), never anything the model was
    fit on (regimes 0/1/2 always use the baseline drift_scale, matching
    ``build_system``'s own fixed behavior)."""
    if condition.kind == "in_distribution_reference":
        assert condition.drift_scale == BASELINE_DRIFT_SCALE
        return system.test_stream
    stream = generate_regime_stream(regime_sizes=protocol.regime_sizes, drift_scale=condition.drift_scale, seed=seed)
    test_samples = [s for s in stream if s.regime >= 3]
    assert len(test_samples) == sum(protocol.regime_sizes[3:])
    return test_samples


def _assert_no_regime2_leakage(test_samples: list[StreamSample], regime2: dict) -> None:
    def row_hash(ctx: dict[str, float]) -> tuple:
        return tuple(round(ctx[f], 10) for f in FEATURE_NAMES)

    regime2_hashes = {row_hash(c) for c in regime2["regime2_contexts"]}
    test_hashes = {row_hash(s.context) for s in test_samples}
    assert not (regime2_hashes & test_hashes), "A generalization condition's test samples overlap with regime-2 fitting data."


def _compute_condition_arrays(system, candidate: Phase2RepresentationSupervisedRisk, test_samples: list[StreamSample], prevalence_a: float) -> dict:
    """Scores the FROZEN, already-fitted workload model / calibrator /
    original failure memory / candidate D against ``test_samples``. Nothing
    here calls .fit() -- every model was fit once, before this function is
    ever called, on regime-0/1/2 data only."""
    y_fail, correct = [], []
    scores = {name: [] for name in BASELINES}

    for s in test_samples:
        x = np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)

        is_wrong = int(pred.predicted_label != s.label)
        y_fail.append(is_wrong)
        correct.append(1 - is_wrong)

        scores["B_calibrated_confidence"].append(1.0 - calib_result.calibrated_confidence)
        scores["C_original_failure_memory"].append(system.failure_memory.risk(s.context, calib_result.calibrated_confidence))
        scores["D_supervised_failure_risk"].append(candidate.risk(s.context, calib_result.calibrated_confidence))

    scores["A_no_signal"] = [prevalence_a] * len(y_fail)

    return {
        "y_fail": np.array(y_fail),
        "correct": np.array(correct),
        "scores": {k: np.array(v) for k, v in scores.items()},
    }


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
        result["ece"] = None  # not a probability -- Failure Memory's Gaussian-kernel score, Phase 3.1 finding
    return result


def _is_probability(name: str) -> bool:
    return name in ("A_no_signal", "B_calibrated_confidence", "D_supervised_failure_risk")


def run_one_seed(seed: int, protocol: Phase31Protocol) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)  # frozen training, unmodified
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    candidate = _fit_frozen_candidate(regime2, seed)  # fit ONCE; reused unmodified across every condition below
    prevalence_a = system.n_logged_failures / protocol.regime_sizes[2]  # train-side only, fixed across all conditions

    per_condition = {}
    for condition in CONDITIONS:
        test_samples = _condition_test_samples(condition, seed, protocol, system)
        _assert_no_regime2_leakage(test_samples, regime2)
        arrays = _compute_condition_arrays(system, candidate, test_samples, prevalence_a)

        results = {
            name: _evaluate_one(
                arrays["y_fail"], arrays["correct"], arrays["scores"][name],
                protocol.coverage_operating_points, protocol.calibration_bins,
                report_ece=_is_probability(name),
            )
            for name in BASELINES
        }
        per_condition[condition.id] = {
            "condition": {"id": condition.id, "kind": condition.kind, "drift_scale": condition.drift_scale, "description": condition.description},
            "n_test_samples": int(len(arrays["y_fail"])),
            "test_failure_prevalence": float(arrays["y_fail"].mean()),
            "results": results,
            "_arrays": arrays,
        }

    return {
        "seed": seed,
        "n_logged_failures_regime2": system.n_logged_failures,
        "candidate_fitted": candidate.is_fitted,
        "per_condition": per_condition,
    }


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    agg = {}
    for condition in CONDITIONS:
        agg[condition.id] = {}
        for name in BASELINES:
            agg[condition.id][name] = {}
            for m in ["auroc", "auprc", "aurc"]:
                agg[condition.id][name][m] = _t_interval(
                    [row["per_condition"][condition.id]["results"][name][m] for row in per_seed], 0.95
                )
            ece_values = [row["per_condition"][condition.id]["results"][name]["ece"] for row in per_seed]
            agg[condition.id][name]["ece"] = _t_interval(ece_values, 0.95) if all(v is not None for v in ece_values) else {
                "mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0,
                "note": "ECE not meaningful for this baseline -- see _is_probability",
            }
            agg[condition.id][name]["precision_recall_at_coverage"] = []
            for i, cov in enumerate(protocol.coverage_operating_points):
                precisions = [row["per_condition"][condition.id]["results"][name]["precision_recall_at_coverage"][i]["precision"] for row in per_seed]
                recalls = [row["per_condition"][condition.id]["results"][name]["precision_recall_at_coverage"][i]["recall"] for row in per_seed]
                agg[condition.id][name]["precision_recall_at_coverage"].append(
                    {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
                )
    return agg


def run_bootstrap_for_primary_seed(per_seed: list[dict], protocol: Phase31Protocol) -> dict:
    row = next(r for r in per_seed if r["seed"] == protocol.primary_seed)
    result = {}
    for condition in CONDITIONS:
        arrays = row["per_condition"][condition.id]["_arrays"]
        y_fail = arrays["y_fail"]
        result[condition.id] = {}
        for name in BASELINES:
            score = arrays["scores"][name]
            result[condition.id][name] = {
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

    clean_per_seed = []
    for row in per_seed:
        clean_row = {k: v for k, v in row.items() if k != "per_condition"}
        clean_row["per_condition"] = {
            cid: {k: v for k, v in cond.items() if k != "_arrays"} for cid, cond in row["per_condition"].items()
        }
        clean_per_seed.append(clean_row)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_config": protocol.raw,
        "conditions": [c.__dict__ for c in CONDITIONS],
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "note": "Phase 3.1 protocol reused unmodified. Candidate frozen from Phase 3.2C's Experiment B. No refitting on any generalization condition.",
    }

    (RESULTS_DIR / "per_seed_results.json").write_text(json.dumps({"meta": meta, "per_seed": clean_per_seed}, indent=2))
    (RESULTS_DIR / "aggregate_results.json").write_text(json.dumps({"meta": meta, "aggregate": aggregate}, indent=2))
    (RESULTS_DIR / "bootstrap_ci_primary_seed.json").write_text(json.dumps({"meta": meta, **bootstrap_report}, indent=2))

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "condition", "drift_scale", "baseline", "auroc", "auprc", "ece", "aurc", "n_test_samples"])
        for row in clean_per_seed:
            for condition in CONDITIONS:
                cond_row = row["per_condition"][condition.id]
                for name in BASELINES:
                    r = cond_row["results"][name]
                    writer.writerow([row["seed"], condition.id, condition.drift_scale, name, r["auroc"], r["auprc"], r["ece"], r["aurc"], cond_row["n_test_samples"]])

    print(f"Phase 3.3 generalization -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    for condition in CONDITIONS:
        print(f"=== {condition.id} (drift_scale={condition.drift_scale}) ===")
        print(f"{'Baseline':<30} {'AUROC (mean, 95% CI)':<30}")
        for name in BASELINES:
            a = aggregate[condition.id][name]["auroc"]
            a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
            print(f"{name:<30} {a_s:<30}")
        print()

    print(f"Wrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
