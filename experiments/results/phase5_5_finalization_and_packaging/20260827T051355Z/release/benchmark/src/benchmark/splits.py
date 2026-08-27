"""Split inheritance: copy dataset split_assignment; never re-assign."""
from __future__ import annotations

from collections import defaultdict

from .constants import EVALUATION_SPLIT, FITTING_SPLITS


def records_for_split(records: list[dict], split: str) -> list[dict]:
    selected = [r for r in records if r.get("split_assignment") == split]
    selected.sort(key=lambda r: r["identity"]["record_id"])
    return selected


def split_counts(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in records:
        counts[str(r.get("split_assignment"))] += 1
    return dict(sorted(counts.items()))


def assert_no_test_in_fit_population(records: list[dict]) -> None:
    for r in records:
        if r.get("split_assignment") == EVALUATION_SPLIT:
            raise ValueError(
                f"test-split record {r['identity']['record_id']} used in a fitting population"
            )


def fitting_records(records: list[dict]) -> list[dict]:
    selected = [r for r in records if r.get("split_assignment") in FITTING_SPLITS]
    # Thresholds/policies fit on calibration_validation only (split policy §3).
    selected = [r for r in selected if r.get("split_assignment") == "calibration_validation"]
    selected.sort(key=lambda r: r["identity"]["record_id"])
    return selected


def test_records(records: list[dict]) -> list[dict]:
    return records_for_split(records, EVALUATION_SPLIT)


def inherit_split(record: dict) -> str:
    return str(record["split_assignment"])
