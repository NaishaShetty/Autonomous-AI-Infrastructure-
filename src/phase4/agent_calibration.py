"""Phase 4.7 -- ``AgentDecisionCalibrationProfile``: a mechanism-aware
decision policy for the agent self-consistency uncertainty signal.

Why this exists (read ``docs/archive/PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md``
lines 186-204 first): wiring the agent task family through the existing,
unmodified ``src.decision.policy.DecisionPolicy`` (``answer_threshold=0.70``,
``abstain_threshold=0.40``) produced a real, honestly-reported finding --
at ``n_samples=5``, every wrong answer's risk score (``1 - agreement_rate``)
landed in the REVIEW band, so RETRY-with-more-samples (which a real,
isolated measurement shows reliably helps -- the calibration curve in that
report) never fired autonomously. That is not a bug in the generic policy;
the generic policy was never calibrated against this mechanism's actual
discrete score distribution (self-consistency agreement at n=5 only takes
values in {0.6, 0.8, 1.0} for a majority-of-5, plus lower values when there
is no majority) or against the actual yield of retrying.

This module does NOT lower the generic thresholds until RETRY starts
firing (explicitly forbidden by the project's own calibration protocol).
It instead fits a SEPARATE, disjointly-scoped policy via a proper
TRAIN/CALIBRATION/TEST split (mirroring the discipline already used for
the ML failure predictor in ``prediction_training.py``: fit on one split,
threshold-select on a second, evaluate once, frozen, on a third), reusing
the same ``AutonomyDecision`` output shape and the same downstream
safety-gate / circuit-breaker / planner machinery -- it changes ONLY which
band of agreement_rate is treated as "confident enough to act
autonomously", based on a documented expected-utility calculation, not a
re-implementation of the decision/safety/execution machinery.

Honesty notes:
  - There is no trainable model here -- ``AgentDecisionCalibrationProfile``
    is a calibrated empirical-frequency table over four fixed agreement-
    rate buckets, not an ML model. The TRAIN split is therefore legitimately
    UNUSED by this specific profile (the CALIBRATION split alone is enough
    to estimate the two frequencies the utility formula needs); TRAIN is
    still kept disjoint from CALIBRATION/TEST so the same seed-range
    protocol composes cleanly with any future model-based profile that
    would need it, and so this module cannot be accused of secretly using
    "training" data for calibration.
  - The bucket edges (0.0-0.4 / 0.4-0.6 / 0.6-0.8 / 0.8-1.0) are fixed
    before any evaluation, reused unmodified from the bucket convention
    already reported in PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md
    -- not re-derived from this profile's own calibration data.
  - The utility costs below (``COST_WRONG_ANSWER`` etc.) are fixed,
    documented judgment calls, not fit or tuned against any evaluation
    outcome. They are deliberately simple (same discipline as
    ``MonitoringBaseline`` / ``agent_task.BASE_ERROR_RATE``): an incorrect
    autonomous answer is the worst outcome (cost 1.0, same scale as the
    benefit of a correct answer); a real retry costs a small, fixed amount
    (extra compute, here modeled as proportional to the extra samples it
    consumes); REVIEW costs a human's attention but never risks a wrong
    autonomous action; ABSTAIN costs slightly more than REVIEW because it
    forfeits an eventual human-verified answer entirely rather than
    deferring to one.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .agent_task import generate_task, run_self_consistency
from .architecture import AutonomyState, Prediction

CALIBRATION_VERSION = "phase4.7-agent-decision-calibration-v1"

# Fixed before any evaluation; reused unmodified from the bucket convention
# already used to report the self-consistency calibration curve in
# PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md.
AGREEMENT_BUCKETS: tuple[tuple[float, float], ...] = ((0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0))

# Fixed, documented utility constants (see module docstring). Not tuned
# against any evaluation outcome.
BENEFIT_CORRECT = 1.0
COST_WRONG_ANSWER = 1.0
COST_RETRY_PER_EXTRA_SAMPLE = 0.01  # small, real compute cost per additional sample
COST_REVIEW = 0.30
COST_ABSTAIN = 0.40

# Reused unmodified from AgentRecoveryExecutor's own default
# (agent_recovery.py) -- not re-derived here, so a profile-authorized
# RETRY and the executor that actually performs it agree on how many
# samples the retry will use.
RETRY_SAMPLE_INCREASE_FACTOR = 2
# A per-episode safety cap independent of (and narrower than) the
# cross-episode RecoveryCircuitBreaker in guardrails.py: refuses to ever
# propose a retry that would need more than this many samples, regardless
# of how favorable the utility calculation looks, so a chain of doublings
# cannot spiral within a single episode. The pipeline's own retry path
# (agent_recovery.py) is one-shot per episode today, so this mostly
# documents the intended ceiling rather than actively firing, but it is a
# a real, checked bound, not a comment.
MAX_RETRY_N_SAMPLES = 40

_LAPLACE_ALPHA = 1.0  # add-1 smoothing so no bucket ever reports a hard 0.0/1.0 probability


@dataclass(frozen=True)
class AgentSplitSeeds:
    """Disjoint seed ranges, mirroring ``prediction_training.SplitSeeds``.
    Every seed belongs to exactly one split; no seed used to fit or
    threshold-select the profile is ever reused for its evaluation."""

    train: range
    calibration: range
    test: range

    def __post_init__(self) -> None:
        t, c, e = set(self.train), set(self.calibration), set(self.test)
        if t & c or t & e or c & e:
            raise ValueError("train/calibration/test seed ranges must be disjoint")


@dataclass(frozen=True)
class BucketStats:
    bucket: tuple[float, float]
    n_observed: int
    n_correct: int
    n_retry_observed: int
    n_retry_correct: int

    @property
    def p_correct(self) -> float:
        return (self.n_correct + _LAPLACE_ALPHA) / (self.n_observed + 2 * _LAPLACE_ALPHA)

    @property
    def p_retry_success(self) -> float:
        return (self.n_retry_correct + _LAPLACE_ALPHA) / (self.n_retry_observed + 2 * _LAPLACE_ALPHA)


def _bucket_for(agreement_rate: float) -> tuple[float, float]:
    for lo, hi in AGREEMENT_BUCKETS:
        if agreement_rate <= hi or hi == AGREEMENT_BUCKETS[-1][1]:
            if agreement_rate >= lo:
                return (lo, hi)
    return AGREEMENT_BUCKETS[-1]


def _estimate_bucket_stats(seeds: Iterable[int], base_n_samples: int, retry_n_samples: int) -> dict[tuple[float, float], BucketStats]:
    counts: dict[tuple[float, float], list[int]] = {b: [0, 0, 0, 0] for b in AGREEMENT_BUCKETS}
    for seed in seeds:
        instance = generate_task(seed)
        base = run_self_consistency(instance, n_samples=base_n_samples, base_seed=seed)
        bucket = _bucket_for(base.agreement_rate)
        counts[bucket][0] += 1
        counts[bucket][1] += int(base.is_correct)
        retry = run_self_consistency(instance, n_samples=retry_n_samples, base_seed=seed)
        counts[bucket][2] += 1
        counts[bucket][3] += int(retry.is_correct)
    return {
        b: BucketStats(bucket=b, n_observed=c[0], n_correct=c[1], n_retry_observed=c[2], n_retry_correct=c[3])
        for b, c in counts.items()
    }


@dataclass(frozen=True)
class UtilityBreakdown:
    answer: float
    retry: float
    review: float
    abstain: float


@dataclass(frozen=True)
class AgentDecisionCalibrationProfile:
    """Fitted, frozen policy: agreement-rate bucket -> {ANSWER, RETRY,
    ABSTAIN, REVIEW}, chosen by maximizing a documented expected-utility
    formula over per-bucket empirical probabilities estimated on the
    CALIBRATION split only. Exposes the same ``decide(prediction) ->
    AutonomyDecision``-shaped output as ``AbstentionAwareDecisionPolicy``
    so it drops into ``AutonomyPipeline`` without changing the safety
    gate, planner, executor, or validator."""

    bucket_stats: Mapping[tuple[float, float], BucketStats]
    calibration_seed_range: tuple[int, int]
    profile_version: str = CALIBRATION_VERSION

    @classmethod
    def fit(cls, seeds: AgentSplitSeeds, base_n_samples: int = 5, retry_n_samples: int | None = None) -> "AgentDecisionCalibrationProfile":
        """Fits on ``seeds.calibration`` only (see module honesty notes on
        why ``seeds.train`` is unused by this particular, non-ML profile).
        ``seeds.test`` is never touched here."""
        retry_n = retry_n_samples if retry_n_samples is not None else base_n_samples * RETRY_SAMPLE_INCREASE_FACTOR
        stats = _estimate_bucket_stats(seeds.calibration, base_n_samples, retry_n)
        return cls(
            bucket_stats=stats,
            calibration_seed_range=(seeds.calibration.start, seeds.calibration.stop),
        )

    def utility_for_bucket(self, bucket: tuple[float, float], current_n_samples: int) -> UtilityBreakdown:
        stats = self.bucket_stats[bucket]
        p_correct = stats.p_correct
        p_retry = stats.p_retry_success
        retry_n = current_n_samples * RETRY_SAMPLE_INCREASE_FACTOR
        extra_samples = retry_n - current_n_samples

        u_answer = p_correct * BENEFIT_CORRECT - (1.0 - p_correct) * COST_WRONG_ANSWER
        if retry_n <= MAX_RETRY_N_SAMPLES:
            u_retry = p_retry * BENEFIT_CORRECT - (1.0 - p_retry) * COST_WRONG_ANSWER - COST_RETRY_PER_EXTRA_SAMPLE * extra_samples
        else:
            u_retry = -math.inf  # safety cap: never propose a retry beyond MAX_RETRY_N_SAMPLES
        u_review = -COST_REVIEW
        u_abstain = -COST_ABSTAIN
        return UtilityBreakdown(answer=u_answer, retry=u_retry, review=u_review, abstain=u_abstain)

    def decide(self, prediction: Prediction, current_n_samples: int) -> "AgentAutonomyDecision":
        agreement_rate = 1.0 - prediction.score
        bucket = _bucket_for(agreement_rate)
        stats = self.bucket_stats.get(bucket)
        if stats is None:
            # A bucket with zero calibration observations still has a
            # well-defined (Laplace-smoothed 0.5/0.5) BucketStats via
            # fit(); this branch only guards a profile constructed by hand
            # without every bucket populated.
            stats = BucketStats(bucket=bucket, n_observed=0, n_correct=0, n_retry_observed=0, n_retry_correct=0)
        utilities = self.utility_for_bucket(bucket, current_n_samples)

        # Tie-break order favors caution: REVIEW > ABSTAIN > RETRY > ANSWER
        # when utilities are exactly equal (documented, not tuned).
        ranked = sorted(
            [("REVIEW", utilities.review), ("ABSTAIN", utilities.abstain), ("RETRY", utilities.retry), ("ANSWER", utilities.answer)],
            key=lambda kv: kv[1],
        )
        action, best_utility = ranked[-1]

        next_state = {
            "ANSWER": AutonomyState.DIAGNOSING.value,
            "RETRY": AutonomyState.DIAGNOSING.value,
            "ABSTAIN": AutonomyState.ABSTAINED.value,
            "REVIEW": AutonomyState.ESCALATED.value,
        }[action]

        rationale = (
            f"agreement_rate={agreement_rate:.3f} bucket={bucket} "
            f"p_correct={stats.p_correct:.3f} p_retry_success={stats.p_retry_success:.3f} "
            f"utilities(answer={utilities.answer:.3f}, retry={utilities.retry:.3f}, "
            f"review={utilities.review:.3f}, abstain={utilities.abstain:.3f}) -> {action}"
        )
        return AgentAutonomyDecision(
            decision=action,
            fused_score=stats.p_correct,
            next_state=next_state,
            rationale=rationale,
            policy_version=self.profile_version,
            bucket=bucket,
            utilities=utilities,
        )


@dataclass(frozen=True)
class AgentAutonomyDecision:
    """Same shape as ``decision.AutonomyDecision`` (decision/fused_score/
    next_state/rationale/policy_version) plus the extra fields the
    calibration evaluation needs, so it is a drop-in return value for
    ``AutonomyPipeline.run_agent_task``'s existing ``decision.decision``
    checks without changing their string-comparison logic."""

    decision: str  # "ANSWER" | "RETRY" | "ABSTAIN" | "REVIEW"
    fused_score: float
    next_state: str
    rationale: str
    policy_version: str
    bucket: tuple[float, float]
    utilities: UtilityBreakdown
