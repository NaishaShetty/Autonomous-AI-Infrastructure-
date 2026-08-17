"""Runs the Phase 3.1 leakage-audit checks (the same functions used by
``benchmarks/phase3_1_leakage_audit.py``) as pytest regressions, at small
scale, so a future change that introduces leakage fails CI rather than
requiring someone to remember to re-run the standalone script."""
from __future__ import annotations

from benchmarks.phase3_1_leakage_audit import (
    check_duplicate_samples_across_splits,
    check_label_leakage_in_features,
    check_regime_identifiability_from_features,
    check_synthetic_generation_triviality,
    check_temporal_and_fit_isolation,
)
from src.pipeline_builder import build_system

SMALL_REGIME_SIZES = (300, 150, 150, 150, 150)


def test_no_temporal_or_fit_isolation_leakage():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=11)
    result = _run_with_regime_sizes(check_temporal_and_fit_isolation, system, SMALL_REGIME_SIZES)
    assert result["passed"]


def _run_with_regime_sizes(fn, system, regime_sizes):
    """The standalone script's check functions close over its own
    module-level DEFAULT_REGIME_SIZES/SEED constants; this helper
    monkeypatches them for the duration of the call so the same check logic
    runs against the small test-only regime sizes instead of duplicating
    the check implementation here."""
    import benchmarks.phase3_1_leakage_audit as audit_module

    original_sizes, original_seed = audit_module.DEFAULT_REGIME_SIZES, audit_module.SEED
    audit_module.DEFAULT_REGIME_SIZES = regime_sizes
    try:
        return fn(system)
    finally:
        audit_module.DEFAULT_REGIME_SIZES = original_sizes
        audit_module.SEED = original_seed


def test_no_label_leakage_in_features():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=12)
    result = check_label_leakage_in_features(system)
    assert result["passed"]
    assert set(result["context_keys_seen"]) == set(result["expected_keys"])


def test_no_duplicate_samples_across_splits():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=13)
    result = _run_with_regime_sizes(check_duplicate_samples_across_splits, system, SMALL_REGIME_SIZES)
    assert result["passed"]
    assert result["overlaps_found"] == {}


def test_regime_not_trivially_identifiable_from_features():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=14)
    result = _run_with_regime_sizes(check_regime_identifiability_from_features, system, SMALL_REGIME_SIZES)
    assert result["passed"]


def test_synthetic_generation_not_trivial():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=15)
    result = _run_with_regime_sizes(check_synthetic_generation_triviality, system, SMALL_REGIME_SIZES)
    assert result["passed"]
