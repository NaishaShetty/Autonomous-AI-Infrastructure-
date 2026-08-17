"""Phase 4.2.11/4.2.12: row-level pattern precision/recall and tier-level
calibration, per configs/phase4_2_pattern_protocol.json's
row_level_evaluation / metrics blocks."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Optional

from .schema import EvidenceTier, PatternCandidate


def evaluate_rows(
    test_rows: list[dict],
    candidates_by_key: dict[tuple, PatternCandidate],
    is_flagged: Callable[[PatternCandidate], bool],
) -> dict:
    """``is_flagged`` implements one retrieval_method's flagging rule
    (A/B/C1/C2 -- see benchmarks/phase4_2_pattern_evaluate.py). Returns
    coverage, precision, recall, and per-row detail for failure-case
    analysis."""
    covered = []
    for r in test_rows:
        key = (r["workload_id"], r["diagnosed_cause"])
        candidate = candidates_by_key.get(key)
        if candidate is None:
            continue
        is_true_structure = r["condition_id"] == candidate.mode_condition_train
        flagged = is_flagged(candidate)
        covered.append({
            "workload_id": r["workload_id"],
            "diagnosed_cause": r["diagnosed_cause"],
            "condition_id": r["condition_id"],
            "tier": candidate.tier.value,
            "is_true_structure": is_true_structure,
            "flagged": flagged,
        })

    n_total = len(test_rows)
    n_covered = len(covered)
    n_flagged = sum(1 for c in covered if c["flagged"])
    n_flagged_true = sum(1 for c in covered if c["flagged"] and c["is_true_structure"])
    n_true_structure = sum(1 for c in covered if c["is_true_structure"])
    n_true_structure_flagged = sum(1 for c in covered if c["is_true_structure"] and c["flagged"])

    precision = (n_flagged_true / n_flagged) if n_flagged > 0 else None
    recall = (n_true_structure_flagged / n_true_structure) if n_true_structure > 0 else None

    return {
        "n_total_test_rows": n_total,
        "n_covered": n_covered,
        "coverage_rate": (n_covered / n_total) if n_total > 0 else None,
        "n_flagged": n_flagged,
        "n_true_structure": n_true_structure,
        "precision": precision,
        "recall": recall,
        "rows": covered,
    }


def tier_level_true_structure_rate(
    test_rows: list[dict], candidates_by_key: dict[tuple, PatternCandidate],
) -> dict:
    by_tier: dict[str, list[bool]] = defaultdict(list)
    for r in test_rows:
        key = (r["workload_id"], r["diagnosed_cause"])
        candidate = candidates_by_key.get(key)
        if candidate is None:
            continue
        by_tier[candidate.tier.value].append(r["condition_id"] == candidate.mode_condition_train)

    out = {}
    for tier in EvidenceTier:
        values = by_tier.get(tier.value, [])
        out[tier.value] = {
            "n": len(values),
            "true_structure_rate": (sum(values) / len(values)) if values else None,
        }
    return out
