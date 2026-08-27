"""Fail-closed dataset validation. A single failure stops the benchmark run."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .constants import (
    DATASET_VERSION,
    EXPECTED_ALL_RECORDS_SHA256,
    EXPECTED_ENVIRONMENTS,
    EXPECTED_EPISODES,
    EXPECTED_SPLIT_COUNTS,
    EXPECTED_TOTAL_RECORDS,
    EXPECTED_WORKLOADS,
    SCHEMA_VERSION,
)
from .status import FAILED_VALIDATION

REQUIRED_TOP_LEVEL = (
    "identity",
    "provenance",
    "experimental_boundary",
    "evidence_class",
    "temporal",
    "split_assignment",
)
REQUIRED_IDENTITY = (
    "dataset_version",
    "schema_version",
    "record_id",
    "track",
    "environment_id",
    "workload_id",
    "run_id",
    "episode_id",
)
VALID_SPLITS = {"train", "calibration_validation", "test"}
VALID_AVAILABILITY = {
    "AVAILABLE_BEFORE_DECISION",
    "AVAILABLE_AT_DECISION",
    "AVAILABLE_AFTER_DECISION",
    "AVAILABLE_AFTER_OUTCOME",
    "TIMESTAMP_UNKNOWN",
    "UNAVAILABLE",
}


class DatasetValidationError(Exception):
    def __init__(self, violations: list[dict]):
        self.violations = violations
        super().__init__(f"dataset validation failed with {len(violations)} violation(s)")


def _v(rule: str, message: str, record_id: str | None = None) -> dict:
    return {"rule": rule, "message": message, "record_id": record_id}


def validate_dataset(bundle: dict, *, expected_hash: str | None = EXPECTED_ALL_RECORDS_SHA256) -> dict:
    """Validate schema, IDs, hashes, splits, workloads, provenance, temporal, publication."""
    violations: list[dict] = []
    records: list[dict] = bundle["records"]
    metadata = bundle.get("metadata") or {}

    if metadata.get("dataset_version") != DATASET_VERSION:
        violations.append(_v("dataset_version", f"expected {DATASET_VERSION}, got {metadata.get('dataset_version')}"))
    if metadata.get("schema_version") != SCHEMA_VERSION:
        violations.append(_v("schema_version", f"expected {SCHEMA_VERSION}, got {metadata.get('schema_version')}"))

    if expected_hash is not None and bundle.get("all_records_sha256") != expected_hash:
        violations.append(
            _v(
                "source_hash",
                f"all_records.jsonl sha256 {bundle.get('all_records_sha256')} != expected {expected_hash}",
            )
        )

    if len(records) != EXPECTED_TOTAL_RECORDS and expected_hash is not None:
        violations.append(_v("record_count", f"expected {EXPECTED_TOTAL_RECORDS} records, got {len(records)}"))

    ids: list[str] = []
    full_digests: list[str] = []
    workload_to_splits: dict[str, set[str]] = defaultdict(set)
    split_counts: Counter[str] = Counter()
    env_ids: set[str] = set()
    episode_ids: set[str] = set()
    workload_ids: set[str] = set()
    seen_ids: set[str] = set()

    for rec in records:
        ident = rec.get("identity") or {}
        rid = ident.get("record_id")
        for field in REQUIRED_TOP_LEVEL:
            if field not in rec:
                violations.append(_v("schema", f"missing top-level field {field}", rid))
        for field in REQUIRED_IDENTITY:
            if field not in ident:
                violations.append(_v("schema", f"missing identity.{field}", rid))
        if rid is None:
            violations.append(_v("record_id", "missing record_id"))
            continue
        if rid in seen_ids:
            violations.append(_v("record_id", "duplicate record_id", rid))
        seen_ids.add(rid)
        ids.append(rid)
        fd = ident.get("record_id_full_digest")
        if fd:
            full_digests.append(fd)
        split = rec.get("split_assignment")
        if split not in VALID_SPLITS:
            violations.append(_v("split", f"invalid split_assignment {split!r}", rid))
        else:
            split_counts[split] += 1
            workload_to_splits[ident.get("workload_id", "")].add(split)
        env_ids.add(ident.get("environment_id"))
        episode_ids.add(ident.get("episode_id"))
        workload_ids.add(ident.get("workload_id"))
        if ident.get("dataset_version") != DATASET_VERSION:
            violations.append(_v("dataset_version", "per-record dataset_version mismatch", rid))
        if ident.get("schema_version") != SCHEMA_VERSION:
            violations.append(_v("schema_version", "per-record schema_version mismatch", rid))
        prov = rec.get("provenance") or {}
        if not prov.get("checksum"):
            violations.append(_v("provenance", "missing provenance.checksum", rid))
        if prov.get("evidence_class") not in (1, 2, 3, 4, 5, 6, 7, 8):
            violations.append(_v("publication", f"invalid evidence_class {prov.get('evidence_class')}", rid))
        if rec.get("experimental_boundary") not in (
            "controlled_runtime_evidence",
            "research_evaluation_evidence",
            "benchmark_ready_evidence",
            "engineering_only_evidence",
        ):
            violations.append(_v("publication", f"invalid experimental_boundary {rec.get('experimental_boundary')}", rid))
        temporal = rec.get("temporal") or {}
        avail = temporal.get("availability_of_this_record")
        if avail not in VALID_AVAILABILITY:
            violations.append(_v("temporal", f"invalid availability {avail!r}", rid))
        if "decision_time" not in temporal:
            violations.append(_v("temporal", "missing decision_time", rid))

    if expected_hash is not None:
        if len(episode_ids) != EXPECTED_EPISODES:
            violations.append(_v("episodes", f"expected {EXPECTED_EPISODES} episodes, got {len(episode_ids)}"))
        if len(workload_ids) != EXPECTED_WORKLOADS:
            violations.append(_v("workloads", f"expected {EXPECTED_WORKLOADS} workloads, got {len(workload_ids)}"))
        if len(env_ids) != EXPECTED_ENVIRONMENTS:
            violations.append(_v("environments", f"expected {EXPECTED_ENVIRONMENTS} environments, got {len(env_ids)} {sorted(env_ids)}"))
        for split, n in EXPECTED_SPLIT_COUNTS.items():
            if split_counts[split] != n:
                violations.append(_v("split", f"expected {n} {split} records, got {split_counts[split]}"))

    crossing = {wl: sorted(s) for wl, s in workload_to_splits.items() if len(s) > 1}
    if crossing:
        examples = list(crossing.items())[:5]
        violations.append(_v("workload_grouping", f"workload_id crosses splits: {examples}"))

    if len(full_digests) == len(records) and len(set(full_digests)) != len(full_digests):
        violations.append(_v("record_id", "duplicate record_id_full_digest"))

    audit = {
        "ok": len(violations) == 0,
        "n_records": len(records),
        "n_unique_record_ids": len(seen_ids),
        "n_episodes": len(episode_ids),
        "n_workloads": len(workload_ids),
        "n_environments": len(env_ids),
        "environments": sorted(x for x in env_ids if x is not None),
        "split_counts": dict(split_counts),
        "all_records_sha256": bundle.get("all_records_sha256"),
        "violations": violations,
        "status": "PASSED" if not violations else FAILED_VALIDATION,
    }
    if violations:
        raise DatasetValidationError(violations)
    return audit
