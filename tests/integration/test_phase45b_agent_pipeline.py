"""Phase 4.5b -- the second gap named in the project's own strategic review,
end to end: an actual AI/ML agent task, with a ground-truth correctness
oracle and a genuine self-consistency uncertainty signal, wired through the
SAME AutonomyPipeline state machine, diagnosis engine, recovery planner,
safety gate, executor, validator, memory, and learning loop as every
process-failure scenario -- proven on real subprocess executions, not
stubbed events.
"""
import pathlib
import tempfile

from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.memory import FailureMemoryStore
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline


def _pipeline(n_samples=5, memory=None):
    tmp = tempfile.TemporaryDirectory()
    store1 = PersistentEventStore(pathlib.Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(pathlib.Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=n_samples))
    pipeline = AutonomyPipeline(runtime, memory=memory, agent_runtime=agent_runtime)
    return pipeline, tmp


def test_run_agent_task_raises_a_clear_error_when_not_configured_for_agent_tasks():
    tmp = tempfile.TemporaryDirectory()
    store = PersistentEventStore(pathlib.Path(tmp.name) / "e.sqlite")
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    pipeline = AutonomyPipeline(runtime)  # no agent_runtime
    try:
        pipeline.run_agent_task(1)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "agent_runtime" in str(exc)
    finally:
        tmp.cleanup()


def test_a_correct_answer_completes_without_entering_the_decision_loop():
    pipeline, tmp = _pipeline(n_samples=5)
    try:
        for seed in range(200):
            result = pipeline.run_agent_task(seed, workload_id=f"w-{seed}")
            if result.diagnosis is None:
                break
        assert result.diagnosis is None
        assert result.final_state == "COMPLETED"
        assert result.decision is None
        assert "prediction/decision/recovery loop not entered" in result.notes[-1]
    finally:
        tmp.cleanup()


def test_a_wrong_answer_is_diagnosed_as_agent_incorrect_output_with_real_evidence():
    pipeline, tmp = _pipeline(n_samples=1)  # n=1 -> higher effective error rate -> finds a failure fast
    try:
        for seed in range(500):
            result = pipeline.run_agent_task(seed, workload_id=f"w-{seed}")
            if result.diagnosis is not None:
                break
        assert result.diagnosis is not None
        assert result.diagnosis.primary_hypothesis.name == "AGENT_INCORRECT_OUTPUT"
        assert result.diagnosis.causal_status == "OBSERVED"
        assert result.prediction_score is not None
        assert result.decision is not None
    finally:
        tmp.cleanup()


def test_an_autonomous_retry_is_executed_and_validated_end_to_end():
    """n_samples=1 means a single sample trivially "agrees" with itself
    (agreement_rate=1.0), so AgentUncertaintyPredictor's risk score is
    always 0.0 -- every incident here lands in the ANSWER decision band,
    so autonomous execution is always authorized once a wrong answer is
    diagnosed. This exercises every stage of the state machine
    (DIAGNOSING -> PLANNING -> SAFETY_CHECK -> EXECUTING -> VALIDATING ->
    RECOVERED/NOT_RECOVERED) for a real AI/ML output-correctness incident.
    Real recovery is not deterministic (majority-vote-at-2-samples can
    still land on the wrong answer) -- both outcomes are accepted here;
    the AGGREGATE recovery-rate claim is checked separately, below."""
    pipeline, tmp = _pipeline(n_samples=1)
    try:
        found = None
        for seed in range(500):
            result = pipeline.run_agent_task(seed, workload_id=f"w-retry-{seed}")
            if result.diagnosis is not None:
                found = result
                break
        assert found is not None, "expected at least one wrong answer within 500 seeds at n_samples=1"
        assert found.decision.decision == "ANSWER"
        assert found.action.action_type == "retry"
        assert found.execution is not None and found.execution.executed
        assert found.execution.run_result.task_result["n_samples"] == 2  # doubled from 1
        assert found.validation.status in ("RECOVERED", "NOT_RECOVERED")
        assert found.learning is not None
        assert found.final_state == "COMPLETED"  # every path terminates at COMPLETED
        assert found.validation.status in found.state_history  # but the real intermediate outcome is recorded
    finally:
        tmp.cleanup()


def test_retry_recovery_measurably_beats_doing_nothing_at_scale():
    """The real, quantified claim the RETRY action rests on: doubling
    self-consistency samples for a task the agent got wrong the first time
    recovers a meaningfully positive fraction of those cases -- not
    100% (recovery isn't deterministic), just genuinely better than 0%.
    Reported as measured, not asserted to hit a specific number."""
    pipeline, tmp = _pipeline(n_samples=1)
    try:
        outcomes = []
        for seed in range(600):
            result = pipeline.run_agent_task(seed, workload_id=f"w-agg-{seed}")
            if result.diagnosis is not None and result.execution is not None and result.execution.executed:
                outcomes.append(result.validation.status)
            if len(outcomes) >= 40:
                break
        assert len(outcomes) >= 10, f"expected at least 10 executed retries within 600 seeds, got {len(outcomes)}"
        recovered = sum(1 for o in outcomes if o == "RECOVERED")
        rate = recovered / len(outcomes)
        assert rate > 0.0, f"expected some real recovery from doubling self-consistency samples, measured rate={rate} over n={len(outcomes)}"
    finally:
        tmp.cleanup()


def test_high_disagreement_wrong_answers_are_escalated_or_abstained_not_silently_autonomous():
    """Honest, measured property of reusing the existing abstention policy
    unmodified for this new signal: at n_samples=5, a wrong majority vote
    reached via genuine sample disagreement (not near-unanimous agreement,
    since these errors are i.i.d. per-sample noise rather than a
    systematic bias) lands in REVIEW or ABSTAIN, never silently treated as
    trustworthy enough for autonomous action. This is the abstention
    mission statement ("abstain ... when the available evidence is
    insufficient") actually operating on real AI/ML output uncertainty for
    the first time in this project."""
    pipeline, tmp = _pipeline(n_samples=5)
    try:
        seen_high_disagreement_wrong = False
        for seed in range(150):
            result = pipeline.run_agent_task(seed, workload_id=f"w-hd-{seed}")
            if result.diagnosis is not None and result.prediction_score is not None and result.prediction_score >= 0.4:
                seen_high_disagreement_wrong = True
                assert result.decision.decision in ("REVIEW", "ABSTAIN")
                assert result.execution is None
        assert seen_high_disagreement_wrong, "expected at least one moderate/high-disagreement wrong answer within 150 seeds at n_samples=5"
    finally:
        tmp.cleanup()


def test_agent_failures_and_process_failures_share_one_memory_store_without_cross_contamination():
    memory = FailureMemoryStore()
    pipeline, tmp = _pipeline(n_samples=1, memory=memory)
    try:
        agent_wrong_seeds = []
        for seed in range(300):
            result = pipeline.run_agent_task(seed, workload_id="shared-w1")
            if result.diagnosis is not None:
                agent_wrong_seeds.append(seed)
            if len(agent_wrong_seeds) >= 2:
                break
        assert len(agent_wrong_seeds) >= 2

        # A process-failure run recorded against the SAME workload_id/environment
        # must never be retrieved when scoping by failure_class=AGENT_INCORRECT_ANSWER.
        process_result = pipeline.run_workload("fail", {"mode": "fail"}, workload_id="shared-w1")
        assert process_result.diagnosis is not None

        agent_matches = memory.retrieve(
            workload_id="shared-w1", environment_id=pipeline.agent_runtime.config.environment_id,
            failure_class="AGENT_INCORRECT_ANSWER", exclude_run_id="nonexistent-run", at_or_before="2999-01-01T00:00:00Z",
        )
        assert agent_matches, "expected the agent-task failures to be retrievable from shared memory"
        assert all(m.record.failure_class == "AGENT_INCORRECT_ANSWER" for m in agent_matches)
    finally:
        tmp.cleanup()
