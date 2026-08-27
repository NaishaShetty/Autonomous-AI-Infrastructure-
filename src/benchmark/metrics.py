"""Phase 5.3 metric catalog implementations.

Pathological cases return structured statuses, never fabricated numbers:
- single-class AUROC -> NOT_DEFINED_SINGLE_CLASS (not 0.5)
- zero denominators -> UNDEFINED_ZERO_DENOMINATOR (not 0)
- coverage=0 selective risk -> UNDEFINED_ZERO_COVERAGE (not 0)

ECE uses 10 equal-width bins on [0, 1] (last bin closed on both ends).
Confidence intervals: nonparametric percentile bootstrap for ranking metrics
(AUROC/AUPRC/Brier/ECE) with an explicit seed; Wilson score interval for
binomial rates.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from .constants import (
    BOOTSTRAP_CONFIDENCE_LEVEL,
    BOOTSTRAP_N_RESAMPLES,
    BOOTSTRAP_SEED,
    ECE_N_BINS,
    ALWAYS_FIRES_FAR_THRESHOLD,
)
from .status import (
    NOT_DEFINED_SINGLE_CLASS,
    RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID,
    UNDEFINED_ZERO_COVERAGE,
    UNDEFINED_ZERO_DENOMINATOR,
)


def _as_float_array(x) -> np.ndarray:
    return np.asarray(x, dtype=float)


def wilson_ci(k: int, n: int, z: float = 1.96) -> dict:
    if n <= 0:
        return {
            "point": None,
            "ci_low": None,
            "ci_high": None,
            "status": UNDEFINED_ZERO_DENOMINATOR,
            "method": "wilson",
            "n": n,
            "k": k,
        }
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (z * np.sqrt((p * (1.0 - p) / n) + z2 / (4.0 * n * n))) / denom
    return {
        "point": float(p),
        "ci_low": float(max(0.0, center - margin)),
        "ci_high": float(min(1.0, center + margin)),
        "status": "DEFINED",
        "method": "wilson",
        "n": int(n),
        "k": int(k),
    }


def auroc(y_true, y_score) -> dict:
    y_true = np.asarray(y_true)
    y_score = _as_float_array(y_score)
    if len(y_true) == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0}
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return {
            "value": None,
            "status": NOT_DEFINED_SINGLE_CLASS,
            "n": int(len(y_true)),
            "n_positive": n_pos,
            "n_negative": n_neg,
        }
    return {
        "value": float(roc_auc_score(y_true, y_score)),
        "status": "DEFINED",
        "n": int(len(y_true)),
        "n_positive": n_pos,
        "n_negative": n_neg,
    }


def auprc(y_true, y_score) -> dict:
    y_true = np.asarray(y_true)
    y_score = _as_float_array(y_score)
    if len(y_true) == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0, "positive_base_rate": None}
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())
    base = float(n_pos / len(y_true)) if len(y_true) else None
    if n_pos == 0 or n_neg == 0:
        return {
            "value": None,
            "status": NOT_DEFINED_SINGLE_CLASS,
            "n": int(len(y_true)),
            "positive_base_rate": base,
            "n_positive": n_pos,
            "n_negative": n_neg,
        }
    return {
        "value": float(average_precision_score(y_true, y_score)),
        "status": "DEFINED",
        "n": int(len(y_true)),
        "positive_base_rate": base,
        "n_positive": n_pos,
        "n_negative": n_neg,
    }


def brier(y_true, y_prob) -> dict:
    y_true = _as_float_array(y_true)
    y_prob = _as_float_array(y_prob)
    if len(y_true) == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0}
    return {
        "value": float(np.mean((y_prob - y_true) ** 2)),
        "status": "DEFINED",
        "n": int(len(y_true)),
    }


def ece(y_true, y_prob, n_bins: int = ECE_N_BINS) -> dict:
    """Equal-width ECE on [0, 1] with ``n_bins`` bins (default 10).

    Bin i is [i/B, (i+1)/B) for i < B-1; the last bin is closed [ (B-1)/B, 1 ].
    Empty bins contribute 0 and are recorded with count=0.
    """
    y_true = _as_float_array(y_true)
    y_prob = _as_float_array(y_prob)
    if len(y_true) == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0, "n_bins": n_bins, "binning": "equal_width_[0,1]"}
    if y_prob.min() < 0.0 or y_prob.max() > 1.0:
        raise ValueError("y_prob must be in [0, 1] for ECE")
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(y_true)
    ece_val = 0.0
    bins = []
    for i in range(n_bins):
        lo, hi = float(bin_edges[i]), float(bin_edges[i + 1])
        if i == n_bins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi)
        else:
            mask = (y_prob >= lo) & (y_prob < hi)
        count = int(mask.sum())
        if count == 0:
            bins.append({"lo": lo, "hi": hi, "count": 0, "mean_predicted": None, "empirical_rate": None})
            continue
        mean_predicted = float(y_prob[mask].mean())
        empirical_rate = float(y_true[mask].mean())
        ece_val += (count / n) * abs(mean_predicted - empirical_rate)
        bins.append(
            {
                "lo": lo,
                "hi": hi,
                "count": count,
                "mean_predicted": mean_predicted,
                "empirical_rate": empirical_rate,
            }
        )
    return {
        "value": float(ece_val),
        "status": "DEFINED",
        "n": int(n),
        "n_bins": n_bins,
        "binning": "equal_width_[0,1]",
        "bins": bins,
    }


def risk_coverage(trust_scores, correct, n_points: int = 20) -> dict:
    """risk(c) = error rate among the top-c-fraction most-confident predictions.

    Ties broken by record order (caller must pass a deterministically ordered array).
    Scalar summary is trapezoidal AURC over the evaluated coverage grid.
    """
    trust = _as_float_array(trust_scores)
    corr = np.asarray(correct, dtype=int)
    n = len(trust)
    if n == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0, "curve": []}
    order = np.lexsort((np.arange(n), -trust))  # higher trust first; tie -> original index
    sorted_corr = corr[order]
    curve = []
    coverages = []
    risks = []
    for i in range(1, n_points + 1):
        c = i / n_points
        k = max(1, int(round(c * n)))
        taken = sorted_corr[:k]
        risk = float(1.0 - taken.mean())
        curve.append({"coverage": c, "n": k, "selective_risk": risk})
        coverages.append(c)
        risks.append(risk)
    trapz = getattr(np, "trapezoid", None) or np.trapz
    aurc = float(trapz(np.array(risks), np.array(coverages)) / (coverages[-1] - coverages[0]))
    return {
        "value": aurc,
        "status": "DEFINED",
        "n": int(n),
        "summary": "AURC",
        "direction": "lower_is_better",
        "curve": curve,
    }


def selective_risk(is_answer: np.ndarray, is_correct: np.ndarray) -> dict:
    mask = np.asarray(is_answer, dtype=bool)
    corr = np.asarray(is_correct, dtype=bool)
    n_ans = int(mask.sum())
    if n_ans == 0:
        return {"value": None, "status": UNDEFINED_ZERO_COVERAGE, "n_answered": 0, "n": int(len(mask))}
    err = int((~corr[mask]).sum())
    return {"value": float(err / n_ans), "status": "DEFINED", "n_answered": n_ans, "n": int(len(mask)), **wilson_ci(err, n_ans)}


def coverage_metric(actions: list[str]) -> dict:
    n = len(actions)
    if n == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n": 0}
    n_not_abstain = sum(1 for a in actions if a != "ABSTAIN")
    return {"value": float(n_not_abstain / n), "status": "DEFINED", "n": n, **wilson_ci(n_not_abstain, n)}


def abstention_rate(actions: list[str]) -> dict:
    cov = coverage_metric(actions)
    if cov["value"] is None:
        return cov
    return {**cov, "value": float(1.0 - cov["value"]), "k": cov["n"] - cov["k"]}


def unnecessary_abstention(actions: list[str], would_have_been_correct: np.ndarray) -> dict:
    actions = list(actions)
    would = np.asarray(would_have_been_correct, dtype=bool)
    n_abs = sum(1 for a in actions if a == "ABSTAIN")
    if n_abs == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "n_abstain": 0, "n": len(actions)}
    n_unnec = sum(1 for a, w in zip(actions, would) if a == "ABSTAIN" and bool(w))
    return {"value": float(n_unnec / n_abs), "status": "DEFINED", "n_abstain": n_abs, **wilson_ci(n_unnec, n_abs)}


def final_correctness(actions: list[str], is_correct: np.ndarray) -> dict:
    corr = np.asarray(is_correct, dtype=bool)
    mask = np.array([a in ("ANSWER", "RETRY") for a in actions], dtype=bool)
    n = int(mask.sum())
    if n == 0:
        return {"value": None, "status": UNDEFINED_ZERO_COVERAGE, "n_resolved": 0}
    k = int(corr[mask].sum())
    return {"value": float(k / n), "status": "DEFINED", "n_resolved": n, **wilson_ci(k, n)}


def confusion_counts(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "n": int(len(y_true))}


def precision(y_true, y_pred) -> dict:
    c = confusion_counts(y_true, y_pred)
    denom = c["tp"] + c["fp"]
    if denom == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, **c}
    return {"value": float(c["tp"] / denom), "status": "DEFINED", **c, **wilson_ci(c["tp"], denom)}


def recall(y_true, y_pred) -> dict:
    c = confusion_counts(y_true, y_pred)
    denom = c["tp"] + c["fn"]
    if denom == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, **c}
    return {"value": float(c["tp"] / denom), "status": "DEFINED", **c, **wilson_ci(c["tp"], denom)}


def false_alarm_rate(y_true, y_pred) -> dict:
    c = confusion_counts(y_true, y_pred)
    denom = c["fp"] + c["tn"]
    if denom == 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, **c}
    return {"value": float(c["fp"] / denom), "status": "DEFINED", **c, **wilson_ci(c["fp"], denom)}


def specificity(y_true, y_pred) -> dict:
    far = false_alarm_rate(y_true, y_pred)
    if far["value"] is None:
        return far
    return {**far, "value": float(1.0 - far["value"]), "k": far["tn"]}


def rate(k: int, n: int) -> dict:
    if n <= 0:
        return {"value": None, "status": UNDEFINED_ZERO_DENOMINATOR, "k": k, "n": n}
    return {"value": float(k / n), "status": "DEFINED", **wilson_ci(k, n)}


def bootstrap_metric(
    metric_fn: Callable[[np.ndarray, np.ndarray], float | None],
    y_true,
    y_score,
    *,
    n_resamples: int = BOOTSTRAP_N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    confidence_level: float = BOOTSTRAP_CONFIDENCE_LEVEL,
) -> dict:
    y_true = np.asarray(y_true)
    y_score = _as_float_array(y_score)
    n = len(y_true)
    point = metric_fn(y_true, y_score)
    rng = np.random.default_rng(seed)
    values = []
    n_degenerate = 0
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        v = metric_fn(y_true[idx], y_score[idx])
        if v is None:
            n_degenerate += 1
            continue
        values.append(float(v))
    alpha = 1.0 - confidence_level
    if values:
        arr = np.array(values)
        ci_low = float(np.percentile(arr, 100 * (alpha / 2)))
        ci_high = float(np.percentile(arr, 100 * (1 - alpha / 2)))
        boot_mean = float(arr.mean())
        boot_std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    else:
        ci_low = ci_high = boot_mean = boot_std = None
    return {
        "point_estimate": None if point is None else float(point),
        "bootstrap_mean": boot_mean,
        "bootstrap_std": boot_std,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence_level": confidence_level,
        "n_resamples": n_resamples,
        "n_degenerate_resamples": n_degenerate,
        "seed": seed,
        "method": "nonparametric_percentile_bootstrap",
    }


def auroc_scalar(y_true, y_score) -> float | None:
    r = auroc(y_true, y_score)
    return r["value"]


def auprc_scalar(y_true, y_score) -> float | None:
    r = auprc(y_true, y_score)
    return r["value"]


def brier_scalar(y_true, y_score) -> float | None:
    r = brier(y_true, y_score)
    return r["value"]


def ece_scalar(y_true, y_score) -> float | None:
    r = ece(y_true, y_score)
    return r["value"]


def operating_point_validity(auroc_result: dict, far_result: dict) -> dict:
    """Always-fires protection: high AUROC + FAR≈1 is not operational success."""
    auroc_v = auroc_result.get("value") if isinstance(auroc_result, dict) else auroc_result
    far_v = far_result.get("value") if isinstance(far_result, dict) else far_result
    if auroc_v is None or far_v is None:
        return {
            "status": "NOT_ASSESSABLE",
            "reason": "AUROC or false-alarm-rate undefined",
            "auroc": auroc_v,
            "false_alarm_rate": far_v,
        }
    if far_v >= ALWAYS_FIRES_FAR_THRESHOLD:
        return {
            "status": RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID,
            "reason": f"false_alarm_rate={far_v} >= {ALWAYS_FIRES_FAR_THRESHOLD} (always-fires) regardless of AUROC={auroc_v}",
            "auroc": auroc_v,
            "false_alarm_rate": far_v,
            "operationally_successful": False,
        }
    return {
        "status": "OPERATING_POINT_DEFINED",
        "auroc": auroc_v,
        "false_alarm_rate": far_v,
        "operationally_successful": True,
    }


def ranking_with_ci(y_true, y_score, *, seed: int = BOOTSTRAP_SEED, n_resamples: int = BOOTSTRAP_N_RESAMPLES) -> dict:
    au = auroc(y_true, y_score)
    ap = auprc(y_true, y_score)
    br = brier(y_true, y_score)
    ec = ece(y_true, np.clip(_as_float_array(y_score), 0.0, 1.0))
    rc = risk_coverage(y_score, y_true)
    out = {
        "MET-AUROC": {**au, "ci": bootstrap_metric(auroc_scalar, y_true, y_score, seed=seed, n_resamples=n_resamples)},
        "MET-AUPRC": {**ap, "ci": bootstrap_metric(auprc_scalar, y_true, y_score, seed=seed + 1, n_resamples=n_resamples)},
        "MET-BRIER": {**br, "ci": bootstrap_metric(brier_scalar, y_true, y_score, seed=seed + 2, n_resamples=n_resamples)},
        "MET-ECE": {**{k: v for k, v in ec.items() if k != "bins"}, "bins": ec.get("bins"), "ci": bootstrap_metric(ece_scalar, y_true, np.clip(_as_float_array(y_score), 0.0, 1.0), seed=seed + 3, n_resamples=n_resamples)},
        "MET-RISK-COVERAGE": rc,
    }
    return out


METRIC_IDS = [
    "MET-AUROC", "MET-AUPRC", "MET-BRIER", "MET-ECE", "MET-RISK-COVERAGE",
    "MET-SELECTIVE-RISK", "MET-COVERAGE", "MET-ABSTENTION-RATE", "MET-UNNECESSARY-ABSTENTION",
    "MET-FINAL-CORRECTNESS", "MET-PRECISION", "MET-RECALL", "MET-FALSE-ALARM-RATE",
    "MET-SPECIFICITY", "MET-LEAD-TIME", "MET-USEFUL-LEAD-TIME", "MET-FAILURE-CLASS-ACCURACY",
    "MET-EVIDENCE-CORRECTNESS", "MET-TEMPORAL-INTEGRITY", "MET-CONTRADICTION-HANDLING",
    "MET-UNKNOWN-HANDLING", "MET-UNSUPPORTED-CAUSE-RATE", "MET-FALSE-CAUSAL-ATTRIBUTION-RATE",
    "MET-RECOVERY-SUCCESS-RATE", "MET-UNSAFE-ACTION-RATE", "MET-UNNECESSARY-RECOVERY-RATE",
    "MET-ACTION-SELECTION-ACCURACY", "MET-TIME-COST-OVERHEAD", "MET-VALIDATION-CORRECTNESS",
    "MET-MEMORY-RETRIEVAL-PRECISION", "MET-REPEATED-INCIDENT-ADAPTATION", "MET-DECISION-CHANGE-RATE",
    "MET-RECOVERY-IMPROVEMENT", "MET-CROSS-WORKLOAD-CONTAMINATION", "MET-CROSS-ENVIRONMENT-CONTAMINATION",
    "MET-TEMPORAL-LEAKAGE", "MET-PERSISTENCE-CORRECTNESS", "MET-RANKING-GENERALIZATION-DEGRADATION",
    "MET-OPERATING-POINT-GENERALIZATION", "MET-END-TO-END-RECOVERY-RATE",
    "MET-END-TO-END-UNSAFE-ACTION-RATE", "MET-REPRODUCIBILITY-INDICATOR",
]
# Catalog claims 33 metrics; the JSON file lists more unique metric_id values
# (memory contamination metrics are listed after the 33-count header). We
# implement every metric_id present in PHASE5_3_METRIC_CATALOG.json.


def catalog_metric_count(metric_catalog: dict) -> int:
    return int(metric_catalog.get("_meta", {}).get("total_metrics", len(metric_catalog.get("metrics", []))))
