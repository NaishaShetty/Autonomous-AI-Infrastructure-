"""Deterministic 2-step scenario generator + state-transition environment
for Active Phase 4.4 (Sequential Recovery with Abstention).

Does NOT modify ``src.recovery.environment`` -- Phase 4.3's frozen
artifact. Reuses (imports, never edits) its taxonomy, action vocabulary,
and outcome table so the two phases stay on identical ground-truth
recovery-probability assumptions; the only new mechanics here are the
2-step budget, the noisy step-1 observation, and per-step RNG namespacing.

SEEDING: uses the SAME corrected pattern Phase 4.3 landed on after fixing
the hash()-nondeterminism bug -- ``random.Random(f"{seed}|...")``, a
string seed hashed by Python's fixed, PYTHONHASHSEED-independent internal
algorithm, NEVER the builtin ``hash()`` on a string/tuple (which is
randomized per-process unless PYTHONHASHSEED is pinned). Step 1 and step 2
draws are namespaced separately (``step1``/``step2`` in the seed string)
so choosing the same action at both steps does not silently reuse the same
draw.

LEAKAGE BOUNDARY: ``generate_scenario_v2`` returns a ``RecoveryScenarioV2``
whose ``hidden_cause`` is never passed to anything in
``src.recovery.policy_v2``. Policies only ever receive a
``DecisionContextV2`` (schema_v2.py, ``extra="forbid"``, no ``hidden_cause``
field declared).
"""
from __future__ import annotations

import random

from src.recovery.actions import ACTIONS, is_unsafe
from src.recovery.environment import _OUTCOME_TABLE, oracle_best_action as _oracle_best_action_v1
from src.recovery.schema import ActionId, ScenarioFamily, ValidatedOutcome
from src.recovery.schema_v2 import (
    ActionSelectionV2,
    DecisionContextV2,
    EpisodeOutcomeClass,
    ObservationSignal,
    RecoveryScenarioV2,
    StepTransition,
)
from src.recovery.taxonomy import TAXONOMY, TAXONOMY_VERSION
from src.recovery.validation import VALIDATION_WINDOW_SECONDS

GENERATOR_V2_VERSION = "phase4_4_generator_v1"
STEP_BUDGET = 2


def _scenario_id(family: ScenarioFamily, seed: int) -> str:
    import hashlib
    raw = f"phase4_4|{GENERATOR_V2_VERSION}|{family.value}|{seed}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def generate_scenario_v2(family: ScenarioFamily, seed: int) -> RecoveryScenarioV2:
    """Deterministic given (family, seed). Same generative model as Phase
    4.3's ``generate_scenario`` (same taxonomy, same noisy symptom/severity
    draw) -- only the wrapping into a step-1 ``DecisionContextV2`` differs."""
    rng = random.Random(seed)
    spec = TAXONOMY[family]

    cause = spec.causes[rng.randrange(len(spec.causes))]
    symptom_pattern = "A" if rng.random() < cause.p_symptom_a else "B"

    sev_names = list(cause.severity_weights.keys())
    sev_weights = list(cause.severity_weights.values())
    severity = rng.choices(sev_names, weights=sev_weights, k=1)[0]

    workload_type = spec.workload_types[rng.randrange(len(spec.workload_types))]

    scenario_id = _scenario_id(family, seed)
    episode_id = scenario_id

    step1_context = DecisionContextV2(
        scenario_id=scenario_id,
        episode_id=episode_id,
        family=family,
        symptom_pattern=symptom_pattern,
        severity=severity,
        workload_type=workload_type,
        candidate_actions=list(spec.candidate_actions),
        step=1,
    )
    return RecoveryScenarioV2(
        scenario_id=scenario_id,
        family=family,
        hidden_cause=cause.cause_id,
        step1_context=step1_context,
        seed=seed,
        generator_version=GENERATOR_V2_VERSION,
        scenario_taxonomy_version=TAXONOMY_VERSION,
    )


def _nominal_latency(action: ActionId) -> float:
    return ACTIONS[action].base_latency_seconds


def _nominal_cost(action: ActionId) -> float:
    return ACTIONS[action].base_cost


def _resolve_action_outcome(scenario: RecoveryScenarioV2, action: ActionId, step: int) -> StepTransition:
    """Resolve one action at one step, deterministic given
    (scenario.seed, step, action). Reuses Phase 4.3's frozen ground-truth
    ``_OUTCOME_TABLE`` (imported, not duplicated) -- this function and the
    table it reads are the ONLY things in this module allowed to see
    ``scenario.hidden_cause``."""
    spec = TAXONOMY[scenario.family]
    action_rng = random.Random(f"{scenario.seed}|step{step}|{action.value}")

    if is_unsafe(action):
        return StepTransition(
            outcome=ValidatedOutcome.UNSAFE,
            unsafe_action_taken=True,
            recovery_latency_seconds=10.0,
            recovery_cost=45.0,
            validation_window_seconds=VALIDATION_WINDOW_SECONDS,
            partial=False,
        )

    if action == ActionId.ESCALATE_TO_HUMAN:
        return StepTransition(
            outcome=ValidatedOutcome.TIMEOUT,
            unsafe_action_taken=False,
            recovery_latency_seconds=VALIDATION_WINDOW_SECONDS,
            recovery_cost=8.0,
            validation_window_seconds=VALIDATION_WINDOW_SECONDS,
            partial=False,
        )

    if action == ActionId.ABSTAIN:
        return StepTransition(
            outcome=ValidatedOutcome.TIMEOUT,
            unsafe_action_taken=False,
            recovery_latency_seconds=_nominal_latency(action),
            recovery_cost=_nominal_cost(action),
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
    return StepTransition(
        outcome=outcome,
        unsafe_action_taken=False,
        recovery_latency_seconds=latency,
        recovery_cost=cost,
        validation_window_seconds=VALIDATION_WINDOW_SECONDS,
        partial=partial,
    )


def _true_intermediate_signal(scenario: RecoveryScenarioV2, action: ActionId, outcome: ValidatedOutcome) -> ObservationSignal:
    """The TRUE (pre-noise) step-1 intermediate signal, only ever computed
    when step 1 did not already terminate the episode (i.e. outcome is
    PARTIAL_SUCCESS or FAILURE from a safe, non-abstain/escalate action).
    Tied to whether the chosen action was well- or poorly-matched to the
    (hidden) cause, via the SAME ground-truth table used to resolve the
    outcome -- not a second independent source of ground truth."""
    if outcome == ValidatedOutcome.PARTIAL_SUCCESS:
        return ObservationSignal.IMPROVED
    key = (scenario.family.value, scenario.hidden_cause, action.value)
    p_success_taken, _ = _OUTCOME_TABLE.get(key, (0.0, 0.0))
    best_p = -1.0
    for a in TAXONOMY[scenario.family].candidate_actions:
        if is_unsafe(a) or a in (ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN):
            continue
        k = (scenario.family.value, scenario.hidden_cause, a.value)
        if k in _OUTCOME_TABLE:
            best_p = max(best_p, _OUTCOME_TABLE[k][0])
    if best_p <= 0:
        return ObservationSignal.NO_CHANGE
    # Threshold calibrated against the frozen ground-truth table
    # (environment.py's _OUTCOME_TABLE, read-only import): 0.75 is the
    # value at which configuration_failure's stale_config mismatch
    # (reconfigure=0.55 vs rollback-best=0.85, ratio 0.647) and
    # dependency_failure's downstream_outage mismatch (retry=0.05 vs
    # abstain-best=0.10, ratio 0.5) both register as WORSENED, while
    # resource_exhaustion/transient_failure -- where the taxonomy's own
    # per-cause success rates are close enough that no single fixed first
    # action is meaningfully mismatched for either cause -- correctly
    # register NO_CHANGE. A 0.5 threshold made WORSENED never fire at all
    # (checked empirically before freezing this value), which would make
    # any rule conditioning on WORSENED vacuous.
    return ObservationSignal.NO_CHANGE if p_success_taken >= 0.75 * best_p else ObservationSignal.WORSENED


def _noisy_observation(true_signal: ObservationSignal, noise_rate: float, scenario_seed: int) -> ObservationSignal:
    """Flips ``true_signal`` to a uniformly-random OTHER ternary value with
    probability ``noise_rate``; deterministic given (seed, true_signal,
    noise_rate)."""
    rng = random.Random(f"{scenario_seed}|observation_noise|{noise_rate}")
    if rng.random() >= noise_rate:
        return true_signal
    others = [s for s in ObservationSignal if s != true_signal]
    return others[rng.randrange(len(others))]


def run_step1(scenario: RecoveryScenarioV2, action: ActionId, observation_noise_rate: float) -> tuple[StepTransition, bool]:
    """Resolves step 1. Returns (transition, episode_terminates_here).
    ``transition.observation`` is populated with the (possibly noisy)
    ternary signal iff the episode continues to step 2."""
    trans = _resolve_action_outcome(scenario, action, step=1)

    if trans.outcome == ValidatedOutcome.SUCCESS:
        return trans, True
    if trans.outcome == ValidatedOutcome.UNSAFE:
        return trans, True
    if action in (ActionId.ABSTAIN, ActionId.ESCALATE_TO_HUMAN):
        return trans, True

    true_signal = _true_intermediate_signal(scenario, action, trans.outcome)
    observed = _noisy_observation(true_signal, observation_noise_rate, scenario.seed)
    trans_with_obs = trans.model_copy(update={"observation": observed})
    return trans_with_obs, False


def make_step2_context(scenario: RecoveryScenarioV2, step1_action: ActionId, step1_observation: ObservationSignal) -> DecisionContextV2:
    ctx1 = scenario.step1_context
    return DecisionContextV2(
        scenario_id=ctx1.scenario_id,
        episode_id=ctx1.episode_id,
        family=ctx1.family,
        symptom_pattern=ctx1.symptom_pattern,
        severity=ctx1.severity,
        workload_type=ctx1.workload_type,
        candidate_actions=ctx1.candidate_actions,
        step=2,
        step1_action=step1_action,
        step1_observation=step1_observation,
    )


def run_step2(scenario: RecoveryScenarioV2, action: ActionId) -> StepTransition:
    return _resolve_action_outcome(scenario, action, step=2)


def classify_outcome(step1_transition: StepTransition, step1_terminal: bool,
                      step1_action: ActionId, step2_transition: StepTransition | None,
                      step2_action: ActionId | None) -> EpisodeOutcomeClass:
    if step1_terminal:
        if step1_transition.outcome == ValidatedOutcome.SUCCESS:
            return EpisodeOutcomeClass.SUCCESS_STEP1
        if step1_action in (ActionId.ABSTAIN, ActionId.ESCALATE_TO_HUMAN):
            return EpisodeOutcomeClass.ABSTAIN_OR_ESCALATE
        return EpisodeOutcomeClass.BUDGET_EXHAUSTED  # unsafe-at-step1 case
    assert step2_transition is not None and step2_action is not None
    if step2_transition.outcome == ValidatedOutcome.SUCCESS:
        return EpisodeOutcomeClass.SUCCESS_STEP2
    if step2_action in (ActionId.ABSTAIN, ActionId.ESCALATE_TO_HUMAN):
        return EpisodeOutcomeClass.ABSTAIN_OR_ESCALATE
    return EpisodeOutcomeClass.BUDGET_EXHAUSTED


def oracle_best_action_v2(scenario: RecoveryScenarioV2) -> ActionId:
    """Reference upper bound ONLY (protocol section 5, item 3) -- uses
    ``hidden_cause`` directly via Phase 4.3's frozen ``oracle_best_action``.
    Never used as a policy input or competing baseline."""
    from src.recovery.schema import RecoveryScenario as _RecoveryScenarioV1
    v1_ctx_kwargs = dict(
        scenario_id=scenario.scenario_id, episode_id=scenario.step1_context.episode_id,
        family=scenario.family, symptom_pattern=scenario.step1_context.symptom_pattern,
        severity=scenario.step1_context.severity, workload_type=scenario.step1_context.workload_type,
        candidate_actions=scenario.step1_context.candidate_actions,
    )
    from src.recovery.schema import DecisionContext as _DecisionContextV1
    v1_scenario = _RecoveryScenarioV1(
        scenario_id=scenario.scenario_id, family=scenario.family, hidden_cause=scenario.hidden_cause,
        decision_context=_DecisionContextV1(**v1_ctx_kwargs), seed=scenario.seed,
        generator_version=scenario.generator_version, scenario_taxonomy_version=scenario.scenario_taxonomy_version,
    )
    return _oracle_best_action_v1(v1_scenario)
