"""Post-P5-remediation follow-up 5 -- OOM operating-point follow-up.

Step 3 (``P3_PREDICTABILITY_REMEDIATION_REPORT.md``) found the `oom`
family's >=2-pre-outcome-telemetry-sample subset to be a "PLAUSIBLE,
UNCONFIRMED USEFUL PREDICTOR" (real AUROC ranking signal replicated vs. its
own shuffled control) but explicitly flagged that false-alarm-rate/
specificity were NOT computed per-subset, so operating-point usability was
never established -- only ranking quality was.

This script freezes the EXACT same predictor/feature set Step 3 used for
`oom` (`prediction_features_v3.py`'s 6-feature `full_v3` interface, the
same `StandardScaler`+`LogisticRegression` model, the same 3-replicate
protocol and seed ranges as ``protocol/P3_STEP3_PROTOCOL.md``) -- no
redesign, no new feature. The model and its calibrated threshold are fit
ONCE per replicate on the full `oom` family population (train+validation),
exactly as Step 3 did; ONLY the TEST evaluation is then split into the
>=2-sample subset and the 0-1-sample control subset, and full operating-
point metrics (not just AUROC) are computed for each subset separately.
The threshold is never re-selected using either test subset's outcomes.

Usage:
    python scripts/run_followup5_oom_operating_point.py <run_dir>

Writes:
    <run_dir>/raw/followup5_oom_operating_point.json
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
from src.phase4.prediction_features_v3 import generate_corpus_rows_v3
from src.phase4.prediction_training import calibrate_threshold, _xy

TIMEOUT_SECONDS = 0.15
# IDENTICAL to protocol/P3_STEP3_PROTOCOL.md's pre-registered ranges.
REPLICATE_SEED_RANGES = [
    {"train": range(0, 400), "validation": range(2000, 2100), "test": range(4000, 4300)},
    {"train": range(10_000, 10_400), "validation": range(12_000, 12_100), "test": range(14_000, 14_300)},
    {"train": range(20_000, 20_400), "validation": range(22_000, 22_100), "test": range(24_000, 24_300)},
]
FAMILY = "oom"


def _extend_metrics(base_metrics):
    tp, fp, fn, tn = base_metrics["true_positives"], base_metrics["false_positives"], base_metrics["false_negatives"], base_metrics["true_negatives"]
    specificity = (tn / (tn + fp)) if (tn + fp) else None
    fpr = (fp / (fp + tn)) if (fp + tn) else None
    detection_before_failure_rate = (
        base_metrics["run_level_true_positives"] / (base_metrics["run_level_true_positives"] + base_metrics["run_level_false_negatives"])
    ) if (base_metrics["run_level_true_positives"] + base_metrics["run_level_false_negatives"]) else None
    return {**base_metrics, "specificity": specificity, "false_positive_rate": fpr, "detection_before_failure_rate": detection_before_failure_rate}


def _wilson_ci(successes: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z ** 2 / n
    centre = p + z ** 2 / (2 * n)
    margin = z * ((p * (1 - p) / n + z ** 2 / (4 * n ** 2)) ** 0.5)
    return ((centre - margin) / denom, (centre + margin) / denom)


def _aggregate(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "std": None, "n": 0}
    return {"mean": mean(vals), "std": pstdev(vals) if len(vals) > 1 else 0.0, "n": len(vals)}


def main(run_dir: Path) -> None:
    print("Generating corpora for 3 replicates (oom family, frozen full_v3 predictor)...")
    replicate_corpora = []
    for i, seed_range in enumerate(REPLICATE_SEED_RANGES):
        print(f"  replicate {i}: train/val/test...")
        replicate_corpora.append({
            split: generate_corpus_rows_v3(list(seed_range[split]), f"r{i}-{split}", TIMEOUT_SECONDS)
            for split in ("train", "validation", "test")
        })

    subset_results = {"ge2_samples": [], "lt2_samples": []}
    shuffled_subset_results = {"ge2_samples": [], "lt2_samples": []}

    for rep_idx, corpus in enumerate(replicate_corpora):
        train_rows = [r for r in corpus["train"] if r.mode == FAMILY]
        val_rows = [r for r in corpus["validation"] if r.mode == FAMILY]
        test_rows_all = [r for r in corpus["test"] if r.mode == FAMILY]

        if len(set(r.label for r in train_rows)) < 2:
            print(f"  replicate {rep_idx}: train has single class, skipping")
            continue

        # Frozen model + threshold, fit ONCE on the full family population --
        # never refit or re-thresholded using either test subset.
        model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
        x_train, y_train = _xy(train_rows)
        model.fit(x_train, y_train)
        threshold = calibrate_threshold(model, val_rows)

        shuffle_seed = _stable_seed("phase4.post_p5.followup5-label-shuffle", str(len(train_rows)), str(rep_idx))
        shuffled_train = _shuffle_labels_by_run(train_rows, shuffle_seed)
        shuffled_val = _shuffle_labels_by_run(val_rows, shuffle_seed + 1)
        shuf_model = None
        shuf_threshold = None
        if len(set(r.label for r in shuffled_train)) >= 2:
            shuf_model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
            x_shuf, y_shuf = _xy(shuffled_train)
            shuf_model.fit(x_shuf, y_shuf)
            shuf_threshold = calibrate_threshold(shuf_model, shuffled_val)

        for label, predicate in (("ge2_samples", lambda r: r.n_telemetry_samples >= 2), ("lt2_samples", lambda r: r.n_telemetry_samples < 2)):
            subset_rows = [r for r in test_rows_all if predicate(r)]
            if len(set(r.label for r in subset_rows)) < 2:
                subset_results[label].append(None)
                shuffled_subset_results[label].append(None)
                continue
            metrics = _extend_metrics(_compute_metrics_base(model, threshold, subset_rows))
            metrics["n_test_rows"] = len(subset_rows)
            metrics["n_positive"] = sum(r.label for r in subset_rows)
            metrics["precision_wilson_ci95"] = _wilson_ci(metrics["true_positives"], metrics["true_positives"] + metrics["false_positives"])
            metrics["recall_wilson_ci95"] = _wilson_ci(metrics["true_positives"], metrics["true_positives"] + metrics["false_negatives"])
            metrics["specificity_wilson_ci95"] = _wilson_ci(metrics["true_negatives"], metrics["true_negatives"] + metrics["false_positives"])
            subset_results[label].append(metrics)

            if shuf_model is not None:
                shuf_metrics = _extend_metrics(_compute_metrics_base(shuf_model, shuf_threshold, subset_rows))
                shuffled_subset_results[label].append(shuf_metrics)
            else:
                shuffled_subset_results[label].append(None)

    out = {"protocol": "frozen full_v3 oom predictor from P3 Step 3, same 3 seed-range replicates, threshold never re-selected using either test subset", "subsets": {}}
    for label in ("ge2_samples", "lt2_samples"):
        reps = subset_results[label]
        shuf_reps = shuffled_subset_results[label]
        agg = {
            "auroc": _aggregate([r["auroc"] for r in reps if r is not None]),
            "auprc": _aggregate([r["auprc"] for r in reps if r is not None]),
            "brier_score": _aggregate([r["brier_score"] for r in reps if r is not None]),
            "ece": _aggregate([r["ece"] for r in reps if r is not None]),
            "precision": _aggregate([r["precision"] for r in reps if r is not None]),
            "recall": _aggregate([r["recall"] for r in reps if r is not None]),
            "specificity": _aggregate([r["specificity"] for r in reps if r is not None]),
            "false_positive_rate": _aggregate([r["false_positive_rate"] for r in reps if r is not None]),
            "false_alarm_rate": _aggregate([r["false_alarm_rate"] for r in reps if r is not None]),
            "detection_before_failure_rate": _aggregate([r["detection_before_failure_rate"] for r in reps if r is not None]),
            "lead_time_seconds_mean": _aggregate([r["lead_time_seconds_mean"] for r in reps if r is not None]),
            "useful_lead_time_seconds_mean": _aggregate([r["useful_lead_time_seconds_mean"] for r in reps if r is not None]),
            "shuffled_control_auroc": _aggregate([r["auroc"] for r in shuf_reps if r is not None]),
            "shuffled_control_false_alarm_rate": _aggregate([r["false_alarm_rate"] for r in shuf_reps if r is not None]),
        }
        fa = agg["false_alarm_rate"]["mean"]
        spec = agg["specificity"]["mean"]
        real_auroc = agg["auroc"]["mean"]
        shuf_auroc = agg["shuffled_control_auroc"]["mean"]
        real_std = agg["auroc"]["std"] or 0.0
        shuf_std = agg["shuffled_control_auroc"]["std"] or 0.0
        always_fires = fa is not None and fa >= 0.95
        clears_shuffled = (real_auroc is not None and shuf_auroc is not None and real_auroc > shuf_auroc + max(real_std, shuf_std))

        if always_fires:
            verdict = "NOT VALIDATED -- always-fires at calibrated operating point (false_alarm_rate={:.2f}), regardless of AUROC ranking quality".format(fa)
        elif not clears_shuffled:
            verdict = "NOT VALIDATED -- does not clear shuffled-label control at more than one pooled std"
        else:
            verdict = "OPERATIONALLY USABLE AT THIS OPERATING POINT -- clears shuffled control AND is not an always-fires predictor"

        out["subsets"][label] = {"replicate_metrics": reps, "aggregate_metrics": agg, "verdict": verdict, "always_fires_flag": always_fires}
        print(f"{label}: auroc={real_auroc}, false_alarm_rate={fa}, specificity={spec} -> {verdict}")

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "raw" / "followup5_oom_operating_point.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print("wrote raw/followup5_oom_operating_point.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
