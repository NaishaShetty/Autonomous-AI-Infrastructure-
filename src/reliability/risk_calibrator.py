"""Offline-fitted risk calibration with runtime-compatible confidence output."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression


@dataclass(frozen=True)
class RiskCalibration:
    raw_confidence: float
    calibrated_confidence: float
    raw_risk: float
    calibrated_risk: float


class IsotonicRiskCalibrator:
    """Calibrate positive failure risk on a disjoint validation set only."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self._iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self._fitted = False

    def fit_validation(self, risk_values: list[float], labels: list[int]) -> "IsotonicRiskCalibrator":
        if len(risk_values) != len(labels) or len(risk_values) < 2:
            raise ValueError("validation risks and labels must have equal length >= 2")
        if len(set(int(v) for v in labels)) < 2:
            raise ValueError("validation labels must contain both classes")
        self._iso.fit(np.asarray(risk_values, dtype=float), np.asarray(labels, dtype=float))
        self._fitted = True
        return self

    def calibrate_risk(self, risk: float) -> float:
        if not self._fitted:
            raise RuntimeError("IsotonicRiskCalibrator must be fit_validation() before prediction")
        return float(np.clip(self._iso.predict([float(risk)])[0], 0.0, 1.0))

    def predict(self, features: dict) -> RiskCalibration:
        if not self._fitted:
            raise RuntimeError("IsotonicRiskCalibrator must be fit_validation() before prediction")
        predicted_label = int(features.get("predicted_label", 0))
        predicted_proba = float(np.clip(features.get("predicted_proba", 0.5), 0.0, 1.0))
        raw_risk = 1.0 - predicted_proba if predicted_label == 1 else predicted_proba
        calibrated_risk = self.calibrate_risk(raw_risk)
        calibrated_confidence = 1.0 - calibrated_risk if predicted_label == 1 else calibrated_risk
        return RiskCalibration(1.0 - raw_risk, calibrated_confidence, raw_risk, calibrated_risk)
