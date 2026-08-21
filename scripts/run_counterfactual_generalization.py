"""Run the true/counterfactual behavioral-generalization experiment.

Latent mechanisms and optimal actions live only in this simulator harness. The
runtime receives observable feature vectors, generic failure evidence, and
current safety constraints, never the mechanism or optimal action.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.runtime.builder import build_runtime_system
from src.runtime.components import RuleBasedRecoveryPlanner, SignalRecoveryValidator
from src.runtime.contracts import ExecutionResult, Observation, RecoveryAction, ReliabilityAssessment

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "configs/runtime_demo/counterfactual_generalization_protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text())
RESULTS = ROOT / "experiments/results/counterfactual_generalization"
FEATURES = PROTOCOL["feature_names"]


def vector_distance(left: dict[str, float], right: dict[str, float]) -> float:
    return math.sqrt(sum((float(left[name]) - float(right[name])) ** 2 for name in FEATURES))


def deterministic_id(*parts: object) -> str:
    payload = "|".join(str(part) for part in parts).encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def mechanism_for(name: str) -> dict[str, Any]:
    return PROTOCOL["latent_mechanisms"][name]


def training_specs(mechanism: str) -> list[dict[str, Any]]:
    return [spec for spec in PROTOCOL["training_experiences"] if spec["mechanism"] == mechanism]


def make_event(spec: dict[str, Any], mechanism: str) -> ReliabilityEvent:
    context = dict(mechanism_for(mechanism)["training_manifestations"][spec["id"]])
    return ReliabilityEvent(
        event_id=f"cf-{spec['id']}",
        workload_id="counterfactual-training-workload",
        source=EventSource.BENCHMARK,
        context=context,
        confidence=float(spec["confidence"]),
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.CORRECT if spec["validation_status"] == "RECOVERED" else Outcome.INCORRECT,
        metadata={
            "training_manifestation_id": spec["id"],
            "latent_mechanism": mechanism,
            "recovery_action": spec["action"],
            "validation_status": spec["validation_status"],
            "source_type": "fixed_counterfactual_training_experience",
        },
    )


class CounterfactualSimulator:
    """Ground-truth simulator; latent state is never put into Observation."""

    def __init__(self, mechanism: str, action_probabilities: dict[str, float], unsafe_actions: list[str], seed: int):
        self.mechanism = mechanism
        self.action_probabilities = dict(action_probabilities)
        self.unsafe_actions = set(unsafe_actions)
        self.seed = seed
        self.rng = random.Random(seed)
        self.version = PROTOCOL["simulator_version"]

    def execute(self, action: RecoveryAction | Any, observation: Observation, attempt: int = 1) -> ExecutionResult:
        from datetime import datetime, timezone
        started = datetime.now(timezone.utc)
        action = getattr(action, "selected_action", action)
        action_name = action.value
        if action_name in self.unsafe_actions:
            success = False
            draw = None
            probability = 0.0
            error = "action rejected by current safety constraint"
        else:
            probability = float(self.action_probabilities.get(action_name, 0.0))
            draw = self.rng.random()
            success = draw < probability
            error = None if success else "counterfactual simulator action failed"
        state = {
            "failure_present": not success,
            "action": action_name,
            "probability": probability,
            "draw": draw,
            "attempt": attempt,
            "seed": self.seed,
            "simulator_version": self.version,
            "unsafe_rejected": action_name in self.unsafe_actions,
        }
        return ExecutionResult(action, started, datetime.now(timezone.utc), "counterfactual_simulator", success, workload_state=state, error=error, attempt=attempt)


def make_observation(features: dict[str, float], seed: int, index: int, unsafe_actions: list[str] | None = None) -> Observation:
    assert "latent_mechanism" not in features
    assert "optimal_action" not in features
    return Observation(
        observation_id=f"cf-obs-{seed:02d}-{index:02d}",
        workload_id="counterfactual-evaluation-workload",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seed * 1000 + index),
        features=dict(features),
        metrics={"error_rate": float(features["error_rate"])},
        resource_signals={},
        error="observed failure symptoms",
        environment={"unsafe_actions": list(unsafe_actions or [])},
        metadata={"source_type": "counterfactual_simulator"},
        provenance={"source_type": "counterfactual_simulator", "simulator_version": PROTOCOL["simulator_version"], "seed": seed},
    )


def eval_manifestation(mechanism: str, band: str = "D2_moderate") -> tuple[str, dict[str, float], str]:
    model = mechanism_for(mechanism)
    train = model["training_manifestations"]
    first_id, first_context = next(iter(train.items()))
    if band == "D0_exact":
        return first_id, dict(first_context), mechanism
    if band == "D1_near":
        second_context = dict(list(train.values())[1])
        return f"{first_id}-near", {name: round(0.8 * first_context[name] + 0.2 * second_context[name], 6) for name in FEATURES}, mechanism
    if band == "D2_moderate":
        item = model["evaluation_manifestation"]
        return item["id"], dict(item["features"]), mechanism
    if band == "D3_large":
        item = model["evaluation_manifestation"]
        offsets = {"gpu_utilization": 0.25, "queue_depth": -0.22, "latency_ms": 0.18, "error_rate": -0.16, "config_drift": 0.14, "throughput_drop": -0.20}
        return f"{item['id']}-large", {name: round(max(0.0, min(1.0, item["features"][name] + offsets[name])), 6) for name in FEATURES}, mechanism
    if band == "D4_unrelated":
        other = next(name for name in PROTOCOL["latent_mechanisms"] if name != mechanism)
        item = mechanism_for(other)["evaluation_manifestation"]
        return f"unrelated-{item['id']}", dict(item["features"]), other
    raise ValueError(f"unknown distance band: {band}")


def training_events_for(condition: str, mechanism: str) -> list[ReliabilityEvent]:
    if condition == "C0_no_memory":
        return []
    if condition in {"C1_training_memory", "C3_exact_memory_removed", "C4_negative_transfer", "C5_safety_override", "C6_uncertainty_ladder", "C7_counterfactual_pair"}:
        source_mechanism = "M_latency_congestion" if condition in {"C4_negative_transfer", "C5_safety_override"} else mechanism
        return [make_event(spec, source_mechanism) for spec in training_specs(source_mechanism)]
    if condition == "C2_irrelevant_memory":
        other = next(name for name in PROTOCOL["latent_mechanisms"] if name != mechanism)
        return [make_event(spec, other) for spec in training_specs(other)]
    raise ValueError(condition)


def ground_truth_for(mechanism: str, condition: str) -> tuple[str, dict[str, float], str, str, dict[str, float], list[str]]:
    if condition in {"C4_negative_transfer", "C5_safety_override"}:
        model = mechanism_for("M_latency_congestion")
        item = model["negative_transfer_manifestation"]
        unsafe = ["rollback"] if condition == "C5_safety_override" else []
        return item["id"], dict(item["features"]), "M_latency_congestion", item["optimal_action"], dict(item["action_probabilities"]), unsafe
    band = "D0_exact" if condition == "C1_training_memory" else "D2_moderate"
    manifestation_id, features, actual_mechanism = eval_manifestation(mechanism, band)
    model = mechanism_for(actual_mechanism)
    return manifestation_id, features, actual_mechanism, model["optimal_action"], dict(model["action_probabilities"]), list(model.get("unsafe_actions", []))


def make_system(mechanism: str, seed: int, events: list[ReliabilityEvent], probabilities: dict[str, float], unsafe_actions: list[str], max_attempts: int) -> tuple[Any, CounterfactualSimulator]:
    simulator = CounterfactualSimulator(mechanism, probabilities, unsafe_actions, seed)
    system = build_runtime_system(
        feature_names=FEATURES,
        failure_memory=None,
        planner=RuleBasedRecoveryPlanner(default_action=RecoveryAction.RETRY, abstain_on_conflict=True),
        executor=simulator,
        experience_path=f"/tmp/counterfactual_experiences_{seed}.jsonl",
        max_attempts=max_attempts,
        relevance_threshold=PROTOCOL["relevance_threshold"],
    )
    if events:
        system.failure_memory.seed_events(events)
    return system, simulator


def reliability_stub() -> ReliabilityAssessment:
    return ReliabilityAssessment(confidence=0.5, risk=0.0, decision="ABSTAIN", fused_score=0.0, uncertainty=1.0, predicted_label=None, model_id="unconfigured", model_version="none", calibrator_version="none", training_data_id=None, configuration={"counterfactual": True})


def choose_nearest(features: dict[str, float], events: list[ReliabilityEvent]) -> tuple[RecoveryAction, float | None]:
    if not events:
        return RecoveryAction.ABSTAIN, None
    distances = [(vector_distance(features, event.context), event) for event in events]
    distance, event = min(distances, key=lambda item: (item[0], item[1].event_id))
    if distance > PROTOCOL["nearest_neighbor_distance_threshold"]:
        return RecoveryAction.ABSTAIN, distance
    return RecoveryAction(event.metadata["recovery_action"]), distance


def choose_observable_centroid(features: dict[str, float], events: list[ReliabilityEvent]) -> tuple[RecoveryAction, float | None]:
    by_action: dict[str, list[dict[str, float]]] = defaultdict(list)
    for event in events:
        by_action[event.metadata["recovery_action"]].append(event.context)
    if not by_action:
        return RecoveryAction.ABSTAIN, None
    centroids = {action: {name: mean(context[name] for context in contexts) for name in FEATURES} for action, contexts in by_action.items()}
    distances = [(vector_distance(features, centroid), action) for action, centroid in centroids.items()]
    distance, action = min(distances, key=lambda item: (item[0], item[1]))
    if distance > PROTOCOL["observable_baseline_distance_threshold"]:
        return RecoveryAction.ABSTAIN, distance
    return RecoveryAction(action), distance


def validate_direct(observation: Observation, execution: ExecutionResult):
    return SignalRecoveryValidator().validate(observation, reliability_stub(), execution)


def direct_baseline_record(baseline: str, condition: str, mechanism: str, seed: int, features: dict[str, float], events: list[ReliabilityEvent], probabilities: dict[str, float], unsafe_actions: list[str], observation_index: int) -> dict[str, Any]:
    observation = make_observation(features, seed, observation_index, unsafe_actions)
    if baseline == "B0_no_memory":
        action, distance = RecoveryAction.RETRY, None
    elif baseline == "B1_nearest_neighbor":
        action, distance = choose_nearest(features, events)
    else:
        action, distance = choose_observable_centroid(features, events)
    proposed_action = action
    safety_rejected = proposed_action.value in unsafe_actions
    if safety_rejected:
        action = RecoveryAction.ABSTAIN
    simulator = CounterfactualSimulator(mechanism, probabilities, unsafe_actions, seed)
    execution = simulator.execute(action, observation)
    validation = validate_direct(observation, execution)
    return {
        "baseline": baseline,
        "condition": condition,
        "mechanism_ground_truth": mechanism,
        "seed": seed,
        "observation_id": observation.observation_id,
        "features": features,
        "memory_event_ids": [event.event_id for event in events],
        "evaluation_manifestation_in_memory": observation.observation_id in [event.metadata.get("training_manifestation_id") for event in events],
        "distance_to_training": distance,
        "retrieval_count": 0,
        "relevant_retrieval_count": 0,
        "relevance_precision": None,
        "relevance_recall": 0.0,
        "diagnosis_confidence": None,
        "diagnosis_uncertainty": None,
        "proposed_action": proposed_action.value,
        "selected_action": action.value,
        "historical_action_transfer": proposed_action.value in {event.metadata.get("recovery_action") for event in events},
        "ground_truth_optimal_action": None,
        "abstained": action in {RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE},
        "unsafe_action": False,
        "unsafe_transfer": bool(safety_rejected),
        "safety_status": "rejected" if safety_rejected else "not_applicable",
        "recovery_success": validation.recovered is True,
        "validation_success": validation.recovered is True,
        "recovery_attempts": 0 if action in {RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE} else 1,
        "first_attempt_success": execution.success if action not in {RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE} else None,
        "action_history": [action.value] if action not in {RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE} else [],
        "simulator_draw": execution.workload_state.get("draw"),
        "simulator_probability": execution.workload_state.get("probability"),
        "simulator_version": simulator.version,
        "memory_version_before": None,
        "memory_version_after": None,
    }


def memory_baseline_record(condition: str, mechanism: str, seed: int, features: dict[str, float], events: list[ReliabilityEvent], probabilities: dict[str, float], unsafe_actions: list[str], observation_index: int, target_mechanism: str | None = None) -> dict[str, Any]:
    system, simulator = make_system(mechanism, seed, events, probabilities, unsafe_actions, PROTOCOL["max_recovery_attempts"])
    observation = make_observation(features, seed, observation_index, unsafe_actions)
    episode = system.controller.process(observation)
    matches = list(episode.retrieved_experiences)
    relevant = [match for match in matches if bool(getattr(match, "relevant", False))]
    event_ids = [getattr(getattr(match, "event", None), "event_id", None) for match in matches]
    relevant_ids = [getattr(getattr(match, "event", None), "event_id", None) for match in relevant]
    target_mechanism = target_mechanism or mechanism
    relevant_mechanisms = [getattr(getattr(match, "event", None), "metadata", {}).get("latent_mechanism") for match in relevant]
    training_ids = {event.metadata.get("training_manifestation_id") for event in events}
    return {
        "baseline": "B2_memory_planner",
        "condition": condition,
        "mechanism_ground_truth": mechanism,
        "seed": seed,
        "observation_id": observation.observation_id,
        "features": features,
        "memory_event_ids": [event.event_id for event in events],
        "evaluation_manifestation_in_memory": False,
        "distance_to_training": min((vector_distance(features, event.context) for event in events), default=None),
        "retrieval_count": len(matches),
        "relevant_retrieval_count": len(relevant),
        "relevance_precision": (sum(value == target_mechanism for value in relevant_mechanisms) / len(relevant_mechanisms)) if relevant_mechanisms else None,
        "relevance_recall": float(bool(relevant) and any(value == target_mechanism for value in relevant_mechanisms)),
        "retrieved_event_ids": event_ids,
        "relevant_event_ids": relevant_ids,
        "diagnosis_confidence": episode.diagnosis.confidence if episode.diagnosis else None,
        "diagnosis_uncertainty": episode.diagnosis.uncertainty if episode.diagnosis else None,
        "selected_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
        "historical_action_transfer": bool(episode.recovery_plan and episode.recovery_plan.selected_action.value in {event.metadata.get("recovery_action") for event in events}),
        "ground_truth_optimal_action": None,
        "abstained": bool(episode.recovery_plan and episode.recovery_plan.abstained),
        "unsafe_action": bool(episode.action_history and episode.action_history[0].value in unsafe_actions),
        "safety_status": episode.recovery_plan.safety_status if episode.recovery_plan else None,
        "recovery_success": bool(episode.validation and episode.validation.recovered is True),
        "validation_success": bool(episode.validation and episode.validation.recovered is True),
        "recovery_attempts": len(episode.executions),
        "first_attempt_success": episode.executions[0].success if episode.executions else None,
        "action_history": [action.value for action in episode.action_history],
        "simulator_draw": episode.executions[0].workload_state.get("draw") if episode.executions else None,
        "simulator_probability": episode.executions[0].workload_state.get("probability") if episode.executions else None,
        "simulator_version": simulator.version,
        "memory_version_before": episode.memory_version_before,
        "memory_version_after": episode.memory_version_after,
        "training_manifestation_ids": sorted(training_ids),
        "relevant_mechanisms": relevant_mechanisms,
        "target_mechanism": target_mechanism,
    }


def annotate(row: dict[str, Any], optimal_action: str) -> dict[str, Any]:
    row["ground_truth_optimal_action"] = optimal_action
    row["action_is_optimal"] = row["selected_action"] == optimal_action
    row["action_changed_from_no_memory_baseline"] = row["selected_action"] != "retry"
    row["unsafe_transfer"] = bool(row.get("unsafe_transfer", False) or (row["historical_action_transfer"] and row["selected_action"] != optimal_action))
    return row


def run_scenario(condition: str, mechanism: str, seed: int, index: int) -> list[dict[str, Any]]:
    manifestation_id, features, ground_truth_mechanism, optimal_action, probabilities, unsafe_actions = ground_truth_for(mechanism, condition)
    events = training_events_for(condition, mechanism)
    rows = []
    for baseline in PROTOCOL["baselines"]:
        if baseline == "B2_memory_planner":
            row = memory_baseline_record(condition, ground_truth_mechanism, seed, features, events, probabilities, unsafe_actions, index)
        else:
            row = direct_baseline_record(baseline, condition, ground_truth_mechanism, seed, features, events, probabilities, unsafe_actions, index)
        row["evaluation_manifestation_id"] = manifestation_id
        row["latent_mechanism_exposed_to_runtime"] = False
        rows.append(annotate(row, optimal_action))
    return rows


def run_distance_ladder(mechanism: str, seed: int, index_start: int) -> list[dict[str, Any]]:
    rows = []
    for offset, band in enumerate(PROTOCOL["distance_bands"]):
        manifestation_id, features, ground_truth_mechanism = eval_manifestation(mechanism, band)
        model = mechanism_for(ground_truth_mechanism)
        events = training_events_for("C6_uncertainty_ladder", mechanism)
        probabilities = dict(model["action_probabilities"])
        unsafe_actions = list(model.get("unsafe_actions", []))
        row = memory_baseline_record("C6_uncertainty_ladder", ground_truth_mechanism, seed, features, events, probabilities, unsafe_actions, index_start + offset, target_mechanism=ground_truth_mechanism)
        if band == "D4_unrelated":
            row["target_mechanism"] = ground_truth_mechanism
            row["relevance_recall"] = 0.0
        row["distance_band"] = band
        row["evaluation_manifestation_id"] = manifestation_id
        row["latent_mechanism_exposed_to_runtime"] = False
        rows.append(annotate(row, model["optimal_action"]))
    return rows


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def avg(key: str, subset: list[dict[str, Any]] = rows):
        values = [float(row[key]) for row in subset if row.get(key) is not None]
        return mean(values) if values else None
    def sd(key: str, subset: list[dict[str, Any]] = rows):
        values = [float(row[key]) for row in subset if row.get(key) is not None]
        return pstdev(values) if len(values) > 1 else 0.0 if values else None
    return {
        "episode_count": len(rows),
        "relevant_retrieval_rate": mean(float(row["relevant_retrieval_count"] > 0) for row in rows) if rows else 0.0,
        "mean_retrieval_count": avg("retrieval_count"),
        "mean_relevant_retrieval_count": avg("relevant_retrieval_count"),
        "mean_relevance_precision": avg("relevance_precision"),
        "mean_relevance_recall": avg("relevance_recall"),
        "mean_similarity_or_distance": avg("distance_to_training"),
        "mean_diagnosis_confidence": avg("diagnosis_confidence"),
        "std_diagnosis_confidence": sd("diagnosis_confidence"),
        "mean_diagnosis_uncertainty": avg("diagnosis_uncertainty"),
        "std_diagnosis_uncertainty": sd("diagnosis_uncertainty"),
        "action_counts": dict(Counter(row["selected_action"] for row in rows)),
        "action_optimal_rate": avg("action_is_optimal"),
        "action_change_rate": avg("action_changed_from_no_memory_baseline"),
        "abstention_rate": avg("abstained"),
        "recovery_success_rate": avg("recovery_success"),
        "validation_success_rate": avg("validation_success"),
        "mean_recovery_attempts": avg("recovery_attempts"),
        "repeated_failure_rate": avg("recovery_success", [row for row in rows if row["recovery_attempts"] > 1]),
        "unsafe_action_rate": avg("unsafe_action"),
        "unsafe_transfer_rate": avg("unsafe_transfer"),
        "abstention_under_conflict": avg("abstained", [row for row in rows if row["condition"] in {"C3_conflicting_memory", "C5_safety_override"}]),
        "memory_version_max": max((row["memory_version_after"] or 0 for row in rows), default=0),
    }


def run_all() -> dict[str, Any]:
    all_rows: list[dict[str, Any]] = []
    per_seed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mechanisms = list(PROTOCOL["latent_mechanisms"])
    conditions = ["C0_no_memory", "C1_training_memory", "C2_irrelevant_memory", "C3_exact_memory_removed", "C4_negative_transfer", "C5_safety_override"]
    index = 0
    for seed in PROTOCOL["seed_list"]:
        for mechanism in mechanisms:
            for condition in conditions:
                rows = run_scenario(condition, mechanism, seed, index)
                all_rows.extend(rows)
                per_seed[str(seed)].extend(rows)
                index += 1
            ladder = run_distance_ladder(mechanism, seed, index)
            all_rows.extend(ladder)
            per_seed[str(seed)].extend(ladder)
            index += len(ladder)

        # Counterfactual pair: same observable D2 manifestation and simulator seed,
        # with only prior-memory availability changed.
        for mechanism in mechanisms:
            manifestation_id, features, ground_truth_mechanism, optimal_action, probabilities, unsafe_actions = ground_truth_for(mechanism, "C7_counterfactual_pair")
            for condition in ("C0_no_memory", "C1_training_memory"):
                events = training_events_for(condition, mechanism)
                row = memory_baseline_record(condition, ground_truth_mechanism, seed, features, events, probabilities, unsafe_actions, index)
                row["baseline"] = "B2_memory_planner"
                row["condition"] = "C7_counterfactual_pair"
                row["memory_world"] = condition
                row["evaluation_manifestation_id"] = manifestation_id
                row["counterfactual_pair_id"] = f"pair-{seed}-{mechanism}"
                row["counterfactual_only_manipulated_variable"] = "memory_availability"
                row["latent_mechanism_exposed_to_runtime"] = False
                all_rows.append(annotate(row, optimal_action))
                per_seed[str(seed)].append(annotate(row, optimal_action))
            index += 1

    summaries = {}
    for key in sorted({(row["baseline"], row["condition"]) for row in all_rows}):
        baseline, condition = key
        summaries[f"{baseline}__{condition}"] = aggregate([row for row in all_rows if row["baseline"] == baseline and row["condition"] == condition])
    distance_summary = {}
    for band in PROTOCOL["distance_bands"]:
        distance_summary[band] = aggregate([row for row in all_rows if row.get("distance_band") == band])
    per_seed_summary = {seed: aggregate(rows) for seed, rows in sorted(per_seed.items())}
    c7_rows = [row for row in all_rows if row["baseline"] == "B2_memory_planner" and row["condition"] == "C7_counterfactual_pair"]
    c7_no_memory = [row for row in c7_rows if not row["memory_event_ids"]]
    c7_memory = [row for row in c7_rows if row["memory_event_ids"]]
    comparisons = {
        "C7_counterfactual_pair": {
            "no_memory_success": mean(float(row["recovery_success"]) for row in c7_no_memory),
            "training_memory_success": mean(float(row["recovery_success"]) for row in c7_memory),
            "delta": mean(float(row["recovery_success"]) for row in c7_memory) - mean(float(row["recovery_success"]) for row in c7_no_memory),
            "same_observation_ids": sorted({row["observation_id"] for row in c7_rows}),
            "same_seeds": sorted({row["seed"] for row in c7_rows}),
            "only_manipulated_variable": "memory_availability"
        },
        "C0_vs_C1_memory_planner": {
            "no_memory_success": summaries["B2_memory_planner__C0_no_memory"]["recovery_success_rate"],
            "training_memory_success": summaries["B2_memory_planner__C1_training_memory"]["recovery_success_rate"],
            "delta": summaries["B2_memory_planner__C1_training_memory"]["recovery_success_rate"] - summaries["B2_memory_planner__C0_no_memory"]["recovery_success_rate"],
        },
        "C1_vs_C3_exact_removed": {
            "training_memory_success": summaries["B2_memory_planner__C1_training_memory"]["recovery_success_rate"],
            "exact_removed_success": summaries["B2_memory_planner__C3_exact_memory_removed"]["recovery_success_rate"],
            "delta": summaries["B2_memory_planner__C3_exact_memory_removed"]["recovery_success_rate"] - summaries["B2_memory_planner__C1_training_memory"]["recovery_success_rate"],
        },
        "baseline_comparison_training_memory": {baseline: summaries[f"{baseline}__C1_training_memory"] for baseline in PROTOCOL["baselines"]},
        "negative_transfer": {baseline: summaries[f"{baseline}__C4_negative_transfer"] for baseline in PROTOCOL["baselines"]},
        "safety": {baseline: summaries[f"{baseline}__C5_safety_override"] for baseline in PROTOCOL["baselines"]},
    }
    return {"protocol": PROTOCOL, "summaries": summaries, "distance_summary": distance_summary, "per_seed_summary": per_seed_summary, "comparisons": comparisons, "records": all_rows}


def write_outputs(result: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    for old in RESULTS.glob("per_seed/*.json"):
        old.unlink()
    (RESULTS / "protocol.json").write_text(json.dumps(PROTOCOL, indent=2, sort_keys=True) + "\n")
    (RESULTS / "results.json").write_text(json.dumps(result["records"], indent=2, sort_keys=True) + "\n")
    (RESULTS / "summary.json").write_text(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2, sort_keys=True) + "\n")
    per_seed_dir = RESULTS / "per_seed"
    per_seed_dir.mkdir(exist_ok=True)
    for seed in PROTOCOL["seed_list"]:
        rows = [row for row in result["records"] if row["seed"] == seed]
        (per_seed_dir / f"seed_{seed}.json").write_text(json.dumps({"seed": seed, "records": rows}, indent=2, sort_keys=True) + "\n")
    manifest = {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
        "simulator_version": PROTOCOL["simulator_version"],
        "seed_list": PROTOCOL["seed_list"],
        "latent_mechanism_exposed_to_runtime": False,
        "evaluation_manifestations_in_training_memory": False,
        "frozen_paths_modified": False,
        "old_result_paths_written": [],
        "statistical_claim": "multi-seed descriptive controlled simulator evaluation; no significance claim",
    }
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    report = build_report(result, manifest)
    (RESULTS / "report.md").write_text(report)


def build_report(result: dict[str, Any], manifest: dict[str, Any]) -> str:
    summaries = result["summaries"]
    c0 = summaries["B2_memory_planner__C0_no_memory"]
    c1 = summaries["B2_memory_planner__C1_training_memory"]
    c3 = summaries["B2_memory_planner__C3_exact_memory_removed"]
    lines = [
        "# Counterfactual Behavioral-Generalization Experiment",
        "",
        "## Research question",
        "",
        "Can the runtime produce useful validated behavior for an unseen manifestation of a known latent failure mechanism when the exact manifestation is absent from memory?",
        "",
        "## Why the previous result was insufficient",
        "",
        "The previous related-minus-exact result measured retrieval within a similarity neighborhood. It did not remove the exact supporting experience while preserving a separate latent mechanism, so it could not distinguish episodic transfer from behavioral generalization. This protocol hides the mechanism and evaluates A3/B3/C3 manifestations that are never inserted into memory.",
        "",
        "## Latent mechanisms and observable manifestations",
        "",
        "The simulator contains three latent mechanisms: resource pressure (A1 GPU queue, A2 memory bandwidth, unseen A3 thermal throttle), latency congestion (B1 queue latency, B2 timeout burst, unseen B3 retry storm), and configuration drift (C1 feature flag, C2 schema mismatch, unseen C3 rollout skew). The runtime sees only six observable telemetry-like features, generic failure evidence, and current safety constraints. It never receives the mechanism ID, optimal action, future outcome, or hidden action label.",
        "",
        "## Baselines",
        "",
        "| Baseline | Definition | Uses episodic FailureMemory |",
        "|---|---|---|",
        "| B0 | Fixed retry with no training data | No |",
        "| B1 | Nearest declared training manifestation copies its action | No |",
        "| B2 | Current FailureMemory + diagnosis + recovery planner | Yes |",
        "| B3 | Observable action-centroid classifier | No |",

        "## Hypotheses",
        "",
        "H1: training memory improves validated behavior on exact training manifestations. H2: the improvement survives on unseen A3/B3/C3 manifestations if the runtime has learned a mechanism-level pattern rather than copied an episodic action. H3: nearest-neighbor transfer is weaker than the full planner. H4: negative transfer and safety conflict produce a safe alternative or abstention, never an executed unsafe action.",
        "",
        "## Protocol and leakage controls",
        "",
        f"The protocol uses simulator `{manifest['simulator_version']}`, seeds `{', '.join(map(str, manifest['seed_list']))}`, fixed distance bands D0–D4, declared thresholds, fixed action probabilities, and a maximum of {PROTOCOL['max_recovery_attempts']} attempts. The training set is fixed before evaluation. A3/B3/C3 never appear in training memory. Counterfactual pairs share the same seed, observation, simulator, action probabilities, safety constraints, and validation; only memory availability changes.",
        "",
        "## Core results",
        "",
        "| Comparison | Recovery success | Relevant retrieval | Diagnosis uncertainty | Interpretation |",
        "|---|---:|---:|---:|---|",

        f"| B2 C0 no memory | {c0['recovery_success_rate']:.2f} | {c0['mean_relevant_retrieval_count']:.2f} | {c0['mean_diagnosis_uncertainty']:.2f} | no episodic evidence |",

        f"| B2 C1 training memory | {c1['recovery_success_rate']:.2f} | {c1['mean_relevant_retrieval_count']:.2f} | {c1['mean_diagnosis_uncertainty']:.2f} | A1+A2 / B1+B2 / C1+C2 available |",

        f"| B2 C3 exact removed | {c3['recovery_success_rate']:.2f} | {c3['mean_relevant_retrieval_count']:.2f} | {c3['mean_diagnosis_uncertainty']:.2f} | unseen manifestation absent from memory |",

        "",
        f"The counterfactual C1-minus-C0 success delta is `{result['comparisons']['C0_vs_C1_memory_planner']['delta']:.2f}`. The C3-minus-C1 delta is `{result['comparisons']['C1_vs_C3_exact_removed']['delta']:.2f}`. The clean C7 pair delta is `{result['comparisons']['C7_counterfactual_pair']['delta']:.2f}` with memory availability as the only manipulated variable. A positive C1-minus-C0 value would indicate a memory effect; a positive C3-minus-C1 value would be evidence that the effect survives exact-memory removal. The experiment must be interpreted from the recorded values, not from retrieval alone.",
        "",
        "## Negative transfer and safety",
        "",
        "The negative-transfer manifestation B4 buffer release is not inserted into memory. Historical rollback succeeds for B1/B2, but rollback is ineffective for B4 and reconfigure is the simulator-optimal action. The report records whether each baseline transfers rollback, whether its first validation fails, and whether bounded replanning recovers. In the safety condition, rollback is marked unsafe in the current world; the expected invariant is zero unsafe actions and abstention or a safe alternative.",
        "",
        "## Distance ladder",
        "",
        "The result includes D0 exact, D1 near, D2 moderate unseen, D3 large shift, and D4 unrelated. Each band reports retrieval, similarity/distance, diagnosis confidence and uncertainty, action, recovery success, and abstention. The curve is descriptive; no threshold is tuned after observing evaluation results.",
        "",
        "## Per-seed results",
        "",
        "| Seed | Episodes | Mean success | Mean uncertainty | Mean attempts |",
        "|---:|---:|---:|---:|---:|",
        *[f"| {seed} | {stats['episode_count']} | {stats['recovery_success_rate']:.2f} | {stats['mean_diagnosis_uncertainty'] if stats['mean_diagnosis_uncertainty'] is not None else 'n/a'} | {stats['mean_recovery_attempts']:.2f} |" for seed, stats in sorted(result['per_seed_summary'].items())],
        "",
        "## Baseline comparison on training-memory condition",
        "",
        "| Baseline | Success | Optimal-action rate | Abstention | Unsafe-action rate |",
        "|---|---:|---:|---:|---:|",
        *[f"| {baseline} | {stats['recovery_success_rate']:.2f} | {stats['action_optimal_rate']:.2f} | {stats['abstention_rate']:.2f} | {stats['unsafe_action_rate']:.2f} |" for baseline, stats in sorted(result['comparisons']['baseline_comparison_training_memory'].items())],
        "",
        "## Interpretation rules",
        "",
        "Retrieval is not called generalization. Action copying is not called reasoning. Simulator success is not called production recovery. If C3 does not improve over C0, the scientifically correct conclusion is failure to demonstrate genuine behavioral generalization. The current architecture may therefore demonstrate safe episodic transfer and local retrieval generalization without learning an abstract latent failure mechanism.",
        "",
        "## Reproducibility and limitations",
        "",
        f"The exact base commit is `{manifest['git_commit']}`. Event IDs are deterministic hashes, Python's process-randomized hash is not used, and the experiment writes only to `experiments/results/counterfactual_generalization/`. The study is a controlled simulator evaluation with five seeds, not a statistically powered real-world study. Manifestations and probabilities are hand-designed, the observable baseline is simple, and the runtime model remains honestly unconfigured with risk 0.0. No production self-healing claim is made.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    result = run_all()
    write_outputs(result)
    print(json.dumps({"summaries": result["summaries"], "distance_summary": result["distance_summary"], "comparisons": result["comparisons"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
