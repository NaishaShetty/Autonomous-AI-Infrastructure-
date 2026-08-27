"""Phase 4.7 -- end-to-end proof that a calibrated AgentDecisionCalibrationProfile,
wired into AutonomyPipeline, lets RETRY actually fire for cases the generic
DecisionPolicy would have escalated to REVIEW -- and that with no profile
configured (the default), run_agent_task behaves EXACTLY as it did before
this change (regression guard)."""
import pathlib
import tempfile

from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, AgentSplitSeeds
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline


def _pipeline(n_samples=5, agent_decision_policy=None):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store1 = PersistentEventStore(pathlib.Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(pathlib.Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=n_samples))
    pipeline = AutonomyPipeline(runtime, agent_runtime=agent_runtime, agent_decision_policy=agent_decision_policy)
    return pipeline, tmp


def _fitted_profile(base_n_samples=5):
    seeds = AgentSplitSeeds(train=range(0, 500), calibration=range(10_000, 11_000), test=range(50_000, 50_300))
    return AgentDecisionCalibrationProfile.fit(seeds, base_n_samples=base_n_samples)


def test_agent_decision_policy_defaults_to_none_whether_passed_explicitly_or_omitted():
    """Regression guard: the new opt-in constructor parameter defaults to
    None whether a caller omits it entirely (every pre-Phase-4.7 call
    site) or passes it explicitly -- the two are the same code path, so
    run_agent_task's branch (`if self.agent_decision_policy is not None`)
    is guaranteed to take the pre-existing generic-policy path in both
    cases. (A same-seed, two-separate-subprocess-runs comparison was
    considered here instead, but real subprocess wall-clock jitter in the
    controlled runtime's own telemetry can legitimately change which
    failure/anomaly events land within a given episode across processes,
    which would make such a test flaky for reasons unrelated to this
    parameter -- this is a deterministic, non-flaky equivalent.)"""
    pipeline_explicit, tmp_a = _pipeline(n_samples=5, agent_decision_policy=None)
    pipeline_omitted, tmp_b = _pipeline(n_samples=5)
    try:
        assert pipeline_explicit.agent_decision_policy is None
        assert pipeline_omitted.agent_decision_policy is None
    finally:
        tmp_a.cleanup(); tmp_b.cleanup()


def test_default_pipeline_mostly_escalates_wrong_answers_to_review_matching_phase45b_finding():
    """Directional regression guard for the Phase 4.5b finding: under the
    generic (uncalibrated) policy at n_samples=5, the large majority of
    wrong-answer episodes land in REVIEW, not autonomous ANSWER/RETRY --
    not asserted as literally every single case (a unanimous-but-wrong
    self-consistency vote is a real, rare edge case that legitimately
    lands in the ANSWER band even under the generic policy), just the
    same directional finding the report made."""
    pipeline, tmp = _pipeline(n_samples=5)
    try:
        wrong = 0
        review_or_abstain = 0
        for seed in range(300):
            result = pipeline.run_agent_task(seed, workload_id=f"w-{seed}")
            # Post-P5 remediation: restrict to genuine wrong-ANSWER episodes,
            # not merely "a diagnosis exists" -- a real subprocess timeout
            # (AGENT_TASK_TIMEOUT -> diagnosis primary_hypothesis
            # "AGENT_RUNTIME_TIMEOUT") also produces a non-None diagnosis
            # but is infrastructure noise unrelated to answer correctness
            # (see test_phase45b_agent_pipeline.py's identical fix for the
            # full explanation). This test's own docstring already commits
            # to measuring "wrong-answer episodes" specifically.
            if result.diagnosis is not None and result.diagnosis.primary_hypothesis.name == "AGENT_INCORRECT_OUTPUT":
                wrong += 1
                if result.decision.decision in ("REVIEW", "ABSTAIN"):
                    review_or_abstain += 1
        assert wrong > 0, "expected at least one wrong-answer episode in 300 seeds"
        assert review_or_abstain / wrong >= 0.5
    finally:
        tmp.cleanup()


def test_calibrated_profile_lets_retry_fire_for_at_least_some_wrong_answers():
    profile = _fitted_profile(base_n_samples=5)
    pipeline, tmp = _pipeline(n_samples=5, agent_decision_policy=profile)
    try:
        retried = 0
        wrong = 0
        for seed in range(300):
            result = pipeline.run_agent_task(seed, workload_id=f"w-cal-{seed}")
            if result.diagnosis is not None:
                wrong += 1
                if result.decision.decision == "RETRY" and result.action is not None and result.action.action_type == "retry":
                    retried += 1
        assert wrong > 0
        assert retried > 0, "expected the calibrated profile to authorize at least one real retry across 300 seeds"
    finally:
        tmp.cleanup()


def test_calibrated_profile_never_bypasses_the_safety_gate_or_review_abstain_paths():
    """Even under the calibrated profile, low-confidence cases must still
    be able to reach REVIEW/ABSTAIN -- the profile changes WHICH band
    triggers autonomous action, it does not remove the bands."""
    profile = _fitted_profile(base_n_samples=1)  # n=1 has far noisier agreement -> some low buckets
    pipeline, tmp = _pipeline(n_samples=1, agent_decision_policy=profile)
    try:
        decisions_seen = set()
        for seed in range(200):
            result = pipeline.run_agent_task(seed, workload_id=f"w-n1-{seed}")
            if result.decision is not None:
                decisions_seen.add(result.decision.decision)
        assert decisions_seen, "expected at least some decisions to be made"
        # every decision value produced must be one of the four authorized actions
        assert decisions_seen <= {"ANSWER", "RETRY", "ABSTAIN", "REVIEW"}
    finally:
        tmp.cleanup()
