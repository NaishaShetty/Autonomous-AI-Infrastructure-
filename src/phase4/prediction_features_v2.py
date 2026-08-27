"""Phase 4.8, Priority 3D -- ONE bounded, pre-registered feature-improvement
attempt, tried only after the leak-free per-family evaluation methodology
(``prediction_eval_v2.py``) was already validated and had already produced
its headline finding (none of the four bimodal families show real,
above-chance, replicated signal with the original 4-feature set -- see
``PHASE4_8_PREDICTION_REPORT.md``).

Structural reasoning for why THIS feature and not others (fixed here,
before running the improved model against TEST, per the project's
no-post-hoc-feature-selection rule):

  - `cpu` (timeout): the busy-loop workload's wall-clock elapsed time is
    the only real signal, and it is already captured as `elapsed_ratio`.
    A trend/derivative of elapsed time adds no new information (elapsed
    time increases at a constant rate by construction), so no new
    time-based feature is added for this family -- adding one anyway
    would be feature engineering for its own sake, which the project's
    integrity rules forbid ("no cherry-picked features").
  - `oom`: PHASE4_5_GAP_FIXES / PHASE4_5B report already established this
    family typically completes (allocates until it fails or finishes) in
    a tight, unpaced loop with 0-1 telemetry samples before the outcome
    is already decided. The one feature that COULD carry information if
    more than one sample exists is the RATE of RSS growth between
    consecutive samples (distinguishing a large `alloc_mb` request, which
    should grow RSS faster, from a small one) -- this is added as
    `rss_growth_rate`, honestly expected to help only on the rare runs
    with >= 2 telemetry samples before their outcome.
  - `resource_unavailable` / `flaky`: neither family's outcome has any
    real relationship to RSS or elapsed time at all (`resource_unavailable`
    is decided by a single bind() syscall at/near execution start;
    `flaky` is decided by an external invocation counter never reflected
    in telemetry) -- no candidate feature from this runtime's event
    stream is expected to help either family, and none is added
    specifically for them. They still receive `rss_growth_rate` (for
    interface uniformity -- all four families are scored by one shared
    5-feature model, as with the original 4-feature model), but the
    honest expectation, stated here BEFORE running the evaluation, is
    that it will not move their AUROC.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .monitoring import MonitoringBaseline
from .observability import PersistentEventStore
from .prediction import PredictionFeatures, extract_features, rolling_checkpoints
from .prediction_training import CorpusRow, _dt, scenario_for_seed

FEATURE_NAMES_V2 = ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio", "rss_growth_rate")


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class ExtendedFeatures:
    base: PredictionFeatures
    rss_growth_rate: float  # normalized RSS delta between the last two telemetry samples in the prefix

    def as_vector(self) -> tuple[float, ...]:
        return self.base.as_vector() + (self.rss_growth_rate,)


def extract_features_v2(
    events_prefix: Sequence[Mapping[str, Any]],
    baseline: MonitoringBaseline,
    configured_timeout_seconds: float | None,
    run_start_iso: str,
    at_time_iso: str,
) -> ExtendedFeatures:
    base = extract_features(events_prefix, baseline, configured_timeout_seconds, run_start_iso, at_time_iso)
    telemetry = [e for e in events_prefix if e.get("event_type") == "telemetry_observed"]
    rss_values = []
    for e in telemetry:
        rss = (e.get("payload") or {}).get("process_rss_bytes")
        if isinstance(rss, (int, float)):
            rss_values.append(float(rss))
    growth = 0.0
    if len(rss_values) >= 2 and baseline.max_process_rss_bytes:
        growth = _clip01((rss_values[-1] - rss_values[-2]) / float(baseline.max_process_rss_bytes))
    return ExtendedFeatures(base=base, rss_growth_rate=growth)


def generate_corpus_rows_v2(seeds: Sequence[int], split: str, timeout_seconds: float = 0.15) -> list[CorpusRow]:
    """Same generation protocol as ``prediction_training.generate_corpus_rows``
    (same scenarios, same rolling-checkpoint temporal-cut discipline), but
    features are extracted with ``extract_features_v2`` (5 features) instead
    of the original 4. Reuses ``CorpusRow`` unmodified -- only its
    ``features`` tuple is longer."""
    baseline = MonitoringBaseline()
    rows: list[CorpusRow] = []
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
            workload_id = f"{split}-v2-seed-{seed}"
            mode = str(params.get("mode") or workload_type)
            result = runtime.run(workload_type, params, workload_id=workload_id)
            failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
            label = 1 if failure_events else 0
            failure_class = str(failure_events[0]["payload"].get("failure_kind")) if failure_events else None
            failure_ts = _dt(str(failure_events[0]["timestamp"])) if failure_events else None
            for idx, (checkpoint_time, prefix) in enumerate(rolling_checkpoints(result.events, result.collection_start)):
                if failure_ts is not None and _dt(checkpoint_time) >= failure_ts:
                    continue
                features = extract_features_v2(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                ttf = (failure_ts - _dt(checkpoint_time)).total_seconds() if failure_ts is not None else None
                rows.append(CorpusRow(
                    seed=seed, split=split, run_id=result.run_id, workload_id=workload_id,
                    failure_class=failure_class, label=label, checkpoint_index=idx,
                    checkpoint_time=checkpoint_time, time_to_failure_seconds=ttf,
                    features=features.as_vector(), mode=mode,
                ))
        store.close()
    return rows


def generate_corpus_v2(seeds, timeout_seconds: float = 0.15) -> dict[str, list[CorpusRow]]:
    return {
        "train": generate_corpus_rows_v2(list(seeds.train), "train", timeout_seconds),
        "validation": generate_corpus_rows_v2(list(seeds.validation), "validation", timeout_seconds),
        "test": generate_corpus_rows_v2(list(seeds.test), "test", timeout_seconds),
    }
