"""Explicit observation sources for runtime, replay, and simulation.

These sources emit the same normalized Observation contract. Dataset replay and
simulation are labeled in provenance so they cannot be mistaken for live
telemetry.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from .contracts import Observation
from .observation import MappingEventNormalizer


@dataclass
class MappingEventSource:
    event: Mapping[str, Any]
    normalizer: MappingEventNormalizer = field(default_factory=MappingEventNormalizer)

    def observe(self) -> Observation:
        return self.normalizer.normalize({**self.event, "source": self.event.get("source", "structured_mapping")})


class DatasetReplaySource:
    """Replay normalized dataset records with explicit replay provenance."""

    def __init__(self, records: Iterable[Mapping[str, Any]], dataset_id: str, normalizer: MappingEventNormalizer | None = None):
        self._records: Iterator[Mapping[str, Any]] = iter(records)
        self.dataset_id = dataset_id
        self.normalizer = normalizer or MappingEventNormalizer()

    def observe(self) -> Observation:
        record = next(self._records)
        return self.normalizer.normalize({
            **record,
            "source": "dataset_replay",
            "provenance": {**dict(record.get("provenance") or {}), "source_type": "dataset_replay", "dataset_id": self.dataset_id},
        })


class DeterministicSimulatorSource:
    """Finite deterministic source for controlled runtime experiments."""

    def __init__(self, records: Iterable[Mapping[str, Any]], scenario_id: str, normalizer: MappingEventNormalizer | None = None):
        self._records: Iterator[Mapping[str, Any]] = iter(records)
        self.scenario_id = scenario_id
        self.normalizer = normalizer or MappingEventNormalizer()
        self._step = 0

    def observe(self) -> Observation:
        record = next(self._records)
        self._step += 1
        return self.normalizer.normalize({
            **record,
            "source": "deterministic_simulator",
            "provenance": {**dict(record.get("provenance") or {}), "source_type": "simulator", "scenario_id": self.scenario_id, "step": self._step},
        })
