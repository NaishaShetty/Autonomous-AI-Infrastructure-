"""Post-P5 remediation, Step 3 -- feature/corpus extensions used ONLY by
``run_p3_step3_predictability.py``, built directly from the Step 2
observability audit's per-family recommendations
(``experiments/results/post_p5_remediation/*/audits/P3_PREDICTIVE_OBSERVABILITY_AUDIT.md``).

Two additions, both pre-registered in ``protocol/P3_STEP3_PROTOCOL.md``
before any evaluation ran:

1. ``resource_preflight_available`` -- a 6th feature, built from the real
   pre-flight `bind()` probe added to ``controlled_runtime.py`` in Step 2
   (``telemetry_kind == "resource_preflight_probe"``). Only meaningful for
   ``resource_unavailable``-mode rows; every other family gets the neutral
   ``0.5`` ("no probe event exists for this family") so the same 6-feature
   model interface is usable everywhere, matching the project's existing
   "one shared model per family" convention (see ``prediction_features_v2.py``).
2. ``n_telemetry_samples`` -- NOT a model feature (adding it as one would
   be redundant with the existing ``sample_count_ratio`` and would not
   change what's predictable). It is a decision-time-available property
   used only to split ``oom`` test rows into "sufficient observability"
   (>=2 samples) vs "insufficient observability" (0-1 samples) subsets for
   separate reporting, per the audit's finding that pooling them dilutes
   any real signal in the observable subset. This is a split on an
   available covariate, not on the outcome label.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .monitoring import MonitoringBaseline
from .observability import PersistentEventStore
from .prediction import rolling_checkpoints
from .prediction_features_v2 import extract_features_v2
from .prediction_training import CorpusRow, _dt, scenario_for_seed

FEATURE_NAMES_V3 = ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio", "rss_growth_rate", "resource_preflight_available")


@dataclass(frozen=True)
class CorpusRowV3(CorpusRow):
    n_telemetry_samples: int = 0


def _resource_preflight_value(events_prefix: Sequence[Mapping[str, Any]]) -> float:
    for e in events_prefix:
        if e.get("event_type") == "telemetry_observed" and (e.get("payload") or {}).get("telemetry_kind") == "resource_preflight_probe":
            return 1.0 if e["payload"].get("resource_available") else 0.0
    return 0.5  # no probe event in this prefix -- not this family, or probe not yet observed at this checkpoint


def generate_corpus_rows_v3(seeds: Sequence[int], split: str, timeout_seconds: float = 0.15) -> list[CorpusRowV3]:
    baseline = MonitoringBaseline()
    rows: list[CorpusRowV3] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        config = RuntimeConfig(timeout_seconds=timeout_seconds, telemetry_interval_seconds=0.01)
        runtime = ControlledRuntime(store, config)
        for seed in seeds:
            workload_type, params = scenario_for_seed(seed)
            params = dict(params)
            occupy = params.pop("_occupy", None)
            if occupy:
                runtime.occupy_external_resource(int(params["port"]))
            workload_id = f"{split}-v3-seed-{seed}"
            mode = str(params.get("mode") or workload_type)
            result = runtime.run(workload_type, params, workload_id=workload_id)
            failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
            label = 1 if failure_events else 0
            failure_class = str(failure_events[0]["payload"].get("failure_kind")) if failure_events else None
            failure_ts = _dt(str(failure_events[0]["timestamp"])) if failure_events else None
            for idx, (checkpoint_time, prefix) in enumerate(rolling_checkpoints(result.events, result.collection_start)):
                if failure_ts is not None and _dt(checkpoint_time) >= failure_ts:
                    continue
                v2 = extract_features_v2(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                preflight = _resource_preflight_value(prefix)
                n_samples = sum(1 for e in prefix if e.get("event_type") == "telemetry_observed" and (e.get("payload") or {}).get("telemetry_kind") != "resource_preflight_probe")
                ttf = (failure_ts - _dt(checkpoint_time)).total_seconds() if failure_ts is not None else None
                rows.append(CorpusRowV3(
                    seed=seed, split=split, run_id=result.run_id, workload_id=workload_id,
                    failure_class=failure_class, label=label, checkpoint_index=idx,
                    checkpoint_time=checkpoint_time, time_to_failure_seconds=ttf,
                    features=v2.as_vector() + (preflight,), mode=mode,
                    n_telemetry_samples=n_samples,
                ))
        store.close()
    return rows


def generate_corpus_v3(seeds, timeout_seconds: float = 0.15) -> dict[str, list[CorpusRowV3]]:
    return {
        "train": generate_corpus_rows_v3(list(seeds.train), "train", timeout_seconds),
        "validation": generate_corpus_rows_v3(list(seeds.validation), "validation", timeout_seconds),
        "test": generate_corpus_rows_v3(list(seeds.test), "test", timeout_seconds),
    }
