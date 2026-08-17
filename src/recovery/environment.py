"""Deterministic scenario generator + state-transition environment for
Active Phase 4.3.

Chosen environment class (Phase 4.3 brief section 14): **static labeled
episodes over a deterministic single-decision state-transition function**
-- not an interactive multi-step simulator. A recovery decision in the
frozen scenario taxonomy is a single (failure state -> action -> validated
outcome) transition; nothing in the frozen research question requires
multi-step planning, so a heavier interactive simulator was not built
(brief section 39: don't over-engineer).

LEAKAGE BOUNDARY (enforced by module layout, checked by
tests/recovery/test_leakage.py and benchmarks/phase4_3_recovery_leakage_audit.py):
``generate_scenario`` returns a ``RecoveryScenario`` whose ``hidden_cause``
and whose ground-truth ``_OUTCOME_TABLE`` (this module) are never passed to
anything in ``src.recovery.policy``. Policies only ever receive
``scenario.decision_context`` (a ``DecisionContext``, which has no
``hidden_cause`` field at all -- pydantic ``extra="forbid"``).
"""
from __future__ import annotations

import hashlib
import random

from src.recovery.actions import is_unsafe
from src.recovery.schema import (
    ActionId,
    DecisionContext,
    RecoveryScenario,
    ScenarioFamily,
    Transition,
    ValidatedOutcome,
)
from src.recovery.taxonomy import TAXONOMY, TAXONOMY_VERSION
from src.recovery.validation import VALIDATION_WINDOW_SECONDS

GENERATOR_VERSION = "phase4_3_generator_v1"

# Ground truth P(outcome | family, hidden_cause, action) for SAFE actions
# other than ABSTAIN/ESCALATE_TO_HUMAN, which have their own rules below.
# NEVER imported by src.recovery.policy. Each tuple is (p_success, p_partial);
# p_failure = 1 - p_success - p_partial.
_OUTCOME_TABLE: dict[tuple[str, str, str], tuple[float, float]] = {
    # RESOURCE_EXHAUSTION
    ("resource_exhaustion", "memory_leak", "retry"): (0.05, 0.10),
    ("resource_exhaustion", "memory_leak", "restart"): (0.85, 0.10),
    ("resource_exhaustion", "memory_leak", "abstain"): (0.05, 0.00),
    ("resource_exhaustion", "transient_spike", "retry"): (0.75, 0.10),
    ("resource_exhaustion", "transient_spike", "restart"): (0.60, 0.15),
    ("resource_exhaustion", "transient_spike", "abstain"): (0.20, 0.00),
    # TRANSIENT_FAILURE
    ("transient_failure", "network_blip", "retry"): (0.80, 0.10),
    ("transient_failure", "network_blip", "restart"): (0.50, 0.20),
    ("transient_failure", "network_blip", "abstain"): (0.30, 0.00),
    ("transient_failure", "dependency_timeout", "retry"): (0.35, 0.20),
    ("transient_failure", "dependency_timeout", "restart"): (0.30, 0.15),
    ("transient_failure", "dependency_timeout", "abstain"): (0.10, 0.00),
    # CONFIGURATION_FAILURE
    ("configuration_failure", "bad_config", "reconfigure"): (0.85, 0.10),
    ("configuration_failure", "bad_config", "rollback"): (0.55, 0.15),
    ("configuration_failure", "bad_config", "restart"): (0.05, 0.05),
    ("configuration_failure", "bad_config", "abstain"): (0.05, 0.00),
    ("configuration_failure", "stale_config", "rollback"): (0.85, 0.10),
    ("configuration_failure", "stale_config", "reconfigure"): (0.55, 0.15),
    ("configuration_failure", "stale_config", "restart"): (0.05, 0.00),
    ("configuration_failure", "stale_config", "abstain"): (0.05, 0.00),
    # DEPENDENCY_FAILURE (force_restart is UNSAFE, handled separately, not here)
    ("dependency_failure", "downstream_outage", "retry"): (0.05, 0.05),
    ("dependency_failure", "downstream_outage", "abstain"): (0.10, 0.00),
    ("dependency_failure", "downstream_degraded", "retry"): (0.55, 0.20),
    ("dependency_failure", "downstream_degraded", "abstain"): (0.15, 0.00),
}


def _scenario_id(family: ScenarioFamily, seed: int) -> str:
    raw = f"phase4_3|{GENERATOR_VERSION}|{family.value}|{seed}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def generate_scenario(family: ScenarioFamily, seed: int) -> RecoveryScenario:
    """Deterministic given (family, seed) -- the same seed always yields the
    exact same scenario, including the same noisy symptom draw. The
    generator is independent of any recovery policy: it is called once per
    seed with no knowledge of which policy will later be evaluated (brief
    section 15, "generator must not know which policy will be evaluated")."""
    rng = random.Random(seed)
    spec = TAXONOMY[family]

    cause = spec.causes[rng.randrange(len(spec.causes))]
    symptom_pattern = "A" if rng.random() < cause.p_symptom_a else "B"

    sev_names = list(cause.severity_weights.keys())
    sev_weights = list(cause.severity_weights.values())
    severity = rng.choices(sev_names, weights=sev_weights, k=1)[0]

    workload_type = spec.workload_types[rng.randrange(len(spec.workload_types))]

    scenario_id = _scenario_id(family, seed)
    episode_id = scenario_id  # 1:1 for this environment (single decision per episode)

    decision_context = DecisionContext(
        scenario_id=scenario_id,
        episode_id=episode_id,
        family=family,
        symptom_pattern=symptom_pattern,
        severity=severity,
        workload_type=workload_type,
        candidate_actions=list(spec.candidate_actions),
    )
    return RecoveryScenario(
        scenario_id=scenario_id,
        family=family,
        hidden_cause=cause.cause_id,
        decision_context=decision_context,
        seed=seed,
        generator_version=GENERATOR_VERSION,
        scenario_taxonomy_version=TAXONOMY_VERSION,
    )


def transition(scenario: RecoveryScenario, action: ActionId) -> Transition:
    """Deterministic-given-(scenario.seed, action) outcome. Never called
    before a policy has already committed to ``action`` -- this function,
    and the ground-truth table it reads, are the ONLY things in this
    package allowed to see ``scenario.hidden_cause``."""
    spec = TAXONOMY[scenario.family]
    action_rng = random.Random(hash((scenario.seed, action.value)) & 0xFFFFFFFF)

    if is_unsafe(action):
        return Transition(
            outcome=ValidatedOutcome.UNSAFE,
            unsafe_action_taken=True,
            recovery_latency_seconds=10.0,
            recovery_cost=45.0,
            validation_window_seconds=VALIDATION_WINDOW_SECONDS,
            partial=False,
        )

    if action == ActionId.ESCALATE_TO_HUMAN:
        return Transition(
            outcome=ValidatedOutcome.TIMEOUT,
            unsafe_action_taken=False,
            recovery_latency_seconds=VALIDATION_WINDOW_SECONDS,
            recovery_cost=8.0,
            validation_window_seconds=VALIDATION_WINDOW_SECONDS,
            partial=False,
        )

    if action not in spec.candidate_actions:
        raise ValueError(f"{action} is not a candidate action for family {scenario.family}")

    key = (scenario.family.value, scenario.hidden_cause, action.value)
    p_success, p_partial = _OUTCOME_TABLE[key]
    draw = action_rng.random()
    if draw < p_success:
        outcome, partial = ValidatedOutcome.SUCCESS, False
    elif draw < p_success + p_partial:
        outcome, partial = ValidatedOutcome.PARTIAL_SUCCESS, True
    else:
        outcome, partial = ValidatedOutcome.FAILURE, False

    latency = max(0.5, action_rng.gauss(_nominal_latency(action), 2.0))
    cost = max(0.1, action_rng.gauss(_nominal_cost(action), 0.5))
    return Transition(
        outcome=outcome,
        unsafe_action_taken=False,
        recovery_latency_seconds=latency,
        recovery_cost=cost,
        validation_window_seconds=VALIDATION_WINDOW_SECONDS,
        partial=partial,
    )


def _nominal_latency(action: ActionId) -> float:
    from src.recovery.actions import ACTIONS
    return ACTIONS[action].base_latency_seconds


def _nominal_cost(action: ActionId) -> float:
    from src.recovery.actions import ACTIONS
    return ACTIONS[action].base_cost


def oracle_best_action(scenario: RecoveryScenario) -> ActionId:
    """Reference upper bound ONLY -- uses ``hidden_cause`` directly and must
    never be used as a policy input or a competing baseline (brief section
    22: "if an oracle exists, use it as an upper/reference bound rather
    than a competitor"). Restricted to safe candidate actions."""
    spec = TAXONOMY[scenario.family]
    best_action, best_p = None, -1.0
    for action in spec.candidate_actions:
        if is_unsafe(action) or action == ActionId.ESCALATE_TO_HUMAN:
            continue
        key = (scenario.family.value, scenario.hidden_cause, action.value)
        if key not in _OUTCOME_TABLE:
            continue
        p_success, _ = _OUTCOME_TABLE[key]
        if p_success > best_p:
            best_action, best_p = action, p_success
    return best_action or ActionId.ESCALATE_TO_HUMAN
