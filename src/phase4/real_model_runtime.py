"""Phase 4.6 -- loading and reproducibility manifest for the two real,
open-weight, locally-run Hugging Face models used as the classification
and extractive-QA task families.

Honesty notes (read before trusting any number produced with this module):
  - These are real pretrained model weights downloaded once from the
    Hugging Face Hub and run locally on CPU with `torch` -- not an API
    call to a hosted LLM service, and not the synthetic arithmetic agent
    in ``agent_task.py`` relabeled. Both are small (<300MB) DistilBERT-
    family checkpoints chosen to fit CPU-only local hardware; no larger
    model was assumed to fit.
  - Models are loaded in ``eval()`` mode (dropout disabled) with a fixed
    ``torch.manual_seed`` before load, so repeated inference on the same
    input is deterministic -- there is no sampling temperature for these
    non-generative heads (classification logits / QA span logits), unlike
    the arithmetic agent's genuinely stochastic self-consistency sampling.
  - The revision (commit) hash of each model on the Hub is recorded below
    and re-verified at import time is NOT re-fetched over the network on
    every run (that would make offline evaluation impossible); it is
    fixed here as documentation of exactly which weights were evaluated
    the day this module was written.
"""
from __future__ import annotations

import platform
from dataclasses import dataclass, field
from functools import lru_cache

import torch
import transformers
from transformers import (
    AutoModelForQuestionAnswering,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

RUNTIME_VERSION = "phase4.6-real-model-runtime-v1"
INFERENCE_SEED = 4600

CLASSIFICATION_MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"
CLASSIFICATION_MODEL_REVISION = "714eb0fa89d2f80546fda750413ed43d93601a13"

QA_MODEL_ID = "distilbert-base-cased-distilled-squad"
QA_MODEL_REVISION = "564e9b582944a57a3e586bbb98fd6f0a4118db7f"

DEVICE = "cpu"
PRECISION = "fp32"


@dataclass(frozen=True)
class ModelManifest:
    """Full reproducibility record for one loaded model, per the project's
    reproducibility requirements (model, version, source, weights id,
    tokenizer, inference config, precision, device, seed, dependencies)."""

    task_family: str
    model_id: str
    model_revision: str
    source: str = "huggingface_hub"
    tokenizer_id: str = ""
    device: str = DEVICE
    precision: str = PRECISION
    seed: int = INFERENCE_SEED
    torch_version: str = field(default_factory=lambda: torch.__version__)
    transformers_version: str = field(default_factory=lambda: transformers.__version__)
    python_version: str = field(default_factory=platform.python_version)
    platform: str = field(default_factory=platform.platform)
    runtime_version: str = RUNTIME_VERSION

    def as_dict(self) -> dict:
        return {
            "task_family": self.task_family,
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "source": self.source,
            "tokenizer_id": self.tokenizer_id or self.model_id,
            "device": self.device,
            "precision": self.precision,
            "seed": self.seed,
            "torch_version": self.torch_version,
            "transformers_version": self.transformers_version,
            "python_version": self.python_version,
            "platform": self.platform,
            "runtime_version": self.runtime_version,
        }


@lru_cache(maxsize=1)
def load_classification_model():
    """Loads the sentiment classifier once per process. Cached so repeated
    evaluation calls do not re-download/re-load weights."""
    torch.manual_seed(INFERENCE_SEED)
    tokenizer = AutoTokenizer.from_pretrained(CLASSIFICATION_MODEL_ID, revision=CLASSIFICATION_MODEL_REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(
        CLASSIFICATION_MODEL_ID, revision=CLASSIFICATION_MODEL_REVISION
    )
    model.eval()
    manifest = ModelManifest(
        task_family="classification",
        model_id=CLASSIFICATION_MODEL_ID,
        model_revision=CLASSIFICATION_MODEL_REVISION,
        tokenizer_id=CLASSIFICATION_MODEL_ID,
    )
    return tokenizer, model, manifest


@lru_cache(maxsize=1)
def load_qa_model():
    """Loads the extractive-QA model once per process."""
    torch.manual_seed(INFERENCE_SEED)
    tokenizer = AutoTokenizer.from_pretrained(QA_MODEL_ID, revision=QA_MODEL_REVISION)
    model = AutoModelForQuestionAnswering.from_pretrained(QA_MODEL_ID, revision=QA_MODEL_REVISION)
    model.eval()
    manifest = ModelManifest(
        task_family="extractive_qa",
        model_id=QA_MODEL_ID,
        model_revision=QA_MODEL_REVISION,
        tokenizer_id=QA_MODEL_ID,
    )
    return tokenizer, model, manifest
