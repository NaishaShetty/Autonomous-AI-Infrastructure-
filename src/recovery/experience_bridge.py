"""Bridge from a completed Active Phase 4.3 ``RecoveryEpisode`` into the
canonical ``FailureExperience`` representation (Active Phase 4.1, PASS).

Per the Phase 4.3 brief section 18: reuse ``src.failure_experience`` as the
canonical experience representation rather than building a second, competing
schema. This module is purely additive -- it does not modify
``src.failure_experience.schema`` (no gap was found requiring an extension:
``RecoveryInfo``/``ValidationInfo``/``OutcomeInfo`` already had every field
this bridge needs, matching the Active Phase 4.1 report's own "Phase 4.2+
readiness" note referenced in the post-4.2 reassessment).
"""
from __future__ import annotations

from src.failure_experience.schema import (
    Diagnosis,
    DiagnosisSource,
    EligibilityAssessment,
    EligibilityRole,
    FailureExperience,
    FailureInfo,
    FinalStatus,
    Identity,
    LifecycleStatus,
    Observations,
    OutcomeInfo,
    Provenance,
    RecoveryInfo,
    RecoveryStatus,
    TemporalLineage,
    ValidationInfo,
    ValidationResult,
    WorkloadContext,
    deterministic_experience_id,
    utcnow,
)
from src.recovery.schema import RecoveryEpisode, ValidatedOutcome

_OUTCOME_TO_VALIDATION_RESULT = {
    ValidatedOutcome.SUCCESS: ValidationResult.PASSED,
    ValidatedOutcome.PARTIAL_SUCCESS: ValidationResult.PARTIAL,
    ValidatedOutcome.FAILURE: ValidationResult.FAILED,
    ValidatedOutcome.UNSAFE: ValidationResult.FAILED,
    ValidatedOutcome.TIMEOUT: ValidationResult.NOT_PERFORMED,
    ValidatedOutcome.UNRECOVERABLE: ValidationResult.FAILED,
}

_OUTCOME_TO_FINAL_STATUS = {
    ValidatedOutcome.SUCCESS: FinalStatus.SUCCESS,
    ValidatedOutcome.PARTIAL_SUCCESS: FinalStatus.PARTIAL_SUCCESS,
    ValidatedOutcome.FAILURE: FinalStatus.FAILURE,
    ValidatedOutcome.UNSAFE: FinalStatus.WORSENED,
    ValidatedOutcome.TIMEOUT: FinalStatus.UNKNOWN,
    ValidatedOutcome.UNRECOVERABLE: FinalStatus.FAILURE,
}

CONTROLLED_SOURCE_DATASET = "phase4_3_controlled_recovery"


def to_failure_experience(episode: RecoveryEpisode) -> FailureExperience:
    """Convert one resolved (scenario + selection + transition) episode into
    a ``FailureExperience``. Requires ``policy_selection`` and ``transition``
    to be populated (i.e. this is for STORING completed episodes, not for
    what a policy sees at decision time -- see schema.py's ``DecisionContext``
    for that boundary)."""
    if episode.policy_selection is None or episode.transition is None:
        raise ValueError("to_failure_experience requires a resolved episode (selection + transition present)")

    ctx = episode.scenario.decision_context
    now = utcnow()
    experience_id = deterministic_experience_id(
        CONTROLLED_SOURCE_DATASET, episode.episode_id, episode.scenario.scenario_id,
    )

    outcome = episode.transition.outcome
    validation_result = _OUTCOME_TO_VALIDATION_RESULT[outcome]
    final_status = _OUTCOME_TO_FINAL_STATUS[outcome]

    return FailureExperience(
        identity=Identity(
            experience_id=experience_id,
            episode_id=episode.episode_id,
            observed_at=now,
            created_at=now,
            lifecycle_status=LifecycleStatus.CLOSED,
        ),
        workload_context=WorkloadContext(
            workload_id=episode.scenario.scenario_id,
            workload_type=ctx.workload_type,
            environment="controlled",
        ),
        observations=Observations(
            anomaly_signals={"symptom_pattern_is_a": 1.0 if ctx.symptom_pattern == "A" else 0.0},
            system_state={"severity": ctx.severity},
        ),
        failure=FailureInfo(
            failure_type=ctx.family.value,
            failure_signature=f"{ctx.family.value}:{ctx.symptom_pattern}:{ctx.severity}",
            severity=ctx.severity,
            failure_status="closed",
        ),
        diagnosis=Diagnosis(
            suspected_cause=None,  # by construction: hidden_cause is NEVER copied into the stored experience's
            source=DiagnosisSource.NOT_ATTEMPTED,  # decision-visible fields -- see benchmarks/phase4_3_recovery_leakage_audit.py
        ),
        recovery=RecoveryInfo(
            status=RecoveryStatus.ATTEMPTED,
            candidate_actions=[a.value for a in ctx.candidate_actions],
            selected_action=episode.policy_selection.selected_action.value,
            action_rationale=episode.policy_selection.rationale,
            action_confidence=episode.policy_selection.confidence,
            execution_result=outcome.value,
            recovery_policy_version=f"{episode.policy_selection.policy_id}:{episode.policy_selection.policy_version}",
        ),
        validation=ValidationInfo(
            validation_result=validation_result,
            residual_failure=outcome in (ValidatedOutcome.FAILURE, ValidatedOutcome.UNRECOVERABLE, ValidatedOutcome.UNSAFE),
            validation_metrics={
                "recovery_latency_seconds": episode.transition.recovery_latency_seconds,
                "recovery_cost": episode.transition.recovery_cost,
            },
        ),
        outcome=OutcomeInfo(
            recovery_success=outcome == ValidatedOutcome.SUCCESS,
            task_success=outcome in (ValidatedOutcome.SUCCESS, ValidatedOutcome.PARTIAL_SUCCESS),
            recovery_latency_seconds=episode.transition.recovery_latency_seconds,
            recovery_cost=episode.transition.recovery_cost,
            attempts=1,
            final_status=final_status,
        ),
        provenance=Provenance(
            source_dataset=CONTROLLED_SOURCE_DATASET,
            source_workload=ctx.family.value,
            recovery_policy_version=f"{episode.policy_selection.policy_id}:{episode.policy_selection.policy_version}",
            ingestion_timestamp=now,
            experiment_id=episode.provenance.protocol_version,
            raw_record_ref={
                "scenario_id": episode.scenario.scenario_id,
                "split": episode.provenance.split.value,
                "source_type": episode.provenance.source_type.value,  # always "controlled" -- never omitted
                "generator_version": episode.provenance.generator_version,
            },
        ),
        temporal_lineage=TemporalLineage(
            observation_ts=now, detection_ts=now, recovery_decision_ts=now,
            recovery_execution_ts=now, validation_ts=now, outcome_ts=now,
        ),
        eligibility=EligibilityAssessment(
            observation_completeness=1.0,
            provenance_completeness=1.0,
            diagnosis_status="not_attempted",
            outcome_certainty="certain",
            validation_status=validation_result,
            data_integrity=True,
            temporal_validity=True,
            role=EligibilityRole.EXCLUDED,  # controlled data is never auto-promoted into a "learning eligible" real-evidence pool
            reasons=["source_type=controlled: excluded from real-evidence learning-eligible pool by policy, not a data-quality defect"],
        ),
    )
