"""Capability-matrix reporting. No single overall benchmark score is ever
computed (PHASE5_3_BENCHMARK_SPECIFICATION.md does not define one)."""
from __future__ import annotations

from .status import (
    COMPLETED,
    LIMITED,
    NOT_EVALUABLE,
    SIMULATED_POLICY_EVALUATION,
    UNDERPOWERED,
)

CAP_VALIDATED = "VALIDATED"
CAP_PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
CAP_DESCRIPTIVE = "DESCRIPTIVE"
CAP_UNDERPOWERED = "UNDERPOWERED"
CAP_NOT_VALIDATED = "NOT_VALIDATED"
CAP_NOT_EVALUABLE = "NOT_EVALUABLE"


def _auroc_excludes_chance(metrics: dict, key: str = "MET-AUROC") -> bool | None:
    m = metrics.get(key)
    if not isinstance(m, dict) or m.get("value") is None:
        return None
    ci = m.get("ci") or {}
    lo = ci.get("ci_low")
    if lo is None:
        return m["value"] > 0.55  # weak fallback if CI missing
    return lo > 0.5


def classify_capability(task_id: str, result: dict) -> dict:
    status = result.get("status")
    metrics = result.get("metrics") or {}
    primary_metric = None
    evidence = f"n={result.get('sample_count')}"

    if status == NOT_EVALUABLE:
        return {"status": CAP_NOT_EVALUABLE, "evidence": evidence, "primary_metric": None}

    if status == UNDERPOWERED:
        return {"status": CAP_UNDERPOWERED, "evidence": evidence, "primary_metric": None}

    if task_id in ("UNC-ARITH", "UNC-SENT", "UNC-QA"):
        excludes = _auroc_excludes_chance(metrics)
        primary_metric = metrics.get("MET-AUROC", {}).get("value")
        if excludes is True:
            return {"status": CAP_VALIDATED, "evidence": evidence, "primary_metric": primary_metric}
        if excludes is False:
            return {"status": CAP_NOT_VALIDATED, "evidence": evidence, "primary_metric": primary_metric}
        return {"status": CAP_DESCRIPTIVE, "evidence": evidence, "primary_metric": primary_metric}

    if status == SIMULATED_POLICY_EVALUATION:
        return {
            "status": CAP_PARTIALLY_VALIDATED,
            "evidence": f"{evidence}; simulated policy only, no realized abstain/retry episodes",
            "primary_metric": metrics.get("MET-SELECTIVE-RISK", {}).get("value"),
        }

    if status == LIMITED:
        return {
            "status": CAP_PARTIALLY_VALIDATED,
            "evidence": evidence,
            "primary_metric": None,
        }

    if status == COMPLETED:
        # DIAG-EVAL / REC-EVAL etc: dataset_coverage_status for these tracks is
        # PARTIALLY_SUPPORTED per PHASE5_3_DATASET_COVERAGE.json (small n,
        # several per-class slices UNDERPOWERED) -- a task-level COMPLETED run
        # is reported PARTIALLY_VALIDATED at the capability-matrix level, never
        # promoted to VALIDATED merely because the code executed without error.
        return {"status": CAP_PARTIALLY_VALIDATED, "evidence": evidence, "primary_metric": None}

    return {"status": CAP_DESCRIPTIVE, "evidence": evidence, "primary_metric": None}


def build_capability_matrix(all_results: dict[str, dict]) -> list[dict]:
    rows = []
    for task_id, result in all_results.items():
        cap = classify_capability(task_id, result)
        rows.append(
            {
                "task_id": task_id,
                "track": result.get("track"),
                "status": cap["status"],
                "evidence": cap["evidence"],
                "primary_metric": cap["primary_metric"],
                "limitations": (result.get("limitations") or [])[:2],
            }
        )
    rows.sort(key=lambda r: r["task_id"])
    return rows


def bucket_results(all_results: dict[str, dict]) -> dict[str, list[str]]:
    buckets = {
        "VALIDATED": [],
        "LIMITED": [],
        "UNDERPOWERED": [],
        "DESCRIPTIVE": [],
        "NOT_EVALUABLE": [],
        "NEGATIVE": [],
        "AGGREGATE_REFERENCE": [],
    }
    for task_id, result in all_results.items():
        status = result.get("status")
        cap = classify_capability(task_id, result)["status"]
        if result.get("aggregate_reference_evidence") is not None:
            buckets["AGGREGATE_REFERENCE"].append(task_id)
        if status == NOT_EVALUABLE:
            buckets["NOT_EVALUABLE"].append(task_id)
        elif status == UNDERPOWERED:
            buckets["UNDERPOWERED"].append(task_id)
        elif cap == CAP_NOT_VALIDATED:
            buckets["NEGATIVE"].append(task_id)
        elif cap == CAP_VALIDATED:
            buckets["VALIDATED"].append(task_id)
        elif cap == CAP_PARTIALLY_VALIDATED:
            buckets["LIMITED"].append(task_id)
        else:
            buckets["DESCRIPTIVE"].append(task_id)
    return buckets
