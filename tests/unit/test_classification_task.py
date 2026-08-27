"""Phase 4.6 -- real sentiment-classification task family."""
from src.phase4.classification_task import (
    ClassificationInstance,
    load_corpus,
    run_classification,
    run_corpus,
)


def test_corpus_loads_with_version_and_examples():
    version, instances = load_corpus()
    assert version
    assert len(instances) >= 100
    labels = {inst.true_label for inst in instances}
    assert labels == {"POSITIVE", "NEGATIVE"}


def test_unambiguous_positive_example_is_usually_classified_correctly():
    instance = ClassificationInstance(
        example_id="test-pos", text="This was an absolutely wonderful and delightful experience.",
        true_label="POSITIVE", subject="test",
    )
    result = run_classification(instance)
    assert result.predicted_label in ("POSITIVE", "NEGATIVE")
    assert result.is_correct is True
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.margin <= 1.0
    assert 0.0 <= result.entropy <= 1.0
    assert result.mechanism == "softmax_margin_classification"


def test_unambiguous_negative_example_is_usually_classified_correctly():
    instance = ClassificationInstance(
        example_id="test-neg", text="This was an absolutely terrible and dreadful experience.",
        true_label="NEGATIVE", subject="test",
    )
    result = run_classification(instance)
    assert result.is_correct is True


def test_run_corpus_returns_one_result_per_instance():
    _, instances = load_corpus()
    sample = instances[:20]
    results = run_corpus(sample)
    assert len(results) == 20
    assert all(r.instance.example_id == inst.example_id for r, inst in zip(results, sample))


def test_higher_confidence_correlates_with_correctness_over_full_corpus():
    _, instances = load_corpus()
    results = run_corpus(instances)
    high = [r.is_correct for r in results if r.confidence >= 0.95]
    low = [r.is_correct for r in results if r.confidence < 0.95]
    assert high, "expected some high-confidence predictions in this corpus"
    high_acc = sum(high) / len(high)
    if low:
        low_acc = sum(low) / len(low)
        assert high_acc >= low_acc
