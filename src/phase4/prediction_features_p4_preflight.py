"""Post-P5-remediation follow-up 3 -- carries Step 3's
``resource_preflight_available`` feature (real pre-flight ``bind()`` probe,
``controlled_runtime.py``, already emitted for every ``resource_unavailable``
workload in every P4 environment -- ``environments.py`` reuses the same
``ControlledRuntime.run()`` code path Step 2 instrumented, so no runtime
change was needed to make this feature available in P4's corpora) into
P4's environment-generalization pipeline, which never included it.

Used only by ``scripts/run_followup3_p4_preflight.py``. Not wired into any
other script -- this module does not change ``prediction.py``,
``prediction_features_env.py``, or any other frozen feature set.

Three feature sets, per the followups task:
  A. existing P4 baseline: ``(rss_ratio, anomaly_rate, elapsed_ratio,
     sample_count_ratio)`` -- ``prediction.extract_features``, unchanged.
  B. P3 preflight feature alone: ``(resource_preflight_available,)``.
  C. combined: A's 4 features plus the preflight feature (5 total).

Verified pre-outcome (no leakage): the probe event is emitted by
``ControlledRuntime.run()`` strictly BEFORE the child subprocess is even
spawned (see ``controlled_runtime.py`` around the `resource_preflight_probe`
telemetry emission, which precedes `subprocess.Popen(...)` in the same
function). ``rolling_checkpoints`` only ever includes events at-or-before
the checkpoint time and excludes the run's own `failure_detected` event by
construction, so this feature carries the same decision-time semantics as
every other ``prediction.py`` feature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .monitoring import MonitoringBaseline
from .prediction import PredictionFeatures, extract_features

FEATURE_NAMES_A = ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio")
FEATURE_NAMES_B = ("resource_preflight_available",)
FEATURE_NAMES_C = FEATURE_NAMES_A + FEATURE_NAMES_B


def _resource_preflight_value(events_prefix: Sequence[Mapping[str, Any]]) -> float:
    for e in events_prefix:
        if e.get("event_type") == "telemetry_observed" and (e.get("payload") or {}).get("telemetry_kind") == "resource_preflight_probe":
            return 1.0 if e["payload"].get("resource_available") else 0.0
    return 0.5  # no probe event in this prefix -- not this family, or probe not yet observed at this checkpoint


@dataclass(frozen=True)
class PreflightFeatures:
    base: PredictionFeatures
    resource_preflight_available: float

    def vector_a(self) -> tuple[float, ...]:
        return self.base.as_vector()

    def vector_b(self) -> tuple[float, ...]:
        return (self.resource_preflight_available,)

    def vector_c(self) -> tuple[float, ...]:
        return self.base.as_vector() + (self.resource_preflight_available,)


def extract_features_with_preflight(
    events_prefix: Sequence[Mapping[str, Any]],
    baseline: MonitoringBaseline,
    configured_timeout_seconds: float | None,
    run_start_iso: str,
    at_time_iso: str,
) -> PreflightFeatures:
    base = extract_features(events_prefix, baseline, configured_timeout_seconds, run_start_iso, at_time_iso)
    preflight = _resource_preflight_value(events_prefix)
    return PreflightFeatures(base=base, resource_preflight_available=preflight)
