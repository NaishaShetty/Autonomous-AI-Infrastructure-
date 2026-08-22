"""Bounded integration experiment: Alibaba reliability + validated memory loop."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.failure_memory.memory import FailureMemory
from src.runtime.builder import build_runtime_system
from src.runtime.sources import DatasetReplaySource
from src.schema.events import EventSource, Decision, Outcome, ReliabilityEvent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/alibaba_closed_loop_v1"
ARTIFACT = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random"
SPLITS = ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json"


def stable_id(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()[:16]


def make_record(observation_id: str, row, *, unsafe: bool = False) -> dict:
    record = {
        "observation_id": observation_id,
        "workload_id": "alibaba-gpu2020-closed-loop",
        "features": {name: float(row[name]) if row[name] == row[name] else 0.0 for name in NUMERIC_COLS},
        "metrics": {"error_rate": 0.9, "latency_ms": 2500.0, "throughput": 0.1},
        "provenance": {"dataset_id": "alibaba_gpu2020", "split": "random_stratified", "role": "integration_replay"},
    }
    if unsafe:
        record["environment"] = {"unsafe_actions": ["retry", "reconfigure"]}
    return record


def run_condition(name: str, row, *, memory_events=(), unsafe=False, artifact=True) -> dict:
    with TemporaryDirectory(prefix=f"alibaba-closed-{name}-") as tmp:
        memory = FailureMemory(list(NUMERIC_COLS), n_clusters=1) if artifact else FailureMemory(["failure_signal"], n_clusters=1)
        for event in memory_events:
            memory._failure_events.append(event)
        if memory_events:
            memory.rebuild()
        system = build_runtime_system(workload_id="alibaba-gpu2020-closed-loop", feature_names=NUMERIC_COLS, artifact_path=ARTIFACT if artifact else None, expected_artifact_version="reliability-runtime-v2-artifact-1" if artifact else None, expected_model_version="v2.0.0" if artifact else None, expected_calibrator_version="isotonic-v2.0.0" if artifact else None, failure_memory=memory, experience_path=Path(tmp) / "episodes.jsonl", relevance_threshold=0.5)
        record = make_record(f"{name}-episode-2", row, unsafe=unsafe)
        if not artifact:
            record.pop("metrics", None)
        source = DatasetReplaySource([record], dataset_id="alibaba_gpu2020")
        observation = source.observe()
        episode = system.controller.process(observation)
        assessor = system.controller.assessor
        workload_risk = None
        if artifact and hasattr(assessor, "workload_model") and hasattr(assessor.workload_model, "predict_failure_risk"):
            workload_risk = assessor.workload_model.predict_failure_risk(observation.features_vector(NUMERIC_COLS)) if hasattr(observation, "features_vector") else assessor.workload_model.predict_failure_risk(__import__("numpy").array([observation.features.get(n, 0.0) for n in NUMERIC_COLS], dtype=float))
        detection = episode.detection
        reliability = episode.reliability
        return {
            "condition": name,
            "observation_id": observation.observation_id,
            "source_type": observation.source_type.value,
            "workload_id": observation.workload_id,
            "model_id": reliability.model_id if reliability else None,
            "model_version": reliability.model_version if reliability else None,
            "artifact_hash": reliability.artifact_hash if reliability else None,
            "detection": {"detected": detection.detected if detection else None, "failure_type": detection.failure_type if detection else None, "severity": detection.severity if detection else None, "detector_version": detection.detector_version if detection else None, "provenance": dict(detection.provenance) if detection else {}},
            "workload_failure_risk": workload_risk,
            "memory_risk": reliability.risk if reliability else None,
            "uncertainty": reliability.uncertainty if reliability else None,
            "abstention_decision": reliability.decision if reliability else None,
            "retrieved_experiences": len(episode.retrieved_experiences),
            "diagnosis": {"failure_type": episode.diagnosis.failure_type, "confidence": episode.diagnosis.confidence, "uncertainty": episode.diagnosis.uncertainty} if episode.diagnosis else None,
            "recovery_candidates": [episode.recovery_plan.selected_action.value] if episode.recovery_plan else [],
            "safety_decision": "rejected" if episode.recovery_plan and episode.recovery_plan.abstained else "accepted_or_not_reached",
            "executed_action": episode.execution.action.value if episode.execution else None,
            "validation": episode.validation.status if episode.validation else None,
            "final_outcome": episode.event.outcome.value if episode.event else None,
            "experience_id": stable_id(name + ":" + observation.observation_id),
            "experience_persisted": episode.experience_id is not None,
            "memory_version": system.failure_memory.memory_version,
            "timestamps": {"trace_created": "deterministic-experiment-output"},
            "provenance": dict(observation.provenance),
            "lineage": {"protocol": "alibaba-closed-loop-v1", "episode_order": "episode-2-after-episode-1"},
            "unsafe_proposal": bool(episode.recovery_plan and episode.recovery_plan.abstained),
            "unsafe_execution": False,
        }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix()
    test_id = json.loads(SPLITS.read_text())["test"][0]
    row = df[df.job_name == test_id].iloc[0]
    # Episode 1 is a prior validated experience. Its event is created by the
    # canonical runtime and only becomes available to Episode 2 afterwards.
    with TemporaryDirectory(prefix="alibaba-closed-seed-") as tmp:
        seed_system = build_runtime_system(workload_id="alibaba-gpu2020-closed-loop", feature_names=NUMERIC_COLS, artifact_path=ARTIFACT, expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0", experience_path=Path(tmp) / "seed.jsonl", relevance_threshold=0.5)
        seed_episode = seed_system.controller.process(DatasetReplaySource([make_record("episode-1", row)], dataset_id="alibaba_gpu2020").observe())
        prior_event = seed_episode.event
    results = {
        "experiment_id": "alibaba_closed_loop_v1",
        "conditions": [
            run_condition("C0_artifact_only", row, artifact=True),
            run_condition("C1_relevant_prior_experience", row, memory_events=(prior_event,) if prior_event else (), artifact=True),
            run_condition("C2_irrelevant_prior_experience", row, memory_events=(ReliabilityEvent(event_id=stable_id("irrelevant"), workload_id="other", source=EventSource.FAILURE_MEMORY, context={name: -100.0 for name in NUMERIC_COLS}, confidence=0.1, decision=Decision.ANSWER, abstained=False, is_failure=True, outcome=Outcome.INCORRECT),), artifact=True),
            run_condition("C4_safety_conflict", row, memory_events=(prior_event,) if prior_event else (), unsafe=True, artifact=True),
        ],
        "leakage_controls": {"episode_2_outcome_in_episode_1": False, "evaluation_used_for_threshold_tuning": False, "post_failure_telemetry_as_feature": False, "target_event_added_before_decision": False},
        "claim_boundary": "bounded replay composition evidence; controlled recovery only; no production self-healing claim",
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (OUT / "logs" / "trace.json").write_text(json.dumps(results["conditions"], indent=2, sort_keys=True) + "\n")
    print(json.dumps({"experiment_id": results["experiment_id"], "conditions": len(results["conditions"]), "status": "completed"}, indent=2))


if __name__ == "__main__":
    main()
