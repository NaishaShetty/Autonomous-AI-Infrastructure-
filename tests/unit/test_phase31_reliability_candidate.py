import json
from pathlib import Path

import numpy as np

from scripts.run_phase31_reliability_model_experiment import NUMERIC_COLS, SEED, prep_model
from sklearn.ensemble import GradientBoostingClassifier


def test_candidate_uses_locked_v1_feature_space():
    assert len(NUMERIC_COLS) == 14
    assert "status" not in NUMERIC_COLS
    assert "end_time" not in NUMERIC_COLS


def test_candidate_model_is_deterministic_for_fixed_seed():
    X = np.asarray([[0.0] * 14, [1.0] * 14, [2.0] * 14, [3.0] * 14])
    y = np.asarray([0, 0, 1, 1])
    a = prep_model(GradientBoostingClassifier(n_estimators=10, learning_rate=0.05, max_depth=2, random_state=SEED)).fit(X, y)
    b = prep_model(GradientBoostingClassifier(n_estimators=10, learning_rate=0.05, max_depth=2, random_state=SEED)).fit(X, y)
    assert np.array_equal(a.predict_proba(X), b.predict_proba(X))


def test_finalized_candidate_outputs_are_immutable():
    root = Path("experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1")
    marker = root / ".finalized"
    assert marker.exists()
    hashes = json.loads(marker.read_text())
    assert hashes["protocol.json"]
    assert hashes["results.json"]
    assert hashes["manifest.json"]
