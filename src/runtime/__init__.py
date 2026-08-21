"""Canonical autonomous runtime package."""

from .builder import RuntimeSystem, build_runtime_system
from .contracts import Observation, RuntimeEpisode, RuntimeState
from .controller import RuntimeController
from .observation import MappingEventNormalizer
from .sources import DatasetReplaySource, DeterministicSimulatorSource, MappingEventSource

__all__ = [
    "MappingEventNormalizer",
    "Observation",
    "RuntimeController",
    "RuntimeEpisode",
    "RuntimeState",
    "RuntimeSystem",
    "build_runtime_system",
    "DatasetReplaySource",
    "DeterministicSimulatorSource",
    "MappingEventSource",
]
