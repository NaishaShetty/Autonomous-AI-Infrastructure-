"""Canonical contracts for the autonomous runtime control loop.

These contracts are intentionally small. They define the data flow between
runtime stages without replacing the frozen schemas used by historical
experiments. ``FailureExperience`` remains the durable complete-episode model;
these objects are the live controller's stage-local inputs and outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeState(str, Enum):
    OBSERVED = "observed"
    DETECTED = "detected"
    ASSESSING = "assessing"
    ABSTAINED = "abstained"
    DIAGNOSED = "diagnosed"
    RECOVERY_PLANNED = "recovery_planned"
    RECOVERY_EXECUTING = "recovery_executing"
    RECOVERY_VALIDATING = "recovery_validating"
    RECOVERED = "recovered"
    RECOVERY_FAILED = "recovery_failed"
    ESCALATED = "escalated"
    LEARNED = "learned"


class RecoveryAction(str, Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    RECONFIGURE = "reconfigure"
    RETRAIN = "retrain"
    REDEPLOY = "redeploy"
    ABSTAIN = "abstain"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Observation:
    observation_id: str
    timestamp: datetime
    workload_id: str
    features: Mapping[str, float] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    latency_seconds: float | None = None
    error: str | None = None
    resource_signals: Mapping[str, float] = field(default_factory=dict)
    environment: Mapping[str, Any] = field(default_factory=dict)
    model_id: str | None = None
    model_version: str | None = None
    source: str = "unknown"
    provenance: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id must not be empty")
        if not self.workload_id:
            raise ValueError("workload_id must not be empty")
        if self.latency_seconds is not None and self.latency_seconds < 0:
            raise ValueError("latency_seconds must be non-negative")
        for name, values in (("features", self.features), ("metrics", self.metrics), ("resource_signals", self.resource_signals)):
            for key, value in values.items():
                if not isinstance(key, str) or not isinstance(value, (int, float)):
                    raise ValueError(f"{name} must contain numeric values keyed by strings")


@dataclass(frozen=True)
class DetectionResult:
    detected: bool
    failure_type: str | None = None
    severity: str | None = None
    evidence: tuple[str, ...] = ()
    uncertainty: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("detection uncertainty must be in [0, 1]")


@dataclass(frozen=True)
class ReliabilityAssessment:
    confidence: float | None
    risk: float | None
    decision: str
    fused_score: float
    uncertainty: float
    predicted_label: int | None = None
    model_id: str | None = None
    model_version: str | None = None
    calibrator_version: str | None = None
    training_data_id: str | None = None
    configuration: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (("confidence", self.confidence), ("risk", self.risk), ("fused_score", self.fused_score), ("uncertainty", self.uncertainty)):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True)
class DiagnosisResult:
    failure_type: str | None
    likely_causes: tuple[str, ...] = ()
    confidence: float = 0.0
    uncertainty: float = 1.0
    supporting_experience_ids: tuple[str, ...] = ()
    supporting_pattern_ids: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0 or not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("diagnosis confidence and uncertainty must be in [0, 1]")


@dataclass(frozen=True)
class RecoveryPlan:
    candidate_actions: tuple[RecoveryAction, ...]
    selected_action: RecoveryAction
    confidence: float
    rationale: str
    safety_status: str
    feasibility_status: str
    abstained: bool = False
    escalated: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("recovery confidence must be in [0, 1]")
        if self.abstained and self.selected_action not in (RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE):
            raise ValueError("abstained recovery plans must select abstain or escalate")


@dataclass(frozen=True)
class ExecutionResult:
    action: RecoveryAction
    started_at: datetime
    finished_at: datetime
    executor: str
    success: bool
    workload_state: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempt: int = 1


@dataclass(frozen=True)
class ValidationResult:
    status: str
    recovered: bool | None
    reliability_before: float | None
    reliability_after: float | None
    metrics: Mapping[str, float] = field(default_factory=dict)
    rationale: str = ""


@dataclass(frozen=True)
class StateTransition:
    from_state: RuntimeState | None
    to_state: RuntimeState
    timestamp: datetime = field(default_factory=utcnow)
    reason: str = ""


@dataclass
class RuntimeEpisode:
    observation: Observation
    state: RuntimeState = RuntimeState.OBSERVED
    transitions: list[StateTransition] = field(default_factory=list)
    detection: DetectionResult | None = None
    reliability: ReliabilityAssessment | None = None
    retrieved_experiences: list[Any] = field(default_factory=list)
    diagnosis: DiagnosisResult | None = None
    recovery_plan: RecoveryPlan | None = None
    execution: ExecutionResult | None = None
    validation: ValidationResult | None = None
    executions: list[ExecutionResult] = field(default_factory=list)
    validations: list[ValidationResult] = field(default_factory=list)
    action_history: list[RecoveryAction] = field(default_factory=list)
    experience_id: str | None = None
    learning_update: Mapping[str, Any] | None = None
    memory_version_before: int | None = None
    memory_version_after: int | None = None
    event: Any | None = None

    def transition_to(self, state: RuntimeState, reason: str = "") -> None:
        if state == self.state:
            return
        self.transitions.append(StateTransition(self.state, state, reason=reason))
        self.state = state


class ObservationSource(Protocol):
    def observe(self) -> Observation:
        ...


class EventNormalizer(Protocol):
    def normalize(self, raw_event: Mapping[str, Any]) -> Observation:
        ...


class FailureDetector(Protocol):
    def detect(self, observation: Observation) -> DetectionResult:
        ...


class ReliabilityAssessor(Protocol):
    def assess(self, observation: Observation, retrieved: Sequence[Any] = ()) -> ReliabilityAssessment:
        ...


class FailureMemoryPort(Protocol):
    def retrieve(self, context: Mapping[str, float], confidence: float, k: int = 5) -> list[Any]:
        ...

    def risk(self, context: Mapping[str, float], confidence: float) -> float:
        ...


class DiagnosisEngine(Protocol):
    def diagnose(self, observation: Observation, detection: DetectionResult, reliability: ReliabilityAssessment, retrieved: Sequence[Any] = ()) -> DiagnosisResult:
        ...


class RecoveryPlanner(Protocol):
    def plan(self, diagnosis: DiagnosisResult, reliability: ReliabilityAssessment, retrieved: Sequence[Any] = (), operational_context: Mapping[str, Any] | None = None) -> RecoveryPlan:
        ...


class RecoveryExecutor(Protocol):
    def execute(self, plan: RecoveryPlan, observation: Observation, attempt: int = 1) -> ExecutionResult:
        ...


class RecoveryValidator(Protocol):
    def validate(self, observation: Observation, reliability: ReliabilityAssessment, execution: ExecutionResult) -> ValidationResult:
        ...


class ExperienceStore(Protocol):
    def save_episode(self, episode: RuntimeEpisode) -> str:
        ...


class LearningManager(Protocol):
    def update(self, episode: RuntimeEpisode) -> Mapping[str, Any]:
        ...
