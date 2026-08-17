"""Integration tests for Phase 3.6.3 diagnosis: deterministic rule
correctness, ground-truth-class mapping, and pipeline-level sanity
(dropout is perfectly detectable by construction; the rule never fits
anything)."""
from __future__ import annotations

import pytest

from src.evaluation.diagnosis import DIAGNOSIS_CLASSES, condition_to_true_class, diagnose
from src.data.synthetic import FEATURE_NAMES


def test_dropout_detected_from_two_zeroed_features():
    ctx = {"f1": 1.0, "f2": 0.0, "f3": -1.0, "f4": 0.0, "f5": 0.5}
    assert diagnose(ctx, FEATURE_NAMES) == "feature_dropout"


def test_single_zero_feature_is_not_treated_as_dropout():
    # only one feature is exactly zero (could happen by chance for any
    # continuous distribution with vanishing probability) -- the rule
    # requires >=2 to avoid over-triggering on a coincidental zero.
    ctx = {"f1": 1.0, "f2": 0.0, "f3": -1.0, "f4": 0.3, "f5": 0.5}
    assert diagnose(ctx, FEATURE_NAMES) != "feature_dropout"


def test_high_magnitude_features_detected_as_noise():
    ctx = {"f1": 3.0, "f2": -2.5, "f3": 2.8, "f4": -3.1, "f5": 2.6}  # mean_sq way above 2.0
    assert diagnose(ctx, FEATURE_NAMES) == "feature_noise"


def test_small_magnitude_features_detected_as_clean():
    ctx = {"f1": 0.1, "f2": -0.2, "f3": 0.05, "f4": 0.15, "f5": -0.1}
    assert diagnose(ctx, FEATURE_NAMES) == "clean"


def test_rule_is_pure_deterministic_function():
    ctx = {"f1": 0.9, "f2": -0.4, "f3": 1.2, "f4": -0.6, "f5": 0.3}
    assert diagnose(ctx, FEATURE_NAMES) == diagnose(dict(ctx), FEATURE_NAMES)


def test_condition_to_true_class_mapping():
    assert condition_to_true_class("clean") == "clean"
    assert condition_to_true_class("feature_noise_mild") == "feature_noise"
    assert condition_to_true_class("feature_noise_severe") == "feature_noise"
    assert condition_to_true_class("feature_dropout") == "feature_dropout"


def test_condition_to_true_class_rejects_unknown():
    with pytest.raises(ValueError):
        condition_to_true_class("not_a_real_condition")


def test_diagnosis_classes_match_frozen_protocol():
    import json
    from pathlib import Path
    protocol36 = json.loads((Path(__file__).resolve().parents[2] / "configs" / "phase3_6_decision_recovery_protocol.json").read_text())
    assert protocol36["diagnosis_taxonomy"]["classes"] == DIAGNOSIS_CLASSES


def test_diagnosis_pipeline_evaluates_all_six_seeds():
    from src.evaluation.protocol import Phase31Protocol
    from benchmarks.phase3_5_attack_generalization import load_protocol35
    from benchmarks.phase3_6_diagnosis import run_one_seed

    protocol = Phase31Protocol.load()
    protocol.regime_sizes = (300, 150, 150, 150, 150)
    protocol.seeds = [1, 2]
    protocol35 = load_protocol35()
    rows = [run_one_seed(s, protocol, protocol35) for s in protocol.seeds]
    for row in rows:
        assert row["n_failures"] == len(row["y_true"]) == len(row["y_pred"])
        assert all(c in DIAGNOSIS_CLASSES for c in row["y_pred"])
        assert all(c in DIAGNOSIS_CLASSES for c in row["y_true"])


def test_dropout_condition_pooled_always_correctly_diagnosed():
    """The dropout condition is a fully deterministic corruption (no
    RNG) -- confirms the rule catches 100% of it, matching the reported
    pooled per-class recall of 1.0 for feature_dropout."""
    from src.evaluation.protocol import Phase31Protocol
    from src.pipeline_builder import build_system
    from benchmarks.phase3_5_attack_generalization import _condition_test_samples, load_protocol35

    protocol = Phase31Protocol.load()
    protocol.regime_sizes = (300, 150, 150, 150, 150)
    protocol35 = load_protocol35()
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=1)
    dropout_condition = next(c for c in protocol35["attack_matrix"] if c["id"] == "feature_dropout")
    samples = _condition_test_samples(dropout_condition, 1, system)
    for s in samples:
        assert diagnose(s.context, FEATURE_NAMES) == "feature_dropout"
