from __future__ import annotations

import random

from src.recovery.actions import is_unsafe
from src.recovery.environment import generate_scenario, transition
from src.recovery.policy import (
    EmpiricalRecoveryPolicy,
    FixedPriorityPolicy,
    FrequencyOnlyPolicy,
    RandomValidPolicy,
    UnmaskedUtilityPolicy,
    make_family_only_policy,
    make_no_abstention_policy,
)
from src.recovery.schema import ActionId, ActionSelection, RecoveryEpisode, ScenarioFamily, Split
from src.recovery.provenance import stamp_provenance
from src.recovery.taxonomy import safe_candidate_actions


def _build_train_corpus(family: ScenarioFamily, n: int, seed_offset: int) -> list[RecoveryEpisode]:
    episodes = []
    rng = random.Random(f"corpus|{family}|{seed_offset}")
    safe = safe_candidate_actions(family)
    for i in range(n):
        seed = seed_offset + i
        scenario = generate_scenario(family, seed)
        action = safe[rng.randrange(len(safe))]
        trans = transition(scenario, action)
        selection = ActionSelection(selected_action=action, policy_id="exploration_test", policy_version="v1")
        episodes.append(RecoveryEpisode(
            episode_id=scenario.decision_context.episode_id, scenario=scenario,
            policy_selection=selection, transition=trans,
            provenance=stamp_provenance(scenario.decision_context.episode_id, seed, Split.TRAIN),
        ))
    return episodes


def test_fixed_priority_never_selects_unsafe_action():
    policy = FixedPriorityPolicy()
    for family in ScenarioFamily:
        for seed in range(30):
            scenario = generate_scenario(family, seed)
            sel = policy.select_action(scenario.decision_context)
            assert not is_unsafe(sel.selected_action)
            assert sel.selected_action in scenario.decision_context.candidate_actions


def test_random_valid_never_selects_unsafe_action_and_is_deterministic():
    policy = RandomValidPolicy()
    scenario = generate_scenario(ScenarioFamily.DEPENDENCY_FAILURE, seed=5)
    sel1 = policy.select_action(scenario.decision_context)
    sel2 = policy.select_action(scenario.decision_context)
    assert sel1.selected_action == sel2.selected_action  # reproducible given episode_id
    assert not is_unsafe(sel1.selected_action)


def test_empirical_policy_requires_fit_before_use():
    policy = EmpiricalRecoveryPolicy()
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    try:
        policy.select_action(scenario.decision_context)
        assert False, "expected RuntimeError before fit()"
    except RuntimeError:
        pass


def test_empirical_policy_abstains_with_no_evidence():
    policy = EmpiricalRecoveryPolicy(min_evidence=5).fit([])
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    sel = policy.select_action(scenario.decision_context)
    assert sel.abstained is True
    assert sel.selected_action in (ActionId.ABSTAIN, ActionId.ESCALATE_TO_HUMAN)


def test_empirical_policy_learns_and_prefers_high_success_action():
    train = _build_train_corpus(ScenarioFamily.RESOURCE_EXHAUSTION, n=400, seed_offset=1000)
    policy = EmpiricalRecoveryPolicy(min_evidence=5).fit(train)
    # memory_leak scenarios: RESTART (0.85) should be strongly preferred over RETRY (0.05)
    restart_picks, total = 0, 0
    for seed in range(2000, 2100):
        scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=seed)
        if scenario.hidden_cause != "memory_leak":
            continue
        sel = policy.select_action(scenario.decision_context)
        total += 1
        if sel.selected_action == ActionId.RESTART:
            restart_picks += 1
    assert total > 0
    assert restart_picks / total > 0.7


def test_no_abstention_ablation_never_abstains():
    policy = make_no_abstention_policy(min_evidence=1000).fit([])
    scenario = generate_scenario(ScenarioFamily.TRANSIENT_FAILURE, seed=1)
    sel = policy.select_action(scenario.decision_context)
    assert sel.abstained is False


def test_family_only_ablation_ignores_symptom_and_severity():
    train = _build_train_corpus(ScenarioFamily.CONFIGURATION_FAILURE, n=300, seed_offset=3000)
    policy = make_family_only_policy(min_evidence=5).fit(train)
    scenario_a = generate_scenario(ScenarioFamily.CONFIGURATION_FAILURE, seed=4000)
    sel_a = policy.select_action(scenario_a.decision_context)
    # family-only stats depend only on family -> two different scenarios of the
    # same family must receive identical estimated_utility dicts
    scenario_b = generate_scenario(ScenarioFamily.CONFIGURATION_FAILURE, seed=4001)
    sel_b = policy.select_action(scenario_b.decision_context)
    assert sel_a.estimated_utility == sel_b.estimated_utility


def test_frequency_only_ablation_ignores_outcome():
    train = _build_train_corpus(ScenarioFamily.TRANSIENT_FAILURE, n=200, seed_offset=5000)
    policy = FrequencyOnlyPolicy().fit(train)
    scenario = generate_scenario(ScenarioFamily.TRANSIENT_FAILURE, seed=5)
    sel = policy.select_action(scenario.decision_context)
    assert sel.selected_action in scenario.decision_context.candidate_actions


def test_unmasked_utility_ablation_can_select_unsafe_action():
    """This ablation exists specifically to demonstrate the safety mask is
    load-bearing: without it, the raw-utility argmax CAN pick the unsafe
    action for downstream_outage (where all safe actions have low success)."""
    train = _build_train_corpus(ScenarioFamily.DEPENDENCY_FAILURE, n=300, seed_offset=6000)
    inner = EmpiricalRecoveryPolicy(min_evidence=5).fit(train)
    unmasked = UnmaskedUtilityPolicy(inner)
    saw_unsafe = False
    for seed in range(7000, 7200):
        scenario = generate_scenario(ScenarioFamily.DEPENDENCY_FAILURE, seed=seed)
        sel = unmasked.select_action(scenario.decision_context)
        if is_unsafe(sel.selected_action):
            saw_unsafe = True
            break
    assert saw_unsafe, "safety-ablation policy never selected the unsafe action across 200 draws -- test may need a larger sample"
