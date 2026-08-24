"""Phase 4.5 gap 6 -- a real recovery budget / circuit breaker.

Without this, nothing in ``src/phase4/pipeline.py`` bounds how many times an
autonomously-executed recovery action (a real subprocess re-invocation via
``ControlledRuntimeRecoveryExecutor``) can be attempted against one
``workload_id`` across repeated calls to ``AutonomyPipeline.run_workload``.
The memory-informed planner already avoids re-selecting one specific action
once it has accumulated enough failures (``min_failures_before_avoidance``
in ``src/phase4/recovery.py``), but that is a per-action heuristic, not a
hard cap -- an unrecoverable workload with several declared candidate
actions could still burn through every one of them, worth
``min_failures_before_avoidance`` real executions each, before the planner
ever reaches ``ESCALATE_TO_HUMAN``. This module adds an explicit, simple,
independent hard cap: this is deliberately a SEPARATE guardrail from the
planner's avoidance heuristic, not a replacement for it, and it is a
single-process, in-memory-by-default counter (an optional durable path is
supported the same way ``FailureMemoryStore`` supports one, for the same
restart-survives-the-count reason) -- it makes no claim about coordinating
a budget across multiple machines or processes.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BudgetCheck:
    allowed: bool
    attempts_used: int
    max_attempts: int
    reason: str


class RecoveryCircuitBreaker:
    """Hard cap on the number of real recovery EXECUTIONS (not diagnoses,
    not escalations, not abstentions -- only actions that actually reach
    ``ExecutorPort.execute`` with ``executed=True``) attempted for a given
    ``(workload_id, environment_id)`` pair. Once the cap is reached, the
    breaker stays OPEN for that pair forever (this is intentionally not a
    time-windowed/resettable breaker -- an unrecoverable workload should
    require a human or an explicit ``reset`` call, not silently start
    retrying again a few minutes later)."""

    version = "phase4.5-recovery-circuit-breaker-v1"

    def __init__(self, max_attempts: int = 5, path: str | Path | None = None) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.path = str(path) if path is not None else ":memory:"
        self._db = sqlite3.connect(self.path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS recovery_attempts (workload_id TEXT NOT NULL, environment_id TEXT NOT NULL, "
            "attempts INTEGER NOT NULL, PRIMARY KEY (workload_id, environment_id))"
        )
        self._db.commit()

    def _attempts(self, workload_id: str, environment_id: str) -> int:
        row = self._db.execute(
            "SELECT attempts FROM recovery_attempts WHERE workload_id=? AND environment_id=?",
            (workload_id, environment_id),
        ).fetchone()
        return int(row[0]) if row else 0

    def check(self, workload_id: str, environment_id: str) -> BudgetCheck:
        """Read-only: does this (workload_id, environment_id) still have
        budget for one more real execution? Callers must call ``record``
        themselves after an execution actually happens -- this method never
        mutates state, so repeated ``check`` calls without ``record`` never
        trip the breaker."""
        used = self._attempts(workload_id, environment_id)
        if used >= self.max_attempts:
            return BudgetCheck(
                allowed=False, attempts_used=used, max_attempts=self.max_attempts,
                reason=f"recovery circuit breaker OPEN for workload_id={workload_id!r} environment_id={environment_id!r}: {used} real recovery executions already attempted (max_attempts={self.max_attempts}); refusing another autonomous execution",
            )
        return BudgetCheck(
            allowed=True, attempts_used=used, max_attempts=self.max_attempts,
            reason=f"{used}/{self.max_attempts} recovery executions used; still within budget",
        )

    def record_attempt(self, workload_id: str, environment_id: str) -> int:
        """Record that a real recovery execution just happened. Returns the
        new attempt count. Must only be called after
        ``ExecutorPort.execute`` actually ran (``executed=True``) -- an
        abstention, escalation, or not-executed action must never consume
        budget, or the breaker would trip on workloads that were never
        actually autonomously acted upon."""
        used = self._attempts(workload_id, environment_id) + 1
        self._db.execute(
            "INSERT INTO recovery_attempts(workload_id, environment_id, attempts) VALUES (?, ?, ?) "
            "ON CONFLICT(workload_id, environment_id) DO UPDATE SET attempts=excluded.attempts",
            (workload_id, environment_id, used),
        )
        self._db.commit()
        return used

    def reset(self, workload_id: str, environment_id: str) -> None:
        """Explicit, deliberate reset -- e.g. after a human operator has
        intervened and wants to allow autonomous recovery again."""
        self._db.execute(
            "DELETE FROM recovery_attempts WHERE workload_id=? AND environment_id=?", (workload_id, environment_id)
        )
        self._db.commit()

    def close(self) -> None:
        self._db.close()
