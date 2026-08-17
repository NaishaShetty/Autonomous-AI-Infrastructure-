"""Integration tests for the Phase 3.1 evaluation infrastructure: correct
train/test separation, deterministic seed handling, and result
serialization -- exercised against small (fast) regime sizes, not the full
protocol config (that's covered by running benchmarks/phase3_1_evaluate.py
itself, not by the test suite)."""
from __future__ import annotations

import json

import numpy as np

from benchmarks.phase3_1_evaluate import (
    BASELINES,
    _compute_test_arrays,
    _strip_arrays,
    _t_interval,
    aggregate_across_seeds,
    run_one_seed,
)
from src.evaluation.protocol import Phase31Protocol
from src.pipeline_builder import build_system

SMALL_REGIME_SIZES = (300, 150, 150, 150, 150)


def _small_protocol() -> Phase31Protocol:
    protocol = Phase31Protocol.load()
    protocol.regime_sizes = SMALL_REGIME_SIZES
    protocol.seeds = [1, 2, 3]
    protocol.primary_seed = 1
    return protocol


def test_same_seed_produces_identical_test_arrays():
    system_a = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=7)
    system_b = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=7)
    arrays_a = _compute_test_arrays(system_a, SMALL_REGIME_SIZES)
    arrays_b = _compute_test_arrays(system_b, SMALL_REGIME_SIZES)
    np.testing.assert_array_equal(arrays_a["y_fail"], arrays_b["y_fail"])
    np.testing.assert_allclose(arrays_a["scores"]["C_failure_memory"], arrays_b["scores"]["C_failure_memory"])


def test_different_seeds_produce_different_test_data():
    system_a = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=1)
    system_b = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=2)
    arrays_a = _compute_test_arrays(system_a, SMALL_REGIME_SIZES)
    arrays_b = _compute_test_arrays(system_b, SMALL_REGIME_SIZES)
    assert not np.array_equal(arrays_a["y_fail"], arrays_b["y_fail"])


def test_test_stream_is_disjoint_from_fitting_data_by_construction():
    """Same check as the standalone leakage audit script, run inline as a
    pytest regression test so CI-style runs catch a future regression, not
    just a manually-invoked script."""
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=2, seed=3)
    failure_regimes = {e.metadata.get("regime") for e in system.failure_memory._failure_events}
    assert failure_regimes <= {2}
    assert all(s.regime >= 3 for s in system.test_stream)


def test_run_one_seed_result_is_json_serializable_after_stripping_arrays():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    clean = _strip_arrays([row])[0]
    serialized = json.dumps(clean)  # must not raise
    assert "_arrays" not in clean
    reloaded = json.loads(serialized)
    for name in BASELINES:
        assert "auroc" in reloaded["baselines"][name]


def test_aggregate_across_seeds_produces_valid_confidence_intervals():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    for name in BASELINES:
        auroc_agg = aggregate[name]["auroc"]
        if auroc_agg["mean"] is not None:
            assert auroc_agg["ci_low"] <= auroc_agg["mean"] <= auroc_agg["ci_high"]


def test_t_interval_matches_mean_for_single_value():
    result = _t_interval([0.7], confidence_level=0.95)
    assert result["mean"] == 0.7
    assert result["ci_low"] == result["ci_high"] == 0.7


def test_t_interval_handles_empty_list():
    result = _t_interval([], confidence_level=0.95)
    assert result["mean"] is None
    assert result["n"] == 0


def test_no_signal_baseline_auroc_is_always_exactly_half_across_seeds():
    """Sanity/regression check on the evaluation pipeline itself: Baseline
    A is a constant score by construction, so its AUROC must be exactly 0.5
    for every seed -- if this ever fails, the bug is in the evaluation
    code, not in Failure Memory."""
    protocol = _small_protocol()
    for seed in protocol.seeds:
        row = run_one_seed(seed, protocol)
        assert row["baselines"]["A_no_signal"]["auroc"] == 0.5
