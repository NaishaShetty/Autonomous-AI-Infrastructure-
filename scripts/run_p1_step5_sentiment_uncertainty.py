"""Post-P5 remediation, Step 5 (P1-W1) -- sentiment uncertainty mechanism
comparison. Implements exactly the protocol pre-registered in
``experiments/results/post_p5_remediation/<TIMESTAMP>/protocol/P1_STEP5_SENTIMENT_UNCERTAINTY_PROTOCOL.md``.

Usage:
    python scripts/run_p1_step5_sentiment_uncertainty.py <run_dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch

from src.phase4.classification_task import DEFAULT_CORPUS_PATH, load_corpus
from src.phase4.real_model_runtime import load_classification_model
from src.phase4.uncertainty_eval import UncertaintyRecord, compute_uncertainty_metrics

CALIBRATION_FRACTION = 0.4


def _stable_split(example_id: str) -> str:
    digest = hashlib.sha256(f"phase4.post_p5.step5-split\x1f{example_id}".encode("utf-8")).hexdigest()
    frac = int(digest[:8], 16) / 0xFFFFFFFF
    return "calibration" if frac < CALIBRATION_FRACTION else "test"


def _forward(tokenizer, model, text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    return logits


def _fit_temperature(logits_list, labels_list, n_iters: int = 200, lr: float = 0.01) -> float:
    """Standard single-scalar temperature scaling: minimize NLL on the
    calibration split only. logits_list: list of 1D tensors; labels_list:
    list of int class indices."""
    logits_tensor = torch.stack(logits_list)
    labels_tensor = torch.tensor(labels_list, dtype=torch.long)
    log_temp = torch.zeros(1, requires_grad=True)  # optimize in log-space to keep T>0
    optimizer = torch.optim.Adam([log_temp], lr=lr)
    nll = torch.nn.CrossEntropyLoss()
    for _ in range(n_iters):
        optimizer.zero_grad()
        temp = torch.exp(log_temp)
        loss = nll(logits_tensor / temp, labels_tensor)
        loss.backward()
        optimizer.step()
    return float(torch.exp(log_temp).item())


def main(run_dir: Path) -> None:
    corpus_version, instances = load_corpus(DEFAULT_CORPUS_PATH)
    tokenizer, model, manifest = load_classification_model()
    id2label = model.config.id2label
    label2id = {v: k for k, v in id2label.items()}

    print(f"running {len(instances)} real forward passes...")
    per_example = []
    for inst in instances:
        logits = _forward(tokenizer, model, inst.text)
        probs = torch.softmax(logits, dim=-1).tolist()
        ranked = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
        top_idx, second_idx = ranked[0], ranked[1] if len(ranked) > 1 else ranked[0]
        predicted_label = id2label[top_idx]
        is_correct = predicted_label == inst.true_label
        margin = probs[top_idx] - probs[second_idx]
        import math
        raw_entropy = -sum(p * math.log(p) for p in probs if p > 0.0)
        max_entropy = math.log(len(probs)) if len(probs) > 1 else 1.0
        entropy = raw_entropy / max_entropy if max_entropy > 0 else 0.0
        split = _stable_split(inst.example_id)
        per_example.append({
            "example_id": inst.example_id, "is_correct": is_correct, "split": split,
            "baseline_confidence": probs[top_idx], "margin": margin, "entropy": entropy,
            "logits": logits, "true_label_id": label2id[inst.true_label],
        })

    calibration = [r for r in per_example if r["split"] == "calibration"]
    test = [r for r in per_example if r["split"] == "test"]
    print(f"calibration={len(calibration)}, test={len(test)}")

    print("fitting temperature on calibration split only...")
    temperature = _fit_temperature(
        [r["logits"] for r in calibration],
        [r["true_label_id"] for r in calibration],
    )
    print(f"fitted temperature T={temperature}")

    def _temp_confidence(row):
        scaled = torch.softmax(row["logits"] / temperature, dim=-1).tolist()
        # confidence of the ALREADY-CHOSEN predicted class (temperature scaling
        # does not change argmax, only the confidence magnitude)
        pred_idx = max(range(len(scaled)), key=lambda i: row["logits"][i].item())
        return scaled[pred_idx]

    candidates = {
        "baseline_softmax_confidence": lambda r: r["baseline_confidence"],
        "margin": lambda r: min(1.0, r["margin"] / 1.0),
        "entropy_based_confidence": lambda r: 1.0 - r["entropy"],
        "temperature_scaled_confidence": _temp_confidence,
    }

    results = {"corpus_version": corpus_version, "n_total": len(instances), "n_calibration": len(calibration), "n_test": len(test), "fitted_temperature": temperature, "candidates": {}}
    for name, fn in candidates.items():
        records = [
            UncertaintyRecord(example_id=r["example_id"], is_correct=r["is_correct"], confidence=float(fn(r)), mechanism=name, task_family="classification")
            for r in test
        ]
        metrics = compute_uncertainty_metrics(records)
        metrics.pop("risk_coverage_curve", None)  # verbose; omitted from the summary JSON, full detail not needed for the verdict
        results["candidates"][name] = metrics
        print(f"{name}: AUROC={metrics.get('auroc_error_detection')}, Brier={metrics.get('brier_score')}, ECE={metrics.get('ece')}")

    baseline_auroc = results["candidates"]["baseline_softmax_confidence"]["auroc_error_detection"]
    best_name, best_auroc = None, None
    for name, m in results["candidates"].items():
        auroc = m.get("auroc_error_detection")
        if auroc is not None and (best_auroc is None or auroc > best_auroc):
            best_name, best_auroc = name, auroc
    improvement = (best_auroc - baseline_auroc) if (best_auroc is not None and baseline_auroc is not None) else None
    results["verdict"] = {
        "baseline_auroc": baseline_auroc, "best_candidate": best_name, "best_auroc": best_auroc,
        "improvement_over_baseline": improvement,
        "material_improvement": (improvement is not None and improvement > 0.03),
    }
    print("verdict:", results["verdict"])

    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw" / "p1_step5_sentiment_uncertainty_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("wrote raw/p1_step5_sentiment_uncertainty_results.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
