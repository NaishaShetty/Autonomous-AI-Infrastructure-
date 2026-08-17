"""The single authoritative decision policy.

Phase 1 found the source Abstention Engine implemented 10 overlapping
"abstention strategies" that were mostly cosmetic re-weightings of the same
few signals, plus a second, dead "compatibility shim" abstention function
with no live callers (PHASE1_AUDIT_REPORT.md sections 2, 7). This module
replaces both with one policy, operating exclusively on the canonical
0-1 confidence representation from ``src/schema/events.py``.

The same policy class serves all three Phase 2 evaluation systems
(``benchmarks/run_baselines.py``): Baseline A (confidence only), Baseline B
(failure-memory risk only) and System C (combined) select the fusion
strategy via ``DecisionMode`` -- the threshold logic itself is identical
across all three, so a difference in outcome measures a difference in the
*input signal*, not a difference in policy plumbing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

from src.schema.events import Decision


class DecisionMode(str, Enum):
    CONFIDENCE_ONLY = "confidence_only"  # Baseline A
    RISK_ONLY = "risk_only"  # Baseline B
    COMBINED = "combined"  # System C


@dataclass
class PolicyConfig:
    """All thresholds/weights in one place, loadable from
    ``configs/policy.yaml``-style config rather than hardcoded per call site
    (the Phase 1 audit's specific complaint about the source repos)."""

    answer_threshold: float = 0.70
    abstain_threshold: float = 0.40
    risk_weight: float = 0.50  # only used in COMBINED mode

    def __post_init__(self) -> None:
        if not 0.0 <= self.abstain_threshold <= self.answer_threshold <= 1.0:
            raise ValueError(
                "require 0 <= abstain_threshold <= answer_threshold <= 1, got "
                f"abstain_threshold={self.abstain_threshold}, answer_threshold={self.answer_threshold}"
            )
        if not 0.0 <= self.risk_weight <= 1.0:
            raise ValueError(f"risk_weight must be in [0, 1], got {self.risk_weight}")

    @classmethod
    def from_json(cls, path: str | Path) -> "PolicyConfig":
        data = json.loads(Path(path).read_text())
        return cls(**data)


class DecisionPolicy:
    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()

    def fuse(
        self,
        confidence: float | None,
        risk: float | None,
        mode: DecisionMode = DecisionMode.COMBINED,
    ) -> float:
        """Return a single [0, 1] "trustworthiness" score from the
        available signal(s), per the requested mode."""
        if mode == DecisionMode.CONFIDENCE_ONLY:
            if confidence is None:
                raise ValueError("CONFIDENCE_ONLY mode requires a confidence value")
            return float(np.clip(confidence, 0.0, 1.0))

        if mode == DecisionMode.RISK_ONLY:
            if risk is None:
                raise ValueError("RISK_ONLY mode requires a risk value")
            return float(np.clip(1.0 - risk, 0.0, 1.0))

        # COMBINED: calibrated confidence discounted by historical failure risk.
        c = confidence if confidence is not None else 0.0
        r = risk if risk is not None else 0.0
        return float(np.clip(c - self.config.risk_weight * r, 0.0, 1.0))

    def decide(
        self,
        confidence: float | None,
        risk: float | None,
        mode: DecisionMode = DecisionMode.COMBINED,
    ) -> tuple[Decision, float]:
        """Returns (decision, fused_score). Same threshold rule for every
        mode: score >= answer_threshold -> ANSWER, score < abstain_threshold
        -> ABSTAIN, otherwise -> REVIEW."""
        score = self.fuse(confidence, risk, mode)
        if score >= self.config.answer_threshold:
            return Decision.ANSWER, score
        if score < self.config.abstain_threshold:
            return Decision.ABSTAIN, score
        return Decision.REVIEW, score
