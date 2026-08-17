from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.recovery.environment import generate_scenario, transition
from src.recovery.schema import (
    ActionId,
    DecisionContext,
    RecoveryEpisode,
    ScenarioFamily,
    Split,
)
from src.recovery.provenance import stamp_provenance


def test_decision_context_rejects_hidden_cause_field():
    """extra='forbid' must reject any attempt to smuggle a hidden_cause (or
    any other undeclared field) into DecisionContext -- the structural
    leakage guard the whole protocol depends on."""
    with pytest.raises(ValidationError):
        DecisionContext(
            scenario_id="x", episode_id="x", family=ScenarioFamily.RESOURCE_EXHAUSTION,
            symptom_pattern="A", severity="low", workload_type="batch",
            candidate_actions=[ActionId.RETRY], hidden_cause="memory_leak",
        )


def test_decision_context_has_no_hidden_cause_attribute():
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    assert not hasattr(scenario.decision_context, "hidden_cause")


def test_recovery_episode_frozen_and_hashable_content():
    scenario = generate_scenario(ScenarioFamily.TRANSIENT_FAILURE, seed=2)
    trans = transition(scenario, ActionId.RETRY)
    from src.recovery.schema import ActionSelection
    selection = ActionSelection(selected_action=ActionId.RETRY, policy_id="test", policy_version="v1")
    ep = RecoveryEpisode(
        episode_id=scenario.decision_context.episode_id, scenario=scenario,
        policy_selection=selection, transition=trans,
        provenance=stamp_provenance(scenario.decision_context.episode_id, 2, Split.TRAIN),
    )
    assert ep.content_hash()
    with pytest.raises(ValidationError):
        ep.episode_id = "changed"  # frozen model


def test_episode_id_mismatch_rejected():
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=3)
    with pytest.raises(ValidationError):
        RecoveryEpisode(
            episode_id="not-the-real-id", scenario=scenario,
            provenance=stamp_provenance("not-the-real-id", 3, Split.TRAIN),
        )


def test_source_type_always_controlled():
    scenario = generate_scenario(ScenarioFamily.CONFIGURATION_FAILURE, seed=4)
    prov = stamp_provenance(scenario.decision_context.episode_id, 4, Split.TEST)
    assert prov.source_type.value == "controlled"
