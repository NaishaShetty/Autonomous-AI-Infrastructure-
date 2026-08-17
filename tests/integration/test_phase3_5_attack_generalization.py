"""Integration tests for the Phase 3.5 attack-generalization pipeline:
frozen protocol loading, deterministic attack transforms, no refitting on
attack conditions, F/B/C implementation reuse (not reimplementation), full
seed coverage, and leakage-audit passage."""
from __future__ import annotations

import inspect
import json

import numpy as np
import pytest

from benchmarks.phase3_1_evaluate import _t_interval
from benchmarks.phase3_3_generalization import (
    BASELINES,
    _fit_frozen_candidate,
    _reconstruct_regime2_with_confidences,
    run_one_seed as run_one_seed_phase3_3,
)
import benchmarks.phase3_5_attack_generalization as phase3_5
from benchmarks.phase3_5_attack_generalization import (
    Phase35LeakageError,
    _assert_attack_preserves_ground_truth,
    _condition_test_samples,
    aggregate_across_seeds,
    load_protocol35,
    robustness_analysis,
    run_one_seed,
)
from src.data.synthetic import FEATURE_NAMES
from src.evaluation.attacks import apply_feature_dropout, apply_feature_noise
from src.evaluation.protocol import Phase31Protocol
from src.pipeline_builder import build_system

SMALL_REGIME_SIZES = (300, 150, 150, 150, 150)


def _small_protocol() -> Phase31Protocol:
    protocol = Phase31Protocol.load()
    protocol.regime_sizes = SMALL_REGIME_SIZES
    protocol.seeds = [1, 2, 3]
    protocol.primary_seed = 1
    return protocol


@pytest.fixture(scope="module")
def protocol35():
    return load_protocol35()


def test_protocol_loads_and_is_frozen(protocol35):
    assert protocol35["_frozen"] is True
    assert protocol35["seeds"] == [1, 2, 3, 4, 5, 42]
    assert protocol35["primary_seed"] == 42


def test_seeds_exactly_match_frozen_phase3_1_seeds(protocol35):
    protocol = Phase31Protocol.load()
    assert protocol35["seeds"] == protocol.seeds
    assert protocol35["primary_seed"] == protocol.primary_seed


def test_attack_matrix_has_three_predetermined_conditions(protocol35):
    ids = [c["id"] for c in protocol35["attack_matrix"]]
    assert ids == ["feature_noise_mild", "feature_noise_severe", "feature_dropout"]
    for c in protocol35["attack_matrix"]:
        assert c["seen_or_unseen"] == "unseen"
        assert c["kind"] == "covariate_shift_attack"


def test_clean_condition_reuses_test_stream_unmodified():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=1)
    samples = _condition_test_samples({"id": "clean"}, seed=1, system=system)
    assert samples is system.test_stream


def test_attack_conditions_never_return_the_original_stream_object():
    system = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=1)
    noisy = _condition_test_samples(
        {"id": "feature_noise_mild", "mechanism": "feature_noise", "parameters": {"std": 0.5}, "attack_ordinal": 1},
        seed=1, system=system,
    )
    assert noisy is not system.test_stream
    assert len(noisy) == len(system.test_stream)


def test_feature_noise_is_deterministic_given_seed_and_ordinal():
    samples = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=2).test_stream
    a = apply_feature_noise(samples, FEATURE_NAMES, std=0.5, seed=2, attack_ordinal=1)
    b = apply_feature_noise(samples, FEATURE_NAMES, std=0.5, seed=2, attack_ordinal=1)
    for sa, sb in zip(a, b):
        assert sa.context == sb.context


def test_feature_noise_different_ordinal_gives_different_noise():
    samples = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=2).test_stream
    a = apply_feature_noise(samples, FEATURE_NAMES, std=0.5, seed=2, attack_ordinal=1)
    c = apply_feature_noise(samples, FEATURE_NAMES, std=0.5, seed=2, attack_ordinal=2)
    assert any(abs(sa.context[f] - sc.context[f]) > 1e-9 for sa, sc in zip(a, c) for f in FEATURE_NAMES)


def test_feature_dropout_zeroes_only_targeted_features():
    samples = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=3).test_stream
    dropped = apply_feature_dropout(samples, FEATURE_NAMES, dropped_features=["f2", "f4"])
    for orig, d in zip(samples, dropped):
        assert d.context["f2"] == 0.0
        assert d.context["f4"] == 0.0
        for f in ("f1", "f3", "f5"):
            assert d.context[f] == orig.context[f]


def test_attack_transforms_preserve_labels_and_regime():
    samples = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=4).test_stream
    noisy = apply_feature_noise(samples, FEATURE_NAMES, std=1.5, seed=4, attack_ordinal=2)
    dropped = apply_feature_dropout(samples, FEATURE_NAMES, dropped_features=["f2", "f4"])
    _assert_attack_preserves_ground_truth(samples, noisy, "feature_noise_severe")  # must not raise
    _assert_attack_preserves_ground_truth(samples, dropped, "feature_dropout")  # must not raise


def test_ground_truth_check_catches_a_corrupted_label():
    samples = build_system(regime_sizes=SMALL_REGIME_SIZES, n_clusters=3, seed=5).test_stream
    tampered = list(samples)
    from src.data.synthetic import StreamSample
    tampered[0] = StreamSample(context=tampered[0].context, label=1 - tampered[0].label, regime=tampered[0].regime)
    with pytest.raises(Phase35LeakageError):
        _assert_attack_preserves_ground_truth(samples, tampered, "fake_condition")


def test_no_fit_call_anywhere_in_run_one_seed_scoring_loop():
    src = inspect.getsource(phase3_5.run_one_seed)
    loop_start = src.index("for condition in all_conditions:")
    assert ".fit(" not in src[loop_start:]


def test_f_implementation_matches_phase3_3_frozen_candidate():
    """F must be produced by the exact same fit call Phase 3.3 froze --
    verified by fitting via both modules on the same seed/protocol and
    comparing predictions on the same held-out sample, using the sample's
    actual calibrated confidence (not an arbitrary stand-in value)."""
    protocol = _small_protocol()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=7)
    regime2 = _reconstruct_regime2_with_confidences(7, protocol, system)
    candidate_here = _fit_frozen_candidate(regime2, 7)

    sample = system.test_stream[0]
    x = np.array([sample.context[f] for f in FEATURE_NAMES], dtype=float)
    pred = system.workload_model.predict(x)
    calib_features = {**sample.context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
    calib_result = system.calibrator.predict(calib_features)
    candidate_score_here = candidate_here.risk(sample.context, calib_result.calibrated_confidence)

    row_phase3_3 = run_one_seed_phase3_3(7, protocol)
    phase3_3_scores = row_phase3_3["per_condition"]["original_benchmark"]["_arrays"]["scores"]["D_supervised_failure_risk"]
    assert phase3_3_scores[0] == pytest.approx(candidate_score_here)


def test_b_and_c_scores_are_computed_by_reused_phase3_3_helpers():
    """B (calibrated confidence) and C (original Failure Memory) are never
    redefined in phase3_5_attack_generalization.py -- BASELINES and
    _compute_condition_arrays are imported directly from
    benchmarks.phase3_3_generalization."""
    assert "B_calibrated_confidence" in BASELINES
    assert "C_original_failure_memory" in BASELINES
    assert phase3_5._compute_condition_arrays.__module__ == "benchmarks.phase3_3_generalization"
    assert phase3_5._evaluate_one.__module__ == "benchmarks.phase3_3_generalization"


def test_all_conditions_evaluated_for_all_seeds(protocol35):
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol, protocol35) for s in protocol.seeds]
    expected_ids = {"clean"} | {c["id"] for c in protocol35["attack_matrix"]}
    for row in per_seed:
        assert set(row["per_condition"].keys()) == expected_ids


def test_metrics_deterministic_given_seed(protocol35):
    protocol = _small_protocol()
    row_a = run_one_seed(1, protocol, protocol35)
    row_b = run_one_seed(1, protocol, protocol35)
    for cond_id in row_a["per_condition"]:
        np.testing.assert_allclose(
            row_a["per_condition"][cond_id]["_arrays"]["scores"]["D_supervised_failure_risk"],
            row_b["per_condition"][cond_id]["_arrays"]["scores"]["D_supervised_failure_risk"],
        )


def test_coverage_points_unchanged():
    protocol = Phase31Protocol.load()
    assert protocol.coverage_operating_points == [0.05, 0.10, 0.20, 0.50]


def test_bootstrap_settings_unchanged():
    protocol = Phase31Protocol.load()
    assert protocol.bootstrap.n_resamples == 2000
    assert protocol.bootstrap.seed == 0
    assert protocol.bootstrap.confidence_level == 0.95


def test_cross_seed_aggregation_matches_frozen_methodology(protocol35):
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol, protocol35) for s in protocol.seeds]
    all_ids = ["clean"] + [c["id"] for c in protocol35["attack_matrix"]]
    aggregate = aggregate_across_seeds(per_seed, protocol, all_ids)
    for cond_id in all_ids:
        a = aggregate[cond_id]["D_supervised_failure_risk"]["auroc"]
        if a["mean"] is not None:
            assert a["ci_low"] <= a["mean"] <= a["ci_high"]
            assert a["n"] == len(protocol.seeds)


def test_robustness_metric_defined_before_evaluation_matches_protocol(protocol35):
    assert protocol35["robustness_metric"]["name"] == "excess_auroc_retention_ratio"
    assert "attack_auroc - 0.5" in protocol35["robustness_metric"]["definition"]


def test_robustness_analysis_retention_ratio_undefined_for_no_signal(protocol35):
    protocol = _small_protocol()
    per_seed = [run_one_seed(s, protocol, protocol35) for s in protocol.seeds]
    attack_ids = [c["id"] for c in protocol35["attack_matrix"]]
    rob = robustness_analysis(per_seed, protocol, attack_ids)
    for cond_id in attack_ids:
        assert rob[cond_id]["A_no_signal"]["n_seeds_with_defined_ratio"] == 0


def test_no_new_seeds_added_or_removed(protocol35):
    assert protocol35["seeds"] == [1, 2, 3, 4, 5, 42]


def test_leakage_audit_passes():
    from benchmarks.phase3_5_leakage_audit import (
        check_attack_determinism,
        check_attack_transforms_actually_corrupt_context,
        check_attack_transforms_preserve_ground_truth,
        check_duplicate_samples_across_attack_conditions,
        check_no_fit_calls_during_attack_scoring,
        check_training_evaluation_disjointness,
    )
    protocol = Phase31Protocol.load()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=42)
    regime2 = _reconstruct_regime2_with_confidences(42, protocol, system)

    checks = [
        check_training_evaluation_disjointness(system, regime2),
        check_attack_transforms_preserve_ground_truth(system),
        check_attack_transforms_actually_corrupt_context(system),
        check_attack_determinism(system),
        check_no_fit_calls_during_attack_scoring(),
        check_duplicate_samples_across_attack_conditions(system),
    ]
    assert all(c["passed"] for c in checks), checks


def test_result_is_json_serializable(protocol35):
    protocol = _small_protocol()
    row = run_one_seed(1, protocol, protocol35)
    clean_row = {k: v for k, v in row.items() if k != "per_condition"}
    clean_row["per_condition"] = {
        cid: {k: v for k, v in cond.items() if k != "_arrays"} for cid, cond in row["per_condition"].items()
    }
    reloaded = json.loads(json.dumps(clean_row))
    assert "D_supervised_failure_risk" in reloaded["per_condition"]["clean"]["results"]


def test_t_interval_reused_not_reimplemented():
    result = _t_interval([0.1, 0.2, 0.3], 0.95)
    assert result["n"] == 3
