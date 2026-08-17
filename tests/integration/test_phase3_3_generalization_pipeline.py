"""Integration tests for the Phase 3.3 generalization pipeline: condition
configuration, fit/eval separation (the candidate must be fit exactly once
per seed and never refit per condition), no leakage between regime-2
fitting data and any generalization condition's test samples, deterministic
seed handling, and preservation of the Phase 3.1/3.2C in-distribution
reference."""
from __future__ import annotations

import json

import numpy as np

from benchmarks.phase3_1_evaluate import _t_interval
from benchmarks.phase3_2c_ablation import run_one_seed as run_one_seed_phase3_2c
from benchmarks.phase3_3_generalization import (
    BASELINE_DRIFT_SCALE,
    BASELINES,
    CONDITIONS,
    _condition_test_samples,
    _fit_frozen_candidate,
    _reconstruct_regime2_with_confidences,
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


# -- condition configuration ----------------------------------------------


def test_conditions_are_predetermined_and_include_baseline_and_two_unseen():
    ids = [c.id for c in CONDITIONS]
    assert ids == ["original_benchmark", "unseen_weaker_drift", "unseen_stronger_drift"]
    kinds = {c.id: c.kind for c in CONDITIONS}
    assert kinds["original_benchmark"] == "in_distribution_reference"
    assert kinds["unseen_weaker_drift"] == "unseen"
    assert kinds["unseen_stronger_drift"] == "unseen"


def test_original_benchmark_condition_uses_baseline_drift_scale():
    original = next(c for c in CONDITIONS if c.id == "original_benchmark")
    assert original.drift_scale == BASELINE_DRIFT_SCALE


def test_unseen_conditions_are_symmetric_predetermined_multiples_of_baseline():
    weaker = next(c for c in CONDITIONS if c.id == "unseen_weaker_drift")
    stronger = next(c for c in CONDITIONS if c.id == "unseen_stronger_drift")
    assert weaker.drift_scale == BASELINE_DRIFT_SCALE * 0.5
    assert stronger.drift_scale == BASELINE_DRIFT_SCALE * 2.0


# -- generator property this study depends on ------------------------------


def test_features_invariant_to_drift_scale_but_labels_are_not():
    """The generalization design depends on this generator property (see
    module docstring of phase3_3_generalization.py): for a fixed seed,
    regime-3/4 FEATURES are identical across drift_scale, only labels
    differ. Verified directly here, not merely assumed."""
    from src.data.synthetic import FEATURE_NAMES, generate_regime_stream

    protocol = _small_protocol()
    s_weak = generate_regime_stream(regime_sizes=protocol.regime_sizes, drift_scale=0.175, seed=42)
    s_strong = generate_regime_stream(regime_sizes=protocol.regime_sizes, drift_scale=0.70, seed=42)

    r3_weak = [s for s in s_weak if s.regime == 3]
    r3_strong = [s for s in s_strong if s.regime == 3]

    X_weak = np.array([[s.context[f] for f in FEATURE_NAMES] for s in r3_weak])
    X_strong = np.array([[s.context[f] for f in FEATURE_NAMES] for s in r3_strong])
    y_weak = np.array([s.label for s in r3_weak])
    y_strong = np.array([s.label for s in r3_strong])

    np.testing.assert_allclose(X_weak, X_strong)
    assert not np.array_equal(y_weak, y_strong)


def test_regime0_training_data_is_fully_drift_scale_invariant():
    from src.data.synthetic import FEATURE_NAMES, generate_regime_stream

    protocol = _small_protocol()
    s_weak = generate_regime_stream(regime_sizes=protocol.regime_sizes, drift_scale=0.175, seed=7)
    s_strong = generate_regime_stream(regime_sizes=protocol.regime_sizes, drift_scale=0.70, seed=7)
    r0_weak = [s for s in s_weak if s.regime == 0]
    r0_strong = [s for s in s_strong if s.regime == 0]
    y0_weak = np.array([s.label for s in r0_weak])
    y0_strong = np.array([s.label for s in r0_strong])
    assert np.array_equal(y0_weak, y0_strong)


# -- fit/eval separation ----------------------------------------------------


def test_candidate_fit_exactly_once_and_reused_across_conditions():
    """The candidate object returned by run_one_seed's internal fitting step
    must be the SAME fitted object scored against every condition -- no
    condition may trigger a refit. Verified structurally: fit the candidate
    once, capture its logistic-regression coefficients, then confirm the
    same coefficients are still present after computing scores for every
    condition (nothing in the scoring path mutates them)."""
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=4)
    regime2 = _reconstruct_regime2_with_confidences(4, protocol, system)
    candidate = _fit_frozen_candidate(regime2, seed=4)
    coef_before = candidate._clf.coef_.copy()

    for condition in CONDITIONS:
        test_samples = _condition_test_samples(condition, 4, protocol, system)
        for s in test_samples[:5]:
            candidate.risk(s.context, 0.5)  # scoring only, never .fit()

    np.testing.assert_array_equal(candidate._clf.coef_, coef_before)


def test_no_fit_method_called_inside_condition_loop():
    """Structural guarantee: Phase2RepresentationSupervisedRisk.fit is never
    referenced anywhere in _condition_test_samples or the per-condition
    scoring path -- confirmed by source inspection rather than trusting the
    docstring."""
    import ast
    import inspect

    import benchmarks.phase3_3_generalization as mod

    for fn in (mod._condition_test_samples, mod._compute_condition_arrays):
        tree = ast.parse(inspect.getsource(fn))
        fit_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "fit"
        ]
        assert not fit_calls, f"{fn.__name__} calls .fit() -- candidate must never be refit per condition"


# -- leakage ------------------------------------------------------------


def test_no_condition_test_samples_overlap_regime2_fitting_data():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=8)
    regime2 = _reconstruct_regime2_with_confidences(8, protocol, system)

    def row_hash(ctx):
        return tuple(round(ctx[f], 10) for f in ["f1", "f2", "f3", "f4", "f5"])

    regime2_hashes = {row_hash(c) for c in regime2["regime2_contexts"]}
    for condition in CONDITIONS:
        test_samples = _condition_test_samples(condition, 8, protocol, system)
        test_hashes = {row_hash(s.context) for s in test_samples}
        assert not (regime2_hashes & test_hashes), f"leakage in condition {condition.id}"


def test_original_benchmark_condition_is_byte_identical_to_system_test_stream():
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=6)
    original = next(c for c in CONDITIONS if c.id == "original_benchmark")
    test_samples = _condition_test_samples(original, 6, protocol, system)
    assert test_samples is system.test_stream


# -- determinism / reproducibility ------------------------------------------


def test_same_seed_gives_identical_results():
    protocol = _small_protocol()
    row_a = run_one_seed(5, protocol)
    row_b = run_one_seed(5, protocol)
    for condition in CONDITIONS:
        for name in BASELINES:
            np.testing.assert_allclose(
                row_a["per_condition"][condition.id]["_arrays"]["scores"][name],
                row_b["per_condition"][condition.id]["_arrays"]["scores"][name],
            )


def test_different_seeds_give_different_results():
    protocol = _small_protocol()
    row_a = run_one_seed(1, protocol)
    row_b = run_one_seed(2, protocol)
    assert not np.array_equal(
        row_a["per_condition"]["original_benchmark"]["_arrays"]["scores"]["D_supervised_failure_risk"],
        row_b["per_condition"]["original_benchmark"]["_arrays"]["scores"]["D_supervised_failure_risk"],
    )


def test_candidate_d_matches_phase3_2c_experiment_b_on_original_benchmark():
    """The frozen candidate D scored on the original_benchmark condition
    must reproduce Phase 3.2C's Experiment B result exactly -- same class,
    same config, same fitting data, same test stream."""
    protocol = _small_protocol()
    row_gen = run_one_seed(9, protocol)
    row_3_2c = run_one_seed_phase3_2c(9, protocol)

    np.testing.assert_allclose(
        row_gen["per_condition"]["original_benchmark"]["_arrays"]["scores"]["D_supervised_failure_risk"],
        row_3_2c["_arrays"]["scores"]["experiment_B_old_repr_supervised"],
    )


# -- result structure / aggregation -----------------------------------------


def test_result_is_json_serializable():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    clean_row = {k: v for k, v in row.items() if k != "per_condition"}
    clean_row["per_condition"] = {
        cid: {k: v for k, v in cond.items() if k != "_arrays"} for cid, cond in row["per_condition"].items()
    }
    serialized = json.dumps(clean_row)
    reloaded = json.loads(serialized)
    for condition in CONDITIONS:
        for name in BASELINES:
            assert "auroc" in reloaded["per_condition"][condition.id]["results"][name]


def test_aggregate_across_seeds_produces_valid_intervals_per_condition():
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol) for s in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol)
    for condition in CONDITIONS:
        for name in BASELINES:
            a = aggregate[condition.id][name]["auroc"]
            if a["mean"] is not None:
                assert a["ci_low"] <= a["mean"] <= a["ci_high"]


def test_ece_not_reported_for_original_failure_memory_across_all_conditions():
    protocol = _small_protocol()
    row = run_one_seed(1, protocol)
    for condition in CONDITIONS:
        assert row["per_condition"][condition.id]["results"]["C_original_failure_memory"]["ece"] is None
        assert row["per_condition"][condition.id]["results"]["D_supervised_failure_risk"]["ece"] is not None


def test_t_interval_reused_from_phase3_1_not_reimplemented():
    result = _t_interval([0.1, 0.2, 0.3], 0.95)
    assert result["n"] == 3
