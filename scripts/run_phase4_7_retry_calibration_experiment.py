"""Phase 4.7 -- Priority 2B: baseline (generic DecisionPolicy) vs
calibrated (AgentDecisionCalibrationProfile) retry experiment, on
IDENTICAL held-out TEST seeds, disjoint from the seeds used to fit the
calibration profile.

Usage:
    python scripts/run_phase4_7_retry_calibration_experiment.py <output_dir>
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, AgentSplitSeeds, CALIBRATION_VERSION
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline

BASE_N_SAMPLES = 5
TEST_SEEDS = range(60_000, 60_300)  # 300 episodes, matching the Phase 4.5b report's evaluation scale
SPLIT_SEEDS = AgentSplitSeeds(train=range(0, 2000), calibration=range(10_000, 12_000), test=TEST_SEEDS)


def _fresh_pipeline(agent_decision_policy=None):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store1 = PersistentEventStore(pathlib.Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(pathlib.Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=BASE_N_SAMPLES))
    pipeline = AutonomyPipeline(runtime, agent_runtime=agent_runtime, agent_decision_policy=agent_decision_policy)
    return pipeline, tmp


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z ** 2 / n
    centre = p + z ** 2 / (2 * n)
    margin = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5)
    return ((centre - margin) / denom, (centre + margin) / denom)


def run_condition(label: str, agent_decision_policy) -> dict:
    pipeline, tmp = _fresh_pipeline(agent_decision_policy)
    episodes = []
    unsafe_actions = 0
    t0 = time.perf_counter()
    try:
        for seed in TEST_SEEDS:
            result = pipeline.run_agent_task(seed, workload_id=f"{label}-{seed}")
            wrong_initially = result.diagnosis is not None
            decision = result.decision.decision if result.decision is not None else None
            retried = bool(result.action is not None and getattr(result.action, "action_type", None) == "retry" and result.execution is not None and result.execution.executed)
            final_correct = None
            if wrong_initially:
                if retried and result.execution is not None and result.execution.run_result is not None:
                    final_correct = bool(result.execution.run_result.task_result.get("is_correct"))
                else:
                    final_correct = False  # no correction attempted/executed -> still wrong
            else:
                final_correct = True
            unsafe = result.safety_authorized is False and retried
            if unsafe:
                unsafe_actions += 1
            episodes.append({
                "seed": seed, "wrong_initially": wrong_initially, "decision": decision,
                "retried": retried, "final_correct": final_correct,
                "n_samples_used": (result.execution.run_result.task_result.get("n_samples") if retried and result.execution and result.execution.run_result else BASE_N_SAMPLES),
            })
    finally:
        elapsed = time.perf_counter() - t0
        tmp.cleanup()

    n = len(episodes)
    n_wrong_initially = sum(1 for e in episodes if e["wrong_initially"])
    n_retried = sum(1 for e in episodes if e["retried"])
    n_retry_recovered = sum(1 for e in episodes if e["retried"] and e["final_correct"])
    n_final_correct = sum(1 for e in episodes if e["final_correct"])
    n_review = sum(1 for e in episodes if e["decision"] == "REVIEW")
    n_abstain = sum(1 for e in episodes if e["decision"] == "ABSTAIN")
    n_unnecessary_retry = sum(1 for e in episodes if e["retried"] and not e["wrong_initially"])  # structurally impossible here but reported for completeness
    avg_samples = sum(e["n_samples_used"] for e in episodes) / n if n else 0.0
    retry_recovery_rate = (n_retry_recovered / n_retried) if n_retried else None
    retry_recovery_ci = _wilson_ci(n_retry_recovered, n_retried) if n_retried else None

    return {
        "label": label,
        "n_episodes": n,
        "n_wrong_initially": n_wrong_initially,
        "initial_accuracy": (n - n_wrong_initially) / n,
        "final_accuracy": n_final_correct / n,
        "final_error_rate": 1.0 - (n_final_correct / n),
        "retry_rate_among_wrong": (n_retried / n_wrong_initially) if n_wrong_initially else None,
        "n_retried": n_retried,
        "retry_recovery_rate": retry_recovery_rate,
        "retry_recovery_rate_wilson_ci95": retry_recovery_ci,
        "unnecessary_retry_rate": (n_unnecessary_retry / n) if n else 0.0,
        "review_rate": n_review / n,
        "abstention_rate": n_abstain / n,
        "avg_samples_per_episode": avg_samples,
        "unsafe_action_count": unsafe_actions,
        "wall_clock_seconds": elapsed,
    }


def main(output_dir: Path) -> None:
    assert output_dir.exists(), f"output_dir must already exist: {output_dir}"

    print("fitting AgentDecisionCalibrationProfile on the CALIBRATION split (disjoint from TEST)...")
    profile = AgentDecisionCalibrationProfile.fit(SPLIT_SEEDS, base_n_samples=BASE_N_SAMPLES)

    print("running BASELINE (generic DecisionPolicy) over TEST seeds...")
    baseline = run_condition("baseline", agent_decision_policy=None)

    print("running CALIBRATED (AgentDecisionCalibrationProfile) over the SAME TEST seeds...")
    calibrated = run_condition("calibrated", agent_decision_policy=profile)

    report = {
        "calibration_version": CALIBRATION_VERSION,
        "base_n_samples": BASE_N_SAMPLES,
        "split_seeds": {
            "train": [SPLIT_SEEDS.train.start, SPLIT_SEEDS.train.stop],
            "calibration": [SPLIT_SEEDS.calibration.start, SPLIT_SEEDS.calibration.stop],
            "test": [SPLIT_SEEDS.test.start, SPLIT_SEEDS.test.stop],
        },
        "bucket_stats": {
            f"{b[0]}-{b[1]}": {
                "n_observed": s.n_observed, "n_correct": s.n_correct, "p_correct": s.p_correct,
                "n_retry_observed": s.n_retry_observed, "n_retry_correct": s.n_retry_correct, "p_retry_success": s.p_retry_success,
            }
            for b, s in profile.bucket_stats.items()
        },
        "baseline": baseline,
        "calibrated": calibrated,
    }
    (output_dir / "evaluation" / "retry_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"baseline": baseline, "calibrated": calibrated}, indent=2))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
