"""FROZEN recovery-action vocabulary for Active Phase 4.3.

Frozen before policy evaluation (Phase 4.3 brief section 11). Adding an
action here after seeing evaluation results would be a research-integrity
violation (section 38) -- don't.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.recovery.schema import ActionId, SafetyClass

ACTION_VOCABULARY_VERSION = "phase4_3_actions_v1"


@dataclass(frozen=True)
class ActionSpec:
    action_id: ActionId
    description: str
    reversibility: str          # "reversible" | "partially_reversible" | "irreversible"
    safety_classification: SafetyClass
    base_latency_seconds: float  # nominal latency if the action is taken (before outcome-dependent adjustment)
    base_cost: float             # nominal utility cost unit


ACTIONS: dict[ActionId, ActionSpec] = {
    ActionId.RETRY: ActionSpec(
        ActionId.RETRY, "Re-issue the failed operation without changing state.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=5.0, base_cost=1.0,
    ),
    ActionId.RESTART: ActionSpec(
        ActionId.RESTART, "Restart the affected process/container, clearing transient in-memory state.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=30.0, base_cost=3.0,
    ),
    ActionId.ROLLBACK: ActionSpec(
        ActionId.ROLLBACK, "Revert to the last known-good configuration/deployment.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=45.0, base_cost=4.0,
    ),
    ActionId.RECONFIGURE: ActionSpec(
        ActionId.RECONFIGURE, "Apply a targeted configuration correction.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=20.0, base_cost=2.5,
    ),
    ActionId.ESCALATE_TO_HUMAN: ActionSpec(
        ActionId.ESCALATE_TO_HUMAN, "Hand off to a human operator; no automated state change.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=600.0, base_cost=8.0,
    ),
    ActionId.ABSTAIN: ActionSpec(
        ActionId.ABSTAIN, "Take no action; wait and re-observe.",
        reversibility="reversible", safety_classification=SafetyClass.SAFE,
        base_latency_seconds=0.0, base_cost=0.0,
    ),
    ActionId.FORCE_RESTART: ActionSpec(
        ActionId.FORCE_RESTART,
        "Immediately kill and restart the process regardless of in-flight work "
        "(may destroy uncommitted transactions on a dependency-degraded/outage path).",
        reversibility="irreversible", safety_classification=SafetyClass.UNSAFE,
        base_latency_seconds=10.0, base_cost=15.0,
    ),
}


def is_unsafe(action_id: ActionId) -> bool:
    return ACTIONS[action_id].safety_classification == SafetyClass.UNSAFE
