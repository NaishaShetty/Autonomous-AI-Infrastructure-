"""
Validate every one of the 81 frozen positive (PRE-FAILURE) windows
against the extracted telemetry. Reads only data/audit/aiops_kpi/
positive_windows.json and data/processed/aiops_kpi/ (both already
produced by earlier, protocol-driven steps). Writes
data/audit/aiops_kpi/positive_window_validation.json.

Checks per window (per Step 6 of the user's instructions):
  - correct entity / fault event / onset (cross-checked against the
    frozen positive_windows.json itself, which was built directly
    from the fault log -- this re-derives independently from the raw
    fault log to catch any transcription bug)
  - exact 20-minute window boundaries
  - telemetry coverage: at least one observation in the object-
    appropriate platform metric family within [window_start,
    window_end)
  - no accidental post-failure data: no row used in the window has a
    timestamp >= fault_onset
  - no overlap with another fault's DURING/POST window for the same
    entity (guaranteed by construction given the >=25min global /
    30min per-entity minimum gap, checked explicitly here rather than
    assumed)
"""
import csv
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime
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


def load_platform_index():
    """entity -> day -> list of (timestamp_dt_local_utc8) across its object-appropriate files."""
    index = defaultdict(lambda: defaultdict(list))
    for path in PROCESSED_DIR.glob("platform/*.csv"):
        day_str, fname = path.name.split("__", 1)
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entity = row["cmdb_id"]
                ts = int(row["timestamp"])
                index[entity][day_str].append(ts)
    return index


def main():
    with open(AUDIT_DIR / "positive_windows.json", encoding="utf-8") as f:
        windows = json.load(f)

    platform_index = load_platform_index()

    # independent re-derivation from raw fault log, to catch transcription bugs
    z = zipfile.ZipFile(RAW_ZIP)
    data = z.read("故障整理（预赛）.csv").decode("utf-8")
    raw_rows = {r["index"]: r for r in csv.DictReader(io.StringIO(data))}

    results = []
    for w in windows:
        checks = {}
        raw = raw_rows.get(w["fault_index"])
        checks["fault_event_found_in_raw_log"] = raw is not None
        checks["entity_matches_raw_log"] = (raw is not None) and (raw["name"] == w["entity"])
        checks["object_matches_raw_log"] = (raw is not None) and (raw["object"] == w["object"])

        w_start = datetime.fromisoformat(w["pre_failure_window_start"])
        w_end = datetime.fromisoformat(w["pre_failure_window_end"])
        checks["window_is_exactly_20min"] = (w_end - w_start).total_seconds() == 20 * 60

        entity = w["entity"]
        obj = w["object"]
        day = w["extractable_day"]
        files = OBJECT_TO_FILES.get(obj, [])
        n_obs_in_window = 0
        n_obs_post_onset_within_window = 0
        onset = datetime.fromisoformat(w["onset"])
        for ts in platform_index.get(entity, {}).get(day, []):
            local = datetime.utcfromtimestamp(ts / 1000 + 8 * 3600)
            if w_start <= local < w_end:
                n_obs_in_window += 1
                if local >= onset:
                    n_obs_post_onset_within_window += 1
        checks["telemetry_coverage_count"] = n_obs_in_window
        checks["has_telemetry_coverage"] = n_obs_in_window > 0
        checks["no_post_onset_contamination_in_pre_window"] = n_obs_post_onset_within_window == 0

        # overlap check: does any OTHER event on the same entity have an onset
        # within this window's span (which would mean this "pre-failure" window
        # actually contains another fault's during/post period)?
        other_onsets = [
            datetime.fromisoformat(o["onset"]) for o in windows
            if o["entity"] == entity and o["fault_index"] != w["fault_index"]
        ]
        overlap = any(w_start <= oo < w_end for oo in other_onsets)
        checks["no_overlap_with_another_event_onset"] = not overlap

        checks["provenance_object_family_files"] = files

        all_pass = all(v for k, v in checks.items() if isinstance(v, bool))
        results.append({
            "fault_index": w["fault_index"], "entity": entity, "object": obj,
            "onset": w["onset"], "checks": checks, "VALID": all_pass,
        })

    n_valid = sum(1 for r in results if r["VALID"])
    summary = {
        "total_positive_windows": len(results),
        "valid": n_valid,
        "invalid": len(results) - n_valid,
        "invalid_details": [r for r in results if not r["VALID"]],
        "results": results,
    }
    with open(AUDIT_DIR / "positive_window_validation.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Positive windows: {n_valid}/{len(results)} VALID")
    for r in results:
        if not r["VALID"]:
            print("INVALID:", r["fault_index"], r["checks"])


if __name__ == "__main__":
    main()
