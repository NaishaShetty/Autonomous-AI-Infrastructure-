"""Task 9: experience ingestion / normalization pipeline.

    raw episode (source-specific dict)
        -> source adapter (src/failure_experience/sources/*.py) produces a
           NormalizedRecord (a plain dict with a fixed, documented key set --
           see REQUIRED_KEYS / OPTIONAL_KEYS below)
        -> ingest_record(): schema validation, provenance attachment,
           deterministic id assignment, eligibility assessment
        -> FailureExperience

This module is intentionally source-agnostic: it knows nothing about
Alibaba/AIOps/AgentRx/synthetic-episode formats. Each source adapter's job
is to map its raw records into the ``NormalizedRecord`` contract; ingest.py
enforces that contract once, in one place, so validation cannot silently
diverge per source.

Determinism: given the same NormalizedRecord and the same
``ingestion_timestamp`` (passed in explicitly, never taken from wall-clock
inside this module -- see module docstring of schema.py on why that matters
for reproducibility), ``ingest_record`` always produces a byte-identical
FailureExperience (same experience_id, same field values).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from .eligibility import assess
from .schema import (
    Diagnosis,
    DiagnosisSource,
    FailureExperience,
    FailureInfo,
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
)

REQUIRED_KEYS = {
    "source_dataset", "episode_id", "occurrence_key", "observed_at",
    "workload_id", "workload_type", "failure_type", "diagnosis_source",
    "recovery_status", "validation_result", "outcome_final_status",
}


class IngestionError(Exception):
    """Raised for one record; callers batch these, they never propagate
    past ingest_batch (Task 9: 'log invalid/incomplete records
    appropriately' -- not crash the whole batch)."""


@dataclass
class IngestionResult:
    experiences: list[FailureExperience] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)  # {"record_ref": ..., "reason": str}

    @property
    def total(self) -> int:
        return len(self.experiences) + len(self.errors)


def _failure_signature(failure_type: str, affected_component: Optional[str], workload_type: str) -> str:
    import hashlib
    raw = f"{failure_type}|{affected_component or ''}|{workload_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def ingest_record(record: dict, ingestion_timestamp: datetime, data_integrity: bool = True) -> FailureExperience:
    """Validates and converts one NormalizedRecord into a FailureExperience.
    Raises IngestionError (never a bare pydantic ValidationError) on any
    problem, with the offending record's identifying keys attached."""
    missing = REQUIRED_KEYS - record.keys()
    if missing:
        raise IngestionError(f"missing required keys {sorted(missing)} in record "
                              f"{record.get('episode_id', '<unknown>')}")

    try:
        experience_id = deterministic_experience_id(
            record["source_dataset"], record["episode_id"], record["occurrence_key"],
        )

        workload_context = WorkloadContext(
            workload_id=record["workload_id"],
            workload_type=record["workload_type"],
            model_id=record.get("model_id"),
            model_version=record.get("model_version"),
            environment=record.get("environment"),
            deployment_config=record.get("deployment_config") or {},
            runtime_context=record.get("runtime_context") or {},
        )

        observations = Observations(
            telemetry=record.get("telemetry") or {},
            resource_metrics=record.get("resource_metrics") or {},
            performance_metrics=record.get("performance_metrics") or {},
            log_events=record.get("log_events") or [],
            anomaly_signals=record.get("anomaly_signals") or {},
            system_state=record.get("system_state") or {},
        )

        failure = FailureInfo(
            failure_type=record["failure_type"],
            failure_signature=_failure_signature(
                record["failure_type"], record.get("affected_component"), record["workload_type"],
            ),
            severity=record.get("severity"),
            detection_timestamp=record.get("detection_timestamp"),
            affected_component=record.get("affected_component"),
            failure_status=record.get("failure_status", "open"),
        )

        diagnosis = Diagnosis(
            suspected_cause=record.get("diagnosis_suspected_cause"),
            confidence=record.get("diagnosis_confidence"),
            evidence=record.get("diagnosis_evidence") or [],
            method=record.get("diagnosis_method"),
            method_version=record.get("diagnosis_method_version"),
            source=DiagnosisSource(record["diagnosis_source"]),
        )

        recovery = RecoveryInfo(
            status=RecoveryStatus(record["recovery_status"]),
            candidate_actions=record.get("recovery_candidate_actions") or [],
            selected_action=record.get("recovery_selected_action"),
            action_rationale=record.get("recovery_action_rationale"),
            action_confidence=record.get("recovery_action_confidence"),
            execution_result=record.get("recovery_execution_result"),
            rollback_info=record.get("recovery_rollback_info"),
            retry_count=record.get("recovery_retry_count", 0),
            recovery_policy_version=record.get("recovery_policy_version"),
        )

        validation = ValidationInfo(
            pre_recovery_state=record.get("validation_pre_state") or {},
            post_recovery_state=record.get("validation_post_state") or {},
            validation_metrics=record.get("validation_metrics") or {},
            validation_result=ValidationResult(record["validation_result"]),
            residual_failure=record.get("validation_residual_failure"),
            regression_indicators=record.get("validation_regression_indicators") or [],
            validated_cause=record.get("validation_validated_cause"),
        )

        outcome = OutcomeInfo(
            recovery_success=record.get("outcome_recovery_success"),
            task_success=record.get("outcome_task_success"),
            recovery_latency_seconds=record.get("outcome_recovery_latency_seconds"),
            recovery_cost=record.get("outcome_recovery_cost"),
            attempts=record.get("outcome_attempts", 0),
            final_status=record["outcome_final_status"],
        )

        provenance = Provenance(
            source_dataset=record["source_dataset"],
            source_workload=record.get("provenance_source_workload"),
            detector_version=record.get("provenance_detector_version"),
            diagnosis_component_version=record.get("provenance_diagnosis_component_version"),
            recovery_policy_version=record.get("provenance_recovery_policy_version"),
            validation_component_version=record.get("provenance_validation_component_version"),
            ingestion_timestamp=ingestion_timestamp,
            dataset_content_hash=record.get("provenance_dataset_content_hash"),
            experiment_id=record.get("provenance_experiment_id"),
            raw_record_ref=record.get("provenance_raw_record_ref") or {},
        )

        temporal = record.get("temporal") or {}
        temporal_lineage = TemporalLineage(
            observation_ts=temporal.get("observation_ts"),
            detection_ts=temporal.get("detection_ts"),
            diagnosis_ts=temporal.get("diagnosis_ts"),
            recovery_decision_ts=temporal.get("recovery_decision_ts"),
            recovery_execution_ts=temporal.get("recovery_execution_ts"),
            validation_ts=temporal.get("validation_ts"),
            outcome_ts=temporal.get("outcome_ts"),
        )

        eligibility = assess(
            observations, diagnosis, recovery.status.value, validation, outcome,
            provenance, temporal_lineage, data_integrity=data_integrity,
        )

        lifecycle = _infer_lifecycle(diagnosis, recovery, validation, outcome)

        identity = Identity(
            experience_id=experience_id,
            episode_id=record["episode_id"],
            observed_at=record["observed_at"],
            created_at=ingestion_timestamp,
            lifecycle_status=lifecycle,
        )

        return FailureExperience(
            identity=identity, workload_context=workload_context, observations=observations,
            failure=failure, diagnosis=diagnosis, recovery=recovery, validation=validation,
            outcome=outcome, provenance=provenance, temporal_lineage=temporal_lineage,
            eligibility=eligibility,
        )
    except (ValidationError, ValueError, KeyError) as exc:
        raise IngestionError(f"{record.get('episode_id', '<unknown>')}: {exc}") from exc


def _infer_lifecycle(diagnosis: Diagnosis, recovery: RecoveryInfo, validation: ValidationInfo, outcome: OutcomeInfo) -> LifecycleStatus:
    if validation.validation_result != ValidationResult.NOT_PERFORMED:
        return LifecycleStatus.VALIDATED
    if recovery.status == RecoveryStatus.ATTEMPTED:
        return LifecycleStatus.RECOVERY_EXECUTED
    if diagnosis.source != DiagnosisSource.NOT_ATTEMPTED:
        return LifecycleStatus.DIAGNOSED
    return LifecycleStatus.DETECTED


def ingest_batch(records: list[dict], ingestion_timestamp: datetime) -> IngestionResult:
    result = IngestionResult()
    for record in records:
        try:
            result.experiences.append(ingest_record(record, ingestion_timestamp))
        except IngestionError as exc:
            result.errors.append({
                "record_ref": record.get("episode_id", "<unknown>"),
                "source_dataset": record.get("source_dataset", "<unknown>"),
                "reason": str(exc),
            })
    return result
