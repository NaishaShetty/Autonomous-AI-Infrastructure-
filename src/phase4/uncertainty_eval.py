"""Phase 4.6 -- task-family-agnostic uncertainty/correctness evaluation
harness.

Consumes a sequence of ``UncertaintyRecord`` (one per evaluated example,
any task family) and computes the metric set the project's evaluation
protocol requires: error-detection AUROC/AUPRC, Brier score, expected
calibration error (ECE), a risk-coverage curve with selective accuracy at
fixed coverage levels, and plain accuracy/error-rate. Every record keeps
its own ``mechanism`` label (self-consistency disagreement / softmax
margin / softmax span confidence, ...) so metrics can be computed and
reported per-family without collapsing genuinely different uncertainty
signals into one.

Convention: ``confidence`` is always in [0, 1] and always means "the
mechanism's estimate of the probability this example's answer is
correct" -- higher is more confident. Callers translate their own native
signal into this convention once, at the boundary (e.g. self-consistency
agreement_rate is already this; classification uses softmax probability
of the predicted class; QA uses span_confidence). This mirrors the
project's existing single-canonical-scale discipline for ``confidence``
in ``src/schema/events.py``.

Metrics that are mathematically undefined for a given sample (e.g. AUROC
with only one class present) are reported as ``None`` with an explanatory
note, never silently coerced to 0 -- per the project's "never represent
unavailable metrics as zero" rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

METRICS_VERSION = "phase4.6-uncertainty-eval-v1"
COVERAGE_LEVELS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1)
N_CALIBRATION_BINS = 10


@dataclass(frozen=True)
class UncertaintyRecord:
    example_id: str
    is_correct: bool
    confidence: float  # in [0, 1]; higher = more confident the answer is correct
    mechanism: str
    task_family: str


def _expected_calibration_error(is_correct: np.ndarray, confidence: np.ndarray, n_bins: int = N_CALIBRATION_BINS) -> float:
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(confidence)
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        in_bin = (confidence > lo) & (confidence <= hi) if i > 0 else (confidence >= lo) & (confidence <= hi)
        count = int(in_bin.sum())
        if count == 0:
            continue
        bin_acc = float(is_correct[in_bin].mean())
        bin_conf = float(confidence[in_bin].mean())
        ece += (count / n) * abs(bin_acc - bin_conf)
    return ece


def _risk_coverage_curve(is_correct: np.ndarray, confidence: np.ndarray) -> list[dict]:
    order = np.argsort(-confidence)  # most confident first
    sorted_correct = is_correct[order]
    n = len(sorted_correct)
    curve = []
    for coverage in COVERAGE_LEVELS:
        k = max(1, int(round(coverage * n)))
        kept = sorted_correct[:k]
        selective_accuracy = float(kept.mean()) if len(kept) > 0 else None
        curve.append({"coverage": coverage, "n_kept": int(k), "selective_accuracy": selective_accuracy})
    return curve


def compute_uncertainty_metrics(records: Sequence[UncertaintyRecord]) -> dict:
    if not records:
        return {"n": 0, "note": "no records provided"}

    mechanisms = {r.mechanism for r in records}
    task_families = {r.task_family for r in records}

    is_correct = np.array([1.0 if r.is_correct else 0.0 for r in records])
    confidence = np.array([r.confidence for r in records])
    is_error = 1.0 - is_correct  # label for "error detection": 1 = wrong answer
    risk = 1.0 - confidence  # risk score: higher = more likely wrong

    n = len(records)
    n_correct = int(is_correct.sum())
    accuracy = n_correct / n
    n_classes_present = len(set(is_error.tolist()))

    result: dict = {
        "n": n,
        "mechanism": sorted(mechanisms) if len(mechanisms) > 1 else next(iter(mechanisms)),
        "task_family": sorted(task_families) if len(task_families) > 1 else next(iter(task_families)),
        "accuracy": accuracy,
        "error_rate": 1.0 - accuracy,
        "n_correct": n_correct,
        "n_incorrect": n - n_correct,
    }

    if n_classes_present < 2:
        result["auroc_error_detection"] = None
        result["auprc_error_detection"] = None
        result["auroc_note"] = "undefined: only one outcome class (all correct or all incorrect) present in this sample"
    else:
        result["auroc_error_detection"] = float(roc_auc_score(is_error, risk))
        result["auprc_error_detection"] = float(average_precision_score(is_error, risk))

    result["brier_score"] = float(brier_score_loss(is_correct, confidence))
    result["ece"] = _expected_calibration_error(is_correct, confidence)
    result["risk_coverage_curve"] = _risk_coverage_curve(is_correct, confidence)
    result["metrics_version"] = METRICS_VERSION
    return result


def compute_uncertainty_metrics_by_task_family(records: Sequence[UncertaintyRecord]) -> dict:
    """Convenience: computes metrics once overall, and once per distinct
    task_family present, so per-family (mechanism-preserving) numbers are
    always available alongside any pooled view."""
    by_family: dict[str, list[UncertaintyRecord]] = {}
    for r in records:
        by_family.setdefault(r.task_family, []).append(r)
    return {
        "overall": compute_uncertainty_metrics(records),
        "by_task_family": {family: compute_uncertainty_metrics(recs) for family, recs in by_family.items()},
    }
