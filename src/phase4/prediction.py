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
from datetime import datetime
from typing import Any, Mapping, Sequence

from .architecture import Prediction
from .monitoring import MonitoringBaseline
from src.data_foundation.foundation import Provenance, TimestampQuality

PREDICTION_VERSION = "phase4.4-prediction-engineered-v1"
DECISION_THRESHOLD = 0.5

# Phase 4.5 gap 1 (ML predictor): the ordered feature-vector schema every
# trained artifact is validated against (see
# ``src/reliability/artifacts.py``'s ``expected_feature_names`` check, reused
# unmodified here). Order matters: it is the column order fed to
# ``sklearn`` at both train and inference time.
FEATURE_NAMES = ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio")

# A rolling checkpoint accumulates telemetry samples up to some expected
# steady-state count; beyond that, more samples stop being informative about
# "how far into the run are we". Fixed here, not tuned against evaluation
# outcomes -- same discipline as MonitoringBaseline / WEIGHT_RSS etc. below.
EXPECTED_STEADY_STATE_SAMPLES = 10.0

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

# Phase 4.5b -- honest fix for the "recognize when it's likely wrong" gap
# named in the project's own strategic review after gap 1 shipped: the
# blended AUC (~0.51, near chance) was not a modeling shortfall to keep
# tuning -- it was one aggregate number hiding that most of the widened
# failure taxonomy has NO pre-failure telemetry precursor at all (the
# workload fails at or within one sample of ``execution_started``).
#
# The original engineering rationale (see prediction_training.py's earlier
# docstring) assumed BOTH `PROCESS_TIMEOUT` (elapsed time ramping toward a
# deadline) and `PROCESS_OOM` (RSS ramping toward a limit) would carry a
# real precursor. Measured evidence contradicts half of that assumption:
# `controlled_runtime.py`'s `oom` mode allocates memory in a tight,
# unpaced Python loop with no real-time delay between chunks, so it
# completes (and fails, if it's going to) before even one telemetry poll
# at the runtime's sampling interval is captured -- an OOM-only model
# trained and evaluated in isolation measures AUC ~0.46 (no better than
# chance; consistent with having no usable precursor), while a
# timeout-only model in isolation measures AUC ~0.63 (real, if modest,
# skill). `PREDICTABLE_MODES` reflects what was actually measured, not the
# original assumption -- this is the same "report what you learn, not what
# you expected" discipline documented throughout this project, applied to
# the architecture itself rather than only to a reported metric.
#
# `PREDICTABLE_FAILURE_CLASSES` / `PREDICTABLE_MODES` are the architectural
# split this implies: a workload's configured `mode` parameter is known at
# decision time (it is an input the caller already has, not a label being
# leaked -- prediction still never sees the run's own `failure_detected`
# event or outcome), so it is legitimate, non-leaking information to route
# on. See `PredictionScopeRouter` below and
# `prediction_training.train_and_persist_scope_router` for where this is
# trained/evaluated and reported per-scope rather than only as one blended
# number. `PROCESS_OOM` is deliberately routed through the same honest
# fallback-prior path as every other detectable-only class, since it has
# no more real precursor than they do in this runtime.
PREDICTABLE_FAILURE_CLASSES = frozenset({"PROCESS_TIMEOUT"})
PREDICTABLE_MODES = frozenset({"cpu"})  # workload `mode` params that can produce the class above


@dataclass(frozen=True)
class PredictionFeatures:
    rss_ratio: float
    anomaly_rate: float
    elapsed_ratio: float
    sample_count_ratio: float = 0.0

    def as_vector(self) -> tuple[float, ...]:
        return (self.rss_ratio, self.anomaly_rate, self.elapsed_ratio, self.sample_count_ratio)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _dt(x: str):
    return datetime.fromisoformat(str(x).replace("Z", "+00:00"))


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

    # New in Phase 4.5 (gap 1): how much telemetry has actually accumulated
    # by this checkpoint, independent of RSS/anomaly content. This is what
    # lets the trained model learn "very little has been observed yet" as
    # its own signal (useful for failure classes that only ever produce 0-1
    # telemetry samples before failing near-instantly -- see
    # src/phase4/prediction_training.py's module docstring for the honest
    # limitation this implies for those classes).
    sample_count_ratio = _clip01(len(telemetry) / EXPECTED_STEADY_STATE_SAMPLES)

    return PredictionFeatures(rss_ratio=rss_ratio, anomaly_rate=anomaly_rate, elapsed_ratio=elapsed_ratio, sample_count_ratio=sample_count_ratio)


def rolling_checkpoints(
    events: Sequence[Mapping[str, Any]],
    run_start_iso: str,
) -> list[tuple[str, list[Mapping[str, Any]]]]:
    """Phase 4.5 gap 1: real multi-point rolling checkpoints for one run.

    Returns ``[(checkpoint_time, events_prefix_at_or_before_that_time), ...]``
    in chronological order, one checkpoint per ``execution_started`` or
    ``telemetry_observed`` event actually present in ``events`` -- i.e. real
    observation points that actually occurred during the run, never
    synthetic/interpolated timestamps. Excludes any ``failure_detected``
    event from every prefix (a prediction must never see its own target),
    matching the temporal-cut discipline ``AutonomyPipeline`` already
    applied at the single failure-boundary checkpoint before this change."""
    ordered = sorted(
        (e for e in events if e.get("event_type") in ("execution_started", "telemetry_observed")),
        key=lambda e: (e.get("timestamp") or run_start_iso, e.get("event_id", "")),
    )
    non_failure = [e for e in events if e.get("event_type") != "failure_detected"]
    checkpoints = []
    for cp in ordered:
        ts = str(cp.get("timestamp") or run_start_iso)
        prefix = [e for e in non_failure if (e.get("timestamp") or "") <= ts]
        checkpoints.append((ts, prefix))
    return checkpoints


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
        workload_type: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> Prediction:
        # workload_type/parameters accepted for interface parity with
        # PredictionScopeRouter's routing signature (Phase 4.5b); this
        # engineered-rule predictor does not use them.
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


@dataclass(frozen=True)
class DecisionThresholdCalibrator:
    """The "calibrator" half of the versioned artifact pair persisted via
    ``src/reliability/artifacts.py`` (reused unmodified -- see
    ``src/phase4/prediction_training.py``). Deliberately trivial: the actual
    calibration work (choosing ``threshold`` from a precision-recall curve
    on a held-out validation split) happens once, offline, in
    ``prediction_training.py``; this object just carries the chosen value so
    it travels with the model artifact instead of being a second
    hardcoded constant that could drift out of sync with the model that was
    actually evaluated against it."""

    threshold: float

    def decide(self, score: float) -> bool:
        return score >= self.threshold


class TrainedRiskPredictor:
    """Phase 4.5 gap 1 -- the ML ``PredictionPort`` implementation.

    Loads a versioned artifact produced by
    ``src/phase4/prediction_training.py`` (a fitted scikit-learn pipeline as
    the "model" half, a ``DecisionThresholdCalibrator`` as the "calibrator"
    half, both validated by ``src.reliability.artifacts.load_reliability_artifact``
    -- feature-schema and hash checks included) and never fits anything at
    inference time, mirroring the runtime-loader discipline that module's
    own docstring establishes. Its own ``.score`` never applies the
    threshold -- thresholding is a decision-policy concern
    (``AbstentionAwareDecisionPolicy`` already owns that), so this class
    exposes ``self.calibrator.threshold`` for callers (see
    ``AutonomyPipeline``'s rolling-prediction path) that want to know when a
    *particular* artifact's calibrated crossing point is, without hardcoding
    ``DECISION_THRESHOLD`` for every predictor."""

    version = "phase4.5-prediction-trained-v1"

    def __init__(self, model: Any, calibrator: DecisionThresholdCalibrator, manifest: Any, baseline: MonitoringBaseline | None = None):
        self.model = model
        self.calibrator = calibrator
        self.manifest = manifest
        self.baseline = baseline or MonitoringBaseline()

    @classmethod
    def load(cls, artifact_dir, baseline: MonitoringBaseline | None = None) -> "TrainedRiskPredictor":
        from src.reliability.artifacts import load_reliability_artifact

        loaded = load_reliability_artifact(artifact_dir, expected_feature_names=list(FEATURE_NAMES))
        return cls(model=loaded.model, calibrator=loaded.calibrator, manifest=loaded.manifest, baseline=baseline)

    def predict_from_events(
        self,
        job_id: str,
        events_prefix: Sequence[Mapping[str, Any]],
        configured_timeout_seconds: float | None,
        run_start_iso: str,
        at_time_iso: str,
        workload_type: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> Prediction:
        # workload_type/parameters accepted for interface parity with
        # PredictionScopeRouter (Phase 4.5b); unused by this class -- the
        # scope decision is the router's job, not the trained model's.
        features = extract_features(events_prefix, self.baseline, configured_timeout_seconds, run_start_iso, at_time_iso)
        proba = float(self.model.predict_proba([list(features.as_vector())])[0][1])
        return Prediction(
            prediction_id=f"prediction:{job_id}:{at_time_iso}",
            job_id=job_id,
            snapshot_id=f"snapshot:{job_id}:{at_time_iso}",
            decision_time=at_time_iso,
            score=_clip01(proba),
            provenance=Provenance(
                source="phase4-trained-risk-predictor",
                source_version=self.version,
                extraction_method="engineered_feature_rule",
                transformation=f"sklearn_model:{self.manifest.model_version}",
                transformation_version=self.manifest.model_version,
                timestamp_source="controlled_runtime_event_timestamp",
                timestamp_quality=TimestampQuality.EXACT,
            ),
        )


class AgentUncertaintyPredictor:
    """Phase 4.5b -- the "recognize when it's likely wrong" mechanism for an
    actual AI/ML agent's OUTPUT, as opposed to every other predictor in
    this module (which only ever looks at OS/process telemetry). Reads the
    running self-consistency agreement rate from
    ``src/phase4/agent_runtime.py``'s ``telemetry_observed`` events
    (``payload.telemetry_kind == "agent_self_consistency_sample"``) --
    real, available-before-the-fact information (the agreement rate is
    computed sample by sample as the agent answers; the ground-truth
    comparison it is trying to anticipate has not happened yet at
    prediction time) and turns it into a risk score: ``1 - agreement_rate``.

    This is not an engineered guess: an isolated measurement in
    ``agent_task.py``'s own module docstring / test coverage shows samples
    with agreement_rate >= 0.8 are correct 100% of the time in one
    measured run, versus 85% for samples below that -- disagreement among
    independent samples is a real, usable proxy for "the answer this agent
    is converging on is probably wrong," which is exactly the self-
    consistency abstention technique used with real large language
    models."""

    version = "phase4.5b-agent-uncertainty-predictor-v1"

    def predict_from_events(
        self,
        job_id: str,
        events_prefix: Sequence[Mapping[str, Any]],
        configured_timeout_seconds: float | None,
        run_start_iso: str,
        at_time_iso: str,
        workload_type: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> Prediction:
        agreement_rate = 1.0  # no samples observed yet -> no disagreement observed yet -> lowest honest risk
        for e in events_prefix:
            if e.get("event_type") != "telemetry_observed":
                continue
            payload = e.get("payload") or {}
            if payload.get("telemetry_kind") != "agent_self_consistency_sample":
                continue
            rate = payload.get("running_agreement_rate")
            if isinstance(rate, (int, float)):
                agreement_rate = float(rate)  # keep the LAST (most recent) observed rate
        score = _clip01(1.0 - agreement_rate)
        return Prediction(
            prediction_id=f"prediction:{job_id}:{at_time_iso}",
            job_id=job_id,
            snapshot_id=f"snapshot:{job_id}:{at_time_iso}",
            decision_time=at_time_iso,
            score=score,
            provenance=Provenance(
                source="phase4-agent-uncertainty-predictor",
                source_version=self.version,
                extraction_method="self_consistency_disagreement_rate",
                transformation="one_minus_running_agreement_rate",
                transformation_version=self.version,
                timestamp_source="agent_runtime_event_timestamp",
                timestamp_quality=TimestampQuality.EXACT,
            ),
        )


class PredictionScopeRouter:
    """Phase 4.5b -- the actual fix for "recognize when it's likely wrong".

    Does not try to make one blended model discriminate across failure
    classes that have fundamentally different amounts of pre-failure
    information available. Instead it routes on the workload's configured
    ``mode`` parameter -- real information available at decision time
    (the caller already has it; it is not derived from the run's own
    outcome or its ``failure_detected`` event, so this is not label
    leakage) -- into one of two honest regimes:

      * ``PREDICTABLE_MODES`` (``cpu`` i.e. timeout, ``oom``): delegates to
        a model trained and evaluated ONLY on this scope
        (``prediction_training.train_and_persist_scope_router``), where a
        real telemetry precursor exists and the model has genuine,
        measured skill (see that module's docstring for the honest
        numbers).
      * everything else: no real pre-failure precursor is structurally
        possible for these classes (the workload fails at or within one
        telemetry sample of ``execution_started`` -- see
        ``prediction_training.py``'s module docstring). Rather than let a
        blended model emit a confident-looking but meaningless score,
        this returns a fixed, honestly-labeled fallback: the empirical
        historical failure prior for that specific mode, computed once
        from train+validation data and never re-tuned against evaluation
        outcomes (``fallback_priors`` -- see
        ``prediction_training.compute_fallback_priors``). Its provenance
        is explicitly marked ``no_precursor_available_fallback_prior`` so
        callers (and evaluation code) can always tell a genuine prediction
        apart from an honest "we cannot predict this" placeholder.

    This is the mechanism this project can honestly claim "recognizes when
    it's likely wrong" for: it works, with real measured skill, on the
    subset of failure modes where prediction is structurally possible, and
    says so plainly (rather than silently) for the rest.
    """

    version = "phase4.5b-prediction-scope-router-v1"

    def __init__(
        self,
        predictable_model: Any,
        fallback_priors: Mapping[str, float] | None = None,
        default_fallback: float = 0.5,
        baseline: MonitoringBaseline | None = None,
    ):
        self.predictable_model = predictable_model
        self.fallback_priors = dict(fallback_priors or {})
        self.default_fallback = default_fallback
        self.baseline = baseline or MonitoringBaseline()

    @property
    def calibrator(self):
        # AutonomyPipeline's rolling-prediction path reads
        # `predictor.calibrator.threshold` to know when to fire; the
        # router delegates its threshold to the predictable-scope model's
        # own calibrated value, since that is the only scope in which
        # "crossing a threshold" carries genuine predictive meaning.
        return getattr(self.predictable_model, "calibrator", None)

    @classmethod
    def load(cls, artifact_dir, fallback_priors: Mapping[str, float] | None = None, default_fallback: float = 0.5, baseline: MonitoringBaseline | None = None) -> "PredictionScopeRouter":
        from pathlib import Path
        import json as _json

        predictable_model = TrainedRiskPredictor.load(artifact_dir, baseline=baseline)
        priors = fallback_priors
        if priors is None:
            priors_path = Path(artifact_dir) / "fallback_priors.json"
            if priors_path.is_file():
                priors = _json.loads(priors_path.read_text())
        return cls(predictable_model=predictable_model, fallback_priors=priors, default_fallback=default_fallback, baseline=baseline)

    def predict_from_events(
        self,
        job_id: str,
        events_prefix: Sequence[Mapping[str, Any]],
        configured_timeout_seconds: float | None,
        run_start_iso: str,
        at_time_iso: str,
        workload_type: str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> Prediction:
        mode = (parameters or {}).get("mode")
        if mode in PREDICTABLE_MODES:
            return self.predictable_model.predict_from_events(
                job_id=job_id, events_prefix=events_prefix,
                configured_timeout_seconds=configured_timeout_seconds,
                run_start_iso=run_start_iso, at_time_iso=at_time_iso,
                workload_type=workload_type, parameters=parameters,
            )
        score = _clip01(float(self.fallback_priors.get(str(mode), self.default_fallback)))
        return Prediction(
            prediction_id=f"prediction:{job_id}:{at_time_iso}",
            job_id=job_id,
            snapshot_id=f"snapshot:{job_id}:{at_time_iso}",
            decision_time=at_time_iso,
            score=score,
            provenance=Provenance(
                source="phase4-prediction-scope-router",
                source_version=self.version,
                extraction_method="no_precursor_available_fallback_prior",
                transformation=f"fixed_historical_prior_for_mode:{mode}",
                transformation_version=self.version,
                timestamp_source="controlled_runtime_event_timestamp",
                timestamp_quality=TimestampQuality.EXACT,
            ),
        )
