"""Phase 4 historical failure-memory contract and store.

FROZEN CONTRACT -- read this before changing retrieval, scope, or versioning
semantics in this file. This is the contract Decision B of
``docs/PHASE4_5_AUDIT_AND_PLAN.md`` required to exist and be frozen before
any memory-read path was added to diagnosis.

1. Scope. A memory record is eligible for retrieval by
   ``(workload_id, environment_id, failure_class)``. It is NEVER eligible by
   ``run_id`` -- a record produced by the same ``run_id`` as the query is
   always excluded even if it would otherwise match, because "history" must
   never include the current incident's own evidence. This is strictly
   narrower than, and consistent with, the current-run-only guard already
   enforced inside ``DiagnosisEngine._eligible_current_incident`` for
   CURRENT evidence (see the Evaluation Incident 001 fix).

2. Temporal safety. A record is eligible only if its ``recorded_at``
   timestamp is ``<=`` the query's ``at_or_before`` boundary. A record is
   written to the store only after its own episode (diagnosis -> recovery
   -> validation) has fully closed -- ``FailureMemoryStore.add`` is called
   exactly once, by ``LearningManager``, after a ``ValidationOutcome`` exists
   -- so a record can never leak in-progress or future information about the
   run it describes into another run's decision.

3. Versioning. Every successful write increments ``memory_version`` by
   exactly 1, atomically with the write. A retrieval result carries the
   ``memory_version`` it was served from, so any diagnosis or recovery plan
   that consumed memory can always be tied back to a specific, reproducible
   memory snapshot.

4. Relevance. Relevance is failure_class equality (exact match) combined
   with a fixed, un-tuned recency decay:
   ``relevance = 0.5 ** (age_seconds / RELEVANCE_HALF_LIFE_SECONDS)``.
   This is deliberately the simplest thing that can be evaluated -- not a
   similarity search -- per the project's existing "measure influence, do
   not assume it" standard (the Gen 2 precedent in
   ``docs/LEARNING_INFLUENCE_REPORT.md``). ``RELEVANCE_HALF_LIFE_SECONDS``
   is fixed in this file before any ablation is run against it, and must not
   be tuned against evaluation outcomes.

5. What is stored. Only structured, already-derived fields: failure_class,
   root_cause, diagnosis confidence, the action taken, the validated
   outcome, and provenance. No raw stdout/stderr and no free-text beyond
   what the diagnosis evidence already carries.

6. Fail-closed retrieval. If a query's ``workload_id`` or
   ``environment_id`` is missing, retrieval returns an empty result rather
   than falling back to an unscoped search. Under-specified queries must
   never silently widen scope.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

RELEVANCE_HALF_LIFE_SECONDS = 3600.0
MEMORY_CONTRACT_VERSION = "phase4.memory-contract-v1"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    workload_id: str
    environment_id: str
    failure_class: str
    root_cause: str
    diagnosis_confidence: str
    source_run_id: str
    source_diagnosis_id: str
    action_taken: str
    validated_outcome: str
    recorded_at: str
    memory_version: int
    provenance: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryMatch:
    record: MemoryRecord
    relevance: float
    age_seconds: float


class FailureMemoryStore:
    """In-process, append-only historical failure memory.

    Deliberately not shared with, and does not import, ``src.failure_memory``
    or ``src.failure_experience`` (Gen 1/Gen 2 memory implementations). Those
    remain frozen research artifacts on the abandoned trace-replay
    foundation. This is a new, independent implementation scoped to the
    Gen 3 controlled-runtime contracts, per Decision B of
    ``docs/PHASE4_5_AUDIT_AND_PLAN.md``.
    """

    version = MEMORY_CONTRACT_VERSION

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []
        self._memory_version = 0

    @property
    def memory_version(self) -> int:
        return self._memory_version

    def add(
        self,
        *,
        workload_id: str,
        environment_id: str,
        failure_class: str,
        root_cause: str,
        diagnosis_confidence: str,
        source_run_id: str,
        source_diagnosis_id: str,
        action_taken: str,
        validated_outcome: str,
        recorded_at: str,
        provenance: Mapping[str, Any],
    ) -> MemoryRecord:
        if not workload_id or not environment_id or not failure_class:
            raise ValueError("workload_id, environment_id, and failure_class are required to record memory")
        self._memory_version += 1
        record = MemoryRecord(
            memory_id=f"memory:{source_run_id}:{self._memory_version}",
            workload_id=str(workload_id),
            environment_id=str(environment_id),
            failure_class=str(failure_class),
            root_cause=str(root_cause),
            diagnosis_confidence=str(diagnosis_confidence),
            source_run_id=str(source_run_id),
            source_diagnosis_id=str(source_diagnosis_id),
            action_taken=str(action_taken),
            validated_outcome=str(validated_outcome),
            recorded_at=str(recorded_at),
            memory_version=self._memory_version,
            provenance=dict(provenance),
        )
        self._records.append(record)
        return record

    def retrieve(
        self,
        *,
        workload_id: str | None,
        environment_id: str | None,
        failure_class: str,
        exclude_run_id: str,
        at_or_before: str,
        top_k: int = 5,
    ) -> Sequence[MemoryMatch]:
        # Contract item 6: fail closed on under-specified queries.
        if not workload_id or not environment_id:
            return ()
        boundary = _dt(at_or_before)
        matches: list[MemoryMatch] = []
        for record in self._records:
            if record.source_run_id == exclude_run_id:
                continue  # contract item 1: never eligible by run_id
            if record.workload_id != workload_id or record.environment_id != environment_id:
                continue
            if record.failure_class != failure_class:
                continue
            recorded_at = _dt(record.recorded_at)
            if recorded_at > boundary:
                continue  # contract item 2: temporal safety
            age_seconds = max(0.0, (boundary - recorded_at).total_seconds())
            relevance = 0.5 ** (age_seconds / RELEVANCE_HALF_LIFE_SECONDS)
            matches.append(MemoryMatch(record=record, relevance=relevance, age_seconds=age_seconds))
        matches.sort(key=lambda m: m.relevance, reverse=True)
        return tuple(matches[:top_k])

    def prior_outcome_rate(
        self,
        *,
        workload_id: str,
        environment_id: str,
        failure_class: str,
        action: str,
        exclude_run_id: str,
        at_or_before: str,
    ) -> tuple[int, int]:
        """Return (successes, total) for a given action against this
        (workload, environment, failure_class), under the same scope and
        temporal contract as ``retrieve``. Used by the recovery planner to
        avoid re-proposing an action that has already failed repeatedly for
        this exact failure signature -- and by nothing else, so retrieval
        semantics stay in one place."""
        matches = self.retrieve(
            workload_id=workload_id,
            environment_id=environment_id,
            failure_class=failure_class,
            exclude_run_id=exclude_run_id,
            at_or_before=at_or_before,
            top_k=len(self._records) + 1,
        )
        relevant = [m for m in matches if m.record.action_taken == action]
        successes = sum(1 for m in relevant if m.record.validated_outcome == "RECOVERED")
        return successes, len(relevant)
