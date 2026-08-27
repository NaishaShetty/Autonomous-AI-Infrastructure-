"""Executable leakage enforcement. Fail closed: never produce a score on violation."""
from __future__ import annotations

from .constants import EVALUATION_SPLIT
from .status import FAILED_VALIDATION


class LeakageError(Exception):
    def __init__(self, rule: str, message: str, record_id: str | None = None):
        self.rule = rule
        self.message = message
        self.record_id = record_id
        super().__init__(f"{rule}: {message}")


def leakage_failure(rule: str, message: str, record_id: str | None = None) -> dict:
    return {
        "status": FAILED_VALIDATION,
        "reason": message,
        "rule": rule,
        "record_id": record_id,
        "metrics": None,
    }


def check_hidden_fields_not_in_input(input_obj: dict, prohibited_fields: list[str]) -> None:
    """L1: input must not contain leaked/hidden fields (exact or dotted prefixes)."""
    keys = set(_flatten_keys(input_obj))
    for field in prohibited_fields:
        leaf = field.split(".")[-1]
        if field in keys or leaf in keys:
            raise LeakageError("L1", f"prohibited field {field} present in input")


def _flatten_keys(obj, prefix: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            out.append(path)
            out.extend(_flatten_keys(v, path))
    return out


def check_prediction_no_post_failure_input(input_obj: dict) -> None:
    """L2: prediction inputs must not include post-failure / diagnosis / recovery."""
    banned = (
        "failure_detected",
        "suspected_cause",
        "validation_status",
        "executor_self_report",
        "is_correct",
        "correct_answer",
        "outcome_class",
    )
    flat = set(_flatten_keys(input_obj))
    leaves = {p.split(".")[-1] for p in flat}
    for b in banned:
        if b in leaves:
            raise LeakageError("L2", f"post-failure or label field {b} in prediction input")


def check_recovery_action_selection_input(input_obj: dict) -> None:
    """L3: action-selection must not see validation/self-report outcomes."""
    banned = ("validation_status", "executor_self_report")
    leaves = {p.split(".")[-1] for p in _flatten_keys(input_obj)}
    for b in banned:
        if b in leaves:
            raise LeakageError("L3", f"recovery outcome field {b} in action-selection input")


def check_diagnosis_not_used_as_ground_truth(label: dict) -> None:
    """L4: diagnosis output is never ground truth."""
    lt = label.get("label_type")
    if lt == "MODEL_DIAGNOSIS":
        raise LeakageError("L4", "MODEL_DIAGNOSIS used as ground-truth label")


def check_executor_self_report_not_label(used_self_report: bool) -> None:
    """L5: executor self-report never substitutes for validation_status."""
    if used_self_report:
        raise LeakageError("L5", "executor_self_report used as recovery/e2e label")


class FitAudit:
    """L6 / L11 / L12: record every fit; reject test-split peeking."""

    def __init__(self):
        self.events: list[dict] = []
        self.test_results_inspected_for_tuning = False
        self.feature_selection_on_test = False

    def record_fit(self, *, purpose: str, split: str, n: int) -> None:
        if split == EVALUATION_SPLIT:
            raise LeakageError("L6", f"fit '{purpose}' used test-split instances (n={n})")
        self.events.append({"purpose": purpose, "split": split, "n": n})

    def mark_test_tuned(self) -> None:
        self.test_results_inspected_for_tuning = True
        raise LeakageError("L11", "threshold/hyperparameter tuned against test-split results")

    def mark_feature_selection_on_test(self) -> None:
        self.feature_selection_on_test = True
        raise LeakageError("L12", "feature selection based on test-split results")


def check_held_out_not_used_for_fit(environment_roles: list[str]) -> None:
    """L7: held_out/robustness never used for fitting."""
    bad = {r for r in environment_roles if r in ("held_out", "robustness")}
    if bad:
        raise LeakageError("L7", f"held_out/robustness roles used for fitting: {sorted(bad)}")


def check_repeated_workload_same_split(records: list[dict]) -> None:
    """L8: a repeated-workload sequence must not span forbidden split boundaries."""
    from collections import defaultdict

    wl = defaultdict(set)
    for r in records:
        wl[r["identity"]["workload_id"]].add(r.get("split_assignment"))
    crossing = {k: sorted(v) for k, v in wl.items() if len(v) > 1}
    if crossing:
        raise LeakageError("L8", f"repeated workload_id spans splits: {list(crossing.items())[:5]}")


def check_memory_temporal(query_decision_time: str | None, recorded_at: str | None) -> None:
    """L9: memory recorded_at must not postdate query decision_time."""
    if query_decision_time is None or recorded_at is None:
        return
    if recorded_at > query_decision_time:
        raise LeakageError("L9", "memory recorded_at after querying decision_time")


def check_gen3_only(dataset_version: str) -> None:
    """L10: Gen-3 / Phase 5.2 canonical dataset exclusively."""
    if dataset_version != "phase5.2-dataset-v1.0.0":
        raise LeakageError("L10", f"non-canonical dataset_version {dataset_version}")


def pre_evaluation_leakage_scan(records: list[dict], dataset_version: str) -> dict:
    """Run mechanically checkable L-rules over the evaluation population."""
    check_gen3_only(dataset_version)
    check_repeated_workload_same_split(records)
    roles = [r.get("identity", {}).get("environment_role") for r in records]
    # Fitting is not happening in this scan; L7 is checked at fit time.
    n_test = sum(1 for r in records if r.get("split_assignment") == EVALUATION_SPLIT)
    return {
        "status": "PASSED",
        "n_records_scanned": len(records),
        "n_test": n_test,
        "environment_roles": sorted({r for r in roles if r}),
        "rules_checked": ["L8", "L10"],
    }
