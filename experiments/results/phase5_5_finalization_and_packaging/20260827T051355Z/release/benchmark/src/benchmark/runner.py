"""Orchestrates the full Phase 5.4 benchmark run: load -> validate -> leakage
scan -> execute all 16 tasks (fail-closed for unsupported ones) -> ablations
-> capability matrix -> reproducibility metadata. Deterministic given a fixed
seed and fixed inputs; no filesystem-order or hash()-order dependence.
"""
from __future__ import annotations

from . import ablations as ABL
from . import tasks as T
from .dataset_loader import load_canonical_dataset
from .leakage import pre_evaluation_leakage_scan
from .registry import load_registry, may_execute, not_evaluable_result
from .reporting import bucket_results, build_capability_matrix
from .reproducibility import collect_reproducibility_metadata
from .validation import validate_dataset

TASK_DISPATCH = {
    "UNC-ARITH": T.evaluate_uncertainty_task,
    "UNC-SENT": T.evaluate_uncertainty_task,
    "UNC-QA": T.evaluate_uncertainty_task,
    "ABST-ARITH": T.evaluate_abstention_task,
    "ABST-SENT": T.evaluate_abstention_task,
    "ABST-QA": T.evaluate_abstention_task,
    "PRED-RESOURCE-UNAVAILABLE": T.evaluate_failure_prediction_task,
    "PRED-OOM": T.evaluate_failure_prediction_task,
    "PRED-CPU": T.evaluate_failure_prediction_task,
    "PRED-FLAKY": T.evaluate_failure_prediction_task,
    "DIAG-EVAL": T.evaluate_diagnosis_task,
    "REC-EVAL": T.evaluate_recovery_task,
    "MEM-EVAL": T.evaluate_memory_task,
    "GEN-RANKING-CONTRACT": T.evaluate_generalization_task,
    "GEN-OPERATING-POINT-CONTRACT": T.evaluate_generalization_task,
    "E2E-EVAL": None,  # handled specially (needs diagnosis/recovery results)
}


def run_benchmark(dataset_dir=None, spec_dir=None) -> dict:
    bundle = load_canonical_dataset(dataset_dir)
    audit = validate_dataset(bundle)  # fail-closed: raises DatasetValidationError on any violation

    registry = load_registry()
    records = bundle["records"]

    leakage_scan = pre_evaluation_leakage_scan(records, bundle["dataset_version"])

    results: dict[str, dict] = {}
    for task_id, task in registry.items():
        if task_id == "E2E-EVAL":
            continue
        if not may_execute(task):
            # Gated: call the dedicated NOT_EVALUABLE-shaped evaluator so
            # aggregate-reference evidence / repeated-workload counts are
            # attached, never a bare gate message and never real scoring.
            fn = TASK_DISPATCH[task_id]
            results[task_id] = fn(task, records)
            continue
        fn = TASK_DISPATCH[task_id]
        if task_id.startswith("ABST-"):
            from .tasks import fit_generic_policy_threshold

            generic_threshold = fit_generic_policy_threshold(records, registry)
            results[task_id] = fn(task, records, generic_threshold=generic_threshold)
        else:
            results[task_id] = fn(task, records)

    # E2E-EVAL needs diagnosis + recovery results already computed above.
    e2e_task = registry["E2E-EVAL"]
    results["E2E-EVAL"] = T.evaluate_end_to_end_task(
        e2e_task, records, diagnosis_result=results["DIAG-EVAL"], recovery_result=results["REC-EVAL"],
    )

    ablation_results = ABL.run_all_ablations(registry, records)

    capability_matrix = build_capability_matrix(results)
    buckets = bucket_results(results)

    repro = collect_reproducibility_metadata(
        config={"task_ids": sorted(registry.keys()), "n_records": len(records)}
    )

    return {
        "dataset_audit": audit,
        "leakage_scan": leakage_scan,
        "task_results": results,
        "ablation_results": ablation_results,
        "capability_matrix": capability_matrix,
        "result_buckets": buckets,
        "reproducibility": repro,
        "registry_task_count": len(registry),
    }
