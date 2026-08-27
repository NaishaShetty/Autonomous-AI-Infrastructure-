"""Post-P5 remediation, Step 4 (P4-W2) -- an environment-aware feature
representation, used only by ``run_p4_step4_environment_generalization.py``.

Root-cause hypothesis for the P4 OOM generalization collapse (dev AUROC
~0.678 -> held-out ~0.506, per the pre-remediation register): the original
``rss_ratio`` feature (``prediction.py::extract_features``) normalizes a
run's peak observed RSS against ``MonitoringBaseline.max_process_rss_bytes``
-- a FIXED 512MB constant, identical in every environment, with no
relationship whatsoever to the 'oom' mode's actual, real, per-run
``limit_mb`` resource budget (8MB in the memory-constrained held-out
environment vs 32MB at baseline -- a 4x difference). The same absolute RSS
reading therefore represents a wildly different "fraction of budget
consumed" depending on which environment a run happened in, and the
original model had no way to know that, because it was never told the
run's actual configured limit.

``limit_mb`` is a genuine configuration input, known before the run even
starts -- not an outcome, not leaked information -- but was never emitted
into any canonical event before the Step 4 controlled_runtime.py change
(``workload_received``'s payload now carries ``workload_parameters``).
This module reads it back out and computes an environment-normalized RSS
feature: peak RSS as a fraction of THIS RUN'S OWN configured budget,
falling back to the original fixed-baseline normalization for families
where no such budget exists (or is not yet known at feature-extraction
time -- families outside the `oom` mode never have a `limit_mb` in their
`workload_received` payload, so they fall back honestly, not by fabricating
a value).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .monitoring import MonitoringBaseline
from .prediction import PredictionFeatures, _clip01, extract_features

FEATURE_NAMES_ENV = ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio", "rss_ratio_env_normalized")


@dataclass(frozen=True)
class EnvAwareFeatures:
    base: PredictionFeatures
    rss_ratio_env_normalized: float

    def as_vector(self) -> tuple[float, ...]:
        return self.base.as_vector() + (self.rss_ratio_env_normalized,)


def _configured_limit_mb(events_prefix: Sequence[Mapping[str, Any]]) -> float | None:
    for e in events_prefix:
        if e.get("event_type") == "workload_received":
            params = (e.get("payload") or {}).get("workload_parameters") or {}
            if params.get("mode") == "oom" and "limit_mb" in params:
                try:
                    return float(params["limit_mb"])
                except (TypeError, ValueError):
                    return None
    return None


def extract_features_env_aware(
    events_prefix: Sequence[Mapping[str, Any]],
    baseline: MonitoringBaseline,
    configured_timeout_seconds: float | None,
    run_start_iso: str,
    at_time_iso: str,
) -> EnvAwareFeatures:
    base = extract_features(events_prefix, baseline, configured_timeout_seconds, run_start_iso, at_time_iso)

    limit_mb = _configured_limit_mb(events_prefix)
    telemetry = [e for e in events_prefix if e.get("event_type") == "telemetry_observed"]
    max_rss = 0.0
    for e in telemetry:
        rss = (e.get("payload") or {}).get("process_rss_bytes")
        if isinstance(rss, (int, float)) and rss > max_rss:
            max_rss = float(rss)

    if limit_mb is not None and limit_mb > 0:
        env_normalized = _clip01(max_rss / (limit_mb * 1024 * 1024))
    else:
        env_normalized = base.rss_ratio  # honest fallback: no per-run budget known, reuse the fixed-baseline value

    return EnvAwareFeatures(base=base, rss_ratio_env_normalized=env_normalized)
