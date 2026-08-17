"""Adapter: Alibaba GPU cluster trace, cleaned task-level sample
(data/processed/alibaba_gpu2020/task_table.main_sample.csv) ->
NormalizedRecord.

Failure = ``status == "Failed"``. This dataset has resource-plan telemetry
(plan_cpu/plan_mem/plan_gpu/gpu_type) but, per the repo audit, NO diagnosis
field and NO recovery/validation field anywhere in the schema -- represented
honestly as DiagnosisSource.NOT_ATTEMPTED / RecoveryStatus.NOT_OBSERVED,
not fabricated.

``start_time``/``end_time`` are trace-relative seconds-since-trace-start,
not wall-clock timestamps (see the dataset's own README under
data/provenance/alibaba_gpu2020/) -- anchored onto the same synthetic epoch
used elsewhere for non-wall-clock sources, offset by the relative seconds so
ordering within the trace is preserved exactly.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import timedelta
from pathlib import Path

from ._util import SYNTHETIC_TIME_EPOCH

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "alibaba_gpu2020" / "task_table.main_sample.csv"
SPLITS_PATH = Path(__file__).resolve().parents[3] / "data" / "audit" / "alibaba_gpu2020" / "splits_random_stratified.json"


def _load_split_lookup(path: Path = SPLITS_PATH) -> dict:
    """Reuses the existing, frozen Phase 3 real-data split manifest
    (job_name -> train/val/test) rather than inventing a competing split --
    per the brief's Task 7 instruction to reuse an existing split/registry
    if the repo already has one. Read-only; this manifest is never written
    to. Falls back to "unknown" for any job_name not covered by the
    manifest (e.g. jobs excluded during Phase 3's cleaning/sampling)."""
    if not path.exists():
        return {}
    with open(path) as f:
        splits = json.load(f)
    lookup = {}
    for split_name, job_names in splits.items():
        for job_name in job_names:
            lookup[job_name] = split_name
    return lookup

# Deterministic, documented sampling bound -- Alibaba has ~2600 failed tasks
# in the cleaned sample; ingesting all of them is unnecessary for a Phase
# 4.1 demonstration and would dominate experiment runtime. NOT a silent
# truncation: the count sampled vs. available is reported by
# load_normalized's caller (see benchmarks/phase4_1_active_experiments.py
# Experiment A, which logs both numbers).
DEFAULT_SAMPLE_SIZE = 300


def _content_hash(path: Path = DATA_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_failed_rows(path: Path = DATA_PATH) -> list[dict]:
    with open(path, newline="") as f:
        return [row for row in csv.DictReader(f) if row.get("status") == "Failed"]


def _float_or_none(v: str) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def to_normalized(row: dict, dataset_content_hash: str, split_lookup: dict | None = None) -> dict:
    row_idx = row["_source_row_index"]
    job_name = row["job_name"]
    task_name = row["task_name"]
    key = f"{job_name}|{task_name}|{row_idx}"
    split = (split_lookup or {}).get(job_name, "unknown")

    start_s = _float_or_none(row.get("start_time")) or 0.0
    end_s = _float_or_none(row.get("end_time"))
    obs_ts = SYNTHETIC_TIME_EPOCH + timedelta(seconds=start_s)
    detect_ts = SYNTHETIC_TIME_EPOCH + timedelta(seconds=end_s) if end_s is not None else obs_ts

    resource_metrics = {}
    for field, key_name in [("plan_cpu", "plan_cpu"), ("plan_mem", "plan_mem"), ("plan_gpu", "plan_gpu")]:
        val = _float_or_none(row.get(field))
        if val is not None:
            resource_metrics[key_name] = val

    return {
        "source_dataset": "alibaba_gpu2020",
        "episode_id": f"{job_name}__{task_name}__{row_idx}",
        "occurrence_key": row_idx,
        "observed_at": obs_ts,
        "workload_id": job_name,
        "workload_type": "alibaba_gpu_cluster_job",
        "environment": split,  # reused from the frozen Phase 3 real-data split manifest -- see _load_split_lookup
        "resource_metrics": resource_metrics,
        "system_state": {
            "gpu_type": row.get("gpu_type") or None,
            "inst_num": _float_or_none(row.get("inst_num")),
        },
        "failure_type": "task_terminated_failed",
        "affected_component": task_name,
        "detection_timestamp": detect_ts,
        "failure_status": "open",
        "diagnosis_source": "not_attempted",
        "recovery_status": "not_observed",
        "validation_result": "not_performed",
        "outcome_task_success": False,
        "outcome_final_status": "failure",
        "provenance_source_workload": job_name,
        "provenance_detector_version": "rule_based_status_field_v1",
        "provenance_dataset_content_hash": dataset_content_hash,
        "provenance_experiment_id": "real_data_expansion",
        "provenance_raw_record_ref": {"job_name": job_name, "task_name": task_name, "source_row_index": row_idx},
        "temporal": {"observation_ts": obs_ts, "detection_ts": detect_ts},
    }


def load_normalized(path: Path = DATA_PATH, sample_size: int = DEFAULT_SAMPLE_SIZE, seed: int = 42) -> tuple[list[dict], dict]:
    """Returns (normalized_records, sampling_report). sampling_report makes
    the sample-vs-available counts explicit for the experiment log."""
    import random

    content_hash = _content_hash(path)
    split_lookup = _load_split_lookup()
    all_failed = load_failed_rows(path)
    rng = random.Random(seed)
    chosen = sorted(all_failed, key=lambda r: r["_source_row_index"])
    if sample_size is not None and len(chosen) > sample_size:
        chosen = rng.sample(chosen, sample_size)
        chosen = sorted(chosen, key=lambda r: int(r["_source_row_index"]))
    report = {"available_failed_rows": len(all_failed), "sampled": len(chosen), "seed": seed}
    return [to_normalized(r, content_hash, split_lookup) for r in chosen], report
