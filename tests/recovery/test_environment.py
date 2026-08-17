from __future__ import annotations

import pytest

from src.recovery.actions import is_unsafe
from src.recovery.environment import generate_scenario, oracle_best_action, transition
from src.recovery.schema import ActionId, ScenarioFamily, ValidatedOutcome
from src.recovery.taxonomy import TAXONOMY


# ---------------------------------------------------------------------------
# Determinism (STEP 8: environment must be verified before policy results
# are accepted)
# ---------------------------------------------------------------------------


def test_generate_scenario_deterministic_given_seed():
    a = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=42)
    b = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=42)
    assert a.scenario_id == b.scenario_id
    assert a.hidden_cause == b.hidden_cause
    assert a.decision_context.symptom_pattern == b.decision_context.symptom_pattern
    assert a.decision_context.severity == b.decision_context.severity


def test_different_seeds_generally_differ():
    seen = {generate_scenario(ScenarioFamily.TRANSIENT_FAILURE, seed=s).scenario_id for s in range(50)}
    assert len(seen) == 50  # no accidental id collisions across 50 seeds


def test_transition_deterministic_given_seed_and_action():
    scenario = generate_scenario(ScenarioFamily.CONFIGURATION_FAILURE, seed=7)
    t1 = transition(scenario, ActionId.RECONFIGURE)
    t2 = transition(scenario, ActionId.RECONFIGURE)
    assert t1.outcome == t2.outcome
    assert t1.recovery_latency_seconds == t2.recovery_latency_seconds


# ---------------------------------------------------------------------------
# Known-answer environment validation (brief section 32)
# ---------------------------------------------------------------------------


def test_unsafe_action_always_yields_unsafe_outcome():
    """FORCE_RESTART is the frozen protocol's one UNSAFE action -- must
    deterministically resolve to ValidatedOutcome.UNSAFE regardless of
    scenario/seed, known-answer check."""
    for seed in range(20):
        scenario = generate_scenario(ScenarioFamily.DEPENDENCY_FAILURE, seed=seed)
        t = transition(scenario, ActionId.FORCE_RESTART)
        assert t.outcome == ValidatedOutcome.UNSAFE
        assert t.unsafe_action_taken is True


def test_escalate_always_times_out():
    for family in ScenarioFamily:
        scenario = generate_scenario(family, seed=100)
        t = transition(scenario, ActionId.ESCALATE_TO_HUMAN)
        assert t.outcome == ValidatedOutcome.TIMEOUT
        assert t.unsafe_action_taken is False


def test_action_not_in_family_candidates_rejected():
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    with pytest.raises(ValueError):
        transition(scenario, ActionId.ROLLBACK)  # rollback is not a candidate for resource_exhaustion


def test_high_fit_action_succeeds_far_more_often_than_low_fit_action():
    """Known-answer sanity check on the ground-truth table: RESTART should
    resolve to SUCCESS much more often than RETRY for memory_leak-caused
    resource_exhaustion scenarios (0.85 vs 0.05 by the frozen table)."""
    restart_successes, retry_successes, n = 0, 0, 300
    for seed in range(n):
        scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=seed)
        if scenario.hidden_cause != "memory_leak":
            continue
        if transition(scenario, ActionId.RESTART).outcome == ValidatedOutcome.SUCCESS:
            restart_successes += 1
        if transition(scenario, ActionId.RETRY).outcome == ValidatedOutcome.SUCCESS:
            retry_successes += 1
    assert restart_successes > retry_successes * 3


def test_partial_recovery_occurs():
    outcomes = set()
    for seed in range(200):
        scenario = generate_scenario(ScenarioFamily.CONFIGURATION_FAILURE, seed=seed)
        outcomes.add(transition(scenario, ActionId.RECONFIGURE).outcome)
    assert ValidatedOutcome.PARTIAL_SUCCESS in outcomes
    assert ValidatedOutcome.SUCCESS in outcomes
    assert ValidatedOutcome.FAILURE in outcomes


def test_oracle_never_selects_unsafe_action():
    for family in ScenarioFamily:
        for seed in range(30):
            scenario = generate_scenario(family, seed=seed)
            best = oracle_best_action(scenario)
            assert not is_unsafe(best)


def test_symptom_pattern_is_not_a_deterministic_function_of_cause():
    """Avoid-baked-in-answers check (brief section 16): across many seeds,
    both symptom_pattern values must occur for the SAME hidden cause --
    otherwise the noisy symptom would be a disguised lookup key."""
    seen_by_cause: dict[str, set[str]] = {}
    for seed in range(300):
        scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=seed)
        seen_by_cause.setdefault(scenario.hidden_cause, set()).add(scenario.decision_context.symptom_pattern)
    for cause, patterns in seen_by_cause.items():
        assert patterns == {"A", "B"}, f"cause {cause} symptom_pattern is deterministic -- baked-in answer risk"


def test_multiple_valid_actions_have_different_success_rates():
    """Avoid-baked-in-answers check: at least two candidate actions per
    family must have distinguishable ground-truth success rates (not a
    trivial single-correct-answer table)."""
    from src.recovery.environment import _OUTCOME_TABLE
    for family, spec in TAXONOMY.items():
        rates = [p for (fam, cause, action), (p, _) in _OUTCOME_TABLE.items() if fam == family.value]
        assert len(set(rates)) >= 2
