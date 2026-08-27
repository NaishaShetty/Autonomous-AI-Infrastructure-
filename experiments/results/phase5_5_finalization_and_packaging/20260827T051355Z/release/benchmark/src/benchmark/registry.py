"""Machine-readable task registry loaded from the frozen Phase 5.3 catalog.

Unsupported tasks cannot accidentally execute: evaluate() is gated on
eligibility_status / dataset_coverage_status before any metric is computed.
"""
from __future__ import annotations

from .constants import CANONICAL_SPEC_DIR
from .dataset_loader import load_frozen_spec, task_family
from .status import NOT_EVALUABLE

EXECUTE_ELIGIBLE = {"EVALUABLE", "LIMITED"}
BLOCKED_COVERAGE = {"UNSUPPORTED_CONTRACT_ONLY"}


def load_registry(spec: dict | None = None) -> dict[str, dict]:
    if spec is None:
        spec = load_frozen_spec(CANONICAL_SPEC_DIR)
    tasks = spec["task_catalog"]["tasks"]
    registry = {}
    for t in tasks:
        registry[t["task_id"]] = dict(t)
    if len(registry) != 16:
        raise ValueError(f"expected 16 tasks in catalog, got {len(registry)}")
    return registry


def may_execute(task: dict) -> bool:
    if task.get("eligibility_status") == "NOT_EVALUABLE":
        return False
    if task.get("dataset_coverage_status") in BLOCKED_COVERAGE:
        return False
    return task.get("eligibility_status") in EXECUTE_ELIGIBLE


def not_evaluable_result(task: dict, *, available_evidence: list[str], extra: dict | None = None) -> dict:
    out = {
        "task_id": task["task_id"],
        "track": task["track"],
        "status": NOT_EVALUABLE,
        "reason": task.get("unavailable_evidence"),
        "required_evidence": task.get("decision_time_available_information"),
        "available_evidence": available_evidence,
        "eligibility_status": task.get("eligibility_status"),
        "dataset_coverage_status": task.get("dataset_coverage_status"),
        "metrics": None,
        "baseline_results": None,
        "sample_count": 0,
        "limitations": [task.get("unavailable_evidence")],
    }
    if extra:
        out.update(extra)
    return out


def select_records(records: list[dict], task: dict) -> list[dict]:
    sel = task["source_record_selector"]
    track_filter = sel.get("track_filter")
    family_filter = sel.get("task_family_filter")
    failure_filter = sel.get("failure_class_filter")
    additional = sel.get("additional_predicate")
    out: list[dict] = []
    for r in records:
        ident = r.get("identity") or {}
        if track_filter and ident.get("track") != track_filter:
            continue
        if family_filter:
            if task_family(r) != family_filter:
                continue
        if failure_filter:
            fc = (r.get("failure") or {}).get("failure_class")
            if failure_filter == "not NONE":
                if fc in (None, "NONE"):
                    continue
            elif "not present" in str(failure_filter).lower():
                continue
            elif "," in str(failure_filter):
                allowed = {p.strip() for p in str(failure_filter).split(",")}
                if fc not in allowed:
                    continue
            else:
                token = str(failure_filter).split()[0]
                if fc != token:
                    continue
        if additional:
            if additional == "diagnosis field present" and not r.get("diagnosis"):
                continue
            if additional == "recovery field present" and not r.get("recovery"):
                continue
            if "environment_id != UNSPECIFIED_PRE_4_9" in str(additional):
                if ident.get("environment_id") == "UNSPECIFIED_PRE_4_9":
                    continue
            if "workload_id appears more than once" in str(additional):
                continue  # enforced by caller with a frequency map
        out.append(r)
    out.sort(key=lambda r: r["identity"]["record_id"])
    return out
