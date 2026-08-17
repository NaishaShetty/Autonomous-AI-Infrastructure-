"""Phase 3.6.5/3.6.6: deterministic, bounded recovery policy for
CRITICAL-tier samples.

Every action is a pre-specified, deterministic function of already-frozen
components (no new model, no unbounded loop, no runtime-invented action).
See ``configs/phase3_6_decision_recovery_protocol.json.recovery_policy``
for the full spec this module implements.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.data.synthetic import StreamSample
from src.evaluation.attacks import apply_feature_noise
from src.evaluation.decision_policy import RiskTier, TierThresholds, assign_tier
from src.evaluation.diagnosis import diagnose

RETRY_ORDINAL_OFFSET = 100  # documented, reproducible, distinct from every ordinal used elsewhere
MAX_RETRIES = 1


class RecoveryOutcome(str, Enum):
    RECOVERED = "RECOVERED"  # ended in ANSWER/REVIEW after retry or reconfigure
    ROLLED_BACK = "ROLLED_BACK"  # ended in ABSTAIN (the safe fallback)


@dataclass(frozen=True)
class RecoveryResult:
    outcome: RecoveryOutcome
    action_taken: str  # "retry" | "reconfigure" | "rollback" | "none_clean"
    diagnosed_cause: str
    recovered_tier: RiskTier | None
    recovered_correct: bool | None  # only meaningful if outcome == RECOVERED


def attempt_recovery(
    sample: StreamSample,
    original_score: float,
    original_ordinal: int | None,
    seed: int,
    feature_names: list[str],
    workload_predict,
    score_fn,
    b_score_fn,
    thresholds: TierThresholds,
    b_thresholds: TierThresholds,
    condition_id: str,
) -> RecoveryResult:
    """One CRITICAL-tier sample's recovery attempt, per the frozen policy.

    ``workload_predict(x) -> WorkloadPrediction``, ``score_fn(context) ->
    float`` (the acting candidate's risk score, already bound to its
    fitted calibrator/candidate), ``b_score_fn(context) -> float`` (B
    alone, used only by the reconfigure branch). ``original_ordinal`` is
    the attack_ordinal used to generate ``sample`` (None for the clean
    condition, where retry is not attempted at all -- see the module
    docstring)."""
    diagnosed_cause = diagnose(sample.context, feature_names)

    if diagnosed_cause == "clean":
        return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "none_clean", diagnosed_cause, None, None)

    if diagnosed_cause == "feature_noise":
        if original_ordinal is None:
            # The diagnosis rule is imperfect and can misfire on a sample
            # that was NOT actually under a feature_noise condition (e.g.
            # an ordinary clean-condition failure with an unusually large
            # feature magnitude by chance -- see docs section 15/19).
            # There is no attack to re-roll in that case; retrying a
            # deterministic model on an unattacked, unchanged input is
            # provably a no-op, so this falls straight to rollback rather
            # than fabricating a retry. Reported honestly as a
            # misdiagnosis-driven rollback, not hidden.
            return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "misdiagnosed_no_ordinal", diagnosed_cause, None, None)
        retried = apply_feature_noise(
            [sample], feature_names, std=_std_for_condition(condition_id), seed=seed,
            attack_ordinal=original_ordinal + RETRY_ORDINAL_OFFSET,
        )[0]
        new_score = score_fn(retried.context)
        new_tier = assign_tier(new_score, thresholds)
        if new_tier in (RiskTier.LOW, RiskTier.MEDIUM):
            pred = workload_predict(retried)
            correct = pred == retried.label
            return RecoveryResult(RecoveryOutcome.RECOVERED, "retry", diagnosed_cause, new_tier, correct)
        return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "retry", diagnosed_cause, new_tier, None)

    if diagnosed_cause == "feature_dropout":
        b_score = b_score_fn(sample.context)
        new_tier = assign_tier(b_score, b_thresholds)
        if new_tier in (RiskTier.LOW, RiskTier.MEDIUM):
            pred = workload_predict(sample)
            correct = pred == sample.label
            return RecoveryResult(RecoveryOutcome.RECOVERED, "reconfigure", diagnosed_cause, new_tier, correct)
        return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "reconfigure", diagnosed_cause, new_tier, None)

    raise ValueError(diagnosed_cause)


def _std_for_condition(condition_id: str) -> float:
    if condition_id == "feature_noise_mild":
        return 0.5
    if condition_id == "feature_noise_severe":
        return 1.5
    raise ValueError(f"not a feature_noise condition: {condition_id}")
