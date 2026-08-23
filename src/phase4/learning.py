"""Phase 4.4 -- learning feedback loop: recovery outcome -> historical memory.

This is new work, not a port (see ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` section
5.D) -- Gen 2 had a learning manager, but on the abandoned trace-replay
foundation. ``LearningManager.record`` is the only code path in the
repository allowed to call ``FailureMemoryStore.add``, and it is only ever
called after a ``ValidationOutcome`` exists (i.e. after the episode has
actually closed) -- this is what makes memory contract item 2 in
``src/phase4/memory.py`` ("a record is written only after its own episode
has fully closed") true by construction rather than by convention.
"""
from __future__ import annotations

from dataclasses import dataclass

from .memory import FailureMemoryStore, MemoryRecord


@dataclass(frozen=True)
class LearningUpdate:
    recorded: bool
    memory_version: int | None
    reason: str


class LearningManager:
    version = "phase4.4-learning-v1"

    def __init__(self, memory: FailureMemoryStore):
        self.memory = memory

    def record(self, diagnosis, action, validation, failure_class: str, recorded_at: str) -> LearningUpdate:
        if validation.status not in ("RECOVERED", "NOT_RECOVERED"):
            # UNKNOWN and NOT_EXECUTED outcomes are not written to memory --
            # an ambiguous or abstained-on episode must not silently teach
            # future decisions anything, per memory contract item 2/5.
            return LearningUpdate(recorded=False, memory_version=self.memory.memory_version, reason=f"validation status {validation.status!r} is not a closed outcome; not recorded")
        record: MemoryRecord = self.memory.add(
            workload_id=diagnosis.workload_id,
            environment_id=diagnosis.environment_id,
            failure_class=failure_class,
            root_cause=diagnosis.primary_hypothesis.name,
            diagnosis_confidence=diagnosis.confidence,
            source_run_id=diagnosis.run_id,
            source_diagnosis_id=diagnosis.diagnosis_id,
            action_taken=action.action_type,
            validated_outcome=validation.status,
            recorded_at=recorded_at,
            provenance={"source": "phase4-learning-manager", "diagnosis_id": diagnosis.diagnosis_id},
        )
        return LearningUpdate(recorded=True, memory_version=record.memory_version, reason=f"recorded {action.action_type} -> {validation.status} for {failure_class}")
