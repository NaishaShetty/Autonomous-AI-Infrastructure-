"""Explicit runtime learning/update lifecycle."""
from __future__ import annotations

from typing import Any

from src.failure_memory.memory import FailureMemory

from .contracts import RuntimeEpisode


class RuntimeLearningManager:
    """Apply a completed episode to memory after authoritative persistence.

    The current update policy is deterministic and synchronous. The event is
    persisted by ``RuntimeController`` exactly once; this manager only updates
    the in-process learned representation and reports its version transition.
    """

    def __init__(self, failure_memory: FailureMemory):
        self.failure_memory = failure_memory

    def update(self, episode: RuntimeEpisode) -> dict[str, Any]:
        before = self.failure_memory.memory_version
        event = episode.event
        if event is not None and event.is_failure:
            self.failure_memory.ingest(event, rebuild=True)
        return {
            "policy": "synchronous",
            "memory_version_before": before,
            "memory_version_after": self.failure_memory.memory_version,
            "memory_dirty": self.failure_memory.dirty,
            "pending_update_count": self.failure_memory.pending_update_count,
            "updated": self.failure_memory.memory_version != before,
        }
