"""The Phase 2 integration experiment.

Answers the research question stated in the Phase 2 brief: does historical
failure information (Failure Memory) improve selective prediction beyond
calibrated confidence (the Abstention Engine's calibrator) alone?

Compares three systems, evaluated on the SAME held-out test stream (regimes
3+4 of the synthetic regime-drift dataset, never used for fitting anything
-- see ``src/pipeline_builder.py``), using the SAME ``DecisionPolicy``
thresholds for every system (only the input signal differs):

  Baseline A -- Calibrator only  (DecisionMode.CONFIDENCE_ONLY)
  Baseline B -- Failure Memory only (DecisionMode.RISK_ONLY)
  System C   -- Combined (DecisionMode.COMBINED)

Thresholds are fixed a priori (``PolicyConfig`` defaults, chosen before
looking at test-set results) rather than tuned against the test set, per
the Phase 2 brief section 2.11 ("do not optimize against the test set").

Run: python benchmarks/run_baselines.py
Writes: experiments/results/baseline_comparison.json,
        experiments/results/risk_coverage_curves.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision.policy import DecisionMode, DecisionPolicy, PolicyConfig  # noqa: E402
from src.pipeline_builder import DEFAULT_REGIME_SIZES, build_system  # noqa: E402

from risk_coverage import baseline_error, operating_point_metrics, risk_coverage_curve  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results"
SEED = 42

MODES = [
    ("Calibrator only (A)", DecisionMode.CONFIDENCE_ONLY),
    ("Failure Memory only (B)", DecisionMode.RISK_ONLY),
    ("Combined (C)", DecisionMode.COMBINED),
]


def evaluate_test_stream(system, policy: DecisionPolicy) -> dict:
    confidences, risks, corrects = [], [], []
    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = system.calibrator.predict(calib_features)
        risk = system.failure_memory.risk(s.context, calib_result.calibrated_confidence)

        confidences.append(calib_result.calibrated_confidence)
        risks.append(risk)
        corrects.append(int(pred.predicted_label == s.label))

    confidences = np.array(confidences)
    risks = np.array(risks)
    correct = np.array(corrects)

    results = {}
    for name, mode in MODES:
        scores = np.array([policy.fuse(c, r, mode) for c, r in zip(confidences, risks)])
        decisions = [policy.decide(c, r, mode)[0].value for c, r in zip(confidences, risks)]
        results[name] = {
            "curve": risk_coverage_curve(scores, correct),
            "operating_point": operating_point_metrics(decisions, correct),
        }
    return {
        "results": results,
        "baseline_error": baseline_error(correct),
        "n_test_samples": int(len(correct)),
        "n_logged_failures": system.n_logged_failures,
        "failure_memory_fitted": system.failure_memory.is_fitted,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    policy = DecisionPolicy(PolicyConfig())  # a-priori thresholds, not tuned on test data

    system = build_system(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)
    summary = evaluate_test_stream(system, policy)
    summary["config"] = {
        "regime_sizes": DEFAULT_REGIME_SIZES,
        "seed": SEED,
        "policy": {
            "answer_threshold": policy.config.answer_threshold,
            "abstain_threshold": policy.config.abstain_threshold,
            "risk_weight": policy.config.risk_weight,
        },
    }

    out_path = RESULTS_DIR / "baseline_comparison.json"
    out_path.write_text(json.dumps(summary, indent=2))

    # -- plot ----------------------------------------------------------
    plt.figure(figsize=(7, 5))
    for name, _ in MODES:
        curve = summary["results"][name]["curve"]
        xs = [row["coverage"] for row in curve]
        ys = [row["selective_risk"] for row in curve]
        plt.plot(xs, ys, marker="o", label=name)
    plt.axhline(summary["baseline_error"], color="gray", linestyle="--", label="baseline error (no abstention)")
    plt.xlabel("Coverage")
    plt.ylabel("Selective risk (error rate among accepted)")
    plt.title("Risk-coverage: Calibrator vs Failure Memory vs Combined")
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "risk_coverage_curves.png", dpi=120)

    # -- console summary -------------------------------------------------
    print(f"baseline error (no abstention): {summary['baseline_error']:.4f}")
    print(f"test samples: {summary['n_test_samples']}  logged failures used to fit failure memory: {summary['n_logged_failures']}")
    print()
    print(f"{'System':<26} {'Coverage':>10} {'SelectiveRisk':>14} {'AbstainRate':>12} {'AccOnAnswered':>14}")
    for name, _ in MODES:
        op = summary["results"][name]["operating_point"]
        sr = f"{op['selective_risk']:.4f}" if op["selective_risk"] is not None else "n/a"
        acc = f"{op['accuracy_on_answered']:.4f}" if op["accuracy_on_answered"] is not None else "n/a"
        print(f"{name:<26} {op['coverage']:>10.4f} {sr:>14} {op['abstention_rate']:>12.4f} {acc:>14}")
    print(f"\nWrote {out_path}")
    print(f"Wrote {RESULTS_DIR / 'risk_coverage_curves.png'}")


if __name__ == "__main__":
    main()
