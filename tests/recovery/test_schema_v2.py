from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.recovery.environment_v2 import generate_scenario_v2
from src.recovery.schema import ActionId, ScenarioFamily
from src.recovery.schema_v2 import DecisionContextV2, ObservationSignal


def test_decision_context_v2_rejects_hidden_cause_field():
    """Section 4 contamination test: attempting to smuggle hidden_cause
    into a DecisionContextV2 payload must be rejected. Written and
    confirmed failing/rejecting before any Phase 4.4 policy code is
    written against this schema (protocol section 4)."""
    scenario = generate_scenario_v2(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    payload = scenario.step1_context.model_dump()
    payload["hidden_cause"] = scenario.hidden_cause
    with pytest.raises(ValidationError):
        DecisionContextV2(**payload)


def test_decision_context_v2_rejects_step2_outcome_field():
    scenario = generate_scenario_v2(ScenarioFamily.TRANSIENT_FAILURE, seed=2)
    payload = scenario.step1_context.model_dump()
    payload["step2_outcome"] = "success"
    with pytest.raises(ValidationError):
        DecisionContextV2(**payload)


def test_decision_context_v2_rejects_final_outcome_field():
    scenario = generate_scenario_v2(ScenarioFamily.CONFIGURATION_FAILURE, seed=3)
    payload = scenario.step1_context.model_dump()
    payload["final_outcome"] = "success"
    with pytest.raises(ValidationError):
        DecisionContextV2(**payload)


def test_decision_context_v2_step1_forbids_step1_action_populated():
    scenario = generate_scenario_v2(ScenarioFamily.RESOURCE_EXHAUSTION, seed=4)
    payload = scenario.step1_context.model_dump()
    payload["step1_action"] = ActionId.RETRY.value
    with pytest.raises(ValidationError):
        DecisionContextV2(**payload)


def test_decision_context_v2_step2_requires_step1_fields():
    scenario = generate_scenario_v2(ScenarioFamily.RESOURCE_EXHAUSTION, seed=5)
    payload = scenario.step1_context.model_dump()
    payload["step"] = 2
    with pytest.raises(ValidationError):
        DecisionContextV2(**payload)


def test_decision_context_v2_has_no_hidden_cause_attribute():
    scenario = generate_scenario_v2(ScenarioFamily.DEPENDENCY_FAILURE, seed=6)
    assert not hasattr(scenario.step1_context, "hidden_cause")


def test_decision_context_v2_valid_step2_construction_succeeds():
    scenario = generate_scenario_v2(ScenarioFamily.RESOURCE_EXHAUSTION, seed=7)
    ctx1 = scenario.step1_context
    ctx2 = DecisionContextV2(
        scenario_id=ctx1.scenario_id, episode_id=ctx1.episode_id, family=ctx1.family,
        symptom_pattern=ctx1.symptom_pattern, severity=ctx1.severity, workload_type=ctx1.workload_type,
        candidate_actions=ctx1.candidate_actions, step=2,
        step1_action=ActionId.RETRY, step1_observation=ObservationSignal.WORSENED,
    )
    assert ctx2.step1_action == ActionId.RETRY
    assert ctx2.step1_observation == ObservationSignal.WORSENED
