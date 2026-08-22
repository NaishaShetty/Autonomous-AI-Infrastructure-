"""Serializable structured workload-risk model used by offline reliability artifacts."""
from __future__ import annotations

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .workload_model import WorkloadPrediction


class EncodedWorkloadRiskModel:
    """Deterministic logistic model with train-fitted preprocessing."""

    def __init__(self, feature_names: list[str], random_state: int = 42):
        self.feature_names = list(feature_names)
        self.random_state = random_state
        self._imputer = SimpleImputer(strategy="median")
        self._scaler = StandardScaler()
        self._clf = LogisticRegression(max_iter=2000, random_state=random_state)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EncodedWorkloadRiskModel":
        transformed = self._scaler.fit_transform(self._imputer.fit_transform(np.asarray(X, dtype=float)))
        self._clf.fit(transformed, np.asarray(y, dtype=int))
        self._fitted = True
        return self

    def _proba(self, x: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("EncodedWorkloadRiskModel must be fit() before prediction")
        transformed = self._scaler.transform(self._imputer.transform(np.asarray(x, dtype=float).reshape(1, -1)))
        return self._clf.predict_proba(transformed)[0]

    def predict_failure_risk(self, x: np.ndarray) -> float:
        return float(self._proba(x)[1])

    def predict(self, x: np.ndarray) -> WorkloadPrediction:
        proba = self._proba(x)
        predicted_label = int(np.argmax(proba))
        p1 = float(proba[1])
        margin = abs(p1 - 0.5) * 2.0
        eps = 1e-9
        entropy = -(p1 * np.log2(p1 + eps) + (1 - p1) * np.log2(1 - p1 + eps))
        return WorkloadPrediction(predicted_label, float(proba[predicted_label]), float(margin), float(np.clip(entropy, 0.0, 1.0)))
