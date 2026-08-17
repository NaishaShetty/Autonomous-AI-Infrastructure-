"""Phase 3.6.3: deterministic, rule-based failure-cause diagnosis.

Pools FAILURE samples (is_failure==1) across the clean condition and
Phase 3.5's three attack conditions (reusing
``benchmarks.phase3_5_attack_generalization``'s condition builders and
frozen protocol verbatim) and evaluates
``src.evaluation.diagnosis.diagnose`` -- a deterministic rule, not a
trained model -- against the known ground-truth condition each sample
actually came from.

Run: python benchmarks/phase3_6_diagnosis.py
Writes: experiments/results/phase3_6/diagnosis.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES  # noqa: E402
from src.evaluation.diagnosis import DIAGNOSIS_CLASSES, condition_to_true_class, diagnose  # noqa: E402
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402
from benchmarks.phase3_5_attack_generalization import _condition_test_samples, load_protocol35  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_6"


def run_one_seed(seed: int, protocol: Phase31Protocol, protocol35: dict) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    all_conditions = [protocol35["clean_reference_condition"]] + protocol35["attack_matrix"]

    y_true, y_pred = [], []
    for condition in all_conditions:
        true_class = condition_to_true_class(condition["id"])
        test_samples = _condition_test_samples(condition, seed, system)
        for s in test_samples:
            x = np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)
            pred = system.workload_model.predict(x)
            is_failure = pred.predicted_label != s.label
            if not is_failure:
                continue
            y_true.append(true_class)
            y_pred.append(diagnose(s.context, FEATURE_NAMES))

    return {"seed": seed, "n_failures": len(y_true), "y_true": y_true, "y_pred": y_pred}


def _confusion_matrix(y_true: list[str], y_pred: list[str]) -> dict:
    return {
        t: {p: sum(1 for yt, yp in zip(y_true, y_pred) if yt == t and yp == p) for p in DIAGNOSIS_CLASSES}
        for t in DIAGNOSIS_CLASSES
    }


def _per_class_precision_recall(y_true: list[str], y_pred: list[str]) -> dict:
    out = {}
    for c in DIAGNOSIS_CLASSES:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp == c)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != c and yp == c)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn) if (tp + fn) > 0 else None
        f1 = (2 * precision * recall / (precision + recall)) if precision and recall and (precision + recall) > 0 else 0.0
        out[c] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return out


def evaluate_one_seed(row: dict) -> dict:
    y_true, y_pred = row["y_true"], row["y_pred"]
    n = len(y_true)
    accuracy = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / n if n else None
    per_class = _per_class_precision_recall(y_true, y_pred)
    f1_values = [v["f1"] for v in per_class.values() if v["support"] > 0]
    macro_f1 = float(np.mean(f1_values)) if f1_values else None
    return {
        "n_failures": n,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": _confusion_matrix(y_true, y_pred),
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()
    protocol35 = load_protocol35()

    per_seed_raw = [run_one_seed(seed, protocol, protocol35) for seed in protocol.seeds]
    per_seed_eval = [{"seed": row["seed"], **evaluate_one_seed(row)} for row in per_seed_raw]

    accuracy_vals = [r["accuracy"] for r in per_seed_eval if r["accuracy"] is not None]
    macro_f1_vals = [r["macro_f1"] for r in per_seed_eval if r["macro_f1"] is not None]
    aggregate = {
        "accuracy": _t_interval(accuracy_vals, 0.95),
        "macro_f1": _t_interval(macro_f1_vals, 0.95),
    }

    pooled_true = [c for row in per_seed_raw for c in row["y_true"]]
    pooled_pred = [c for row in per_seed_raw for c in row["y_pred"]]
    pooled = evaluate_one_seed({"y_true": pooled_true, "y_pred": pooled_pred})

    output = {
        "meta": {"classes": DIAGNOSIS_CLASSES, "protocol35_attack_matrix": protocol35["attack_matrix"], "diagnosis_rule": protocol35 is not None and "deterministic, see src/evaluation/diagnosis.py"},
        "per_seed": per_seed_eval,
        "aggregate": aggregate,
        "pooled_across_all_seeds": pooled,
    }
    (RESULTS_DIR / "diagnosis.json").write_text(json.dumps(output, indent=2))

    print("Phase 3.6.3 diagnosis\n")
    for row in per_seed_eval:
        print(f"seed {row['seed']:>3}: n_failures={row['n_failures']:>4} accuracy={row['accuracy']:.4f} macro_f1={row['macro_f1']:.4f}")
    print(f"\nAggregate accuracy: {aggregate['accuracy']['mean']:.4f}  macro_f1: {aggregate['macro_f1']['mean']:.4f}")
    print(f"\nPooled confusion matrix: {json.dumps(pooled['confusion_matrix'], indent=2)}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
