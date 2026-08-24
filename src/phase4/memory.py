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

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

RELEVANCE_HALF_LIFE_SECONDS = 3600.0
MEMORY_CONTRACT_VERSION = "phase4.memory-contract-v1"

# Phase 4.5 gap 2: durable storage. This is a SCHEMA version for the SQLite
# table layout itself (bumped only if columns/types change), independent of
# ``MEMORY_CONTRACT_VERSION`` above (which governs retrieval/scope/relevance
# semantics) and independent of ``memory_version`` (a per-store write
# counter). Same three-way separation the rest of this repository already
# uses (see e.g. ``src/phase4/controlled_runtime.py``'s
# RUNTIME_VERSION/SCHEMA_VERSION split).
MEMORY_SCHEMA_VERSION = 1


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
    """Append-only historical failure memory, durable across process restarts.

    Deliberately not shared with, and does not import, ``src.failure_memory``
    or ``src.failure_experience`` (Gen 1/Gen 2 memory implementations). Those
    remain frozen research artifacts on the abandoned trace-replay
    foundation. This is a new, independent implementation scoped to the
    Gen 3 controlled-runtime contracts, per Decision B of
    ``docs/PHASE4_5_AUDIT_AND_PLAN.md``.

    Phase 4.5 gap 2: backing storage is real SQLite (same pattern as
    ``src/phase4/observability.py``'s ``PersistentEventStore``), not an
    in-memory Python list. ``path=None`` (the default -- every pre-existing
    caller/test in this repository constructs ``FailureMemoryStore()`` with
    no arguments) uses an in-memory SQLite database: same engine, same SQL,
    same schema-versioning code path, just not durable across process exit --
    this keeps every existing test byte-for-byte unaffected while giving a
    caller who passes an explicit file ``path`` real, restart-surviving
    persistence with a single shared implementation (no separate "durable"
    subclass to silently drift out of sync with the retrieval contract
    above). All six contract items above are enforced by the SQL query in
    ``retrieve`` exactly as they were by the old Python-list filter.
    """

    version = MEMORY_CONTRACT_VERSION

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = str(path) if path is not None else ":memory:"
        self._db = sqlite3.connect(self.path)
        self._db.execute("PRAGMA journal_mode=WAL" if self.path != ":memory:" else "PRAGMA journal_mode=MEMORY")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS memory_schema_meta (id INTEGER PRIMARY KEY CHECK (id=1), schema_version INTEGER NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS memory_records ("
            "memory_id TEXT PRIMARY KEY, workload_id TEXT NOT NULL, environment_id TEXT NOT NULL, "
            "failure_class TEXT NOT NULL, root_cause TEXT NOT NULL, diagnosis_confidence TEXT NOT NULL, "
            "source_run_id TEXT NOT NULL, source_diagnosis_id TEXT NOT NULL, action_taken TEXT NOT NULL, "
            "validated_outcome TEXT NOT NULL, recorded_at TEXT NOT NULL, memory_version INTEGER NOT NULL, "
            "provenance_json TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_scope ON memory_records(workload_id, environment_id, failure_class)"
        )
        row = self._db.execute("SELECT schema_version FROM memory_schema_meta WHERE id=1").fetchone()
        if row is None:
            self._db.execute("INSERT INTO memory_schema_meta(id, schema_version) VALUES (1, ?)", (MEMORY_SCHEMA_VERSION,))
            self._db.commit()
            self._schema_version = MEMORY_SCHEMA_VERSION
        else:
            self._schema_version = int(row[0])
            if self._schema_version > MEMORY_SCHEMA_VERSION:
                raise ValueError(
                    f"memory store at {self.path!r} was written by a newer schema "
                    f"(schema_version={self._schema_version}) than this code supports "
                    f"(MEMORY_SCHEMA_VERSION={MEMORY_SCHEMA_VERSION})"
                )
            # A future schema migration would branch on self._schema_version
            # here (e.g. ALTER TABLE + rewrite) before continuing; there is
            # exactly one schema version so far, so there is nothing to
            # migrate from yet.
        row = self._db.execute("SELECT COALESCE(MAX(memory_version), 0) FROM memory_records").fetchone()
        self._memory_version = int(row[0]) if row else 0

    @property
    def memory_version(self) -> int:
        return self._memory_version

    @property
    def schema_version(self) -> int:
        return self._schema_version

    def close(self) -> None:
        self._db.close()

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
        self._db.execute(
            "INSERT INTO memory_records(memory_id, workload_id, environment_id, failure_class, root_cause, "
            "diagnosis_confidence, source_run_id, source_diagnosis_id, action_taken, validated_outcome, "
            "recorded_at, memory_version, provenance_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                record.memory_id, record.workload_id, record.environment_id, record.failure_class,
                record.root_cause, record.diagnosis_confidence, record.source_run_id, record.source_diagnosis_id,
                record.action_taken, record.validated_outcome, record.recorded_at, record.memory_version,
                json.dumps(dict(provenance), sort_keys=True),
            ),
        )
        self._db.commit()
        return record

    def _row_to_record(self, row: tuple) -> MemoryRecord:
        (memory_id, workload_id, environment_id, failure_class, root_cause, diagnosis_confidence,
         source_run_id, source_diagnosis_id, action_taken, validated_outcome, recorded_at,
         memory_version, provenance_json) = row
        return MemoryRecord(
            memory_id=memory_id, workload_id=workload_id, environment_id=environment_id,
            failure_class=failure_class, root_cause=root_cause, diagnosis_confidence=diagnosis_confidence,
            source_run_id=source_run_id, source_diagnosis_id=source_diagnosis_id, action_taken=action_taken,
            validated_outcome=validated_outcome, recorded_at=recorded_at, memory_version=memory_version,
            provenance=json.loads(provenance_json),
        )

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
        rows = self._db.execute(
            "SELECT memory_id, workload_id, environment_id, failure_class, root_cause, diagnosis_confidence, "
            "source_run_id, source_diagnosis_id, action_taken, validated_outcome, recorded_at, memory_version, "
            "provenance_json FROM memory_records WHERE workload_id=? AND environment_id=? AND failure_class=? "
            "AND source_run_id != ?",
            (workload_id, environment_id, failure_class, exclude_run_id),
        ).fetchall()
        matches: list[MemoryMatch] = []
        for row in rows:
            record = self._row_to_record(row)
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
            top_k=1_000_000,
        )
        relevant = [m for m in matches if m.record.action_taken == action]
        successes = sum(1 for m in relevant if m.record.validated_outcome == "RECOVERED")
        return successes, len(relevant)

    def action_success_estimate(
        self,
        *,
        workload_id: str,
        environment_id: str,
        failure_class: str,
        action: str,
        exclude_run_id: str,
        at_or_before: str,
    ) -> float:
        """Phase 4.5 gap 5: a real online-updated success-rate estimate per
        (workload, environment, failure_class, action), Beta(1, 1)-smoothed
        (Laplace smoothing) so an action with zero evidence gets a neutral
        0.5 rather than 0.0 or an error. Every call re-derives the estimate
        from the current durable record set, so it updates immediately as
        new validated outcomes are written via ``LearningManager.record`` --
        this is what makes it "online": no separate offline retraining step,
        no cached/stale value. See ``src/phase4/adaptive.py`` for the
        component that actually uses this to rank candidate actions."""
        successes, total = self.prior_outcome_rate(
            workload_id=workload_id, environment_id=environment_id, failure_class=failure_class,
            action=action, exclude_run_id=exclude_run_id, at_or_before=at_or_before,
        )
        return (successes + 1.0) / (total + 2.0)
