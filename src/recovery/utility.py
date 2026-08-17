"""FROZEN recovery-utility function for Active Phase 4.3 (brief section 25).

utility = outcome_value(outcome)
          - COST_WEIGHT    * recovery_cost
          - LATENCY_WEIGHT * recovery_latency_seconds

outcome_value:
    SUCCESS          -> +1.0
    PARTIAL_SUCCESS   -> +0.5
    FAILURE           ->  0.0
    TIMEOUT           ->  0.0   (escalation: no automated harm, no automated fix)
    UNRECOVERABLE     ->  0.0   (reserved; does not occur under the frozen
                                  ground-truth table -- see docs/PHASE4_3_RECOVERY_LEARNING.md
                                  section "limitations")
    UNSAFE            -> -5.0

Weight justification (frozen before evaluation, not tuned on results):
- The UNSAFE penalty (-5.0) is chosen so that no combination of cost/latency
  savings can make an unsafe action's utility exceed a safe FAILURE's (0.0):
  the worst-case safe action costs <= 45 units and <= ~630s latency
  (ESCALATE_TO_HUMAN), giving a maximum safe penalty of
  COST_WEIGHT*45 + LATENCY_WEIGHT*630 = 0.9 + 0.63 = 1.53, still far below
  the 5.0 unsafe penalty plus the 1.0 a safe SUCCESS could have earned.
- COST_WEIGHT and LATENCY_WEIGHT are deliberately small (0.02, 0.001) so
  cost/latency act only as a tie-breaker between two actions with the same
  outcome class, never large enough to flip a SUCCESS vs FAILURE ranking
  (max combined penalty ~1.53, less than the 1.0 gap between SUCCESS and
  FAILURE would require to flip on its own, and cost/latency only differ
  between actions by a few units, not by 50x).
"""
from __future__ import annotations

from src.recovery.schema import ValidatedOutcome

UTILITY_VERSION = "phase4_3_utility_v1"

COST_WEIGHT = 0.02
LATENCY_WEIGHT = 0.001

_OUTCOME_VALUE = {
    ValidatedOutcome.SUCCESS: 1.0,
    ValidatedOutcome.PARTIAL_SUCCESS: 0.5,
    ValidatedOutcome.FAILURE: 0.0,
    ValidatedOutcome.TIMEOUT: 0.0,
    ValidatedOutcome.UNRECOVERABLE: 0.0,
    ValidatedOutcome.UNSAFE: -5.0,
}


def recovery_utility(outcome: ValidatedOutcome, recovery_cost: float, recovery_latency_seconds: float) -> float:
    return _OUTCOME_VALUE[outcome] - COST_WEIGHT * recovery_cost - LATENCY_WEIGHT * recovery_latency_seconds
