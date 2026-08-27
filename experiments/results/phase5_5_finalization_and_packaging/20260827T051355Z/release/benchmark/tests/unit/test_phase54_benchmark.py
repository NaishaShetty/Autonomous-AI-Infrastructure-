"""Unit tests for the Phase 5.4 benchmark implementation.

Covers: dataset loading, schema/split/leakage validation, metric edge cases,
task eligibility gating, NOT_EVALUABLE/UNKNOWN handling, single-class AUROC,
deterministic results, baseline/ablation consistency, provenance, and report
generation -- per the task brief's Step 15 requirement.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.benchmark import baselines as B
from src.benchmark import metrics as M
from src.benchmark.dataset_loader import load_canonical_dataset, confidence_value
from src.benchmark.ids import compute_instance_id
from src.benchmark.leakage import LeakageError, check_hidden_fields_not_in_input, pre_evaluation_leakage_scan
from src.benchmark.registry import load_registry, may_execute, select_records
from src.benchmark.reporting import build_capability_matrix, classify_capability
from src.benchmark.runner import run_benchmark
from src.benchmark.splits import records_for_split, split_counts
from src.benchmark.status import (
    NOT_DEFINED_SINGLE_CLASS,
    NOT_EVALUABLE,
    UNDEFINED_ZERO_COVERAGE,
    UNDEFINED_ZERO_DENOMINATOR,
)
from src.benchmark.validation import DatasetValidationError, validate_dataset


@pytest.fixture(scope="module")
def bundle():
    return load_canonical_dataset()


@pytest.fixture(scope="module")
def registry():
    return load_registry()


# --------------------------------------------------------------------------
# Dataset loading / schema / split / provenance
# --------------------------------------------------------------------------

def test_dataset_loads_expected_record_count(bundle):
    assert len(bundle["records"]) == 3106


def test_dataset_validation_passes(bundle):
    audit = validate_dataset(bundle)
    assert audit["ok"] is True
    assert audit["n_episodes"] == 3106
    assert audit["n_workloads"] == 3104
    assert audit["n_environments"] == 1
    assert audit["split_counts"] == {"train": 2142, "calibration_validation": 482, "test": 482}


def test_dataset_validation_fails_closed_on_tampered_record(bundle):
    tampered = {"records": [dict(bundle["records"][0])], "metadata": bundle["metadata"],
                "all_records_sha256": "deadbeef"}
    tampered["records"][0] = dict(tampered["records"][0])
    tampered["records"][0]["split_assignment"] = "not_a_real_split"
    with pytest.raises(DatasetValidationError):
        validate_dataset(tampered, expected_hash=None)


def test_workload_grouping_never_crosses_splits(bundle):
    from collections import defaultdict

    wl = defaultdict(set)
    for r in bundle["records"]:
        wl[r["identity"]["workload_id"]].add(r["split_assignment"])
    crossing = {k: v for k, v in wl.items() if len(v) > 1}
    assert crossing == {}


def test_splits_module_counts_match(bundle):
    counts = split_counts(bundle["records"])
    assert counts == {"train": 2142, "calibration_validation": 482, "test": 482}
    test_only = records_for_split(bundle["records"], "test")
    assert len(test_only) == 482
    assert all(r["split_assignment"] == "test" for r in test_only)


# --------------------------------------------------------------------------
# Leakage
# --------------------------------------------------------------------------

def test_leakage_scan_passes(bundle):
    scan = pre_evaluation_leakage_scan(bundle["records"], bundle["dataset_version"])
    assert scan["status"] == "PASSED"


def test_leakage_rejects_hidden_field_in_input():
    with pytest.raises(LeakageError):
        check_hidden_fields_not_in_input({"is_correct": True}, ["agent_output.is_correct"])


def test_leakage_allows_clean_input():
    # Should not raise.
    check_hidden_fields_not_in_input({"agreement_rate": 0.6}, ["agent_output.is_correct"])


def test_leakage_rejects_non_canonical_dataset_version():
    from src.benchmark.leakage import check_gen3_only, LeakageError as LE

    with pytest.raises(LE):
        check_gen3_only("some-other-dataset-v0.9.0")


# --------------------------------------------------------------------------
# Metric edge cases
# --------------------------------------------------------------------------

def test_auroc_single_class_not_defined_as_half():
    result = M.auroc([1, 1, 1], [0.9, 0.2, 0.6])
    assert result["status"] == NOT_DEFINED_SINGLE_CLASS
    assert result["value"] is None  # never fabricated as 0.5


def test_auroc_empty():
    result = M.auroc([], [])
    assert result["status"] == UNDEFINED_ZERO_DENOMINATOR


def test_auroc_normal_case_is_high_for_separable_data():
    y = [0, 0, 1, 1]
    s = [0.1, 0.2, 0.8, 0.9]
    result = M.auroc(y, s)
    assert result["status"] == "DEFINED"
    assert result["value"] == 1.0


def test_brier_constant_predictor_under_imbalance():
    y = [0] * 90 + [1] * 10
    p = [0.1] * 100
    result = M.brier(y, p)
    assert result["status"] == "DEFINED"
    assert 0.0 <= result["value"] <= 1.0


def test_ece_all_bins_perfectly_calibrated():
    y = [0, 1] * 50
    p = [0.5] * 100
    result = M.ece(y, p)
    assert result["status"] == "DEFINED"
    assert result["value"] == pytest.approx(0.0, abs=1e-9)


def test_selective_risk_zero_coverage_is_undefined_not_zero():
    is_answer = np.zeros(10, dtype=bool)
    is_correct = np.ones(10, dtype=bool)
    result = M.selective_risk(is_answer, is_correct)
    assert result["status"] == UNDEFINED_ZERO_COVERAGE
    assert result["value"] is None


def test_precision_recall_zero_denominator():
    y_true = [0, 0, 0, 0]
    y_pred = [0, 0, 0, 0]
    p = M.precision(y_true, y_pred)
    r = M.recall(y_true, y_pred)
    assert p["status"] == UNDEFINED_ZERO_DENOMINATOR
    assert r["status"] == UNDEFINED_ZERO_DENOMINATOR


def test_wilson_ci_zero_n():
    result = M.wilson_ci(0, 0)
    assert result["status"] == UNDEFINED_ZERO_DENOMINATOR


def test_wilson_ci_all_positive():
    result = M.wilson_ci(10, 10)
    assert result["point"] == 1.0
    assert result["ci_high"] <= 1.0


def test_all_abstain_coverage_is_zero():
    actions = ["ABSTAIN"] * 20
    cov = M.coverage_metric(actions)
    assert cov["value"] == 0.0


def test_all_answer_coverage_is_one():
    actions = ["ANSWER"] * 20
    cov = M.coverage_metric(actions)
    assert cov["value"] == 1.0


def test_operating_point_validity_flags_always_fires():
    auroc_result = {"value": 0.78}
    far_result = {"value": 1.0}
    flagged = M.operating_point_validity(auroc_result, far_result)
    assert flagged["status"] == "RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID"
    assert flagged["operationally_successful"] is False


def test_operating_point_validity_accepts_valid_operating_point():
    auroc_result = {"value": 0.78}
    far_result = {"value": 0.1}
    result = M.operating_point_validity(auroc_result, far_result)
    assert result["operationally_successful"] is True


def test_recovery_zero_percent_is_a_defined_value_not_undefined():
    """0% recovery on a genuinely unfixable failure must be a real, defined
    result -- never NOT_EVALUABLE or silently coerced to a different status."""
    result = M.rate(0, 35)
    assert result["status"] == "DEFINED"
    assert result["value"] == 0.0


# --------------------------------------------------------------------------
# Deterministic IDs / no Python hash()
# --------------------------------------------------------------------------

def test_instance_id_deterministic():
    a = compute_instance_id("UNC-ARITH", "00060fca88bddeff04c859e6", 0)
    b = compute_instance_id("UNC-ARITH", "00060fca88bddeff04c859e6", 0)
    assert a == b
    assert len(a) == 64  # sha256 hex digest


def test_instance_id_sensitive_to_all_fields():
    a = compute_instance_id("UNC-ARITH", "rid", 0)
    b = compute_instance_id("UNC-SENT", "rid", 0)
    c = compute_instance_id("UNC-ARITH", "rid", 1)
    assert len({a, b, c}) == 3


# --------------------------------------------------------------------------
# Task registry / eligibility gating
# --------------------------------------------------------------------------

def test_registry_has_16_tasks(registry):
    assert len(registry) == 16


def test_unsupported_tasks_cannot_silently_execute(registry):
    for task_id in ("PRED-OOM", "PRED-CPU", "PRED-FLAKY", "PRED-RESOURCE-UNAVAILABLE",
                     "MEM-EVAL", "GEN-RANKING-CONTRACT", "GEN-OPERATING-POINT-CONTRACT"):
        assert may_execute(registry[task_id]) is False


def test_evaluable_tasks_may_execute(registry):
    for task_id in ("UNC-ARITH", "UNC-SENT", "UNC-QA"):
        assert may_execute(registry[task_id]) is True


def test_select_records_filters_by_family(bundle, registry):
    task = registry["UNC-ARITH"]
    selected = select_records(bundle["records"], task)
    assert len(selected) == 2000
    for r in selected:
        assert r["agent_output"]["task_family"] == "arithmetic_self_consistency"


# --------------------------------------------------------------------------
# Full benchmark run: NOT_EVALUABLE shape, status distinctness, determinism
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def benchmark_run():
    return run_benchmark()


def test_all_16_tasks_produce_a_result(benchmark_run):
    assert len(benchmark_run["task_results"]) == 16


def test_not_evaluable_tasks_carry_required_fields(benchmark_run):
    for task_id in ("PRED-OOM", "MEM-EVAL", "GEN-RANKING-CONTRACT"):
        result = benchmark_run["task_results"][task_id]
        assert result["status"] == NOT_EVALUABLE
        assert "reason" in result
        assert "required_evidence" in result
        assert "available_evidence" in result
        # NOT_EVALUABLE must never be silently coerced to a numeric 0 score.
        assert result["metrics"] is None


def test_recovery_task_shows_genuine_zero_percent_not_evaluable(benchmark_run):
    rec = benchmark_run["task_results"]["REC-EVAL"]
    assert rec["metrics"]["MET-RECOVERY-SUCCESS-RATE"]["value"] == 0.0
    assert rec["metrics"]["MET-RECOVERY-SUCCESS-RATE"]["status"] == "DEFINED"


def test_diagnosis_reports_causal_ground_truth_unavailable(benchmark_run):
    diag = benchmark_run["task_results"]["DIAG-EVAL"]
    assert diag["metrics"]["causal_status"] == "CAUSAL_GROUND_TRUTH_UNAVAILABLE"


def test_statuses_remain_distinct_across_tasks(benchmark_run):
    statuses = {r["status"] for r in benchmark_run["task_results"].values()}
    # UNDERPOWERED, NOT_EVALUABLE, SIMULATED_POLICY_EVALUATION, COMPLETED/LIMITED
    # must never collapse into one shared value.
    assert len(statuses) >= 3


def test_capability_matrix_never_says_validated_from_underpowered(benchmark_run):
    matrix = build_capability_matrix(benchmark_run["task_results"])
    for row in matrix:
        result = benchmark_run["task_results"][row["task_id"]]
        if result["status"] == "UNDERPOWERED":
            assert row["status"] != "VALIDATED"
        if result["status"] == NOT_EVALUABLE:
            assert row["status"] == "NOT_EVALUABLE"


def test_ablation_matrix_has_5_entries(benchmark_run):
    assert len(benchmark_run["ablation_results"]) == 5


def test_predictor_ablation_reports_confounded_not_causal(benchmark_run):
    result = benchmark_run["ablation_results"]["ABL-PREDICTOR-ON-OFF"]
    assert "CONFOUNDED" in result["extra_status"]


def test_determinism_two_runs_identical_task_results():
    import json

    run1 = run_benchmark()
    run2 = run_benchmark()

    def _default(o):
        return str(o)

    j1 = json.dumps(run1["task_results"], sort_keys=True, default=_default)
    j2 = json.dumps(run2["task_results"], sort_keys=True, default=_default)
    assert j1 == j2
    assert run1["dataset_audit"]["split_counts"] == run2["dataset_audit"]["split_counts"]


def test_reproducibility_metadata_present(benchmark_run):
    repro = benchmark_run["reproducibility"]
    for key in ("benchmark_version", "dataset_version", "schema_version", "python_version", "config_hash"):
        assert repro.get(key)


def test_baseline_always_abstain_is_flagged_not_successful():
    from src.benchmark.dataset_loader import load_canonical_dataset as _lcd
    from src.benchmark.registry import load_registry as _lr
    from src.benchmark.tasks import evaluate_abstention_task, fit_generic_policy_threshold

    b = _lcd()
    reg = _lr()
    threshold = fit_generic_policy_threshold(b["records"], reg)
    result = evaluate_abstention_task(reg["ABST-QA"], b["records"], generic_threshold=threshold)
    assert result["baseline_results"]["BASE-ALWAYS-ABSTAIN"]["flag"] == "ALWAYS_ABSTAIN_NOT_SUCCESSFUL"


def test_baseline_random_is_near_chance_auroc():
    scores = B.base_random_scores(5000, seed=1)
    y = np.array(([0, 1] * 2500))
    result = M.auroc(y, scores)
    assert result["status"] == "DEFINED"
    assert 0.45 < result["value"] < 0.55
