"""Run the new learning-influence experiment on the repaired runtime.

This is a new experiment. It does not modify or reinterpret frozen Phase 4
results. The control and learned conditions are rebuilt independently for each
evaluation episode so evaluation outcomes cannot leak into future conditions.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from src.failure_memory.memory import FailureMemory
from src.runtime.builder import build_runtime_system
from src.runtime.components import RuleBasedRecoveryPlanner, SimulatedRecoveryExecutor

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "configs/runtime_demo/learning_influence_protocol.json"
RESULTS_DIR = ROOT / "experiments/results/learning_influence"


def _observation(system, episode_id: str):
    return system.normalizer.normalize({
        "observation_id": episode_id,
        "workload_id": "learning-influence-workload",
        "features": {"f1": 0.2},
        "error": "simulated execution error",
        "source": "deterministic_simulator",
        "provenance": {"scenario": "execution_error_recovery_choice", "split": "evaluation"},
    })


def _system(default_action, outcome_by_action):
    return build_runtime_system(
        feature_names=["f1"],
        planner=RuleBasedRecoveryPlanner(default_action=default_action),
        executor=SimulatedRecoveryExecutor(outcome_by_action=outcome_by_action),
    )


def _episode_record(episode):
    relevant = [item for item in episode.retrieved_experiences if getattr(item, "relevant", False)]
    return {
        "state": episode.state.value,
        "retrieval_count": len(episode.retrieved_experiences),
        "relevant_retrieval_count": len(relevant),
        "retrieval_similarities": [getattr(item, "similarity", None) for item in episode.retrieved_experiences],
        "risk": episode.reliability.risk if episode.reliability else None,
        "diagnosis_confidence": episode.diagnosis.confidence if episode.diagnosis else None,
        "diagnosis_uncertainty": episode.diagnosis.uncertainty if episode.diagnosis else None,
        "diagnosis_evidence": list(episode.diagnosis.evidence) if episode.diagnosis else [],
        "selected_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
        "candidate_actions": [action.value for action in episode.recovery_plan.candidate_actions] if episode.recovery_plan else [],
        "safety_status": episode.recovery_plan.safety_status if episode.recovery_plan else None,
        "abstained": bool(episode.recovery_plan and episode.recovery_plan.abstained),
        "recovery_attempts": episode.execution.attempt if episode.execution else 0,
        "validation_status": episode.validation.status if episode.validation else None,
        "recovery_success": episode.validation.recovered if episode.validation else None,
        "memory_version_before": (episode.learning_update or {}).get("memory_version_before"),
        "memory_version_after": (episode.learning_update or {}).get("memory_version_after"),
    }


def run_condition(name: str, training_events, count: int, action, outcomes):
    records = []
    for index in range(count):
        system = _system(action, outcomes)
        if training_events:
            system.failure_memory.seed_events(list(training_events))
        episode = system.controller.process(_observation(system, f"{name}-episode-{index:03d}"))
        records.append(_episode_record(episode))
    return {"condition": name, "episode_count": count, "episodes": records}


def summarize(condition):
    episodes = condition["episodes"]
    return {
        "condition": condition["condition"],
        "episode_count": len(episodes),
        "mean_risk": mean(record["risk"] for record in episodes),
        "mean_diagnosis_confidence": mean(record["diagnosis_confidence"] for record in episodes),
        "mean_diagnosis_uncertainty": mean(record["diagnosis_uncertainty"] for record in episodes),
        "mean_retrieval_count": mean(record["retrieval_count"] for record in episodes),
        "mean_relevant_retrieval_count": mean(record["relevant_retrieval_count"] for record in episodes),
        "action_counts": {action: sum(record["selected_action"] == action for record in episodes) for action in sorted({record["selected_action"] for record in episodes})},
        "abstention_rate": mean(float(record["abstained"]) for record in episodes),
        "mean_recovery_attempts": mean(record["recovery_attempts"] for record in episodes),
        "validation_success_rate": mean(float(record["validation_status"] == "RECOVERED") for record in episodes),
        "recovery_success_rate": mean(float(record["recovery_success"] is True) for record in episodes),
        "safety_violation_count": sum(record["safety_status"] not in (None, "approved") for record in episodes),
    }


def main() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text())
    training_system = _system("reconfigure", {"retry": False, "reconfigure": True})
    training_episode = training_system.controller.process(_observation(training_system, "training-episode-000"))
    training_events = training_system.failure_memory.failure_events
    if not training_events:
        raise RuntimeError("training episode did not produce a failure-memory event")

    control = run_condition("control", (), protocol["evaluation_episode_count"], "retry", protocol["simulated_outcomes"])
    learned = run_condition("learned", training_events, protocol["evaluation_episode_count"], "retry", protocol["simulated_outcomes"])
    control_summary = summarize(control)
    learned_summary = summarize(learned)
    comparison = {
        "experiment": protocol["protocol_version"],
        "baseline_matrix": {
            "B0_reliability_only": {"status": "not_run", "reason": "No explicit workload model artifact is configured; the safe default abstainer is not treated as a model baseline."},
            "B1_model_plus_calibration": {"status": "not_run", "reason": "No explicit workload model and calibrator artifacts were injected."},
            "B2_model_plus_memory": {"status": "measured", "control": "empty memory", "learned": "one declared training experience", "metrics": ["retrieval_count", "relevant_retrieval_count", "risk"]},
            "B3_model_memory_diagnosis": {"status": "measured", "metrics": ["diagnosis_confidence", "diagnosis_uncertainty", "diagnosis_evidence"]},
            "B4_model_memory_diagnosis_recovery": {"status": "measured", "metrics": ["candidate_actions", "selected_action", "safety_status", "recovery_attempts"]},
            "B5_complete_closed_loop": {"status": "measured", "metrics": ["validation_success_rate", "recovery_success_rate", "safety_violation_count"]}
        },
        "control": control_summary,
        "learned": learned_summary,
        "learning_influence": {
            "retrieval_count_delta": learned_summary["mean_retrieval_count"] - control_summary["mean_retrieval_count"],
            "relevant_retrieval_count_delta": learned_summary["mean_relevant_retrieval_count"] - control_summary["mean_relevant_retrieval_count"],
            "risk_delta": learned_summary["mean_risk"] - control_summary["mean_risk"],
            "diagnosis_confidence_delta": learned_summary["mean_diagnosis_confidence"] - control_summary["mean_diagnosis_confidence"],
            "diagnosis_uncertainty_delta": learned_summary["mean_diagnosis_uncertainty"] - control_summary["mean_diagnosis_uncertainty"],
            "action_change_rate": mean(float(l["selected_action"] != c["selected_action"]) for c, l in zip(control["episodes"], learned["episodes"])),
            "abstention_rate_delta": learned_summary["abstention_rate"] - control_summary["abstention_rate"],
        },
        "learning_benefit": {
            "validation_success_rate_delta": learned_summary["validation_success_rate"] - control_summary["validation_success_rate"],
            "recovery_success_rate_delta": learned_summary["recovery_success_rate"] - control_summary["recovery_success_rate"],
            "safety_violation_delta": learned_summary["safety_violation_count"] - control_summary["safety_violation_count"],
        },
        "interpretation": "Influence and benefit are reported separately. This deterministic repeated scenario is an integration experiment, not a statistical generalization claim.",
    }
    manifest = {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
        "historical_paths_modified": False,
        "training_episode_id": "training-episode-000",
        "control_memory": "empty per evaluation episode",
        "learned_memory": "training episode only per evaluation episode",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for name, value in (("protocol", protocol), ("control", control), ("learned", learned), ("comparison", comparison), ("summary", {"control": control_summary, "learned": learned_summary, "comparison": comparison}), ("manifest", manifest)):
        (RESULTS_DIR / f"{name}.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"control": control_summary, "learned": learned_summary, "comparison": comparison}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
