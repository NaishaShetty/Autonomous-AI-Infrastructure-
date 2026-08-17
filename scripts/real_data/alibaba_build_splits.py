"""
Phase 3 real-data replication -- leakage-safe splits for the Alibaba
GPU2020 "main" sample tier (10,000 jobs, see
data/audit/alibaba_gpu2020/sample_job_ids_main.txt).

Two split protocols are built, for two different generalization
questions -- NOT one split forced to serve both:

1. JOB-DISJOINT RANDOM-STRATIFIED SPLIT (for in-distribution
   evaluation, mirrors original Phase 3.1/3.2/3.4 usage): 70/15/15
   train/val/test, stratified on (outcome_status, dominant_gpu_type)
   so class balance and workload mix are preserved in every split.
   Jobs never repeat across splits (the sampling unit already
   guarantees this trivially, but composite child rows -- tasks,
   instances -- inherit their parent job's split assignment, so a
   job's tasks/instances never spread across splits either).

2. TEMPORAL (relative-time) SPLIT (for the "unseen time period"
   generalization test, Section 6/13 of the brief): train = jobs in
   relative-time quartiles Q1-Q3, test = jobs in Q4 (strict future
   holdout by relative start_time), val = a random 15% carved from the
   Q1-Q3 train pool (not from Q4, to avoid leaking the held-out future
   window into model selection). Quartile boundaries were fixed during
   sampling (data/audit/alibaba_gpu2020/sampling_frame.json), before
   this split was built.

What this does NOT attempt: a machine-disjoint split. Alibaba jobs
have a many-to-many relationship with machines (a single job's
instances commonly span multiple machines, and a machine hosts many
jobs), so a clean job-disjoint split is not automatically
machine-disjoint, and forcing one without dropping a nontrivial
fraction of jobs is a real graph-partitioning problem, not a
one-line filter. NOT built in this pass -- documented as a limitation,
not silently skipped (see the cleaning report).

Outputs (data/audit/alibaba_gpu2020/):
  splits_random_stratified.json  -- {train,val,test}: [job_name, ...]
  splits_temporal.json           -- {train,val,test}: [job_name, ...]
  splits_report.json             -- construction parameters, counts,
                                     class balance per split (for both
                                     protocols)

Deterministic: SEED=42, matching the sampling script.
"""
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "alibaba_gpu2020"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "alibaba_gpu2020"

SEED = 42
TIER = "main"
RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


def load_main_sample_jobs():
    with open(AUDIT_DIR / f"sample_job_ids_{TIER}.txt", encoding="utf-8") as f:
        ids = set(l.strip() for l in f if l.strip())
    jobs = {}
    with open(PROCESSED_DIR / "job_table.clean.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["job_name"] in ids:
                jobs[row["job_name"]] = {"status": row["status"], "start_time": float(row["start_time"])}
    assert len(jobs) == len(ids), f"mismatch: {len(jobs)} vs {len(ids)}"
    return jobs


def load_dominant_gpu_type():
    with open(AUDIT_DIR / "sampling_report.json", encoding="utf-8") as f:
        pass  # allocation keys encode (status|gpu|quartile) but not per-job -- recompute from task_table sample instead
    dominant = {}
    counts = defaultdict(lambda: defaultdict(int))
    with open(PROCESSED_DIR / f"task_table.{TIER}_sample.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gt = row["gpu_type"] or "UNSPECIFIED"
            counts[row["job_name"]][gt] += 1
    for jn, c in counts.items():
        m = max(c.values())
        top = sorted(k for k, v in c.items() if v == m)
        dominant[jn] = top[0] if len(top) == 1 else "MIXED"
    return dominant


def stratified_split(jobs, dominant_gpu):
    strata = defaultdict(list)
    for jn in sorted(jobs.keys()):
        strata[(jobs[jn]["status"], dominant_gpu.get(jn, "UNSPECIFIED"))].append(jn)

    rng = random.Random(SEED)
    out = {"train": [], "val": [], "test": []}
    for key, members in strata.items():
        members = sorted(members)
        rng.shuffle(members)
        n = len(members)
        n_train = int(round(n * RATIOS["train"]))
        n_val = int(round(n * RATIOS["val"]))
        out["train"].extend(members[:n_train])
        out["val"].extend(members[n_train:n_train + n_val])
        out["test"].extend(members[n_train + n_val:])
    for k in out:
        out[k] = sorted(out[k])
    return out


def temporal_split(jobs):
    times = sorted(v["start_time"] for v in jobs.values())
    n = len(times)
    q1 = times[int(n * 0.25)]
    q2 = times[int(n * 0.50)]
    q3 = times[int(n * 0.75)]

    pre_q4 = [jn for jn, v in jobs.items() if v["start_time"] <= q3]
    q4 = [jn for jn, v in jobs.items() if v["start_time"] > q3]

    rng = random.Random(SEED)
    pre_q4_sorted = sorted(pre_q4)
    rng.shuffle(pre_q4_sorted)
    n_val = int(round(len(pre_q4_sorted) * (RATIOS["val"] / (RATIOS["train"] + RATIOS["val"]))))
    val = pre_q4_sorted[:n_val]
    train = pre_q4_sorted[n_val:]

    return {"train": sorted(train), "val": sorted(val), "test": sorted(q4)}, {
        "q1_boundary": q1, "q2_boundary": q2, "q3_boundary": q3,
    }


def class_balance(job_list, jobs):
    failed = sum(1 for j in job_list if jobs[j]["status"] == "Failed")
    return {"n": len(job_list), "n_failed": failed, "failed_rate": failed / len(job_list) if job_list else None}


def main():
    jobs = load_main_sample_jobs()
    dominant_gpu = load_dominant_gpu_type()

    rs_split = stratified_split(jobs, dominant_gpu)
    with open(AUDIT_DIR / "splits_random_stratified.json", "w", encoding="utf-8") as f:
        json.dump(rs_split, f, indent=2)

    t_split, t_boundaries = temporal_split(jobs)
    with open(AUDIT_DIR / "splits_temporal.json", "w", encoding="utf-8") as f:
        json.dump(t_split, f, indent=2)

    report = {
        "seed": SEED,
        "source_tier": TIER,
        "random_stratified": {
            "ratios": RATIOS,
            "stratified_on": ["outcome_status", "dominant_gpu_type"],
            "counts": {k: class_balance(v, jobs) for k, v in rs_split.items()},
        },
        "temporal": {
            "definition": "train/val drawn from relative-time Q1-Q3 (val is a random 15% carve-out of that pool); test = strict future holdout Q4",
            "quartile_boundaries_relative_seconds": t_boundaries,
            "counts": {k: class_balance(v, jobs) for k, v in t_split.items()},
        },
        "not_built_this_pass": "machine-disjoint split -- jobs have a many-to-many relationship with machines; deferred, see script docstring",
    }
    with open(AUDIT_DIR / "splits_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
