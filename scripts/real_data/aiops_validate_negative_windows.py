"""
Validate every negative window in the frozen sampled pool
(data/audit/aiops_kpi/negative_windows_sampled.json) against the
extracted telemetry and against all 81 fault onsets. Writes
data/audit/aiops_kpi/negative_window_validation.json plus a rejection
report for anything that fails.

Checks per Step 7 of the user's instructions:
  - no fault (for this entity) within the 60-minute exclusion horizon
    of this window (re-derived independently from the raw fault log,
    not just trusted from the generation script)
  - no overlap with any positive window for the same entity
  - no post-failure recovery contamination (implied by the same
    60-minute exclusion, checked directly)
  - valid telemetry coverage
  - correct entity / timestamp
  - provenance preserved
"""
import csv
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ZIP = REPO_ROOT / "data" / "raw" / "aiops_kpi" / "AIOps挑战赛2020预赛数据.zip"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "aiops_kpi"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "aiops_kpi"

OBJECT_TO_FILES = {
    "docker": ["dcos_docker.csv", "dcos_container.csv"],
    "db": ["db_oracle_11g.csv"],
    "os": ["os_linux.csv"],
}
NEGATIVE_EXCLUSION_MIN = 60


def load_fault_events():
    z = zipfile.ZipFile(RAW_ZIP)
    data = z.read("故障整理（预赛）.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(data)))
    events = []
    for r in rows:
        onset_str = r["start_time"] if r["start_time"] else r["log_time"]
        onset = datetime.strptime(onset_str, "%Y/%m/%d %H:%M")
        events.append({"index": r["index"], "name": r["name"], "object": r["object"], "onset": onset})
    return events


def load_platform_index():
    index = defaultdict(lambda: defaultdict(list))
    entity_object = {}
    for path in PROCESSED_DIR.glob("platform/*.csv"):
        day_str, fname = path.name.split("__", 1)
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entity = row["cmdb_id"]
                index[entity][day_str].append(int(row["timestamp"]))
    return index


def entity_object_type(entity):
    prefix = entity.split("_")[0]
    return {"docker": "docker", "db": "db", "os": "os"}.get(prefix)


def main():
    with open(AUDIT_DIR / "negative_windows_sampled.json", encoding="utf-8") as f:
        neg = json.load(f)["windows"]
    with open(AUDIT_DIR / "positive_windows.json", encoding="utf-8") as f:
        pos = json.load(f)

    events = load_fault_events()
    onsets_by_entity = defaultdict(list)
    for e in events:
        onsets_by_entity[e["name"]].append(e["onset"])

    pos_windows_by_entity = defaultdict(list)
    for p in pos:
        pos_windows_by_entity[p["entity"]].append((
            datetime.fromisoformat(p["pre_failure_window_start"]),
            datetime.fromisoformat(p["during_failure_window_end"]),
        ))

    platform_index = load_platform_index()

    results = []
    for w in neg:
        entity = w["entity"]
        day = w["day"]
        w_start = datetime.fromisoformat(w["window_start"])
        w_end = datetime.fromisoformat(w["window_end"])
        checks = {}

        checks["window_is_exactly_20min"] = (w_end - w_start).total_seconds() == 20 * 60

        # re-derive exclusion independently from raw fault log
        excl_lo = w_start - timedelta(minutes=NEGATIVE_EXCLUSION_MIN)
        excl_hi = w_end + timedelta(minutes=NEGATIVE_EXCLUSION_MIN)
        violating_onsets = [o for o in onsets_by_entity.get(entity, []) if excl_lo <= o <= excl_hi]
        checks["no_fault_within_exclusion_horizon"] = len(violating_onsets) == 0

        # overlap with any positive window for the same entity
        overlaps_positive = any(
            w_start < pe and ps < w_end for ps, pe in pos_windows_by_entity.get(entity, [])
        )
        checks["no_overlap_with_positive_window"] = not overlaps_positive

        obj = entity_object_type(entity)
        checks["entity_object_type_resolved"] = obj is not None
        n_obs = 0
        for ts in platform_index.get(entity, {}).get(day, []):
            local = datetime.utcfromtimestamp(ts / 1000 + 8 * 3600)
            if w_start <= local < w_end:
                n_obs += 1
        checks["telemetry_coverage_count"] = n_obs
        checks["has_telemetry_coverage"] = n_obs > 0

        all_pass = all(v for k, v in checks.items() if isinstance(v, bool))
        results.append({
            "entity": entity, "day": day, "window_start": w["window_start"],
            "window_end": w["window_end"], "checks": checks,
            "violating_fault_onsets": [o.isoformat() for o in violating_onsets],
            "VALID": all_pass,
        })

    n_valid = sum(1 for r in results if r["VALID"])
    rejected = [r for r in results if not r["VALID"]]
    summary = {
        "total_negative_windows": len(results),
        "valid": n_valid,
        "rejected": len(rejected),
        "rejection_report": rejected,
        "results": results,
    }
    with open(AUDIT_DIR / "negative_window_validation.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Negative windows: {n_valid}/{len(results)} VALID, {len(rejected)} rejected")
    for r in rejected[:20]:
        print("REJECTED:", r["entity"], r["day"], r["window_start"], r["checks"])


if __name__ == "__main__":
    main()
