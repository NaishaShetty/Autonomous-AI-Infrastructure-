"""Phase 5.3 ablation matrix (5 ablations).

Only ABL-UNCERTAINTY-MECHANISM and ABL-CALIBRATED-VS-GENERIC-POLICY are
re-runnable from the current canonical dataset (they operate on the 3,060
agent_task records). ABL-MEMORY-ON-OFF, ABL-RETRY-ON-OFF, and
ABL-PREDICTOR-ON-OFF are historical/aggregate findings not re-derivable at
record level from this dataset -- they are reported as
AGGREGATE_REFERENCE_EVIDENCE, never re-computed from scratch.
"""
from __future__ import annotations

import numpy as np

from . import baselines as B
from . import metrics as M
from .constants import AGGREGATE_REFERENCE, TASK_FAMILY_BY_UNC_TASK
from .dataset_loader import confidence_value
from .registry import select_records
from .status import AGGREGATE_REFERENCE_EVIDENCE, CONFOUNDED, NOT_IDENTIFIABLE

ABLATION_IDS = [
    "ABL-UNCERTAINTY-MECHANISM",
    "ABL-CALIBRATED-VS-GENERIC-POLICY",
    "ABL-MEMORY-ON-OFF",
    "ABL-RETRY-ON-OFF",
    "ABL-PREDICTOR-ON-OFF",
]


def _family_xy(records: list[dict], task: dict, split: str):
    sel = [r for r in select_records(records, task) if r["split_assignment"] == split]
    y = np.array([1 if r["agent_output"]["is_correct"] else 0 for r in sel], dtype=int)
    s = np.array([confidence_value(r) for r in sel], dtype=float)
    return y, s


def run_ablation_uncertainty_mechanism(registry: dict, records: list[dict]) -> dict:
    per_family = {}
    for unc_task_id in ("UNC-ARITH", "UNC-SENT", "UNC-QA"):
        task = registry[unc_task_id]
        y, s = _family_xy(records, task, "test")
        on_result = M.risk_coverage(s, y)
        off_result = M.risk_coverage(B.ctrl_constant_score(len(y), 0.5), y)
        per_family[unc_task_id] = {
            "family": TASK_FAMILY_BY_UNC_TASK[unc_task_id],
            "ON_selective_risk_AURC": on_result["value"],
            "OFF_selective_risk_AURC": off_result["value"],
            "delta": (on_result["value"] - off_result["value"]) if on_result["value"] is not None and off_result["value"] is not None else None,
            "n": len(y),
        }
    return {
        "ablation_id": "ABL-UNCERTAINTY-MECHANISM",
        "status": "COMPLETED",
        "per_family": per_family,
        "causal_vs_correlational_status": (
            "CAUSAL for arithmetic and QA (removing the signal flattens the risk-coverage curve to "
            "base rate); CORRELATIONAL-ONLY-AT-CEILING for sentiment (AUROC ~0.66, barely above chance) "
            "-- disclosed per spec, not hidden."
        ),
    }


def run_ablation_calibrated_vs_generic(registry: dict, records: list[dict]) -> dict:
    from .tasks import fit_generic_policy_threshold

    generic_threshold = fit_generic_policy_threshold(records, registry)
    per_family = {}
    for unc_task_id in ("UNC-ARITH", "UNC-SENT", "UNC-QA"):
        task = registry[unc_task_id]
        y_calib, s_calib = _family_xy(records, task, "calibration_validation")
        y_test, s_test = _family_xy(records, task, "test")
        calibrated_t = B.fit_threshold_maximizing_margin(s_calib, y_calib.astype(bool))
        calibrated_policy = B.apply_threshold_policy(s_test, calibrated_t)
        generic_policy = B.apply_threshold_policy(s_test, generic_threshold)
        is_answer_cal = np.array([a == "ANSWER" for a in calibrated_policy])
        is_answer_gen = np.array([a == "ANSWER" for a in generic_policy])
        risk_cal = M.selective_risk(is_answer_cal, y_test.astype(bool))
        risk_gen = M.selective_risk(is_answer_gen, y_test.astype(bool))
        per_family[unc_task_id] = {
            "calibrated_threshold": calibrated_t,
            "generic_threshold": generic_threshold,
            "calibrated_selective_risk": risk_cal.get("value"),
            "generic_selective_risk": risk_gen.get("value"),
        }
    return {
        "ablation_id": "ABL-CALIBRATED-VS-GENERIC-POLICY",
        "status": "COMPLETED",
        "per_family": per_family,
        "causal_vs_correlational_status": (
            "CAUSAL where families have genuinely different discrimination ceilings -- a single pooled "
            "threshold necessarily mis-serves at least one family."
        ),
    }


_ABLATION_TO_REFERENCE_KEY = {
    "ABL-MEMORY-ON-OFF": "MEM-EVAL",
    "ABL-RETRY-ON-OFF": "ABL-RETRY-ON-OFF",
    "ABL-PREDICTOR-ON-OFF": "ABL-PREDICTOR-ON-OFF",
}


def run_historical_ablation(ablation_id: str) -> dict:
    ref = AGGREGATE_REFERENCE.get(_ABLATION_TO_REFERENCE_KEY.get(ablation_id, ablation_id), {})
    extra_status = None
    if ablation_id == "ABL-PREDICTOR-ON-OFF":
        extra_status = f"{CONFOUNDED}/{NOT_IDENTIFIABLE}"
    return {
        "ablation_id": ablation_id,
        "status": AGGREGATE_REFERENCE_EVIDENCE,
        "extra_status": extra_status,
        "aggregate_reference_evidence": ref,
        "reason": "Not re-derivable at record level from the current canonical dataset "
                  "(no repeated-workload structure / no re-executed retry-off or predictor-off run).",
    }


def run_all_ablations(registry: dict, records: list[dict]) -> dict:
    return {
        "ABL-UNCERTAINTY-MECHANISM": run_ablation_uncertainty_mechanism(registry, records),
        "ABL-CALIBRATED-VS-GENERIC-POLICY": run_ablation_calibrated_vs_generic(registry, records),
        "ABL-MEMORY-ON-OFF": run_historical_ablation("ABL-MEMORY-ON-OFF"),
        "ABL-RETRY-ON-OFF": run_historical_ablation("ABL-RETRY-ON-OFF"),
        "ABL-PREDICTOR-ON-OFF": run_historical_ablation("ABL-PREDICTOR-ON-OFF"),
    }
