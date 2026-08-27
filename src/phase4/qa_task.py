"""Phase 4.6 -- real-model task family C: extractive question answering
with a real DistilBERT-SQuAD model (``real_model_runtime.py``) evaluated
against the curated, correctness-by-construction corpus in
``data/real_model_tasks/qa_eval.json`` (every gold answer is a verbatim
substring of its own context by construction, see the generator script).

Uncertainty mechanism for this family: the model's own start/end span
softmax confidence (product of the chosen start-token and end-token
probabilities) plus predictive entropy over the start/end distributions
-- the standard extractive-QA uncertainty signal, distinct from both the
arithmetic agent's self-consistency signal and the classifier's softmax
margin.
"""
from __future__ import annotations

import json
import math
import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import torch

from .real_model_runtime import load_qa_model

TASK_VERSION = "phase4.6-qa-task-v1"
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "real_model_tasks" / "qa_eval.json"
MAX_ANSWER_LENGTH_TOKENS = 12


@dataclass(frozen=True)
class QAInstance:
    example_id: str
    context: str
    question: str
    gold_answers: tuple[str, ...]
    entity: str


@dataclass(frozen=True)
class QAResult:
    instance: QAInstance
    predicted_answer: str
    is_correct: bool  # normalized exact match against any gold answer
    span_confidence: float  # start_prob * end_prob for the chosen span
    entropy: float  # mean of normalized start/end predictive entropy, in [0,1]
    mechanism: str = "softmax_span_confidence_qa"


def load_corpus(path: Path = DEFAULT_CORPUS_PATH) -> tuple[str, list[QAInstance]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    instances = [
        QAInstance(
            example_id=ex["example_id"], context=ex["context"], question=ex["question"],
            gold_answers=tuple(ex["gold_answers"]), entity=ex["entity"],
        )
        for ex in data["examples"]
    ]
    return data["corpus_version"], instances


def _normalize(text: str) -> str:
    text = text.lower()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def _entropy(probs: Sequence[float]) -> float:
    n = len(probs)
    raw = -sum(p * math.log(p) for p in probs if p > 0.0)
    max_entropy = math.log(n) if n > 1 else 1.0
    return raw / max_entropy if max_entropy > 0 else 0.0


def run_qa(instance: QAInstance) -> QAResult:
    tokenizer, model, _manifest = load_qa_model()
    inputs = tokenizer(instance.question, instance.context, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    start_logits = outputs.start_logits[0]
    end_logits = outputs.end_logits[0]
    start_probs = torch.softmax(start_logits, dim=-1)
    end_probs = torch.softmax(end_logits, dim=-1)

    seq_len = start_logits.shape[0]
    best_score = None
    best_start, best_end = 0, 0
    for s in range(seq_len):
        max_e = min(seq_len, s + MAX_ANSWER_LENGTH_TOKENS)
        for e in range(s, max_e):
            score = start_probs[s].item() * end_probs[e].item()
            if best_score is None or score > best_score:
                best_score = score
                best_start, best_end = s, e

    input_ids = inputs["input_ids"][0]
    predicted_answer = tokenizer.decode(input_ids[best_start:best_end + 1], skip_special_tokens=True).strip()

    is_correct = any(_normalize(predicted_answer) == _normalize(gold) for gold in instance.gold_answers)
    entropy = (_entropy(start_probs.tolist()) + _entropy(end_probs.tolist())) / 2.0

    return QAResult(
        instance=instance,
        predicted_answer=predicted_answer,
        is_correct=is_correct,
        span_confidence=float(best_score if best_score is not None else 0.0),
        entropy=entropy,
    )


def run_corpus(instances: Sequence[QAInstance]) -> list[QAResult]:
    return [run_qa(inst) for inst in instances]
