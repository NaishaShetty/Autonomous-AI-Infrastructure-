"""Phase 3.6.2: risk tiers, threshold derivation, cost model, and decision
metrics.

Reuses ``src.schema.events.Decision`` (ANSWER/ABSTAIN/REVIEW) for the
underlying action -- no new action type is added to that frozen schema.
Adds a Phase-3.6-specific ``RiskTier`` (LOW/MEDIUM/HIGH/CRITICAL) that
maps onto those three actions, matching
``configs/phase3_6_decision_recovery_protocol.json.decision_tiers``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.schema.events import Decision

TIER_PERCENTILES = {"t_50": 50, "t_80": 80, "t_95": 95}


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


TIER_ACTION = {
    RiskTier.LOW: Decision.ANSWER,
    RiskTier.MEDIUM: Decision.REVIEW,
    RiskTier.HIGH: Decision.ABSTAIN,
    RiskTier.CRITICAL: Decision.ABSTAIN,
}

RECOVERY_ELIGIBLE_TIERS = {RiskTier.CRITICAL}


@dataclass(frozen=True)
class TierThresholds:
    """t_50/t_80/t_95: the 50th/80th/95th percentile of a candidate's
    risk-score distribution on regime-2 data, computed ONCE per
    (candidate, seed) before any regime-3/4 sample is scored."""

    t_50: float
    t_80: float
    t_95: float

    @classmethod
    def derive(cls, regime2_scores: np.ndarray) -> "TierThresholds":
        return cls(
            t_50=float(np.percentile(regime2_scores, TIER_PERCENTILES["t_50"])),
            t_80=float(np.percentile(regime2_scores, TIER_PERCENTILES["t_80"])),
            t_95=float(np.percentile(regime2_scores, TIER_PERCENTILES["t_95"])),
        )


def assign_tier(score: float, thresholds: TierThresholds) -> RiskTier:
    if score >= thresholds.t_95:
        return RiskTier.CRITICAL
    if score >= thresholds.t_80:
        return RiskTier.HIGH
    if score >= thresholds.t_50:
        return RiskTier.MEDIUM
    return RiskTier.LOW


# -- cost model -----------------------------------------------------------

DEFAULT_COST_MODEL = {
    "answer_correct": 0.0,
    "answer_incorrect": 5.0,
    "review_correct": 0.2,
    "review_incorrect": 5.2,
    "abstain_would_have_been_correct": 1.0,
    "abstain_would_have_been_incorrect": 0.3,
}


def sample_cost(action: Decision, is_failure: int, cost_model: dict) -> float:
    """``is_failure``: 1 if the workload model's prediction on this sample
    would have been wrong (i.e. NOT correct), regardless of what action
    was actually taken -- ground truth, known only for benchmarking."""
    correct = not bool(is_failure)
    if action == Decision.ANSWER:
        return cost_model["answer_correct"] if correct else cost_model["answer_incorrect"]
    if action == Decision.REVIEW:
        return cost_model["review_correct"] if correct else cost_model["review_incorrect"]
    if action == Decision.ABSTAIN:
        return cost_model["abstain_would_have_been_correct"] if correct else cost_model["abstain_would_have_been_incorrect"]
    raise ValueError(action)


def decide_all(scores: np.ndarray, thresholds: TierThresholds) -> tuple[list[RiskTier], list[Decision]]:
    tiers = [assign_tier(float(s), thresholds) for s in scores]
    actions = [TIER_ACTION[t] for t in tiers]
    return tiers, actions


def decision_metrics(actions: list[Decision], y_fail: np.ndarray, cost_model: dict) -> dict:
    """All formulas match
    configs/phase3_6_decision_recovery_protocol.json.evaluation_metrics.decision
    verbatim."""
    n = len(actions)
    actions_arr = np.array([a.value for a in actions])
    answer_or_review = (actions_arr == Decision.ANSWER.value) | (actions_arr == Decision.REVIEW.value)
    abstain = actions_arr == Decision.ABSTAIN.value
    review = actions_arr == Decision.REVIEW.value

    n_attempted = int(answer_or_review.sum())
    n_abstain = int(abstain.sum())
    n_failures_total = int(y_fail.sum())

    unsafe_action_rate = float(y_fail[answer_or_review].mean()) if n_attempted > 0 else None
    false_abstention_rate = float((1 - y_fail[abstain]).mean()) if n_abstain > 0 else None
    failure_recall_among_abstained = float(y_fail[abstain].sum() / n_failures_total) if n_failures_total > 0 else None

    costs = [sample_cost(a, int(f), cost_model) for a, f in zip(actions, y_fail)]

    return {
        "n_total": n,
        "n_answer": int((actions_arr == Decision.ANSWER.value).sum()),
        "n_review": int(review.sum()),
        "n_abstain": n_abstain,
        "unsafe_action_rate": unsafe_action_rate,
        "accepted_task_success_rate": (1.0 - unsafe_action_rate) if unsafe_action_rate is not None else None,
        "abstention_rate": n_abstain / n if n else None,
        "review_rate": float(review.mean()) if n else None,
        "false_abstention_rate": false_abstention_rate,
        "failure_recall_among_abstained": failure_recall_among_abstained,
        "expected_decision_cost": float(np.mean(costs)) if costs else None,
        "utility_retention": n_attempted / n if n else None,
    }
