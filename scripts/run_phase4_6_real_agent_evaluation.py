"""Phase 4.6 -- generates the Priority 1 evaluation artifacts: real-model
+ arithmetic-agent metrics across all three task families, written into a
new immutable directory under experiments/results/phase4_6_to_4_10/.

Usage:
    python scripts/run_phase4_6_real_agent_evaluation.py <output_dir>

<output_dir> must already exist (created once per run, never reused/
overwritten -- see PHASE4_6_REAL_AGENT_REPORT.md's honesty notes).
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.phase4.agent_task import BASE_ERROR_RATE, ERROR_RATE_PER_DIFFICULTY, TASK_VERSION as ARITHMETIC_TASK_VERSION
from src.phase4.agent_task import generate_task, run_self_consistency
from src.phase4.classification_task import TASK_VERSION as CLASSIFICATION_TASK_VERSION
from src.phase4.classification_task import load_corpus as load_sentiment_corpus
from src.phase4.classification_task import run_corpus as run_classification_corpus
from src.phase4.qa_task import TASK_VERSION as QA_TASK_VERSION
from src.phase4.qa_task import load_corpus as load_qa_corpus
from src.phase4.qa_task import run_corpus as run_qa_corpus
from src.phase4.real_model_runtime import RUNTIME_VERSION, load_classification_model, load_qa_model
from src.phase4.uncertainty_eval import METRICS_VERSION, UncertaintyRecord, compute_uncertainty_metrics_by_task_family

N_ARITHMETIC_SEEDS = 2000
ARITHMETIC_N_SAMPLES = 5
ARITHMETIC_BASE_SEED = 4600


def run_arithmetic_family():
    records, raw = [], []
    for seed in range(N_ARITHMETIC_SEEDS):
        instance = generate_task(seed)
        result = run_self_consistency(instance, n_samples=ARITHMETIC_N_SAMPLES, base_seed=ARITHMETIC_BASE_SEED + seed)
        records.append(UncertaintyRecord(
            example_id=instance.task_id, is_correct=result.is_correct,
            confidence=result.agreement_rate, mechanism="self_consistency_disagreement",
            task_family="arithmetic",
        ))
        raw.append({
            "example_id": instance.task_id, "seed": seed, "difficulty": instance.difficulty,
            "expression": instance.expression, "correct_answer": instance.correct_answer,
            "samples": list(result.samples), "majority_answer": result.majority_answer,
            "agreement_rate": result.agreement_rate, "is_correct": result.is_correct,
        })
    return records, raw


def run_classification_family():
    corpus_version, instances = load_sentiment_corpus()
    results = run_classification_corpus(instances)
    records = [
        UncertaintyRecord(example_id=r.instance.example_id, is_correct=r.is_correct, confidence=r.confidence,
                           mechanism=r.mechanism, task_family="classification")
        for r in results
    ]
    raw = [
        {"example_id": r.instance.example_id, "text": r.instance.text, "true_label": r.instance.true_label,
         "predicted_label": r.predicted_label, "is_correct": r.is_correct, "confidence": r.confidence,
         "margin": r.margin, "entropy": r.entropy}
        for r in results
    ]
    return records, raw, corpus_version


def run_qa_family():
    corpus_version, instances = load_qa_corpus()
    results = run_qa_corpus(instances)
    records = [
        UncertaintyRecord(example_id=r.instance.example_id, is_correct=r.is_correct, confidence=r.span_confidence,
                           mechanism=r.mechanism, task_family="extractive_qa")
        for r in results
    ]
    raw = [
        {"example_id": r.instance.example_id, "question": r.instance.question,
         "gold_answers": list(r.instance.gold_answers), "predicted_answer": r.predicted_answer,
         "is_correct": r.is_correct, "span_confidence": r.span_confidence, "entropy": r.entropy}
        for r in results
    ]
    return records, raw, corpus_version


def main(output_dir: Path) -> None:
    assert output_dir.exists(), f"output_dir must already exist: {output_dir}"

    print(f"[1/3] arithmetic family: {N_ARITHMETIC_SEEDS} seeds x {ARITHMETIC_N_SAMPLES} samples...")
    arith_records, arith_raw = run_arithmetic_family()

    print("[2/3] classification family (real distilbert-sst2)...")
    cls_records, cls_raw, cls_corpus_version = run_classification_family()

    print("[3/3] extractive QA family (real distilbert-squad)...")
    qa_records, qa_raw, qa_corpus_version = run_qa_family()

    all_records = arith_records + cls_records + qa_records
    metrics = compute_uncertainty_metrics_by_task_family(all_records)

    (output_dir / "raw" / "episodes" / "arithmetic_episodes.json").write_text(
        json.dumps(arith_raw, indent=2), encoding="utf-8")
    (output_dir / "raw" / "predictions" / "classification_predictions.json").write_text(
        json.dumps(cls_raw, indent=2), encoding="utf-8")
    (output_dir / "raw" / "predictions" / "qa_predictions.json").write_text(
        json.dumps(qa_raw, indent=2), encoding="utf-8")

    (output_dir / "evaluation" / "uncertainty_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")

    agent_metrics = {
        "arithmetic": {
            "n": len(arith_records), "accuracy": metrics["by_task_family"]["arithmetic"]["accuracy"],
            "task_version": ARITHMETIC_TASK_VERSION, "n_samples": ARITHMETIC_N_SAMPLES,
            "base_error_rate": BASE_ERROR_RATE, "error_rate_per_difficulty": ERROR_RATE_PER_DIFFICULTY,
        },
        "classification": {
            "n": len(cls_records), "accuracy": metrics["by_task_family"]["classification"]["accuracy"],
            "task_version": CLASSIFICATION_TASK_VERSION, "corpus_version": cls_corpus_version,
        },
        "extractive_qa": {
            "n": len(qa_records), "accuracy": metrics["by_task_family"]["extractive_qa"]["accuracy"],
            "task_version": QA_TASK_VERSION, "corpus_version": qa_corpus_version,
        },
    }
    (output_dir / "evaluation" / "agent_metrics.json").write_text(
        json.dumps(agent_metrics, indent=2), encoding="utf-8")

    _, _, cls_manifest = load_classification_model()
    _, _, qa_manifest = load_qa_model()
    (output_dir / "reproducibility" / "model.json").write_text(
        json.dumps({"classification": cls_manifest.as_dict(), "extractive_qa": qa_manifest.as_dict(),
                    "arithmetic": {"task_family": "arithmetic", "task_version": ARITHMETIC_TASK_VERSION,
                                    "note": "synthetic controlled baseline, not a pretrained model; retained unchanged from Phase 4.5b"}},
                   indent=2), encoding="utf-8")
    (output_dir / "reproducibility" / "dataset.json").write_text(
        json.dumps({"classification_corpus_version": cls_corpus_version, "qa_corpus_version": qa_corpus_version,
                    "arithmetic_seed_range": [0, N_ARITHMETIC_SEEDS],
                    "generator": "data/real_model_tasks/generate_corpora.py"}, indent=2), encoding="utf-8")
    (output_dir / "reproducibility" / "seeds.json").write_text(
        json.dumps({"arithmetic_base_seed": ARITHMETIC_BASE_SEED, "n_arithmetic_seeds": N_ARITHMETIC_SEEDS,
                    "inference_seed": cls_manifest.seed}, indent=2), encoding="utf-8")
    (output_dir / "reproducibility" / "environment.json").write_text(
        json.dumps({"python_version": platform.python_version(), "platform": platform.platform(),
                    "metrics_version": METRICS_VERSION, "runtime_version": RUNTIME_VERSION}, indent=2),
        encoding="utf-8")

    print(json.dumps(agent_metrics, indent=2))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
