"""Calibrated confidence estimation.

This migrates the one component Phase 1 identified as genuinely reusable
from the AI-Abstention-Engine: structured features -> a classifier -> an
isotonic-regression calibration step (PHASE1_AUDIT_REPORT.md section 7,
"ReliabilityCalibrator ... Reuse with caveats").

Deliberate deviation from the source implementation: the original also fed a
DeBERTa-v3 text embedding into the classifier. Phase 1 found that this made
the very first request pay for a synchronous Hugging Face model download and
in-request XGBoost fit, and made "reproducibility" depend on network access
to an external model host (PHASE1_AUDIT_REPORT.md section 5, "Silent no-op
ML calibrator by default"). Because Phase 2's workloads are structured
(numeric-feature) classification tasks, not open-ended NL queries, the text
embedding has no input to act on anyway. It is dropped rather than migrated;
if a future phase adds NL workloads, a text-embedding feature branch can be
added back behind the same interface without changing callers.

Output confidence is unconditionally in [0.0, 1.0] -- see
``src/schema/events.py`` for why that invariant matters.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import train_test_split


@dataclass
class CalibrationResult:
    raw_confidence: float
    calibrated_confidence: float


class ConfidenceCalibrator:
    """Predicts P(the workload model's prediction is correct | features),
    calibrated so that among events assigned calibrated confidence ~c, the
    empirical correct rate is ~c.
    """

    def __init__(self, feature_names: list[str], random_state: int = 42):
        self.feature_names = list(feature_names)
        self.random_state = random_state
        self._clf = GradientBoostingClassifier(
            n_estimators=100, max_depth=3, random_state=random_state
        )
        self._isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self._fitted = False

    def _vectorize(self, features: dict[str, float]) -> np.ndarray:
        return np.array([features.get(name, 0.0) for name in self.feature_names], dtype=float)

    def fit(self, feature_dicts: list[dict[str, float]], correct: list[int]) -> "ConfidenceCalibrator":
        X = np.stack([self._vectorize(f) for f in feature_dicts])
        y = np.asarray(correct, dtype=int)

        X_train, X_calib, y_train, y_calib = train_test_split(
            X, y, test_size=0.3, random_state=self.random_state, stratify=y
        )
        self._clf.fit(X_train, y_train)

        raw_calib = self._clf.predict_proba(X_calib)[:, 1]
        self._isotonic.fit(raw_calib, y_calib)
        self._fitted = True
        return self

    def predict(self, features: dict[str, float]) -> CalibrationResult:
        if not self._fitted:
            raise RuntimeError("ConfidenceCalibrator must be fit() before predict()")
        x = self._vectorize(features).reshape(1, -1)
        raw = float(self._clf.predict_proba(x)[0, 1])
        calibrated = float(np.clip(self._isotonic.predict([raw])[0], 0.0, 1.0))
        return CalibrationResult(raw_confidence=raw, calibrated_confidence=calibrated)
