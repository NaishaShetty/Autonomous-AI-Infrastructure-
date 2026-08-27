"""Load ONLY the canonical Phase 5.2 dataset (or an explicit test injection)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import (
    CANONICAL_DATASET_DIR,
    CANONICAL_SPEC_DIR,
    DATASET_VERSION,
    EXPECTED_ALL_RECORDS_SHA256,
    SCHEMA_VERSION,
)
from .ids import sha256_file


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    # Deterministic order: record_id, never filesystem/dict iteration order.
    records.sort(key=lambda r: r["identity"]["record_id"])
    return records


def load_canonical_dataset(dataset_dir: Path | None = None) -> dict:
    """Load frozen Phase 5.2 artifacts. Does not modify them."""
    ddir = Path(dataset_dir) if dataset_dir is not None else CANONICAL_DATASET_DIR
    all_path = ddir / "dataset" / "all_records.jsonl"
    if not all_path.is_file():
        raise FileNotFoundError(f"canonical dataset missing: {all_path}")
    records = load_jsonl(all_path)
    metadata = load_json(ddir / "dataset_metadata.json")
    statistics = load_json(ddir / "dataset_statistics.json")
    split_manifest = load_json(ddir / "split_assignment_manifest.json")
    split_audit = load_json(ddir / "split_audit.json")
    leakage_audit = load_json(ddir / "leakage_audit.json")
    provenance_audit = load_json(ddir / "provenance_audit.json")
    record_id_audit = load_json(ddir / "record_id_audit.json")
    publication_audit = load_json(ddir / "publication_boundary_audit.json")
    lineage = load_json(ddir / "lineage.json")
    sha_manifest = load_json(ddir / "SHA256_MANIFEST.json")
    bytes_hash = sha256_file(all_path)
    return {
        "dataset_dir": str(ddir),
        "records": records,
        "metadata": metadata,
        "statistics": statistics,
        "split_assignment_manifest": split_manifest,
        "split_audit": split_audit,
        "leakage_audit": leakage_audit,
        "provenance_audit": provenance_audit,
        "record_id_audit": record_id_audit,
        "publication_boundary_audit": publication_audit,
        "lineage": lineage,
        "sha256_manifest": sha_manifest,
        "all_records_sha256": bytes_hash,
        "expected_all_records_sha256": EXPECTED_ALL_RECORDS_SHA256,
        "dataset_version": metadata.get("dataset_version", DATASET_VERSION),
        "schema_version": metadata.get("schema_version", SCHEMA_VERSION),
    }


def load_frozen_spec(spec_dir: Path | None = None) -> dict:
    sdir = Path(spec_dir) if spec_dir is not None else CANONICAL_SPEC_DIR
    return {
        "spec_dir": str(sdir),
        "task_catalog": load_json(sdir / "PHASE5_3_TASK_CATALOG.json"),
        "metric_catalog": load_json(sdir / "PHASE5_3_METRIC_CATALOG.json"),
        "baseline_catalog": load_json(sdir / "PHASE5_3_BASELINE_CATALOG.json"),
        "ablation_matrix": load_json(sdir / "PHASE5_3_ABLATION_MATRIX.json"),
        "benchmark_schema": load_json(sdir / "PHASE5_3_BENCHMARK_SCHEMA.json"),
        "dataset_coverage": load_json(sdir / "PHASE5_3_DATASET_COVERAGE.json"),
        "unsupported_capabilities": load_json(sdir / "unsupported_capabilities.json"),
        "sha256_manifest": load_json(sdir / "SHA256_MANIFEST.json"),
    }


def task_family(record: dict) -> str | None:
    ao = record.get("agent_output") or {}
    fam = ao.get("task_family")
    if fam:
        return fam
    wl = (record.get("workload") or {}).get("workload_type")
    if wl in (
        "arithmetic_self_consistency",
        "sentiment_softmax_margin",
        "extractive_qa_span_logit",
    ):
        return wl
    return None


def confidence_value(record: dict) -> float | None:
    ao = record.get("agent_output") or {}
    fam = ao.get("task_family")
    if fam == "arithmetic_self_consistency":
        v = ao.get("agreement_rate")
    elif fam == "sentiment_softmax_margin":
        v = ao.get("softmax_margin")
    elif fam == "extractive_qa_span_logit":
        v = ao.get("span_logit_confidence")
    else:
        pred = record.get("prediction") or {}
        v = pred.get("score")
    if v is None:
        return None
    return float(v)
