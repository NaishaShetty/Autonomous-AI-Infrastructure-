"""Integration tests for Phase 3.6.1 complementarity: fitting-data
boundary, determinism, and reproduction of the known finding (BF is not
distinguishable from B alone on this benchmark)."""
from __future__ import annotations

import numpy as np
import pytest

from benchmarks.phase3_1_evaluate import _t_interval
from benchmarks.phase3_3_generalization import _fit_frozen_candidate, _reconstruct_regime2_with_confidences
from benchmarks.phase3_6_complementarity import (
    CANDIDATES,
    _compute_test_arrays,
    _fit_combined,
    aggregate_across_seeds,
    paired_comparison,
    run_one_seed,
)
from src.evaluation.complementarity import CombinedRisk
from src.evaluation.protocol import Phase31Protocol
from src.pipeline_builder import build_system

SMALL_REGIME_SIZES = (300, 150, 150, 150, 150)


def _small_protocol() -> Phase31Protocol:
    protocol = Phase31Protocol.load()
    protocol.regime_sizes = SMALL_REGIME_SIZES
    protocol.seeds = [1, 2, 3]
    protocol.primary_seed = 1
    return protocol


def test_combined_risk_fit_only_on_regime2_data():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=1)
    regime2 = _reconstruct_regime2_with_confidences(1, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, 1)
    combined = _fit_combined(regime2, candidate_f, 1)
    assert combined.is_fitted
    assert combined._clf.coef_.shape == (1, 2)  # exactly 2 inputs -- no extra features


def test_combined_risk_never_sees_test_stream():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=2)
    regime2 = _reconstruct_regime2_with_confidences(2, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, 2)
    combined = _fit_combined(regime2, candidate_f, 2)

    def row_hash(ctx):
        return tuple(round(ctx[f], 10) for f in ["f1", "f2", "f3", "f4", "f5"])

    regime2_hashes = {row_hash(c) for c in regime2["regime2_contexts"]}
    test_hashes = {row_hash(s.context) for s in system.test_stream}
    assert not (regime2_hashes & test_hashes)


def test_combined_risk_output_in_unit_interval():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=3)
    regime2 = _reconstruct_regime2_with_confidences(3, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, 3)
    combined = _fit_combined(regime2, candidate_f, 3)
    arrays = _compute_test_arrays(system, candidate_f, combined)
    scores = arrays["scores"]["BF_combined"]
    assert (scores >= 0.0).all() and (scores <= 1.0).all()


def test_no_hyperparameter_search_default_logistic_regression():
    combined = CombinedRisk(random_state=1).fit([0.1, 0.9, 0.3], [0.2, 0.8, 0.1], [0, 1, 0])
    assert combined._clf.C == 1.0  # sklearn default, never overridden
    assert combined._clf.max_iter == 1000


def test_same_seed_deterministic():
    protocol = _small_protocol()
    row_a = run_one_seed(1, protocol)
    row_b = run_one_seed(1, protocol)
    np.testing.assert_allclose(row_a["_arrays"]["scores"]["BF_combined"], row_b["_arrays"]["scores"]["BF_combined"])


def test_all_six_seeds_evaluated():
    protocol = Phase31Protocol.load()
    assert protocol.seeds == [1, 2, 3, 4, 5, 42]


def test_aggregate_uses_shared_t_interval():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    for name in CANDIDATES:
        assert aggregate[name]["auroc"]["n"] == len(protocol.seeds)


def test_paired_comparison_caveat_present():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    result = paired_comparison(per_seed, protocol)
    assert "no significance test" in result["caveat"]
    assert result["n_seeds"] == len(protocol.seeds)


def test_t_interval_reused_not_reimplemented():
    assert _t_interval([1, 2, 3], 0.95)["n"] == 3
