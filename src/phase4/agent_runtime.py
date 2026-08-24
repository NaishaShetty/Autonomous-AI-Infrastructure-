"""Phase 4.5b -- ``AgentTaskRuntime``: the real-subprocess execution harness
for the AI/ML agent correctness task (``agent_task.py``), emitting the SAME
canonical event schema ``ControlledRuntime`` does so it plugs into the
identical ``ObservationCollector`` / ``MonitoringEngine`` / ``DiagnosisEngine``
/ ``FailureMemoryStore`` / recovery-planning / validation / learning loop --
no parallel/duplicated infrastructure, only a different real thing being
executed and observed.

Event shape, one real subprocess run:
  ``workload_received`` -> ``workload_registered`` -> ``execution_started``
  -> one ``telemetry_observed`` (``payload.telemetry_kind ==
  "agent_self_consistency_sample"``) per self-consistency sample (the
  uncertainty-bearing signal; each carries that sample's own produced
  answer and whether it agreed with the eventual majority) ->
  (``failure_detected`` with ``failure_kind='AGENT_INCORRECT_ANSWER'`` only
  if the majority-vote answer is wrong) -> ``workload_completed``. Reuses
  the existing, frozen ``data_foundation.foundation.EVENT_TYPES`` taxonomy
  rather than adding a new event_type.

This is real subprocess execution (see ``agent_task_worker.py``): the
child process independently generates the task, samples the agent
multiple times, and reports its own real, computed, ground-truth-checked
result -- the parent never simulates or fabricates any part of this.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .controlled_runtime import (
    ENVIRONMENT_ID,
    SCHEMA_VERSION,
    environment_identity,
    event_id,
    now_iso,
)
from .observability import ObservationCollector, PersistentEventStore

AGENT_RUNTIME_VERSION = "phase4.5b-agent-task-runtime-v1"
AGENT_SOURCE_ID = "project-owned-agent-task-runtime"
_WORKER_PATH = Path(__file__).resolve().parent / "agent_task_worker.py"


@dataclass
class AgentRunConfig:
    n_samples: int = 5
    min_difficulty: int = 2
    max_difficulty: int = 5
    timeout_seconds: float = 10.0
    environment_id: str = ENVIRONMENT_ID

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_samples": self.n_samples, "min_difficulty": self.min_difficulty,
            "max_difficulty": self.max_difficulty, "timeout_seconds": self.timeout_seconds,
            "environment_id": self.environment_id,
        }


@dataclass
class AgentRunResult:
    run_id: str
    workload_id: str
    environment_id: str
    status: str  # "COMPLETED" | "TIMEOUT" | "WORKER_ERROR"
    events: list[dict[str, Any]]
    collection_start: str
    collection_end: str
    task_result: dict[str, Any] | None  # the worker's raw JSON payload, or None on WORKER_ERROR/TIMEOUT


class AgentTaskRuntime:
    """Mirrors ``ControlledRuntime``'s contract closely enough that the same
    pipeline components can consume its events, but is intentionally a
    separate class rather than a shoehorned new ``mode`` on
    ``ControlledRuntime`` -- an AI/ML agent correctness evaluation is a
    conceptually different kind of workload (its "telemetry" is
    self-consistency samples, not process RSS/CPU), and keeping it
    separate avoids overloading the frozen, already-audited
    ``ControlledRuntime`` subprocess protocol."""

    def __init__(self, store: PersistentEventStore, config: AgentRunConfig | None = None):
        self.store = store
        self.collector = ObservationCollector(store)
        self.config = config or AgentRunConfig()
        self.env = environment_identity(self.config.environment_id)
        self._raw: list[dict[str, Any]] = []
        # Phase 4.5b gap-6-equivalent: last known-good (seed, n_samples) per
        # workload_id, recorded whenever a run's majority answer is
        # correct -- lets ROLLBACK mean something real here too (re-answer
        # with the last configuration that was actually verified correct).
        self._checkpoints: dict[str, tuple[int, int]] = {}

    def _emit(self, run_id: str, workload_id: str, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        ts = now_iso()
        raw = {
            "event_id": event_id(run_id, kind), "event_type": kind, "job_id": run_id,
            "workload_id": workload_id, "environment_id": self.config.environment_id,
            "timestamp": ts, "timestamp_precision": "microsecond",
            "timestamp_source": "Python wall-clock at actual runtime boundary",
            "timestamp_timezone": "UTC", "producer": AGENT_RUNTIME_VERSION,
            "source_dataset": AGENT_SOURCE_ID, "source_record_id": f"{run_id}:{kind}",
            "payload": payload or {}, "schema_version": SCHEMA_VERSION,
            "provenance": {
                "source": AGENT_SOURCE_ID, "source_version": AGENT_RUNTIME_VERSION,
                "source_record_id": f"{run_id}:{kind}", "extraction_method": "agent_task_runtime_boundary",
                "transformation": "agent_worker_event_to_canonical_event",
                "transformation_version": AGENT_RUNTIME_VERSION,
                "timestamp_source": "Python wall-clock at actual runtime boundary",
                "timestamp_quality": "EXACT",
            },
        }
        self._raw.append(raw)
        self.collector.ingest(raw)
        return raw

    def run(self, seed: int, n_samples: int | None = None, workload_id: str | None = None) -> AgentRunResult:
        n_samples = n_samples if n_samples is not None else self.config.n_samples
        run_id = f"agent-run-{uuid.uuid4().hex}"
        workload_id = workload_id or f"agent-workload-{uuid.uuid4().hex}"
        start = now_iso()
        self._raw = []

        self._emit(run_id, workload_id, "workload_received", {"workload_type": "ai_agent_task", "configuration": self.config.as_dict(), "environment": self.env})
        self._emit(run_id, workload_id, "workload_registered", {"workload_type": "ai_agent_task", "seed": seed, "n_samples": n_samples})

        cmd = [sys.executable, str(_WORKER_PATH), str(seed), str(self.config.min_difficulty), str(self.config.max_difficulty), str(n_samples), str(seed)]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=self.config.timeout_seconds)
        except subprocess.TimeoutExpired:
            self._emit(run_id, workload_id, "execution_started", {"seed": seed, "n_samples": n_samples})
            self._emit(run_id, workload_id, "failure_detected", {"failure_kind": "AGENT_TASK_TIMEOUT", "configured_timeout_seconds": self.config.timeout_seconds})
            end = now_iso()
            return AgentRunResult(run_id, workload_id, self.config.environment_id, "TIMEOUT", list(self._raw), start, end, None)

        self._emit(run_id, workload_id, "execution_started", {"seed": seed, "n_samples": n_samples})

        if proc.returncode != 0:
            self._emit(run_id, workload_id, "failure_detected", {"failure_kind": "AGENT_WORKER_ERROR", "exit_code": proc.returncode, "stderr": proc.stderr[-1000:]})
            end = now_iso()
            return AgentRunResult(run_id, workload_id, self.config.environment_id, "WORKER_ERROR", list(self._raw), start, end, None)

        task_result = json.loads(proc.stdout.strip().splitlines()[-1])
        # Reuses the existing canonical `telemetry_observed` event_type
        # (data_foundation.foundation.EVENT_TYPES is a frozen, shared
        # taxonomy that this additive work does not modify) -- a
        # self-consistency sample genuinely IS an observation made during
        # execution, distinguished from process telemetry by
        # `payload.telemetry_kind`.
        for idx, sample in enumerate(task_result["samples"]):
            self._emit(run_id, workload_id, "telemetry_observed", {
                "telemetry_kind": "agent_self_consistency_sample",
                "sample_index": idx, "produced_answer": sample,
                "agrees_with_majority": (sample == task_result["majority_answer"]),
                "running_agreement_rate": sum(1 for s in task_result["samples"][: idx + 1] if s == task_result["majority_answer"]) / (idx + 1),
            })

        if not task_result["is_correct"]:
            self._emit(run_id, workload_id, "failure_detected", {
                "failure_kind": "AGENT_INCORRECT_ANSWER",
                "expected_answer": task_result["correct_answer"],
                "produced_answer": task_result["majority_answer"],
                "agreement_rate": task_result["agreement_rate"],
                "difficulty": task_result["difficulty"],
                "expression": task_result["expression"],
            })
        else:
            self._emit(run_id, workload_id, "workload_completed", {"majority_answer": task_result["majority_answer"], "agreement_rate": task_result["agreement_rate"]})
            self._checkpoints[workload_id] = (seed, n_samples)

        end = now_iso()
        status = "COMPLETED" if task_result["is_correct"] else "FAILED"
        return AgentRunResult(run_id, workload_id, self.config.environment_id, status, list(self._raw), start, end, task_result)

    def checkpoint_for(self, workload_id: str) -> tuple[int, int] | None:
        return self._checkpoints.get(workload_id)
