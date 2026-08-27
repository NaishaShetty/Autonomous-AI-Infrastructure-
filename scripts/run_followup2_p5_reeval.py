"""Post-P5-remediation follow-up 2 -- re-run the final integrated P5
agent/recovery evaluation with the Step 7 timestamp-tie fix in place
(``pipeline.py``'s ``run_agent_task``/``run_workload`` prediction-boundary
cut changed from strict ``<`` to ``<=``, already applied to the
repository).

Verified source of the original P5 headline numbers ("final accuracy
1.000, retry OFF ~3.0% error, retry ON 0.0% error"): both
``scripts/run_phase4_7_retry_calibration_experiment.py`` (generic vs.
calibrated policy) and ``scripts/run_phase4_10_final_integrated_evaluation.py``
(memory/retry/predictor ablations) call
``AutonomyPipeline.run_agent_task`` -- the exact code path the addendum
documents as having been nondeterministic pre-fix. This script re-runs
both experiments' logic together, using a FRESH held-out test seed range
disjoint from every previously-used split (train/calibration/original
test), so this follow-up's numbers cannot be an artifact of having reused
a seed range whose specific composition was already seen.

Splits (all disjoint):
  - train:        range(0, 2000)          (unused by this non-ML profile,
                                             kept disjoint per protocol)
  - calibration:   range(10_000, 12_000)   (same as Phase 4.7/4.10 -- the
                                             profile itself is not refit)
  - original test: range(60_000, 60_300)   (Phase 4.7/4.10's frozen test --
                                             NOT reused as this run's test)
  - FRESH test:    range(70_000, 70_300)   (this follow-up's held-out set)

No threshold, bucket, or utility constant is tuned after seeing any result
from the fresh test split.

Usage:
    python scripts/run_followup2_p5_reeval.py <run_dir>

Writes:
    <run_dir>/raw/followup2_p5_reeval.json
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.phase4.ablations import NullUncertaintyPredictor, RetryDisabledCalibrationProfile
from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, AgentSplitSeeds, CALIBRATION_VERSION
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.memory import FailureMemoryStore
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline

BASE_N_SAMPLES = 5
ORIGINAL_TEST_SEEDS = range(60_000, 60_300)  # Phase 4.7/4.10's frozen test -- NOT reused here
FRESH_TEST_SEEDS = range(70_000, 70_300)  # this follow-up's genuinely fresh held-out set
SPLIT_SEEDS = AgentSplitSeeds(train=range(0, 2000), calibration=range(10_000, 12_000), test=FRESH_TEST_SEEDS)


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


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z ** 2 / n
    centre = p + z ** 2 / (2 * n)
    margin = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5)
    return ((centre - margin) / denom, (centre + margin) / denom)


def run_condition(label: str, test_seeds, agent_decision_policy, agent_predictor=None, memory_mode: str = "shared") -> dict:
    episodes = []
    unsafe_actions = 0
    safety_violations = 0
    t0 = time.perf_counter()

    persistent_pipeline, persistent_tmp = (None, None)
    if memory_mode == "shared":
        persistent_pipeline, persistent_tmp = _fresh_pipeline(agent_decision_policy, agent_predictor, FailureMemoryStore())

    try:
        for seed in test_seeds:
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
                unsafe = result.safety_authorized is False and retried
                if unsafe:
                    unsafe_actions += 1
                    safety_violations += 1
                episodes.append({
                    "seed": seed, "wrong_initially": wrong_initially, "decision": decision,
                    "retried": retried, "final_correct": final_correct,
                    "memory_recorded": bool(result.learning and result.learning.recorded),
                    "n_samples_used": (result.execution.run_result.task_result.get("n_samples") if retried and result.execution and result.execution.run_result else BASE_N_SAMPLES),
                })
            finally:
                if tmp_to_cleanup is not None:
                    tmp_to_cleanup.cleanup()
    finally:
        elapsed = time.perf_counter() - t0
        if persistent_tmp is not None:
            persistent_tmp.cleanup()

    n = len(episodes)
    n_wrong = sum(1 for e in episodes if e["wrong_initially"])
    n_retried = sum(1 for e in episodes if e["retried"])
    n_retry_recovered = sum(1 for e in episodes if e["retried"] and e["final_correct"])
    n_final_correct = sum(1 for e in episodes if e["final_correct"])
    n_review = sum(1 for e in episodes if e["decision"] == "REVIEW")
    n_abstain = sum(1 for e in episodes if e["decision"] == "ABSTAIN")
    n_answer = sum(1 for e in episodes if e["decision"] == "ANSWER")
    n_retry_decision = sum(1 for e in episodes if e["decision"] == "RETRY")
    n_memory_recorded = sum(1 for e in episodes if e["memory_recorded"])

    return {
        "label": label, "n_episodes": n, "n_wrong_initially": n_wrong,
        "initial_accuracy": (n - n_wrong) / n if n else None,
        "initial_error_rate": (n_wrong / n) if n else None,
        "final_accuracy": (n_final_correct / n) if n else None,
        "final_error_rate": (1.0 - (n_final_correct / n)) if n else None,
        "final_accuracy_wilson_ci95": _wilson_ci(n_final_correct, n),
        "retry_rate_among_wrong": (n_retried / n_wrong) if n_wrong else None,
        "n_retried": n_retried,
        "retry_recovery_rate": (n_retry_recovered / n_retried) if n_retried else None,
        "retry_recovery_rate_wilson_ci95": _wilson_ci(n_retry_recovered, n_retried) if n_retried else None,
        "retry_recovery_failure_count": n_retried - n_retry_recovered,
        "decision_distribution": {"ANSWER": n_answer, "RETRY": n_retry_decision, "REVIEW": n_review, "ABSTAIN": n_abstain},
        "review_rate": n_review / n if n else None, "abstention_rate": n_abstain / n if n else None,
        "memory_records_written": n_memory_recorded,
        "unsafe_action_count": unsafe_actions,
        "safety_violations": safety_violations,
        "wall_clock_seconds": elapsed,
    }


def main(run_dir: Path) -> None:
    print("fitting AgentDecisionCalibrationProfile on the CALIBRATION split (unchanged; not refit for this follow-up)...")
    profile = AgentDecisionCalibrationProfile.fit(SPLIT_SEEDS, base_n_samples=BASE_N_SAMPLES)

    print("[1/6] generic policy (no calibration), FRESH held-out test...")
    generic = run_condition("generic-fresh", FRESH_TEST_SEEDS, agent_decision_policy=None)

    print("[2/6] calibrated policy, FRESH held-out test (reference/full-loop condition)...")
    calibrated = run_condition("calibrated-fresh", FRESH_TEST_SEEDS, agent_decision_policy=profile)

    print("[3/6] ablation: memory OFF (fresh memory store per episode)...")
    memory_off = run_condition("memory-off-fresh", FRESH_TEST_SEEDS, agent_decision_policy=profile, memory_mode="per_episode")

    print("[4/6] ablation: retry OFF (RETRY remapped to REVIEW)...")
    retry_off_profile = RetryDisabledCalibrationProfile(base_profile=profile)
    retry_off = run_condition("retry-off-fresh", FRESH_TEST_SEEDS, agent_decision_policy=retry_off_profile)

    print("[5/6] ablation: predictor OFF (constant, uninformative uncertainty score)...")
    predictor_off = run_condition("predictor-off-fresh", FRESH_TEST_SEEDS, agent_decision_policy=profile,
                                   agent_predictor=NullUncertaintyPredictor(fixed_score=0.5))

    print("[6/6] reproducibility check: re-run calibrated condition a second time on the SAME fresh seeds "
          "to directly verify the timestamp-tie fix produces identical results run-to-run...")
    calibrated_rerun = run_condition("calibrated-fresh-rerun", FRESH_TEST_SEEDS, agent_decision_policy=profile)

    determinism_check = {
        "identical_to_first_run": calibrated["decision_distribution"] == calibrated_rerun["decision_distribution"]
        and calibrated["final_accuracy"] == calibrated_rerun["final_accuracy"]
        and calibrated["n_retried"] == calibrated_rerun["n_retried"],
        "run1_decision_distribution": calibrated["decision_distribution"],
        "run2_decision_distribution": calibrated_rerun["decision_distribution"],
        "run1_final_accuracy": calibrated["final_accuracy"],
        "run2_final_accuracy": calibrated_rerun["final_accuracy"],
    }

    report = {
        "calibration_version": CALIBRATION_VERSION,
        "base_n_samples": BASE_N_SAMPLES,
        "split_seeds": {
            "train": [SPLIT_SEEDS.train.start, SPLIT_SEEDS.train.stop],
            "calibration": [SPLIT_SEEDS.calibration.start, SPLIT_SEEDS.calibration.stop],
            "original_test_not_reused": [ORIGINAL_TEST_SEEDS.start, ORIGINAL_TEST_SEEDS.stop],
            "fresh_test": [FRESH_TEST_SEEDS.start, FRESH_TEST_SEEDS.stop],
        },
        "generic_policy": generic,
        "calibrated_policy": calibrated,
        "calibrated_policy_rerun_for_determinism_check": calibrated_rerun,
        "determinism_check": determinism_check,
        "ablation_memory_off": memory_off,
        "ablation_retry_off": retry_off,
        "ablation_predictor_off": predictor_off,
    }
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw" / "followup2_p5_reeval.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote raw/followup2_p5_reeval.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
