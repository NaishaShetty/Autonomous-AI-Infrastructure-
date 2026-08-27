"""Phase 4.5b -- at-scale, honest evidence for both fixes made in response to
the project's own strategic review after Phase 4.5 shipped:

  (A) "recognize when it's likely wrong" -- the honest, scope-split
      predictor (``PredictionScopeRouter``): real skill within the
      predictable scope (mode=cpu / PROCESS_TIMEOUT), a fixed, honestly
      labeled fallback prior everywhere else, reported per-scope alongside
      the old blended aggregate for direct comparison.
  (B) the pipeline never evaluated an actual AI/ML agent's OUTPUT
      correctness -- the new agent-task capability
      (``src/phase4/agent_task.py`` / ``agent_runtime.py``): a real
      ground-truth-checked arithmetic task, a genuine self-consistency
      uncertainty signal, and a real, executable RETRY-with-more-samples
      recovery action, wired through the same AutonomyPipeline loop.

This is a new, additive evidence script. It does not modify or replace
``scripts/run_phase4_5_evidence_at_scale.py`` and writes to a new,
independent results directory
(``experiments/results/phase4_5b_recognition_and_agent_evaluation/``).

No threshold or scenario is adjusted after seeing these numbers. If a
number is bad, it is reported as measured.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.phase4.agent_runtime import AgentRunConfig, AgentTaskRuntime  # noqa: E402
from src.phase4.agent_task import generate_task, run_self_consistency  # noqa: E402
from src.phase4.architecture import RecoveryAction  # noqa: E402
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig  # noqa: E402
from src.phase4.observability import PersistentEventStore  # noqa: E402
from src.phase4.pipeline import AutonomyPipeline  # noqa: E402
from src.phase4.prediction_training import SplitSeeds, train_and_persist_scope_router  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    if total == 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    center = p + z * z / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return ((center - margin) / denom, (center + margin) / denom)


# ---------------------------------------------------------------------------
# A. PredictionScopeRouter at scale.
# ---------------------------------------------------------------------------

def run_scope_router_at_scale(output_dir: Path) -> dict:
    seeds = SplitSeeds(train=range(0, 1500), validation=range(20000, 20300), test=range(40000, 40300))
    result = train_and_persist_scope_router(seeds, output_dir, timeout_seconds=0.15)
    return result


# ---------------------------------------------------------------------------
# B. Agent-task self-consistency accuracy curve (no subprocess -- pure
#    computation over agent_task.py, so this can run at large N quickly).
# ---------------------------------------------------------------------------

def run_self_consistency_accuracy_curve(n_seeds: int = 1000) -> dict:
    curve = {}
    for n_samples in (1, 3, 5, 10, 20):
        correct = 0
        for seed in range(n_seeds):
            instance = generate_task(seed)
            result = run_self_consistency(instance, n_samples=n_samples, base_seed=seed)
            correct += int(result.is_correct)
        curve[str(n_samples)] = {"n_seeds": n_seeds, "accuracy": correct / n_seeds}
    return curve


def run_uncertainty_signal_calibration(n_seeds: int = 1000, n_samples: int = 5) -> dict:
    """Does agreement_rate (the signal AgentUncertaintyPredictor exposes)
    actually correlate with correctness? Bucketed accuracy, reported as
    measured."""
    buckets = {"[0.0-0.4)": [], "[0.4-0.6)": [], "[0.6-0.8)": [], "[0.8-1.0]": []}
    for seed in range(n_seeds):
        instance = generate_task(seed)
        result = run_self_consistency(instance, n_samples=n_samples, base_seed=seed)
        rate = result.agreement_rate
        if rate < 0.4:
            key = "[0.0-0.4)"
        elif rate < 0.6:
            key = "[0.4-0.6)"
        elif rate < 0.8:
            key = "[0.6-0.8)"
        else:
            key = "[0.8-1.0]"
        buckets[key].append(result.is_correct)
    return {k: {"n": len(v), "accuracy": (sum(v) / len(v) if v else None)} for k, v in buckets.items()}


# ---------------------------------------------------------------------------
# C. Real pipeline evidence: decision-band breakdown for wrong answers, and
#    RETRY recovery-rate with a Wilson CI, on real subprocess executions.
# ---------------------------------------------------------------------------

def _pipeline(n_samples: int, environment_id: str):
    tmp = tempfile.TemporaryDirectory()
    store1 = PersistentEventStore(Path(tmp.name) / "e1.sqlite")
    store2 = PersistentEventStore(Path(tmp.name) / "e2.sqlite")
    runtime = ControlledRuntime(store1, RuntimeConfig(timeout_seconds=0.15, telemetry_interval_seconds=0.01, environment_id=environment_id))
    agent_runtime = AgentTaskRuntime(store2, AgentRunConfig(n_samples=n_samples, environment_id=environment_id))
    pipeline = AutonomyPipeline(runtime, agent_runtime=agent_runtime)
    return pipeline, tmp


def run_pipeline_decision_band_breakdown(n_episodes: int, n_samples: int) -> dict:
    """Real subprocess executions: for every wrong-answer incident, which
    decision band did it land in, and (for ANSWER-band incidents that
    actually executed RETRY) what was the real recovery outcome? Reports
    counts and a Wilson 95% CI on the RETRY recovery rate -- exactly as
    measured, over `n_episodes` real seeds."""
    pipeline, tmp = _pipeline(n_samples=n_samples, environment_id="phase4-5b-evidence-agent-environment")
    try:
        band_counts = {"ANSWER": 0, "REVIEW": 0, "ABSTAIN": 0}
        retry_outcomes = []
        n_wrong = 0
        n_correct = 0
        for seed in range(n_episodes):
            result = pipeline.run_agent_task(seed, workload_id=f"evidence-w-{seed}")
            if result.diagnosis is None:
                n_correct += 1
                continue
            n_wrong += 1
            band_counts[result.decision.decision] += 1
            if result.execution is not None and result.execution.executed:
                retry_outcomes.append(result.validation.status)
        recovered = sum(1 for o in retry_outcomes if o == "RECOVERED")
        ci = wilson_interval(recovered, len(retry_outcomes))
        return {
            "n_episodes": n_episodes, "n_samples": n_samples,
            "n_correct_first_try": n_correct, "n_wrong_first_try": n_wrong,
            "decision_band_counts_among_wrong": band_counts,
            "retry_executions": len(retry_outcomes),
            "retry_recovered": recovered,
            "retry_recovery_rate": (recovered / len(retry_outcomes)) if retry_outcomes else None,
            "retry_recovery_rate_wilson_95ci": ci,
        }
    finally:
        tmp.cleanup()


def main():
    out_dir = ROOT / "experiments" / "results" / "phase4_5b_recognition_and_agent_evaluation"
    scope_router_out_dir = out_dir / "prediction_scope_router_artifact"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] training PredictionScopeRouter at scale (honest, scope-split prediction)...")
    scope_router = run_scope_router_at_scale(scope_router_out_dir)

    print("[2/4] real AI/ML agent task: self-consistency accuracy curve (n_samples=1..20, 1000 seeds each)...")
    accuracy_curve = run_self_consistency_accuracy_curve(n_seeds=1000)
    calibration = run_uncertainty_signal_calibration(n_seeds=1000, n_samples=5)

    print("[3/4] real pipeline decision-band breakdown at n_samples=1 (300 real subprocess episodes)...")
    band_breakdown_n1 = run_pipeline_decision_band_breakdown(n_episodes=300, n_samples=1)

    print("[4/4] real pipeline decision-band breakdown at n_samples=5 (300 real subprocess episodes)...")
    band_breakdown_n5 = run_pipeline_decision_band_breakdown(n_episodes=300, n_samples=5)

    report = {
        "generated_at": now(),
        "purpose": "Phase 4.5b -- at-scale evidence for (A) the honest scope-split predictor and (B) real AI/ML agent output-correctness evaluation",
        "prediction_scope_router": {
            "corpus_sizes": scope_router["corpus_sizes"],
            "threshold": scope_router["threshold"],
            "fallback_priors": scope_router["fallback_priors"],
            "scoped_test_metrics": scope_router["scoped_test_metrics"],
        },
        "agent_task_self_consistency_accuracy_curve": accuracy_curve,
        "agent_task_uncertainty_signal_calibration": calibration,
        "agent_pipeline_decision_band_breakdown": {
            "n_samples_1": band_breakdown_n1,
            "n_samples_5": band_breakdown_n5,
        },
    }
    (out_dir / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    print(f"wrote {out_dir / 'results.json'}")
    print(f"predictable-scope AUC (real trained-model skill, timeout-only): {scope_router['scoped_test_metrics']['predictable_scope'].get('auc')}")
    print(f"router combined-output AUC (all scopes, NOT comparable to the old single-model 0.515 -- see prediction_training.py's evaluate_by_scope docstring): {scope_router['scoped_test_metrics']['router_combined_output_all_scopes'].get('auc')}")
    print("for a genuine apples-to-apples comparison against the original single blended model, see docs/archive/PHASE4_5_GAP_FIXES_REPORT.md's reported AUC=0.515 (that model never saw `mode` at all)")
    print(f"agent self-consistency accuracy curve: {json.dumps(accuracy_curve)}")
    print(f"n_samples=1 decision-band breakdown: {json.dumps(band_breakdown_n1, default=str)}")
    print(f"n_samples=5 decision-band breakdown: {json.dumps(band_breakdown_n5, default=str)}")


if __name__ == "__main__":
    main()
