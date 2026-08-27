"""Phase 5.3 baseline catalog (10 baselines).

Each baseline function takes the same evaluation-split instances a real
system/task would see and returns scores/decisions in the same shape as the
metric functions expect, so a baseline is always scored with exactly the
metric code path used for the "system" result -- never a shortcut formula.

All randomness is explicitly seeded (constants.py); no unseeded random/
numpy.random call appears anywhere in this module.
"""
from __future__ import annotations

import numpy as np

from .constants import (
    FEATURE_PERM_SEED,
    RANDOM_BASELINE_SEED,
    RANDOM_POLICY_SEED,
    SHUFFLE_CONTROL_SEED,
)

BASELINE_IDS = [
    "BASE-RANDOM",
    "BASE-ALWAYS-ANSWER",
    "BASE-ALWAYS-ABSTAIN",
    "BASE-GENERIC-POLICY",
    "BASE-CALIBRATED-MECHANISM-AWARE",
    "BASE-SIMPLE-STATISTICAL-PREDICTOR",
    "BASE-NO-MEMORY-CONTROL",
    "BASE-NO-RETRY-CONTROL",
    "BASE-PREDICTOR-DISABLED-CONTROL",
    "BASE-RAW-CONFIDENCE",
]


def base_random_scores(n: int, *, seed: int = RANDOM_BASELINE_SEED) -> np.ndarray:
    """BASE-RANDOM: score drawn uniformly at random, independent of input."""
    rng = np.random.default_rng(seed)
    return rng.uniform(0.0, 1.0, size=n)


def base_raw_confidence_scores(raw_confidence: np.ndarray) -> np.ndarray:
    """BASE-RAW-CONFIDENCE: the agent's own uncalibrated signal, used directly."""
    return np.asarray(raw_confidence, dtype=float)


def ctrl_shuffled_label(y_true: np.ndarray, *, seed: int = SHUFFLE_CONTROL_SEED) -> np.ndarray:
    """CTRL-SHUFFLED-LABEL: labels shuffled relative to (fixed) scores."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y_true).copy()
    perm = rng.permutation(len(y))
    return y[perm]


def ctrl_feature_permutation(y_score: np.ndarray, *, seed: int = FEATURE_PERM_SEED) -> np.ndarray:
    """CTRL-FEATURE-PERMUTATION: feature/score values permuted across instances."""
    rng = np.random.default_rng(seed)
    s = np.asarray(y_score, dtype=float).copy()
    perm = rng.permutation(len(s))
    return s[perm]


def ctrl_constant_score(n: int, value: float = 0.5) -> np.ndarray:
    """CTRL-CONSTANT-SCORE: a constant predictor, ignoring all input."""
    return np.full(n, float(value))


def base_always_answer(n: int) -> list[str]:
    return ["ANSWER"] * n


def base_always_abstain(n: int) -> list[str]:
    return ["ABSTAIN"] * n


def ctrl_random_policy(n: int, *, seed: int = RANDOM_POLICY_SEED) -> list[str]:
    rng = np.random.default_rng(seed)
    draws = rng.uniform(0.0, 1.0, size=n)
    return ["ANSWER" if d >= 0.5 else "ABSTAIN" for d in draws]


def fit_threshold_maximizing_margin(
    scores_fit: np.ndarray, correct_fit: np.ndarray, *, min_coverage: float = 0.0
) -> float:
    """Fit a single ANSWER/ABSTAIN threshold on a fitting split only.

    Chooses the threshold (candidate = each observed score) minimizing
    selective risk among candidates whose resulting coverage >= min_coverage.
    Ties broken by lower threshold (higher coverage), deterministic.
    """
    scores = np.asarray(scores_fit, dtype=float)
    correct = np.asarray(correct_fit, dtype=bool)
    n = len(scores)
    if n == 0:
        return 0.5
    candidates = sorted(set(scores.tolist()))
    best_t = candidates[0]
    best_risk = 1.0
    for t in candidates:
        answer_mask = scores >= t
        cov = float(answer_mask.mean())
        if cov < min_coverage or answer_mask.sum() == 0:
            continue
        risk = float((~correct[answer_mask]).mean())
        if risk < best_risk or (risk == best_risk and t < best_t):
            best_risk = risk
            best_t = t
    return float(best_t)


def apply_threshold_policy(scores: np.ndarray, threshold: float) -> list[str]:
    return ["ANSWER" if s >= threshold else "ABSTAIN" for s in np.asarray(scores, dtype=float)]


def fit_temperature_scale(scores_fit: np.ndarray, correct_fit: np.ndarray) -> float:
    """Fit a single scalar temperature T minimizing NLL on calibration split.

    scores are treated as pre-calibration probabilities in (0, 1); the
    calibrated probability is p_T = clip(p ** (1/T), eps, 1-eps) rescaled to
    stay in [0, 1] via sigmoid-logit temperature scaling. This is a
    documented, simple, deterministic procedure -- not claimed to be the
    unique valid calibration method, only the one this implementation uses.
    """
    p = np.clip(np.asarray(scores_fit, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(correct_fit, dtype=float)
    logits = np.log(p / (1 - p))
    grid = np.linspace(0.05, 5.0, 200)
    best_T, best_nll = 1.0, float("inf")
    for T in grid:
        q = 1.0 / (1.0 + np.exp(-logits / T))
        q = np.clip(q, 1e-6, 1 - 1e-6)
        nll = float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))
        if nll < best_nll:
            best_nll = nll
            best_T = float(T)
    return best_T


def apply_temperature_scale(scores: np.ndarray, temperature: float) -> np.ndarray:
    p = np.clip(np.asarray(scores, dtype=float), 1e-6, 1 - 1e-6)
    logits = np.log(p / (1 - p))
    q = 1.0 / (1.0 + np.exp(-logits / temperature))
    return np.clip(q, 0.0, 1.0)
