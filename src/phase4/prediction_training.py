"""Phase 4.5 gap 1 -- real training-corpus generation + model training for
``TrainedRiskPredictor`` (src/phase4/prediction.py).

Honesty notes, read before trusting any number this module reports:

  - Several of the widened failure taxonomy's classes (GPU_DEVICE_FAILURE,
    DATA_CORRUPTION, and RESOURCE_UNAVAILABLE when the port is already
    externally occupied) fail at or extremely close to
    ``execution_started`` -- there is often zero, or exactly one, telemetry
    sample before the failure. A predictor CANNOT have a real leading
    indicator for a failure with no pre-failure observation to condition
    on; this is a structural property of those workloads, not a modeling
    shortfall. Recall/lead-time for those classes is expected to be low or
    zero, and this module reports whatever it actually measures per class
    rather than only an aggregate number that would hide this.
  - PROCESS_OOM and PROCESS_TIMEOUT are the two classes with a genuine
    telemetry precursor (growing RSS / elapsed time), so this is where the
    predictor has real signal to learn from.
  - The train/validation/test split is by disjoint SEED BLOCKS (see
    ``SplitSeeds`` below): every scenario for a given seed is generated
    exactly once and its every rolling checkpoint stays entirely inside
    that seed's split, so no run's telemetry (and no run's ``workload_id``,
    since each seed also gets its own workload_id) crosses a split boundary.
"""
from __future__ import annotations

import json
import pickle
import random
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .monitoring import MonitoringBaseline
from .observability import PersistentEventStore
from .prediction import (
    DecisionThresholdCalibrator,
    FEATURE_NAMES,
    PREDICTABLE_MODES,
    PREDICTION_VERSION,
    extract_features,
    rolling_checkpoints,
)

TRAINING_PROTOCOL_VERSION = "phase4.5-prediction-training-v1"


@dataclass(frozen=True)
class SplitSeeds:
    train: range
    validation: range
    test: range


@dataclass(frozen=True)
class CorpusRow:
    seed: int
    split: str
    run_id: str
    workload_id: str
    failure_class: str | None
    label: int  # 1 if the run eventually fails, 0 otherwise
    checkpoint_index: int
    checkpoint_time: str
    time_to_failure_seconds: float | None
    features: tuple[float, ...]
    # Phase 4.5b: the workload's configured `mode` param -- real, known-at-
    # decision-time information (not a leaked label) that PredictionScopeRouter
    # routes on. Defaulted so every pre-existing direct CorpusRow(...)
    # construction (e.g. in tests) keeps working unchanged.
    mode: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dt(x: str) -> datetime:
    return datetime.fromisoformat(str(x).replace("Z", "+00:00"))


def scenario_for_seed(seed: int) -> tuple[str, dict]:
    """Deterministic-given-seed scenario recipe. Covers every failure class
    the controlled runtime supports, deliberately including both a failing
    and a non-failing variant of every family where the runtime can produce
    one (see module docstring for the two families where it genuinely
    cannot: GPU has no real device to succeed against in this environment)."""
    rng = random.Random(seed)
    family = rng.choice([
        "success", "timeout", "nonzero_exit", "network",
        "oom_fail", "oom_ok", "corruption", "gpu",
        "resource_fail", "resource_ok", "flaky_fail_then_ok", "flaky_ok",
    ])
    if family == "success":
        return "success", {"mode": "success"}
    if family == "timeout":
        # timeout_seconds is fixed at 0.15s for every corpus run (see
        # generate_corpus); durations below/above that boundary produce both
        # labels from the same family.
        duration = rng.choice([0.05, 0.08, 0.30, 0.45])
        return "timeout_via_cpu", {"mode": "cpu", "duration_seconds": duration}
    if family == "nonzero_exit":
        return "fail", {"mode": "fail"}
    if family == "network":
        return "network", {"mode": "network", "duration_seconds": 0.05}
    if family == "oom_fail":
        return "oom", {"mode": "oom", "alloc_mb": rng.choice([120, 200, 300]), "limit_mb": 32}
    if family == "oom_ok":
        return "oom", {"mode": "oom", "alloc_mb": 8, "limit_mb": 256}
    if family == "corruption":
        return "corruption", {"mode": "corruption"}
    if family == "gpu":
        return "gpu", {"mode": "gpu"}
    if family == "resource_fail":
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 40000 + (seed % 2000), "_occupy": True}
    if family == "resource_ok":
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 40000 + (seed % 2000), "_occupy": False}
    if family == "flaky_fail_then_ok":
        return "flaky", {"mode": "flaky", "fail_count": rng.choice([1, 2])}
    return "flaky", {"mode": "flaky", "fail_count": 0}  # flaky_ok: never fails


def generate_corpus_rows(seeds: Sequence[int], split: str, timeout_seconds: float = 0.15, environment_id: str | None = None) -> list[CorpusRow]:
    baseline = MonitoringBaseline()
    rows: list[CorpusRow] = []
    with tempfile.TemporaryDirectory() as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        config = RuntimeConfig(timeout_seconds=timeout_seconds, telemetry_interval_seconds=0.01, **({"environment_id": environment_id} if environment_id else {}))
        runtime = ControlledRuntime(store, config)
        for seed in seeds:
            workload_type, params = scenario_for_seed(seed)
            params = dict(params)
            occupy = params.pop("_occupy", None)
            if occupy:
                runtime.occupy_external_resource(int(params["port"]))
            workload_id = f"{split}-seed-{seed}"
            mode = str(params.get("mode") or workload_type)
            result = runtime.run(workload_type, params, workload_id=workload_id)
            failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
            label = 1 if failure_events else 0
            failure_class = str(failure_events[0]["payload"].get("failure_kind")) if failure_events else None
            failure_ts = _dt(str(failure_events[0]["timestamp"])) if failure_events else None
            for idx, (checkpoint_time, prefix) in enumerate(rolling_checkpoints(result.events, result.collection_start)):
                if failure_ts is not None and _dt(checkpoint_time) >= failure_ts:
                    continue  # never let a checkpoint see at/after its own run's failure
                features = extract_features(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                ttf = (failure_ts - _dt(checkpoint_time)).total_seconds() if failure_ts is not None else None
                rows.append(CorpusRow(
                    seed=seed, split=split, run_id=result.run_id, workload_id=workload_id,
                    failure_class=failure_class, label=label, checkpoint_index=idx,
                    checkpoint_time=checkpoint_time, time_to_failure_seconds=ttf,
                    features=features.as_vector(), mode=mode,
                ))
        store.close()
    return rows


def generate_corpus(seeds: SplitSeeds, timeout_seconds: float = 0.15) -> dict[str, list[CorpusRow]]:
    return {
        "train": generate_corpus_rows(list(seeds.train), "train", timeout_seconds),
        "validation": generate_corpus_rows(list(seeds.validation), "validation", timeout_seconds),
        "test": generate_corpus_rows(list(seeds.test), "test", timeout_seconds),
    }


def _xy(rows: list[CorpusRow]):
    return [list(r.features) for r in rows], [r.label for r in rows]


def calibrate_threshold(model, val_rows: list[CorpusRow]) -> float:
    from sklearn.metrics import precision_recall_curve

    if not val_rows or len(set(r.label for r in val_rows)) < 2:
        return 0.5  # not enough label diversity to calibrate against; fall back to the neutral default
    x_val, y_val = _xy(val_rows)
    scores = model.predict_proba(x_val)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_val, scores)
    f1 = [
        (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
        for p, r in zip(precision[:-1], recall[:-1])
    ]
    if not f1:
        return 0.5
    best_index = max(range(len(f1)), key=lambda i: f1[i])
    return float(thresholds[best_index])


def evaluate(model, threshold: float, test_rows: list[CorpusRow]) -> dict[str, Any]:
    from sklearn.metrics import roc_auc_score, brier_score_loss

    x_test, y_test = _xy(test_rows)
    scores = model.predict_proba(x_test)[:, 1]
    preds = [1 if s >= threshold else 0 for s in scores]

    tp = sum(1 for p, y in zip(preds, y_test) if p == 1 and y == 1)
    fp = sum(1 for p, y in zip(preds, y_test) if p == 1 and y == 0)
    fn = sum(1 for p, y in zip(preds, y_test) if p == 0 and y == 1)
    tn = sum(1 for p, y in zip(preds, y_test) if p == 0 and y == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    auc = roc_auc_score(y_test, scores) if len(set(y_test)) > 1 else None
    brier = brier_score_loss(y_test, scores)

    # Run-level early-warning / lead-time evidence: for every FAILING run
    # that has at least one checkpoint in the test split, did the model fire
    # (score >= threshold) at any checkpoint before the failure, and if so
    # what was the real lead time (in seconds, from that checkpoint's own
    # wall-clock timestamp to the run's real failure timestamp)?
    by_run: dict[str, list[tuple[CorpusRow, float]]] = {}
    for row, score in zip(test_rows, scores):
        by_run.setdefault(row.run_id, []).append((row, float(score)))
    lead_times: list[float] = []
    per_class_counts: dict[str, dict[str, int]] = {}
    run_level_tp = run_level_fn = 0
    for run_id, row_scores in by_run.items():
        row_scores_sorted = sorted(row_scores, key=lambda pair: pair[0].checkpoint_index)
        fclass = row_scores_sorted[0][0].failure_class or "NONE"
        counts = per_class_counts.setdefault(fclass, {"runs": 0, "fired_before_failure": 0})
        if row_scores_sorted[0][0].label == 1:
            counts["runs"] += 1
            fired = False
            for row, score in row_scores_sorted:
                if score >= threshold:
                    lead_times.append(row.time_to_failure_seconds or 0.0)
                    counts["fired_before_failure"] += 1
                    fired = True
                    break
            if fired:
                run_level_tp += 1
            else:
                run_level_fn += 1

    lead_times_sorted = sorted(lead_times)

    def _pct(p: float) -> float | None:
        if not lead_times_sorted:
            return None
        k = min(len(lead_times_sorted) - 1, int(round(p * (len(lead_times_sorted) - 1))))
        return lead_times_sorted[k]

    return {
        "per_checkpoint": {
            "n": len(test_rows), "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
            "precision": precision, "recall": recall, "f1": f1, "auc": auc, "brier_score": brier, "threshold": threshold,
        },
        "run_level_early_warning": {
            "true_positive_runs": run_level_tp, "false_negative_runs": run_level_fn,
            "lead_time_seconds": {
                "count": len(lead_times_sorted),
                "mean": (sum(lead_times_sorted) / len(lead_times_sorted)) if lead_times_sorted else None,
                "median": _pct(0.5), "p10": _pct(0.10), "p90": _pct(0.90),
                "min": lead_times_sorted[0] if lead_times_sorted else None,
                "max": lead_times_sorted[-1] if lead_times_sorted else None,
            },
            "per_failure_class": per_class_counts,
        },
    }


def train_and_persist(seeds: SplitSeeds, output_dir: str | Path, timeout_seconds: float = 0.15) -> dict[str, Any]:
    """End-to-end: generate the corpus, fit a real scikit-learn model, pick
    a real calibrated threshold, evaluate on the held-out test split, and
    persist a versioned artifact (reusing
    ``src.reliability.artifacts.save_reliability_artifact`` unmodified).
    Returns the same metrics dict this function persists to
    ``output_dir/metrics.json``, so a caller (or a test) never has to
    re-derive them from the artifact."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from src.reliability.artifacts import save_reliability_artifact

    corpus = generate_corpus(seeds, timeout_seconds=timeout_seconds)
    train_rows, val_rows, test_rows = corpus["train"], corpus["validation"], corpus["test"]
    if len(set(r.label for r in train_rows)) < 2:
        raise ValueError("training corpus has only one class present; cannot fit a classifier")

    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    x_train, y_train = _xy(train_rows)
    model.fit(x_train, y_train)

    threshold = calibrate_threshold(model, val_rows)
    test_metrics = evaluate(model, threshold, test_rows)

    calibrator = DecisionThresholdCalibrator(threshold=threshold)
    manifest = save_reliability_artifact(
        output_dir,
        model=model,
        calibrator=calibrator,
        artifact_version="phase4.5-prediction-artifact-v1",
        model_id="phase4-telemetry-risk-logreg",
        model_version="phase4.5-logreg-v1",
        calibrator_version="phase4.5-pr-curve-threshold-v1",
        feature_schema_version="phase4.5-features-v1",
        feature_names=list(FEATURE_NAMES),
        training_dataset_id=f"phase4.5-train-seeds-{seeds.train.start}-{seeds.train.stop}",
        validation_dataset_id=f"phase4.5-val-seeds-{seeds.validation.start}-{seeds.validation.stop}",
        evaluation_dataset_id=f"phase4.5-test-seeds-{seeds.test.start}-{seeds.test.stop}",
        training_timestamp=_now(),
        repository_commit="phase4.5-working-tree",
        protocol_version=TRAINING_PROTOCOL_VERSION,
        protocol_hash="n/a-controlled-runtime-generated-not-a-fixed-config-file",
        evaluation_metrics={k: v for k, v in test_metrics["per_checkpoint"].items() if isinstance(v, (int, float)) and v is not None},
        calibration_metrics={"brier_score": test_metrics["per_checkpoint"]["brier_score"], "threshold": threshold},
    )
    result = {
        "manifest": manifest.to_dict(),
        "corpus_sizes": {"train_rows": len(train_rows), "validation_rows": len(val_rows), "test_rows": len(test_rows),
                          "train_seeds": len(list(seeds.train)), "validation_seeds": len(list(seeds.validation)), "test_seeds": len(list(seeds.test))},
        "threshold": threshold,
        "test_metrics": test_metrics,
    }
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    return result


# ---------------------------------------------------------------------------
# Phase 4.5b -- honest fix for "recognize when it's likely wrong": rather
# than keep tuning one blended model against a near-chance aggregate AUC,
# split evaluation (and training) by whether the workload's mode can ever
# produce a real pre-failure telemetry precursor. See prediction.py's
# PredictionScopeRouter and this module's own top-level docstring.
# ---------------------------------------------------------------------------

def restrict_to_predictable_scope(rows: list[CorpusRow]) -> list[CorpusRow]:
    """Keep only checkpoints from workloads whose configured mode can
    produce a class with a genuine telemetry precursor (PROCESS_TIMEOUT via
    ``mode=cpu``, PROCESS_OOM via ``mode=oom``) -- both the failing and the
    non-failing runs of those two families. This is exactly the population
    ``PredictionScopeRouter`` routes to its trained model at inference time,
    so evaluating on anything wider or narrower would misstate what that
    model is actually asked to do in production."""
    return [r for r in rows if r.mode in PREDICTABLE_MODES]


def compute_fallback_priors(rows: list[CorpusRow]) -> dict[str, float]:
    """Empirical historical failure rate per mode, computed at the RUN level
    (one label per run_id, not one per checkpoint -- a run with many
    checkpoints must not be overweighted relative to one with few) from
    whatever rows are passed in. Callers must pass only train+validation
    rows here, never test rows -- these priors are meant to be a fixed
    constant fitted before evaluation, exactly like the calibrated
    threshold, not something that peeks at the held-out test split."""
    by_run: dict[str, tuple[str, int]] = {}
    for row in rows:
        by_run[row.run_id] = (row.mode, row.label)
    totals: dict[str, list[int]] = {}
    for mode, label in by_run.values():
        totals.setdefault(mode, []).append(label)
    return {mode: (sum(labels) / len(labels)) for mode, labels in totals.items() if labels}


def _scope_label(mode: str) -> str:
    return "predictable_scope" if mode in PREDICTABLE_MODES else "detectable_only_scope"


def evaluate_by_scope(model, threshold: float, test_rows: list[CorpusRow], fallback_priors: dict[str, float], default_fallback: float = 0.5) -> dict[str, Any]:
    """Honest, non-blended evaluation of the full ``PredictionScopeRouter``
    behavior on the test split: for ``predictable_scope`` rows, scores come
    from the real trained model (the same one ``evaluate()`` reports on,
    restricted to this population); for ``detectable_only_scope`` rows,
    scores are the fixed fallback prior the router would actually return
    (never the trained model's opinion on data it was never meant to
    generalize to). Returns per-scope metrics plus the same aggregate the
    original ``evaluate()`` computes, so the blended number that motivated
    this fix is still visible for direct comparison, not hidden."""
    from sklearn.metrics import roc_auc_score, brier_score_loss

    predictable_rows = [r for r in test_rows if r.mode in PREDICTABLE_MODES]
    other_rows = [r for r in test_rows if r.mode not in PREDICTABLE_MODES]

    scores: dict[int, float] = {}
    if predictable_rows:
        x_pred, _ = _xy(predictable_rows)
        pred_scores = model.predict_proba(x_pred)[:, 1]
        for row, score in zip(predictable_rows, pred_scores):
            scores[id(row)] = float(score)
    for row in other_rows:
        scores[id(row)] = float(fallback_priors.get(row.mode, default_fallback))

    def _metrics_for(rows: list[CorpusRow]) -> dict[str, Any]:
        if not rows:
            return {"n": 0}
        y = [r.label for r in rows]
        s = [scores[id(r)] for r in rows]
        preds = [1 if v >= threshold else 0 for v in s]
        tp = sum(1 for p, yy in zip(preds, y) if p == 1 and yy == 1)
        fp = sum(1 for p, yy in zip(preds, y) if p == 1 and yy == 0)
        fn = sum(1 for p, yy in zip(preds, y) if p == 0 and yy == 1)
        tn = sum(1 for p, yy in zip(preds, y) if p == 0 and yy == 0)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        auc = roc_auc_score(y, s) if len(set(y)) > 1 else None
        brier = brier_score_loss(y, s)
        return {
            "n": len(rows), "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
            "precision": precision, "recall": recall, "f1": f1, "auc": auc, "brier_score": brier,
        }

    return {
        "threshold": threshold,
        # NOT comparable to the original gap-1 single blended model's
        # AUC (~0.515, reported in docs/PHASE4_5_GAP_FIXES_REPORT.md):
        # that model never saw `mode` at all. This number is the
        # ROUTER's own combined-output AUC across every test row --
        # predictable-scope rows get the real trained model's score,
        # detectable-only rows get a FIXED per-mode constant. Because
        # different modes have different true failure base rates, even a
        # constant-per-mode "prediction" carries real separating power at
        # the mode level (e.g. `success` mode never fails, `gpu` mode
        # nearly always does) -- this key measures that combined effect,
        # not a second attempt at telemetry-based discrimination.
        "router_combined_output_all_scopes": _metrics_for(test_rows),
        "predictable_scope": _metrics_for(predictable_rows),
        "detectable_only_scope": _metrics_for(other_rows),
    }


def train_and_persist_scope_router(seeds: SplitSeeds, output_dir: str | Path, timeout_seconds: float = 0.15) -> dict[str, Any]:
    """End-to-end Phase 4.5b training/evaluation/persistence for the honest,
    scope-split predictor. Generates the same full corpus as
    ``train_and_persist`` (so both can be compared on identical data), then:

      1. Fits a model ONLY on ``predictable_scope`` rows (mode in cpu/oom)
         -- the actual population ``PredictionScopeRouter`` will ever send
         to it -- and calibrates/evaluates it on that same scope.
      2. Computes fixed fallback priors per non-predictable mode from
         train+validation rows only (never test).
      3. Reports ``evaluate_by_scope`` on the test split: predictable-scope
         metrics (real skill, if any), detectable-only-scope metrics (the
         fallback's honest performance), and the blended aggregate for
         direct comparison against the un-split model in
         ``experiments/results/.../metrics.json``.
      4. Persists the predictable-scope model as a versioned artifact
         (reusing the same ``save_reliability_artifact`` path as
         ``train_and_persist``) plus ``fallback_priors.json`` alongside it,
         so ``PredictionScopeRouter.load(output_dir)`` reconstructs the
         whole router from one directory.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from src.reliability.artifacts import save_reliability_artifact

    corpus = generate_corpus(seeds, timeout_seconds=timeout_seconds)
    train_rows, val_rows, test_rows = corpus["train"], corpus["validation"], corpus["test"]

    predictable_train = restrict_to_predictable_scope(train_rows)
    predictable_val = restrict_to_predictable_scope(val_rows)
    if len(set(r.label for r in predictable_train)) < 2:
        raise ValueError("predictable-scope training corpus has only one class present; widen the seed range")

    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    x_train, y_train = _xy(predictable_train)
    model.fit(x_train, y_train)

    threshold = calibrate_threshold(model, predictable_val)
    fallback_priors = compute_fallback_priors(train_rows + val_rows)
    scoped_metrics = evaluate_by_scope(model, threshold, test_rows, fallback_priors)

    calibrator = DecisionThresholdCalibrator(threshold=threshold)
    manifest = save_reliability_artifact(
        output_dir,
        model=model,
        calibrator=calibrator,
        artifact_version="phase4.5b-prediction-scope-router-artifact-v1",
        model_id="phase4-telemetry-risk-logreg-predictable-scope",
        model_version="phase4.5b-logreg-predictable-scope-v1",
        calibrator_version="phase4.5b-pr-curve-threshold-v1",
        feature_schema_version="phase4.5-features-v1",
        feature_names=list(FEATURE_NAMES),
        training_dataset_id=f"phase4.5b-train-predictable-scope-seeds-{seeds.train.start}-{seeds.train.stop}",
        validation_dataset_id=f"phase4.5b-val-predictable-scope-seeds-{seeds.validation.start}-{seeds.validation.stop}",
        evaluation_dataset_id=f"phase4.5b-test-seeds-{seeds.test.start}-{seeds.test.stop}",
        training_timestamp=_now(),
        repository_commit="phase4.5b-working-tree",
        protocol_version=TRAINING_PROTOCOL_VERSION,
        protocol_hash="n/a-controlled-runtime-generated-not-a-fixed-config-file",
        evaluation_metrics={k: v for k, v in scoped_metrics["predictable_scope"].items() if isinstance(v, (int, float)) and v is not None},
        calibration_metrics={"brier_score": scoped_metrics["predictable_scope"].get("brier_score"), "threshold": threshold},
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "fallback_priors.json").write_text(json.dumps(fallback_priors, indent=2, sort_keys=True) + "\n")

    result = {
        "manifest": manifest.to_dict(),
        "corpus_sizes": {
            "train_rows": len(train_rows), "validation_rows": len(val_rows), "test_rows": len(test_rows),
            "predictable_scope_train_rows": len(predictable_train), "predictable_scope_validation_rows": len(predictable_val),
        },
        "threshold": threshold,
        "fallback_priors": fallback_priors,
        "scoped_test_metrics": scoped_metrics,
    }
    (Path(output_dir) / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    return result
