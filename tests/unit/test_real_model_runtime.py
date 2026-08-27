"""Phase 4.6 -- real (open-weight, local) model loading + reproducibility
manifest coverage."""
import torch

from src.phase4.real_model_runtime import (
    CLASSIFICATION_MODEL_ID,
    QA_MODEL_ID,
    load_classification_model,
    load_qa_model,
)


def test_classification_model_loads_with_full_reproducibility_manifest():
    tokenizer, model, manifest = load_classification_model()
    assert manifest.task_family == "classification"
    assert manifest.model_id == CLASSIFICATION_MODEL_ID
    assert manifest.device == "cpu"
    assert manifest.precision == "fp32"
    d = manifest.as_dict()
    for key in ("model_id", "model_revision", "source", "tokenizer_id", "device",
                "precision", "seed", "torch_version", "transformers_version",
                "python_version", "platform", "runtime_version"):
        assert d.get(key), f"missing/empty reproducibility field: {key}"
    assert not model.training  # eval() mode


def test_qa_model_loads_with_full_reproducibility_manifest():
    tokenizer, model, manifest = load_qa_model()
    assert manifest.task_family == "extractive_qa"
    assert manifest.model_id == QA_MODEL_ID
    assert not model.training


def test_classification_model_is_cached_across_calls():
    _, model_a, _ = load_classification_model()
    _, model_b, _ = load_classification_model()
    assert model_a is model_b


def test_classification_inference_is_deterministic_given_fixed_input():
    tokenizer, model, _ = load_classification_model()
    text = "This was a wonderful experience."
    logits_runs = []
    for _ in range(3):
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            logits_runs.append(model(**inputs).logits.tolist())
    assert logits_runs[0] == logits_runs[1] == logits_runs[2]
