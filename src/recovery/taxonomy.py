"""FROZEN scenario-family taxonomy for Active Phase 4.3.

Frozen before any dataset generation (STEP 3 of the execution order in the
Phase 4.3 brief). Do not add, remove, or reparametrize families/causes
after test generation without a new ``TAXONOMY_VERSION`` and a fresh
protocol freeze -- see ``configs/phase4_3_recovery_protocol.json``.

Four families were selected (of the ~8 suggested in the brief) because each
maps to a failure family already represented, at least descriptively, in
``FailureExperience`` real-data sources (Active Phase 4.1/4.2):

- RESOURCE_EXHAUSTION   <-> Alibaba GPU 2020 (OOM / resource-pressure kills)
- TRANSIENT_FAILURE     <-> AIOps 2020 (transient entity/fault onsets)
- CONFIGURATION_FAILURE <-> AgentRx (behavioral/config-driven agent failure)
- DEPENDENCY_FAILURE    <-> AIOps 2020 (dependency/cascading entity faults)

Families NOT included (infrastructure failure, model/runtime failure,
agent/behavioral failure as a separate family) were dropped because they
would not add a scenario family with a materially different recovery-action
profile from the four above -- see docs/PHASE4_3_RECOVERY_LEARNING.md
section 7 for the audit trail.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.recovery.schema import ActionId, ScenarioFamily

TAXONOMY_VERSION = "phase4_3_taxonomy_v1"


@dataclass(frozen=True)
class CauseProfile:
    """One hidden ground-truth cause within a family, and the noisy
    decision-time symptom distribution it produces. ``p_symptom_a`` is the
    probability the noisy ``symptom_pattern`` observed at decision time
    reads "A" (vs "B") when this cause is the true one -- deliberately
    non-deterministic (max 85%) so the symptom pattern alone cannot be used
    as a lookup key for the cause (Phase 4.3 brief section 16, "avoid
    baked-in answers")."""

    cause_id: str
    p_symptom_a: float
    severity_weights: dict[str, float]  # noisy severity distribution, sums to 1.0


@dataclass(frozen=True)
class FamilySpec:
    family: ScenarioFamily
    causes: tuple[CauseProfile, ...]
    candidate_actions: tuple[ActionId, ...]
    unsafe_actions: tuple[ActionId, ...] = field(default_factory=tuple)
    workload_types: tuple[str, ...] = ("batch", "service", "streaming")


TAXONOMY: dict[ScenarioFamily, FamilySpec] = {
    ScenarioFamily.RESOURCE_EXHAUSTION: FamilySpec(
        family=ScenarioFamily.RESOURCE_EXHAUSTION,
        causes=(
            CauseProfile("memory_leak", p_symptom_a=0.85, severity_weights={"low": 0.10, "medium": 0.30, "high": 0.60}),
            CauseProfile("transient_spike", p_symptom_a=0.20, severity_weights={"low": 0.40, "medium": 0.40, "high": 0.20}),
        ),
        candidate_actions=(ActionId.RETRY, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
    ),
    ScenarioFamily.TRANSIENT_FAILURE: FamilySpec(
        family=ScenarioFamily.TRANSIENT_FAILURE,
        causes=(
            CauseProfile("network_blip", p_symptom_a=0.80, severity_weights={"low": 0.50, "medium": 0.35, "high": 0.15}),
            CauseProfile("dependency_timeout", p_symptom_a=0.30, severity_weights={"low": 0.15, "medium": 0.45, "high": 0.40}),
        ),
        candidate_actions=(ActionId.RETRY, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
    ),
    ScenarioFamily.CONFIGURATION_FAILURE: FamilySpec(
        family=ScenarioFamily.CONFIGURATION_FAILURE,
        causes=(
            CauseProfile("bad_config", p_symptom_a=0.75, severity_weights={"low": 0.20, "medium": 0.40, "high": 0.40}),
            CauseProfile("stale_config", p_symptom_a=0.25, severity_weights={"low": 0.30, "medium": 0.40, "high": 0.30}),
        ),
        candidate_actions=(ActionId.ROLLBACK, ActionId.RECONFIGURE, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
    ),
    ScenarioFamily.DEPENDENCY_FAILURE: FamilySpec(
        family=ScenarioFamily.DEPENDENCY_FAILURE,
        causes=(
            CauseProfile("downstream_outage", p_symptom_a=0.70, severity_weights={"low": 0.05, "medium": 0.25, "high": 0.70}),
            CauseProfile("downstream_degraded", p_symptom_a=0.30, severity_weights={"low": 0.30, "medium": 0.45, "high": 0.25}),
        ),
        candidate_actions=(ActionId.RETRY, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN, ActionId.FORCE_RESTART),
        unsafe_actions=(ActionId.FORCE_RESTART,),
    ),
}


def safe_candidate_actions(family: ScenarioFamily) -> list[ActionId]:
    """Candidate actions minus the family's unsafe action(s) -- what a
    safety-respecting policy is allowed to choose from."""
    spec = TAXONOMY[family]
    return [a for a in spec.candidate_actions if a not in spec.unsafe_actions]
