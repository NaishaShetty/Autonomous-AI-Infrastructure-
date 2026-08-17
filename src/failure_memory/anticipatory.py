"""EXPERIMENTAL -- anticipatory (recency-weighted) risk adjustment.

Phase 1 found the source ``anticipatory_confidence.py`` to be "a
fixed-coefficient heuristic, not a trained predictive model" with "no
metric anywhere in either repo proving the anticipatory-risk heuristic
actually predicts failures before they occur" (PHASE1_AUDIT_REPORT.md
sections 3, 11).

Per the Phase 2 brief (section 2.6), this idea is preserved but explicitly
NOT wired into the default decision policy, NOT used in the Baseline
A/B/C comparison, and NOT presented as a validated predictor. It is kept
here, isolated, so a future phase can evaluate it properly (define a
predictive-accuracy metric, e.g. AUROC of anticipated risk vs. actual
near-term failure occurrence, before considering it for the live policy).

Do not import this module from ``src/decision`` or ``src/api``.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AnticipatoryRiskEstimator:
    """Discounts a risk score by recent per-cluster failure activity.

    EXPERIMENTAL: coefficients below (``beta``, ``activity_cap``) are
    inherited unchanged from the source prototype and have not been
    validated against any held-out predictive-accuracy metric in this
    project. Do not use for safety-critical decisions.
    """

    beta: float = 0.4
    activity_cap: int = 10
    _cluster_activity: dict[int, int] = field(default_factory=dict)

    def record_cluster_hit(self, cluster_id: int) -> None:
        self._cluster_activity[cluster_id] = self._cluster_activity.get(cluster_id, 0) + 1

    def adjust(self, base_risk: float, cluster_id: int | None) -> float:
        if cluster_id is None:
            return base_risk
        activity = self._cluster_activity.get(cluster_id, 0)
        activity_factor = min(activity / self.activity_cap, 1.0)
        adjusted = base_risk + self.beta * activity_factor * (1.0 - base_risk)
        return float(min(max(adjusted, 0.0), 1.0))
