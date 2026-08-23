"""Phase 4.4 -- concrete ``DecisionPolicyPort`` implementation with abstention.

Closes the gap named in ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` section 3.3: the
project names the AI Abstention Engine as a core foundation, but a repo-wide
search found zero occurrences of "abstention"/"Abstain" in ``src/phase4/``
before this change, and ``DecisionPolicyPort`` had no implementation.

Per Decision A of that plan, this module does not re-derive abstention logic.
It wraps the existing, tested, frozen ``src.decision.policy.DecisionPolicy``
-- "the single authoritative decision policy" (see that module's own
docstring) -- rather than building a second one. The only new work here is
the adapter that maps a Phase 4 ``Prediction`` (a single engineered risk
score, since Phase 4 has no separate calibrated-confidence signal -- see
``src/phase4/prediction.py``) onto that policy's ``RISK_ONLY`` mode, and maps
its ``Decision`` output onto ``AutonomyState`` transitions.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.decision.policy import Decision as PolicyDecision
from src.decision.policy import DecisionMode, DecisionPolicy, PolicyConfig
from .architecture import AutonomyState, Prediction

DECISION_ADAPTER_VERSION = "phase4.4-decision-abstention-v1"


@dataclass(frozen=True)
class AutonomyDecision:
    decision: str
    fused_score: float
    next_state: str
    rationale: str
    policy_version: str = DECISION_ADAPTER_VERSION


class AbstentionAwareDecisionPolicy:
    """Concrete ``DecisionPolicyPort`` implementation (see ``architecture.DecisionPolicyPort``)."""

    def __init__(self, config: PolicyConfig | None = None):
        self._policy = DecisionPolicy(config or PolicyConfig())

    def decide(self, prediction: Prediction) -> AutonomyDecision:
        policy_decision, score = self._policy.decide(confidence=None, risk=prediction.score, mode=DecisionMode.RISK_ONLY)
        if policy_decision == PolicyDecision.ANSWER:
            return AutonomyDecision(
                decision="ANSWER",
                fused_score=score,
                next_state=AutonomyState.DIAGNOSING.value,
                rationale=f"predicted risk {prediction.score:.3f} is low enough to trust autonomous diagnosis/recovery for this incident",
            )
        if policy_decision == PolicyDecision.ABSTAIN:
            return AutonomyDecision(
                decision="ABSTAIN",
                fused_score=score,
                next_state=AutonomyState.ABSTAINED.value,
                rationale=f"predicted risk {prediction.score:.3f} is high enough that autonomous action is not justified; abstaining rather than guessing",
            )
        return AutonomyDecision(
            decision="REVIEW",
            fused_score=score,
            next_state=AutonomyState.ESCALATED.value,
            rationale=f"predicted risk {prediction.score:.3f} is in the uncertain band; escalating to a human rather than acting autonomously",
        )
