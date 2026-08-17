"""
Phase 3 real-data replication -- AIOps telemetry extraction, scoped
EXACTLY to configs/aiops_extraction_protocol_v1.json plus the frozen
positive/negative windows from aiops_build_windows.py.

Reads ONLY data/raw/aiops_kpi/*.zip (never modified). Writes to
data/processed/aiops_kpi/{platform,business,trace_windows}/.

Platform + business metrics: extracted IN FULL for every one of the 15
extractable days (small enough to be fully tractable: ~40MB/day) --
this is the primary evidence family and is kept complete for full
future re-use, not pre-filtered to any window.

Call-traces: stream-filtered to rows whose cmdb_id is one of the 43
fault-eligible entities AND whose timestamp falls inside a KNOWN
window (positive pre/during-failure window, or a sampled negative
window) for that entity on that day. This is a computational-
feasibility decision, not a metric/date exclusion -- the window set
was frozen (aiops_build_windows.py) purely from fault-log timing and
entity IDs, BEFORE any trace content was read, so this filter cannot
have been influenced by what the trace data looks like. Full-file
trace extraction (~1.1GB/day x 14 remaining days =~ 15GB) was assessed
against this and rejected as extracting far more than any frozen
window analysis needs.

Deterministic, no randomness. Every output row keeps source_dataset,
source_file, and original epoch-ms timestamp.
"""
import csv
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ZIP = REPO_ROOT / "data" / "raw" / "aiops_kpi" / "AIOps挑战赛2020预赛数据.zip"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "aiops_kpi"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "aiops_kpi"

PLATFORM_FILES = ["os_linux.csv", "db_oracle_11g.csv", "mw_redis.csv", "dcos_container.csv", "dcos_docker.csv"]
TRACE_FILES = ["trace_csf.csv", "trace_osb.csv", "trace_remote_process.csv", "trace_fly_remote.csv", "trace_jdbc.csv", "trace_local.csv"]

DAY_ZIP_NAMES = {
    "2020-04-11": "2020_04_11", "2020-04-20": "2020_04_20", "2020-04-21": "2020_04_21",
    "2020-04-22": "2020_04_22", "2020-04-23": "2020_04_23",
    "2020-05-22": "2020_05_22", "2020-05-23": "2020_05_23", "2020-05-24": "2020_05_24",
    "2020-05-25": "2020_05_25", "2020-05-26": "2020_05_26", "2020-05-27": "2020_05_27",
    "2020-05-28": "2020_05_28", "2020-05-29": "2020_05_29", "2020-05-30": "2020_05_30",
    "2020-05-31": "2020_05_31",
}


def load_windows():
    """Returns dict: day -> entity -> list of (start_dt, end_dt) intervals to keep."""
    intervals = {}

    with open(AUDIT_DIR / "positive_windows.json", encoding="utf-8") as f:
        pos = json.load(f)
    for p in pos:
        day = p["extractable_day"]
        entity = p["entity"]
        start = datetime.fromisoformat(p["pre_failure_window_start"])
        end = datetime.fromisoformat(p["during_failure_window_end"])  # pre+during, for prediction+diagnosis
        intervals.setdefault(day, {}).setdefault(entity, []).append((start, end))

    with open(AUDIT_DIR / "negative_windows_sampled.json", encoding="utf-8") as f:
        neg = json.load(f)["windows"]
    for n in neg:
        day = n["day"]
        entity = n["entity"]
        start = datetime.fromisoformat(n["window_start"])
        end = datetime.fromisoformat(n["window_end"])
        intervals.setdefault(day, {}).setdefault(entity, []).append((start, end))

    return intervals


def get_day_zip_bytes(day_str):
    inner_name = DAY_ZIP_NAMES[day_str]
    z = zipfile.ZipFile(RAW_ZIP)
    data = z.read(f"AIOps挑战赛数据/{inner_name}.zip")
    return zipfile.ZipFile(io.BytesIO(data)), inner_name


def extract_platform_and_business(day_str, day_zip, inner_name):
    counts = {}
    for fname in PLATFORM_FILES:
        member = f"{inner_name}/平台指标/{fname}"
        try:
            raw = day_zip.read(member).decode("utf-8", errors="replace")
        except KeyError:
            counts[fname] = "MISSING_FROM_ARCHIVE"
            continue
        lines = raw.splitlines()
        out_path = PROCESSED_DIR / "platform" / f"{day_str}__{fname}"
        with open(out_path, "w", newline="", encoding="utf-8") as out_f:
            w = csv.writer(out_f)
            w.writerow(["source_dataset", "source_file", "extraction_day"] + lines[0].split(","))
            for line in lines[1:]:
                if line:
                    w.writerow(["AIOps_2020", member, day_str] + line.split(","))
        counts[fname] = len(lines) - 1

    esb_member = f"{inner_name}/业务指标/esb.csv"
    try:
        raw = day_zip.read(esb_member).decode("utf-8", errors="replace")
        lines = raw.splitlines()
        out_path = PROCESSED_DIR / "business" / f"{day_str}__esb.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as out_f:
            w = csv.writer(out_f)
            w.writerow(["source_dataset", "source_file", "extraction_day"] + lines[0].split(","))
            for line in lines[1:]:
                if line:
                    w.writerow(["AIOps_2020", esb_member, day_str] + line.split(","))
        counts["esb.csv"] = len(lines) - 1
    except KeyError:
        counts["esb.csv"] = "MISSING_FROM_ARCHIVE"

    return counts


def extract_trace_windows(day_str, day_zip, inner_name, day_intervals):
    """Stream each trace file; keep only rows whose cmdb_id is in
    day_intervals and whose startTime (ms) falls within one of that
    entity's known intervals for this day."""
    counts = {}
    for fname in TRACE_FILES:
        member = f"{inner_name}/调用链指标/{fname}"
        out_path = PROCESSED_DIR / "trace_windows" / f"{day_str}__{fname}"
        n_kept, n_total = 0, 0
        try:
            with day_zip.open(member) as f:
                header = f.readline().decode("utf-8").rstrip("\n").split(",")
                cmdb_idx = header.index("cmdb_id")
                start_idx = header.index("startTime")
                with open(out_path, "w", newline="", encoding="utf-8") as out_f:
                    w = csv.writer(out_f)
                    w.writerow(["source_dataset", "source_file", "extraction_day"] + header)
                    for raw_line in f:
                        n_total += 1
                        line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
                        parts = line.split(",")
                        if len(parts) <= max(cmdb_idx, start_idx):
                            continue
                        entity = parts[cmdb_idx]
                        entity_intervals = day_intervals.get(entity)
                        if not entity_intervals:
                            continue
                        try:
                            ts_ms = int(parts[start_idx])
                        except ValueError:
                            continue
                        ts = datetime.utcfromtimestamp(ts_ms / 1000 + 8 * 3600)  # convert to UTC+8 local
                        if any(s <= ts < e for s, e in entity_intervals):
                            w.writerow(["AIOps_2020", member, day_str] + parts)
                            n_kept += 1
        except KeyError:
            counts[fname] = "MISSING_FROM_ARCHIVE"
            continue
        counts[fname] = {"kept": n_kept, "scanned": n_total}
    return counts


def main():
    intervals = load_windows()
    days = sorted(intervals.keys())
    print(f"Windows span {len(days)} days: {days}")

    report = {}
    for day_str in days:
        print(f"\n=== {day_str} ===")
        day_zip, inner_name = get_day_zip_bytes(day_str)
        pb_counts = extract_platform_and_business(day_str, day_zip, inner_name)
        print("platform/business:", pb_counts)
        trace_counts = extract_trace_windows(day_str, day_zip, inner_name, intervals[day_str])
        print("trace (kept/scanned):", trace_counts)
        report[day_str] = {"platform_business": pb_counts, "trace": trace_counts}

    with open(AUDIT_DIR / "extraction_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nExtraction report written to {AUDIT_DIR / 'extraction_report.json'}")


if __name__ == "__main__":
    main()
