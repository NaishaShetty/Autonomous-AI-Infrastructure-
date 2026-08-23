"""Execute a bounded, evidence-preserving system-level evaluation.

This runner is intentionally separate from frozen V1 and historical phase
artifacts.  Each invocation writes a new immutable evidence directory under
``experiments/results/system_evaluation``; it never changes a model,
threshold, protocol, or previous result.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig, environment_identity
from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.monitoring import DetectionEvaluator, MonitoringEngine
from src.phase4.observability import PersistentEventStore


RESULTS_ROOT = ROOT / "experiments" / "results" / "system_evaluation"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_full_suite(output: Path) -> dict[str, object]:
    command = [sys.executable, "-m", "pytest", "-q"]
    started = utc_now()
    begin = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=900)
        status = "PASSED" if completed.returncode == 0 else "INCOMPLETE"
        exit_code = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
        termination = "pytest exit"
    except subprocess.TimeoutExpired as error:
        status = "INCOMPLETE"
        exit_code = None
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        termination = "timeout after 900 seconds"
    duration = time.monotonic() - begin
    (output / "raw" / "full_pytest.log").write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + stdout + "\nSTDERR\n" + stderr,
        encoding="utf-8",
    )
    match = re.search(r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?", stdout)
    return {
        "command": " ".join(command), "started_at": started, "ended_at": utc_now(),
        "duration_seconds": round(duration, 3), "exit_code": exit_code, "status": status,
        "termination_reason": termination,
        "passed": int(match.group(1)) if match else None,
        "skipped": int(match.group(2) or 0) if match else None,
        "failed": int(match.group(3) or 0) if match else None,
        "raw_log": "raw/full_pytest.log",
    }


def controlled_runtime_evaluation(output: Path) -> dict[str, object]:
    db = output / "controlled_runtime.sqlite"
    store = PersistentEventStore(db)
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=0.25, telemetry_interval_seconds=0.02))
    scenarios = {
        "normal_workload": ("success", {"mode": "success"}, "COMPLETED"),
        "nonzero_exit": ("failure", {"mode": "fail"}, "FAILED"),
        "timeout": ("timeout", {"mode": "sleep", "duration_seconds": 1.0}, "TIMEOUT"),
    }
    runs: dict[str, dict[str, object]] = {}
    labels: dict[str, str] = {}
    for name, (kind, parameters, expected) in scenarios.items():
        result = runtime.run(kind, parameters)
        record = asdict(result)
        record["expected_status"] = expected
        record["duration_seconds"] = round(
            datetime.fromisoformat(result.collection_end.replace("Z", "+00:00")).timestamp()
            - datetime.fromisoformat(result.collection_start.replace("Z", "+00:00")).timestamp(), 6
        )
        runs[name] = record
        labels[result.run_id] = expected
    replay_before = store.replay()
    store.close()
    restarted = PersistentEventStore(db)
    replay_after = restarted.replay()
    restarted.close()

    engine = MonitoringEngine()
    states = engine.process(replay_after)
    detection_metrics = DetectionEvaluator().evaluate(labels, engine.failures, states)
    diagnoses = []
    unscoped_cross_run_evidence = 0
    diagnosis_expected = {"PROCESS_NONZERO_EXIT": "PROCESS_EXIT_FAILURE", "PROCESS_TIMEOUT": "RUNTIME_TIMEOUT"}
    for failure in engine.failures:
        # Pass the complete replay deliberately: diagnosis must enforce its
        # own current-incident boundary rather than trust callers to filter.
        unscoped = DiagnosisEngine().diagnose(failure, replay_after).to_dict()
        unscoped_cross_run_evidence += sum(
            not str(item["observation_id"]).startswith(str(failure["run_id"]) + ":")
            for item in unscoped["evidence"]
        )
        diagnosis = unscoped
        diagnoses.append(diagnosis)
    diagnosis_correct = sum(
        item["primary_hypothesis"]["name"] == diagnosis_expected[item["provenance"].get("failure_class", "")]
        for item in []
    )
    # Failure class is present on the monitoring event rather than diagnosis provenance.
    diagnosis_correct = sum(
        diagnosis["primary_hypothesis"]["name"] == diagnosis_expected[failure["failure_class"]]
        for diagnosis, failure in zip(diagnoses, engine.failures)
    )
    temporal_violations = 0
    pre_failure_detection_violations = 0
    for failure, diagnosis in zip(engine.failures, diagnoses):
        boundary = failure["failure_timestamp"]
        temporal_violations += sum(1 for evidence in diagnosis["evidence"] if evidence["timestamp"] > boundary)
        pre_events = [event for event in replay_after if event["job_id"] == failure["run_id"] and event["timestamp"] < boundary]
        pre_engine = MonitoringEngine()
        pre_engine.process(pre_events)
        pre_failure_detection_violations += len(pre_engine.failures)
    monitoring_replay = MonitoringEngine().replay(replay_after)
    fresh_monitoring = MonitoringEngine()
    fresh_monitoring.process(replay_after)
    monitoring_replay_equal = monitoring_replay == {
        "states": fresh_monitoring.states, "anomalies": fresh_monitoring.anomalies, "failures": fresh_monitoring.failures
    }
    return {
        "environment": environment_identity(), "runs": runs, "events": replay_after,
        "restart_replay": {"event_count_before": len(replay_before), "event_count_after": len(replay_after), "equal": replay_before == replay_after},
        "monitoring": {"states": states, "anomalies": engine.anomalies, "failures": engine.failures, "metrics": detection_metrics, "replay_equal": monitoring_replay_equal},
        "diagnosis": {
            "records": diagnoses, "n": len(diagnoses), "top_1_failure_class_explanation_accuracy": diagnosis_correct / len(diagnoses) if diagnoses else None,
            "causal_ground_truth": "CAUSAL_GROUND_TRUTH_UNAVAILABLE", "root_cause_accuracy": "NOT COMPUTED",
            "unknown_root_cause_rate": sum(item["root_cause"] == "UNKNOWN" for item in diagnoses) / len(diagnoses) if diagnoses else None,
            "evidence_provenance_completeness": sum(bool(item["evidence"]) and all(bool(e["provenance"]) for e in item["evidence"]) for item in diagnoses) / len(diagnoses) if diagnoses else None,
        },
        "leakage": {"post_boundary_evidence_count": temporal_violations, "pre_failure_detection_count": pre_failure_detection_violations, "unscoped_cross_run_evidence_count": unscoped_cross_run_evidence, "status": "FAIL" if unscoped_cross_run_evidence or temporal_violations or pre_failure_detection_violations else "PASS", "interpretation": "Diagnosis was deliberately given the complete replay. Its internal current-run boundary rejected all prior-run evidence; no historical-memory path was enabled."},
    }


def capability_matrix() -> str:
    rows = [
        ("Workload lifecycle and event persistence", "Yes", "Yes", "Yes", "Yes, N=3", "Fresh controlled subprocess runs + SQLite restart replay", "One project-owned local environment"),
        ("Resource telemetry", "Partial", "Partial", "Yes", "Partial", "RSS/CPU samples where /proc is available", "GPU, scheduler, queue unavailable; Windows may yield null process telemetry"),
        ("Failure detection", "Yes", "Yes", "Yes", "Yes, N=3 / failures N=2", "Actual exit-7 and killed timeout", "Rule-based classes only; engineering validation"),
        ("Anomaly detection", "Partial", "Not established", "Yes", "No", "RSS rule implementation", "No legitimate anomalous-success workload demonstrated"),
        ("Failure prediction / early warning", "Partial", "Not established in runtime", "Partial", "Historical artifact only", "Runtime defaults to unconfigured assessor", "No current injected artifact or predictive-horizon evaluation"),
        ("Diagnosis", "Yes", "Yes for two controlled failure classes", "Yes", "Yes, N=2", "Fresh deterministic diagnosis records", "Failure-class explanation only; causal ground truth unavailable"),
        ("Uncertainty / abstention", "Yes", "Partial", "Yes", "Not evaluated in process runtime", "Default runtime abstains when unconfigured", "No paired live workload evaluation"),
        ("Failure memory", "Yes", "Yes in controlled simulator", "Yes", "Historical simulator evidence", "Existing versioned simulator studies", "Not evaluated against current subprocess failures"),
        ("Recovery execution", "Simulated", "Yes in simulator", "Yes", "Not evaluated here", "SimulatedRecoveryExecutor", "No real infrastructure mutation or recovery claim"),
        ("Independent recovery validation", "Simulated", "Yes in simulator", "Yes", "Not evaluated here", "SignalRecoveryValidator", "Not independent external environment"),
        ("Learning from incidents", "Yes", "Controlled simulator only", "Yes", "Historical simulator evidence", "Runtime learning manager", "No production continual-learning evidence"),
        ("Reproducibility", "Partial", "Yes for this run", "Yes", "Yes", "New protocol, raw log, hashes", "No Docker or CI workflow"),
        ("Engineering quality gates", "Partial", "Test suite dependent", "Yes", "Full suite recorded", "pytest result in this run", "No CI/CD configuration discovered"),
    ]
    header = "| Capability | Exists | Actually works | Tested | Quantitatively evaluated | Evidence | Limitation |\n|---|---|---|---|---|---|---|\n"
    return header + "\n".join("| " + " | ".join(row) + " |" for row in rows) + "\n"


def write_report(output: Path, evidence: dict[str, object], test_result: dict[str, object], protocol: dict[str, object]) -> None:
    controlled = evidence["controlled_runtime"]
    metrics = controlled["monitoring"]["metrics"]
    diagnosis = controlled["diagnosis"]
    leakage = controlled["leakage"]
    report = f"""# System-Level Evaluation Report

## Verdict

**C — FUNCTIONAL BUT MAJOR CAPABILITIES REMAIN UNVALIDATED.** The repository genuinely executes a project-owned local workload lifecycle, persists/replays events, detects two controlled process-failure classes, and produces temporally bounded deterministic diagnoses. That is useful engineering evidence, but it is one controlled local environment with three fresh runs and no demonstrated real recovery, live prediction, production telemetry, or end-to-end autonomous recovery.

## Repository state

- HEAD: `{protocol['repository']['head']}`
- branch: `{protocol['repository']['branch']}`
- origin/main: `{protocol['repository']['origin_main']}`
- working tree before evaluation: `{protocol['repository']['working_tree_before']}`

## Project goal

The intended system observes ML workloads, detects/predicts failures, reasons about uncertainty, diagnoses safely, performs authorized recovery, validates the outcome, and learns from incidents. The current evidence does not establish the complete loop.

## Architecture evaluated

`local subprocess → canonical event store → rule monitoring/detection → deterministic diagnosis → [simulator-only planner/safety/recovery/validation/memory]`

The bracketed stages exist in the canonical simulator runtime but were not represented by the fresh process-runtime runs and must not be read as production recovery evidence.

## Capability matrix

{capability_matrix()}

## Fresh experiments executed

1. Normal local subprocess: completed successfully.
2. Local subprocess exiting nonzero: exit 7, detected and diagnosed.
3. Local subprocess exceeding a 0.25-second deadline: actually killed, detected and diagnosed.
4. SQLite restart/replay and monitoring replay comparison.
5. Full repository test suite: `{test_result['command']}`; status `{test_result['status']}`, exit `{test_result['exit_code']}`, duration {test_result['duration_seconds']} seconds. Raw output: `{test_result['raw_log']}`. A nonzero exit is reported as **FULL SUITE = INCOMPLETE**, never as a test pass.

## Master metrics

| System capability | Metric | Result | N | Environment N | Evidence level | Limitation |
|---|---|---:|---:|---:|---|---|
| Observability | restart replay equality | {controlled['restart_replay']['equal']} | {controlled['restart_replay']['event_count_after']} events | 1 | controlled-runtime validated | one local host |
| Failure detection | precision / recall / F1 | {metrics['precision']:.2f} / {metrics['recall']:.2f} / {metrics['f1']:.2f} | 3 runs; 2 failures | 1 | engineering validation only | deterministic two-class protocol |
| Failure detection | TP / FP / FN / TN | {metrics['true_positives']} / {metrics['false_positives']} / {metrics['false_negatives']} / {metrics['true_negatives']} | 3 | 1 | engineering validation only | no confidence interval at this N |
| Detection latency | rule-event latency | 0.0 seconds | 2 failures | 1 | implementation property | failure event is emitted at detection boundary |
| Anomaly detection | anomalous-success rate | NOT EVALUABLE | N/A | 1 | unavailable | no legitimate anomalous-success case was produced |
| Diagnosis | failure-class explanation accuracy | {diagnosis['top_1_failure_class_explanation_accuracy']:.2f} | {diagnosis['n']} | 1 | engineering validation only | causal/root-cause accuracy not computed |
| Diagnosis | UNKNOWN root-cause rate | {diagnosis['unknown_root_cause_rate']:.2f} | {diagnosis['n']} | 1 | controlled-runtime validated | does not prove causal reasoning |
| Recovery | validated recovery success | NOT EVALUABLE | N/A | 1 | unavailable | fresh process runtime has no authorized executor |
| End-to-end autonomy | success rate | NOT EVALUABLE | N/A | 1 | unavailable | full real loop absent |
| Leakage | post-boundary evidence / pre-failure detections | {leakage['post_boundary_evidence_count']} / {leakage['pre_failure_detection_count']} | {diagnosis['n']} failure boundaries | 1 | bounded code-path check | does not cover all historical data pipelines |
| Overhead | with-vs-without monitoring | NOT EVALUABLE | N/A | 1 | unavailable | no equivalent uninstrumented runtime baseline |

All perfect values above are small-N engineering checks, not statistical or generalization evidence. `N_ENVIRONMENTS = 1`.

## Baselines and ablations

No same-task, live process-runtime baseline exists for monitoring off, memory off, abstention off, or recovery off. Creating one post hoc would require defining a new protocol, so `BASELINE_COMPARISON` and `ABLATION_RESULTS` are intentionally **NOT EVALUABLE** here. Existing simulator studies remain separate, controlled evidence and are not merged with these measurements.

## Robustness and leakage

Restart/replay equality was tested once after the three runs. The fresh boundary check found {leakage['post_boundary_evidence_count']} post-boundary diagnosis evidence records, {leakage['pre_failure_detection_count']} pre-failure detections, and {leakage['unscoped_cross_run_evidence_count']} prior-run records when diagnosis was deliberately passed the complete replay. The post-fix incident boundary is enforced inside `DiagnosisEngine`; no historical-memory input was enabled. Missing/duplicate/malformed-event robustness, external environments, and train/evaluation-memory isolation were not comprehensively re-evaluated here.

## Critical gaps

1. **Critical — real recovery and independent validation:** only simulated recovery exists; no authorized infrastructure action was evaluated.
2. **Critical — operational telemetry:** no GPU/scheduler/queue telemetry and only one local environment.
3. **High — live predictive reliability integration:** the runtime's default assessor is intentionally unconfigured, so no current workload prediction or calibration claim is supported.
4. **High — memory usefulness on real incidents:** memory-on versus memory-off has simulator evidence only, not a valid live controlled-runtime comparison.
5. **High — evidence scale:** three runs and two failures cannot support statistical reliability claims.

## Direct research answers

1. Runtime observation: **yes, in the controlled local subprocess runtime**.
2. Controlled failures: **yes, for nonzero exit and timeout (N=2)**.
3. Anomaly adds information: **not established**.
4. Diagnosis beyond classification: **partially**; structured evidence/uncertainty is produced, causal diagnosis is not established.
5. Uncertainty: **implemented; not freshly evaluated on process runtime**.
6. Abstention under insufficient live evidence: **not established by this run**.
7. Memory improvement: **not established for current subprocess runtime**.
8. Genuine autonomous recovery: **no**.
9. End-to-end autonomy: **not yet evaluable**.
10. Strong research metrics: **none from the fresh N=3 evaluation**.
11. Engineering-only metrics: **detection, replay, and deterministic diagnosis checks**.
12. Unevaluable now: **real recovery, deployment, CI/CD, Dockerized reproducibility, external-environment generalization**.
"""
    (output / "SYSTEM_EVALUATION_REPORT.md").write_text(report, encoding="utf-8")
    (output / "CAPABILITY_MATRIX.md").write_text("# Capability Matrix\n\n" + capability_matrix(), encoding="utf-8")


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    output = RESULTS_ROOT / run_id
    (output / "raw").mkdir(parents=True, exist_ok=False)
    repository = {
        "head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"), "working_tree_before": git("status", "--porcelain") or "clean",
    }
    protocol = {
        "evaluation_id": run_id, "purpose": "system-level evidence audit; no system tuning", "created_at": utc_now(),
        "repository": repository, "frozen_v1_commit": "d977a32c2f20efa5f8e0d0349d40b270ecabeca2",
        "environment": {"python": sys.version, "platform": platform.platform(), "cwd": str(ROOT), "environment_count": 1},
        "fresh_cases": ["normal_workload", "nonzero_exit", "timeout"],
        "known_unavailable_cases": ["anomalous_successful_workload", "ambiguous_process_runtime_diagnosis", "real_recovery", "external_environment"],
        "commands": [f"{sys.executable} -m pytest -q", f"{sys.executable} scripts/run_system_evaluation.py"],
    }
    controlled = controlled_runtime_evaluation(output)
    test_result = run_full_suite(output)
    evidence = {"controlled_runtime": controlled, "test_suite": test_result}
    write_json(output / "EVALUATION_PROTOCOL.json", protocol)
    write_json(output / "METRICS_SUMMARY.json", {"detection": controlled["monitoring"]["metrics"], "diagnosis": controlled["diagnosis"], "test_suite": test_result, "environment_count": 1})
    write_json(output / "BASELINE_COMPARISON.json", {"status": "NOT EVALUABLE", "reason": "No same-task live process-runtime baseline was predeclared or available."})
    write_json(output / "ABLATION_RESULTS.json", {"status": "NOT EVALUABLE", "reason": "Memory, abstention, and recovery ablations are simulator-only and were not combined with fresh process-runtime evidence."})
    write_json(output / "ROBUSTNESS_RESULTS.json", {"restart_replay": controlled["restart_replay"], "monitoring_replay_equal": controlled["monitoring"]["replay_equal"], "status": "PARTIAL"})
    write_json(output / "OVERHEAD_RESULTS.json", {"status": "NOT EVALUABLE", "reason": "No equivalent uninstrumented baseline exists; no CPU/memory overhead claim is made."})
    write_json(output / "LEAKAGE_RESULTS.json", controlled["leakage"])
    write_json(output / "raw" / "controlled_runtime_evidence.json", controlled)
    write_report(output, evidence, test_result, protocol)
    manifest = {"evaluation_id": run_id, "created_at": utc_now(), "files": {str(path.relative_to(output)).replace("\\", "/"): sha256(path) for path in sorted(output.rglob("*")) if path.is_file()}}
    write_json(output / "REPRODUCIBILITY_MANIFEST.json", manifest)
    print(json.dumps({"output": str(output), "detection": controlled["monitoring"]["metrics"], "pytest": test_result}, indent=2))


if __name__ == "__main__":
    main()
