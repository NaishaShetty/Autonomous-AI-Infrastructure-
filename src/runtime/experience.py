"""Runtime episode persistence built on the existing FailureExperience schema."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.failure_experience.schema import (
    Diagnosis,
    EligibilityAssessment,
    EligibilityRole,
    FailureExperience,
    FailureInfo,
    FinalStatus,
    Identity,
    Observations,
    OutcomeInfo,
    Provenance,
    RecoveryInfo,
    RecoveryStatus,
    TemporalLineage,
    ValidationInfo,
    ValidationResult as ExperienceValidationResult,
    WorkloadContext,
    utcnow,
)

from .contracts import RuntimeEpisode, RuntimeState


class JsonExperienceStore:
    """Append-only JSONL store for runtime episodes.

    The store is intentionally simple and deterministic. It is a runtime
    experience boundary, not a replacement for the frozen experiment stores.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.episodes: list[FailureExperience] = []
        if self.path and self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    self.episodes.append(FailureExperience.model_validate_json(line))

    def save_episode(self, episode: RuntimeEpisode) -> str:
        if episode.detection is None:
            raise ValueError("cannot persist a runtime episode before detection")
        now = utcnow()
        experience_id = str(uuid4())
        validation_result = ExperienceValidationResult.NOT_PERFORMED
        final_status = FinalStatus.UNKNOWN
        recovery_status = RecoveryStatus.NOT_ATTEMPTED
        if episode.validation:
            validation_result = {
                "RECOVERED": ExperienceValidationResult.PASSED,
                "FAILED": ExperienceValidationResult.FAILED,
                "UNCERTAIN": ExperienceValidationResult.NOT_PERFORMED,
            }.get(episode.validation.status, ExperienceValidationResult.NOT_PERFORMED)
            final_status = FinalStatus.SUCCESS if episode.validation.recovered is True else FinalStatus.FAILURE if episode.validation.recovered is False else FinalStatus.UNKNOWN
        if episode.execution:
            recovery_status = RecoveryStatus.ATTEMPTED
        diagnosis = episode.diagnosis
        plan = episode.recovery_plan
        execution = episode.execution
        experience = FailureExperience(
            identity=Identity(experience_id=experience_id, episode_id=episode.observation.observation_id, observed_at=episode.observation.timestamp, created_at=now, lifecycle_status=self._lifecycle(episode.state)),
            workload_context=WorkloadContext(workload_id=episode.observation.workload_id, workload_type="runtime", model_id=episode.observation.model_id, model_version=episode.observation.model_version, environment=str(episode.observation.environment.get("name", "simulated")), runtime_context={**dict(episode.observation.metadata), "memory_version_before": episode.memory_version_before, "memory_version_after": episode.memory_version_after, "reliability_model": {"model_id": episode.reliability.model_id if episode.reliability else None, "model_version": episode.reliability.model_version if episode.reliability else None, "calibrator_version": episode.reliability.calibrator_version if episode.reliability else None, "training_data_id": episode.reliability.training_data_id if episode.reliability else None, "configuration": dict(episode.reliability.configuration) if episode.reliability else {}}, "retrieved_memory": [{"event_id": getattr(getattr(item, "event", item), "event_id", None), "similarity": getattr(item, "similarity", None), "relevant": bool(getattr(item, "relevant", False)), "distance": getattr(item, "distance", None)} for item in episode.retrieved_experiences]}),
            observations=Observations(telemetry=dict(episode.observation.metrics), resource_metrics=dict(episode.observation.resource_signals), system_state={"error": episode.observation.error} if episode.observation.error else {}),
            failure=FailureInfo(failure_type=episode.detection.failure_type or "unknown", failure_signature=":".join(episode.detection.evidence) or "unknown", severity=episode.detection.severity, failure_status="closed" if episode.validation else "open"),
            diagnosis=Diagnosis(suspected_cause=(diagnosis.likely_causes[0] if diagnosis and diagnosis.likely_causes else None), confidence=(diagnosis.confidence if diagnosis else None), evidence=list(diagnosis.evidence if diagnosis else ()), source="automated_system" if diagnosis else "not_attempted"),
            recovery=RecoveryInfo(status=recovery_status, candidate_actions=[a.value for a in plan.candidate_actions] if plan else [], selected_action=(plan.selected_action.value if plan else None), action_rationale=(plan.rationale if plan else None), action_confidence=(plan.confidence if plan else None), execution_result=("success" if execution and execution.success else "failure" if execution else None)),
            validation=ValidationInfo(validation_result=validation_result, residual_failure=(episode.validation.recovered is False if episode.validation else None), validation_metrics=dict(episode.validation.metrics if episode.validation else {})),
            outcome=OutcomeInfo(recovery_success=(episode.validation.recovered if episode.validation else None), task_success=(episode.validation.recovered if episode.validation else None), attempts=(execution.attempt if execution else 0), final_status=final_status),
            provenance=Provenance(source_dataset="runtime", source_workload=episode.observation.workload_id, detector_version="runtime-detector-1", diagnosis_component_version="runtime-diagnosis-1", recovery_policy_version="runtime-policy-1", validation_component_version="runtime-validator-1", ingestion_timestamp=now, experiment_id=episode.observation.metadata.get("experiment_id"), raw_record_ref={"observation_id": episode.observation.observation_id, "source": episode.observation.source, "memory_version_before": episode.memory_version_before, "memory_version_after": episode.memory_version_after}),
            temporal_lineage=self._lineage(episode),
            eligibility=EligibilityAssessment(observation_completeness=1.0 if (episode.observation.metrics or episode.observation.resource_signals or episode.observation.features) else 0.0, provenance_completeness=1.0 if episode.observation.provenance else 0.0, diagnosis_status="validated" if diagnosis else "not_attempted", outcome_certainty="certain" if episode.validation and episode.validation.recovered is not None else "unknown", validation_status=validation_result, data_integrity=True, temporal_validity=True, role=EligibilityRole.LEARNING_ELIGIBLE if episode.validation and episode.validation.recovered is not None else EligibilityRole.STORED, reasons=[]),
        )
        self.episodes.append(experience)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(experience.model_dump_json() + "\n")
        episode.experience_id = experience_id
        return experience_id

    def retrieve(self, limit: int = 5) -> list[FailureExperience]:
        return list(reversed(self.episodes[-limit:]))

    @staticmethod
    def _lifecycle(state: RuntimeState):
        mapping = {
            RuntimeState.OBSERVED: "observed", RuntimeState.DETECTED: "detected", RuntimeState.ASSESSING: "detected", RuntimeState.ABSTAINED: "detected", RuntimeState.DIAGNOSED: "diagnosed", RuntimeState.RECOVERY_PLANNED: "recovery_decided", RuntimeState.RECOVERY_EXECUTING: "recovery_executed", RuntimeState.RECOVERY_VALIDATING: "validated", RuntimeState.RECOVERED: "closed", RuntimeState.RECOVERY_FAILED: "closed", RuntimeState.ESCALATED: "closed", RuntimeState.LEARNED: "closed",
        }
        from src.failure_experience.schema import LifecycleStatus
        return LifecycleStatus(mapping[state])

    @staticmethod
    def _lineage(episode: RuntimeEpisode) -> TemporalLineage:
        timestamps = {transition.to_state: transition.timestamp for transition in episode.transitions}
        return TemporalLineage(observation_ts=episode.observation.timestamp, detection_ts=timestamps.get(RuntimeState.DETECTED), diagnosis_ts=timestamps.get(RuntimeState.DIAGNOSED), recovery_decision_ts=timestamps.get(RuntimeState.RECOVERY_PLANNED), recovery_execution_ts=timestamps.get(RuntimeState.RECOVERY_EXECUTING), validation_ts=timestamps.get(RuntimeState.RECOVERY_VALIDATING), outcome_ts=utcnow())
