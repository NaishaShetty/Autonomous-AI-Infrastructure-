"""ACTIVE Phase 4.2 -- Pattern Type 1 discovery (Alibaba, primary).

Reads ``data/processed/alibaba_gpu2020/task_table.main_sample.csv`` and the
frozen split manifests directly via the same path/hash/split-lookup helpers
``src.failure_experience.sources.real_alibaba`` already defines (imported,
not re-implemented) -- see
``configs/phase4_2_active_pattern_protocol.json``'s ``data_access_decision``
block for why this module does not source population counts through
``src.failure_experience.retrieval`` (FailureExperience only ever stores
the FAILED subset, sampled, by the active Phase 4.1 schema's own design;
Pattern Type 1 needs the full Failed+Terminated+Running population as its
rate denominator, which is structurally outside what FailureExperience
models).

Every function here is pure and takes explicit inputs -- no hidden global
state, no wall-clock, no randomness (the primary path is fully
deterministic; see the protocol's ``seed_usage_note``).
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from src.failure_experience.sources.real_alibaba import (
    DATA_PATH,
    _content_hash,
    _load_split_lookup,
)

from .schema import EvidenceTier, PatternCandidate, AlibabaTestOutcome

PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "configs" / "phase4_2_active_pattern_protocol.json"


def load_protocol(path: Path = PROTOCOL_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def load_population(
    data_path: Path = DATA_PATH,
    split_name: str = "temporal",
) -> list[dict]:
    """Every row (any status) with its (task_name, gpu_type, status,
    split) tuple. ``split_name`` selects which frozen manifest
    (temporal | random_stratified) assigns train/val/test -- see the
    protocol's ``splits`` block. gpu_type empty string is kept literal
    (a real, meaningful 'no GPU allocated' category), never dropped."""
    split_file = {
        "temporal": Path(DATA_PATH).resolve().parents[3] / "data" / "audit" / "alibaba_gpu2020" / "splits_temporal.json",
        "random_stratified": Path(DATA_PATH).resolve().parents[3] / "data" / "audit" / "alibaba_gpu2020" / "splits_random_stratified.json",
    }[split_name]
    lookup = _load_split_lookup(split_file)

    rows = []
    with open(data_path, newline="") as f:
        for row in csv.DictReader(f):
            split = lookup.get(row["job_name"], "unknown")
            rows.append({
                "task_name": row["task_name"],
                "gpu_type": row.get("gpu_type") or "",
                "status": row["status"],
                "split": split,
            })
    return rows


def _baseline_rate(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return sum(1 for r in rows if r["status"] == "Failed") / len(rows)


def _context_counts(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """key -> {"n": int, "n_failed": int}"""
    out: dict[tuple[str, str], dict] = defaultdict(lambda: {"n": 0, "n_failed": 0})
    for r in rows:
        key = (r["task_name"], r["gpu_type"])
        out[key]["n"] += 1
        if r["status"] == "Failed":
            out[key]["n_failed"] += 1
    return dict(out)


def discover(rows: list[dict], protocol: dict) -> dict[tuple[str, str], dict]:
    """TRAIN-only. Returns key -> {"n_train", "train_rate", "train_baseline_rate",
    "provisional_tier"}. Never reads validation or test rows -- caller must
    filter ``rows`` to split=='train' before calling this."""
    assert all(r["split"] == "train" for r in rows), "discover() must only receive train-split rows"
    thresholds = protocol["minimum_evidence_thresholds"]
    margin_cfg = protocol["rate_elevation_criterion"]
    n_min_candidate = thresholds["N_MIN_CANDIDATE"]
    n_min_trusted = thresholds["N_MIN_TRUSTED"]
    margin_train = margin_cfg["MARGIN_TRAIN"]

    baseline = _baseline_rate(rows)
    counts = _context_counts(rows)

    out = {}
    for key, c in counts.items():
        n = c["n"]
        if n < n_min_candidate:
            continue  # not a candidate at all (precedence rule 1)
        rate = c["n_failed"] / n
        if n < n_min_trusted:
            tier = EvidenceTier.UNCERTAIN
        elif (rate - baseline) >= margin_train:
            tier = EvidenceTier.INFERRED  # may be upgraded to CONFIRMED by confirm()
        else:
            tier = EvidenceTier.OBSERVED
        out[key] = {
            "n_train": n,
            "train_rate": rate,
            "train_baseline_rate": baseline,
            "provisional_tier": tier,
        }
    return out


def confirm(discovered: dict[tuple[str, str], dict], validation_rows: list[dict], protocol: dict) -> dict[tuple[str, str], dict]:
    """VALIDATION-only. Upgrades INFERRED candidates to CONFIRMED where
    the elevation independently replicates on validation-split occurrences
    of the identical key. Never reads test rows. Returns a new dict (does
    not mutate ``discovered``)."""
    assert all(r["split"] == "val" for r in validation_rows), "confirm() must only receive validation-split rows"
    thresholds = protocol["rate_elevation_criterion"]
    n_min_validation = thresholds["N_MIN_VALIDATION"]
    margin_validation = thresholds["MARGIN_VALIDATION"]

    val_baseline = _baseline_rate(validation_rows)
    val_counts = _context_counts(validation_rows)

    out = {}
    for key, cand in discovered.items():
        cand = dict(cand)
        vc = val_counts.get(key)
        n_validation = vc["n"] if vc else 0
        validation_rate = (vc["n_failed"] / vc["n"]) if vc and vc["n"] > 0 else None
        cand["n_validation"] = n_validation
        cand["validation_rate"] = validation_rate
        cand["validation_baseline_rate"] = val_baseline

        tier = cand["provisional_tier"]
        if (
            tier == EvidenceTier.INFERRED
            and n_validation >= n_min_validation
            and validation_rate is not None
            and val_baseline is not None
            and (validation_rate - val_baseline) >= margin_validation
        ):
            tier = EvidenceTier.CONFIRMED
        cand["tier"] = tier
        del cand["provisional_tier"]
        out[key] = cand
    return out


def to_candidates(
    confirmed: dict[tuple[str, str], dict],
    protocol_version: str,
    dataset_content_hash: str,
    split_name: str,
) -> list[PatternCandidate]:
    return [
        PatternCandidate(
            task_name=k[0],
            gpu_type=k[1],
            n_train=v["n_train"],
            train_rate=v["train_rate"],
            train_baseline_rate=v["train_baseline_rate"],
            n_validation=v.get("n_validation", 0),
            validation_rate=v.get("validation_rate"),
            validation_baseline_rate=v.get("validation_baseline_rate"),
            tier=v["tier"],
            protocol_version=protocol_version,
            dataset_content_hash=dataset_content_hash,
            split_name=split_name,
        )
        for k, v in confirmed.items()
    ]


def evaluate_test(
    candidates: list[PatternCandidate],
    test_rows: list[dict],
    protocol: dict,
) -> dict[tuple[str, str], AlibabaTestOutcome]:
    """TEST split, touched exactly once by the caller (this function
    itself is pure/re-runnable, but the frozen protocol's discipline is
    that the caller invokes it only once per experiment run and does not
    use its output to revise any candidate/threshold decision)."""
    assert all(r["split"] == "test" for r in test_rows), "evaluate_test() must only receive test-split rows"
    test_baseline = _baseline_rate(test_rows)
    test_counts = _context_counts(test_rows)
    n_min_candidate = protocol["minimum_evidence_thresholds"]["N_MIN_CANDIDATE"]

    out = {}
    for cand in candidates:
        key = (cand.task_name, cand.gpu_type)
        tc = test_counts.get(key)
        n_test = tc["n"] if tc else 0
        if n_test < n_min_candidate:
            out[key] = AlibabaTestOutcome(
                task_name=cand.task_name, gpu_type=cand.gpu_type,
                n_test=n_test, test_rate=None, test_baseline_rate=test_baseline,
            )
            continue
        test_rate = tc["n_failed"] / n_test
        out[key] = AlibabaTestOutcome(
            task_name=cand.task_name, gpu_type=cand.gpu_type,
            n_test=n_test, test_rate=test_rate, test_baseline_rate=test_baseline,
        )
    return out


def all_test_candidates(test_rows: list[dict], protocol: dict) -> dict[tuple[str, str], AlibabaTestOutcome]:
    """Every (task_name, gpu_type) context present in the test split with
    n_test >= N_MIN_CANDIDATE -- the full 'evaluable' population recall is
    computed against, independent of whether train discovery flagged it."""
    n_min_candidate = protocol["minimum_evidence_thresholds"]["N_MIN_CANDIDATE"]
    test_baseline = _baseline_rate(test_rows)
    test_counts = _context_counts(test_rows)
    out = {}
    for key, c in test_counts.items():
        if c["n"] < n_min_candidate:
            continue
        out[key] = AlibabaTestOutcome(
            task_name=key[0], gpu_type=key[1],
            n_test=c["n"], test_rate=c["n_failed"] / c["n"], test_baseline_rate=test_baseline,
        )
    return out


def dataset_content_hash() -> str:
    return _content_hash(DATA_PATH)
