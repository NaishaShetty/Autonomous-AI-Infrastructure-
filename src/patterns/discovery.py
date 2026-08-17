"""Phase 4.2: pattern discovery, tier calibration, and the two secondary
pattern analyses (temporal clustering, cause->outcome), per
configs/phase4_2_pattern_protocol.json.

Discovery/calibration use condition_id (Phase 4.0 ground truth) directly
-- explicitly permitted for training/validation use
(docs/PHASE4_PLAN.md section 3). ``PatternQuery`` (src/patterns/schema.py)
is the only type used when APPLYING an already-discovered candidate's
tier to a new incident, and it structurally excludes condition_id.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Optional

from .schema import EvidenceTier, PatternCandidate


def _key(record: dict) -> tuple:
    return (record["workload_id"], record["diagnosed_cause"])


def _critical_failures(records: list[dict], split: Optional[str] = None) -> list[dict]:
    out = [r for r in records if r["is_failure"] and r["diagnosed_cause"] is not None]
    if split is not None:
        out = [r for r in out if r["split"] == split]
    return out


def discover_candidates(
    train_records: list[dict],
    validation_records: list[dict],
    thresholds: dict,
    protocol_version: str,
    dataset_content_hash: str,
) -> list[PatternCandidate]:
    """Builds one PatternCandidate per (workload_id, diagnosed_cause) key
    with n_train >= 2, using ONLY train_records for discovery and
    validation_records for the CONFIRMED-tier replication check (both
    uses explicitly permitted -- see module docstring). Never touches a
    test-split record."""
    by_key_train: dict[tuple, list[dict]] = defaultdict(list)
    for r in _critical_failures(train_records):
        by_key_train[_key(r)].append(r)

    by_key_val: dict[tuple, list[dict]] = defaultdict(list)
    for r in _critical_failures(validation_records):
        by_key_val[_key(r)].append(r)

    candidates = []
    for key, rows in sorted(by_key_train.items()):
        n_train = len(rows)
        if n_train < 2:
            continue  # not a candidate at all -- see candidacy_rule
        workload_id, diagnosed_cause = key
        condition_counts = Counter(r["condition_id"] for r in rows)
        mode_condition, mode_count = condition_counts.most_common(1)[0]
        purity_train = mode_count / n_train

        val_rows = by_key_val.get(key, [])
        n_validation = len(val_rows)
        purity_validation = (
            sum(1 for r in val_rows if r["condition_id"] == mode_condition) / n_validation
            if n_validation > 0 else None
        )

        tier = assign_tier(n_train, purity_train, n_validation, purity_validation, thresholds)

        candidates.append(
            PatternCandidate(
                workload_id=workload_id,
                diagnosed_cause=diagnosed_cause,
                n_train=n_train,
                mode_condition_train=mode_condition,
                purity_train=purity_train,
                n_validation=n_validation,
                purity_validation=purity_validation,
                tier=tier,
                protocol_version=protocol_version,
                dataset_content_hash=dataset_content_hash,
            )
        )
    return candidates


def assign_tier(
    n_train: int, purity_train: float, n_validation: int, purity_validation: Optional[float], thresholds: dict,
) -> EvidenceTier:
    """Implements configs/phase4_2_pattern_protocol.json's
    tier_assignment_precedence exactly (steps 2-5; step 1's n_train < 2
    exclusion happens before this function is called, in
    discover_candidates)."""
    if (
        n_train >= thresholds["CONFIRMED_MIN_N"]
        and purity_train >= thresholds["TAU_CONFIRMED"]
        and n_validation >= 1
        and purity_validation is not None
        and purity_validation >= thresholds["TAU_CONFIRMED_VALIDATION"]
    ):
        return EvidenceTier.CONFIRMED
    if purity_train >= thresholds["TAU_INFERRED"]:
        return EvidenceTier.INFERRED
    if n_train < thresholds["MIN_OBSERVATIONS_FOR_TRUSTED_PURITY"]:
        return EvidenceTier.UNCERTAIN
    return EvidenceTier.OBSERVED


def candidates_by_key(candidates: list[PatternCandidate]) -> dict[tuple, PatternCandidate]:
    return {(c.workload_id, c.diagnosed_cause): c for c in candidates}


# -- secondary pattern analyses (Phase 4.2 section 8.B / 8.D) --------------


def temporal_clustering_report(records: list[dict], protocol: dict) -> dict:
    """Per known combo: observed inter-occurrence step gaps vs. the
    constant spacing implied by src.data.episodic's deterministic
    round-robin scheduler. Descriptive only -- see protocol's
    secondary_pattern_analyses.temporal_clustering."""
    by_combo: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if not r["is_novel_combo"]:
            by_combo[(r["workload_id"], r["condition_id"])].append(r)

    report = {}
    for combo, rows in sorted(by_combo.items()):
        steps_by_occurrence = sorted({r["occurrence_ordinal"]: r["step"] for r in rows}.items())
        occurrence_steps = [s for _, s in steps_by_occurrence]
        gaps = [b - a for a, b in zip(occurrence_steps, occurrence_steps[1:])]
        report[f"{combo[0]}|{combo[1]}"] = {
            "occurrence_steps": occurrence_steps,
            "gaps": gaps,
            "gap_variance": float(_variance(gaps)) if len(gaps) > 1 else 0.0,
        }
    return report


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def cause_outcome_report(train_records: list[dict]) -> dict:
    """Descriptive only -- recovery_outcome/recovery_correct distribution
    by diagnosed_cause, among train-split CRITICAL-tier recovery
    attempts. NOT used to make or evaluate any recovery decision (Phase
    4.3's separate objective)."""
    attempted = [r for r in train_records if r.get("recovery_attempted")]
    by_cause: dict[str, list[dict]] = defaultdict(list)
    for r in attempted:
        by_cause[r["diagnosed_cause"]].append(r)

    report = {}
    for cause, rows in sorted(by_cause.items()):
        n = len(rows)
        n_recovered = sum(1 for r in rows if r["recovery_outcome"] == "RECOVERED")
        n_rolled_back = n - n_recovered
        recovered_correct = [r for r in rows if r["recovery_outcome"] == "RECOVERED" and r["recovery_correct"] is True]
        recovered_incorrect = [r for r in rows if r["recovery_outcome"] == "RECOVERED" and r["recovery_correct"] is False]
        report[cause] = {
            "n_attempts": n,
            "n_recovered": n_recovered,
            "n_rolled_back": n_rolled_back,
            "n_recovered_correct": len(recovered_correct),
            "n_recovered_incorrect": len(recovered_incorrect),
        }
    return report
