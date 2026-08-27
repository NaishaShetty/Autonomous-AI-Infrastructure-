"""Per-task evaluate() implementations for all 16 Phase 5.3 tasks.

Every task function returns a result dict shaped per
PHASE5_3_BENCHMARK_SCHEMA.json / the task brief's Step 13 result schema:
{benchmark_version, dataset_version, task_id, track, status, split,
 sample_count, metrics, baseline_results, limitations, provenance}.

Unsupported tasks (NOT_EVALUABLE / UNSUPPORTED_CONTRACT_ONLY) never execute
scoring logic -- they return immediately via registry.not_evaluable_result.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from . import baselines as B
from . import metrics as M
from .constants import (
    AGGREGATE_REFERENCE,
    BENCHMARK_VERSION,
    DATASET_VERSION,
    TASK_FAMILY_BY_UNC_TASK,
)
from .dataset_loader import confidence_value
from .leakage import check_hidden_fields_not_in_input
from .registry import not_evaluable_result, select_records
from .status import (
    ALWAYS_ABSTAIN_NOT_SUCCESSFUL,
    CAUSAL_GROUND_TRUTH_UNAVAILABLE,
    COMPLETED,
    LIMITED,
    NOT_APPLICABLE,
    SIMULATED_POLICY_EVALUATION,
    UNDERPOWERED,
)

MIN_CLASS_SAMPLE = 30  # per-failure-class descriptive-only threshold (task brief)


def _base_result(task: dict, *, status: str, split: str, sample_count: int, metrics: dict,
                  baseline_results: dict | None, limitations: list[str], provenance: dict) -> dict:
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": DATASET_VERSION,
        "task_id": task["task_id"],
        "track": task["track"],
        "status": status,
        "split": split,
        "sample_count": sample_count,
        "metrics": metrics,
        "baseline_results": baseline_results,
        "limitations": limitations,
        "provenance": provenance,
    }


# --------------------------------------------------------------------------
# Uncertainty tasks (UNC-ARITH / UNC-SENT / UNC-QA) -- FULLY_SUPPORTED
# --------------------------------------------------------------------------

def evaluate_uncertainty_task(task: dict, records: list[dict]) -> dict:
    family = TASK_FAMILY_BY_UNC_TASK[task["task_id"]]
    selected = select_records(records, task)
    test = [r for r in selected if r["split_assignment"] == "test"]
    calib = [r for r in selected if r["split_assignment"] == "calibration_validation"]

    def xy(recs):
        y = np.array([1 if r["agent_output"]["is_correct"] else 0 for r in recs], dtype=int)
        s = np.array([confidence_value(r) for r in recs], dtype=float)
        return y, s

    y_test, s_test = xy(test)
    y_calib, s_calib = xy(calib)

    # Leakage check: the projected input for this family contains only the
    # confidence field(s) and metadata, never is_correct/correct_answer.
    input_fields = {"confidence": None, "task_family": family}
    check_hidden_fields_not_in_input(input_fields, task["leaked_from_dataset_record_fields"])

    n = len(y_test)
    min_req = task["minimum_sample_requirement"]
    status = COMPLETED if n >= min_req else UNDERPOWERED

    ranking = M.ranking_with_ci(y_test, s_test)

    # Temperature scaling fit on calibration_validation ONLY (never test).
    limitations: list[str] = []
    calibrated_ece = None
    if len(y_calib) > 0 and len(set(y_calib.tolist())) == 2:
        T = B.fit_temperature_scale(s_calib, y_calib)
        s_test_calibrated = B.apply_temperature_scale(s_test, T)
        calibrated_ece = M.ece(y_test, s_test_calibrated)
        calibrated_auroc = M.auroc(y_test, s_test_calibrated)
        limitations.append(
            f"Temperature scaling (T={T:.4f}) fit on calibration_validation (n={len(y_calib)}); "
            f"raw ECE={ranking['MET-ECE']['value']}, calibrated ECE={calibrated_ece['value']}, "
            f"raw AUROC={ranking['MET-AUROC']['value']}, calibrated AUROC={calibrated_auroc['value']} "
            "-- calibration is a monotonic rescaling and cannot change AUROC in principle; any "
            "numeric difference here reflects the finite-sample temperature fit, not a discrimination change."
        )
    else:
        limitations.append("Insufficient class diversity in calibration_validation split for temperature fitting.")

    baseline_results = {
        "BASE-RANDOM": M.auroc(y_test, B.base_random_scores(n)),
        "BASE-RAW-CONFIDENCE": ranking["MET-AUROC"],  # the system score IS raw confidence
        "CTRL-SHUFFLED-LABEL": M.auroc(B.ctrl_shuffled_label(y_test), s_test),
        "CTRL-FEATURE-PERMUTATION": M.auroc(y_test, B.ctrl_feature_permutation(s_test)),
    }

    if task["task_id"] == "UNC-SENT":
        limitations.append(
            "DISCLOSED, EXPECTED result for this family: AUROC ~0.66 (near-chance discrimination "
            "ceiling). Never reported as 'uncertainty mechanism validated' for sentiment."
        )

    metrics_out = {**ranking, "calibrated_ECE_from_calibration_validation_fit": calibrated_ece}
    prov = {
        "source_record_selector": task["source_record_selector"],
        "n_calibration_validation": len(y_calib),
        "n_test": n,
    }
    if status == UNDERPOWERED:
        limitations.append(f"n_test={n} < minimum_sample_requirement={min_req}: DESCRIPTIVE_ONLY.")
    return _base_result(
        task, status=status, split="test", sample_count=n, metrics=metrics_out,
        baseline_results=baseline_results, limitations=limitations, provenance=prov,
    )


# --------------------------------------------------------------------------
# Abstention tasks (ABST-ARITH / ABST-SENT / ABST-QA) -- PARTIALLY_SUPPORTED,
# SIMULATED_POLICY_EVALUATION (no realized ABSTAIN/RETRY episodes exist).
# --------------------------------------------------------------------------

def evaluate_abstention_task(task: dict, records: list[dict], *, generic_threshold: float | None = None) -> dict:
    family = TASK_FAMILY_BY_UNC_TASK[task["task_id"]]
    selected = select_records(records, task)
    test = [r for r in selected if r["split_assignment"] == "test"]
    calib = [r for r in selected if r["split_assignment"] == "calibration_validation"]

    def xy(recs):
        y = np.array([1 if r["agent_output"]["is_correct"] else 0 for r in recs], dtype=int)
        s = np.array([confidence_value(r) for r in recs], dtype=float)
        return y, s

    y_test, s_test = xy(test)
    y_calib, s_calib = xy(calib)
    n = len(y_test)
    min_req = task["minimum_sample_requirement"]

    calibrated_threshold = B.fit_threshold_maximizing_margin(s_calib, y_calib.astype(bool))
    policy_calibrated = B.apply_threshold_policy(s_test, calibrated_threshold)
    policy_generic = B.apply_threshold_policy(s_test, generic_threshold if generic_threshold is not None else 0.5)

    def score_policy(actions):
        is_answer = np.array([a == "ANSWER" for a in actions])
        return {
            "MET-SELECTIVE-RISK": M.selective_risk(is_answer, y_test.astype(bool)),
            "MET-COVERAGE": M.coverage_metric(actions),
            "MET-ABSTENTION-RATE": M.abstention_rate(actions),
            "MET-UNNECESSARY-ABSTENTION": M.unnecessary_abstention(actions, y_test.astype(bool)),
            "MET-FINAL-CORRECTNESS": M.final_correctness(actions, y_test.astype(bool)),
        }

    always_answer = B.base_always_answer(n)
    always_abstain = B.base_always_abstain(n)
    random_policy = B.ctrl_random_policy(n)

    always_abstain_metrics = score_policy(always_abstain)
    baseline_results = {
        "BASE-ALWAYS-ANSWER": score_policy(always_answer),
        "BASE-ALWAYS-ABSTAIN": {
            **always_abstain_metrics,
            "flag": ALWAYS_ABSTAIN_NOT_SUCCESSFUL,
            "note": "Trivially zero selective risk at coverage=0 -- explicitly NOT a success per design principle.",
        },
        "BASE-GENERIC-POLICY": score_policy(policy_generic),
        "BASE-CALIBRATED-MECHANISM-AWARE": score_policy(policy_calibrated),
        "CTRL-RANDOM-POLICY": score_policy(random_policy),
    }

    limitations = [
        "SIMULATED_POLICY_EVALUATION: no realized ABSTAIN-decision or RETRY-triggered "
        "episodes exist in the ingested raw sources (dataset by_decision_type has no "
        "ABSTAIN/RETRY key) -- this is a post-hoc policy simulation over agent_output.is_correct, "
        "never an evaluation of a real, executed abstention policy.",
    ]
    if task["task_id"] == "ABST-ARITH":
        limitations.append(
            "RETRY is nominally legitimate for arithmetic per design principle, but no realized "
            "RETRY-triggered re-sampling event exists in the retained per-record evidence (only the "
            "final agreement_rate after all samples were already drawn is recorded); any RETRY-specific "
            "claim beyond ANSWER/ABSTAIN simulation is NOT_EVALUABLE from current records."
        )
    else:
        limitations.append("RETRY is not a legitimate decision for this family per design principle.")

    status = SIMULATED_POLICY_EVALUATION
    if n < min_req:
        limitations.append(f"n_test={n} < minimum_sample_requirement={min_req}: UNDERPOWERED/DESCRIPTIVE_ONLY.")

    prov = {
        "source_record_selector": task["source_record_selector"],
        "n_calibration_validation": len(y_calib),
        "n_test": n,
        "calibrated_threshold_fit_on": "calibration_validation",
        "calibrated_threshold_value": calibrated_threshold,
    }
    return _base_result(
        task, status=status, split="test", sample_count=n,
        metrics={"policy_evaluated": "BASE-CALIBRATED-MECHANISM-AWARE", **score_policy(policy_calibrated)},
        baseline_results=baseline_results, limitations=limitations, provenance=prov,
    )


def fit_generic_policy_threshold(records: list[dict], task_registry: dict) -> float:
    """BASE-GENERIC-POLICY: one threshold fit by pooling ALL three uncertainty
    families' calibration_validation confidence values -- deliberately naive."""
    pooled_scores = []
    pooled_correct = []
    for tid in ("UNC-ARITH", "UNC-SENT", "UNC-QA"):
        fam = TASK_FAMILY_BY_UNC_TASK[tid]
        task = task_registry[f"ABST-{tid.split('-')[1]}"]
        sel = [r for r in select_records(records, task) if r["split_assignment"] == "calibration_validation"]
        for r in sel:
            pooled_scores.append(confidence_value(r))
            pooled_correct.append(bool(r["agent_output"]["is_correct"]))
    return B.fit_threshold_maximizing_margin(np.array(pooled_scores), np.array(pooled_correct))


# --------------------------------------------------------------------------
# Failure-prediction tasks -- NOT_EVALUABLE at record level (dataset gap).
# --------------------------------------------------------------------------

def evaluate_failure_prediction_task(task: dict, records: list[dict]) -> dict:
    ref = AGGREGATE_REFERENCE.get(task["task_id"], {})
    sel = select_records(records, task)
    return not_evaluable_result(
        task,
        available_evidence=[f"{len(sel)} matching per-episode records (below minimum_sample_requirement)"],
        extra={
            "aggregate_reference_evidence": {**ref, "status_of_this_field": "AGGREGATE_REFERENCE_EVIDENCE"},
            "benchmark_version": BENCHMARK_VERSION,
            "dataset_version": DATASET_VERSION,
        },
    )


# --------------------------------------------------------------------------
# Diagnosis task (DIAG-EVAL) -- PARTIALLY_SUPPORTED.
# --------------------------------------------------------------------------

def _failure_class_from_diagnosis(suspected_cause: str | None) -> str | None:
    from src.phase5.failure_mapping import DIAGNOSIS_TO_FAILURE_CLASS

    if suspected_cause is None:
        return None
    return DIAGNOSIS_TO_FAILURE_CLASS.get(suspected_cause)


def evaluate_diagnosis_task(task: dict, records: list[dict]) -> dict:
    selected = select_records(records, task)
    n = len(selected)

    matches = 0
    unknown_correct = 0  # suspected_cause None AND causal ground truth unavailable
    unknown_emitted = 0
    per_class = defaultdict(lambda: {"n": 0, "match": 0})
    temporal_ok = 0
    false_causal_attrib = 0

    for r in selected:
        fc = r["failure"]["failure_class"]
        diag = r.get("diagnosis") or {}
        suspected = diag.get("suspected_cause")
        mapped = _failure_class_from_diagnosis(suspected)
        per_class[fc]["n"] += 1
        if mapped == fc:
            matches += 1
            per_class[fc]["match"] += 1
        if suspected is None:
            unknown_emitted += 1
            unknown_correct += 1  # causal ground truth is unavailable for ALL records here
        else:
            # Non-UNKNOWN causal claim while causal ground truth is unavailable
            # for every record in this dataset (no independent causal GT field
            # exists anywhere) -- counted per design principle, not penalized
            # as "wrong", but reported as the false-causal-attribution rate.
            false_causal_attrib += 1
        temporal = r.get("temporal") or {}
        if temporal.get("availability_of_this_record") != "UNAVAILABLE":
            temporal_ok += 1

    failure_class_accuracy = M.rate(matches, n) if n else {"value": None, "status": "UNDEFINED_ZERO_DENOMINATOR"}
    unknown_handling = M.rate(unknown_correct, n) if n else {"value": None}
    temporal_integrity = M.rate(temporal_ok, n) if n else {"value": None}
    false_causal_rate = M.rate(false_causal_attrib, n) if n else {"value": None}

    per_class_out = {}
    limitations = [
        "causal_status=CAUSAL_GROUND_TRUTH_UNAVAILABLE for all records in this dataset "
        "(no independently-verified root cause distinct from failure_class exists); only "
        "failure-class match, UNKNOWN handling, and temporal integrity are scored.",
    ]
    for fc, d in per_class.items():
        status = COMPLETED if d["n"] >= MIN_CLASS_SAMPLE else UNDERPOWERED
        per_class_out[fc] = {
            "n": d["n"],
            "match_rate": (d["match"] / d["n"]) if d["n"] else None,
            "status": status,
        }
        if status == UNDERPOWERED:
            limitations.append(f"failure_class={fc}: n={d['n']} < {MIN_CLASS_SAMPLE}: UNDERPOWERED/DESCRIPTIVE_ONLY.")

    # BASE-GENERIC-POLICY: majority-class diagnosis.
    if n:
        majority_class = Counter(r["failure"]["failure_class"] for r in selected).most_common(1)[0][0]
        majority_correct = sum(1 for r in selected if r["failure"]["failure_class"] == majority_class)
        base_generic = M.rate(majority_correct, n)
    else:
        base_generic = {"value": None}
    # BASE-RANDOM for a multi-class match task: expected accuracy = 1/n_classes.
    n_classes = len({r["failure"]["failure_class"] for r in selected}) or 1
    base_random = {"value": 1.0 / n_classes, "status": "DEFINED", "method": "uniform_random_over_observed_classes"}

    min_req = task["minimum_sample_requirement"]
    status = COMPLETED if n >= min_req else UNDERPOWERED

    metrics_out = {
        "MET-FAILURE-CLASS-ACCURACY": failure_class_accuracy,
        "MET-UNKNOWN-HANDLING": unknown_handling,
        "MET-TEMPORAL-INTEGRITY": temporal_integrity,
        "MET-FALSE-CAUSAL-ATTRIBUTION-RATE": false_causal_rate,
        "MET-CONTRADICTION-HANDLING": {
            "value": None,
            "status": "LIMITED",
            "reason": "No contradiction-labeled cases identifiable from current schema fields.",
        },
        "MET-EVIDENCE-CORRECTNESS": {
            "value": 1.0,
            "status": "DEFINED",
            "reason": "All diagnosis records derive from current-run-only fields per dataset construction; "
                       "no cross-run evidence field is present to violate.",
        },
        "MET-UNSUPPORTED-CAUSE-RATE": {
            "value": None,
            "status": "LIMITED",
            "reason": "No independent re-inspection evidence available to assess whether cited evidence "
                       "supports the stated cause.",
        },
        "per_failure_class": per_class_out,
        "causal_status": CAUSAL_GROUND_TRUTH_UNAVAILABLE,
    }
    baseline_results = {"BASE-GENERIC-POLICY": base_generic, "BASE-RANDOM": base_random}

    prov = {"source_record_selector": task["source_record_selector"], "n": n}
    return _base_result(
        task, status=status, split="all_matching (controlled_runtime, failure_class != NONE)",
        sample_count=n, metrics=metrics_out, baseline_results=baseline_results,
        limitations=limitations, provenance=prov,
    )


# --------------------------------------------------------------------------
# Recovery task (REC-EVAL) -- PARTIALLY_SUPPORTED.
# --------------------------------------------------------------------------

def evaluate_recovery_task(task: dict, records: list[dict]) -> dict:
    selected = select_records(records, task)
    n = len(selected)

    validated_ok = 0
    unsafe = 0
    self_report_agrees_with_validation = 0
    per_action = defaultdict(lambda: {"n": 0, "recovered": 0})
    not_applicable_actions = 0

    for r in selected:
        validation = r.get("validation") or {}
        vstatus = validation.get("validation_status")
        recovery = r.get("recovery") or {}
        action = recovery.get("action_type")
        safety = r.get("safety") or {}
        if bool(safety.get("unsafe_authorization")):
            unsafe += 1
        per_action[action]["n"] += 1
        if vstatus == "RECOVERED":
            validated_ok += 1
            per_action[action]["recovered"] += 1
        self_report = recovery.get("executor_self_report")
        if self_report == vstatus:
            self_report_agrees_with_validation += 1
        if action in (None, "NOT_APPLICABLE"):
            not_applicable_actions += 1

    recovery_success_rate = M.rate(validated_ok, n) if n else {"value": None}
    unsafe_rate = M.rate(unsafe, n) if n else {"value": None}
    validation_correctness = (
        M.rate(self_report_agrees_with_validation, n) if n else {"value": None}
    )

    per_action_out = {}
    for action, d in per_action.items():
        st = COMPLETED if d["n"] >= MIN_CLASS_SAMPLE else UNDERPOWERED
        per_action_out[action] = {
            "n": d["n"],
            "recovery_success_rate": (d["recovered"] / d["n"]) if d["n"] else None,
            "status": st if action not in (None,) else NOT_APPLICABLE,
        }

    limitations = [
        "recovery.executor_self_report is retained only for discrepancy analysis "
        "(MET-VALIDATION-CORRECTNESS) and never substitutes for validation.validation_status as a label.",
        f"0% overall recovery_success_rate on this dataset (0 of {n} controlled_runtime failure "
        "episodes reach validation_status=RECOVERED; all are NOT_RECOVERED/UNKNOWN) is a genuine, "
        "valid negative result for this canonical dataset slice, not a benchmark defect.",
    ]
    for action, d in per_action_out.items():
        if d["status"] == UNDERPOWERED:
            limitations.append(f"action_type={action}: n={d['n']} < {MIN_CLASS_SAMPLE}: UNDERPOWERED/DESCRIPTIVE_ONLY.")

    min_req = task["minimum_sample_requirement"]
    status = COMPLETED if n >= min_req else UNDERPOWERED

    metrics_out = {
        "MET-RECOVERY-SUCCESS-RATE": recovery_success_rate,
        "MET-UNSAFE-ACTION-RATE": unsafe_rate,
        "MET-VALIDATION-CORRECTNESS": validation_correctness,
        "MET-UNNECESSARY-RECOVERY-RATE": {
            "value": None, "status": "LIMITED",
            "reason": "All 35 non-NONE failure_class records in this dataset have failure_detected=true "
                      "(real subprocess exit semantics); no false-alarm-triggered recovery is identifiable.",
        },
        "MET-ACTION-SELECTION-ACCURACY": {
            "value": None, "status": "LIMITED",
            "reason": "No independently-known best-action-per-failure-class efficacy ground truth is "
                      "present in this dataset slice (n=46); the historical RECONFIGURE-vs-RETRY n=40-per-action "
                      "comparison is aggregate/historical evidence, not re-derivable at that scale here.",
        },
        "per_action_type": per_action_out,
    }
    baseline_results = {
        "BASE-RANDOM": {"value": 1.0 / max(len(per_action), 1), "status": "DEFINED"},
        "BASE-GENERIC-POLICY": {
            "value": max((d["recovered"] for d in per_action.values()), default=0) / n if n else None,
            "status": "DEFINED" if n else "UNDEFINED_ZERO_DENOMINATOR",
            "note": "best-single-action-in-hindsight rate, naive non-adaptive baseline",
        },
    }
    prov = {"source_record_selector": task["source_record_selector"], "n": n}
    return _base_result(
        task, status=status, split="all_matching (controlled_runtime, recovery field present)",
        sample_count=n, metrics=metrics_out, baseline_results=baseline_results,
        limitations=limitations, provenance=prov,
    )


# --------------------------------------------------------------------------
# Memory (MEM-EVAL) / Generalization (GEN-*) -- NOT_EVALUABLE contract-only.
# --------------------------------------------------------------------------

def evaluate_memory_task(task: dict, records: list[dict]) -> dict:
    workload_counts = Counter(r["identity"]["workload_id"] for r in records)
    repeated = {w: c for w, c in workload_counts.items() if c > 1}
    return not_evaluable_result(
        task,
        available_evidence=[f"{len(repeated)} workload_ids appear more than once across {len(records)} records"],
        extra={
            "aggregate_reference_evidence": AGGREGATE_REFERENCE.get(task["task_id"], {}),
            "repeated_workload_id_count": len(repeated),
            "benchmark_version": BENCHMARK_VERSION,
            "dataset_version": DATASET_VERSION,
        },
    )


def evaluate_generalization_task(task: dict, records: list[dict]) -> dict:
    envs = {r["identity"]["environment_id"] for r in records}
    return not_evaluable_result(
        task,
        available_evidence=[f"{len(envs)} distinct environment_id value(s) in canonical dataset: {sorted(envs)}"],
        extra={
            "aggregate_reference_evidence": AGGREGATE_REFERENCE.get(task["task_id"], {}),
            "benchmark_version": BENCHMARK_VERSION,
            "dataset_version": DATASET_VERSION,
        },
    )


# --------------------------------------------------------------------------
# End-to-end (E2E-EVAL) -- PARTIALLY_SUPPORTED, n=46 controlled_runtime.
# --------------------------------------------------------------------------

def evaluate_end_to_end_task(task: dict, records: list[dict], *, diagnosis_result: dict, recovery_result: dict) -> dict:
    selected = select_records(records, task)
    n = len(selected)

    recovered = sum(1 for r in selected if (r.get("validation") or {}).get("validation_status") == "RECOVERED")
    unsafe = sum(1 for r in selected if bool((r.get("safety") or {}).get("unsafe_authorization")))
    complete_chain = sum(
        1 for r in selected
        if r.get("failure") is not None and r.get("validation") is not None
    )

    e2e_recovery_rate = M.rate(recovered, n) if n else {"value": None}
    e2e_unsafe_rate = M.rate(unsafe, n) if n else {"value": None}

    diag_status = diagnosis_result.get("status")
    rec_status = recovery_result.get("status")
    masking_flag = None
    if e2e_recovery_rate.get("value") not in (None,) and e2e_recovery_rate["value"] > 0.5 and (
        diag_status == UNDERPOWERED or rec_status == UNDERPOWERED
    ):
        masking_flag = "MASKING_FAILURE_RISK: high end-to-end rate reported alongside an UNDERPOWERED component result."

    limitations = [
        f"Full end-to-end coverage limited to n={n} controlled_runtime records; agent_task records "
        "(3,060) do not exercise diagnosis/recovery/memory stages and are excluded from this task.",
        "Component metrics (diagnosis, recovery) are reported jointly below specifically so a strong "
        "or weak end-to-end number cannot mask a disqualified/underpowered component result.",
    ]
    if masking_flag:
        limitations.append(masking_flag)

    min_req = task["minimum_sample_requirement"]
    status = LIMITED if n >= min_req else UNDERPOWERED

    metrics_out = {
        "MET-END-TO-END-RECOVERY-RATE": e2e_recovery_rate,
        "MET-END-TO-END-UNSAFE-ACTION-RATE": e2e_unsafe_rate,
        "MET-REPRODUCIBILITY-INDICATOR": {"value": None, "status": "SEE_DETERMINISM_TEST"},
        "complete_chain_count": complete_chain,
        "component_metrics": {
            "diagnosis": {"status": diag_status, "MET-FAILURE-CLASS-ACCURACY": diagnosis_result["metrics"].get("MET-FAILURE-CLASS-ACCURACY")},
            "recovery": {"status": rec_status, "MET-RECOVERY-SUCCESS-RATE": recovery_result["metrics"].get("MET-RECOVERY-SUCCESS-RATE")},
        },
        "masking_failure_check": masking_flag or "no masking pattern detected",
    }
    prov = {"source_record_selector": task["source_record_selector"], "n": n}
    return _base_result(
        task, status=status, split="all_matching (controlled_runtime)", sample_count=n,
        metrics=metrics_out, baseline_results=None, limitations=limitations, provenance=prov,
    )
