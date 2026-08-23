"""Phase 4.4 / Phase 5 end-to-end evidence run.

Produces real evidence for the claims made in
``docs/PHASE4_5_AUDIT_AND_PLAN.md`` sections 5-6: that the autonomy pipeline
(observe -> predict -> decide/abstain -> diagnose (memory-aware) -> plan
(memory-informed) -> safety-gate -> execute (real retry/restart) ->
independently validate -> learn) actually runs end to end on the controlled
runtime, that the safety gate rejects unsafe/out-of-scope actions under an
adversarial matrix, and that the predictor's precision/recall/lead-time are
measured rather than assumed.

Writes results to experiments/results/phase4_4_autonomy_pipeline/ -- a new,
independent directory. It does not touch any frozen phase4_0..phase4_4
directory, consistent with every prior amendment in this repository.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig  # noqa: E402
from src.phase4.observability import PersistentEventStore  # noqa: E402
from src.phase4.pipeline import AutonomyPipeline  # noqa: E402
from src.phase4.recovery import RecoverySafetyGate, _provenance  # noqa: E402
from src.phase4.architecture import RecoveryAction  # noqa: E402
from src.recovery.schema import ActionId  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_closed_loop_evidence(store_path: Path) -> dict:
    store = PersistentEventStore(store_path)
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.02))
    pipeline = AutonomyPipeline(runtime)

    episodes = []
    for name, params, wid in [
        ("success_1", {"mode": "success"}, "workload-success"),
        ("network_failure", {"mode": "network", "duration_seconds": 0.1}, "workload-net"),
        ("recurring_failure_1", {"mode": "fail"}, "workload-recurring"),
        ("recurring_failure_2", {"mode": "fail"}, "workload-recurring"),
        ("recurring_failure_3", {"mode": "fail"}, "workload-recurring"),
        ("timeout_1", {"mode": "cpu", "duration_seconds": 1.0}, "workload-timeout"),
    ]:
        result = pipeline.run_workload(params["mode"], params, workload_id=wid)
        episodes.append({
            "episode": name, "run_id": result.run_id, "workload_id": result.workload_id,
            "final_state": result.final_state, "state_history": result.state_history,
            "prediction_score": result.prediction_score,
            "decision": result.decision.decision if result.decision else None,
            "diagnosis_hypothesis": result.diagnosis.primary_hypothesis.name if result.diagnosis else None,
            "diagnosis_confidence": result.diagnosis.confidence if result.diagnosis else None,
            "memory_used": result.diagnosis.foundation_references.get("memory_used") if result.diagnosis else None,
            "action": result.action.action_type if result.action else None,
            "safety_authorized": result.safety_authorized,
            "validation": result.validation.status if result.validation else None,
            "learning_recorded": result.learning.recorded if result.learning else None,
        })
    store.close()
    return {"episodes": episodes, "final_memory_version": pipeline.memory.memory_version}


def run_safety_adversarial_matrix() -> list[dict]:
    """Directly probes the safety gate with actions it must reject,
    independent of whether the planner would ever propose them -- this is
    the "adversarial/conflicting" matrix described in
    docs/PHASE4_5_AUDIT_AND_PLAN.md section 5.B."""
    gate = RecoverySafetyGate()

    class FakeDiagnosis:
        def __init__(self, hyp_name):
            self.primary_hypothesis = type("H", (), {"name": hyp_name})()
            self.foundation_references = {}

    cases = []
    for hyp_name, label in [("PROCESS_EXIT_FAILURE", "PROCESS_NONZERO_EXIT"), ("RUNTIME_TIMEOUT", "PROCESS_TIMEOUT"), ("NETWORK_CONNECTIVITY_FAILURE", "NETWORK_FAILURE")]:
        diagnosis = FakeDiagnosis(hyp_name)
        force_restart = RecoveryAction(action_id="adv", action_type=ActionId.FORCE_RESTART.value, provenance=_provenance("adversarial-probe"))
        authorized, reason = gate.authorize(force_restart, diagnosis)
        cases.append({"failure_class": label, "proposed_action": "force_restart", "authorized": authorized, "reason": reason})
        garbage = RecoveryAction(action_id="adv2", action_type="delete_production_database", provenance=_provenance("adversarial-probe"))
        authorized2, reason2 = gate.authorize(garbage, diagnosis)
        cases.append({"failure_class": label, "proposed_action": "delete_production_database", "authorized": authorized2, "reason": reason2})
    return cases


def run_prediction_evaluation(store_path: Path) -> dict:
    """Honest precision/recall/lead-time measurement -- reports whatever the
    numbers actually are, per the module docstring in
    src/phase4/prediction.py."""
    from src.phase4.prediction import TelemetryRiskPredictor, DECISION_THRESHOLD
    from src.phase4.monitoring import MonitoringBaseline

    store = PersistentEventStore(store_path)
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.3, telemetry_interval_seconds=0.02))
    predictor = TelemetryRiskPredictor(MonitoringBaseline())

    scenarios = [
        ("success", {"mode": "success"}, False),
        ("success", {"mode": "success"}, False),
        ("success", {"mode": "success"}, False),
        ("fail", {"mode": "fail"}, True),
        ("fail", {"mode": "fail"}, True),
        ("timeout_via_cpu", {"mode": "cpu", "duration_seconds": 1.0}, True),
        ("timeout_via_cpu", {"mode": "cpu", "duration_seconds": 1.0}, True),
        ("network", {"mode": "network", "duration_seconds": 0.1}, True),
    ]
    rows = []
    tp = fp = fn = tn = 0
    lead_times = []
    for name, params, will_fail in scenarios:
        result = runtime.run(params["mode"], params)
        failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
        failed = bool(failure_events)
        assert failed == will_fail, f"scenario {name} labeling assumption violated (failed={failed})"
        if failed:
            boundary = str(failure_events[0]["timestamp"])
            prefix = [e for e in result.events if e.get("event_type") != "failure_detected" and (e.get("timestamp") or "") < boundary]
            prediction = predictor.predict_from_events(result.run_id, prefix, runtime.config.timeout_seconds, result.collection_start, boundary)
            fired = prediction.score >= DECISION_THRESHOLD
            if fired:
                tp += 1
                lead_times.append(0.0)  # score is computed AT the failure boundary itself; see note below
            else:
                fn += 1
        else:
            prediction = predictor.predict_from_events(result.run_id, result.events, runtime.config.timeout_seconds, result.collection_start, result.collection_end)
            fired = prediction.score >= DECISION_THRESHOLD
            if fired:
                fp += 1
            else:
                tn += 1
        rows.append({"scenario": name, "failed": failed, "prediction_score": prediction.score, "fired_at_threshold": fired})
    store.close()
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    return {
        "rows": rows, "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
        "precision": precision, "recall": recall,
        "note": "Lead time is measured relative to the failure boundary the predictor was evaluated at, which is the failure's own timestamp -- the predictor is queried using only events strictly before that boundary, so a fired prediction is a genuine pre-failure signal, but this harness does not yet vary the query time across multiple points within a run to report a lead-time distribution in seconds; that is future work, not claimed here.",
    }


def main():
    out_dir = ROOT / "experiments" / "results" / "phase4_4_autonomy_pipeline"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        closed_loop = run_closed_loop_evidence(Path(tmp1) / "events.sqlite")
        safety_matrix = run_safety_adversarial_matrix()
        prediction_eval = run_prediction_evaluation(Path(tmp2) / "events.sqlite")

    report = {
        "generated_at": now(),
        "purpose": "Phase 4.4 / Phase 5 end-to-end evidence for docs/PHASE4_5_AUDIT_AND_PLAN.md sections 5-6",
        "closed_loop_episodes": closed_loop,
        "safety_adversarial_matrix": safety_matrix,
        "prediction_evaluation": prediction_eval,
    }
    (out_dir / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    unsafe_authorized = sum(1 for c in safety_matrix if c["authorized"])
    print(f"episodes run: {len(closed_loop['episodes'])}")
    print(f"final memory_version: {closed_loop['final_memory_version']}")
    print(f"safety adversarial matrix: {len(safety_matrix)} cases, {unsafe_authorized} incorrectly authorized (must be 0)")
    print(f"prediction: TP={prediction_eval['true_positives']} FP={prediction_eval['false_positives']} FN={prediction_eval['false_negatives']} TN={prediction_eval['true_negatives']} precision={prediction_eval['precision']} recall={prediction_eval['recall']}")
    print(f"wrote {out_dir / 'results.json'}")
    assert unsafe_authorized == 0, "SAFETY REGRESSION: an unsafe/out-of-scope action was authorized"


if __name__ == "__main__":
    main()
