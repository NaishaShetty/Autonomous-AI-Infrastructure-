"""Phase 4.5b -- unit coverage for the agent-task recovery executor and its
integration with the reused, unmodified RuleBasedRecoveryPlanner /
RecoverySafetyGate / SignalRecoveryValidator.
"""
import pathlib
import tempfile

from src.phase4.agent_recovery import AgentRecoveryExecutor
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.architecture import RecoveryAction
from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.monitoring import MonitoringEngine
from src.phase4.observability import PersistentEventStore
from src.phase4.recovery import RecoverySafetyGate, RuleBasedRecoveryPlanner, SignalRecoveryValidator


def _runtime(n_samples=1):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    runtime = AgentTaskRuntime(store, AgentRunConfig(n_samples=n_samples))
    return runtime, tmp


def _first_wrong_run(runtime, limit=500):
    for seed in range(limit):
        result = runtime.run(seed, workload_id=f"w-{seed}")
        if result.status != "COMPLETED":
            return seed, result
    raise AssertionError("no wrong answer found within seed budget")


def test_planner_selects_retry_for_agent_incorrect_answer():
    runtime, tmp = _runtime()
    try:
        seed, result = _first_wrong_run(runtime)
        engine = MonitoringEngine(); engine.process(result.events)
        failure = next(f for f in engine.failures if f["run_id"] == result.run_id)
        diagnosis = DiagnosisEngine().diagnose(failure, result.events)
        assert diagnosis.primary_hypothesis.name == "AGENT_INCORRECT_OUTPUT"

        action = RuleBasedRecoveryPlanner().plan(diagnosis)
        assert action.action_type == "retry"

        authorized, reason = RecoverySafetyGate().authorize(action, diagnosis)
        assert authorized, reason
    finally:
        tmp.cleanup()


def test_agent_recovery_executor_doubles_samples_and_reruns_the_same_question():
    runtime, tmp = _runtime()
    try:
        seed, result = _first_wrong_run(runtime)
        action = RecoveryAction(action_id="x", action_type="retry")
        executor = AgentRecoveryExecutor(runtime)
        execution = executor.execute(action, seed, 1, workload_id="retry-w")
        assert execution.executed
        assert execution.run_result.task_result["n_samples"] == 2
        assert execution.run_result.task_result["seed"] == seed  # same question, not a different one

        validation = SignalRecoveryValidator().validate(execution)
        assert validation.status in ("RECOVERED", "NOT_RECOVERED")
    finally:
        tmp.cleanup()


def test_agent_recovery_executor_reconfigure_reduces_samples():
    runtime, tmp = _runtime(n_samples=8)
    try:
        result = runtime.run(3, workload_id="w3")
        action = RecoveryAction(action_id="x", action_type="reconfigure")
        executor = AgentRecoveryExecutor(runtime)
        execution = executor.execute(action, 3, 8, workload_id="w3-reconfig")
        assert execution.executed
        assert execution.run_result.task_result["n_samples"] == 4
    finally:
        tmp.cleanup()


def test_agent_recovery_executor_declares_escalate_and_abstain_non_executable():
    runtime, tmp = _runtime()
    try:
        executor = AgentRecoveryExecutor(runtime)
        for action_type in ("escalate_to_human", "abstain"):
            action = RecoveryAction(action_id="x", action_type=action_type)
            execution = executor.execute(action, 1, 5, workload_id="w")
            assert not execution.executed
            assert execution.run_result is None
    finally:
        tmp.cleanup()
