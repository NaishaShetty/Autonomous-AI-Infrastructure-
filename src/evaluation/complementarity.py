"""Phase 3.6.1: a simple, pre-specified combination of calibrated
confidence and Supervised Failure Risk.

Per ``configs/phase3_6_decision_recovery_protocol.json.complementarity_
experiment``: a 2-input logistic regression, no hyperparameter search, no
additional features, fit ONCE per seed on regime-2 data only (the same
training-data convention every other supervised candidate in this project
uses -- see ``src/evaluation/representations.py``). This is deliberately
the simplest possible combination, not a tuned ensemble.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass
class CombinedRisk:
    """input = [1 - calibrated_confidence, F.risk(context, confidence)].
    ``is_probability`` mirrors the convention in
    ``src/evaluation/representations.py`` -- a logistic regression's
    predict_proba output is a probability by construction."""

    random_state: int = 42
    is_probability: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        self._clf: LogisticRegression | None = None
        self._fitted = False

    def fit(self, b_scores: list[float], f_scores: list[float], is_failure: list[int]) -> "CombinedRisk":
        X = np.column_stack([np.asarray(b_scores, dtype=float), np.asarray(f_scores, dtype=float)])
        y = np.asarray(is_failure, dtype=int)
        if len(np.unique(y)) < 2:
            self._fitted = False
            return self
        self._clf = LogisticRegression(max_iter=1000, random_state=self.random_state)
        self._clf.fit(X, y)
        self._fitted = True
        return self

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def risk(self, b_score: float, f_score: float) -> float:
        if not self._fitted or self._clf is None:
            return 0.0
        x = np.array([[b_score, f_score]], dtype=float)
        return float(self._clf.predict_proba(x)[0, 1])
