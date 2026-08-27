"""Phase 4.6 -- real-model task family B: binary sentiment classification
with a real DistilBERT classifier (``real_model_runtime.py``) evaluated
against the curated, correctness-by-construction corpus in
``data/real_model_tasks/sentiment_eval.json``.

Uncertainty mechanism for this family: calibrated softmax probability of
the predicted class, plus predictive entropy and the top1-vs-top2 margin
-- the standard classification uncertainty signals (not self-consistency,
which does not apply to a deterministic single-forward-pass classifier).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import torch

from .real_model_runtime import load_classification_model

TASK_VERSION = "phase4.6-classification-task-v1"
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "real_model_tasks" / "sentiment_eval.json"


@dataclass(frozen=True)
class ClassificationInstance:
    example_id: str
    text: str
    true_label: str
    subject: str


@dataclass(frozen=True)
class ClassificationResult:
    instance: ClassificationInstance
    predicted_label: str
    is_correct: bool
    confidence: float  # softmax probability of the predicted class
    margin: float  # top1 - top2 softmax probability
    entropy: float  # predictive entropy in nats, normalized to [0,1] by log(num_classes)
    mechanism: str = "softmax_margin_classification"


def load_corpus(path: Path = DEFAULT_CORPUS_PATH) -> tuple[str, list[ClassificationInstance]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    instances = [
        ClassificationInstance(
            example_id=ex["example_id"], text=ex["text"], true_label=ex["true_label"], subject=ex["subject"],
        )
        for ex in data["examples"]
    ]
    return data["corpus_version"], instances


def _entropy(probs: Sequence[float]) -> float:
    n = len(probs)
    raw = -sum(p * math.log(p) for p in probs if p > 0.0)
    max_entropy = math.log(n) if n > 1 else 1.0
    return raw / max_entropy if max_entropy > 0 else 0.0


def run_classification(instance: ClassificationInstance) -> ClassificationResult:
    tokenizer, model, _manifest = load_classification_model()
    inputs = tokenizer(instance.text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    probs = torch.softmax(logits, dim=-1).tolist()
    id2label = model.config.id2label
    ranked = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
    top_idx, second_idx = ranked[0], ranked[1] if len(ranked) > 1 else ranked[0]
    predicted_label = id2label[top_idx]
    confidence = probs[top_idx]
    margin = probs[top_idx] - probs[second_idx]
    return ClassificationResult(
        instance=instance,
        predicted_label=predicted_label,
        is_correct=(predicted_label == instance.true_label),
        confidence=confidence,
        margin=margin,
        entropy=_entropy(probs),
    )


def run_corpus(instances: Sequence[ClassificationInstance]) -> list[ClassificationResult]:
    return [run_classification(inst) for inst in instances]
