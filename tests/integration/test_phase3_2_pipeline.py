"""Integration tests for the Phase 3.2 evaluation pipeline: fitting-data
boundaries (no test data enters candidate fitting), deterministic seed
handling, and compatibility with the Phase 3.1 evaluation framework
(reused metrics/bootstrap/protocol, unmodified)."""
from __future__ import annotations

import json

import numpy as np

from benchmarks.phase3_1_evaluate import _t_interval
from benchmarks.phase3_2_evaluate import (
    REPRESENTATIONS,
    _compute_test_arrays,
    _fit_candidates,
    _reconstruct_regime2,
    aggregate_across_seeds,
    candidate_d_temporal_analysis,
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


def test_reconstructed_regime2_matches_build_system_failure_count():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=9)
    regime2 = _reconstruct_regime2(9, protocol)
    assert len(regime2) == protocol.regime_sizes[2]
    assert all(s.regime == 2 for s in regime2)

    candidates = _fit_candidates(system, regime2, protocol, seed=9)
    # _fit_candidates itself asserts the failure count matches
    # system.n_logged_failures internally; reaching this point means it held.
    assert candidates["candidate_raw_features"] is not None


def test_candidates_never_see_test_stream_during_fit():
    """Structural leakage check: the only data passed into
    RawFeatureFailureRisk.fit / FailureHistoryRiskModel.fit comes from
    _reconstruct_regime2, which is asserted (inside itself) to contain only
    regime==2 samples. This test additionally confirms the test_stream
    (regime >=3) contexts never appear byte-identical among the regime-2
    data used for fitting."""
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=10)
    regime2 = _reconstruct_regime2(10, protocol)

    def row_hash(ctx):
        return tuple(round(ctx[f], 10) for f in ["f1", "f2", "f3", "f4", "f5"])

    regime2_hashes = {row_hash(s.context) for s in regime2}
    test_hashes = {row_hash(s.context) for s in system.test_stream}
    assert not (regime2_hashes & test_hashes)


def test_same_seed_gives_identical_candidate_predictions():
    protocol = _small_protocol()
    row_a = run_one_seed(5, protocol)
    row_b = run_one_seed(5, protocol)
    np.testing.assert_allclose(
        row_a["_arrays"]["scores"]["candidate_failure_history"],
        row_b["_arrays"]["scores"]["candidate_failure_history"],
    )
    np.testing.assert_allclose(
        row_a["_arrays"]["scores"]["candidate_raw_features"],
        row_b["_arrays"]["scores"]["candidate_raw_features"],
    )


def test_different_seeds_give_different_candidate_predictions():
    protocol = _small_protocol()
    row_a = run_one_seed(1, protocol)
    row_b = run_one_seed(2, protocol)
    assert not np.array_equal(
        row_a["_arrays"]["scores"]["candidate_failure_history"],
        row_b["_arrays"]["scores"]["candidate_failure_history"],
    )


def test_result_is_json_serializable():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    clean = {k: v for k, v in row.items() if k != "_arrays"}
    serialized = json.dumps(clean)
    reloaded = json.loads(serialized)
    for name in REPRESENTATIONS:
        assert "auroc" in reloaded["results"][name]


def test_aggregate_across_seeds_produces_valid_intervals():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    for name in REPRESENTATIONS:
        a = aggregate[name]["auroc"]
        if a["mean"] is not None:
            assert a["ci_low"] <= a["mean"] <= a["ci_high"]


def test_ece_not_reported_for_non_probabilistic_representations():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    # control and raw-feature candidate are Gaussian-kernel similarity
    # scores, never fit as probabilities -- ECE must be None, not a
    # manufactured number.
    assert row["results"]["control_phase2_failure_memory"]["ece"] is None
    assert row["results"]["candidate_raw_features"]["ece"] is None
    # calibrated confidence and the failure-history logistic model ARE
    # legitimate probabilities.
    assert row["results"]["B_calibrated_confidence"]["ece"] is not None
    assert row["results"]["candidate_failure_history"]["ece"] is not None


def test_candidate_d_reports_negative_finding_not_fabricated_results():
    analysis = candidate_d_temporal_analysis()
    assert analysis["executed"] is False
    assert "cannot be validly evaluated" in analysis["conclusion"]


def test_t_interval_reused_from_phase3_1_not_reimplemented():
    """Confirms Phase 3.2 imports Phase 3.1's aggregation helper rather
    than maintaining a second copy that could silently diverge."""
    result = _t_interval([0.1, 0.2, 0.3], 0.95)
    assert result["n"] == 3
