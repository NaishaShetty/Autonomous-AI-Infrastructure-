import numpy as np

from src.reliability.calibrator import ConfidenceCalibrator
from src.reliability.workload_model import WorkloadModel


def _synthetic_features_and_correctness(n=800, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 3))
    w = np.array([2.0, -1.0, 0.5])
    p_correct = 1.0 / (1.0 + np.exp(-(X @ w)))
    correct = (rng.random(n) < p_correct).astype(int)
    feature_dicts = [{"f1": x[0], "f2": x[1], "f3": x[2]} for x in X]
    return feature_dicts, correct.tolist()


def test_predict_before_fit_raises():
    calibrator = ConfidenceCalibrator(["f1", "f2", "f3"])
    try:
        calibrator.predict({"f1": 0.0, "f2": 0.0, "f3": 0.0})
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_calibrated_confidence_is_always_in_unit_interval():
    feature_dicts, correct = _synthetic_features_and_correctness()
    calibrator = ConfidenceCalibrator(["f1", "f2", "f3"]).fit(feature_dicts, correct)
    for fd in feature_dicts[:20]:
        result = calibrator.predict(fd)
        assert 0.0 <= result.raw_confidence <= 1.0
        assert 0.0 <= result.calibrated_confidence <= 1.0


def test_calibration_correlates_with_actual_correctness():
    """Not a tight numeric bound (this is a statistical model on synthetic
    data), just a sanity check that the learned signal carries real
    information: samples in the top confidence quartile should be correct
    more often than samples in the bottom quartile."""
    feature_dicts, correct = _synthetic_features_and_correctness(n=1500, seed=1)
    calibrator = ConfidenceCalibrator(["f1", "f2", "f3"]).fit(feature_dicts, correct)

    confidences = np.array([calibrator.predict(fd).calibrated_confidence for fd in feature_dicts])
    correct_arr = np.array(correct)
    order = np.argsort(confidences)
    low_quartile = correct_arr[order[: len(order) // 4]]
    high_quartile = correct_arr[order[-len(order) // 4 :]]
    assert high_quartile.mean() > low_quartile.mean()


def test_workload_model_predict_shapes():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = WorkloadModel().fit(X, y)
    pred = model.predict(X[0])
    assert 0.0 <= pred.predicted_proba <= 1.0
    assert 0.0 <= pred.margin <= 1.0
    assert 0.0 <= pred.entropy <= 1.0
    assert pred.predicted_label in (0, 1)
