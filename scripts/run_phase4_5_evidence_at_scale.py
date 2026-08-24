"""Phase 4.5 gap 7 -- statistically meaningful evidence at real scale.

This is a NEW, additive evidence script -- it does not modify or replace
``scripts/run_phase4_5_pipeline_demo.py`` (Phase 4.4's own evidence run) and
writes to a new, independent results directory
(``experiments/results/phase4_5_autonomy_pipeline_at_scale/``), consistent
with every prior amendment in this repository never touching a frozen
phase's own results.

What this produces, honestly, exactly as measured:

  1. Per-(failure_class, action) recovery-action efficacy, at least 40
     episodes each across a spread of seeds, with sample counts and a
     Wilson-score 95% confidence interval on the observed recovery rate
     (not just a point estimate).
  2. The safety adversarial matrix, extended to cover every failure class
     the widened taxonomy now diagnoses (not only the original three).
  3. A real, at-scale run of the ML prediction training pipeline
     (src/phase4/prediction_training.py): several hundred training seeds,
     held-out validation and test splits, full metrics (AUC, precision,
     recall, F1, Brier score) plus the run-level early-warning / lead-time
     distribution, reported per failure class.
  4. A bounded continuous-mode run (src/phase4/pipeline.py's
     ``run_continuous``) writing its own lightweight JSON-lines metrics log.
  5. The same adaptive-learning bandit-convergence evidence as
     tests/unit/test_phase44_adaptive_learning.py, at a larger episode
     count, reported here as evidence rather than only as a test assertion.

No threshold or scenario is adjusted after seeing these numbers. If a
number is bad (an action is never selected, recall for a class is 0, the
predictor's AUC is close to 0.5), it is reported as measured.
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

from src.phase4.adaptive import AdaptiveRecoveryPlanner  # noqa: E402
from src.phase4.architecture import RecoveryAction  # noqa: E402
from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig  # noqa: E402
from src.phase4.diagnosis import DiagnosisEngine  # noqa: E402
from src.phase4.memory import FailureMemoryStore  # noqa: E402
from src.phase4.monitoring import MonitoringEngine  # noqa: E402
from src.phase4.observability import PersistentEventStore  # noqa: E402
from src.phase4.pipeline import AutonomyPipeline  # noqa: E402
from src.phase4.prediction_training import SplitSeeds, train_and_persist  # noqa: E402
from src.phase4.recovery import ACTIONS, ControlledRuntimeRecoveryExecutor, RecoverySafetyGate, SignalRecoveryValidator, _provenance  # noqa: E402
from src.recovery.schema import ActionId  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    """Standard Wilson score 95% confidence interval for a binomial
    proportion. Returns None if there is no sample."""
    if total == 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    center = p + z * z / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return ((center - margin) / denom, (center + margin) / denom)


# ---------------------------------------------------------------------------
# 1. Per-(failure_class, action) recovery-action efficacy, at scale.
# ---------------------------------------------------------------------------

# (failure_class, mode, base_params_fn(seed), pre-run setup, workload_id_fn)
def _scenario(failure_class: str, seed: int):
    if failure_class == "PROCESS_TIMEOUT":
        return "cpu", {"mode": "cpu", "duration_seconds": 1.0}
    if failure_class == "PROCESS_NONZERO_EXIT":
        return "fail", {"mode": "fail"}
    if failure_class == "NETWORK_FAILURE":
        return "network", {"mode": "network", "duration_seconds": 0.05}
    if failure_class == "PROCESS_OOM":
        return "oom", {"mode": "oom", "alloc_mb": 200, "limit_mb": 32}
    if failure_class == "DATA_CORRUPTION":
        return "corruption", {"mode": "corruption"}
    if failure_class == "RESOURCE_UNAVAILABLE":
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 42000 + (seed % 5000)}
    if failure_class == "INTERMITTENT_FAILURE":
        return "flaky", {"mode": "flaky", "fail_count": 3}  # never resolves within one action attempt
    raise ValueError(failure_class)


_CLASS_ACTIONS = {
    "PROCESS_TIMEOUT": (ActionId.RETRY, ActionId.RESTART),
    "PROCESS_NONZERO_EXIT": (ActionId.RESTART, ActionId.RETRY),
    "NETWORK_FAILURE": (ActionId.RETRY,),
    "PROCESS_OOM": (ActionId.RECONFIGURE, ActionId.RETRY),
    "DATA_CORRUPTION": (ActionId.ROLLBACK, ActionId.RETRY),
    "RESOURCE_UNAVAILABLE": (ActionId.RETRY, ActionId.RECONFIGURE),
    "INTERMITTENT_FAILURE": (ActionId.RETRY,),
    "GPU_DEVICE_FAILURE": (),  # no real executable action exists for this class (see src/phase4/recovery.py)
}


def _run_one_action_trial(failure_class: str, action_id: ActionId, seed: int, environment_id: str) -> str:
    """Runs one real failing episode of ``failure_class`` then forces
    ``action_id`` (bypassing the planner's declared-order/avoidance logic,
    deliberately, so every action gets real, direct, sufficient sample
    coverage rather than whatever the planner's sequential avoidance rule
    happens to try) via the same real ``RecoverySafetyGate`` /
    ``ControlledRuntimeRecoveryExecutor`` / ``SignalRecoveryValidator``
    components the pipeline itself uses. Returns the real validated
    outcome status string."""
    with tempfile.TemporaryDirectory() as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.01, environment_id=environment_id))
        workload_id = f"efficacy-{failure_class}-{action_id.value}-{seed}"
        workload_type, params = _scenario(failure_class, seed)

        if failure_class == "DATA_CORRUPTION" and action_id == ActionId.ROLLBACK:
            runtime.run("success", {"mode": "success"}, workload_id=workload_id)  # real checkpoint to roll back to
        if failure_class == "RESOURCE_UNAVAILABLE":
            runtime.occupy_external_resource(int(params["port"]))

        result = runtime.run(workload_type, params, workload_id=workload_id)
        monitor = MonitoringEngine()
        monitor.process(result.events)
        failures = [f for f in monitor.failures if f["run_id"] == result.run_id]
        if not failures:
            store.close()
            return "NO_FAILURE_OBSERVED"  # scenario did not fail as expected for this seed; excluded by caller
        diagnosis = DiagnosisEngine().diagnose(failures[0], result.events)

        spec = ACTIONS[action_id]
        action = RecoveryAction(
            action_id=f"efficacy-probe:{result.run_id}:{action_id.value}", action_type=action_id.value,
            preconditions=(f"diagnosis={diagnosis.diagnosis_id}",), expected_effect="forced action-efficacy probe",
            risk=spec.safety_classification.value.upper(), cost=str(spec.base_cost),
            reversible=spec.reversibility in ("reversible", "partially_reversible"), authorization_required=True,
            validation_requirements=("independent_post_execution_event_check",), provenance=_provenance("phase4-evidence-at-scale"),
        )
        authorized, reason = RecoverySafetyGate().authorize(action, diagnosis)
        if not authorized:
            store.close()
            return f"SAFETY_REJECTED:{reason}"
        execution = ControlledRuntimeRecoveryExecutor(runtime).execute(action, workload_type, params, workload_id=workload_id)
        validation = SignalRecoveryValidator().validate(execution)
        runtime.close()
        store.close()
        return validation.status


def run_action_efficacy_at_scale(n_episodes: int, environment_id: str) -> dict:
    report = {}
    for failure_class, actions in _CLASS_ACTIONS.items():
        report[failure_class] = {}
        for action_id in actions:
            outcomes = [_run_one_action_trial(failure_class, action_id, seed, environment_id) for seed in range(n_episodes)]
            valid = [o for o in outcomes if o != "NO_FAILURE_OBSERVED"]
            successes = sum(1 for o in valid if o == "RECOVERED")
            total = len(valid)
            ci = wilson_interval(successes, total)
            report[failure_class][action_id.value] = {
                "n_episodes_requested": n_episodes, "n_valid_trials": total,
                "n_excluded_no_failure_observed": n_episodes - total,
                "successes": successes, "recovery_rate": (successes / total) if total else None,
                "wilson_95_ci": ci,
                "outcome_counts": {status: valid.count(status) for status in set(valid)},
            }
        if not actions:
            report[failure_class]["_note"] = "no real executable action exists for this failure class (see src/phase4/recovery.py _CANDIDATES); not fabricated"
    return report


# ---------------------------------------------------------------------------
# 2. Safety adversarial matrix, extended to every diagnosable failure class.
# ---------------------------------------------------------------------------

def run_safety_adversarial_matrix() -> list[dict]:
    gate = RecoverySafetyGate()

    class FakeDiagnosis:
        def __init__(self, hyp_name):
            self.primary_hypothesis = type("H", (), {"name": hyp_name})()
            self.foundation_references = {}

    hyp_by_class = {
        "PROCESS_NONZERO_EXIT": "PROCESS_EXIT_FAILURE", "PROCESS_TIMEOUT": "RUNTIME_TIMEOUT",
        "NETWORK_FAILURE": "NETWORK_CONNECTIVITY_FAILURE", "PROCESS_OOM": "OUT_OF_MEMORY",
        "GPU_DEVICE_FAILURE": "GPU_DEVICE_UNAVAILABLE", "DATA_CORRUPTION": "DATA_INTEGRITY_FAILURE",
        "RESOURCE_UNAVAILABLE": "RESOURCE_UNAVAILABLE", "INTERMITTENT_FAILURE": "INTERMITTENT_TRANSIENT_FAILURE",
    }
    cases = []
    for label, hyp_name in hyp_by_class.items():
        diagnosis = FakeDiagnosis(hyp_name)
        force_restart = RecoveryAction(action_id="adv", action_type=ActionId.FORCE_RESTART.value, provenance=_provenance("adversarial-probe"))
        authorized, reason = gate.authorize(force_restart, diagnosis)
        cases.append({"failure_class": label, "proposed_action": "force_restart", "authorized": authorized, "reason": reason})
        garbage = RecoveryAction(action_id="adv2", action_type="delete_production_database", provenance=_provenance("adversarial-probe"))
        authorized2, reason2 = gate.authorize(garbage, diagnosis)
        cases.append({"failure_class": label, "proposed_action": "delete_production_database", "authorized": authorized2, "reason": reason2})
    return cases


# ---------------------------------------------------------------------------
# 3. ML prediction training at scale.
# ---------------------------------------------------------------------------

def run_prediction_training_at_scale(output_dir: Path) -> dict:
    seeds = SplitSeeds(train=range(0, 600), validation=range(10_000, 10_150), test=range(20_000, 20_150))
    return train_and_persist(seeds, output_dir, timeout_seconds=0.15)


# ---------------------------------------------------------------------------
# 4. Bounded continuous mode.
# ---------------------------------------------------------------------------

def run_continuous_mode_evidence(output_dir: Path) -> dict:
    import itertools

    scenarios = [
        {"workload_type": "success", "parameters": {"mode": "success"}},
        {"workload_type": "fail", "parameters": {"mode": "fail"}},
        {"workload_type": "network", "parameters": {"mode": "network", "duration_seconds": 0.02}},
        {"workload_type": "oom", "parameters": {"mode": "oom", "alloc_mb": 200, "limit_mb": 32}},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.2, telemetry_interval_seconds=0.01))
        pipeline = AutonomyPipeline(runtime)
        report = pipeline.run_continuous(itertools.cycle(scenarios), max_episodes=40, metrics_log_path=output_dir / "continuous_mode_metrics.jsonl")
        store.close()
    return {"episodes_run": report.episodes_run, "stopped_reason": report.stopped_reason, "wall_clock_seconds": report.wall_clock_seconds, "final_state_counts": report.final_state_counts}


# ---------------------------------------------------------------------------
# 5. Adaptive-learning bandit-convergence evidence, at a larger scale.
# ---------------------------------------------------------------------------

def run_adaptive_learning_evidence() -> dict:
    import random
    from datetime import timedelta

    from src.phase4.recovery import RuleBasedRecoveryPlanner

    def ts(i):
        return (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=i)).isoformat().replace("+00:00", "Z")

    def ev(i, t, ts_, rid):
        return {"event_id": i, "event_type": t, "timestamp": ts_, "job_id": rid, "workload_id": "w1", "environment_id": "env1", "payload": {"failure_kind": "NONZERO_EXIT"} if t == "failure_detected" else {}, "provenance": {"source": "evidence", "source_record_id": i, "timestamp_quality": "EXACT"}}

    def diagnose(rid, boundary, memory):
        events = [ev("start", "execution_started", ts(0), rid), ev("fobs", "failure_detected", boundary, rid)]
        failure = {"failure_id": f"f-{rid}", "failure_class": "RESOURCE_UNAVAILABLE", "run_id": rid, "workload_id": "w1", "environment_id": "env1", "failure_timestamp": boundary, "evidence_references": ["fobs"], "provenance": {"source": "evidence", "source_record_id": "fobs", "timestamp_quality": "EXACT"}}
        return DiagnosisEngine().diagnose(failure, events, memory=memory)

    def run_bandit(planner, n_episodes, epsilon, seed):
        true_success_prob = {"retry": 0.35, "reconfigure": 0.65}
        memory = FailureMemoryStore()
        rng = random.Random(seed)
        correct = []
        for i in range(n_episodes):
            rid = f"run-{i}"
            boundary = ts(i + 1)
            diagnosis = diagnose(rid, boundary, memory)
            action = planner.plan(diagnosis, memory=memory)
            chosen = action.action_type
            if chosen not in true_success_prob:
                correct.append(0)
                continue
            realized = chosen if rng.random() >= epsilon else rng.choice(list(true_success_prob))
            outcome = "RECOVERED" if rng.random() < true_success_prob[realized] else "NOT_RECOVERED"
            memory.add(workload_id="w1", environment_id="env1", failure_class="RESOURCE_UNAVAILABLE", root_cause="RESOURCE_UNAVAILABLE", diagnosis_confidence=diagnosis.confidence, source_run_id=rid, source_diagnosis_id=diagnosis.diagnosis_id, action_taken=realized, validated_outcome=outcome, recorded_at=boundary, provenance={})
            correct.append(1 if chosen == "reconfigure" else 0)
        return correct

    adaptive_correct = run_bandit(AdaptiveRecoveryPlanner(), n_episodes=1000, epsilon=0.15, seed=987654321)
    base_correct = run_bandit(RuleBasedRecoveryPlanner(), n_episodes=1000, epsilon=0.15, seed=987654321)

    def window_rate(seq, n):
        return sum(seq[:n]) / n, sum(seq[-n:]) / n

    a_early, a_late = window_rate(adaptive_correct, 50)
    b_early, b_late = window_rate(base_correct, 50)
    return {
        "n_episodes": 1000, "true_success_prob": {"retry": 0.35, "reconfigure": 0.65},
        "adaptive_planner": {"early_window_correct_rate": a_early, "late_window_correct_rate": a_late},
        "base_planner_control": {"early_window_correct_rate": b_early, "late_window_correct_rate": b_late},
    }


def main():
    out_dir = ROOT / "experiments" / "results" / "phase4_5_autonomy_pipeline_at_scale"
    prediction_out_dir = out_dir / "prediction_artifact"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] running per-(failure_class, action) efficacy at scale (this spawns many real subprocesses)...")
    action_efficacy = run_action_efficacy_at_scale(n_episodes=40, environment_id="evidence-at-scale-environment")

    print("[2/5] running the extended safety adversarial matrix...")
    safety_matrix = run_safety_adversarial_matrix()

    print("[3/5] training the ML predictor at scale...")
    prediction_training = run_prediction_training_at_scale(prediction_out_dir)

    print("[4/5] running bounded continuous mode...")
    continuous = run_continuous_mode_evidence(out_dir)

    print("[5/5] running adaptive-learning bandit-convergence evidence...")
    adaptive_learning = run_adaptive_learning_evidence()

    report = {
        "generated_at": now(),
        "purpose": "Phase 4.5 'what's lacking' review -- statistically meaningful, at-scale evidence for all 7 gaps",
        "action_efficacy": action_efficacy,
        "safety_adversarial_matrix": safety_matrix,
        "prediction_training": prediction_training,
        "continuous_mode": continuous,
        "adaptive_learning": adaptive_learning,
    }
    (out_dir / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    unsafe_authorized = sum(1 for c in safety_matrix if c["authorized"])
    print(f"wrote {out_dir / 'results.json'}")
    print(f"safety adversarial matrix: {len(safety_matrix)} cases, {unsafe_authorized} incorrectly authorized (must be 0)")
    print(f"prediction (test split, per-checkpoint): {json.dumps(prediction_training['test_metrics']['per_checkpoint'], default=str)}")
    assert unsafe_authorized == 0, "SAFETY REGRESSION: an unsafe/out-of-scope action was authorized"


if __name__ == "__main__":
    main()
