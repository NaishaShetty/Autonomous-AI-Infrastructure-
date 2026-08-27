"""Mechanical split/workload-ID compatibility validator (Phase 5.1 Open
Question 2).

Checks:
  1. TRAIN ∩ CALIBRATION = ∅, TRAIN ∩ TEST = ∅, CALIBRATION ∩ TEST = ∅ at
     the record level.
  2. No workload_id crosses a forbidden sample-level split boundary (a
     workload_id's records must all share one of train/calibration_validation/test).
  3. Environment-held-out boundary check: whether any record's
     environment_id corresponds to a genuine Phase 4.9 held-out/robustness
     environment and, if so, whether it was fit on (this dataset's current
     source evidence carries NO per-episode Phase-4.9 environment_id --
     every record has environment_id=UNSPECIFIED_PRE_4_9 -- so this check
     is reported as N/A/disclosed-limitation, not silently skipped).

Writes split_audit.json (machine-readable) and SPLIT_VALIDATION_REPORT.md
(prose, cites the audit numbers).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter


def main(dataset_dir: str) -> None:
    out = Path(dataset_dir)
    records = []
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    by_split = defaultdict(set)
    workload_to_splits = defaultdict(set)
    workload_to_records = defaultdict(list)
    env_counts = Counter()
    per_split_counts = defaultdict(lambda: {
        "records": 0, "workloads": set(), "runs": set(), "episodes": set(), "environments": set(),
    })

    for r in records:
        rid = r["identity"]["record_id"]
        split = r["split_assignment"]
        workload_id = r["identity"]["workload_id"]
        env_id = r["identity"]["environment_id"]

        by_split[split].add(rid)
        workload_to_splits[workload_id].add(split)
        workload_to_records[workload_id].append(rid)
        env_counts[env_id] += 1

        bucket = per_split_counts[split]
        bucket["records"] += 1
        bucket["workloads"].add(workload_id)
        bucket["runs"].add(r["identity"]["run_id"])
        bucket["episodes"].add(r["identity"]["episode_id"])
        bucket["environments"].add(env_id)

    train = by_split.get("train", set())
    calib = by_split.get("calibration_validation", set())
    test = by_split.get("test", set())

    overlap_train_calib = train & calib
    overlap_train_test = train & test
    overlap_calib_test = calib & test

    workloads_crossing_splits = {
        wl: sorted(splits) for wl, splits in workload_to_splits.items() if len(splits) > 1
    }

    per_split_summary = {
        split: {
            "records": b["records"],
            "workloads": len(b["workloads"]),
            "runs": len(b["runs"]),
            "episodes": len(b["episodes"]),
            "environments": sorted(b["environments"]),
        }
        for split, b in per_split_counts.items()
    }

    audit = {
        "total_records": len(records),
        "per_split_counts": per_split_summary,
        "overlap_counts": {
            "train_and_calibration_validation": len(overlap_train_calib),
            "train_and_test": len(overlap_train_test),
            "calibration_validation_and_test": len(overlap_calib_test),
        },
        "workload_id_cross_split_violations": {
            "count": len(workloads_crossing_splits),
            "examples": dict(list(workloads_crossing_splits.items())[:20]),
        },
        "environment_axis_check": {
            "distinct_environment_ids_present": dict(env_counts),
            "status": "DISCLOSED_LIMITATION_NOT_APPLICABLE",
            "explanation": (
                "No source used in this construction carries a genuine "
                "per-episode Phase-4.9 EnvironmentId (phase4.9-env-baseline-cpu / "
                "-memory-constrained / -dependency-network-constrained); every "
                "extracted record's identity.environment_id is "
                "UNSPECIFIED_PRE_4_9 because the only sources with real "
                "per-episode raw evidence available to this construction "
                "(phase4_4_autonomy_pipeline/results.json, "
                "phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl, "
                "phase4_6_to_4_10 agent-task raw evidence) predate Phase 4.9's "
                "EnvironmentProfile introduction or do not carry it at the "
                "per-record level. The Phase-4.9/post-P5-Step-4 environment-role "
                "evidence that DOES exist (experiments/results/post_p5_remediation/"
                "20260825T064402Z/raw/p4_step4_results.json) is aggregate-only "
                "(per-environment metric rollups, no retained per-episode/per-run "
                "identity), so it cannot be joined back to individual dataset "
                "records without fabricating a join key. This is classified as "
                "(c) unavailable source evidence, disclosed rather than worked "
                "around by inventing environment_id values."
            ),
        },
    }

    with open(out / "split_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")

    all_zero = (
        audit["overlap_counts"]["train_and_calibration_validation"] == 0
        and audit["overlap_counts"]["train_and_test"] == 0
        and audit["overlap_counts"]["calibration_validation_and_test"] == 0
        and audit["workload_id_cross_split_violations"]["count"] == 0
    )

    report = [
        "# Phase 5.2 Split Validation Report",
        "",
        f"Total records: {len(records)}",
        "",
        "## Per-split counts",
        "",
        "| split | records | workloads | runs | episodes |",
        "|---|---|---|---|---|",
    ]
    for split, s in sorted(per_split_summary.items()):
        report.append(f"| {split} | {s['records']} | {s['workloads']} | {s['runs']} | {s['episodes']} |")

    report += [
        "",
        "## Forbidden overlap counts (must all be zero)",
        "",
        f"- train ∩ calibration_validation = {audit['overlap_counts']['train_and_calibration_validation']}",
        f"- train ∩ test = {audit['overlap_counts']['train_and_test']}",
        f"- calibration_validation ∩ test = {audit['overlap_counts']['calibration_validation_and_test']}",
        f"- workload_id records crossing a forbidden split boundary = {audit['workload_id_cross_split_violations']['count']}",
        "",
        f"**Overall: {'PASS -- all forbidden overlaps are zero' if all_zero else 'FAIL -- see counts above'}**",
        "",
        "## Environment-axis (held-out/robustness) boundary check",
        "",
        "Status: DISCLOSED LIMITATION / NOT APPLICABLE to the current record set.",
        audit["environment_axis_check"]["explanation"],
        "",
        "## Known coverage gap (Phase 5.1 Split Policy §6)",
        "",
        "Per PHASE5_1_SPLIT_POLICY.md §6, prior full-loop evaluation runs used a "
        "unique workload_id per episode by design in some runs, meaning the "
        "workload-grouping rule is exercised only where multiple records "
        "genuinely share a workload_id (this happens for the arithmetic "
        "self-consistency family, grouped by seed, and for the controlled-runtime "
        "`workload-recurring` repeated-incident episodes in Phase 4.4). Other "
        "workload_ids in this dataset are 1:1 with a single record by "
        "construction (agent sentiment/QA task instances, most controlled-runtime "
        "episodes) -- this is a coverage characteristic of the source evidence, "
        "not a flaw in the split policy or its enforcement.",
    ]
    with open(out / "SPLIT_VALIDATION_REPORT.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")

    print(f"split audit: overlaps={audit['overlap_counts']}, "
          f"workload_violations={audit['workload_id_cross_split_violations']['count']}")


if __name__ == "__main__":
    main(sys.argv[1])
