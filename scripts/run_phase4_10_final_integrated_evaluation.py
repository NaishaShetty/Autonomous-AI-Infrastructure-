"""Phase 4.10 -- Priority 5: the complete integrated loop (real agent task
-> uncertainty -> decision -> ANSWER/RETRY/ABSTAIN/REVIEW -> safety gate
-> recovery execution -> independent validation -> memory) evaluated on
held-out cases, plus the three ablations not already covered by a
dedicated priority (Memory ON/OFF, Retry ON/OFF, Predictor ON/OFF).
Generic-vs-calibrated policy (Priority 2), real-vs-shuffled labels
(Priority 3), and dev-vs-held-out environment (Priority 4) are each
already evaluated in their own priority and are not re-run here --
this script's own contribution is the three additional ablations and one
consolidated "full loop" pass over the SAME frozen TEST seeds Priority 2
used, for direct comparability.

Usage:
    python scripts/run_phase4_10_final_integrated_evaluation.py <output_dir>
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.phase4.ablations import NullUncertaintyPredictor, RetryDisabledCalibrationProfile
from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, AgentSplitSeeds
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.memory import FailureMemoryStore
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline

BASE_N_SAMPLES = 5
TEST_SEEDS = range(60_000, 60_300)  # identical to Phase 4.7's frozen TEST split
SPLIT_SEEDS = AgentSplitSeeds(train=range(0, 2000), calibration=range(10_000, 12_000), test=TEST_SEEDS)


def _fresh_pipeline(agent_decision_policy=None, agent_predictor=None, shared_memory=None):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store1 = PersistentEventStore(pathlib.Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(pathlib.Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=BASE_N_SAMPLES))
    kwargs = {"agent_runtime": agent_runtime, "agent_decision_policy": agent_decision_policy}
    if agent_predictor is not None:
        kwargs["agent_predictor"] = agent_predictor
    if shared_memory is not None:
        kwargs["memory"] = shared_memory
    pipeline = AutonomyPipeline(runtime, **kwargs)
    return pipeline, tmp


def run_condition(label: str, agent_decision_policy, agent_predictor=None, memory_mode: str = "shared") -> dict:
    """``memory_mode="shared"`` (every non-memory ablation): ONE pipeline
    instance (one FailureMemoryStore, one RecoveryCircuitBreaker) reused
    across all 300 episodes -- matching Phase 4.7's actual setup, so
    accumulated experience and the cross-episode circuit breaker behave
    exactly as they do in every other reported condition.
    ``memory_mode="per_episode"`` (the "memory OFF" ablation): a FRESH
    pipeline -- and therefore a fresh ``FailureMemoryStore`` AND a fresh
    ``RecoveryCircuitBreaker`` -- constructed for every single episode, so
    no episode's outcome can ever be seen by any later episode's planner
    or diagnosis. This is the honest way to force "no accumulated
    experience" given ``LearningManager``/``RuleBasedRecoveryPlanner``
    capture a direct reference to the memory store passed at construction
    time, not a live lookup of ``pipeline.memory`` -- swapping the
    attribute mid-run would not actually disconnect the learner."""
    episodes = []
    unsafe_actions = 0

    persistent_pipeline, persistent_tmp = (None, None)
    if memory_mode == "shared":
        persistent_pipeline, persistent_tmp = _fresh_pipeline(agent_decision_policy, agent_predictor, FailureMemoryStore())

    try:
        for seed in TEST_SEEDS:
            if memory_mode == "shared":
                pipeline = persistent_pipeline
                tmp_to_cleanup = None
            else:
                pipeline, tmp_to_cleanup = _fresh_pipeline(agent_decision_policy, agent_predictor, FailureMemoryStore())
            try:
                result = pipeline.run_agent_task(seed, workload_id=f"{label}-{seed}")
                wrong_initially = result.diagnosis is not None
                decision = result.decision.decision if result.decision is not None else None
                retried = bool(result.action is not None and getattr(result.action, "action_type", None) == "retry"
                               and result.execution is not None and result.execution.executed)
                if wrong_initially:
                    if retried and result.execution and result.execution.run_result:
                        final_correct = bool(result.execution.run_result.task_result.get("is_correct"))
                    else:
                        final_correct = False
                else:
                    final_correct = True
                if result.safety_authorized is False and retried:
                    unsafe_actions += 1
                episodes.append({
                    "seed": seed, "wrong_initially": wrong_initially, "decision": decision,
                    "retried": retried, "final_correct": final_correct,
                    "memory_recorded": bool(result.learning and result.learning.recorded),
                })
            finally:
                if tmp_to_cleanup is not None:
                    tmp_to_cleanup.cleanup()
    finally:
        if persistent_tmp is not None:
            persistent_tmp.cleanup()

    n = len(episodes)
    n_wrong = sum(1 for e in episodes if e["wrong_initially"])
    n_retried = sum(1 for e in episodes if e["retried"])
    n_retry_recovered = sum(1 for e in episodes if e["retried"] and e["final_correct"])
    n_final_correct = sum(1 for e in episodes if e["final_correct"])
    n_review = sum(1 for e in episodes if e["decision"] == "REVIEW")
    n_abstain = sum(1 for e in episodes if e["decision"] == "ABSTAIN")
    n_memory_recorded = sum(1 for e in episodes if e["memory_recorded"])

    return {
        "label": label, "n_episodes": n, "n_wrong_initially": n_wrong,
        "initial_accuracy": (n - n_wrong) / n, "final_accuracy": n_final_correct / n,
        "final_error_rate": 1.0 - (n_final_correct / n),
        "retry_rate_among_wrong": (n_retried / n_wrong) if n_wrong else None,
        "n_retried": n_retried,
        "retry_recovery_rate": (n_retry_recovered / n_retried) if n_retried else None,
        "review_rate": n_review / n, "abstention_rate": n_abstain / n,
        "memory_records_written": n_memory_recorded,
        "unsafe_action_count": unsafe_actions,
    }


def main(output_dir: Path) -> None:
    assert output_dir.exists(), f"output_dir must already exist: {output_dir}"

    print("fitting AgentDecisionCalibrationProfile (frozen, identical to Phase 4.7)...")
    profile = AgentDecisionCalibrationProfile.fit(SPLIT_SEEDS, base_n_samples=BASE_N_SAMPLES)

    print("[1/4] full loop: calibrated policy, memory ON, retry ON, real predictor ON (reference condition)...")
    full_loop = run_condition("full-loop", agent_decision_policy=profile, memory_mode="shared")

    print("[2/4] ablation: memory OFF (fresh memory store per episode)...")
    memory_off = run_condition("memory-off", agent_decision_policy=profile, memory_mode="per_episode")

    print("[3/4] ablation: retry OFF (RETRY remapped to REVIEW)...")
    retry_off_profile = RetryDisabledCalibrationProfile(base_profile=profile)
    retry_off = run_condition("retry-off", agent_decision_policy=retry_off_profile, memory_mode="shared")

    print("[4/4] ablation: predictor OFF (constant, uninformative uncertainty score)...")
    predictor_off = run_condition("predictor-off", agent_decision_policy=profile,
                                   agent_predictor=NullUncertaintyPredictor(fixed_score=0.5), memory_mode="shared")

    report = {
        "test_seeds": [TEST_SEEDS.start, TEST_SEEDS.stop],
        "note": "generic-vs-calibrated policy = Phase 4.7; real-vs-shuffled labels = Phase 4.8; dev-vs-held-out environment = Phase 4.9. This report covers the remaining ablations plus one consolidated full-loop pass.",
        "full_loop_reference": full_loop,
        "ablation_memory_off": memory_off,
        "ablation_retry_off": retry_off,
        "ablation_predictor_off": predictor_off,
    }
    (output_dir / "evaluation" / "ablation_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
