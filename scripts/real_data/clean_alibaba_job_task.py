"""
Phase 3 real-data replication — conservative cleaning of
pai_job_table.csv and pai_task_table.csv (Alibaba GPU2020).

Reads ONLY from data/raw/alibaba_gpu2020/*.tar.gz (never modified, never
extracted to disk in place). Writes:
  data/processed/alibaba_gpu2020/job_table.clean.csv
  data/processed/alibaba_gpu2020/task_table.clean.csv
  data/audit/alibaba_gpu2020/job_table_removed_records.csv
  data/audit/alibaba_gpu2020/task_table_removed_records.csv
  data/audit/alibaba_gpu2020/cleaning_report.json

Cleaning rules (conservative — see docs/PHASE3_REAL_DATA_CLEANING_REPORT.md
for full justification):
  - A row is REMOVED only if it is malformed: wrong field count, a
    required numeric field that fails to parse, a status value outside
    the documented enum, or end_time < start_time (a physically
    impossible ordering).
  - Missing end_time (censored Running/Waiting jobs, per the official
    schema) is NOT an error and is NOT imputed — preserved as empty.
  - Missing/optional fields (plan_mem, gpu_type, etc.) are preserved
    as-is, not filled.
  - No row is removed because of "outlier" values — only genuinely
    impossible ones (see above).
  - Every source row keeps a `_source_row_index` (0-based line number
    within the raw CSV) for full traceability back to the raw file.

Deterministic and reproducible: no randomness in this script.
"""
import csv
import json
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "alibaba_gpu2020"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "alibaba_gpu2020"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "alibaba_gpu2020"

JOB_STATUS_ENUM = {"Running", "Terminated", "Failed", "Waiting"}
TASK_STATUS_ENUM = {"Running", "Terminated", "Failed", "Waiting"}

JOB_FIELDS = ["job_name", "inst_id", "user", "status", "start_time", "end_time"]
TASK_FIELDS = [
    "job_name", "task_name", "inst_num", "status", "start_time",
    "end_time", "plan_cpu", "plan_mem", "plan_gpu", "gpu_type",
]


def stream_csv_rows(tar_path, member_name):
    tf = tarfile.open(tar_path, "r:gz")
    f = tf.extractfile(member_name)
    for i, raw in enumerate(f):
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        yield i, line.split(",")


def parse_float_or_empty(s):
    if s == "":
        return None, True  # (value, is_empty)
    try:
        return float(s), False
    except ValueError:
        return None, False  # parse failure, not empty


def clean_job_table():
    report = {
        "table": "pai_job_table",
        "raw_rows": 0,
        "retained": 0,
        "removed": 0,
        "removed_reasons": {},
        "status_distribution_raw": {},
        "missing_end_time_raw": 0,
        "duplicate_job_name": 0,
    }
    seen_job_names = set()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "job_table.clean.csv"
    removed_path = AUDIT_DIR / "job_table_removed_records.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as out_f, \
         open(removed_path, "w", newline="", encoding="utf-8") as rem_f:
        out_w = csv.writer(out_f)
        out_w.writerow(["_source_row_index"] + JOB_FIELDS)
        rem_w = csv.writer(rem_f)
        rem_w.writerow(["_source_row_index", "raw_line", "reason"])

        for idx, parts in stream_csv_rows(RAW_DIR / "pai_job_table.tar.gz", "pai_job_table.csv"):
            report["raw_rows"] += 1
            reason = None

            if len(parts) != len(JOB_FIELDS):
                reason = f"wrong_field_count:{len(parts)}"
            else:
                job_name, inst_id, user, status, start_s, end_s = parts
                if job_name == "":
                    reason = "empty_job_name"
                elif status not in JOB_STATUS_ENUM:
                    reason = f"invalid_status:{status}"
                else:
                    start_v, start_empty = parse_float_or_empty(start_s)
                    if start_v is None and not start_empty:
                        reason = "unparseable_start_time"
                    elif start_empty and status != "Waiting":
                        # A job that has left the Waiting state must have
                        # a start_time; missing start_time is only
                        # domain-meaningful (not-yet-launched) for
                        # status=Waiting, per the official schema.
                        reason = "missing_start_time_for_non_waiting_status"
                    elif not start_empty:
                        end_v, end_empty = parse_float_or_empty(end_s)
                        if not end_empty and end_v is None:
                            reason = "unparseable_end_time"
                        elif not end_empty and end_v < start_v:
                            reason = "end_before_start"

            if reason is None:
                job_name = parts[0]
                report["status_distribution_raw"][parts[3]] = (
                    report["status_distribution_raw"].get(parts[3], 0) + 1
                )
                if parts[5] == "":
                    report["missing_end_time_raw"] += 1
                if job_name in seen_job_names:
                    report["duplicate_job_name"] += 1
                else:
                    seen_job_names.add(job_name)
                out_w.writerow([idx] + parts)
                report["retained"] += 1
            else:
                rem_w.writerow([idx, ",".join(parts), reason])
                report["removed"] += 1
                report["removed_reasons"][reason] = report["removed_reasons"].get(reason, 0) + 1

    return report


def clean_task_table(valid_job_names):
    report = {
        "table": "pai_task_table",
        "raw_rows": 0,
        "retained": 0,
        "removed": 0,
        "removed_reasons": {},
        "status_distribution_raw": {},
        "missing_end_time_raw": 0,
        "job_name_not_in_clean_job_table": 0,
    }
    out_path = PROCESSED_DIR / "task_table.clean.csv"
    removed_path = AUDIT_DIR / "task_table_removed_records.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as out_f, \
         open(removed_path, "w", newline="", encoding="utf-8") as rem_f:
        out_w = csv.writer(out_f)
        out_w.writerow(["_source_row_index"] + TASK_FIELDS)
        rem_w = csv.writer(rem_f)
        rem_w.writerow(["_source_row_index", "raw_line", "reason"])

        for idx, parts in stream_csv_rows(RAW_DIR / "pai_task_table.tar.gz", "pai_task_table.csv"):
            report["raw_rows"] += 1
            reason = None

            if len(parts) != len(TASK_FIELDS):
                reason = f"wrong_field_count:{len(parts)}"
            else:
                (job_name, task_name, inst_num_s, status, start_s, end_s,
                 plan_cpu_s, plan_mem_s, plan_gpu_s, gpu_type) = parts
                if job_name == "":
                    reason = "empty_job_name"
                elif status not in TASK_STATUS_ENUM:
                    reason = f"invalid_status:{status}"
                else:
                    start_v, start_empty = parse_float_or_empty(start_s)
                    if start_v is None and not start_empty:
                        reason = "unparseable_start_time"
                    elif start_empty and status != "Waiting":
                        reason = "missing_start_time_for_non_waiting_status"
                    elif not start_empty:
                        end_v, end_empty = parse_float_or_empty(end_s)
                        if not end_empty and end_v is None:
                            reason = "unparseable_end_time"
                        elif not end_empty and end_v < start_v:
                            reason = "end_before_start"
                        elif not end_empty and end_v == start_v:
                            pass  # zero-duration task: legitimate, not an error

            if reason is None:
                report["status_distribution_raw"][parts[3]] = (
                    report["status_distribution_raw"].get(parts[3], 0) + 1
                )
                if parts[5] == "":
                    report["missing_end_time_raw"] += 1
                if parts[0] not in valid_job_names:
                    report["job_name_not_in_clean_job_table"] += 1
                out_w.writerow([idx] + parts)
                report["retained"] += 1
            else:
                rem_w.writerow([idx, ",".join(parts), reason])
                report["removed"] += 1
                report["removed_reasons"][reason] = report["removed_reasons"].get(reason, 0) + 1

    return report


def main():
    job_report = clean_job_table()
    print("job_table:", json.dumps(job_report, indent=2))

    valid_job_names = set()
    with open(PROCESSED_DIR / "job_table.clean.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            valid_job_names.add(row["job_name"])

    task_report = clean_task_table(valid_job_names)
    print("task_table:", json.dumps(task_report, indent=2))

    combined = {"job_table": job_report, "task_table": task_report}
    with open(AUDIT_DIR / "cleaning_report.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)


if __name__ == "__main__":
    main()
