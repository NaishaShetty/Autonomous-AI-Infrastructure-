"""The canonical FailureExperience representation (active Phase 4.1).

Design constraints (see docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md section 3
for the full rationale):

1. OBSERVATION AND INTERPRETATION ARE SEPARATE TYPES. ``Observations`` and
   ``FailureInfo`` hold only what was measured/detected. ``Diagnosis`` holds
   the system's (or a dataset annotator's) INTERPRETATION of those
   observations, tagged with its own confidence and source, and is never
   silently treated as ground truth. ``ValidationInfo`` is the only place a
   later-confirmed/contradicted cause is recorded, and it does NOT overwrite
   ``Diagnosis`` -- both are kept, so a wrong initial diagnosis is preserved,
   not corrected-in-place.
2. RECOVERY/VALIDATION MAY BE GENUINELY ABSENT. The current real-data
   sources (see src/failure_experience/sources/) do not all provide
   recovery or validation information -- ``RecoveryInfo.status`` and
   ``ValidationInfo.validation_result`` have explicit NOT_OBSERVED /
   NOT_PERFORMED states so an experience with no recovery data is
   distinguishable from an experience whose recovery failed.
3. NOTHING HERE IS "TRAINING DATA" BY DEFAULT. Storing a FailureExperience
   never implies it is safe to learn from -- that is decided by
   ``EligibilityAssessment`` (src/failure_experience/eligibility.py), a
   separate, explicit step downstream of ingestion.
4. This schema is built PARALLEL to, not by extending in place,
   ``src.schema.events.ReliabilityEvent`` (frozen, ``extra="forbid"``, no
   free slots for diagnosis/recovery/validation). A FailureExperience MAY
   be built from a ReliabilityEvent-producing pipeline, but does not
   subclass or mutate ReliabilityEvent.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "4.1.0-active"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LifecycleStatus(str, Enum):
    """Where this experience currently sits in the observation -> outcome
    chain (Task J: temporal lineage). Monotonically advances; never regresses."""

    OBSERVED = "observed"
    DETECTED = "detected"
    DIAGNOSED = "diagnosed"
    RECOVERY_DECIDED = "recovery_decided"
    RECOVERY_EXECUTED = "recovery_executed"
    VALIDATED = "validated"
    CLOSED = "closed"

    @classmethod
    def ordinal(cls, status: "LifecycleStatus") -> int:
        order = [
            cls.OBSERVED, cls.DETECTED, cls.DIAGNOSED, cls.RECOVERY_DECIDED,
            cls.RECOVERY_EXECUTED, cls.VALIDATED, cls.CLOSED,
        ]
        return order.index(status)


class DiagnosisSource(str, Enum):
    """Who/what produced the interpretation in ``Diagnosis`` -- kept
    explicit because a human dataset annotation and a live automated
    diagnosis component carry different trust profiles (Task 3)."""

    AUTOMATED_SYSTEM = "automated_system"
    HUMAN_DATASET_ANNOTATION = "human_dataset_annotation"
    NOT_ATTEMPTED = "not_attempted"


class RecoveryStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"       # a recovery decision was in scope but none was taken
    NOT_OBSERVED = "not_observed"          # the source data has no recovery field at all (structural gap)
    ATTEMPTED = "attempted"


class ValidationResult(str, Enum):
    NOT_PERFORMED = "not_performed"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class FinalStatus(str, Enum):
    """Task 4: the closed set of outcome labels the memory must be able to
    represent without collapsing distinct cases into one bucket."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    ABSTAINED = "abstained"
    ROLLED_BACK = "rolled_back"
    RETRIED = "retried"
    WORSENED = "worsened"          # recovery action made the situation worse (Task 4)
    UNKNOWN = "unknown"


class EligibilityRole(str, Enum):
    """Task 6: explicit distinction between "stored" and "usable for
    learning" -- never conflated."""

    STORED = "stored"
    VALIDATED_USABLE = "validated_usable"
    LEARNING_ELIGIBLE = "learning_eligible"
    EXCLUDED = "excluded"
    QUARANTINED = "quarantined"


# ---------------------------------------------------------------------------
# Sub-objects (A-J from the brief)
# ---------------------------------------------------------------------------


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Identity(_Frozen):
    """A. Identity."""

    experience_id: str
    episode_id: str
    observed_at: datetime
    created_at: datetime
    lifecycle_status: LifecycleStatus = LifecycleStatus.OBSERVED


class WorkloadContext(_Frozen):
    """B. Workload context."""

    workload_id: str
    workload_type: str
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    environment: Optional[str] = None
    deployment_config: dict = Field(default_factory=dict)
    runtime_context: dict = Field(default_factory=dict)


class Observations(_Frozen):
    """C. Observations -- facts only, no interpretation (Task 3)."""

    telemetry: dict[str, float] = Field(default_factory=dict)
    resource_metrics: dict[str, float] = Field(default_factory=dict)
    performance_metrics: dict[str, float] = Field(default_factory=dict)
    log_events: list[str] = Field(default_factory=list)
    anomaly_signals: dict[str, float] = Field(default_factory=dict)
    system_state: dict = Field(default_factory=dict)

    def completeness(self) -> float:
        """Fraction of the 6 observation slots that are non-empty. Used by
        EligibilityAssessment.observation_completeness -- a plain,
        documented count, not a fabricated weighting."""
        slots = [self.telemetry, self.resource_metrics, self.performance_metrics,
                 self.log_events, self.anomaly_signals, self.system_state]
        return sum(1 for s in slots if s) / len(slots)


class FailureInfo(_Frozen):
    """D. Failure."""

    failure_type: str
    failure_signature: str
    severity: Optional[str] = None
    detection_timestamp: Optional[datetime] = None
    affected_component: Optional[str] = None
    failure_status: str = "open"


class Diagnosis(_Frozen):
    """E. Diagnosis -- an INTERPRETATION, never ground truth (Task 3)."""

    suspected_cause: Optional[str] = None
    confidence: Optional[float] = None
    evidence: list[str] = Field(default_factory=list)
    method: Optional[str] = None
    method_version: Optional[str] = None
    source: DiagnosisSource = DiagnosisSource.NOT_ATTEMPTED
    later_validated: Optional[bool] = None  # filled in only by a later ValidationInfo/outcome update, see Task 5

    @model_validator(mode="after")
    def _confidence_range(self) -> "Diagnosis":
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Diagnosis.confidence must be in [0,1], got {self.confidence}")
        return self


class RecoveryInfo(_Frozen):
    """F. Recovery."""

    status: RecoveryStatus = RecoveryStatus.NOT_OBSERVED
    candidate_actions: list[str] = Field(default_factory=list)
    selected_action: Optional[str] = None
    action_rationale: Optional[str] = None
    action_confidence: Optional[float] = None
    execution_result: Optional[str] = None
    rollback_info: Optional[str] = None
    retry_count: int = 0
    recovery_policy_version: Optional[str] = None


class ValidationInfo(_Frozen):
    """G. Validation."""

    pre_recovery_state: dict = Field(default_factory=dict)
    post_recovery_state: dict = Field(default_factory=dict)
    validation_metrics: dict[str, float] = Field(default_factory=dict)
    validation_result: ValidationResult = ValidationResult.NOT_PERFORMED
    residual_failure: Optional[bool] = None
    regression_indicators: list[str] = Field(default_factory=list)
    validated_cause: Optional[str] = None  # Task 5: the later-confirmed cause, kept SEPARATE from Diagnosis.suspected_cause


class OutcomeInfo(_Frozen):
    """H. Outcome."""

    recovery_success: Optional[bool] = None
    task_success: Optional[bool] = None
    recovery_latency_seconds: Optional[float] = None
    recovery_cost: Optional[float] = None
    attempts: int = 0
    final_status: FinalStatus = FinalStatus.UNKNOWN


class Provenance(_Frozen):
    """I. Provenance."""

    source_dataset: str
    source_workload: Optional[str] = None
    detector_version: Optional[str] = None
    diagnosis_component_version: Optional[str] = None
    recovery_policy_version: Optional[str] = None
    validation_component_version: Optional[str] = None
    memory_schema_version: str = SCHEMA_VERSION
    ingestion_timestamp: datetime
    dataset_content_hash: Optional[str] = None
    experiment_id: Optional[str] = None
    raw_record_ref: dict = Field(default_factory=dict)  # identifying keys only, never full free-text payload


class TemporalLineage(_Frozen):
    """J. Temporal lineage -- must reconstruct the chronological chain
    observation -> detection -> diagnosis -> recovery decision -> recovery
    execution -> validation -> outcome. Fields are Optional (a given
    experience may not have reached every stage) but where two are both
    present, ordering is validated non-decreasing."""

    observation_ts: Optional[datetime] = None
    detection_ts: Optional[datetime] = None
    diagnosis_ts: Optional[datetime] = None
    recovery_decision_ts: Optional[datetime] = None
    recovery_execution_ts: Optional[datetime] = None
    validation_ts: Optional[datetime] = None
    outcome_ts: Optional[datetime] = None

    def ordered_events(self) -> list[tuple[str, datetime]]:
        fields = [
            ("observation", self.observation_ts), ("detection", self.detection_ts),
            ("diagnosis", self.diagnosis_ts), ("recovery_decision", self.recovery_decision_ts),
            ("recovery_execution", self.recovery_execution_ts), ("validation", self.validation_ts),
            ("outcome", self.outcome_ts),
        ]
        return [(name, ts) for name, ts in fields if ts is not None]

    @model_validator(mode="after")
    def _monotonic(self) -> "TemporalLineage":
        present = self.ordered_events()
        for (_, a), (_, b) in zip(present, present[1:]):
            if b < a:
                raise ValueError(f"TemporalLineage out of order: {present}")
        return self


class EligibilityAssessment(_Frozen):
    """Task 6: explicit evidence-quality fields, not an unjustified single
    trust score. ``role`` is the ONLY field learning code should branch on;
    the rest are its documented inputs, kept visible for audit."""

    observation_completeness: float
    provenance_completeness: float
    diagnosis_status: str          # "not_attempted" | "unvalidated" | "validated" | "contradicted"
    outcome_certainty: str          # "unknown" | "partial" | "certain"
    validation_status: ValidationResult
    data_integrity: bool
    temporal_validity: bool
    role: EligibilityRole
    reasons: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level FailureExperience
# ---------------------------------------------------------------------------


class FailureExperience(_Frozen):
    identity: Identity
    workload_context: WorkloadContext
    observations: Observations
    failure: FailureInfo
    diagnosis: Diagnosis
    recovery: RecoveryInfo
    validation: ValidationInfo
    outcome: OutcomeInfo
    provenance: Provenance
    temporal_lineage: TemporalLineage
    eligibility: EligibilityAssessment
    schema_version: str = SCHEMA_VERSION

    def content_hash(self) -> str:
        """Deterministic, order-independent identity hash used for
        idempotency (re-ingesting the same raw record twice must not create
        a duplicate stored row) and store-version content hashing."""
        payload = self.model_dump_json(exclude={"provenance": {"ingestion_timestamp"}})
        return hashlib.sha256(payload.encode()).hexdigest()


def deterministic_experience_id(source_dataset: str, episode_id: str, occurrence_key: str) -> str:
    """Reproducible id -- NOT random -- so re-ingesting the same source
    record always yields the same ``experience_id`` (idempotency, Task 13
    item 19)."""
    raw = f"{source_dataset}|{episode_id}|{occurrence_key}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
