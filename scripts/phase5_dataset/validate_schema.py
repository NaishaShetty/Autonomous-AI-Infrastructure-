"""Validates every constructed record against PHASE5_1_SCHEMA.json using the
`jsonschema` package (programmatic structural validation, per Phase 5.2
deliverable 11).

Usage:
    python scripts/phase5_dataset/validate_schema.py <dataset_dir>

Writes <dataset_dir>/schema_validation_report.md and
<dataset_dir>/schema_validation_audit.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "experiments/results/phase5_dataset_specification/20260826T053011Z/PHASE5_1_SCHEMA.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main(dataset_dir: str) -> None:
    out = Path(dataset_dir)
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)

    n_pass = 0
    n_fail = 0
    failures = []
    with open(out / "dataset" / "all_records.jsonl", "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            rec = json.loads(line)
            errors = sorted(validator.iter_errors(rec), key=lambda e: e.path)
            if errors:
                n_fail += 1
                failures.append({
                    "line": line_no,
                    "record_id": rec.get("identity", {}).get("record_id"),
                    "errors": [
                        {"path": list(e.path), "message": e.message} for e in errors[:5]
                    ],
                })
            else:
                n_pass += 1

    audit = {
        "schema_version": schema.get("schema_version"),
        "total_records": n_pass + n_fail,
        "passed": n_pass,
        "failed": n_fail,
        "failures_sample": failures[:50],
        "n_failure_records_total": len(failures),
    }
    with open(out / "schema_validation_audit.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, sort_keys=True)
        f.write("\n")

    report = [
        "# Phase 5.2 Schema Validation Report",
        "",
        f"Schema: `{schema.get('$id')}` version `{schema.get('schema_version')}`",
        f"Total records validated: {n_pass + n_fail}",
        f"Passed: {n_pass}",
        f"Failed: {n_fail}",
        "",
    ]
    if failures:
        report.append("## Sample failures (first 50)")
        for fail in failures[:50]:
            report.append(f"- record_id={fail['record_id']} line={fail['line']}")
            for e in fail["errors"]:
                report.append(f"  - path={e['path']} message={e['message']}")
    else:
        report.append("No schema validation failures.")
    with open(out / "SCHEMA_VALIDATION_REPORT.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")

    print(f"schema validation: {n_pass} passed, {n_fail} failed")


if __name__ == "__main__":
    main(sys.argv[1])
