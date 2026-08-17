"""Builds one trained system (workload model + calibrator + failure memory)
from the synthetic regime-drift stream. Used by both the live API
(``src/api/train.py``) and the benchmark harness
(``benchmarks/run_baselines.py``) so there is exactly one training procedure
-- not a live-demo version and a separately-maintained paper/benchmark
version (the divergence Phase 1 found between the source Failure Memory
model's live dashboard and its offline scripts).

Data split (fixed, deterministic given ``seed``):
  regime 0                -> train the workload model
  regime 1                -> fit the confidence calibrator
  regime 2                -> "logging" pass: run the trained
                              workload+calibrator, record every wrong
                              ANSWER as a failure, fit failure memory on them
  regimes 3, 4 (concatenated) -> held-out test stream, never used for fitting
                              anything; this is what benchmarks are scored on
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.data.synthetic import FEATURE_NAMES, StreamSample, generate_regime_stream
from src.failure_memory.memory import FailureMemory
from src.reliability.calibrator import ConfidenceCalibrator
from src.reliability.workload_model import WorkloadModel
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent

CALIBRATION_FEATURE_NAMES = FEATURE_NAMES + ["predicted_proba", "margin", "entropy"]

DEFAULT_REGIME_SIZES = (3000, 1500, 1500, 1500, 1500)


@dataclass
class TrainedSystem:
    workload_model: WorkloadModel
    calibrator: ConfidenceCalibrator
    failure_memory: FailureMemory
    feature_names: list[str]
    test_stream: list[StreamSample]
    n_logged_failures: int


def _to_array(sample_context: dict[str, float]) -> np.ndarray:
    return np.array([sample_context[f] for f in FEATURE_NAMES], dtype=float)


def build_system(
    regime_sizes: tuple[int, ...] = DEFAULT_REGIME_SIZES,
    n_clusters: int = 3,
    seed: int = 42,
) -> TrainedSystem:
    if len(regime_sizes) < 5:
        raise ValueError("regime_sizes must have at least 5 regimes (train/calib/log/test/test)")

    stream = generate_regime_stream(regime_sizes=regime_sizes, seed=seed)
    by_regime: dict[int, list[StreamSample]] = {}
    for s in stream:
        by_regime.setdefault(s.regime, []).append(s)

    train_samples = by_regime[0]
    calib_samples = by_regime[1]
    logging_samples = by_regime[2]
    test_stream = [s for r in sorted(by_regime) if r >= 3 for s in by_regime[r]]

    # 1. Workload model, trained once on regime 0 only.
    X_train = np.stack([_to_array(s.context) for s in train_samples])
    y_train = np.array([s.label for s in train_samples])
    workload_model = WorkloadModel(random_state=seed).fit(X_train, y_train)

    # 2. Calibrator, trained on regime 1 using the (already-frozen) workload
    #    model's own predictions as features.
    calib_feature_dicts = []
    calib_correct = []
    for s in calib_samples:
        pred = workload_model.predict(_to_array(s.context))
        calib_feature_dicts.append(
            {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        )
        calib_correct.append(int(pred.predicted_label == s.label))
    calibrator = ConfidenceCalibrator(CALIBRATION_FEATURE_NAMES, random_state=seed).fit(
        calib_feature_dicts, calib_correct
    )

    # 3. Failure memory, fit on failures observed during a logging pass over
    #    regime 2 (post-drift data the workload model has NOT been retrained
    #    on -- this is exactly the situation where historical failure
    #    information could plausibly add value beyond calibrated confidence).
    failure_events: list[ReliabilityEvent] = []
    for s in logging_samples:
        pred = workload_model.predict(_to_array(s.context))
        if pred.predicted_label == s.label:
            continue
        calib_features = {**s.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
        calib_result = calibrator.predict(calib_features)
        failure_events.append(
            ReliabilityEvent(
                workload_id="synthetic-regime-stream",
                source=EventSource.FAILURE_MEMORY,
                context=s.context,
                raw_confidence=calib_result.raw_confidence,
                confidence=calib_result.calibrated_confidence,
                decision=Decision.ANSWER,
                abstained=False,
                is_failure=True,
                outcome=Outcome.INCORRECT,
                metadata={"regime": s.regime, "predicted_label": pred.predicted_label, "true_label": s.label},
            )
        )

    failure_memory = FailureMemory(FEATURE_NAMES, n_clusters=n_clusters, random_state=seed)
    failure_memory._failure_events = failure_events  # logging pass, no repository needed here
    failure_memory.fit()

    return TrainedSystem(
        workload_model=workload_model,
        calibrator=calibrator,
        failure_memory=failure_memory,
        feature_names=FEATURE_NAMES,
        test_stream=test_stream,
        n_logged_failures=len(failure_events),
    )
