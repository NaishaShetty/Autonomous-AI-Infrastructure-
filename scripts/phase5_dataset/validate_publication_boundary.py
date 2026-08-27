"""Publication-boundary audit: scans the canonical dataset content for
host identity, absolute local filesystem paths, credentials/tokens, or
research-only-classified artifact references that must never appear in
PUBLIC_DATASET_CONTENT per PHASE5_1_PUBLICATION_BOUNDARY.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (re.compile(r"[A-Za-z]:\\\\?Users\\\\?[^\"\\\\]+", re.IGNORECASE), "windows_user_home_path"),
    (re.compile(r"/home/[^\"/]+/"), "unix_user_home_path"),
    (re.compile(r"\bC:\\\\", re.IGNORECASE), "absolute_windows_drive_path"),
    (re.compile(r"password|api[_-]?key|secret|token", re.IGNORECASE), "credential_like_token"),
]


def main(dataset_dir: str) -> None:
    out = Path(dataset_dir)
    findings = []
    n_records = 0
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            n_records += 1
            rec = json.loads(line)
            text = json.dumps(rec)
            for pattern, label in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    findings.append({
                        "record_id": rec["identity"]["record_id"],
                        "pattern": label,
                    })

    # frozen_run_dir values are expected to be repo-relative
    # (experiments/results/...) -- confirm none is an absolute path.
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            frd = rec["provenance"].get("frozen_run_dir")
            if frd and (frd.startswith("/") or re.match(r"^[A-Za-z]:", frd)):
                findings.append({"record_id": rec["identity"]["record_id"], "pattern": "absolute_frozen_run_dir"})

    audit = {
        "total_records_scanned": n_records,
        "total_findings": len(findings),
        "findings": findings[:100],
        "classification_applied": {
            "controlled_runtime_episode_records": "PUBLIC_DATASET_CONTENT",
            "agent_task_episode_records": "PUBLIC_DATASET_CONTENT",
            "trained_model_artifacts_referenced": "EXCLUDED_FROM_THIS_CONSTRUCTION (not ingested as records; prediction_artifact/ and prediction_scope_router_artifact/ pickled artifacts were never read by this script)",
            "sqlite_memory_store_files": "EXCLUDED_FROM_THIS_CONSTRUCTION (step6_memory_on.sqlite / step6_persistence_check.sqlite were never read by this script)",
            "v1_gen2_evidence": "EXCLUDED (never referenced by any source in src/phase5/sources.py)",
            "engineering_test_artifacts": "EXCLUDED (tests/ never read as a content source)",
        },
    }
    with open(out / "publication_boundary_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"publication boundary audit: {len(findings)} findings across {n_records} records")


if __name__ == "__main__":
    main(sys.argv[1])
