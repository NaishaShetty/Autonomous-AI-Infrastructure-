"""Observation ingestion and normalization boundaries for the runtime."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from .contracts import EventNormalizer, Observation, TelemetrySourceType


def _utc(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    raise ValueError("timestamp must be an ISO string or datetime")


def _numeric_mapping(value: Any, field: str) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object of numeric values")
    result: dict[str, float] = {}
    for key, item in value.items():
        if not isinstance(key, str) or isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field} must contain numeric values keyed by strings")
        result[key] = float(item)
    return result


class MappingEventNormalizer:
    """Normalize a mapping without inventing unavailable telemetry.

    The legacy ``context`` field is accepted as a compatibility input and is
    copied into ``features``. Dataset and simulator adapters can provide the
    richer fields directly.
    """

    def normalize(self, raw_event: Mapping[str, Any]) -> Observation:
        if not isinstance(raw_event, Mapping):
            raise ValueError("observation event must be an object")
        workload_id = raw_event.get("workload_id", "default-workload")
        features = raw_event.get("features", raw_event.get("context", {}))
        source = str(raw_event.get("source", "api"))
        raw_source_type = raw_event.get("source_type")
        if raw_source_type is None:
            source_type = {
                "dataset_replay": TelemetrySourceType.DATASET_REPLAY,
                "deterministic_simulator": TelemetrySourceType.SIMULATOR,
                "synthetic_test": TelemetrySourceType.SYNTHETIC_TEST,
                "live": TelemetrySourceType.LIVE,
                "api": TelemetrySourceType.LIVE,
                "structured_mapping": TelemetrySourceType.STRUCTURED_MAPPING,
            }.get(source, TelemetrySourceType.UNKNOWN)
        else:
            try:
                source_type = TelemetrySourceType(str(raw_source_type))
            except ValueError as exc:
                raise ValueError(f"unsupported source_type: {raw_source_type}") from exc
        ingest_timestamp = _utc(raw_event.get("ingest_timestamp")) if raw_event.get("ingest_timestamp") is not None else None
        return Observation(
            observation_id=str(raw_event.get("observation_id") or uuid4()),
            timestamp=_utc(raw_event.get("timestamp")),
            workload_id=str(workload_id),
            model_id=raw_event.get("model_id"),
            model_version=raw_event.get("model_version"),
            deployment_id=raw_event.get("deployment_id"),
            environment_id=raw_event.get("environment_id"),
            ingest_timestamp=ingest_timestamp,
            request_id=raw_event.get("request_id"),
            throughput_per_second=(float(raw_event["throughput_per_second"]) if raw_event.get("throughput_per_second") is not None else None),
            model_confidence=(float(raw_event["model_confidence"]) if raw_event.get("model_confidence") is not None else None),
            predicted_label=raw_event.get("predicted_label"),
            prediction_distribution=_numeric_mapping(raw_event.get("prediction_distribution"), "prediction_distribution"),
            failure_indicators=_numeric_mapping(raw_event.get("failure_indicators"), "failure_indicators"),
            features=_numeric_mapping(features, "features"),
            metrics=_numeric_mapping(raw_event.get("metrics"), "metrics"),
            latency_seconds=(float(raw_event["latency_seconds"]) if raw_event.get("latency_seconds") is not None else None),
            error=(str(raw_event["error"]) if raw_event.get("error") is not None else None),
            resource_signals=_numeric_mapping(raw_event.get("resource_signals"), "resource_signals"),
            environment=dict(raw_event.get("environment") or {}),
            source=source,
            source_type=source_type,
            provenance={**dict(raw_event.get("provenance") or {}), "source_type": source_type.value},
            metadata=dict(raw_event.get("metadata") or {}),
        )


class StaticObservationSource:
    """Deterministic source useful for simulations and adapter tests."""

    def __init__(self, observation: Observation):
        self._observation = observation

    def observe(self) -> Observation:
        return self._observation
