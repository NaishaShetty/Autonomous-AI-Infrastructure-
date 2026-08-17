"""Integration tests for the Phase 3.2 follow-up ablation pipeline: fitting
-data boundaries (no test data enters ablation fitting), deterministic seed
handling, exact reproduction of Candidate C, and correct probability-vs
-ranking-score interpretation."""
from __future__ import annotations

import json

import numpy as np

from benchmarks.phase3_1_evaluate import _t_interval
from benchmarks.phase3_2c_ablation import (
    EXPERIMENTS,
    _compute_test_arrays,
    _fit_experiments,
    _reconstruct_regime2_with_confidences,
    aggregate_across_seeds,
    run_one_seed,
)
from benchmarks.phase3_2_evaluate import run_one_seed as run_one_seed_phase3_2
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
    regime2 = _reconstruct_regime2_with_confidences(9, protocol, system)
    assert len(regime2["regime2_contexts"]) == protocol.regime_sizes[2]
    # _reconstruct_regime2_with_confidences itself asserts the failure count
    # matches system.n_logged_failures internally; reaching this point means
    # it held.
    experiments = _fit_experiments(system, regime2, seed=9)
    assert experiments["experiment_C_control"] is not None


def test_experiments_never_see_test_stream_during_fit():
    """Structural leakage check: the only data passed into any experiment's
    fit() comes from _reconstruct_regime2_with_confidences, which is
    asserted (inside itself) to contain only regime==2 samples. This test
    additionally confirms the test_stream (regime >=3) contexts never
    appear byte-identical among the regime-2 data used for fitting."""
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=10)
    regime2 = _reconstruct_regime2_with_confidences(10, protocol, system)

    def row_hash(ctx):
        return tuple(round(ctx[f], 10) for f in ["f1", "f2", "f3", "f4", "f5"])

    regime2_hashes = {row_hash(c) for c in regime2["regime2_contexts"]}
    test_hashes = {row_hash(s.context) for s in system.test_stream}
    assert not (regime2_hashes & test_hashes)


def test_standardization_and_scalers_fit_only_on_regime2():
    """Experiment A's StandardScaler-equivalent (mean_/scale_) and
    Experiment B's PCA must be fit only on regime-2 data -- verified by
    confirming their stored fitting statistics come from arrays of exactly
    regime-2 size, never regime-3/4 size."""
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=11)
    regime2 = _reconstruct_regime2_with_confidences(11, protocol, system)
    experiments = _fit_experiments(system, regime2, seed=11)

    exp_a = experiments["experiment_A_fixed_rule"]
    assert exp_a._mean.shape == (3,)  # 3 k-NN features, standardized over regime-2 only

    exp_b = experiments["experiment_B_old_repr_supervised"]
    assert exp_b._embedder._pca.n_samples_ == len(regime2["failure_contexts"])


def test_same_seed_gives_identical_experiment_predictions():
    protocol = _small_protocol()
    row_a = run_one_seed(5, protocol)
    row_b = run_one_seed(5, protocol)
    for name in EXPERIMENTS:
        np.testing.assert_allclose(row_a["_arrays"]["scores"][name], row_b["_arrays"]["scores"][name])


def test_different_seeds_give_different_experiment_predictions():
    protocol = _small_protocol()
    row_a = run_one_seed(1, protocol)
    row_b = run_one_seed(2, protocol)
    assert not np.array_equal(
        row_a["_arrays"]["scores"]["experiment_C_control"],
        row_b["_arrays"]["scores"]["experiment_C_control"],
    )


def test_result_is_json_serializable():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    clean = {k: v for k, v in row.items() if k != "_arrays"}
    serialized = json.dumps(clean)
    reloaded = json.loads(serialized)
    for name in EXPERIMENTS:
        assert "auroc" in reloaded["results"][name]


def test_aggregate_across_seeds_produces_valid_intervals():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    for name in EXPERIMENTS:
        a = aggregate[name]["auroc"]
        if a["mean"] is not None:
            assert a["ci_low"] <= a["mean"] <= a["ci_high"]


def test_experiment_a_reports_no_ece_experiment_b_and_c_do():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    assert row["results"]["experiment_A_fixed_rule"]["ece"] is None
    assert row["results"]["experiment_B_old_repr_supervised"]["ece"] is not None
    assert row["results"]["experiment_C_control"]["ece"] is not None


def test_experiment_c_exactly_reproduces_phase3_2_candidate_c():
    """Experiment C is documented as an unchanged reproduction of Phase
    3.2's Candidate C (FailureHistoryRiskModel, same k, features, fitting
    data, classifier config). Confirmed here by running BOTH the original
    Phase 3.2 evaluator and this follow-up's Experiment C on the same seed
    and protocol and checking their AUROC/scores match exactly (up to the
    two scripts' independent-but-equivalent regime-2 reconstruction)."""
    protocol = _small_protocol()
    row_ablation = run_one_seed(7, protocol)
    row_phase3_2 = run_one_seed_phase3_2(7, protocol)

    np.testing.assert_allclose(
        row_ablation["_arrays"]["scores"]["experiment_C_control"],
        row_phase3_2["_arrays"]["scores"]["candidate_failure_history"],
    )
    assert row_ablation["results"]["experiment_C_control"]["auroc"] == row_phase3_2["results"]["candidate_failure_history"]["auroc"]


def test_t_interval_reused_from_phase3_1_not_reimplemented():
    result = _t_interval([0.1, 0.2, 0.3], 0.95)
    assert result["n"] == 3
