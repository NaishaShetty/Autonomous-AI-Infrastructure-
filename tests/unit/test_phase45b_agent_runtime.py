"""Phase 4.5b -- unit coverage for AgentTaskRuntime: real subprocess
execution, canonical event shape, and checkpoint tracking.
"""
import pathlib
import tempfile

from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.observability import PersistentEventStore


def _runtime(n_samples=5):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    runtime = AgentTaskRuntime(store, AgentRunConfig(n_samples=n_samples))
    return runtime, tmp


def test_run_emits_the_expected_canonical_event_sequence_for_a_correct_answer():
    runtime, tmp = _runtime()
    try:
        # search for a seed that answers correctly on the first try
        for seed in range(200):
            result = runtime.run(seed, workload_id=f"w-{seed}")
            if result.status == "COMPLETED":
                break
        assert result.status == "COMPLETED"
        types = [e["event_type"] for e in result.events]
        assert types[:3] == ["workload_received", "workload_registered", "execution_started"]
        assert types[-1] == "workload_completed"
        assert types.count("telemetry_observed") == 5
        assert all(e["payload"].get("telemetry_kind") == "agent_self_consistency_sample" for e in result.events if e["event_type"] == "telemetry_observed")
        assert "failure_detected" not in types
    finally:
        tmp.cleanup()


def test_run_emits_a_real_failure_detected_event_with_ground_truth_evidence_when_wrong():
    runtime, tmp = _runtime(n_samples=1)  # n=1 raises effective error rate to find a failure quickly
    try:
        for seed in range(500):
            result = runtime.run(seed, workload_id=f"w-{seed}")
            if result.status != "COMPLETED":
                break
        assert result.status == "FAILED"
        failures = [e for e in result.events if e["event_type"] == "failure_detected"]
        assert len(failures) == 1
        payload = failures[0]["payload"]
        assert payload["failure_kind"] == "AGENT_INCORRECT_ANSWER"
        assert payload["expected_answer"] != payload["produced_answer"]
        assert 0.0 <= payload["agreement_rate"] <= 1.0
    finally:
        tmp.cleanup()


def test_checkpoint_is_recorded_only_after_a_verified_correct_answer():
    runtime, tmp = _runtime(n_samples=5)
    try:
        assert runtime.checkpoint_for("w1") is None
        # find a correct-first-try seed
        for seed in range(200):
            result = runtime.run(seed, workload_id="w1")
            if result.status == "COMPLETED":
                break
        assert result.status == "COMPLETED"
        checkpoint = runtime.checkpoint_for("w1")
        assert checkpoint == (seed, 5)
    finally:
        tmp.cleanup()


def test_two_runs_of_the_same_seed_are_reproducible():
    runtime, tmp = _runtime(n_samples=5)
    try:
        r1 = runtime.run(11, workload_id="w-a")
        r2 = runtime.run(11, workload_id="w-b")
        assert r1.task_result["majority_answer"] == r2.task_result["majority_answer"]
        assert r1.task_result["samples"] == r2.task_result["samples"]
    finally:
        tmp.cleanup()
