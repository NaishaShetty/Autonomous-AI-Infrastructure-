"""
Phase 3 real-data replication — Alibaba GPU2020 stratified job-level
sampling protocol. Reads ONLY the cleaned tables produced by
clean_alibaba_job_task.py (data/processed/alibaba_gpu2020/); never
touches data/raw/.

Sampling unit: JOB (job_name). Population, strata, allocation, and
sample sizes are all fixed BEFORE any Phase 3.1-3.6 evaluation is run
-- this script contains no reference to, and was not tuned against,
any evaluation metric.

Population (eligibility criteria):
  - status in {Terminated, Failed}  (excludes Running/Waiting: these
    are right-censored -- outcome not yet known at trace cutoff -- and
    are NOT eligible for a binary failure/success label; see
    docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md and the
    feasibility audit for the censoring rationale).

Strata:
  1. outcome: {Terminated, Failed} -- the target itself; proportional
     allocation preserves the real-world 25.94% Failed base rate
     rather than artificially rebalancing it (artificial rebalancing
     would misrepresent real operating conditions and was explicitly
     not authorized).
  2. dominant_gpu_type: the modal gpu_type across a job's tasks (from
     the cleaned task_table), one of {MISC, T4, P100, V100, V100M32,
     UNSPECIFIED (no gpu_type recorded on any task), MIXED (tie
     between >1 non-empty types)}. Chosen because gpu_type is exactly
     the kind of workload/resource-class variable the brief calls out
     as a candidate stratum, and it is well-populated (unlike
     `workload` in group_tag_table, tagged on only ~9% of instances
     per the official docs -- too sparse to stratify on reliably).
  3. relative_time_quartile: quartile (Q1-Q4) of the job's start_time
     within the full observed range -- chosen to give the later
     temporal/"unseen time period" split (Step 9) balanced material to
     work with in every quartile, given Alibaba has no absolute
     calendar time (see schema dictionary).

Sample-size tiers (from data/audit/alibaba_gpu2020/power_analysis.json,
frozen BEFORE this script ran):
  - pilot:      2,000 jobs  (pipeline verification only)
  - main:      10,000 jobs  (exceeds the ~8,100 needed to detect a
               0.03 AUROC difference at power=0.80, alpha=0.05, under
               the conservative independent-samples bound; also gives
               ~0.02 AUROC estimation precision)
  - robustness: 50,000 jobs (for 3.5-style generalization/robustness
               work and finer per-stratum subgroup analysis)

Allocation within each tier: proportional to each stratum's share of
the eligible population (Neyman/proportional allocation), not
equal-per-stratum -- equal allocation would over-represent rare
gpu_types relative to their real prevalence.

Selection algorithm: deterministic. Within each stratum, job_names are
sorted lexicographically (removing any dependency on file/iteration
order), then a seeded random.Random(SEED).sample() draws the required
count. SEED=42, matching this repo's existing convention (see
benchmarks/run_baselines.py).

Outputs (data/audit/alibaba_gpu2020/):
  - sampling_frame.json: population/strata sizes before sampling
  - sample_job_ids_pilot.txt / _main.txt / _robustness.txt: one
    job_name per line, the exact reproducible sample for that tier
  - sampling_report.json: full protocol record (strata definitions,
    allocation, seed, resulting counts) per Step 8's requirements
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
TIERS = {"pilot": 2000, "main": 10000, "robustness": 50000}
GPU_TYPES = {"MISC", "T4", "P100", "V100", "V100M32"}


def load_job_table():
    jobs = {}
    with open(PROCESSED_DIR / "job_table.clean.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] in ("Terminated", "Failed"):
                jobs[row["job_name"]] = {
                    "status": row["status"],
                    "start_time": float(row["start_time"]),
                }
    return jobs


def compute_dominant_gpu_type(job_names):
    """One pass over the (larger) task_table to get each eligible job's
    modal gpu_type, without loading task_table fully into memory
    beyond a per-job counter."""
    counts = defaultdict(lambda: defaultdict(int))
    with open(PROCESSED_DIR / "task_table.clean.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            jn = row["job_name"]
            if jn in job_names:
                gt = row["gpu_type"] if row["gpu_type"] in GPU_TYPES else ("UNSPECIFIED" if row["gpu_type"] == "" else "OTHER")
                counts[jn][gt] += 1

    dominant = {}
    for jn in job_names:
        c = counts.get(jn)
        if not c:
            dominant[jn] = "UNSPECIFIED"
            continue
        max_count = max(c.values())
        top = [k for k, v in c.items() if v == max_count]
        dominant[jn] = top[0] if len(top) == 1 else "MIXED"
    return dominant


def assign_relative_time_quartile(jobs):
    times = sorted(v["start_time"] for v in jobs.values())
    n = len(times)
    q1 = times[int(n * 0.25)]
    q2 = times[int(n * 0.50)]
    q3 = times[int(n * 0.75)]
    out = {}
    for jn, v in jobs.items():
        t = v["start_time"]
        if t <= q1:
            out[jn] = "Q1"
        elif t <= q2:
            out[jn] = "Q2"
        elif t <= q3:
            out[jn] = "Q3"
        else:
            out[jn] = "Q4"
    return out, {"q1_boundary": q1, "q2_boundary": q2, "q3_boundary": q3}


def main():
    jobs = load_job_table()
    job_names = set(jobs.keys())
    print(f"Eligible population (Terminated+Failed): {len(job_names)}")

    dominant_gpu = compute_dominant_gpu_type(job_names)
    time_quartile, quartile_boundaries = assign_relative_time_quartile(jobs)

    strata = defaultdict(list)
    for jn in sorted(job_names):  # sort first for full determinism
        key = (jobs[jn]["status"], dominant_gpu[jn], time_quartile[jn])
        strata[key].append(jn)

    population_size = len(job_names)
    strata_sizes = {"|".join(k): len(v) for k, v in strata.items()}

    sampling_frame = {
        "sampling_unit": "job (job_name)",
        "eligibility_criteria": "status in {Terminated, Failed} (Running/Waiting excluded as right-censored)",
        "population_size": population_size,
        "strata_definition": ["outcome_status", "dominant_gpu_type", "relative_time_quartile"],
        "quartile_boundaries_relative_seconds": quartile_boundaries,
        "num_strata": len(strata),
        "strata_sizes": strata_sizes,
    }
    with open(AUDIT_DIR / "sampling_frame.json", "w", encoding="utf-8") as f:
        json.dump(sampling_frame, f, indent=2)

    report = {
        "seed": SEED,
        "selection_algorithm": "per-stratum lexicographic sort of job_name, then random.Random(seed).sample()",
        "allocation": "proportional to stratum share of eligible population",
        "tiers": {},
    }

    for tier_name, tier_n in TIERS.items():
        rng = random.Random(SEED)
        selected = []
        tier_alloc = {}
        # Largest-remainder proportional allocation for determinism/exactness.
        raw_alloc = {k: (len(v) / population_size) * tier_n for k, v in strata.items()}
        floor_alloc = {k: int(raw_alloc[k]) for k in strata}
        remainder = tier_n - sum(floor_alloc.values())
        remainders_sorted = sorted(strata.keys(), key=lambda k: (-(raw_alloc[k] - floor_alloc[k]), k))
        for k in remainders_sorted[:remainder]:
            floor_alloc[k] += 1

        for k, members in strata.items():
            n_take = min(floor_alloc[k], len(members))
            chosen = rng.sample(sorted(members), n_take) if n_take > 0 else []
            selected.extend(chosen)
            tier_alloc["|".join(k)] = {"target": floor_alloc[k], "available": len(members), "selected": len(chosen)}

        selected_sorted = sorted(selected)
        out_path = AUDIT_DIR / f"sample_job_ids_{tier_name}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(selected_sorted) + "\n")

        report["tiers"][tier_name] = {
            "target_n": tier_n,
            "actual_n": len(selected_sorted),
            "output_file": str(out_path.relative_to(REPO_ROOT)),
            "strata_allocation": tier_alloc,
        }
        print(f"tier={tier_name} target={tier_n} actual={len(selected_sorted)} -> {out_path.name}")

    with open(AUDIT_DIR / "sampling_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSampling report written to {AUDIT_DIR / 'sampling_report.json'}")


if __name__ == "__main__":
    main()
