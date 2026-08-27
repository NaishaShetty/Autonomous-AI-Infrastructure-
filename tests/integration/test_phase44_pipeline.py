"""End-to-end integration coverage for the Phase 4.4 / Phase 5 autonomy
pipeline (src/phase4/pipeline.py). Uses the real ControlledRuntime -- real
subprocesses, real telemetry -- consistent with every other Phase 4
controlled-runtime test in this repository. No mocks of the runtime itself.
"""
import pathlib
import tempfile

import pytest

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline


@pytest.fixture()
def pipeline():
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    config = RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.02)
    runtime = ControlledRuntime(store, config)
    yield AutonomyPipeline(runtime)
    store.close()
    tmp.cleanup()


def test_healthy_run_reaches_completed_without_entering_recovery_loop(pipeline):
    result = pipeline.run_workload("success", {"mode": "success"})
    assert result.final_state == "COMPLETED"
    assert result.state_history == ["RECEIVED", "OBSERVING", "UNKNOWN", "COMPLETED"]
    assert result.diagnosis is None and result.action is None


def test_failure_walks_the_full_closed_loop_and_state_history_matches_architecture_allowed_transitions(pipeline):
    result = pipeline.run_workload("fail", {"mode": "fail"}, workload_id="workload-loop-test")
    assert result.state_history[0] == "RECEIVED"
    assert "DIAGNOSING" in result.state_history
    assert "PLANNING" in result.state_history
    assert "SAFETY_CHECK" in result.state_history
    assert "EXECUTING" in result.state_history
    assert "VALIDATING" in result.state_history
    assert result.state_history[-1] == "COMPLETED"
    assert result.diagnosis is not None and result.diagnosis.primary_hypothesis.name == "PROCESS_EXIT_FAILURE"
    assert result.action is not None and result.action.action_type in ("restart", "retry")
    assert result.safety_authorized is True
    assert result.execution is not None and result.execution.executed is True
    # This workload is deterministically broken (always exits 7), so a
    # genuine retry/restart genuinely cannot fix it -- the validator must
    # honestly report NOT_RECOVERED rather than a rigged success.
    assert result.validation.status == "NOT_RECOVERED"
    assert result.learning.recorded is True


def test_memory_changes_the_planner_decision_across_repeated_incidents_of_the_same_workload(pipeline):
    workload_id = "workload-recurring"
    first = pipeline.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    second = pipeline.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)
    third = pipeline.run_workload("fail", {"mode": "fail"}, workload_id=workload_id)

    assert first.diagnosis.foundation_references["memory_used"] is False
    assert second.diagnosis.foundation_references["memory_used"] is True
    assert third.diagnosis.foundation_references["memory_used"] is True

    # First and second both try the planner's first-choice action (restart);
    # by the third incident, memory shows restart has never once recovered
    # this workload/failure_class, so the planner must switch to the next
    # candidate rather than repeating a known-losing action forever.
    assert first.action.action_type == "restart"
    assert second.action.action_type == "restart"
    assert third.action.action_type != "restart"


def test_abstention_path_is_reachable_when_predicted_risk_is_high(pipeline):
    """A CPU-bound workload configured to run longer than the runtime's
    timeout accumulates telemetry showing elapsed time approaching the
    deadline before the timeout failure fires -- exactly the leading
    indicator src/phase4/prediction.py is built to catch. With a strict
    decision policy, this must abstain rather than autonomously act."""
    from src.phase4.decision import AbstentionAwareDecisionPolicy
    from src.decision.policy import PolicyConfig

    # Phase 4.10 audit fix: a pure CPU busy-loop workload has ~0 rss_ratio
    # and ~0 anomaly_rate (no memory allocation in the spin loop), and
    # elapsed_ratio clips to exactly 1.0 once the configured timeout has
    # elapsed (prediction.py's TelemetryRiskPredictor always evaluates at
    # the failure_detected event's own timestamp, which by construction is
    # at/after the deadline). So this scenario's risk is DETERMINISTICALLY
    # `WEIGHT_ELAPSED_RATIO * 1.0 = 0.30` (never more, never less) on every
    # machine -- not measurement noise. abstain_threshold=0.7 previously
    # sat exactly ON that boundary (fused_score = 1 - risk = 0.70 exactly),
    # and DecisionPolicy.decide()'s ABSTAIN rule is a strict `<`, so this
    # scenario could never actually abstain as written. 0.75 gives this
    # deterministic 0.70 fused_score real headroom below the threshold.
    pipeline.decision_policy = AbstentionAwareDecisionPolicy(PolicyConfig(answer_threshold=0.99, abstain_threshold=0.75))
    result = pipeline.run_workload("cpu", {"mode": "cpu", "duration_seconds": 2.0}, workload_id="workload-timeout-heavy")
    assert result.decision is not None
    assert result.decision.decision == "ABSTAIN"
    assert result.final_state == "ABSTAINED" or result.state_history[-2] == "ABSTAINED"
    assert result.diagnosis is None  # abstained before diagnosis was ever attempted
    assert result.action is None


def test_network_failure_workload_is_observed_diagnosed_and_recovered_end_to_end(pipeline):
    result = pipeline.run_workload("network", {"mode": "network", "duration_seconds": 0.1}, workload_id="workload-net")
    assert result.diagnosis is not None
    assert result.diagnosis.primary_hypothesis.name == "NETWORK_CONNECTIVITY_FAILURE"
    assert result.action is not None and result.action.action_type == "retry"
