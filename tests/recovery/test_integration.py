from __future__ import annotations

from src.failure_experience.schema import FailureExperience
from src.recovery.environment import generate_scenario, transition
from src.recovery.experience_bridge import to_failure_experience
from src.recovery.policy import EmpiricalRecoveryPolicy, FixedPriorityPolicy
from src.recovery.schema import ActionId, ActionSelection, ScenarioFamily, ValidatedOutcome
from src.recovery.schema import RecoveryEpisode, Split
from src.recovery.provenance import stamp_provenance


def _resolved_episode(family, seed, action):
    scenario = generate_scenario(family, seed)
    trans = transition(scenario, action)
    selection = ActionSelection(selected_action=action, policy_id="test", policy_version="v1")
    return RecoveryEpisode(
        episode_id=scenario.decision_context.episode_id, scenario=scenario,
        policy_selection=selection, transition=trans,
        provenance=stamp_provenance(scenario.decision_context.episode_id, seed, Split.TRAIN),
    )


def test_recovery_episode_converts_to_failure_experience():
    ep = _resolved_episode(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1, action=ActionId.RESTART)
    fx = to_failure_experience(ep)
    assert isinstance(fx, FailureExperience)
    assert fx.provenance.source_dataset == "phase4_3_controlled_recovery"
    assert fx.recovery.selected_action == "restart"
    assert fx.recovery.status.value == "attempted"


def test_bridge_never_leaks_hidden_cause_into_diagnosis():
    ep = _resolved_episode(ScenarioFamily.CONFIGURATION_FAILURE, seed=2, action=ActionId.RECONFIGURE)
    fx = to_failure_experience(ep)
    assert fx.diagnosis.suspected_cause is None
    # hidden_cause must not appear anywhere in the serialized experience
    dumped = fx.model_dump_json()
    assert ep.scenario.hidden_cause not in dumped


def test_bridge_marks_controlled_provenance_and_excluded_eligibility():
    ep = _resolved_episode(ScenarioFamily.TRANSIENT_FAILURE, seed=3, action=ActionId.RETRY)
    fx = to_failure_experience(ep)
    assert fx.provenance.raw_record_ref["source_type"] == "controlled"
    assert fx.eligibility.role.value == "excluded"


def test_outcome_maps_to_correct_validation_result_and_final_status():
    for family, action in [
        (ScenarioFamily.RESOURCE_EXHAUSTION, ActionId.RESTART),
        (ScenarioFamily.DEPENDENCY_FAILURE, ActionId.FORCE_RESTART),
    ]:
        ep = _resolved_episode(family, seed=10, action=action)
        fx = to_failure_experience(ep)
        if ep.transition.outcome == ValidatedOutcome.UNSAFE:
            assert fx.outcome.final_status.value == "worsened"
            assert fx.validation.validation_result.value == "failed"


def test_end_to_end_fit_select_transition_bridge_pipeline():
    """FailureExperience -> recovery learner -> evaluation harness ->
    FailureExperience outcome, minimal end-to-end integration check
    (brief section 34, integration tests)."""
    train = [
        _resolved_episode(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1000 + i,
                           action=[ActionId.RETRY, ActionId.RESTART][i % 2])
        for i in range(50)
    ]
    policy = EmpiricalRecoveryPolicy(min_evidence=3).fit(train)
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=99999)
    selection = policy.select_action(scenario.decision_context)
    trans = transition(scenario, selection.selected_action)
    ep = RecoveryEpisode(
        episode_id=scenario.decision_context.episode_id, scenario=scenario,
        policy_selection=selection, transition=trans,
        provenance=stamp_provenance(scenario.decision_context.episode_id, 99999, Split.TEST),
    )
    fx = to_failure_experience(ep)
    assert fx.recovery.selected_action == selection.selected_action.value
