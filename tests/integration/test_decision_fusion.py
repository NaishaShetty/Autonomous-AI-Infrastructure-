"""risk + confidence -> decision, exercised through the real trained
components (small synthetic system), not hand-constructed numbers."""
from __future__ import annotations

from src.decision.policy import DecisionMode, DecisionPolicy, PolicyConfig
from src.pipeline_builder import build_system


def test_all_three_modes_produce_valid_decisions_on_a_trained_system():
    system = build_system(regime_sizes=(300, 150, 150, 150, 150), n_clusters=2, seed=7)
    policy = DecisionPolicy(PolicyConfig())

    sample = system.test_stream[0]
    import numpy as np

    x = np.array([sample.context[f] for f in system.feature_names])
    pred = system.workload_model.predict(x)
    calib_features = {
        **sample.context,
        "predicted_proba": pred.predicted_proba,
        "margin": pred.margin,
        "entropy": pred.entropy,
    }
    calib_result = system.calibrator.predict(calib_features)
    risk = system.failure_memory.risk(sample.context, calib_result.calibrated_confidence)

    for mode in DecisionMode:
        decision, score = policy.decide(calib_result.calibrated_confidence, risk, mode=mode)
        assert decision.value in {"ANSWER", "ABSTAIN", "REVIEW"}
        assert 0.0 <= score <= 1.0


def test_failure_memory_is_actually_fitted_after_build_system():
    system = build_system(regime_sizes=(300, 150, 150, 150, 150), n_clusters=2, seed=7)
    assert system.n_logged_failures > 0
    assert system.failure_memory.is_fitted
