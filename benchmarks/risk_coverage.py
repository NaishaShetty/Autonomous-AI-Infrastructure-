"""Standardized risk-coverage benchmark harness.

Migrates the evaluation methodology Phase 1 found to be the single most
reliable, independently-reproduced result in either source repository
(``risk_coverage_curve.py`` -- PHASE1_AUDIT_REPORT.md sections 3, 4, 9:
"reproduced exactly" against a baseline error of 35.44%, ~8.05% at 15%
coverage, ~7.14% at 20% coverage).

Protocol (documented per section 2.9 of the Phase 2 brief):
  - Dataset: ``src/data/synthetic.py`` regime-drift stream (see module
    docstring), fixed seed.
  - Split: regimes 0/1/2 used for fitting (train/calibrate/log failures,
    see ``src/pipeline_builder.py``); regimes 3+4 held out, never fit on --
    that is what this harness scores.
  - Score: a per-sample scalar in [0, 1] where higher = more trustworthy.
    For Baseline A this is calibrated confidence; for Baseline B it is
    ``1 - failure_risk``; for System C it is the policy's fused score. All
    three are produced by the SAME ``DecisionPolicy.fuse`` used for live
    decisions (``src/decision/policy.py``), not a separately-maintained
    scoring formula.
  - Coverage sweep: samples are ranked by score descending and accepted at
    coverage levels 5%..100% in 5-point steps; selective risk is the error
    rate among the accepted (highest-score) fraction.
  - Metrics: coverage, selective risk (1 - accuracy among accepted),
    abstention rate and accuracy-on-accepted are also reported at the
    policy's actual fixed operating point (``PolicyConfig`` thresholds),
    separately from the swept curve -- the curve shows the full tradeoff,
    the operating-point numbers show what the system would actually do.
"""
from __future__ import annotations

import numpy as np


def risk_coverage_curve(
    scores: np.ndarray, correct: np.ndarray, coverages: tuple[float, ...] = tuple(np.arange(0.05, 1.01, 0.05))
) -> list[dict]:
    """``scores``: higher = more trustworthy. ``correct``: 1 if the
    workload model's prediction was correct, 0 otherwise. Returns one row
    per coverage level."""
    order = np.argsort(-scores)
    sorted_correct = correct[order]
    n = len(scores)
    rows = []
    for cov in coverages:
        k = max(1, int(round(cov * n)))
        accepted = sorted_correct[:k]
        selective_risk = 1.0 - float(accepted.mean())
        rows.append({"coverage": round(float(cov), 4), "selective_risk": selective_risk, "n_accepted": int(k)})
    return rows


def baseline_error(correct: np.ndarray) -> float:
    return 1.0 - float(correct.mean())


def operating_point_metrics(decisions: list[str], correct: np.ndarray) -> dict:
    """Metrics at the policy's actual fixed-threshold operating point.
    ``decisions`` are the string values of ``Decision`` ("ANSWER"/"ABSTAIN"/
    "REVIEW"), aligned with ``correct``."""
    n = len(decisions)
    decisions_arr = np.array(decisions)
    answered_mask = decisions_arr == "ANSWER"
    abstained_mask = decisions_arr != "ANSWER"

    n_answered = int(answered_mask.sum())
    coverage = n_answered / n if n else 0.0
    abstention_rate = float(abstained_mask.mean()) if n else 0.0

    if n_answered > 0:
        accepted_correct = correct[answered_mask]
        selective_risk = 1.0 - float(accepted_correct.mean())
        accuracy_on_answered = float(accepted_correct.mean())
    else:
        selective_risk = None
        accuracy_on_answered = None

    return {
        "coverage": coverage,
        "selective_risk": selective_risk,
        "abstention_rate": abstention_rate,
        "accuracy_on_answered": accuracy_on_answered,
        "n_total": n,
        "n_answered": n_answered,
    }
