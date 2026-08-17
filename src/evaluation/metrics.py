"""Phase 3.1 evaluation metrics.

These are NEW infrastructure for Phase 3.1 -- none of this existed in
Phase 2. The Phase 2 risk-coverage harness (``benchmarks/risk_coverage.py``)
is imported and reused unchanged for AURC (per the Phase 3.1 brief's
instruction to preserve the original Phase 2 evaluation code rather than
duplicate or silently modify it), everything else here is additive.

All functions operate on a single, explicit convention documented at each
call site in ``benchmarks/phase3_1_evaluate.py``:

  y_true  : 1 = the event IS the defined failure (workload prediction wrong),
            0 = it is not. This is the target Phase 3.1 evaluates prediction
            of -- see docs/PHASE3_1_EVALUATION_PROTOCOL.md section 1.
  y_score : higher = model judges the event MORE likely to be a failure
            (a "failure risk" score, not a "trust" score -- the opposite
            convention from Phase 2's DecisionPolicy.fuse, which scores
            trustworthiness). Call sites are responsible for using
            ``1 - confidence`` etc. where a Phase 2 component's native
            output is on the opposite convention.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from benchmarks.risk_coverage import risk_coverage_curve


def auroc(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    """Area under the ROC curve. Returns None (not a fabricated number) if
    only one class is present -- AUROC is undefined in that case, not 0.5
    or 1.0."""
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def auprc(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    """Area under the precision-recall curve (average precision)."""
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return None
    return float(average_precision_score(y_true, y_score))


def expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> dict:
    """Standard equal-width-bin Expected Calibration Error:
    ECE = sum_b (|bin_b| / N) * |mean_predicted_prob_b - empirical_rate_b|

    ``y_prob`` must already be in [0, 1] and represent a predicted
    probability of the positive class (y_true=1). For scores that were
    never fit/designed as calibrated probabilities (e.g. Failure Memory's
    similarity-kernel risk), this is reported anyway as an honest diagnostic
    of how far the raw score is from a calibrated probability -- see
    docs/PHASE3_1_EVALUATION_PROTOCOL.md section 8 for why that is still a
    meaningful (if expected-to-be-poor) number to report, not a
    methodological error.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    if not (0.0 <= y_prob.min() and y_prob.max() <= 1.0):
        raise ValueError("y_prob must be in [0, 1]")

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(y_true)
    ece = 0.0
    bin_rows = []
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi)
        else:
            mask = (y_prob >= lo) & (y_prob < hi)
        count = int(mask.sum())
        if count == 0:
            bin_rows.append({"lo": float(lo), "hi": float(hi), "count": 0, "mean_predicted": None, "empirical_rate": None})
            continue
        mean_predicted = float(y_prob[mask].mean())
        empirical_rate = float(y_true[mask].mean())
        ece += (count / n) * abs(mean_predicted - empirical_rate)
        bin_rows.append(
            {"lo": float(lo), "hi": float(hi), "count": count, "mean_predicted": mean_predicted, "empirical_rate": empirical_rate}
        )

    return {"ece": float(ece), "n_bins": n_bins, "bins": bin_rows}


def aurc(trust_scores: np.ndarray, correct: np.ndarray) -> dict:
    """Area under the risk-coverage curve, via the frozen Phase 2
    ``risk_coverage_curve`` (unmodified), trapezoidally integrated over its
    existing 5%-100% (step 5%) coverage grid.

    ``trust_scores``: higher = more trustworthy (NOT a failure-risk score --
    callers pass ``1 - failure_risk`` where needed, matching Phase 2's own
    convention in ``DecisionPolicy.fuse``).
    ``correct``: 1 if the workload prediction was correct, 0 otherwise
    (i.e. the complement of this module's y_true failure label).

    Lower AURC is better (less average selective risk across coverage
    levels). The grid does not extend to coverage=0, so this is an
    approximation over [0.05, 1.0], documented explicitly rather than
    silently extrapolated.
    """
    curve = risk_coverage_curve(np.asarray(trust_scores), np.asarray(correct))
    coverages = np.array([row["coverage"] for row in curve])
    risks = np.array([row["selective_risk"] for row in curve])
    order = np.argsort(coverages)
    trapz = getattr(np, "trapezoid", None) or np.trapz
    value = float(trapz(risks[order], coverages[order]) / (coverages[order][-1] - coverages[order][0]))
    return {"aurc": value, "coverage_range_evaluated": [float(coverages.min()), float(coverages.max())], "curve": curve}


def precision_recall_at_coverage(y_true: np.ndarray, y_score: np.ndarray, coverage: float) -> dict:
    """Treats the top ``coverage`` fraction of samples by y_score (failure
    risk, higher = more likely positive) as "flagged"; computes precision
    and recall of that flagged set against the true failure label.

    ``coverage`` here means "fraction of the test set flagged as high-risk"
    -- the operating point is defined by a fixed, pre-declared fraction, NOT
    by a score threshold chosen after looking at test-set performance (see
    docs/PHASE3_1_EVALUATION_PROTOCOL.md section 6).
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n = len(y_true)
    k = max(1, int(round(coverage * n)))
    order = np.argsort(-y_score)
    flagged = order[:k]
    flagged_mask = np.zeros(n, dtype=bool)
    flagged_mask[flagged] = True

    n_positive = int(y_true.sum())
    true_positives = int(y_true[flagged_mask].sum())
    precision = true_positives / k if k > 0 else None
    recall = (true_positives / n_positive) if n_positive > 0 else None

    return {
        "coverage": coverage,
        "n_flagged": k,
        "n_positive_total": n_positive,
        "true_positives_in_flagged": true_positives,
        "precision": precision,
        "recall": recall,
    }
