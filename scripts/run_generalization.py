"""Run the versioned generalization experiment without touching frozen results."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from statistics import mean

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.runtime.builder import build_runtime_system
from src.runtime.components import RuleBasedRecoveryPlanner, SimulatedRecoveryExecutor

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "configs/runtime_demo/generalization_protocol.json").read_text())
RESULTS = ROOT / "experiments/results/generalization"


def make_event(spec, failure_type):
    context = dict(PROTOCOL["failure_types"][failure_type]["train_context"])
    action = spec["action"]
    status = spec["validation_status"]
    return ReliabilityEvent(
        event_id=f"generalization-{spec['id']}",
        workload_id=f"generalization-{failure_type}",
        source=EventSource.BENCHMARK,
        context=context,
        confidence=float(spec["confidence"]),
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.CORRECT if status == "RECOVERED" else Outcome.INCORRECT,
        metadata={
            "experience_id": spec["id"],
            "failure_class": failure_type,
            "recovery_action": action,
            "validation_status": status,
            "source_type": "fixed_training_experience",
        },
    )


def training_events_for(failure_types):
    return [make_event(spec, failure_type) for spec in PROTOCOL["training_experiences"] for failure_type in [spec["failure_type"]] if failure_type in failure_types]


def build_condition(condition, failure_type, seed, mode="related"):
    failure_spec = PROTOCOL["failure_types"][failure_type]
    context = failure_spec["train_context"] if mode == "exact" else failure_spec["evaluation_context"]
    memory_types = {failure_type}
    training = training_events_for(memory_types)
    environment = {"failure_class": failure_type}
    default_action = "retry"
    if condition == "C0_no_memory":
        training = []
    elif condition == "C2_irrelevant_memory":
        distant = next(name for name in PROTOCOL["failure_types"] if name != failure_type)
        training = training_events_for({distant})
    elif condition == "C3_conflicting_memory":
        training = [
            make_event({"id": "conflict-retry", "action": "retry", "validation_status": "RECOVERED", "confidence": 0.8}, failure_type),
            make_event({"id": "conflict-reconfigure", "action": "reconfigure", "validation_status": "RECOVERED", "confidence": 0.8}, failure_type),
        ]
    elif condition == "C4_negative_experience":
        training = [make_event({"id": "negative-retry", "action": "retry", "validation_status": "FAILED", "confidence": 0.5}, failure_type)]
    elif condition == "C5_safety_conflict":
        training = [make_event({"id": "unsafe-reconfigure", "action": "reconfigure", "validation_status": "RECOVERED", "confidence": 0.5}, failure_type)]
        environment["unsafe_actions"] = ["reconfigure"]
    elif condition == "C6_multi_step":
        training = []
        default_action = "retry"
    elif condition in {"C1_relevant_memory", "C7_full_closed_loop"}:
        training = training_events_for({failure_type})

    executor = SimulatedRecoveryExecutor(
        outcome_probabilities=PROTOCOL["action_outcome_probabilities"],
        seed=seed,
        simulator_version=PROTOCOL["simulator_version"],
    )
    system = build_runtime_system(
        feature_names=PROTOCOL["feature_names"],
        planner=RuleBasedRecoveryPlanner(default_action=default_action, abstain_on_conflict=True),
        executor=executor,
        max_attempts=PROTOCOL["max_recovery_attempts"],
        relevance_threshold=PROTOCOL["relevance_threshold"],
    )
    if training:
        system.failure_memory.seed_events(training)
    observation = system.normalizer.normalize({
        "observation_id": f"{condition}-{failure_type}-{mode}-{seed}",
        "workload_id": "generalization-workload",
        "features": context,
        "error": "simulated failure",
        "source": "deterministic_simulator",
        "environment": environment,
        "metadata": {"failure_class": failure_type, "match_mode": mode, "condition": condition, "seed": seed},
        "provenance": {"source_type": "deterministic_simulator", "simulator_version": PROTOCOL["simulator_version"], "seed": seed},
    })
    return system, observation


def record(episode, condition, failure_type, seed, mode):
    matches = list(episode.retrieved_experiences)
    relevant = [item for item in matches if bool(getattr(item, "relevant", False))]
    true_class = failure_type
    retrieved_classes = [getattr(getattr(item, "event", None), "metadata", {}).get("failure_class") for item in matches]
    relevant_classes = [getattr(getattr(item, "event", None), "metadata", {}).get("failure_class") for item in relevant]
    return {
        "condition": condition,
        "failure_type": failure_type,
        "seed": seed,
        "match_mode": mode,
        "state": episode.state.value,
        "retrieval_count": len(matches),
        "relevant_retrieval_count": len(relevant),
        "retrieval_similarities": [getattr(item, "similarity", None) for item in matches],
        "retrieved_failure_classes": retrieved_classes,
        "relevant_failure_classes": relevant_classes,
        "relevance_precision": (sum(value == true_class for value in relevant_classes) / len(relevant_classes)) if relevant_classes else None,
        "relevance_recall": float(bool(relevant_classes and true_class in relevant_classes)),
        "diagnosis_confidence": episode.diagnosis.confidence if episode.diagnosis else None,
        "diagnosis_uncertainty": episode.diagnosis.uncertainty if episode.diagnosis else None,
        "selected_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
        "candidate_actions": [action.value for action in episode.recovery_plan.candidate_actions] if episode.recovery_plan else [],
        "abstained": bool(episode.recovery_plan and episode.recovery_plan.abstained),
        "safety_status": episode.recovery_plan.safety_status if episode.recovery_plan else None,
        "action_history": [action.value for action in episode.action_history],
        "validation_history": [validation.status for validation in episode.validations],
        "recovery_success": bool(episode.validation and episode.validation.recovered is True),
        "recovery_attempts": len(episode.executions),
        "unsafe_action": bool(episode.recovery_plan and episode.recovery_plan.selected_action.value in episode.observation.environment.get("unsafe_actions", [])),
        "memory_version_before": episode.memory_version_before,
        "memory_version_after": episode.memory_version_after,
    }


def run(condition, mode="related"):
    records = []
    for seed in PROTOCOL["seed_list"]:
        for failure_type in PROTOCOL["failure_types"]:
            condition_mode = "exact" if condition in {"C3_conflicting_memory", "C4_negative_experience", "C5_safety_conflict"} else mode
            system, observation = build_condition(condition, failure_type, seed, condition_mode)
            episode = system.controller.process(observation)
            records.append(record(episode, condition, failure_type, seed, condition_mode))
    return records


def summarize(records):
    return {
        "episode_count": len(records),
        "mean_retrieval_count": mean(row["retrieval_count"] for row in records),
        "mean_relevant_retrieval_count": mean(row["relevant_retrieval_count"] for row in records),
        "mean_relevance_precision": mean(row["relevance_precision"] for row in records if row["relevance_precision"] is not None) if any(row["relevance_precision"] is not None for row in records) else None,
        "precision_defined_rate": mean(float(row["relevance_precision"] is not None) for row in records),
        "mean_relevance_recall": mean(row["relevance_recall"] for row in records),
        "mean_diagnosis_confidence": mean(row["diagnosis_confidence"] for row in records),
        "mean_diagnosis_uncertainty": mean(row["diagnosis_uncertainty"] for row in records),
        "action_counts": dict(Counter(row["selected_action"] for row in records)),
        "abstention_rate": mean(float(row["abstained"]) for row in records),
        "unsafe_action_rate": mean(float(row["unsafe_action"]) for row in records),
        "recovery_success_rate": mean(float(row["recovery_success"]) for row in records),
        "mean_recovery_attempts": mean(row["recovery_attempts"] for row in records),
        "multi_step_rate": mean(float(len(row["action_history"]) > 1) for row in records),
        "failed_first_attempt_rate": mean(float(len(row["validation_history"]) > 0 and row["validation_history"][0] == "FAILED") for row in records),
    }


def main():
    conditions = list(PROTOCOL["conditions"])
    all_records = {condition: run(condition) for condition in conditions}
    exact_records = run("C1_relevant_memory", mode="exact")
    related_records = all_records["C1_relevant_memory"]
    summaries = {condition: summarize(records) for condition, records in all_records.items()}
    summaries["C1_exact_memory"] = summarize(exact_records)
    summaries["C1_related_memory"] = summarize(related_records)
    comparison = {
        "retrieval_effect": {"related_relevant_count": summaries["C1_related_memory"]["mean_relevant_retrieval_count"], "irrelevant_relevant_count": summaries["C2_irrelevant_memory"]["mean_relevant_retrieval_count"]},
        "decision_effect": {"no_memory_action_counts": summaries["C0_no_memory"]["action_counts"], "related_action_counts": summaries["C1_related_memory"]["action_counts"], "conflict_action_counts": summaries["C3_conflicting_memory"]["action_counts"]},
        "performance_effect": {"no_memory_success": summaries["C0_no_memory"]["recovery_success_rate"], "related_success": summaries["C1_related_memory"]["recovery_success_rate"], "multi_step_success": summaries["C6_multi_step"]["recovery_success_rate"]},
        "safety_effect": {"safety_conflict_abstention": summaries["C5_safety_conflict"]["abstention_rate"], "safety_conflict_unsafe_action_rate": summaries["C5_safety_conflict"]["unsafe_action_rate"], "ambiguous_abstention": summaries["C3_conflicting_memory"]["abstention_rate"]},
        "generalization": {"exact_success": summaries["C1_exact_memory"]["recovery_success_rate"], "related_success": summaries["C1_related_memory"]["recovery_success_rate"], "related_minus_exact": summaries["C1_related_memory"]["recovery_success_rate"] - summaries["C1_exact_memory"]["recovery_success_rate"]},
        "negative_experience_avoidance": {"negative_action_counts": summaries["C4_negative_experience"]["action_counts"], "default_no_memory_action_counts": summaries["C0_no_memory"]["action_counts"]},
    }
    manifest = {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": hashlib.sha256((ROOT / "configs/runtime_demo/generalization_protocol.json").read_bytes()).hexdigest(),
        "seed_list": PROTOCOL["seed_list"],
        "simulator_version": PROTOCOL["simulator_version"],
        "original_learning_influence_untouched": True,
        "evaluation_outcomes_seeded_before_decision": False,
        "statistical_claim": "not made; results are multi-seed descriptive controlled evaluation",
    }
    result = {"protocol": PROTOCOL, "summaries": summaries, "comparison": comparison, "manifest": manifest, "records": all_records, "exact_records": exact_records}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "generalization_results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (RESULTS / "summary.json").write_text(json.dumps({"summaries": summaries, "comparison": comparison}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summaries": summaries, "comparison": comparison, "manifest": manifest}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
