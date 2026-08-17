"""Bootstrap confidence intervals.

Method: nonparametric percentile bootstrap. Resample rows (y_true, y_score)
pairs WITH replacement, n times; recompute the metric on each resample;
report the [alpha/2, 1-alpha/2] percentiles of the resulting distribution as
the confidence interval. This is standard, documented, and does not assume
normality of the metric's sampling distribution (which AUROC/AUPRC/ECE do
not generally satisfy for finite samples).

Every parameter that affects the result (resample count, seed, confidence
level) is an explicit, required-or-documented-default argument -- see
``docs/PHASE3_1_EVALUATION_PROTOCOL.md`` section 5 for the values actually
used in the frozen Phase 3.1 protocol.
"""
from __future__ import annotations

from typing import Callable

import numpy as np


def bootstrap_ci(
    metric_fn: Callable[[np.ndarray, np.ndarray], float | None],
    y_true: np.ndarray,
    y_score: np.ndarray,
    n_resamples: int = 1000,
    seed: int = 0,
    confidence_level: float = 0.95,
) -> dict:
    """Returns point estimate (metric on the full, unresampled data), the
    bootstrap mean/std, and a percentile confidence interval.

    Resamples for which ``metric_fn`` returns None (e.g. a resample that by
    chance contains only one class, making AUROC undefined) are excluded
    from the interval and counted in ``n_degenerate_resamples`` -- not
    silently treated as 0 or dropped without a trace.
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n = len(y_true)
    if n != len(y_score):
        raise ValueError("y_true and y_score must have the same length")

    point_estimate = metric_fn(y_true, y_score)

    rng = np.random.default_rng(seed)
    values = []
    n_degenerate = 0
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        v = metric_fn(y_true[idx], y_score[idx])
        if v is None:
            n_degenerate += 1
            continue
        values.append(v)

    alpha = 1.0 - confidence_level
    if values:
        values_arr = np.array(values)
        ci_low = float(np.percentile(values_arr, 100 * (alpha / 2)))
        ci_high = float(np.percentile(values_arr, 100 * (1 - alpha / 2)))
        boot_mean = float(values_arr.mean())
        boot_std = float(values_arr.std(ddof=1)) if len(values_arr) > 1 else 0.0
    else:
        ci_low = ci_high = boot_mean = boot_std = None

    return {
        "point_estimate": point_estimate,
        "bootstrap_mean": boot_mean,
        "bootstrap_std": boot_std,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence_level": confidence_level,
        "n_resamples": n_resamples,
        "n_degenerate_resamples": n_degenerate,
        "seed": seed,
    }
