"""Adapter: AIOps 2020 challenge injected-fault windows
(data/audit/aiops_kpi/positive_windows.json) -> NormalizedRecord.

Each entry is one injected/labeled fault window (entity, fault type, onset,
pre/during-failure window bounds) produced during the real-data Phase 3
preparation (docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md) -- read
here read-only, not regenerated or modified.

KNOWN LIMITATION (documented, not silently dropped): full time-series
telemetry (the per-minute business/platform CSVs under
data/processed/aiops_kpi/) is NOT joined into ``telemetry`` here -- only
window metadata (duration, extractability) is captured as
``resource_metrics``/``anomaly_signals``. A full metric-window join is a
reasonable Phase 4.1.x follow-on, not attempted in this ingestion pass; see
docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md limitations section.

Per the repo audit, AIOps has no frozen train/test split manifest and no
recovery/validation field of any kind -- both represented explicitly
(``environment="unsplit"``, RecoveryStatus.NOT_OBSERVED).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "audit" / "aiops_kpi" / "positive_windows.json"


def _content_hash(path: Path = DATA_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_records(path: Path = DATA_PATH) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def _parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def to_normalized(record: dict, dataset_content_hash: str) -> dict:
    fault_index = record["fault_index"]
    entity = record.get("entity", "unknown_entity")
    onset = _parse_ts(record.get("onset"))
    pre_start = _parse_ts(record.get("pre_failure_window_start"))
    during_end = _parse_ts(record.get("during_failure_window_end"))

    duration_minutes = None
    if pre_start is not None and during_end is not None:
        duration_minutes = (during_end - pre_start).total_seconds() / 60.0

    return {
        "source_dataset": "aiops_kpi_2020",
        "episode_id": f"aiops_fault_{fault_index}",
        "occurrence_key": fault_index,
        "observed_at": onset or pre_start,
        "workload_id": entity,
        "workload_type": f"aiops_{record.get('object', 'component')}",
        "environment": "unsplit",  # no frozen train/test manifest exists for AIOps -- see module docstring
        "resource_metrics": {"window_duration_minutes": duration_minutes} if duration_minutes is not None else {},
        "anomaly_signals": {"day_is_extractable": 1.0 if record.get("day_is_extractable") else 0.0},
        "system_state": {"onset_rule": record.get("onset_rule"), "extractable_day": record.get("extractable_day")},
        "failure_type": record.get("fault_desrcibtion", "unspecified_fault"),
        "affected_component": entity,
        "detection_timestamp": onset,
        "failure_status": "open",
        "diagnosis_suspected_cause": record.get("fault_desrcibtion"),
        "diagnosis_confidence": None,
        "diagnosis_evidence": [f"object={record.get('object')}", f"onset_rule={record.get('onset_rule')}"],
        "diagnosis_method": "aiops_injected_fault_ground_truth_label",
        "diagnosis_method_version": "aiops_2020_challenge",
        "diagnosis_source": "human_dataset_annotation",
        "recovery_status": "not_observed",
        "validation_result": "not_performed",
        "outcome_final_status": "failure",
        "provenance_source_workload": entity,
        "provenance_dataset_content_hash": dataset_content_hash,
        "provenance_experiment_id": "real_data_expansion",
        "provenance_raw_record_ref": {"fault_index": fault_index, "entity": entity, "object": record.get("object")},
        "temporal": {
            "observation_ts": pre_start,
            "detection_ts": onset,
        },
    }


def load_normalized(path: Path = DATA_PATH) -> list[dict]:
    content_hash = _content_hash(path)
    return [to_normalized(r, content_hash) for r in load_records(path)]
