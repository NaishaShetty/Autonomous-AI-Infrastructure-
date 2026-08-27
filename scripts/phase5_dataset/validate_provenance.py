"""Provenance validator: confirms ground truth is never conflated with
model output/self-report, and that every record's provenance object is
structurally complete and traces to a real, hash-verified source file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3] if False else None


def main(dataset_dir: str) -> None:
    out = Path(dataset_dir)
    records = []
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    metadata = json.loads((out / "dataset_metadata.json").read_text(encoding="utf-8"))
    source_hashes = metadata["source_file_sha256"]

    problems = []
    label_type_counts = {}
    from collections import Counter
    all_label_types = Counter()

    for r in records:
        prov = r["provenance"]
        required_prov_fields = ["source", "source_version", "extraction_method", "timestamp_quality", "evidence_class"]
        for f_ in required_prov_fields:
            if f_ not in prov or prov[f_] is None:
                problems.append({"record_id": r["identity"]["record_id"], "issue": f"missing provenance.{f_}"})

        # checksum must match a real, recorded source file hash
        checksum = prov.get("checksum")
        if checksum not in source_hashes.values():
            problems.append({"record_id": r["identity"]["record_id"], "issue": "provenance.checksum not found in dataset_metadata.json source_file_sha256"})

        for lbl in r.get("labels", []):
            all_label_types[lbl["label_type"]] += 1
            # ground-truth-eligible must only be OBJECTIVE_GROUND_TRUTH or OBSERVED_OUTCOME_VALIDATED
            if lbl.get("is_ground_truth_eligible") and lbl["label_type"] not in (
                "OBJECTIVE_GROUND_TRUTH", "OBSERVED_OUTCOME_VALIDATED"
            ):
                problems.append({
                    "record_id": r["identity"]["record_id"],
                    "issue": f"is_ground_truth_eligible=true but label_type={lbl['label_type']}",
                })

        # diagnosis/prediction/recovery.executor_self_report must carry
        # their mandated non-ground-truth label_type
        if r.get("diagnosis") is not None and r["diagnosis"]["label_type"] != "MODEL_DIAGNOSIS":
            problems.append({"record_id": r["identity"]["record_id"], "issue": "diagnosis.label_type is not MODEL_DIAGNOSIS"})
        if r.get("prediction") is not None and r["prediction"]["label_type"] != "MODEL_PREDICTION":
            problems.append({"record_id": r["identity"]["record_id"], "issue": "prediction.label_type is not MODEL_PREDICTION"})
        if r.get("decision") is not None and r["decision"]["label_type"] != "MODEL_PREDICTION":
            problems.append({"record_id": r["identity"]["record_id"], "issue": "decision.label_type is not MODEL_PREDICTION"})
        if r.get("validation") is not None and r["validation"]["label_type"] != "OBSERVED_OUTCOME_VALIDATED":
            problems.append({"record_id": r["identity"]["record_id"], "issue": "validation.label_type is not OBSERVED_OUTCOME_VALIDATED"})

    audit = {
        "total_records": len(records),
        "total_problems": len(problems),
        "problems_sample": problems[:50],
        "label_type_distribution": dict(all_label_types),
        "source_files_referenced": sorted(source_hashes.keys()),
    }
    with open(out / "provenance_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")

    report = [
        "# Phase 5.2 Provenance Validation Report",
        "",
        f"Total records: {len(records)}",
        f"Total provenance problems: {len(problems)}",
        "",
        "## Label type distribution (across all labels[] entries)",
    ]
    for lt, c in sorted(all_label_types.items()):
        report.append(f"- {lt}: {c}")
    report += [
        "",
        f"**Result: {'PASS' if not problems else 'FAIL -- see provenance_audit.json'}**",
        "",
        "## What was checked",
        "- every record's provenance object has source/source_version/extraction_method/timestamp_quality/evidence_class",
        "- every record's provenance.checksum matches a real, recorded sha256 of an actual frozen source file (dataset_metadata.json)",
        "- every labels[] entry with is_ground_truth_eligible=true has label_type in {OBJECTIVE_GROUND_TRUTH, OBSERVED_OUTCOME_VALIDATED} only",
        "- diagnosis/prediction/decision/validation sub-objects carry their schema-mandated, non-substitutable label_type",
    ]
    with open(out / "PROVENANCE_VALIDATION_REPORT.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")

    print(f"provenance audit: {len(problems)} problems across {len(records)} records")


if __name__ == "__main__":
    main(sys.argv[1])
