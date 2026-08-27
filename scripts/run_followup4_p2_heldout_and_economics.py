"""Post-P5-remediation follow-up 4 -- P2-W1 (larger held-out evaluation for
the calibrated arithmetic uncertainty/decision policy) + P2-W3 (retry
economics sensitivity grid, pre-registered in
``protocol/FOLLOWUP4_P2W3_ECONOMICS_GRID_PROTOCOL.md`` BEFORE this script
was run).

P2-W1: generic vs. calibrated policy compared on a genuinely disjoint,
much larger held-out set (600 seeds vs. the original 300) than any prior
report used. No threshold is tuned on this set.

P2-W3: the pre-registered 18-point grid over
(COST_RETRY_PER_EXTRA_SAMPLE, BENEFIT_CORRECT, COST_WRONG_ANSWER),
evaluated via module-attribute monkey-patching of
``src.phase4.agent_calibration``'s three utility constants (restored after
each configuration) around a single, unchanged, once-fitted
``AgentDecisionCalibrationProfile`` -- see the protocol doc for why
re-fitting per grid point is unnecessary and was not done.

Usage:
    python scripts/run_followup4_p2_heldout_and_economics.py <run_dir>

Writes:
    <run_dir>/raw/followup4_p2w1_heldout.json
    <run_dir>/raw/followup4_p2w3_economics_grid.json
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.phase4 import agent_calibration
from src.phase4.agent_calibration import AgentDecisionCalibrationProfile, AgentSplitSeeds, CALIBRATION_VERSION
from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline

BASE_N_SAMPLES = 5
CALIBRATION_SEEDS = range(10_000, 12_000)
TRAIN_SEEDS = range(0, 2000)

# P2-W1: much larger, genuinely fresh held-out set -- disjoint from train,
# calibration, the original Phase 4.7/4.10 test (60_000-60_300), and
# follow-up 2's fresh test (70_000-70_300).
P2W1_HELDOUT_SEEDS = range(80_000, 80_600)  # 600 seeds, 2x the original 300

# P2-W3: fixed grid-evaluation seed set, disjoint from all of the above.
P2W3_GRID_SEEDS = range(90_000, 90_040)  # 40 seeds

GRID_COST_RETRY = [0.0, 0.01, 0.05]
GRID_BENEFIT_CORRECT = [1.0, 2.0]
GRID_COST_WRONG = [0.5, 1.0, 2.0]


def _fresh_pipeline(agent_decision_policy=None):
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store1 = PersistentEventStore(pathlib.Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(pathlib.Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=BASE_N_SAMPLES))
    pipeline = AutonomyPipeline(runtime, agent_runtime=agent_runtime, agent_decision_policy=agent_decision_policy)
    return pipeline, tmp


def _wilson_ci(successes: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z ** 2 / n
    centre = p + z ** 2 / (2 * n)
    margin = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5)
    return ((centre - margin) / denom, (centre + margin) / denom)


def run_condition(label: str, test_seeds, agent_decision_policy) -> dict:
    pipeline, tmp = _fresh_pipeline(agent_decision_policy)
    episodes = []
    unsafe_actions = 0
    try:
        for seed in test_seeds:
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
            episodes.append({
                "seed": seed, "wrong_initially": wrong_initially, "decision": decision,
                "retried": retried, "final_correct": final_correct,
            })
    finally:
        tmp.cleanup()

    n = len(episodes)
    n_wrong = sum(1 for e in episodes if e["wrong_initially"])
    n_retried = sum(1 for e in episodes if e["retried"])
    n_retry_recovered = sum(1 for e in episodes if e["retried"] and e["final_correct"])
    n_final_correct = sum(1 for e in episodes if e["final_correct"])
    n_review = sum(1 for e in episodes if e["decision"] == "REVIEW")
    n_abstain = sum(1 for e in episodes if e["decision"] == "ABSTAIN")
    n_unnecessary_retry = sum(1 for e in episodes if e["retried"] and not e["wrong_initially"])

    return {
        "label": label, "n_episodes": n, "n_wrong_initially": n_wrong,
        "initial_accuracy": (n - n_wrong) / n if n else None,
        "initial_error_rate": (n_wrong / n) if n else None,
        "final_accuracy": (n_final_correct / n) if n else None,
        "final_accuracy_wilson_ci95": _wilson_ci(n_final_correct, n),
        "final_error_rate": (1.0 - (n_final_correct / n)) if n else None,
        "retry_rate_among_wrong": (n_retried / n_wrong) if n_wrong else None,
        "n_retried": n_retried,
        "pct_wrong_corrected_by_retry": (n_retry_recovered / n_wrong) if n_wrong else None,
        "retry_recovery_rate": (n_retry_recovered / n_retried) if n_retried else None,
        "retry_recovery_rate_wilson_ci95": _wilson_ci(n_retry_recovered, n_retried) if n_retried else None,
        "unnecessary_retry_rate": (n_unnecessary_retry / n) if n else 0.0,
        "review_rate": n_review / n if n else None, "abstention_rate": n_abstain / n if n else None,
        "unsafe_action_count": unsafe_actions,
    }


def run_p2w1(run_dir: Path, profile) -> None:
    print(f"[P2-W1] generic policy on {len(P2W1_HELDOUT_SEEDS)} fresh held-out seeds...")
    generic = run_condition("p2w1-generic", P2W1_HELDOUT_SEEDS, agent_decision_policy=None)
    print(f"[P2-W1] calibrated policy on the SAME {len(P2W1_HELDOUT_SEEDS)} fresh held-out seeds...")
    calibrated = run_condition("p2w1-calibrated", P2W1_HELDOUT_SEEDS, agent_decision_policy=profile)

    out = {
        "n_episodes": len(P2W1_HELDOUT_SEEDS),
        "heldout_seed_range": [P2W1_HELDOUT_SEEDS.start, P2W1_HELDOUT_SEEDS.stop],
        "prior_report_seed_range_for_comparison": [60_000, 60_300],
        "generic": generic,
        "calibrated": calibrated,
        "calibrated_improvement_survives": (
            calibrated["final_accuracy"] is not None and generic["final_accuracy"] is not None
            and calibrated["final_accuracy"] >= generic["final_accuracy"]
        ),
    }
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw" / "followup4_p2w1_heldout.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote raw/followup4_p2w1_heldout.json")


def _realized_utility(episode, utilities_by_decision):
    return utilities_by_decision.get(episode["decision"])


def run_p2w3(run_dir: Path, profile) -> None:
    grid = list(product(GRID_COST_RETRY, GRID_BENEFIT_CORRECT, GRID_COST_WRONG))
    print(f"[P2-W3] running {len(grid)} pre-registered configurations over {len(P2W3_GRID_SEEDS)} seeds each...")

    orig_cost_retry = agent_calibration.COST_RETRY_PER_EXTRA_SAMPLE
    orig_benefit = agent_calibration.BENEFIT_CORRECT
    orig_cost_wrong = agent_calibration.COST_WRONG_ANSWER

    configs_out = []
    try:
        for i, (cost_retry, benefit_correct, cost_wrong) in enumerate(grid):
            agent_calibration.COST_RETRY_PER_EXTRA_SAMPLE = cost_retry
            agent_calibration.BENEFIT_CORRECT = benefit_correct
            agent_calibration.COST_WRONG_ANSWER = cost_wrong
            try:
                label = f"p2w3-config{i}"
                print(f"  [{i + 1}/{len(grid)}] cost_retry={cost_retry} benefit_correct={benefit_correct} cost_wrong={cost_wrong}")
                result = run_condition(label, P2W3_GRID_SEEDS, agent_decision_policy=profile)
                result["grid_config"] = {
                    "cost_retry_per_extra_sample": cost_retry,
                    "benefit_correct": benefit_correct,
                    "cost_wrong_answer": cost_wrong,
                    "is_project_baseline": (cost_retry == 0.01 and benefit_correct == 1.0 and cost_wrong == 1.0),
                }
                configs_out.append(result)
            finally:
                agent_calibration.COST_RETRY_PER_EXTRA_SAMPLE = orig_cost_retry
                agent_calibration.BENEFIT_CORRECT = orig_benefit
                agent_calibration.COST_WRONG_ANSWER = orig_cost_wrong
    finally:
        agent_calibration.COST_RETRY_PER_EXTRA_SAMPLE = orig_cost_retry
        agent_calibration.BENEFIT_CORRECT = orig_benefit
        agent_calibration.COST_WRONG_ANSWER = orig_cost_wrong

    final_error_rates = [c["final_error_rate"] for c in configs_out if c["final_error_rate"] is not None]
    unsafe_counts = [c["unsafe_action_count"] for c in configs_out]

    out = {
        "protocol_file": "protocol/FOLLOWUP4_P2W3_ECONOMICS_GRID_PROTOCOL.md",
        "grid_seed_range": [P2W3_GRID_SEEDS.start, P2W3_GRID_SEEDS.stop],
        "n_configurations": len(grid),
        "configurations": configs_out,
        "summary": {
            "final_error_rate_min": min(final_error_rates) if final_error_rates else None,
            "final_error_rate_max": max(final_error_rates) if final_error_rates else None,
            "final_error_rate_range": (max(final_error_rates) - min(final_error_rates)) if final_error_rates else None,
            "unsafe_action_count_max": max(unsafe_counts) if unsafe_counts else None,
            "any_config_worse_than_never_retry": None,  # filled in narratively in the report; needs a no-retry baseline for exact comparison
        },
    }
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw" / "followup4_p2w3_economics_grid.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote raw/followup4_p2w3_economics_grid.json")


def main(run_dir: Path) -> None:
    split_seeds = AgentSplitSeeds(train=TRAIN_SEEDS, calibration=CALIBRATION_SEEDS, test=P2W1_HELDOUT_SEEDS)
    print("fitting AgentDecisionCalibrationProfile once on the unchanged CALIBRATION split...")
    profile = AgentDecisionCalibrationProfile.fit(split_seeds, base_n_samples=BASE_N_SAMPLES)

    run_p2w1(run_dir, profile)
    run_p2w3(run_dir, profile)
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
