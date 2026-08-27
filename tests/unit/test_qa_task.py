"""Phase 4.6 -- real extractive-QA task family."""
from src.phase4.qa_task import QAInstance, _normalize, load_corpus, run_corpus, run_qa


def test_corpus_loads_and_every_gold_answer_is_a_verbatim_substring_of_its_context():
    version, instances = load_corpus()
    assert version
    assert len(instances) >= 100
    for inst in instances:
        assert any(gold in inst.context for gold in inst.gold_answers), (
            f"gold answer not verbatim in context for {inst.example_id}"
        )


def test_normalize_strips_articles_case_and_punctuation():
    assert _normalize("The Northgate Robotics.") == _normalize("northgate robotics")


def test_run_qa_returns_well_formed_result():
    instance = QAInstance(
        example_id="test-qa", context="Acme Corp was founded in 1990 by Jane Doe.",
        question="When was Acme Corp founded?", gold_answers=("1990",), entity="Acme Corp",
    )
    result = run_qa(instance)
    assert isinstance(result.predicted_answer, str)
    assert 0.0 <= result.span_confidence <= 1.0
    assert 0.0 <= result.entropy <= 1.0
    assert result.mechanism == "softmax_span_confidence_qa"


def test_run_corpus_returns_one_result_per_instance():
    _, instances = load_corpus()
    sample = instances[:20]
    results = run_corpus(sample)
    assert len(results) == 20
    assert all(r.instance.example_id == inst.example_id for r, inst in zip(results, sample))
