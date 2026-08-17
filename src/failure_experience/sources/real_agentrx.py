"""Adapter: AgentRx joined trajectory records
(data/processed/agentrx/{tau_retail_joined,magentic_joined}.jsonl) ->
NormalizedRecord.

AgentRx is agent-trajectory data, not infra telemetry -- its "observations"
are thin by nature (no CPU/memory/latency signal exists for an LLM-agent
trajectory), and per the repo audit, its own ``recovery_action`` /
``recovery_outcome`` fields are literally the string ``"MISSING"`` for
every record inspected: this dataset structurally has no recovery data.
Both facts are represented honestly (RecoveryStatus.NOT_OBSERVED, sparse
Observations) rather than papered over.

``root_cause_reason`` / ``failure_categories`` are dataset-curator
annotations (human judgment), not a live system's diagnosis -- tagged
DiagnosisSource.HUMAN_DATASET_ANNOTATION, per the observation/interpretation
separation rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ._util import synthetic_timestamp

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed" / "agentrx"
DEFAULT_FILES = ["tau_retail_joined.jsonl", "magentic_joined.jsonl"]

MAX_EVIDENCE_TEXT_CHARS = 300


def load_records(files: list[str] | None = None) -> list[dict]:
    records: list[dict] = []
    for name in files or DEFAULT_FILES:
        path = DATA_DIR / name
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def _content_hash(files: list[str] | None = None) -> str:
    h = hashlib.sha256()
    for name in files or DEFAULT_FILES:
        path = DATA_DIR / name
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()[:16]


def to_normalized(record: dict, dataset_content_hash: str) -> dict | None:
    if not record.get("has_failure_annotation"):
        return None  # only failure episodes belong in a FailureExperience store

    trajectory_id = record["trajectory_id"]
    key = f"agentrx|{trajectory_id}"
    obs_ts = synthetic_timestamp(key)
    failure_categories = record.get("failure_categories") or []
    failure_type = failure_categories[0] if failure_categories else "unspecified_agent_failure"
    reason = (record.get("root_cause_reason") or "")[:MAX_EVIDENCE_TEXT_CHARS] or None
    recovery_missing = record.get("recovery_action") in (None, "MISSING")

    return {
        "source_dataset": "agentrx",
        "episode_id": trajectory_id,
        "occurrence_key": record.get("annotation_id_used_for_join", trajectory_id),
        "observed_at": obs_ts,
        "workload_id": record.get("domain", "agentrx_agent"),
        "workload_type": "llm_agent_trajectory",
        "environment": record.get("source_dataset"),
        "runtime_context": {"num_steps": record.get("num_steps")},
        "system_state": {
            "num_failures": record.get("num_failures"),
            "root_cause_failure_id": record.get("root_cause_failure_id"),
        },
        "failure_type": failure_type,
        "affected_component": record.get("domain"),
        "failure_status": "open",
        "diagnosis_suspected_cause": reason,
        "diagnosis_confidence": None,  # categorical human annotation, not a probability
        "diagnosis_evidence": failure_categories,
        "diagnosis_method": "agentrx_dataset_curator_annotation",
        "diagnosis_method_version": "agentrx_v1",
        "diagnosis_source": "human_dataset_annotation" if reason else "not_attempted",
        "recovery_status": "not_observed" if recovery_missing else "attempted",
        "recovery_selected_action": None if recovery_missing else record.get("recovery_action"),
        "recovery_execution_result": None if recovery_missing else record.get("recovery_outcome"),
        "validation_result": "not_performed",
        "outcome_task_success": False,
        "outcome_final_status": "failure",
        "provenance_source_workload": record.get("domain"),
        "provenance_dataset_content_hash": dataset_content_hash,
        "provenance_experiment_id": "real_data_expansion",
        "provenance_raw_record_ref": {
            "trajectory_id": trajectory_id,
            "source_trajectory_file": record.get("source_trajectory_file"),
            "source_annotation_file": record.get("source_annotation_file"),
        },
        "temporal": {"observation_ts": obs_ts, "detection_ts": obs_ts},
    }


def load_normalized(files: list[str] | None = None) -> list[dict]:
    content_hash = _content_hash(files)
    out = []
    for r in load_records(files):
        n = to_normalized(r, content_hash)
        if n is not None:
            out.append(n)
    return out
