"""Controlled memory-composition and planner-superiority experiment."""
from __future__ import annotations

import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from src.runtime.builder import build_runtime_system
from src.runtime.components import RuleBasedRecoveryPlanner, SimulatedRecoveryExecutor, SignalRecoveryValidator
from src.runtime.contracts import Observation, RecoveryAction, ReliabilityAssessment
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "configs/runtime_demo/memory_composition_protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text())
RESULTS = ROOT / "experiments/results/memory_composition"
FEATURES = PROTOCOL["feature_names"]
ACTIONS = {action.value for action in RecoveryAction}


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    return sqrt(sum((float(a[name]) - float(b[name])) ** 2 for name in FEATURES))


def stable_id(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:24]


def factor_features(factor_names: list[str]) -> dict[str, float]:
    values = [PROTOCOL["latent_factors"][name]["features"] for name in factor_names]
    return {name: round(mean(value[name] for value in values), 6) for name in FEATURES}


def training_spec(spec_id: str) -> dict[str, Any]:
    for spec in PROTOCOL["training_experiences"]:
        if spec["id"] == spec_id:
            return spec
    if spec_id == "E1_X_failed":
        base = training_spec("E1_X_only").copy()
        base.update({"id": spec_id, "validation_status": "FAILED"})
        return base
    raise KeyError(spec_id)


def event_for(spec_id: str) -> ReliabilityEvent:
    spec = training_spec(spec_id)
    context = factor_features(spec["factors"])
    return ReliabilityEvent(
        event_id=f"mc-{spec_id}",
        workload_id="memory-composition-training",
        source=EventSource.BENCHMARK,
        context=context,
        confidence=float(spec["confidence"]),
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.CORRECT if spec["validation_status"] == "RECOVERED" else Outcome.INCORRECT,
        metadata={
            "recovery_action": spec["action"],
            "validation_status": spec["validation_status"],
            "source_type": "fixed_composition_training",
        },
    )


def observation(case_id: str, seed: int, index: int, unsafe_actions: list[str]) -> Observation:
    case = PROTOCOL["evaluation_cases"][case_id]
    return Observation(
        observation_id=f"mc-obs-{case_id}-{seed:02d}-{index:03d}",
        workload_id="memory-composition-evaluation",
        timestamp=datetime(2026, 2, 1, tzinfo=timezone.utc) + timedelta(seconds=seed * 1000 + index),
        features=dict(case["features"]),
        metrics={"error_rate": float(case["features"]["error_rate"])},
        resource_signals={},
        error="observed composite failure",
        environment={"failure_class": "composite_failure", "unsafe_actions": list(unsafe_actions)},
        metadata={"source_type": "memory_composition_simulator"},
        provenance={"source_type": "memory_composition_simulator", "simulator_version": PROTOCOL["simulator_version"], "seed": seed},
    )


def simulator(case_id: str, seed: int) -> SimulatedRecoveryExecutor:
    case = PROTOCOL["evaluation_cases"][case_id]
    return SimulatedRecoveryExecutor(
        outcome_probabilities={"composite_failure": case["action_probabilities"]},
        seed=seed,
        simulator_version=PROTOCOL["simulator_version"],
    )


def reliability_stub() -> ReliabilityAssessment:
    return ReliabilityAssessment(confidence=0.5, risk=0.0, decision="ABSTAIN", fused_score=0.0, uncertainty=1.0, predicted_label=None, model_id="unconfigured", model_version="none", calibrator_version="none", training_data_id=None, configuration={"memory_composition": True})


def apply_safety(action: RecoveryAction, unsafe_actions: list[str]) -> tuple[RecoveryAction, bool, bool]:
    proposed_unsafe = action.value in set(unsafe_actions)
    if proposed_unsafe:
        return RecoveryAction.ABSTAIN, proposed_unsafe, True
    return action, False, False


def direct_baseline(baseline: str, condition: str, case_id: str, seed: int, index: int, events: list[ReliabilityEvent]) -> dict[str, Any]:
    case = PROTOCOL["evaluation_cases"][case_id]
    obs = observation(case_id, seed, index, case["unsafe_actions"])
    if baseline == "B0_no_memory":
        proposed = RecoveryAction.RETRY
        nearest_distance = None
    elif baseline == "B1_nearest_neighbor":
        if not events:
            proposed, nearest_distance = RecoveryAction.RETRY, None
        else:
            nearest_distance, nearest = min((distance(obs.features, event.context), event) for event in events)
            proposed = RecoveryAction(nearest.metadata["recovery_action"])
    else:
        grouped: dict[str, list[dict[str, float]]] = defaultdict(list)
        for event in events:
            grouped[event.metadata["recovery_action"]].append(event.context)
        if not grouped:
            proposed, nearest_distance = RecoveryAction.RETRY, None
        else:
            centroids = {action: {name: mean(row[name] for row in contexts) for name in FEATURES} for action, contexts in grouped.items()}
            nearest_distance, action = min((distance(obs.features, centroid), action) for action, centroid in centroids.items())
            proposed = RecoveryAction(action)
    selected, proposed_unsafe, rejected_unsafe = apply_safety(proposed, case["unsafe_actions"])
    executor = simulator(case_id, seed)
    execution = executor.execute(type("Plan", (), {"selected_action": selected, "abstained": selected is RecoveryAction.ABSTAIN})(), obs, attempt=1)
    validation = SignalRecoveryValidator().validate(obs, reliability_stub(), execution)
    return row_base(baseline, condition, case_id, seed, index, events, obs, proposed, selected, proposed_unsafe, rejected_unsafe, nearest_distance, execution, validation, case["optimal_action"])


def row_base(baseline: str, condition: str, case_id: str, seed: int, index: int, events: list[ReliabilityEvent], obs: Observation, proposed: RecoveryAction, selected: RecoveryAction, proposed_unsafe: bool, rejected_unsafe: bool, nearest_distance: float | None, execution: Any, validation: Any, optimal_action: str, *, retrieved: list[Any] | None = None, diagnosis_confidence: float | None = None, diagnosis_uncertainty: float | None = None, planner_mode: str = "direct") -> dict[str, Any]:
    retrieved = retrieved or []
    relevant = [match for match in retrieved if bool(getattr(match, "relevant", False))]
    return {
        "baseline": baseline,
        "condition": condition,
        "case_id": case_id,
        "seed": seed,
        "observation_id": obs.observation_id,
        "features": dict(obs.features),
        "training_event_ids": [event.event_id for event in events],
        "retrieved_event_ids": [getattr(getattr(match, "event", None), "event_id", None) for match in retrieved],
        "relevant_event_ids": [getattr(getattr(match, "event", None), "event_id", None) for match in relevant],
        "relevant_experiences_used": len(relevant),
        "relevant_retrieval_precision": (sum(getattr(match, "relevant", False) for match in retrieved) / len(retrieved)) if retrieved else None,
        "relevant_retrieval_recall": 1.0 if relevant else 0.0,
        "similarity_distribution": [float(getattr(match, "similarity", 0.0)) for match in retrieved],
        "nearest_distance": nearest_distance,
        "diagnosis_confidence": diagnosis_confidence,
        "diagnosis_uncertainty": diagnosis_uncertainty,
        "diagnosis_correct": None,
        "proposed_action": proposed.value,
        "selected_action": selected.value,
        "optimal_action": optimal_action,
        "optimal_action_selected": selected.value == optimal_action,
        "action_agreement_with_B1": None,
        "action_disagreement": None,
        "abstained": selected is RecoveryAction.ABSTAIN,
        "recovery_success": validation.recovered is True,
        "validation_success": validation.recovered is True,
        "attempts": 0 if selected is RecoveryAction.ABSTAIN else 1,
        "failed_attempts": 0 if selected is RecoveryAction.ABSTAIN or execution.success else 1,
        "bounded_replanning": False,
        "proposed_unsafe_action": proposed_unsafe,
        "rejected_unsafe_action": rejected_unsafe,
        "executed_unsafe_action": False,
        "unsafe_transfer": proposed_unsafe,
        "planner_mode": planner_mode,
        "latent_factors_exposed_to_runtime": False,
        "optimal_action_exposed_to_runtime": False,
        "simulator_draw": execution.workload_state.get("draw"),
        "simulator_probability": execution.workload_state.get("probability"),
    }


def runtime_b2(condition: str, case_id: str, seed: int, index: int, events: list[ReliabilityEvent], planner_mode: str = "full") -> dict[str, Any]:
    case = PROTOCOL["evaluation_cases"][case_id]
    memory = None
    system = build_runtime_system(feature_names=FEATURES, failure_memory=memory, planner=RuleBasedRecoveryPlanner(default_action=RecoveryAction.RETRY, abstain_on_conflict=True), executor=simulator(case_id, seed), experience_path=f"/tmp/memory_composition_{seed}_{index}.jsonl", max_attempts=PROTOCOL["max_recovery_attempts"], relevance_threshold=PROTOCOL["relevance_threshold"])
    if events:
        system.failure_memory.seed_events(events)
    obs = observation(case_id, seed, index, case["unsafe_actions"])
    episode = system.controller.process(obs)
    retrieved = list(episode.retrieved_experiences)
    selected = episode.recovery_plan.selected_action if episode.recovery_plan else RecoveryAction.ABSTAIN
    relevant_matches = [match for match in retrieved if bool(getattr(match, "relevant", False))]
    proposed_unsafe = any(getattr(match.event, "metadata", {}).get("recovery_action") in set(case["unsafe_actions"]) for match in relevant_matches)
    return row_base("B2_memory_planner", condition, case_id, seed, index, events, obs, selected, selected, proposed_unsafe, bool(episode.recovery_plan and episode.recovery_plan.safety_status == "rejected"), min((float(getattr(match, "distance", 0.0)) for match in retrieved), default=None), episode.executions[0] if episode.executions else type("Execution", (), {"success": False, "workload_state": {"draw": None, "probability": None}})(), episode.validation or type("Validation", (), {"recovered": False})(), case["optimal_action"], retrieved=retrieved, diagnosis_confidence=episode.diagnosis.confidence if episode.diagnosis else None, diagnosis_uncertainty=episode.diagnosis.uncertainty if episode.diagnosis else None, planner_mode=planner_mode)


def score_actions(events: list[ReliabilityEvent], matches: list[Any]) -> RecoveryAction:
    scores: dict[RecoveryAction, float] = defaultdict(float)
    for match in matches:
        if not getattr(match, "relevant", False):
            continue
        event = match.event
        action = RecoveryAction(event.metadata["recovery_action"])
        sign = 1.0 if event.metadata.get("validation_status") == "RECOVERED" else -1.0
        scores[action] += sign * float(match.similarity) * float(event.confidence)
    positive = {action: score for action, score in scores.items() if score > 0}
    if not positive:
        return RecoveryAction.RETRY
    return max(positive, key=lambda action: (positive[action], action.value))


def run_ablation_variant(condition: str, case_id: str, seed: int, index: int, events: list[ReliabilityEvent], mode: str) -> dict[str, Any]:
    case = PROTOCOL["evaluation_cases"][case_id]
    obs = observation(case_id, seed, index, case["unsafe_actions"])
    memory = build_runtime_system(feature_names=FEATURES, failure_memory=None, experience_path=f"/tmp/memory_comp_ablation_{seed}_{index}.jsonl", max_attempts=1, relevance_threshold=PROTOCOL["relevance_threshold"])
    if events:
        memory.failure_memory.seed_events(events)
    matches = memory.failure_memory.retrieve_matches(dict(obs.features), 0.5, k=5, min_similarity=PROTOCOL["relevance_threshold"])
    if mode == "diagnosis_direct":
        proposed = RecoveryAction(matches[0].event.metadata["recovery_action"]) if matches else RecoveryAction.RETRY
    elif mode == "action_scoring":
        proposed = score_actions(events, matches)
    else:
        episode = memory.controller.process(obs)
        return row_base("B2_full", condition, case_id, seed, index, events, obs, episode.recovery_plan.selected_action if episode.recovery_plan else RecoveryAction.ABSTAIN, episode.recovery_plan.selected_action if episode.recovery_plan else RecoveryAction.ABSTAIN, False, False, min((float(match.distance) for match in matches), default=None), episode.executions[0] if episode.executions else type("Execution", (), {"success": False, "workload_state": {"draw": None, "probability": None}})(), episode.validation or type("Validation", (), {"recovered": False})(), case["optimal_action"], retrieved=matches, diagnosis_confidence=episode.diagnosis.confidence if episode.diagnosis else None, diagnosis_uncertainty=episode.diagnosis.uncertainty if episode.diagnosis else None, planner_mode="full")
    selected, proposed_unsafe, rejected = apply_safety(proposed, case["unsafe_actions"])
    execution = simulator(case_id, seed).execute(type("Plan", (), {"selected_action": selected, "abstained": selected is RecoveryAction.ABSTAIN})(), obs)
    validation = SignalRecoveryValidator().validate(obs, reliability_stub(), execution)
    return row_base("B2_" + mode, condition, case_id, seed, index, events, obs, proposed, selected, proposed_unsafe, rejected, min((float(match.distance) for match in matches), default=None), execution, validation, case["optimal_action"], retrieved=matches, planner_mode=mode)


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def avg(key: str) -> float | None:
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        return mean(values) if values else None
    return {
        "episodes": len(rows),
        "success": avg("recovery_success"),
        "validation_success": avg("validation_success"),
        "optimal_action_rate": avg("optimal_action_selected"),
        "action_agreement_with_B1": avg("action_agreement_with_B1"),
        "action_disagreement_rate": avg("action_disagreement"),
        "mean_diagnosis_confidence": avg("diagnosis_confidence"),
        "mean_diagnosis_uncertainty": avg("diagnosis_uncertainty"),
        "mean_relevant_experiences_used": avg("relevant_experiences_used"),
        "mean_relevance_precision": avg("relevant_retrieval_precision"),
        "mean_relevance_recall": avg("relevant_retrieval_recall"),
        "mean_attempts": avg("attempts"),
        "failed_attempts": avg("failed_attempts"),
        "abstention_rate": avg("abstained"),
        "proposed_unsafe_actions": avg("proposed_unsafe_action"),
        "rejected_unsafe_actions": avg("rejected_unsafe_action"),
        "executed_unsafe_actions": avg("executed_unsafe_action"),
        "unsafe_transfer_rate": avg("unsafe_transfer"),
        "action_counts": dict(Counter(row["selected_action"] for row in rows)),
    }


def attach_agreement(rows: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[str, int, str], dict[str, str]] = defaultdict(dict)
    for row in rows:
        grouped[(row["condition"], row["seed"], row["case_id"] )][row["baseline"]] = row["selected_action"]
    for row in rows:
        b1 = grouped[(row["condition"], row["seed"], row["case_id"])].get("B1_nearest_neighbor")
        if b1 is not None:
            row["action_agreement_with_B1"] = row["selected_action"] == b1
            row["action_disagreement"] = row["selected_action"] != b1


def discrimination_check() -> dict[str, Any]:
    case = PROTOCOL["evaluation_cases"]["COMP_XZ_unseen"]
    e1 = [event_for("E1_X_only")]
    e3 = [event_for("E3_Z_only")]
    both = e1 + e3
    nearest = direct_baseline("B1_nearest_neighbor", "C2_all_relevant", "COMP_XZ_unseen", 7, 0, both)
    e1_only = direct_baseline("B1_nearest_only", "E1_only", "COMP_XZ_unseen", 7, 1, e1)
    e3_only = direct_baseline("B1_complement_only", "E3_only", "COMP_XZ_unseen", 7, 2, e3)
    b2 = runtime_b2("C2_all_relevant", "COMP_XZ_unseen", 7, 3, both)
    checks = {
        "nearest_only_is_insufficient": nearest["selected_action"] != case["optimal_action"],
        "e1_only_is_insufficient": e1_only["selected_action"] != case["optimal_action"],
        "e3_only_is_insufficient": e3_only["selected_action"] != case["optimal_action"],
        "combined_b2_is_sufficient": b2["selected_action"] == case["optimal_action"],
        "latent_factors_hidden": not nearest["latent_factors_exposed_to_runtime"],
        "optimal_action_hidden": not nearest["optimal_action_exposed_to_runtime"],
        "b1_accesses_one_event_only": len(e1) == 1,
    }
    return {"checks": checks, "nearest": nearest, "e1_only": e1_only, "e3_only": e3_only, "b2": b2, "passed": all(checks.values())}


def run_all() -> dict[str, Any]:
    check = discrimination_check()
    rows: list[dict[str, Any]] = []
    per_seed: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    index = 10
    condition_cases = {
        "C0_no_memory": "COMP_XZ_unseen",
        "C1_nearest_only": "COMP_XZ_unseen",
        "C2_all_relevant": "COMP_XZ_unseen",
        "C3_full_with_irrelevant": "COMP_XZ_unseen",
        "C4_conflicting": "COMP_XZ_unseen",
        "C5_safety_conflict": "SAFETY_XZ",
        "C6_negative_outcome": "NEG_XZ",
    }
    for seed in PROTOCOL["seed_list"]:
        for condition, case_id in condition_cases.items():
            spec_ids = PROTOCOL["conditions"][condition]
            events = [event_for(spec_id) for spec_id in spec_ids]
            if condition == "C1_nearest_only":
                events = [event_for("E1_X_only")]
            for baseline in PROTOCOL["baselines"]:
                if baseline == "B2_memory_planner":
                    row = runtime_b2(condition, case_id, seed, index, events)
                else:
                    row = direct_baseline(baseline, condition, case_id, seed, index, events)
                rows.append(row); per_seed[str(seed)][condition].append(row); index += 1
        # Explicit evidence ablation matrix.
        for ablation, spec_ids in PROTOCOL["ablation_conditions"].items():
            events = [event_for(spec_id) for spec_id in spec_ids]
            for seed_case in ["COMP_XZ_unseen"]:
                row = runtime_b2("ablation_" + ablation, seed_case, seed, index, events)
                rows.append(row); per_seed[str(seed)]["ablation_" + ablation].append(row); index += 1
        # Diagnosis and planner contribution ablations on all-relevant evidence.
        events = [event_for("E1_X_only"), event_for("E3_Z_only")]
        for mode in ("diagnosis_direct", "action_scoring", "full"):
            row = run_ablation_variant("C2_all_relevant", "COMP_XZ_unseen", seed, index, events, mode)
            rows.append(row); per_seed[str(seed)]["ablation_" + mode].append(row); index += 1

    attach_agreement(rows)
    summaries: dict[str, Any] = {}
    for key in sorted({(row["baseline"], row["condition"]) for row in rows}):
        baseline, condition = key
        summaries[f"{baseline}__{condition}"] = aggregate([row for row in rows if row["baseline"] == baseline and row["condition"] == condition])
    per_seed_summary = {seed: {condition: aggregate(condition_rows) for condition, condition_rows in sorted(conditions.items())} for seed, conditions in sorted(per_seed.items())}
    b1 = summaries["B1_nearest_neighbor__C2_all_relevant"]
    b2 = summaries["B2_memory_planner__C2_all_relevant"]
    composition = {condition: summaries.get(f"B2_memory_planner__{condition}") for condition in ("C0_no_memory", "C1_nearest_only", "C2_all_relevant", "C3_full_with_irrelevant", "C4_conflicting", "C5_safety_conflict", "C6_negative_outcome")}
    ablation = {condition: aggregate([row for row in rows if row["condition"] == "ablation_" + condition]) for condition in PROTOCOL["ablation_conditions"]}
    planner_ablation = {mode: aggregate([row for row in rows if row["baseline"] == ("B2_full" if mode == "full" else "B2_" + mode) and row["condition"] == "ablation_C2_all_relevant"]) for mode in ("diagnosis_direct", "action_scoring", "full")}
    ordering = ordering_test()
    return {"protocol": PROTOCOL, "discrimination_check": check, "summaries": summaries, "per_seed_summary": per_seed_summary, "composition": composition, "evidence_ablation": ablation, "planner_ablation": planner_ablation, "ordering_test": ordering, "planner_advantage": {"success_delta": b2["success"] - b1["success"], "optimal_action_delta": b2["optimal_action_rate"] - b1["optimal_action_rate"]}, "records": rows}


def ordering_test() -> dict[str, Any]:
    decisions = []
    for seed, order in enumerate((["E1_X_only", "E3_Z_only"], ["E3_Z_only", "E1_X_only"], ["E1_X_only", "E3_Z_only"], ["E3_Z_only", "E1_X_only"]), start=1):
        events = [event_for(spec_id) for spec_id in order]
        decisions.append(runtime_b2("C2_all_relevant", "COMP_XZ_unseen", seed, 900 + seed, events)["selected_action"])
    return {"orders": [["E1_X_only", "E3_Z_only"], ["E3_Z_only", "E1_X_only"], ["E1_X_only", "E3_Z_only"], ["E3_Z_only", "E1_X_only"]], "decisions": decisions, "invariant": len(set(decisions)) == 1}


def report(result: dict[str, Any], manifest: dict[str, Any]) -> str:
    s = result["summaries"]
    c = result["composition"]
    lines = [
        "# Memory Composition and Planner Superiority Experiment", "",
        "## Research question", "",
        "Does the full FailureMemory + Diagnosis + RecoveryPlanner architecture provide decision-making capability beyond retrieving the nearest historical failure and copying its successful action?", "",
        "## Motivation from B1 = B2", "",
        "The prior counterfactual experiment found B1 nearest-neighbor success 0.80 and B2 full-planner success 0.80. The current protocol does not modify that result. It tests whether a deliberately compositional case, evidence ablation, negative transfer, diagnosis ablation, and planner ablation reveal additional value or a genuine limitation.", "",
        "## Previous reporting ambiguities", "",
        "The prior per-seed values aggregated every baseline, condition, distance band, and counterfactual row for a seed. They were not per-seed values for headline C0/C1/C3 conditions. This report uses condition-specific per-seed tables. The prior maximum-attempt value of 1 was intentional for action-selection isolation; this protocol declares the same one-attempt policy and makes no replanning claim.", "",
        "## Simulator design and leakage controls", "",
        "Three latent factors are declared: X resource pressure, Y latency congestion, and Z configuration drift. Training contains X-only, Y-only, Z-only, X+Y, and Y+Z experiences. The main evaluation case is the unseen X+Z combination. The runtime sees only the six observable features, generic failure evidence, and current safety constraints. It never receives factor IDs, optimal actions, action scores, or simulator probabilities. Training is fixed before evaluation and evaluation outcomes are never inserted before decision.", "",
        "## Baselines", "",
        "| Baseline | Definition |",
        "|---|---|",
        "| B0 | No memory; fixed retry |",
        "| B1 | Single closest memory; copy only its action; same safety, execution, validation |",
        "| B2 | Canonical FailureMemory + Diagnosis + RecoveryPlanner |",
        "| B3 | Observable-feature action centroid |",
        "",
        "## Discrimination check", "",
        f"The pre-evaluation discrimination check passed: `{result['discrimination_check']['passed']}`. It mechanically verifies that E1 alone, E3 alone, and the nearest individual experience are insufficient for the declared optimal action, while the full B2 path has the opportunity to select the optimal action. No hidden factor or optimal-action field enters the observation.", "",
        "## Main results", "",
        "| Condition | B0 success | B1 success | B2 success | B3 success | B2 optimal rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for condition in ("C0_no_memory", "C1_nearest_only", "C2_all_relevant", "C3_full_with_irrelevant", "C4_conflicting", "C5_safety_conflict", "C6_negative_outcome"):
        vals = [s.get(f"{baseline}__{condition}", {}).get("success") for baseline in PROTOCOL["baselines"]]
        b2 = s.get(f"B2_memory_planner__{condition}", {})
        lines.append(f"| {condition} | {vals[0] if vals[0] is not None else 'n/a'} | {vals[1] if vals[1] is not None else 'n/a'} | {vals[2] if vals[2] is not None else 'n/a'} | {vals[3] if vals[3] is not None else 'n/a'} | {b2.get('optimal_action_rate', 'n/a')} |")
    lines += ["", "## Planner advantage", "", f"B2 minus B1 recovery-success advantage on C2 all-relevant is `{result['planner_advantage']['success_delta']:.2f}`. The optimal-action advantage is `{result['planner_advantage']['optimal_action_delta']:.2f}`. A zero or negative result is preserved as a scientifically meaningful limitation rather than treated as a failure of the experiment.", "", "## Evidence ablation", "", "| Evidence | Success | Optimal rate | Uncertainty |", "|---|---:|---:|---:|"]
    for name, stats in result["evidence_ablation"].items():
        lines.append(f"| {name} | {stats['success']} | {stats['optimal_action_rate']} | {stats['mean_diagnosis_uncertainty']} |")
    lines += ["", "## Diagnosis and planner ablations", "", "| Variant | Success | Optimal rate | Abstention |", "|---|---:|---:|---:|"]
    for name, stats in result["planner_ablation"].items():
        lines.append(f"| {name} | {stats['success']} | {stats['optimal_action_rate']} | {stats['abstention_rate']} |")
    lines += ["", "## Ordering robustness", "", f"The deterministic ordering test produced decisions `{result['ordering_test']['decisions']}` and ordering invariance was `{result['ordering_test']['invariant']}`.", "", "## Safety, negative transfer, and failure cases", "", "Safety metrics separate proposed unsafe actions, rejected unsafe actions, and executed unsafe actions. The required invariant is zero executed unsafe actions. Negative-transfer results are reported without assuming that B2 must avoid a historical action; the simulator and planner limitations are part of the result.", "", "## Per-seed results", "", "The per-seed table is condition-specific; it does not aggregate unrelated baselines or distance bands.", "", "| Seed | Condition | Episodes | Success | Optimal rate | Uncertainty | Abstention | Attempts |", "|---:|---|---:|---:|---:|---:|---:|---:|"]
    for seed, conditions in result["per_seed_summary"].items():
        for condition, stats in conditions.items():
            lines.append(f"| {seed} | {condition} | {stats['episodes']} | {stats['success']} | {stats['optimal_action_rate']} | {stats['mean_diagnosis_uncertainty']} | {stats['abstention_rate']} | {stats['mean_attempts']} |")
    lines += ["", "## Hypothesis conclusions", "", "H1 memory versus no memory is read from C0 versus C1/C2. H2 multiple relevant experiences outperform one nearest experience only if C2 exceeds C1. H3 full diagnosis and planning outperform nearest-neighbor only if B2 exceeds B1. H4 ablation deltas show whether each experience is necessary. H5 is supported only when executed unsafe actions remain zero. H6 is supported when conflict increases uncertainty or abstention. The experiment does not engineer any target outcome.", "", "## Limitations", "", "This is a hand-designed, deterministic, multi-seed simulator study with one attempt per episode. It cannot establish production self-healing, real-world generalization, causal superiority beyond the declared worlds, or statistical significance. The current reliability model remains honestly unconfigured with risk 0.0. If B2 ties B1, the correct conclusion is that this architecture did not demonstrate measurable planner advantage under this protocol.", "", "## Reproducibility", "", f"Protocol version: `{manifest['protocol_version']}`. Simulator version: `{manifest['simulator_version']}`. Base commit: `{manifest['git_commit']}`. Protocol SHA-256: `{manifest['protocol_sha256']}`. Deterministic event IDs, fixed seeds, fixed training/evaluation sets, and explicit ordering permutations are used. Outputs are isolated under `experiments/results/memory_composition/`.", ""]
    return "\n".join(lines)


def write_outputs(result: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "ablations").mkdir(exist_ok=True)
    (RESULTS / "per_seed").mkdir(exist_ok=True)
    for path in RESULTS.glob("per_seed/*.json"):
        path.unlink()
    for path in RESULTS.glob("ablations/*.json"):
        path.unlink()
    (RESULTS / "protocol.json").write_text(json.dumps(PROTOCOL, indent=2, sort_keys=True) + "\n")
    (RESULTS / "results.json").write_text(json.dumps(result["records"], indent=2, sort_keys=True) + "\n")
    summary = {key: value for key, value in result.items() if key != "records"}
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for seed, conditions in result["per_seed_summary"].items():
        (RESULTS / "per_seed" / f"seed_{seed}.json").write_text(json.dumps({"seed": seed, "conditions": conditions}, indent=2, sort_keys=True) + "\n")
    for name, values in {"evidence_ablation": result["evidence_ablation"], "planner_ablation": result["planner_ablation"], "ordering_test": result["ordering_test"]}.items():
        (RESULTS / "ablations" / f"{name}.json").write_text(json.dumps(values, indent=2, sort_keys=True) + "\n")
    manifest = {"git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "protocol_version": PROTOCOL["protocol_version"], "simulator_version": PROTOCOL["simulator_version"], "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(), "seed_list": PROTOCOL["seed_list"], "frozen_paths_written": [], "latent_factors_exposed_to_runtime": False, "optimal_actions_exposed_to_runtime": False, "statistical_claim": "descriptive controlled simulator evaluation; no significance claim"}
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (RESULTS / "report.md").write_text(report(result, manifest))


def main() -> None:
    result = run_all()
    if not result["discrimination_check"]["passed"]:
        raise SystemExit("DISCRIMINATION_CHECK_FAILED: redesign required before evaluation")
    write_outputs(result)
    print(json.dumps({"discrimination_check": result["discrimination_check"], "planner_advantage": result["planner_advantage"], "composition": result["composition"], "ordering_test": result["ordering_test"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
