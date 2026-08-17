"""The monitored workload: a simple classifier standing in for "the AI/ML
model being made reliable". This plays the role that an LLM played in the
Abstention Engine and that the synthetic classifier played in the Failure
Memory model -- Phase 2 keeps it intentionally simple (logistic regression
over structured features) because the research question is about the
reliability/failure-memory layer *around* a model, not about the model
itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass
class WorkloadPrediction:
    predicted_label: int
    predicted_proba: float  # probability assigned to the predicted class
    margin: float  # |p - 0.5| * 2, in [0, 1]
    entropy: float  # binary entropy of the predicted distribution, in [0, 1]


class WorkloadModel:
    """Thin wrapper around a binary classifier plus derived uncertainty
    features. Any scikit-learn-compatible classifier could be substituted;
    logistic regression is used for a fast, deterministic Phase 2 baseline.
    """

    def __init__(self, random_state: int = 42):
        self._clf = LogisticRegression(max_iter=1000, random_state=random_state)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "WorkloadModel":
        self._clf.fit(X, y)
        self._fitted = True
        return self

    def predict(self, x: np.ndarray) -> WorkloadPrediction:
        if not self._fitted:
            raise RuntimeError("WorkloadModel must be fit() before predict()")
        proba = self._clf.predict_proba(x.reshape(1, -1))[0]
        predicted_label = int(np.argmax(proba))
        p1 = float(proba[1])
        margin = abs(p1 - 0.5) * 2.0
        eps = 1e-9
        entropy = -(p1 * np.log2(p1 + eps) + (1 - p1) * np.log2(1 - p1 + eps))
        return WorkloadPrediction(
            predicted_label=predicted_label,
            predicted_proba=float(proba[predicted_label]),
            margin=float(margin),
            entropy=float(np.clip(entropy, 0.0, 1.0)),
        )
