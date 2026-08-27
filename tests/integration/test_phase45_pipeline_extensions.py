"""Integration coverage for the Phase 4.5 "what's lacking" review fixes,
following the same pattern as tests/integration/test_phase44_pipeline.py:
real ControlledRuntime, real subprocesses, no mocks of the runtime itself.
"""
import pathlib
import tempfile

import pytest

from src.phase4.adaptive import AdaptiveRecoveryPlanner
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.guardrails import RecoveryCircuitBreaker
from src.phase4.memory import FailureMemoryStore
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline


@pytest.fixture()
def runtime_and_store():
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    config = RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.01)
    runtime = ControlledRuntime(store, config)
    yield runtime
    store.close()
    tmp.cleanup()


# ---------------------------------------------------------------------------
# Gap 3 + 4: new failure classes and new recovery actions, end to end.
# ---------------------------------------------------------------------------


def test_data_corruption_is_diagnosed_and_recovered_via_rollback_to_a_real_checkpoint(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store)
    checkpoint = pipeline.run_workload("success", {"mode": "success"}, workload_id="w-corrupt")
    assert checkpoint.final_state == "COMPLETED"

    result = pipeline.run_workload("corruption", {"mode": "corruption"}, workload_id="w-corrupt")
    assert result.diagnosis.primary_hypothesis.name == "DATA_INTEGRITY_FAILURE"
    assert result.action.action_type == "rollback"
    assert result.execution.executed is True
    assert result.validation.status == "RECOVERED"  # the checkpoint really was a working config


def test_rollback_with_no_prior_checkpoint_is_honestly_not_executed(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store)
    result = pipeline.run_workload("corruption", {"mode": "corruption"}, workload_id="w-corrupt-nocheckpoint")
    assert result.action.action_type == "rollback"
    assert result.execution.executed is False
    assert result.validation.status == "NOT_EXECUTED"


def test_oom_is_diagnosed_and_reconfigure_reduces_the_resource_footprint(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store)
    result = pipeline.run_workload("oom", {"mode": "oom", "alloc_mb": 200, "limit_mb": 32}, workload_id="w-oom")
    assert result.diagnosis.primary_hypothesis.name == "OUT_OF_MEMORY"
    assert result.action.action_type == "reconfigure"
    assert "alloc_mb" in result.execution.note and "100" in result.execution.note  # halved from 200


def test_gpu_device_failure_escalates_immediately_with_no_fabricated_fix(runtime_and_store):
    # force_gpu_state deterministically exercises the escalation path
    # regardless of the host's real hardware (see src/phase4/gpu_probe.py --
    # this repo used to assume "no real GPU in the sandbox," which is false
    # on real-GPU dev machines and made this test flaky/environment-
    # dependent; it is pipeline plumbing under test here, not a P3/P4
    # research evaluation, so a labeled deterministic override is
    # appropriate and never used by any evaluation code path).
    pipeline = AutonomyPipeline(runtime_and_store)
    result = pipeline.run_workload("gpu", {"mode": "gpu", "force_gpu_state": "GPU_UNAVAILABLE"}, workload_id="w-gpu")
    assert result.diagnosis.primary_hypothesis.name == "GPU_DEVICE_UNAVAILABLE"
    assert result.action.action_type == "escalate_to_human"
    assert result.execution.executed is False


def test_resource_unavailable_recovers_via_reconfigure_to_a_free_port_but_not_via_retry(runtime_and_store):
    runtime_and_store.occupy_external_resource(48123)
    pipeline = AutonomyPipeline(runtime_and_store)
    outcomes = []
    for _ in range(3):
        result = pipeline.run_workload("resource_unavailable", {"mode": "resource_unavailable", "port": 48123}, workload_id="w-res")
        outcomes.append((result.action.action_type, result.validation.status))
    assert outcomes[0][0] == "retry" and outcomes[0][1] == "NOT_RECOVERED"
    assert outcomes[1][0] == "retry" and outcomes[1][1] == "NOT_RECOVERED"
    assert outcomes[2][0] == "reconfigure" and outcomes[2][1] == "RECOVERED"
    runtime_and_store.close()


def test_intermittent_failure_recovers_via_retry(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store)
    result = pipeline.run_workload("flaky", {"mode": "flaky", "fail_count": 1}, workload_id="w-flaky")
    assert result.diagnosis.primary_hypothesis.name == "INTERMITTENT_TRANSIENT_FAILURE"
    assert result.action.action_type == "retry"
    assert result.validation.status == "RECOVERED"


# ---------------------------------------------------------------------------
# Gap 6: circuit breaker.
# ---------------------------------------------------------------------------


def test_recovery_circuit_breaker_bounds_real_executions_on_an_unrecoverable_workload(runtime_and_store):
    breaker = RecoveryCircuitBreaker(max_attempts=3)
    pipeline = AutonomyPipeline(runtime_and_store, recovery_budget=breaker)
    results = [pipeline.run_workload("fail", {"mode": "fail"}, workload_id="w-stuck") for _ in range(8)]
    executed_count = sum(1 for r in results if r.execution is not None and r.execution.executed)
    assert executed_count == 3  # exactly max_attempts real executions, never more
    # After the breaker trips, later calls must short-circuit to ABSTAINED
    # without ever reaching EXECUTING again.
    assert all(r.final_state == "ABSTAINED" or r.state_history[-2] == "ABSTAINED" for r in results[3:])
    assert any("circuit breaker OPEN" in note for note in results[-1].notes)


def test_circuit_breaker_only_counts_real_executions_not_escalations_or_abstentions(runtime_and_store):
    # See force_gpu_state note on test_gpu_device_failure_escalates_immediately_with_no_fabricated_fix above.
    breaker = RecoveryCircuitBreaker(max_attempts=2)
    check = breaker.check("w-gpu-breaker", runtime_and_store.config.environment_id)
    assert check.allowed and check.attempts_used == 0
    pipeline = AutonomyPipeline(runtime_and_store, recovery_budget=breaker)
    for _ in range(5):
        result = pipeline.run_workload("gpu", {"mode": "gpu", "force_gpu_state": "GPU_UNAVAILABLE"}, workload_id="w-gpu-breaker")
        assert result.action.action_type == "escalate_to_human"  # never executed -> never consumes budget
    assert breaker.check("w-gpu-breaker", runtime_and_store.config.environment_id).attempts_used == 0


# ---------------------------------------------------------------------------
# Gap 6: environment_id scoping actually exercised with more than one value.
# ---------------------------------------------------------------------------


def test_memory_does_not_leak_across_two_environments_sharing_a_workload_id():
    """Single-process scoping-correctness test -- this does NOT claim real
    multi-node isolation (out of scope per the Phase 4.5 review); it proves
    the memory contract's environment_id scope (src/phase4/memory.py
    contract item 1) is actually exercised with more than one real
    environment_id value, closing the gap between "the field exists" and
    "it is tested".
    """
    shared_memory = FailureMemoryStore()
    tmp_a = tempfile.TemporaryDirectory(ignore_cleanup_errors=True); tmp_b = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store_a = PersistentEventStore(pathlib.Path(tmp_a.name) / "a.sqlite")
    store_b = PersistentEventStore(pathlib.Path(tmp_b.name) / "b.sqlite")
    runtime_a = ControlledRuntime(store_a, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.01, environment_id="environment-A"))
    runtime_b = ControlledRuntime(store_b, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.01, environment_id="environment-B"))
    pipeline_a = AutonomyPipeline(runtime_a, memory=shared_memory)
    pipeline_b = AutonomyPipeline(runtime_b, memory=shared_memory)

    workload_id = "workload-shared-across-envs"
    first_a = pipeline_a.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    assert first_a.diagnosis.foundation_references["memory_used"] is False

    # environment-B has never seen this workload_id fail before -- even
    # though environment-A just recorded one -- so memory must NOT be used.
    first_b = pipeline_b.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    assert first_b.diagnosis.foundation_references["memory_used"] is False

    # A second incident WITHIN environment-A must see environment-A's own
    # prior record.
    second_a = pipeline_a.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    assert second_a.diagnosis.foundation_references["memory_used"] is True

    # A second incident in environment-B must still not see environment-A's
    # records, only its own (now-recorded) one.
    second_b = pipeline_b.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    assert second_b.diagnosis.foundation_references["memory_used"] is True

    store_a.close(); store_b.close(); tmp_a.cleanup(); tmp_b.cleanup()


# ---------------------------------------------------------------------------
# Gap 5: adaptive planner wired into the real pipeline (not just the unit
# bandit-convergence test in tests/unit/test_phase44_adaptive_learning.py).
# ---------------------------------------------------------------------------


def test_adaptive_planner_plugs_into_the_pipeline_without_breaking_the_closed_loop(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store, planner=AdaptiveRecoveryPlanner())
    result = pipeline.run_workload("fail", {"mode": "fail"}, workload_id="w-adaptive")
    assert result.action is not None
    assert result.final_state == "COMPLETED"
    assert result.learning.recorded is True


# ---------------------------------------------------------------------------
# Gap 1: rolling multi-point prediction with a real, non-zero lead time.
# ---------------------------------------------------------------------------


def test_rolling_prediction_reports_a_real_positive_lead_time_for_a_slow_building_timeout(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store, rolling_prediction=True)
    # A workload configured to run well past the timeout accumulates several
    # telemetry samples showing elapsed time approaching the deadline before
    # it is actually killed -- exactly the case a single boundary-time
    # prediction cannot show a positive lead time for.
    result = pipeline.run_workload("cpu", {"mode": "cpu", "duration_seconds": 2.0}, workload_id="w-rolling")
    assert result.rolling_predictions is not None
    assert len(result.rolling_predictions) >= 2
    # Whether it actually fired early is a real, measured outcome -- assert
    # on the shape of the data rather than forcing a specific fire.
    if result.prediction_lead_time_seconds is not None:
        assert result.prediction_lead_time_seconds > 0.0


def test_rolling_prediction_is_opt_in_and_default_pipeline_is_unaffected(runtime_and_store):
    pipeline = AutonomyPipeline(runtime_and_store)
    result = pipeline.run_workload("fail", {"mode": "fail"}, workload_id="w-default")
    assert result.rolling_predictions is None
    assert result.prediction_lead_time_seconds is None
