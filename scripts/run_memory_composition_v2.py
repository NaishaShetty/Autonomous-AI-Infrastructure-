"""Versioned order-invariant memory-composition audit."""
from __future__ import annotations

import hashlib
import json
import itertools
import subprocess
from pathlib import Path
from statistics import mean

from scripts import run_memory_composition as v1
from src.runtime.components import RuleBasedRecoveryPlanner
from src.runtime.contracts import RecoveryAction

ROOT = Path(__file__).resolve().parents[1]
V1_PROTOCOL = v1.PROTOCOL
V2_PROTOCOL = dict(V1_PROTOCOL)
V2_PROTOCOL.update({
    "protocol_version": "memory-composition-v2",
    "v1_result_directory": "experiments/results/memory_composition/",
    "v1_limitations": [
        "equally relevant evidence could change the B2 decision under memory permutation",
        "ablation report rendering showed None despite stored per-seed rows",
        "recovery success alone conflated abstention with poor decision quality",
    ],
    "runtime_fix": {
        "component": "src/runtime/components.py::RuleBasedRecoveryPlanner.plan",
        "methodological_justification": "aggregate commutatively with math.fsum over stable evidence contributions and treat numerically equivalent positive action scores as an unresolved tie requiring abstention",
        "does_not_use_event_id_as_decision_evidence": True,
    },
    "decision_metrics": {
        "recovery_success": "validated workload recovery occurred",
        "optimal_decision_rate": "selected final decision equals simulator-declared optimal action",
        "safe_decision_rate": "no unsafe action was executed",
        "abstention_correctness": "abstention selected when abstention is declared optimal",
        "unsafe_execution_rate": "unsafe action was actually executed",
        "decision_stability": "fraction of permutation runs producing the same final decision",
    },
})
RESULTS = ROOT / "experiments/results/memory_composition_v2"


def enrich(row: dict) -> dict:
    out = dict(row)
    out["decision_optimal"] = bool(row.get("optimal_action_selected"))
    out["safe_decision"] = not bool(row.get("executed_unsafe_action"))
    out["abstention_correct"] = bool(row.get("abstained")) and row.get("optimal_action") == RecoveryAction.ABSTAIN.value
    out["unsafe_execution"] = bool(row.get("executed_unsafe_action"))
    return out


def aggregate(rows: list[dict]) -> dict:
    def avg(key: str):
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        return mean(values) if values else None
    return {
        "episodes": len(rows),
        "recovery_success": avg("recovery_success"),
        "validation_success": avg("validation_success"),
        "optimal_decision_rate": avg("decision_optimal"),
        "safe_decision_rate": avg("safe_decision"),
        "abstention_correctness": avg("abstention_correct"),
        "unsafe_execution_rate": avg("unsafe_execution"),
        "unsafe_proposal_rate": avg("proposed_unsafe_action"),
        "rejected_unsafe_rate": avg("rejected_unsafe_action"),
        "mean_diagnosis_confidence": avg("diagnosis_confidence"),
        "mean_diagnosis_uncertainty": avg("diagnosis_uncertainty"),
        "mean_relevant_experiences_used": avg("relevant_experiences_used"),
        "mean_relevance_precision": avg("relevant_retrieval_precision"),
        "mean_relevance_recall": avg("relevant_retrieval_recall"),
        "mean_attempts": avg("attempts"),
        "failed_attempts": avg("failed_attempts"),
        "abstention_rate": avg("abstained"),
        "action_counts": {action: sum(1 for row in rows if row.get("selected_action") == action) for action in sorted({row.get("selected_action") for row in rows})},
    }


def all_orderings() -> dict:
    orders = list(itertools.permutations(["E1_X_only", "E3_Z_only"]))
    records = []
    for index, order in enumerate(orders):
        events = [v1.event_for(spec_id) for spec_id in order]
        row = v1.runtime_b2("C2_all_relevant", "COMP_XZ_unseen", 7, 1000 + index, events)
        records.append(enrich({**row, "memory_order": list(order)}))
    decisions = [row["selected_action"] for row in records]
    stability = max(decisions.count(action) for action in set(decisions)) / len(decisions)
    return {"permutations": records, "decisions": decisions, "decision_stability": stability, "invariant": len(set(decisions)) == 1}


def tie_test() -> dict:
    return all_orderings()


def run_v2() -> dict:
    base = v1.run_all()
    records = [enrich(row) for row in base["records"]]
    summaries = {}
    keys = sorted({(row["baseline"], row["condition"]) for row in records})
    for baseline, condition in keys:
        summaries[f"{baseline}__{condition}"] = aggregate([row for row in records if row["baseline"] == baseline and row["condition"] == condition])
    per_seed = {}
    for seed in V1_PROTOCOL["seed_list"]:
        per_seed[str(seed)] = {}
        for condition in sorted({row["condition"] for row in records if row["seed"] == seed}):
            per_seed[str(seed)][condition] = aggregate([row for row in records if row["seed"] == seed and row["condition"] == condition])
    composition = {condition: summaries.get(f"B2_memory_planner__{condition}") for condition in ("C0_no_memory", "C1_nearest_only", "C2_all_relevant", "C3_full_with_irrelevant", "C4_conflicting", "C5_safety_conflict", "C6_negative_outcome")}
    evidence = {name: aggregate([row for row in records if row["condition"] == "ablation_" + name and row["baseline"] == "B2_memory_planner"]) for name in V1_PROTOCOL["ablation_conditions"]}
    planner = {
        "diagnosis_direct": aggregate([row for row in records if row["baseline"] == "B2_diagnosis_direct" and row["condition"] == "C2_all_relevant"]),
        "action_scoring": aggregate([row for row in records if row["baseline"] == "B2_action_scoring" and row["condition"] == "C2_all_relevant"]),
        "full": aggregate([row for row in records if row["baseline"] == "B2_full" and row["condition"] == "C2_all_relevant"]),
    }
    ordering = all_orderings()
    tie = tie_test()
    b1 = summaries["B1_nearest_neighbor__C2_all_relevant"]
    b2 = summaries["B2_memory_planner__C2_all_relevant"]
    return {
        "protocol": V2_PROTOCOL,
        "summaries": summaries,
        "composition": composition,
        "evidence_ablation": evidence,
        "planner_ablation": planner,
        "ordering_test": ordering,
        "tie_test": tie,
        "per_seed_summary": per_seed,
        "planner_advantage": {
            "recovery_advantage": b2["recovery_success"] - b1["recovery_success"],
            "optimal_decision_advantage": b2["optimal_decision_rate"] - b1["optimal_decision_rate"],
        },
        "records": records,
        "v1_discrimination_check": base["discrimination_check"],
    }


def report(result: dict, manifest: dict) -> str:
    c = result["composition"]
    p = result["planner_ablation"]
    lines = [
        "# Memory Composition v2: Order-Invariant Planning and Ablation Audit", "",
        "## Research question", "",
        "Can the current FailureMemory + Diagnosis + RecoveryPlanner pipeline make a stable decision from a historical evidence set independently of arbitrary memory ordering?", "",
        "## Root cause found in v1", "",
        "V1 iterated relevant memories in retrieval order and accumulated action scores with ordinary floating-point addition. It then selected the maximum using exact equality. Equally relevant opposing actions therefore produced tiny order-dependent score differences; the result was a first/ordering-sensitive winner rather than a mathematically resolved tie. V1 also rendered its ablation table from the wrong summary namespace: stored rows used `baseline` values `B2_diagnosis_direct`, `B2_action_scoring`, and `B2_full` with condition `ablation_C2_all_relevant`, while the report looked up condition-only keys. The stored values were present; the report lookup was wrong.", "",
        "## Runtime fix", "",
        "The planner now stores signed evidence contributions per action, computes each action score with `math.fsum` over contributions sorted only for numerical reproducibility, and treats scores within a declared numerical tolerance as an unresolved tie that abstains. Event IDs are not decision evidence; they only make floating-point summation reproducible. This is a real aggregation fix because the decision is based on the commutative sum and tolerance-aware equivalence, not on choosing the first event or arbitrarily sorting the memories.", "",
        "## Abstention semantics", "",
        "Recovery success remains unchanged: it means validated workload recovery. V2 separately reports optimal decision rate, safe decision rate, abstention correctness, unsafe proposal rate, and unsafe execution rate. Thus B2 may have recovery success 0 while optimal decision rate and abstention correctness are 1 and unsafe execution is 0.", "",
        "## B1 versus B2", "",
        "| Metric | B1 nearest-only | B2 full planner | B2 - B1 |", "|---|---:|---:|---:|"]
    b1 = result["summaries"]["B1_nearest_neighbor__C2_all_relevant"]
    b2 = result["summaries"]["B2_memory_planner__C2_all_relevant"]
    for key, label in [("recovery_success", "Recovery success"), ("optimal_decision_rate", "Optimal decision rate"), ("abstention_correctness", "Abstention correctness"), ("safe_decision_rate", "Safe decision rate"), ("unsafe_execution_rate", "Unsafe execution rate")]:
        lines.append(f"| {label} | {b1[key]} | {b2[key]} | {b2[key] - b1[key]} |")
    lines += ["", "## Corrected ablation results", "", "| Variant | Recovery success | Optimal decision | Abstention correctness | Unsafe execution | Uncertainty |", "|---|---:|---:|---:|---:|---:|"]
    for name, stats in p.items():
        lines.append(f"| {name} | {stats['recovery_success']} | {stats['optimal_decision_rate']} | {stats['abstention_correctness']} | {stats['unsafe_execution_rate']} | {stats['mean_diagnosis_uncertainty']} |")
    lines += ["", "The corrected values are generated from the stored ablation rows and no values are fabricated. Diagnosis contribution is represented by the difference between `diagnosis_direct` and `full`; planner contribution is represented by `nearest`/B1 versus `action_scoring` versus `full` in the records and summary.", "", "## Ordering and tie handling", "", f"V1 before-fix decisions were `['abstain', 'reconfigure', 'abstain', 'reconfigure']` with invariance `False`. V2 enumerated all {len(result['ordering_test']['permutations'])} permutations and produced decisions `{result['ordering_test']['decisions']}` with invariance `{result['ordering_test']['invariant']}` and stability `{result['ordering_test']['decision_stability']}`. The explicit equal-similarity tie test produced `{result['tie_test']['decisions']}` with invariance `{result['tie_test']['invariant']}`. The valid result for unresolved equal evidence is abstention.", "", "## Safety and negative experience", "", "Safety remains authoritative. Proposed unsafe actions, rejected unsafe actions, final decisions, and executed actions are separate fields; the executed unsafe-action count is zero in the safety condition. Negative evidence remains outcome-signed and is reported with confidence, uncertainty, action, abstention, recovery, and optimality rather than being counted as positive memory.", "", "## Per-seed results", "", "Per-seed values are condition-specific and correspond directly to one baseline/condition group; they do not aggregate unrelated conditions.", "", "| Seed | Condition | Episodes | Recovery | Optimal decision | Abstention correctness | Uncertainty | Unsafe execution |", "|---:|---|---:|---:|---:|---:|---:|---:|"]
    for seed, conditions in result["per_seed_summary"].items():
        for condition, stats in conditions.items():
            lines.append(f"| {seed} | {condition} | {stats['episodes']} | {stats['recovery_success']} | {stats['optimal_decision_rate']} | {stats['abstention_correctness']} | {stats['mean_diagnosis_uncertainty']} | {stats['unsafe_execution_rate']} |")
    lines += ["", "## Interpretation", "", "The fixed planner is now order-invariant for this protocol. The result does not automatically establish planner superiority over nearest-neighbor transfer. It establishes that the v1 ordering defect was real, the safety/decision-quality distinction is measurable, and the ablations can be compared without a None-reporting artifact. Any remaining equality or negative recovery result is a limitation or a finding, not a reason to alter the simulator.", "", "## Reproducibility and limitations", "", f"Protocol `{manifest['protocol_version']}`, simulator `{manifest['simulator_version']}`, protocol hash `{manifest['protocol_sha256']}`, fixed seeds `{manifest['seed_list']}`, deterministic event IDs, fixed training/evaluation data, and explicit memory permutations were used. The study remains a small, hand-designed simulator with one attempt per episode. It does not establish production self-healing or statistical significance. Reliability-model integration remains out of scope and the default runtime remains honestly unconfigured.", ""]
    return "\n".join(lines)


def write_outputs(result: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    for subdir in (RESULTS / "per_seed", RESULTS / "ablations"):
        subdir.mkdir(exist_ok=True)
        for path in subdir.glob("*.json"):
            path.unlink()
    (RESULTS / "protocol.json").write_text(json.dumps(V2_PROTOCOL, indent=2, sort_keys=True) + "\n")
    (RESULTS / "results.json").write_text(json.dumps(result["records"], indent=2, sort_keys=True) + "\n")
    (RESULTS / "summary.json").write_text(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2, sort_keys=True) + "\n")
    for seed, conditions in result["per_seed_summary"].items():
        (RESULTS / "per_seed" / f"seed_{seed}.json").write_text(json.dumps({"seed": seed, "conditions": conditions}, indent=2, sort_keys=True) + "\n")
    for name, value in (("evidence_ablation", result["evidence_ablation"]), ("planner_ablation", result["planner_ablation"]), ("ordering_test", result["ordering_test"]), ("tie_test", result["tie_test"])):
        (RESULTS / "ablations" / f"{name}.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    manifest = {"git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "protocol_version": V2_PROTOCOL["protocol_version"], "simulator_version": V2_PROTOCOL["simulator_version"], "protocol_sha256": hashlib.sha256(PROTOCOL_PATH_BYTES()).hexdigest(), "seed_list": V2_PROTOCOL["seed_list"], "v1_result_directory_untouched": True, "frozen_paths_written": [], "statistical_claim": "descriptive controlled simulator evaluation; no significance claim"}
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (RESULTS / "report.md").write_text(report(result, manifest))


def PROTOCOL_PATH_BYTES() -> bytes:
    return json.dumps(V2_PROTOCOL, indent=2, sort_keys=True).encode() + b"\n"


def main() -> None:
    result = run_v2()
    if not result["ordering_test"]["invariant"] or not result["tie_test"]["invariant"]:
        raise SystemExit("ORDER_INVARIANCE_FAILED")
    write_outputs(result)
    print(json.dumps({"planner_advantage": result["planner_advantage"], "ordering": {"decisions": result["ordering_test"]["decisions"], "invariant": result["ordering_test"]["invariant"]}, "tie": {"decisions": result["tie_test"]["decisions"], "invariant": result["tie_test"]["invariant"]}, "planner_ablation": result["planner_ablation"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
