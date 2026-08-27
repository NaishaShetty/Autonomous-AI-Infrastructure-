"""Post-P5-remediation follow-up 1 -- re-run P3 Step 3's `cpu`-family
predictability evaluation with the Step 7 CPU-timing-margin fix in place
(``prediction_training.py``'s 0.01s/0.02s "fast" duration choice + the
auto-widening train-seed-range backstop, both already applied to the
repository).

This script is a byte-for-byte behavioral copy of
``scripts/run_p3_step3_predictability.py`` restricted to the ``cpu`` family
(both the ``full_v3`` and ``elapsed_only`` variants) -- same replicate seed
ranges, same model, same shuffled-label control, same stopping rule. It
does NOT change any split, feature, model, or threshold-selection logic
from the original protocol (``protocol/P3_STEP3_PROTOCOL.md`` in the
original 20260825T064402Z run directory) -- that protocol is preserved
exactly; only the corpus generation now runs on top of the already-fixed
``prediction_training.py``/``prediction_features_v3.py`` code path, and
only the `cpu` family is evaluated (the other three families were not
affected by the CPU-timing defect and are not re-run here, per the
followups prompt's explicit scope).

Usage:
    python scripts/run_followup1_cpu_predictability.py <run_dir>

Writes:
    <run_dir>/raw/followup1_cpu_predictability.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, pstdev

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.phase4.prediction_eval_v2 import _stable_seed, _shuffle_labels_by_run, compute_metrics as _compute_metrics_base
from src.phase4.prediction_features_v3 import generate_corpus_rows_v3, FEATURE_NAMES_V3
from src.phase4.prediction_training import calibrate_threshold, _xy

TIMEOUT_SECONDS = 0.15
N_REPLICATES = 3
# IDENTICAL to protocol/P3_STEP3_PROTOCOL.md's pre-registered ranges --
# not changed for this re-run.
REPLICATE_SEED_RANGES = [
    {"train": range(0, 400), "validation": range(2000, 2100), "test": range(4000, 4300)},
    {"train": range(10_000, 10_400), "validation": range(12_000, 12_100), "test": range(14_000, 14_300)},
    {"train": range(20_000, 20_400), "validation": range(22_000, 22_100), "test": range(24_000, 24_300)},
]

ELAPSED_RATIO_INDEX = FEATURE_NAMES_V3.index("elapsed_ratio")


def _select_features(rows, indices):
    return [type(r)(**{**r.__dict__, "features": tuple(r.features[i] for i in indices)}) for r in rows]


def _prevalence_baseline_metrics(train_rows, test_rows):
    prevalence = (sum(r.label for r in train_rows) / len(train_rows)) if train_rows else 0.0
    y = [r.label for r in test_rows]
    scores = [prevalence] * len(test_rows)
    from sklearn.metrics import brier_score_loss
    brier = float(brier_score_loss(y, scores)) if y else None
    return {"prevalence": prevalence, "brier_score": brier}


def _extend_metrics(base_metrics):
    tp, fp, fn, tn = base_metrics["true_positives"], base_metrics["false_positives"], base_metrics["false_negatives"], base_metrics["true_negatives"]
    specificity = (tn / (tn + fp)) if (tn + fp) else None
    fpr = (fp / (fp + tn)) if (fp + tn) else None
    detection_before_failure_rate = (
        base_metrics["run_level_true_positives"] / (base_metrics["run_level_true_positives"] + base_metrics["run_level_false_negatives"])
    ) if (base_metrics["run_level_true_positives"] + base_metrics["run_level_false_negatives"]) else None
    return {**base_metrics, "specificity": specificity, "false_positive_rate": fpr, "detection_before_failure_rate": detection_before_failure_rate}


def _fit_eval(train_rows, val_rows, test_rows):
    if len(set(r.label for r in train_rows)) < 2 or len(set(r.label for r in test_rows)) < 2:
        return None
    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    x_train, y_train = _xy(train_rows)
    model.fit(x_train, y_train)
    threshold = calibrate_threshold(model, val_rows)
    real = _extend_metrics(_compute_metrics_base(model, threshold, test_rows))

    shuffle_seed = _stable_seed("phase4.post_p5.followup1-label-shuffle", str(len(train_rows)))
    shuffled_train = _shuffle_labels_by_run(train_rows, shuffle_seed)
    shuffled_val = _shuffle_labels_by_run(val_rows, shuffle_seed + 1)
    shuffled = None
    if len(set(r.label for r in shuffled_train)) >= 2:
        shuf_model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
        x_shuf, y_shuf = _xy(shuffled_train)
        shuf_model.fit(x_shuf, y_shuf)
        shuf_threshold = calibrate_threshold(shuf_model, shuffled_val)
        shuffled = _extend_metrics(_compute_metrics_base(shuf_model, shuf_threshold, test_rows))

    prevalence = _prevalence_baseline_metrics(train_rows, test_rows)
    return {"real": real, "shuffled_control": shuffled, "prevalence_baseline": prevalence}


def _aggregate(replicate_results, metric_path):
    vals = []
    for r in replicate_results:
        if r is None:
            continue
        v = r
        for key in metric_path:
            v = v.get(key) if v is not None else None
        if v is not None:
            vals.append(v)
    if not vals:
        return {"mean": None, "std": None, "n": 0}
    return {"mean": mean(vals), "std": pstdev(vals) if len(vals) > 1 else 0.0, "n": len(vals)}


def main(run_dir: Path) -> None:
    results = {"protocol_version": "phase4.post_p5.followup1-v1 (identical protocol to step3-v1, cpu family only, timing-fixed corpus)", "n_replicates": N_REPLICATES, "families": {}}

    print("Generating corpora for 3 replicates (cpu family, timing-fixed corpus generator)...")
    replicate_corpora = []
    for i, seed_range in enumerate(REPLICATE_SEED_RANGES):
        print(f"  replicate {i}: train/val/test...")
        replicate_corpora.append({
            split: generate_corpus_rows_v3(list(seed_range[split]), f"r{i}-{split}", TIMEOUT_SECONDS)
            for split in ("train", "validation", "test")
        })

    family = "cpu"
    results["families"][family] = {}
    variants = {"full_v3": list(range(len(FEATURE_NAMES_V3))), "elapsed_only": [ELAPSED_RATIO_INDEX]}

    for variant_name, feature_indices in variants.items():
        replicate_outputs = []
        for corpus in replicate_corpora:
            train_rows = [r for r in corpus["train"] if r.mode == family]
            val_rows = [r for r in corpus["validation"] if r.mode == family]
            test_rows = [r for r in corpus["test"] if r.mode == family]
            train_sel = _select_features(train_rows, feature_indices)
            val_sel = _select_features(val_rows, feature_indices)
            test_sel = _select_features(test_rows, feature_indices)
            replicate_outputs.append(_fit_eval(train_sel, val_sel, test_sel))

        agg = {
            "real_auroc": _aggregate(replicate_outputs, ["real", "auroc"]),
            "shuffled_auroc": _aggregate(replicate_outputs, ["shuffled_control", "auroc"]),
            "real_auprc": _aggregate(replicate_outputs, ["real", "auprc"]),
            "real_brier": _aggregate(replicate_outputs, ["real", "brier_score"]),
            "real_ece": _aggregate(replicate_outputs, ["real", "ece"]),
            "real_precision": _aggregate(replicate_outputs, ["real", "precision"]),
            "real_recall": _aggregate(replicate_outputs, ["real", "recall"]),
            "real_specificity": _aggregate(replicate_outputs, ["real", "specificity"]),
            "real_false_positive_rate": _aggregate(replicate_outputs, ["real", "false_positive_rate"]),
            "real_false_alarm_rate": _aggregate(replicate_outputs, ["real", "false_alarm_rate"]),
            "real_detection_before_failure_rate": _aggregate(replicate_outputs, ["real", "detection_before_failure_rate"]),
            "real_lead_time_seconds_mean": _aggregate(replicate_outputs, ["real", "lead_time_seconds_mean"]),
            "real_useful_lead_time_seconds_mean": _aggregate(replicate_outputs, ["real", "useful_lead_time_seconds_mean"]),
            "prevalence_baseline_brier": _aggregate(replicate_outputs, ["prevalence_baseline", "brier_score"]),
        }
        real_auroc_mean = agg["real_auroc"]["mean"]
        shuffled_auroc_mean = agg["shuffled_auroc"]["mean"]
        real_std = agg["real_auroc"]["std"] or 0.0
        shuffled_std = agg["shuffled_auroc"]["std"] or 0.0
        if real_auroc_mean is None or shuffled_auroc_mean is None:
            verdict = "UNDEFINED (single-class test set in >=1 replicate)"
        elif real_auroc_mean > shuffled_auroc_mean + max(real_std, shuffled_std):
            verdict = "SIGNAL: real AUROC exceeds shuffled control by more than one pooled std"
        else:
            verdict = "NO DEMONSTRATED PREDICTIVE SIGNAL under this observability regime"

        # always-fires check, same rule as Step 3's report used.
        fa = agg["real_false_alarm_rate"]["mean"]
        always_fires = fa is not None and fa >= 0.95

        results["families"][family][variant_name] = {
            "aggregate_metrics": agg, "mechanical_verdict": verdict,
            "always_fires_flag": always_fires,
            "n_replicates_evaluated": sum(1 for r in replicate_outputs if r is not None),
        }
        print(f"{family}/{variant_name}: real_auroc={real_auroc_mean}, shuffled_auroc={shuffled_auroc_mean}, false_alarm_rate={fa} -> {verdict} (always_fires={always_fires})")

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "raw" / "followup1_cpu_predictability.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print("wrote raw/followup1_cpu_predictability.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
