"""Phase 4.6 -- end-to-end integration: all three task families (arithmetic
self-consistency, real sentiment classification, real extractive QA)
evaluated through the shared uncertainty metrics harness, each preserving
its own mechanism identity."""
import math

from src.phase4.agent_task import generate_task, run_self_consistency
from src.phase4.classification_task import load_corpus as load_sentiment_corpus
from src.phase4.classification_task import run_corpus as run_classification_corpus
from src.phase4.qa_task import load_corpus as load_qa_corpus
from src.phase4.qa_task import run_corpus as run_qa_corpus
from src.phase4.uncertainty_eval import UncertaintyRecord, compute_uncertainty_metrics_by_task_family

N_ARITHMETIC = 150
N_CLASSIFICATION = 150
N_QA = 100


def _arithmetic_records():
    records = []
    for seed in range(N_ARITHMETIC):
        instance = generate_task(seed)
        result = run_self_consistency(instance, n_samples=5, base_seed=seed)
        records.append(UncertaintyRecord(
            example_id=instance.task_id, is_correct=result.is_correct,
            confidence=result.agreement_rate, mechanism="self_consistency_disagreement",
            task_family="arithmetic",
        ))
    return records


def _classification_records():
    _, instances = load_sentiment_corpus()
    results = run_classification_corpus(instances[:N_CLASSIFICATION])
    return [
        UncertaintyRecord(
            example_id=r.instance.example_id, is_correct=r.is_correct, confidence=r.confidence,
            mechanism=r.mechanism, task_family="classification",
        )
        for r in results
    ]


def _qa_records():
    _, instances = load_qa_corpus()
    results = run_qa_corpus(instances[:N_QA])
    return [
        UncertaintyRecord(
            example_id=r.instance.example_id, is_correct=r.is_correct, confidence=r.span_confidence,
            mechanism=r.mechanism, task_family="extractive_qa",
        )
        for r in results
    ]


def test_all_three_task_families_produce_complete_metrics_with_no_nan_or_exception():
    all_records = _arithmetic_records() + _classification_records() + _qa_records()
    grouped = compute_uncertainty_metrics_by_task_family(all_records)

    assert set(grouped["by_task_family"].keys()) == {"arithmetic", "classification", "extractive_qa"}
    assert grouped["overall"]["n"] == N_ARITHMETIC + N_CLASSIFICATION + N_QA

    for family, metrics in grouped["by_task_family"].items():
        assert metrics["n"] > 0, family
        assert not math.isnan(metrics["brier_score"]), family
        assert not math.isnan(metrics["ece"]), family
        for pt in metrics["risk_coverage_curve"]:
            if pt["selective_accuracy"] is not None:
                assert not math.isnan(pt["selective_accuracy"])
        if metrics["auroc_error_detection"] is not None:
            assert 0.0 <= metrics["auroc_error_detection"] <= 1.0, family


def test_each_task_family_preserves_its_own_distinct_uncertainty_mechanism():
    all_records = _arithmetic_records()[:10] + _classification_records()[:10] + _qa_records()[:10]
    mechanisms_by_family = {r.task_family: r.mechanism for r in all_records}
    assert mechanisms_by_family["arithmetic"] == "self_consistency_disagreement"
    assert mechanisms_by_family["classification"] == "softmax_margin_classification"
    assert mechanisms_by_family["extractive_qa"] == "softmax_span_confidence_qa"
    # three genuinely different mechanisms, not one forced onto all families
    assert len({r.mechanism for r in all_records}) == 3
