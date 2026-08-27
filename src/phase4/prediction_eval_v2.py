"""Phase 4.8 -- a scientifically valid, leak-free, per-failure-class
prediction evaluation, replacing the 0.857 "detectable-only" number as
evidence (that number was flagged in
``docs/archive/PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md`` as a mixing
artifact of blending deterministic-outcome failure classes together, and
must not be reused).

Core design decision: evaluate EVERY failure family WITHIN its own mode
population only (never blended across modes), exactly the precedent
``PredictionScopeRouter``/``restrict_to_predictable_scope`` already set
for ``cpu``/``oom`` -- generalized here to every mode
``scenario_for_seed`` (prediction_training.py) can produce, not just the
two the project had already singled out.

This surfaces a structural fact about the controlled runtime that the
project's own subprocess code already implies but had not stated
explicitly per-class: ``fail``, ``network``, ``gpu``, and ``corruption``
modes are each DETERMINISTIC -- every run of that mode fails, unconditionally,
regardless of parameters (see ``controlled_runtime.py``'s ``_SUBPROCESS_CODE``:
'fail' always ``sys.exit(7)``; 'network' always connects to a fixed
unroutable address; 'gpu' always finds no device in this sandbox;
'corruption' always flips a byte). A mode with only one possible outcome
has no label variance to predict -- AUROC/AUPRC are mathematically
undefined, not merely hard to estimate, and are reported as such
(``NOT_PREDICTABLE_SINGLE_CLASS``), never coerced to a fabricated number.

Only four modes are genuinely bimodal (both a failing and a non-failing
variant exist in ``prediction_training.scenario_for_seed``): ``cpu``
(timeout, duration vs. configured timeout), ``oom`` (alloc_mb vs.
limit_mb), ``resource_unavailable`` (port pre-occupied or not), and
``flaky`` (fail_count > 0 or = 0). These four get a real per-class
model, real per-class metrics, AND a label-shuffled negative control.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .prediction_training import CorpusRow, SplitSeeds, _xy, calibrate_threshold, generate_corpus

EVAL_V2_VERSION = "phase4.8-prediction-eval-v2"

# Every mode `scenario_for_seed` (prediction_training.py) can emit, and
# whether it has a genuine bimodal (failing/non-failing) population.
# Fixed here from direct inspection of controlled_runtime.py's subprocess
# code, before any evaluation is run -- not inferred from measured label
# variance after the fact (though the measured variance will, honestly,
# agree with this classification; see module docstring).
BIMODAL_FAMILY_MODES: dict[str, str] = {
    "cpu": "PROCESS_TIMEOUT",
    "oom": "PROCESS_OOM",
    "resource_unavailable": "RESOURCE_UNAVAILABLE",
    "flaky": "INTERMITTENT_TRANSIENT",
}
DETERMINISTIC_MODES: dict[str, str] = {
    "fail": "NONZERO_EXIT",
    "network": "NETWORK_ERROR",
    "gpu": "GPU_DEVICE_UNAVAILABLE",
    "corruption": "DATA_CHECKSUM_MISMATCH",
}
ALL_EVALUATED_MODES = {**BIMODAL_FAMILY_MODES, **DETERMINISTIC_MODES}

_ECE_BINS = 10
_USEFUL_LEAD_TIME_EPSILON_SECONDS = 0.01


def _ece(y: list[int], scores: list[float], n_bins: int = _ECE_BINS) -> float:
    y_arr, s_arr = np.array(y, dtype=float), np.array(scores, dtype=float)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(y_arr)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        in_bin = (s_arr > lo) & (s_arr <= hi) if i > 0 else (s_arr >= lo) & (s_arr <= hi)
        count = int(in_bin.sum())
        if count == 0:
            continue
        ece += (count / total) * abs(float(y_arr[in_bin].mean()) - float(s_arr[in_bin].mean()))
    return ece


def _stable_seed(*parts: str) -> int:
    """A seed derived from ``parts`` that is stable across processes.

    Python's builtin ``hash()`` on str/tuple is salted per-process by
    ``PYTHONHASHSEED`` (randomized by default) specifically to make
    dict/set ordering attack-resistant -- it is NOT a reproducible digest,
    despite looking like one. Using ``hash()`` here previously meant the
    shuffled-label negative control silently used a different seed on
    every interpreter invocation, so the "reproducible" claim in the
    caller's comment did not hold and results could differ run-to-run
    (including across separate pytest invocations of the same test).
    ``hashlib`` digests are stable across processes and Python versions by
    design, so they are used instead.
    """
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _shuffle_labels_by_run(rows: list[CorpusRow], seed: int) -> list[CorpusRow]:
    """The negative control: permute which RUN got which outcome label
    (not a per-row shuffle, which would create internally-inconsistent
    within-run labels) -- kills any real relationship between a run's own
    telemetry and its own outcome while preserving the feature
    distribution and the marginal label rate exactly."""
    run_ids = sorted({r.run_id for r in rows})
    labels_by_run = {r.run_id: r.label for r in rows}
    original_labels = [labels_by_run[rid] for rid in run_ids]
    shuffled = list(original_labels)
    random.Random(seed).shuffle(shuffled)
    shuffled_label_by_run = dict(zip(run_ids, shuffled))
    return [replace(r, label=shuffled_label_by_run[r.run_id]) for r in rows]


def compute_metrics(model, threshold: float, test_rows: list[CorpusRow]) -> dict[str, Any]:
    x_test, y_test = _xy(test_rows)
    scores = list(model.predict_proba(x_test)[:, 1])
    preds = [1 if s >= threshold else 0 for s in scores]

    tp = sum(1 for p, y in zip(preds, y_test) if p == 1 and y == 1)
    fp = sum(1 for p, y in zip(preds, y_test) if p == 1 and y == 0)
    fn = sum(1 for p, y in zip(preds, y_test) if p == 0 and y == 1)
    tn = sum(1 for p, y in zip(preds, y_test) if p == 0 and y == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    has_both_classes = len(set(y_test)) > 1
    auroc = float(roc_auc_score(y_test, scores)) if has_both_classes else None
    auprc = float(average_precision_score(y_test, scores)) if has_both_classes else None
    brier = float(brier_score_loss(y_test, scores))
    ece = _ece(y_test, scores)

    by_run: dict[str, list[tuple[CorpusRow, float]]] = {}
    for row, score in zip(test_rows, scores):
        by_run.setdefault(row.run_id, []).append((row, score))

    lead_times: list[float] = []
    useful_lead_times: list[float] = []
    run_level_tp = run_level_fn = 0
    n_negative_runs = 0
    n_false_alarm_runs = 0
    for run_id, row_scores in by_run.items():
        row_scores_sorted = sorted(row_scores, key=lambda pair: pair[0].checkpoint_index)
        run_label = row_scores_sorted[0][0].label
        fired_at = None
        for row, score in row_scores_sorted:
            if score >= threshold:
                fired_at = row
                break
        if run_label == 1:
            if fired_at is not None:
                run_level_tp += 1
                lt = fired_at.time_to_failure_seconds or 0.0
                lead_times.append(lt)
                if lt > _USEFUL_LEAD_TIME_EPSILON_SECONDS:
                    useful_lead_times.append(lt)
            else:
                run_level_fn += 1
        else:
            n_negative_runs += 1
            if fired_at is not None:
                n_false_alarm_runs += 1

    false_alarm_rate = (n_false_alarm_runs / n_negative_runs) if n_negative_runs else None

    def _mean(xs: list[float]) -> float | None:
        return (sum(xs) / len(xs)) if xs else None

    return {
        "n_checkpoints": len(test_rows),
        "n_runs": len(by_run),
        "threshold": threshold,
        "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
        "precision": precision, "recall": recall, "f1": f1,
        "auroc": auroc, "auprc": auprc, "brier_score": brier, "ece": ece,
        "false_alarm_rate": false_alarm_rate, "n_negative_runs": n_negative_runs,
        "run_level_true_positives": run_level_tp, "run_level_false_negatives": run_level_fn,
        "lead_time_seconds_mean": _mean(lead_times), "lead_time_seconds_n": len(lead_times),
        "useful_lead_time_seconds_mean": _mean(useful_lead_times), "useful_lead_time_seconds_n": len(useful_lead_times),
    }


@dataclass(frozen=True)
class FamilyEvaluation:
    mode: str
    failure_class: str
    status: str  # "EVALUATED" | "NOT_PREDICTABLE_SINGLE_CLASS"
    note: str
    n_train_rows: int
    n_validation_rows: int
    n_test_rows: int
    n_train_runs: int
    n_test_runs: int
    metrics: dict[str, Any] | None = None
    shuffled_control_metrics: dict[str, Any] | None = None


def evaluate_family(mode: str, failure_class: str, corpus: dict[str, list[CorpusRow]]) -> FamilyEvaluation:
    train_rows = [r for r in corpus["train"] if r.mode == mode]
    val_rows = [r for r in corpus["validation"] if r.mode == mode]
    test_rows = [r for r in corpus["test"] if r.mode == mode]
    n_train_runs = len({r.run_id for r in train_rows})
    n_test_runs = len({r.run_id for r in test_rows})

    if len(set(r.label for r in train_rows)) < 2 or len(set(r.label for r in test_rows)) < 2:
        return FamilyEvaluation(
            mode=mode, failure_class=failure_class, status="NOT_PREDICTABLE_SINGLE_CLASS",
            note=(
                "NOT PREDICTABLE FROM AVAILABLE OBSERVABLE PRECURSORS: this mode produces only one "
                "outcome label in the observed seed population (a deterministic-outcome workload -- "
                "see controlled_runtime.py's subprocess code for this mode). AUROC/AUPRC are "
                "mathematically undefined with a single class present, not merely hard to estimate; "
                "no score is fabricated here."
            ),
            n_train_rows=len(train_rows), n_validation_rows=len(val_rows), n_test_rows=len(test_rows),
            n_train_runs=n_train_runs, n_test_runs=n_test_runs,
        )

    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    x_train, y_train = _xy(train_rows)
    model.fit(x_train, y_train)
    threshold = calibrate_threshold(model, val_rows)
    real_metrics = compute_metrics(model, threshold, test_rows)

    # Negative control: same model class, same features, TRAIN+VALIDATION
    # labels permuted at the run level (fixed seed derived from the mode
    # name so it is reproducible without being tunable), evaluated against
    # the REAL test labels. Expected: ~chance AUROC.
    shuffle_seed = _stable_seed("phase4.8-label-shuffle", mode)
    shuffled_train = _shuffle_labels_by_run(train_rows, shuffle_seed)
    shuffled_val = _shuffle_labels_by_run(val_rows, shuffle_seed + 1)
    shuffled_metrics = None
    if len(set(r.label for r in shuffled_train)) >= 2:
        shuffled_model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
        x_shuf, y_shuf = _xy(shuffled_train)
        shuffled_model.fit(x_shuf, y_shuf)
        shuffled_threshold = calibrate_threshold(shuffled_model, shuffled_val)
        shuffled_metrics = compute_metrics(shuffled_model, shuffled_threshold, test_rows)

    return FamilyEvaluation(
        mode=mode, failure_class=failure_class, status="EVALUATED",
        note="real per-checkpoint, per-run rolling-checkpoint evaluation restricted to this mode's own population",
        n_train_rows=len(train_rows), n_validation_rows=len(val_rows), n_test_rows=len(test_rows),
        n_train_runs=n_train_runs, n_test_runs=n_test_runs,
        metrics=real_metrics, shuffled_control_metrics=shuffled_metrics,
    )


def evaluate_all_families(seeds: SplitSeeds, timeout_seconds: float = 0.15) -> dict[str, Any]:
    corpus = generate_corpus(seeds, timeout_seconds=timeout_seconds)
    results: dict[str, FamilyEvaluation] = {}
    for mode, failure_class in ALL_EVALUATED_MODES.items():
        results[mode] = evaluate_family(mode, failure_class, corpus)

    evaluated = [r for r in results.values() if r.status == "EVALUATED"]
    macro = {}
    for key in ("auroc", "auprc", "brier_score", "ece", "false_alarm_rate"):
        vals = [r.metrics[key] for r in evaluated if r.metrics is not None and r.metrics.get(key) is not None]
        macro[f"macro_{key}"] = (sum(vals) / len(vals)) if vals else None
        macro[f"macro_{key}_n_families"] = len(vals)

    return {
        "eval_version": EVAL_V2_VERSION,
        "families": {mode: _family_eval_as_dict(fe) for mode, fe in results.items()},
        "macro_averages_over_evaluable_families": macro,
        "n_families_evaluated": len(evaluated),
        "n_families_not_predictable": len(results) - len(evaluated),
    }


def _family_eval_as_dict(fe: FamilyEvaluation) -> dict[str, Any]:
    return {
        "mode": fe.mode, "failure_class": fe.failure_class, "status": fe.status, "note": fe.note,
        "n_train_rows": fe.n_train_rows, "n_validation_rows": fe.n_validation_rows, "n_test_rows": fe.n_test_rows,
        "n_train_runs": fe.n_train_runs, "n_test_runs": fe.n_test_runs,
        "metrics": fe.metrics, "shuffled_control_metrics": fe.shuffled_control_metrics,
    }
