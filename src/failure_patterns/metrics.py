"""ACTIVE Phase 4.2 -- Alibaba baselines and metrics, computed exactly per
``configs/phase4_2_active_pattern_protocol.json``'s ``baselines`` and
``metrics`` blocks. Pure functions; the frozen test-split outcome is a
required argument, never re-derived here, so this module cannot
accidentally touch test data before the caller has explicitly run
``discovery_alibaba.evaluate_test`` / ``all_test_candidates``.
"""
from __future__ import annotations

from .schema import EvidenceTier, PatternCandidate, AlibabaTestOutcome


def flag_baseline_a(candidates: list[PatternCandidate]) -> set[tuple[str, str]]:
    return set()


def flag_baseline_b(candidates: list[PatternCandidate], n_min_trusted: int) -> set[tuple[str, str]]:
    return {(c.task_name, c.gpu_type) for c in candidates if c.n_train >= n_min_trusted}


def flag_method_c(candidates: list[PatternCandidate]) -> set[tuple[str, str]]:
    return {(c.task_name, c.gpu_type) for c in candidates if c.tier in (EvidenceTier.INFERRED, EvidenceTier.CONFIRMED)}


def flag_ablation_c_prime(candidates: list[PatternCandidate], n_min_candidate: int, margin_train: float) -> set[tuple[str, str]]:
    """Flat threshold, N_MIN_CANDIDATE floor only (no N_MIN_TRUSTED)."""
    out = set()
    for c in candidates:
        if c.n_train < n_min_candidate:
            continue
        if c.train_elevation is not None and c.train_elevation >= margin_train:
            out.add((c.task_name, c.gpu_type))
    return out


def flag_ablation_c_double_prime(candidates: list[PatternCandidate]) -> set[tuple[str, str]]:
    return {(c.task_name, c.gpu_type) for c in candidates if c.tier == EvidenceTier.CONFIRMED}


def rate_elevation_metrics(
    flagged: set[tuple[str, str]],
    test_outcomes: dict[tuple[str, str], AlibabaTestOutcome],
    all_test_candidates: dict[tuple[str, str], AlibabaTestOutcome],
    margin_train: float,
) -> dict:
    """precision/recall/false_pattern_rate against the frozen test split.
    ``test_outcomes`` = test-split outcome for each train/val-discovered
    candidate (may include candidates with n_test below the coverage
    floor, reported as not elevated=None). ``all_test_candidates`` = every
    test-split-eligible context, used as the recall denominator."""

    def is_elevated(o: AlibabaTestOutcome | None) -> bool | None:
        if o is None or o.test_rate is None or o.test_baseline_rate is None:
            return None
        return (o.test_rate - o.test_baseline_rate) >= margin_train

    flagged_evaluable = [k for k in flagged if is_elevated(test_outcomes.get(k)) is not None]
    n_flagged_evaluable = len(flagged_evaluable)
    n_flagged_true = sum(1 for k in flagged_evaluable if is_elevated(test_outcomes.get(k)))

    precision = (n_flagged_true / n_flagged_evaluable) if n_flagged_evaluable > 0 else None
    false_pattern_rate = (1 - precision) if precision is not None else None

    all_elevated_true = [k for k, o in all_test_candidates.items() if is_elevated(o) is True]
    n_true_total = len(all_elevated_true)
    n_true_flagged = sum(1 for k in all_elevated_true if k in flagged)
    recall = (n_true_flagged / n_true_total) if n_true_total > 0 else None

    return {
        "n_flagged": len(flagged),
        "n_flagged_evaluable_on_test": n_flagged_evaluable,
        "n_flagged_true_elevated_on_test": n_flagged_true,
        "precision": precision,
        "false_pattern_rate": false_pattern_rate,
        "n_true_elevated_test_candidates": n_true_total,
        "n_true_elevated_flagged": n_true_flagged,
        "recall": recall,
    }


def tier_calibration(
    candidates: list[PatternCandidate],
    test_outcomes: dict[tuple[str, str], AlibabaTestOutcome],
    margin_train: float,
) -> dict:
    """Test-split elevation rate within each tier -- measured, not
    assumed. See the protocol's ``metrics.tier_calibration``."""
    by_tier: dict[str, list[bool]] = {t.value: [] for t in EvidenceTier}
    for c in candidates:
        o = test_outcomes.get((c.task_name, c.gpu_type))
        if o is None or o.test_rate is None or o.test_baseline_rate is None:
            continue
        elevated = (o.test_rate - o.test_baseline_rate) >= margin_train
        by_tier[c.tier.value].append(elevated)

    out = {}
    for tier, values in by_tier.items():
        if not values:
            out[tier] = {"n_evaluable": 0, "elevation_rate": None}
        else:
            out[tier] = {"n_evaluable": len(values), "elevation_rate": sum(values) / len(values)}
    return out
