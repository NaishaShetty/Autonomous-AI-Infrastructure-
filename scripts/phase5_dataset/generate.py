"""Phase 5.2 dataset generation driver.

Usage:
    python scripts/phase5_dataset/generate.py <output_dir>

Writes the canonical dataset (JSONL + metadata) into <output_dir>. Pure
function of frozen evidence; does not touch any frozen path. Run this
script twice into two different output directories (with nothing else
changed) to test reproducibility -- see
scripts/phase5_dataset/regeneration_check.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from phase5.build_dataset import (  # noqa: E402
    build_all_records, DATASET_VERSION, SCHEMA_VERSION, GENERATION_SPEC_VERSION,
)


# Fields whose schema definition does NOT accept `null` as a valid value
# (unlike `agent_output`, whose schema is an explicit `oneOf [...,
# {"type": "null"}]`). PHASE5_1_SCHEMA.json makes none of its top-level
# properties `required` except identity/provenance/experimental_boundary/
# evidence_class/temporal/split_assignment, so a genuinely inapplicable
# optional sub-object (e.g. no `decision` was made in this episode) is
# correctly represented by OMITTING the key, not by writing `null` -- the
# earlier draft of this generator wrote explicit `null`s, which
# jsonschema Draft 2020-12 correctly rejected (`None is not of type
# 'object'`) since those definitions have no `"type": ["object", "null"]`
# union. This is classified as an implementation bug in the generator
# (category (a) per the task's classification requirement), NOT a Phase
# 5.1 schema deficiency: the schema's own optionality (absence of these
# keys from `required`) already provides the correct mechanism for
# "not applicable to this episode" and does not need a null-accepting
# type union.
_OMIT_IF_NONE = {
    "decision", "diagnosis", "recovery", "validation", "memory_interaction",
    "generalization", "prediction",
}


# Nested (sub_object, leaf_field) pairs whose schema type is a plain
# `boolean` (no null union) -- e.g. Recovery.reversible/authorized are
# genuinely unknown for some episodes (no explicit authorization gate was
# exercised in the raw evidence), which is legitimate missing information,
# not a schema violation; the correct fix is to omit the leaf key (letting
# it be absent, since it is not `required`) rather than encode `null` into
# a non-nullable boolean slot. Same implementation-bug category as above.
_OMIT_LEAF_IF_NONE = {
    "recovery": {"reversible", "authorized"},
}


def _clean_record(row: dict) -> dict:
    cleaned = dict(row)
    for key in _OMIT_IF_NONE:
        if key in cleaned and cleaned[key] is None:
            del cleaned[key]
    for parent, leaves in _OMIT_LEAF_IF_NONE.items():
        if parent in cleaned and isinstance(cleaned[parent], dict):
            sub = dict(cleaned[parent])
            for leaf in leaves:
                if leaf in sub and sub[leaf] is None:
                    del sub[leaf]
            cleaned[parent] = sub
    return cleaned


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(_clean_record(row), sort_keys=True, ensure_ascii=False))
            f.write("\n")


def write_json(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, sort_keys=True, ensure_ascii=False, indent=2)
        f.write("\n")


def compute_statistics(records: list[dict]) -> dict:
    stats: dict = {}
    stats["total_records"] = len(records)
    stats["by_track"] = dict(Counter(r["identity"]["track"] for r in records))
    stats["episodes"] = len({r["identity"]["episode_id"] for r in records})
    stats["runs"] = len({r["identity"]["run_id"] for r in records})
    stats["workloads"] = len({r["identity"]["workload_id"] for r in records})
    stats["environments"] = len({r["identity"]["environment_id"] for r in records})

    stats["by_task_family"] = dict(Counter(
        (r.get("agent_output") or {}).get("task_family", "NOT_APPLICABLE") for r in records
    ))
    stats["by_failure_class"] = dict(Counter(
        (r.get("failure") or {}).get("failure_class", "UNKNOWN") for r in records
    ))
    stats["by_decision_type"] = dict(Counter(
        ((r.get("decision") or {}).get("action") if r.get("decision") else "NOT_APPLICABLE") for r in records
    ))
    stats["by_recovery_outcome"] = dict(Counter(
        ((r.get("validation") or {}).get("validation_status") if r.get("validation") else "NOT_APPLICABLE") for r in records
    ))
    stats["by_outcome_class"] = dict(Counter(r.get("outcome_class", "UNKNOWN") for r in records))
    stats["by_uncertainty_mechanism"] = dict(Counter(
        (r.get("agent_output") or {}).get("task_family") if r.get("agent_output") else
        ("controlled_runtime_prediction_score" if r.get("prediction") else "NOT_APPLICABLE")
        for r in records
    ))
    stats["by_split_assignment"] = dict(Counter(r["split_assignment"] for r in records))
    stats["by_track_and_split"] = {}
    by_track_split = defaultdict(Counter)
    for r in records:
        by_track_split[r["identity"]["track"]][r["split_assignment"]] += 1
    for track, c in by_track_split.items():
        stats["by_track_and_split"][track] = dict(c)

    # UNKNOWN/UNAVAILABLE/NOT_APPLICABLE counts (never coerced to null/0)
    unknown_counts = {
        "diagnosis_suspected_cause_null_UNKNOWN": sum(
            1 for r in records if r.get("diagnosis") and r["diagnosis"].get("suspected_cause") is None
        ),
        "validation_status_UNKNOWN": sum(
            1 for r in records if r.get("validation") and r["validation"]["validation_status"] == "UNKNOWN"
        ),
        "environment_id_UNSPECIFIED_PRE_4_9": sum(
            1 for r in records if r["identity"]["environment_id"] == "UNSPECIFIED_PRE_4_9"
        ),
        "prediction_absent_NOT_APPLICABLE": sum(1 for r in records if r.get("prediction") is None),
        "decision_absent_NOT_APPLICABLE": sum(1 for r in records if r.get("decision") is None),
        "recovery_absent_NOT_APPLICABLE": sum(1 for r in records if r.get("recovery") is None),
    }
    stats["unknown_unavailable_not_applicable_counts"] = unknown_counts

    negative_results = {
        "NOT_RECOVERED_episodes": sum(
            1 for r in records if r.get("validation") and r["validation"]["validation_status"] == "NOT_RECOVERED"
        ),
        "UNKNOWN_validation_episodes": unknown_counts["validation_status_UNKNOWN"],
        "UNKNOWN_diagnosis_episodes": unknown_counts["diagnosis_suspected_cause_null_UNKNOWN"],
        "agent_task_incorrect_answers": sum(
            1 for r in records if r.get("failure", {}).get("failure_class") == "AGENT_INCORRECT_ANSWER"
        ),
        "predictability_status_NOT_EVALUATED": sum(
            1 for r in records if r.get("prediction") and r["prediction"]["predictability_status"] == "NOT_EVALUATED"
        ),
        "failure_class_mapping_fallback_used": sum(
            1 for r in records if r.get("failure_class_mapping_fallback_used")
        ),
    }
    stats["negative_result_counts"] = negative_results

    return stats


def main(output_dir: str) -> None:
    out = Path(output_dir)
    (out / "dataset" / "controlled_runtime").mkdir(parents=True, exist_ok=True)
    (out / "dataset" / "agent_task").mkdir(parents=True, exist_ok=True)

    records, hashcache = build_all_records()

    cr_records = [r for r in records if r["identity"]["track"] == "controlled_runtime"]
    at_records = [r for r in records if r["identity"]["track"] == "agent_task"]

    write_jsonl(out / "dataset" / "controlled_runtime" / "records.jsonl", cr_records)
    write_jsonl(out / "dataset" / "agent_task" / "records.jsonl", at_records)
    write_jsonl(out / "dataset" / "all_records.jsonl", records)

    metadata = {
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generation_spec_version": GENERATION_SPEC_VERSION,
        "source_file_sha256": hashcache.as_dict(),
        "total_records": len(records),
        "tracks": sorted({r["identity"]["track"] for r in records}),
    }
    write_json(out / "dataset_metadata.json", metadata)

    stats = compute_statistics(records)
    write_json(out / "dataset_statistics.json", stats)

    # lineage.json: source -> record_ids map (sorted)
    lineage = defaultdict(list)
    for r in records:
        lineage[r["provenance"]["source"]].append(r["identity"]["record_id"])
    lineage_out = {k: sorted(v) for k, v in sorted(lineage.items())}
    write_json(out / "lineage.json", {"source_to_record_ids": lineage_out})

    # split_assignment manifest
    split_manifest = sorted([
        {
            "record_id": r["identity"]["record_id"],
            "workload_id": r["identity"]["workload_id"],
            "run_id": r["identity"]["run_id"],
            "episode_id": r["identity"]["episode_id"],
            "environment_id": r["identity"]["environment_id"],
            "track": r["identity"]["track"],
            "split_assignment": r["split_assignment"],
        }
        for r in records
    ], key=lambda x: x["record_id"])
    write_json(out / "split_assignment_manifest.json", split_manifest)

    print(f"wrote {len(records)} records to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
