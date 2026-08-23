"""Phase 4.4 -- concrete ``PredictionPort`` implementation.

Closes the gap named in ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` section 5.B:
``PredictionPort`` was defined as an empty ``Protocol`` in
``src/phase4/architecture.py`` with no implementation anywhere in the
repository.

This is deliberately NOT a trained model. ``docs/RELIABILITY_MODEL_INTEGRATION_AUDIT.md``
already established the project's honest position: no versioned, persisted
model/calibrator artifact exists, and the project chose an honest
unconfigured fallback over a fabricated one. Consistent with that stance,
``TelemetryRiskPredictor`` is a fixed, documented, engineered scoring rule
over the same controlled-runtime telemetry the rest of Phase 4 already
observes -- not a machine-learned model, so there is nothing to overclaim
calibration for. Its weights are fixed here, before any evaluation is run
against it, and must not be tuned against evaluation outcomes (same
discipline as ``MonitoringBaseline`` in ``src/phase4/monitoring.py``).

The prediction is evaluated for real in
``scripts/run_phase4_5_pipeline_demo.py`` / ``tests/unit/test_phase44_prediction.py``:
precision/recall of "score crossed the decision threshold before the run's
own failure_detected event" against ground-truth run outcomes, plus lead
time in seconds when a true positive fires ahead of the failure. Numbers are
reported as measured, not asserted in advance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .architecture import Prediction
from .monitoring import MonitoringBaseline
from src.data_foundation.foundation import Provenance, TimestampQuality

PREDICTION_VERSION = "phase4.4-prediction-engineered-v1"
DECISION_THRESHOLD = 0.5

# Fixed feature weights. Sum to 1.0 by construction; not tuned against any
# evaluation outcome. Documented rationale per weight:
#  - rss: the only anomaly signal Phase 4.2 already tracks; the strongest
#    available leading indicator.
#  - anomaly_rate: repeated anomalies in a short run are a stronger signal
#    than one anomaly in a long one (matches the sustained-anomaly
#    escalation added to MonitoringEngine.process in the same change).
#  - elapsed_ratio: a workload approaching its configured timeout without
#    completing is the single most common failure precursor this runtime
#    can observe (PROCESS_TIMEOUT is one of only three supported failure
#    classes).
WEIGHT_RSS = 0.45
WEIGHT_ANOMALY_RATE = 0.25
WEIGHT_ELAPSED_RATIO = 0.30


@dataclass(frozen=True)
class PredictionFeatures:
    rss_ratio: float
    anomaly_rate: float
    elapsed_ratio: float


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def extract_features(
    events_prefix: Sequence[Mapping[str, Any]],
    baseline: MonitoringBaseline,
    configured_timeout_seconds: float | None,
    run_start_iso: str,
    at_time_iso: str,
) -> PredictionFeatures:
    """Compute features from a prefix of a run's events (only events at or
    before ``at_time_iso`` -- callers are responsible for the temporal cut,
    consistent with every other Phase 4 decision-boundary contract in this
    repository)."""
    from datetime import datetime

    def _dt(x: str):
        return datetime.fromisoformat(str(x).replace("Z", "+00:00"))

    telemetry = [e for e in events_prefix if e.get("event_type") == "telemetry_observed"]
    max_rss = 0.0
    for e in telemetry:
        rss = (e.get("payload") or {}).get("process_rss_bytes")
        if isinstance(rss, (int, float)) and rss > max_rss:
            max_rss = float(rss)
    rss_ratio = _clip01(max_rss / float(baseline.max_process_rss_bytes)) if baseline.max_process_rss_bytes else 0.0

    sample_count = max(1, len(telemetry))
    over_threshold = sum(
        1 for e in telemetry
        if isinstance((e.get("payload") or {}).get("process_rss_bytes"), (int, float))
        and (e["payload"]["process_rss_bytes"]) > baseline.max_process_rss_bytes
    )
    anomaly_rate = _clip01(over_threshold / sample_count)

    elapsed_ratio = 0.0
    if configured_timeout_seconds:
        elapsed = (_dt(at_time_iso) - _dt(run_start_iso)).total_seconds()
        elapsed_ratio = _clip01(elapsed / configured_timeout_seconds)

    return PredictionFeatures(rss_ratio=rss_ratio, anomaly_rate=anomaly_rate, elapsed_ratio=elapsed_ratio)


class TelemetryRiskPredictor:
    """Concrete ``PredictionPort`` implementation (see ``architecture.PredictionPort``)."""

    version = PREDICTION_VERSION

    def __init__(self, baseline: MonitoringBaseline | None = None):
        self.baseline = baseline or MonitoringBaseline()

    def predict_from_events(
        self,
        job_id: str,
        events_prefix: Sequence[Mapping[str, Any]],
        configured_timeout_seconds: float | None,
        run_start_iso: str,
        at_time_iso: str,
    ) -> Prediction:
        features = extract_features(events_prefix, self.baseline, configured_timeout_seconds, run_start_iso, at_time_iso)
        score = _clip01(
            WEIGHT_RSS * features.rss_ratio
            + WEIGHT_ANOMALY_RATE * features.anomaly_rate
            + WEIGHT_ELAPSED_RATIO * features.elapsed_ratio
        )
        return Prediction(
            prediction_id=f"prediction:{job_id}:{at_time_iso}",
            job_id=job_id,
            snapshot_id=f"snapshot:{job_id}:{at_time_iso}",
            decision_time=at_time_iso,
            score=score,
            provenance=Provenance(
                source="phase4-telemetry-risk-predictor",
                source_version=self.version,
                extraction_method="engineered_feature_rule",
                transformation="weighted_sum_fixed_weights",
                transformation_version=self.version,
                timestamp_source="controlled_runtime_event_timestamp",
                timestamp_quality=TimestampQuality.EXACT,
            ),
        )
