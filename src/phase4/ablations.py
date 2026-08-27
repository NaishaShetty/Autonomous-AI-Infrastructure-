"""Phase 4.10 -- minimal, additive ablation helpers for the final
integrated evaluation. Each helper wraps an existing, unmodified
component rather than forking it, so every ablation differs from the
full-loop configuration in exactly one dimension.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .agent_calibration import AgentDecisionCalibrationProfile
from .architecture import Prediction
from src.data_foundation.foundation import Provenance, TimestampQuality
from .prediction import _clip01


class NullUncertaintyPredictor:
    """'Predictor OFF' ablation: returns a fixed, uninformative score for
    every episode, regardless of the agent's real self-consistency
    agreement rate. Same call signature as ``AgentUncertaintyPredictor``,
    so it drops into ``AutonomyPipeline(agent_predictor=...)`` unchanged.
    A constant score of 0.5 is maximally uninformative under the
    RISK_ONLY fusion rule (``fused_score = 1 - risk = 0.5``), landing
    every episode in the same decision band regardless of what actually
    happened -- the honest "this signal carries no information" control."""

    version = "phase4.10-null-uncertainty-predictor-v1"

    def __init__(self, fixed_score: float = 0.5):
        self.fixed_score = _clip01(fixed_score)

    def predict_from_events(
        self,
        job_id: str,
        events_prefix: Sequence[Mapping[str, Any]],
        configured_timeout_seconds: float | None,
        run_start_iso: str,
        at_time_iso: str,
        workload_type: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> Prediction:
        return Prediction(
            prediction_id=f"prediction:{job_id}:{at_time_iso}",
            job_id=job_id,
            snapshot_id=f"snapshot:{job_id}:{at_time_iso}",
            decision_time=at_time_iso,
            score=self.fixed_score,
            provenance=Provenance(
                source="phase4.10-null-uncertainty-predictor", source_version=self.version,
                extraction_method="fixed_constant", transformation="none", transformation_version=self.version,
                timestamp_source="n/a", timestamp_quality=TimestampQuality.EXACT,
            ),
        )


@dataclass(frozen=True)
class RetryDisabledCalibrationProfile:
    """'Retry OFF' ablation: wraps a fitted ``AgentDecisionCalibrationProfile``
    and remaps any RETRY decision it would have made to REVIEW instead --
    the same downstream consequence the generic policy already has for
    REVIEW (diagnosis/planning still run for observability, but the
    SAFETY_CHECK gate in ``pipeline.py`` never lets execution proceed).
    Everything else (ANSWER/ABSTAIN, the rationale, the fused_score) is
    passed through unchanged, so this isolates exactly one dimension:
    whether RETRY is ever an available action, not a different
    uncertainty estimate or a different underlying profile."""

    base_profile: AgentDecisionCalibrationProfile

    def decide(self, prediction: Prediction, current_n_samples: int):
        decision = self.base_profile.decide(prediction, current_n_samples)
        # Both "RETRY" and "ANSWER" permit AutonomyPipeline.run_agent_task's
        # DIAGNOSING->PLANNING->SAFETY_CHECK->EXECUTING path (see
        # pipeline.py: `entry_state = DIAGNOSING if decision.decision in
        # ("ANSWER", "RETRY") else ESCALATED`), and RuleBasedRecoveryPlanner
        # picks RETRY as its top candidate for AGENT_INCORRECT_ANSWER
        # regardless of which of those two labels produced the decision
        # (the diagnosis, not the decision label, drives the planner's
        # choice). So a genuine "retry can never execute" ablation must
        # remap BOTH labels to REVIEW, not only ones literally named
        # "RETRY" -- remapping only "RETRY" would still let the rare
        # unanimous-but-wrong self-consistency vote (which this profile
        # can legitimately label "ANSWER", see agent_calibration.py) reach
        # the planner and execute a real retry.
        if decision.decision not in ("RETRY", "ANSWER"):
            return decision
        from .architecture import AutonomyState
        from .agent_calibration import AgentAutonomyDecision

        return AgentAutonomyDecision(
            decision="REVIEW", fused_score=decision.fused_score, next_state=AutonomyState.ESCALATED.value,
            rationale=decision.rationale + f" [retry-disabled ablation: {decision.decision} remapped to REVIEW]",
            policy_version=decision.policy_version + "+retry-disabled", bucket=decision.bucket, utilities=decision.utilities,
        )
