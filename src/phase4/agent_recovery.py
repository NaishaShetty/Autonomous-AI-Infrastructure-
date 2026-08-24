"""Phase 4.5b -- the real, executable recovery executor for AI/ML agent
output-correctness failures.

Deliberately a separate class from ``ControlledRuntimeRecoveryExecutor``
(it re-invokes a different runtime with a different parameterization --
``seed``/``n_samples`` rather than ``workload_type``/``parameters``) but
reuses everything else in ``recovery.py`` unmodified: ``RuleBasedRecoveryPlanner``
/ ``AdaptiveRecoveryPlanner`` (candidate selection is generic over
``_CANDIDATES``, extended in ``recovery.py`` for the three new agent
failure classes), ``RecoverySafetyGate`` (generic over the same table),
and ``SignalRecoveryValidator`` (only needs ``execution.run_result.events``
/ ``.status``, which ``AgentRunResult`` already provides in the identical
shape ``RunResult`` does -- no changes needed there at all).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.recovery.schema import ActionId

from .agent_runtime import AgentRunResult, AgentTaskRuntime
from .architecture import RecoveryAction
from src.data_foundation.foundation import Provenance, TimestampQuality

AGENT_RECOVERY_ADAPTER_VERSION = "phase4.5b-agent-recovery-adapter-v1"

_EXECUTABLE = {ActionId.RETRY, ActionId.RESTART, ActionId.RECONFIGURE}


def _provenance(source: str) -> Provenance:
    return Provenance(source=source, source_version=AGENT_RECOVERY_ADAPTER_VERSION, timestamp_quality=TimestampQuality.EXACT)


@dataclass(frozen=True)
class AgentExecutionResult:
    action_type: str
    executed: bool
    run_result: AgentRunResult | None
    note: str


class AgentRecoveryExecutor:
    """RETRY = re-answer the SAME question (same seed, so it is a genuine
    retry of the same task, not a different problem) with real, measurably
    more self-consistency samples -- a real, more-costly action with a
    real, previously-measured effect on accuracy (see recovery.py's
    _CANDIDATES comment for the isolated measurement this claim rests on).
    RECONFIGURE = the inverse real, executable resource-reduction action
    (fewer samples, faster) for AGENT_TASK_TIMEOUT. RESTART = re-run the
    exact same configuration again, for AGENT_WORKER_ERROR (a real retry of
    a possibly-transient subprocess crash)."""

    version = "phase4.5b-agent-executor-v1"

    def __init__(self, runtime: AgentTaskRuntime, sample_increase_factor: int = 2):
        self.runtime = runtime
        self.sample_increase_factor = sample_increase_factor

    def execute(self, action: RecoveryAction, original_seed: int, original_n_samples: int, workload_id: str | None = None) -> AgentExecutionResult:
        action_id = ActionId(action.action_type)
        if action_id not in _EXECUTABLE:
            return AgentExecutionResult(action_type=action_id.value, executed=False, run_result=None, note=f"{action_id.value} has no executor for agent-task recovery; recorded as not-executed rather than simulated")
        if action_id == ActionId.RETRY:
            new_n_samples = max(1, original_n_samples * self.sample_increase_factor)
            result = self.runtime.run(original_seed, n_samples=new_n_samples, workload_id=workload_id)
            return AgentExecutionResult(action_type=action_id.value, executed=True, run_result=result, note=f"re-answered the same task (seed={original_seed}) with more self-consistency samples ({original_n_samples} -> {new_n_samples})")
        if action_id == ActionId.RECONFIGURE:
            new_n_samples = max(1, original_n_samples // 2)
            result = self.runtime.run(original_seed, n_samples=new_n_samples, workload_id=workload_id)
            return AgentExecutionResult(action_type=action_id.value, executed=True, run_result=result, note=f"re-answered the same task (seed={original_seed}) with fewer self-consistency samples ({original_n_samples} -> {new_n_samples}) to reduce runtime")
        result = self.runtime.run(original_seed, n_samples=original_n_samples, workload_id=workload_id)
        return AgentExecutionResult(action_type=action_id.value, executed=True, run_result=result, note=f"re-invoked AgentTaskRuntime.run for {action_id.value} with the same configuration")
