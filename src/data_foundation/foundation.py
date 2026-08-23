"""Canonical data-foundation primitives for Phase 3.11 + 3.12.

The module is schema/infrastructure only. It does not train models or alter
any existing V1 runtime behavior.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "3.11.3.12.v1"

class TimestampQuality(str, Enum):
    EXACT = "EXACT"; SYNCHRONIZED = "SYNCHRONIZED"; APPROXIMATE = "APPROXIMATE"; INFERRED = "INFERRED"; UNKNOWN = "UNKNOWN"
class Availability(str, Enum):
    BEFORE = "AVAILABLE_BEFORE_DECISION"; AT = "AVAILABLE_AT_DECISION"; AFTER = "AVAILABLE_AFTER_DECISION"; OUTCOME = "AVAILABLE_AFTER_OUTCOME"; UNKNOWN = "TIMESTAMP_UNKNOWN"; UNAVAILABLE = "UNAVAILABLE"

EVENT_TYPES = ("workload_received","workload_registered","task_created","scheduling_event","resource_requested","resource_allocated","environment_state_observed","node_state_observed","queue_state_observed","prediction_input_snapshot","prediction_generated","prediction_decision","execution_started","telemetry_observed","anomaly_detected","failure_detected","failure_classified","diagnosis_started","diagnosis_completed","recovery_started","recovery_action","recovery_completed","validation_started","validation_completed","workload_completed")


def utc_iso(value: datetime | str | None) -> str | None:
    if value is None: return None
    if isinstance(value, str): value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None: raise ValueError("timezone-naive timestamps are not accepted")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True)
class Provenance:
    source: str
    source_version: str | None = None
    source_record_id: str | None = None
    extraction_method: str | None = None
    transformation: str | None = None
    transformation_version: str | None = None
    timestamp_source: str | None = None
    timestamp_quality: TimestampQuality = TimestampQuality.UNKNOWN
    schema_version: str = SCHEMA_VERSION
    ingestion_time: str | None = None
    processing_time: str | None = None
    checksum: str | None = None

@dataclass(frozen=True)
class CanonicalEvent:
    event_id: str
    event_type: str
    entity_id: str | None = None
    workload_id: str | None = None
    job_id: str | None = None
    task_id: str | None = None
    environment_id: str | None = None
    cluster_id: str | None = None
    node_id: str | None = None
    resource_id: str | None = None
    timestamp: str | None = None
    timestamp_precision: str | None = None
    timestamp_source: str | None = None
    timestamp_timezone: str | None = None
    ingestion_timestamp: str | None = None
    producer: str | None = None
    provenance: Provenance | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    event_version: str = "1"
    parent_event_id: str | None = None
    correlation_id: str | None = None
    source_dataset: str | None = None
    source_record_id: str | None = None

    def __post_init__(self):
        if self.event_type not in EVENT_TYPES: raise ValueError(f"unsupported event_type: {self.event_type}")
        if self.timestamp is not None: utc_iso(self.timestamp)
        if self.ingestion_timestamp is not None: utc_iso(self.ingestion_timestamp)
        if self.provenance is None: raise ValueError("provenance is required; use explicit UNKNOWN fields")

    def to_dict(self):
        value = asdict(self); value["provenance"]["timestamp_quality"] = self.provenance.timestamp_quality.value; return value

@dataclass(frozen=True)
class DecisionTimeContract:
    prediction_input_snapshot_time: str
    prediction_generated_time: str
    prediction_decision_time: str
    relationship: str = "snapshot <= generated <= decision"
    timestamp_quality: TimestampQuality = TimestampQuality.UNKNOWN

    def validate(self):
        times = [datetime.fromisoformat(x.replace("Z", "+00:00")) for x in [self.prediction_input_snapshot_time, self.prediction_generated_time, self.prediction_decision_time]]
        if not (times[0] <= times[1] <= times[2]): raise ValueError("invalid decision-time ordering")
        return True

@dataclass(frozen=True)
class DecisionTimeSnapshot:
    snapshot_id: str
    decision_time: str
    workload_context: Mapping[str, Any] = field(default_factory=dict)
    task_context: Mapping[str, Any] = field(default_factory=dict)
    resource_context: Mapping[str, Any] = field(default_factory=dict)
    scheduler_context: Mapping[str, Any] = field(default_factory=dict)
    queue_context: Mapping[str, Any] = field(default_factory=dict)
    environment_context: Mapping[str, Any] = field(default_factory=dict)
    recent_historical_context: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[Provenance, ...] = ()
    timestamp_quality: TimestampQuality = TimestampQuality.UNKNOWN
    availability: Availability = Availability.AT

    def __post_init__(self):
        utc_iso(self.decision_time)
        if self.availability not in {Availability.AT, Availability.BEFORE}: raise ValueError("snapshot must contain only before/at decision information")

@dataclass(frozen=True)
class EnvironmentIdentity:
    environment_id: str
    source: str
    provenance: str
    hardware_metadata: Mapping[str, Any] = field(default_factory=dict)
    scheduler_metadata: Mapping[str, Any] = field(default_factory=dict)
    collection_period: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    availability_status: str = "REGISTERED_METADATA_ONLY"
    checksum: str | None = None

@dataclass(frozen=True)
class DatasetIdentity:
    dataset_id: str
    dataset_version: str
    source: str
    source_version: str | None
    adapter_version: str
    schema_version: str
    processing_version: str
    checksum: str
    row_count: int
    temporal_range: Mapping[str, Any]
    environment_count: int
    workload_count: int
    failure_count: int

@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    job_id: str | None = None
    task_id: str | None = None
    environment_id: str | None = None
    failure_timestamp: str | None = None
    detection_timestamp: str | None = None
    failure_type: str | None = None
    failure_source: str | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    provenance: Provenance | None = None
    operational_consequence: Mapping[str, Any] = field(default_factory=dict)
    recovery_status: str | None = None


def classify_availability(observation_time: str | None, decision_time: str | None, outcome_time: str | None = None) -> Availability:
    if observation_time is None or decision_time is None: return Availability.UNKNOWN
    obs, dec = datetime.fromisoformat(observation_time.replace("Z", "+00:00")), datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
    if outcome_time is not None and obs >= datetime.fromisoformat(outcome_time.replace("Z", "+00:00")): return Availability.OUTCOME
    if obs < dec: return Availability.BEFORE
    if obs == dec: return Availability.AT
    return Availability.AFTER


def validate_event_order(events: list[CanonicalEvent], order: tuple[str, ...] = ("workload_received", "prediction_generated", "execution_started", "failure_detected", "recovery_started", "recovery_completed", "validation_completed")) -> list[str]:
    by_type = {e.event_type: e for e in events if e.timestamp is not None}
    diagnostics=[]
    for left, right in zip(order, order[1:]):
        if left in by_type and right in by_type:
            l=datetime.fromisoformat(by_type[left].timestamp.replace("Z", "+00:00")); r=datetime.fromisoformat(by_type[right].timestamp.replace("Z", "+00:00"))
            if l > r: diagnostics.append(f"INVALID_ORDER:{left}>{right}")
    return diagnostics

class EnvironmentRegistry:
    def __init__(self): self._items: dict[str, EnvironmentIdentity] = {}
    def register(self, item: EnvironmentIdentity):
        if item.environment_id in self._items: raise ValueError(f"duplicate environment_id: {item.environment_id}")
        self._items[item.environment_id] = item
    def records(self): return [asdict(x) for x in self._items.values()]

class CanonicalBatchAdapter:
    adapter_version = "canonical-batch-adapter-v1"
    def __init__(self, source: str): self.source = source
    def normalize(self, records: list[Mapping[str, Any]]) -> list[CanonicalEvent]:
        return [CanonicalEvent(event_id=str(r["event_id"]), event_type=str(r["event_type"]), timestamp=r.get("timestamp"), source_dataset=self.source, source_record_id=r.get("source_record_id"), provenance=Provenance(source=self.source, source_record_id=r.get("source_record_id"), extraction_method="structured_batch", transformation="identity_normalization", transformation_version=self.adapter_version), payload=r.get("payload", {})) for r in records]


def make_split_contract(name: str, train: list[str], validation: list[str], test: list[str], strategy: str) -> dict[str, Any]:
    if set(train) & set(test): raise ValueError("train/test contamination")
    return {"split_id": name, "strategy": strategy, "train_environments_or_periods": train, "validation_environments_or_periods": validation, "test_environments_or_periods": test, "status": "CONTRACT_ONLY_NOT_EXECUTED"}
