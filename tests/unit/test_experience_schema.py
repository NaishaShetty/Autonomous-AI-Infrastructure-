"""Unit tests for src/experience/schema.py: structural leakage prevention,
determinism, and provenance correctness."""
from __future__ import annotations

import dataclasses

from src.experience.schema import (
    DecisionTimeQuery,
    Experience,
    deterministic_event_id,
    experience_from_episode_record,
)

RECORD = {
    "step": 7,
    "occurrence_ordinal": 1,
    "sample_index_in_occurrence": 2,
    "workload_id": "workload_1",
    "condition_id": "feature_noise_mild",
    "is_novel_combo": False,
    "split": "train",
    "occurrence_count_for_combo": 2,
    "context": {"f1": 0.1, "f2": 0.2, "f3": 0.3, "f4": 0.4, "f5": 0.5},
    "true_label": 1,
    "predicted_label": 0,
    "confidence": 0.42,
    "b_risk_score": 0.58,
    "tier": "CRITICAL",
    "decision": "ABSTAIN",
    "is_failure": True,
    "outcome": "INCORRECT",
    "diagnosed_cause": "feature_noise",
    "recovery_attempted": True,
    "recovery_action": "retry",
    "recovery_outcome": "ROLLED_BACK",
    "recovery_correct": None,
}


def test_decision_time_query_has_no_outcome_or_ground_truth_fields():
    """Structural leakage prevention: DecisionTimeQuery's field set must
    never grow to include condition_id, true_label, outcome, is_failure,
    or any recovery_* field -- this test fails loudly if it ever does."""
    field_names = {f.name for f in dataclasses.fields(DecisionTimeQuery)}
    forbidden = {"condition_id", "true_label", "outcome", "is_failure", "recovery_action", "recovery_outcome", "recovery_correct"}
    assert field_names.isdisjoint(forbidden)


def test_experience_from_episode_record_round_trips_core_fields():
    exp = experience_from_episode_record(RECORD, protocol_version="v1", dataset_content_hash="deadbeef")
    assert exp.event.workload_id == "workload_1"
    assert exp.event.context == RECORD["context"]
    assert exp.event.confidence == 0.42
    assert exp.event.failure_risk == 0.58
    assert exp.event.is_failure is True
    assert exp.event.decision.value == "ABSTAIN"
    assert exp.event.abstained is True
    assert exp.provenance.condition_id == "feature_noise_mild"
    assert exp.provenance.step == 7
    assert exp.provenance.diagnosed_cause == "feature_noise"


def test_deterministic_event_id_is_stable_and_fits_db_column():
    a = deterministic_event_id(7, "workload_1", "feature_noise_mild")
    b = deterministic_event_id(7, "workload_1", "feature_noise_mild")
    assert a == b
    assert len(a) <= 32  # ReliabilityEventRecord.event_id is String(32)


def test_deterministic_event_id_differs_for_different_steps():
    a = deterministic_event_id(7, "workload_1", "feature_noise_mild")
    b = deterministic_event_id(8, "workload_1", "feature_noise_mild")
    assert a != b


def test_decision_time_query_excludes_ground_truth_condition_id():
    exp = experience_from_episode_record(RECORD, protocol_version="v1", dataset_content_hash="deadbeef")
    query = exp.decision_time_query()
    assert not hasattr(query, "condition_id")
    assert query.context == RECORD["context"]
    assert query.diagnosed_cause == "feature_noise"


def test_metadata_mirrors_provenance_for_persistence():
    exp = experience_from_episode_record(RECORD, protocol_version="v1", dataset_content_hash="deadbeef")
    assert exp.event.metadata["condition_id"] == "feature_noise_mild"
    assert exp.event.metadata["dataset_content_hash"] == "deadbeef"
