"""
Phase 3 real-data replication -- retain linked task/instance/sensor/
machine_metric records for a given sampled job-id tier, WITHOUT
sampling those child tables independently (per Step 6: "do not sample
sensor rows independently of their parent entities").

Reads job IDs from data/audit/alibaba_gpu2020/sample_job_ids_<tier>.txt
(produced by alibaba_stratified_sampling.py) and streams the raw
instance_table / sensor_table / machine_metric archives (never
modified) to pull out exactly the rows belonging to a sampled job.
task_table linkage is a simple filter of the already-cleaned
task_table.clean.csv.

NOTE on machine_metric/sensor_table: these are retained here for
completeness of the linked record set and for POST-HOC/descriptive
use only -- per docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md
both tables are CONFIRMED LEAKING (full-instance-lifetime aggregates)
and must not be used as decision-time input features in any
predictive Phase 3.1-3.6 evaluation.
"""
import csv
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "alibaba_gpu2020"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "alibaba_gpu2020"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "alibaba_gpu2020"

INSTANCE_FIELDS = ["job_name", "task_name", "inst_name", "worker_name", "inst_id", "status", "start_time", "end_time", "machine"]
SENSOR_FIELDS = ["job_name", "task_name", "worker_name", "inst_id", "machine", "gpu_name", "cpu_usage", "gpu_wrk_util", "avg_mem", "max_mem", "avg_gpu_wrk_mem", "max_gpu_wrk_mem", "read", "write", "read_count", "write_count"]
MACHINE_METRIC_FIELDS = ["worker_name", "machine", "start_time", "end_time", "machine_cpu_iowait", "machine_cpu_kernel", "machine_cpu_usr", "machine_gpu", "machine_load_1", "machine_net_receive", "machine_num_worker", "machine_cpu"]


def stream_csv_rows(tar_path, member_name):
    tf = tarfile.open(tar_path, "r:gz")
    f = tf.extractfile(member_name)
    for raw in f:
        yield raw.decode("utf-8", errors="replace").rstrip("\n").split(",")


def filter_task_table(job_ids, tier):
    out_path = PROCESSED_DIR / f"task_table.{tier}_sample.csv"
    n = 0
    with open(PROCESSED_DIR / "task_table.clean.csv", encoding="utf-8") as fin, \
         open(out_path, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(reader.fieldnames)
        for row in reader:
            if row["job_name"] in job_ids:
                writer.writerow(row.values())
                n += 1
    print(f"task_table.{tier}_sample.csv: {n} rows")
    return n


def filter_table(archive, member, fields, job_ids, tier, label):
    out_path = PROCESSED_DIR / f"{label}.{tier}_sample.csv"
    n = 0
    total = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(fields)
        for parts in stream_csv_rows(RAW_DIR / archive, member):
            total += 1
            if len(parts) == len(fields) and parts[0] in job_ids:
                writer.writerow(parts)
                n += 1
    print(f"{label}.{tier}_sample.csv: {n} / {total} rows retained")
    return n, total


def main(tier="main"):
    id_path = AUDIT_DIR / f"sample_job_ids_{tier}.txt"
    with open(id_path, encoding="utf-8") as f:
        job_ids = set(l.strip() for l in f if l.strip())
    print(f"Loaded {len(job_ids)} sampled job IDs for tier={tier}")

    filter_task_table(job_ids, tier)
    filter_table("pai_instance_table.tar.gz", "pai_instance_table.csv", INSTANCE_FIELDS, job_ids, tier, "instance_table")
    filter_table("pai_sensor_table.tar.gz", "pai_sensor_table.csv", SENSOR_FIELDS, job_ids, tier, "sensor_table")

    # machine_metric is keyed by worker_name (col0), not job_name -- derive the
    # worker_name set from the just-extracted instance_table sample (the
    # parent-entity linkage), not by independently filtering machine_metric
    # on anything of its own.
    worker_names = set()
    with open(PROCESSED_DIR / f"instance_table.{tier}_sample.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            worker_names.add(row["worker_name"])
    print(f"Derived {len(worker_names)} worker_names from instance_table.{tier}_sample.csv")

    out_path = PROCESSED_DIR / f"machine_metric.{tier}_sample.csv"
    n, total = 0, 0
    with open(out_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(MACHINE_METRIC_FIELDS)
        for parts in stream_csv_rows(RAW_DIR / "pai_machine_metric.tar.gz", "pai_machine_metric.csv"):
            total += 1
            if len(parts) == len(MACHINE_METRIC_FIELDS) and parts[0] in worker_names:
                writer.writerow(parts)
                n += 1
    print(f"machine_metric.{tier}_sample.csv: {n} / {total} rows retained")


if __name__ == "__main__":
    tier = sys.argv[1] if len(sys.argv) > 1 else "main"
    main(tier)
