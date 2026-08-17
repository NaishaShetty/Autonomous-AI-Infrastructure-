"""Diagnostic companion to run_baselines.py.

The headline operating-point table in ``run_baselines.py`` compares systems
at DIFFERENT coverage levels (because each system's own thresholds select a
different fraction of the test stream), which can be misleading. This
script answers the methodologically correct question -- at MATCHED coverage,
does adding the failure-memory risk signal help? -- and directly measures
whether the risk signal correlates with actual failure at all, which is the
root-cause diagnostic for whatever the answer turns out to be.

Run: python benchmarks/diagnose_risk_signal.py
Writes: experiments/results/risk_signal_diagnosis.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision.policy import DecisionMode, DecisionPolicy, PolicyConfig  # noqa: E402
from src.pipeline_builder import DEFAULT_REGIME_SIZES, build_system  # noqa: E402

from risk_coverage import risk_coverage_curve  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results"
SEED = 42
RISK_WEIGHTS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
MATCHED_COVERAGES = (0.2, 0.5, 0.8)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    system = build_system(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)

    confidences, risks, corrects = [], [], []
    for s in system.test_stream:
        x = np.array([s.context[f] for f in system.feature_names], dtype=float)
        pred = system.workload_model.predict(x)
        cf = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        cr = system.calibrator.predict(cf)
        risk = system.failure_memory.risk(s.context, cr.calibrated_confidence)
        confidences.append(cr.calibrated_confidence)
        risks.append(risk)
        corrects.append(int(pred.predicted_label == s.label))

    confidences = np.array(confidences)
    risks = np.array(risks)
    correct = np.array(corrects)
    incorrect = 1 - correct

    signal_quality = {
        "confidence_mean": float(confidences.mean()),
        "confidence_std": float(confidences.std()),
        "confidence_correlation_with_correct": float(np.corrcoef(confidences, correct)[0, 1]),
        "failure_risk_mean": float(risks.mean()),
        "failure_risk_std": float(risks.std()),
        "failure_risk_correlation_with_incorrect": float(np.corrcoef(risks, incorrect)[0, 1]),
    }

    sensitivity = []
    for w in RISK_WEIGHTS:
        policy = DecisionPolicy(PolicyConfig(risk_weight=w))
        scores = np.array([policy.fuse(c, r, DecisionMode.COMBINED) for c, r in zip(confidences, risks)])
        curve = {round(row["coverage"], 2): row["selective_risk"] for row in risk_coverage_curve(scores, correct)}
        sensitivity.append(
            {"risk_weight": w, **{f"selective_risk_at_cov_{c}": curve[c] for c in MATCHED_COVERAGES}}
        )

    out = {
        "seed": SEED,
        "n_test_samples": int(len(correct)),
        "signal_quality": signal_quality,
        "risk_weight_sensitivity": sensitivity,
        "matched_coverages_evaluated": list(MATCHED_COVERAGES),
    }
    out_path = RESULTS_DIR / "risk_signal_diagnosis.json"
    out_path.write_text(json.dumps(out, indent=2))

    print("Signal quality:")
    for k, v in signal_quality.items():
        print(f"  {k}: {v:.4f}")
    print("\nSelective risk at matched coverage, by risk_weight (0.0 = calibrator only):")
    header = f"{'risk_weight':>11} " + " ".join(f"cov={c:<5}" for c in MATCHED_COVERAGES)
    print(header)
    for row in sensitivity:
        vals = " ".join(f"{row[f'selective_risk_at_cov_{c}']:.4f}   " for c in MATCHED_COVERAGES)
        print(f"{row['risk_weight']:>11.2f} {vals}")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
