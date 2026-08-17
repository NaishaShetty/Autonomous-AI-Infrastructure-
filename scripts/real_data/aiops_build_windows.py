"""
Phase 3 real-data replication -- AIOps positive/negative window
construction. Pure date/entity/timestamp arithmetic; reads ONLY the
fault log (from data/raw/aiops_kpi/*.zip, read-only) and the entity
roster (from data/intermediate/aiops_kpi/data_release_v3.5/, already
extracted read-only in an earlier pass). Touches NO telemetry data --
this script runs and its output is frozen BEFORE any telemetry beyond
2020_04_11 is extracted, per
docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md.

Outputs (data/audit/aiops_kpi/):
  positive_windows.json                    -- one row per fault event
  negative_window_natural_population.json  -- full eligible-grid count
  negative_windows_sampled.json            -- the frozen, capped, seeded sample
"""
import json
import random
import zipfile
import csv
import io
import openpyxl
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ZIP = REPO_ROOT / "data" / "raw" / "aiops_kpi" / "AIOps挑战赛2020预赛数据.zip"
ARCH_XLSX = REPO_ROOT / "data" / "intermediate" / "aiops_kpi" / "data_release_v3.5" / "1应用部署架构清单.xlsx"
AUDIT_DIR = REPO_ROOT / "data" / "audit" / "aiops_kpi"

SEED = 42
PRE_FAILURE_MIN = 20
DURING_FAILURE_MIN = 5
NEGATIVE_EXCLUSION_MIN = 60
PER_ENTITY_CAP = 20

EXTRACTABLE_DAYS = [
    "2020-04-11", "2020-04-20", "2020-04-21", "2020-04-22", "2020-04-23",
    "2020-05-22", "2020-05-23", "2020-05-24", "2020-05-25", "2020-05-26",
    "2020-05-27", "2020-05-28", "2020-05-29", "2020-05-30", "2020-05-31",
]


def load_fault_events():
    z = zipfile.ZipFile(RAW_ZIP)
    data = z.read("故障整理（预赛）.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(data)))
    events = []
    for r in rows:
        onset_str = r["start_time"] if r["start_time"] else r["log_time"]
        onset_rule = "start_time" if r["start_time"] else "log_time"
        onset = datetime.strptime(onset_str, "%Y/%m/%d %H:%M")
        events.append({
            "index": r["index"], "name": r["name"], "object": r["object"],
            "fault_desrcibtion": r["fault_desrcibtion"],
            "onset": onset, "onset_rule": onset_rule,
        })
    return events


def load_fault_eligible_entities():
    wb = openpyxl.load_workbook(ARCH_XLSX, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(values_only=True))
    names = [r[3] for r in rows[1:] if r[3]]
    eligible = [n for n in names if n.split("_")[0] in ("docker", "db", "os")]
    return sorted(eligible)


def build_positive_windows(events):
    out = []
    for e in events:
        w_start = e["onset"] - timedelta(minutes=PRE_FAILURE_MIN)
        w_end = e["onset"]
        during_end = e["onset"] + timedelta(minutes=DURING_FAILURE_MIN)
        out.append({
            "fault_index": e["index"],
            "entity": e["name"],
            "object": e["object"],
            "fault_desrcibtion": e["fault_desrcibtion"],
            "onset": e["onset"].isoformat(),
            "onset_rule": e["onset_rule"],
            "pre_failure_window_start": w_start.isoformat(),
            "pre_failure_window_end": w_end.isoformat(),
            "during_failure_window_end": during_end.isoformat(),
            "extractable_day": e["onset"].date().isoformat(),
            "day_is_extractable": e["onset"].date().isoformat() in EXTRACTABLE_DAYS,
        })
    return out


def build_negative_grid(entities, events):
    """For each entity, each extractable day, 72 fixed 20-min blocks;
    a block is eligible unless within NEGATIVE_EXCLUSION_MIN of that
    entity's OWN fault onset."""
    onsets_by_entity = defaultdict(list)
    for e in events:
        onsets_by_entity[e["name"]].append(e["onset"])

    natural_population = []
    for day_str in EXTRACTABLE_DAYS:
        day = datetime.strptime(day_str, "%Y-%m-%d")
        blocks = [day + timedelta(minutes=20 * i) for i in range(72)]
        for entity in entities:
            entity_onsets = onsets_by_entity.get(entity, [])
            for b_start in blocks:
                b_end = b_start + timedelta(minutes=PRE_FAILURE_MIN)
                excluded = any(
                    (b_start - timedelta(minutes=NEGATIVE_EXCLUSION_MIN)) <= onset <=
                    (b_end + timedelta(minutes=NEGATIVE_EXCLUSION_MIN))
                    for onset in entity_onsets
                )
                if not excluded:
                    natural_population.append({
                        "entity": entity, "day": day_str,
                        "window_start": b_start.isoformat(),
                        "window_end": b_end.isoformat(),
                    })
    return natural_population


def sample_negative_pool(natural_population):
    by_entity = defaultdict(list)
    for cand in natural_population:
        by_entity[cand["entity"]].append(cand)

    sampled = []
    for entity in sorted(by_entity.keys()):
        candidates = sorted(by_entity[entity], key=lambda c: (c["day"], c["window_start"]))
        rng = random.Random(SEED)
        n_take = min(PER_ENTITY_CAP, len(candidates))
        chosen = rng.sample(candidates, n_take)
        chosen_sorted = sorted(chosen, key=lambda c: (c["day"], c["window_start"]))
        sampled.extend(chosen_sorted)
    return sampled


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    events = load_fault_events()
    entities = load_fault_eligible_entities()
    print(f"Loaded {len(events)} fault events, {len(entities)} fault-eligible entities")

    pos_windows = build_positive_windows(events)
    with open(AUDIT_DIR / "positive_windows.json", "w", encoding="utf-8") as f:
        json.dump(pos_windows, f, indent=2)
    n_extractable = sum(1 for p in pos_windows if p["day_is_extractable"])
    print(f"Positive windows: {len(pos_windows)} total, {n_extractable} on extractable days")

    natural_pop = build_negative_grid(entities, events)
    with open(AUDIT_DIR / "negative_window_natural_population.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_candidate_blocks": len(natural_pop),
            "entities": len(entities),
            "days": len(EXTRACTABLE_DAYS),
            "note": "72 blocks/entity/day minus per-entity fault-exclusion; this is the FULL eligible population, not the extracted/sampled pool",
            "candidates": natural_pop,
        }, f, indent=2)
    print(f"Negative natural population: {len(natural_pop)} eligible candidate blocks")

    sampled = sample_negative_pool(natural_pop)
    with open(AUDIT_DIR / "negative_windows_sampled.json", "w", encoding="utf-8") as f:
        json.dump({
            "seed": SEED, "per_entity_cap": PER_ENTITY_CAP,
            "total_sampled": len(sampled),
            "windows": sampled,
        }, f, indent=2)
    print(f"Negative sampled pool: {len(sampled)} windows (cap={PER_ENTITY_CAP}/entity)")


if __name__ == "__main__":
    main()
