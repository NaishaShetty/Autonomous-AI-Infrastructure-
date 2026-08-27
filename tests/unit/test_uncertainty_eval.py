"""Phase 4.6 -- uncertainty/calibration metrics harness."""
from src.phase4.uncertainty_eval import (
    UncertaintyRecord,
    compute_uncertainty_metrics,
    compute_uncertainty_metrics_by_task_family,
)


def _record(i, is_correct, confidence, mechanism="m", family="f"):
    return UncertaintyRecord(example_id=f"ex-{i}", is_correct=is_correct, confidence=confidence,
                              mechanism=mechanism, task_family=family)


def test_perfectly_separable_confidence_gives_auroc_one():
    records = [_record(i, True, 0.95) for i in range(20)] + [_record(i + 20, False, 0.05) for i in range(20)]
    metrics = compute_uncertainty_metrics(records)
    assert metrics["auroc_error_detection"] == 1.0
    assert metrics["auprc_error_detection"] == 1.0


def test_uninformative_constant_confidence_gives_undefined_or_chance_auroc():
    records = [_record(i, i % 2 == 0, 0.5) for i in range(40)]
    metrics = compute_uncertainty_metrics(records)
    # constant confidence -> AUROC of a degenerate score is 0.5 by sklearn convention
    assert metrics["auroc_error_detection"] == 0.5


def test_single_class_present_reports_none_not_zero():
    records = [_record(i, True, 0.9) for i in range(10)]
    metrics = compute_uncertainty_metrics(records)
    assert metrics["auroc_error_detection"] is None
    assert metrics["auprc_error_detection"] is None
    assert "only one outcome class" in metrics["auroc_note"]


def test_empty_records_reports_n_zero_not_fabricated_metrics():
    metrics = compute_uncertainty_metrics([])
    assert metrics["n"] == 0


def test_perfect_calibration_gives_zero_ece():
    # 10 correct at confidence 1.0, 10 incorrect at confidence 0.0 -> perfectly calibrated
    records = [_record(i, True, 1.0) for i in range(10)] + [_record(i + 10, False, 0.0) for i in range(10)]
    metrics = compute_uncertainty_metrics(records)
    assert metrics["ece"] == 0.0


def test_risk_coverage_curve_selective_accuracy_improves_as_coverage_shrinks():
    # confidence perfectly ranks correctness -> restricting to the most
    # confident (lowest-coverage) slice should never hurt selective accuracy
    # vs. keeping everything (full coverage). COVERAGE_LEVELS runs 1.0 -> 0.1,
    # so curve[0] is full coverage and curve[-1] is the most-confident 10%.
    n = 100
    records = [_record(i, is_correct=(i < 60), confidence=(1.0 if i < 60 else 0.0)) for i in range(n)]
    metrics = compute_uncertainty_metrics(records)
    curve = metrics["risk_coverage_curve"]
    accuracies = [pt["selective_accuracy"] for pt in curve]
    assert accuracies[0] <= accuracies[-1]


def test_mechanism_and_task_family_identity_preserved_and_by_family_breakdown_works():
    records = (
        [_record(i, True, 0.9, mechanism="self_consistency_disagreement", family="arithmetic") for i in range(5)]
        + [_record(i + 5, False, 0.4, mechanism="softmax_margin_classification", family="classification") for i in range(5)]
    )
    grouped = compute_uncertainty_metrics_by_task_family(records)
    assert set(grouped["by_task_family"].keys()) == {"arithmetic", "classification"}
    assert grouped["by_task_family"]["arithmetic"]["mechanism"] == "self_consistency_disagreement"
    assert grouped["by_task_family"]["classification"]["mechanism"] == "softmax_margin_classification"
    assert grouped["overall"]["n"] == 10
