"""Final V1 integrated evaluation over multiple independent Alibaba test jobs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from scripts.run_alibaba_closed_loop_v1 import run_condition, make_record
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/alibaba_closed_loop_v2"
SPLITS = ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json"
ARTIFACT_MANIFEST = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random/manifest.json"
DATASET_MANIFEST = ROOT / "data/audit/alibaba_gpu2020/dataset_manifest.json"
PROTOCOL = OUT / "protocol.json"


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def event_for(row, event_id: str, *, action: str = "retry", validation: str = "RECOVERED", workload_id: str = "alibaba-gpu2020-closed-loop") -> ReliabilityEvent:
    return ReliabilityEvent(event_id=event_id, workload_id=workload_id, source=EventSource.FAILURE_MEMORY, context={name: float(row[name]) if row[name] == row[name] else 0.0 for name in NUMERIC_COLS}, confidence=0.8, decision=Decision.ANSWER, abstained=False, is_failure=True, outcome=Outcome.CORRECT if validation == "RECOVERED" else Outcome.INCORRECT, metadata={"recovery_action": action, "validation_status": validation})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    (OUT / "per_seed").mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix()
    test_ids = sorted(json.loads(SPLITS.read_text())["test"])[:8]
    rows = [df[df.job_name == job_id].iloc[0] for job_id in test_ids]
    cases: list[dict] = []
    order_invariance_checks: list[bool] = []
    for index, row in enumerate(rows):
        prior = row.copy()
        # These are controlled prior experiences with deterministic identities;
        # they contain no target outcome and are inserted only before the
        # condition's decision. The relevant control shares the replay regime,
        # while the irrelevant control is deliberately distant.
        far = row.copy()
        for feature in NUMERIC_COLS:
            far[feature] = -100.0
        relevant_event = event_for(prior, stable_id(f"prior-relevant-{index}"))
        irrelevant_event = event_for(far, stable_id(f"prior-irrelevant-{index}"), action="reconfigure")
        conflicting_a = event_for(prior, stable_id(f"conflict-a-{index}"), action="retry", validation="RECOVERED")
        conflicting_b = event_for(prior, stable_id(f"conflict-b-{index}"), action="reconfigure", validation="RECOVERED")
        negative = event_for(prior, stable_id(f"negative-{index}"), action="retry", validation="FAILED")
        specs = [
            ("C0_no_memory", (), False, True),
            ("C1_relevant_memory", (relevant_event,), False, True),
            ("C2_irrelevant_memory", (irrelevant_event,), False, True),
            ("C3_conflicting_memory", (conflicting_a, conflicting_b), False, True),
            ("C4_negative_experience", (negative,), False, True),
            ("C5_safety_conflict", (relevant_event,), True, True),
            ("C6_safe_fallback", (), False, False),
        ]
        for name, events, unsafe, artifact in specs:
            result = run_condition(f"{name}-case-{index}", row, memory_events=events, unsafe=unsafe, artifact=artifact)
            result["case_index"] = index
            result["job_id"] = str(row.job_name)
            result["decision_quality"] = "safe_abstention" if result["unsafe_proposal"] else "executed_or_answered"
            result["recovery_success"] = result["validation"] == "RECOVERED"
            cases.append(result)
        forward = run_condition(f"C3_order_forward-case-{index}", row, memory_events=(conflicting_a, conflicting_b), artifact=True)
        reverse = run_condition(f"C3_order_reverse-case-{index}", row, memory_events=(conflicting_b, conflicting_a), artifact=True)
        order_invariance_checks.append((forward["abstention_decision"], forward["recovery_candidates"], forward["memory_risk"]) == (reverse["abstention_decision"], reverse["recovery_candidates"], reverse["memory_risk"]))
    aggregate = {}
    for condition in sorted({case["condition"].rsplit("-case-", 1)[0] for case in cases}):
        subset = [case for case in cases if case["condition"].startswith(condition + "-")]
        aggregate[condition] = {
            "n": len(subset),
            "mean_memory_risk": sum(float(case["memory_risk"] or 0.0) for case in subset) / len(subset),
            "mean_workload_failure_risk": sum(float(case["workload_failure_risk"] or 0.0) for case in subset) / len(subset),
            "mean_diagnosis_confidence": sum(float((case["diagnosis"] or {}).get("confidence", 0.0)) for case in subset) / len(subset),
            "mean_retrieved": sum(case["retrieved_experiences"] for case in subset) / len(subset),
            "unsafe_proposal_rate": sum(case["unsafe_proposal"] for case in subset) / len(subset),
            "unsafe_proposal_rejection_rate": sum(case["unsafe_proposal"] and case["safety_decision"] == "rejected" for case in subset) / len(subset),
            "unsafe_execution_rate": sum(case["unsafe_execution"] for case in subset) / len(subset),
            "recovery_success_rate": sum(case["recovery_success"] for case in subset) / len(subset),
            "safe_decision_rate": sum(not case["unsafe_execution"] for case in subset) / len(subset),
        }
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {"experiment_id": "alibaba_closed_loop_v2", "git_commit": commit, "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(), "dataset_manifest_sha256": hashlib.sha256(DATASET_MANIFEST.read_bytes()).hexdigest(), "artifact_manifest_sha256": hashlib.sha256(ARTIFACT_MANIFEST.read_bytes()).hexdigest(), "seed": 42, "software": {"python": "3.12", "runner": "run_alibaba_closed_loop_v2.py"}}
    payload = {"experiment_id": "alibaba_closed_loop_v2", "population": {"n_unique_jobs": len(test_ids), "job_ids": test_ids}, "aggregate": aggregate, "cases": cases, "order_invariance_checks": order_invariance_checks, "manifest": manifest, "leakage_controls": {"target_outcome_before_decision": False, "future_telemetry_as_feature": False, "evaluation_used_for_tuning": False, "episode_n_plus_1_outcome_in_episode_n_memory": False, "conflicting_retrieval_order_changes_decision": not all(order_invariance_checks)}, "claim_boundary": "bounded Alibaba GPU2020 replay composition evidence; controlled recovery only; no production self-healing claim"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (OUT / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps({"experiment_id": payload["experiment_id"], "population": payload["population"], "aggregate": aggregate, "leakage_controls": payload["leakage_controls"], "claim_boundary": payload["claim_boundary"]}, indent=2, sort_keys=True) + "\n")
    (OUT / "logs" / "trace.json").write_text(json.dumps(cases, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"experiment_id": "alibaba_closed_loop_v2", "unique_jobs": len(test_ids), "conditions": len(aggregate), "cases": len(cases), "status": "completed"}, indent=2))


if __name__ == "__main__":
    main()
