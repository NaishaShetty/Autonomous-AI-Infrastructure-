from __future__ import annotations

from pathlib import Path

import pytest

from src.failure_memory.memory import FailureMemory
from src.runtime.builder import build_runtime_system
from src.runtime.components import SimulatedRecoveryExecutor
from src.runtime.contracts import RecoveryAction


def test_observation_normalizer_rejects_malformed_numeric_input():
    system = build_runtime_system(feature_names=["f1"])
    with pytest.raises(ValueError, match="numeric"):
        system.normalizer.normalize({"features": {"f1": "not-a-number"}})


def test_closed_loop_records_transitions_and_learning_update(tmp_path: Path):
    system = build_runtime_system(feature_names=["f1"], experience_path=tmp_path / "episodes.jsonl")
    observation = system.normalizer.normalize({
        "observation_id": "episode-001",
        "workload_id": "sim",
        "features": {"f1": 1.0},
        "resource_signals": {"gpu": 0.99},
        "source": "simulator",
        "provenance": {"scenario": "resource_failure"},
    })
    episode = system.controller.process(observation)
    assert episode.detection and episode.detection.detected
    assert episode.diagnosis and episode.diagnosis.failure_type == "resource_exhaustion"
    assert episode.recovery_plan and episode.recovery_plan.selected_action == RecoveryAction.RECONFIGURE
    assert episode.execution and episode.execution.executor == "simulated"
    assert episode.validation and episode.validation.status == "RECOVERED"
    assert episode.experience_id
    assert episode.learning_update["updated"] is True
    assert episode.learning_update["memory_version_after"] > episode.learning_update["memory_version_before"]
    assert [t.to_state.value for t in episode.transitions] == [
        "detected", "assessing", "diagnosed", "recovery_planned", "recovery_executing", "recovery_validating", "recovered", "learned"
    ]
    assert len(system.experience_store.episodes) == 1


def test_unsafe_recovery_abstains_without_execution(tmp_path: Path):
    system = build_runtime_system(feature_names=["f1"], experience_path=tmp_path / "episodes.jsonl")
    observation = system.normalizer.normalize({
        "observation_id": "episode-unsafe",
        "workload_id": "sim",
        "features": {"f1": 1.0},
        "resource_signals": {"gpu": 0.99},
        "environment": {"unsafe_actions": ["reconfigure"]},
    })
    episode = system.controller.process(observation)
    assert episode.state.value == "learned"
    assert episode.recovery_plan and episode.recovery_plan.abstained
    assert episode.execution is None
    assert episode.validation is None
    assert episode.learning_update["updated"] is True


def test_failure_memory_marks_dirty_and_rebuilds_synchronously():
    memory = FailureMemory(["f1"])
    assert not memory.dirty
    event = __import__("src.schema.events", fromlist=["ReliabilityEvent"]).ReliabilityEvent(
        workload_id="w", source="reliability_engine", context={"f1": 1.0}, raw_confidence=0.2, confidence=0.2,
        failure_risk=0.8, decision="ANSWER", abstained=False, is_failure=True,
        outcome="INCORRECT",
    )
    memory.ingest(event)
    assert not memory.dirty
    assert memory.memory_version == 1
    assert memory.last_fit_event_count == 1
    assert memory.pending_update_count == 0
    assert memory.risk({"f1": 1.0}, 0.2) >= 0.0


def test_stale_memory_cannot_be_queried_as_current():
    memory = FailureMemory(["f1"])
    event = __import__("src.schema.events", fromlist=["ReliabilityEvent"]).ReliabilityEvent(
        workload_id="w", source="reliability_engine", context={"f1": 1.0}, raw_confidence=0.2, confidence=0.2,
        failure_risk=0.8, decision="ANSWER", abstained=False, is_failure=True,
        outcome="INCORRECT",
    )
    memory.ingest(event)
    memory.store(event, repository=None, persist=False, rebuild=False)  # type: ignore[arg-type]
    assert memory.dirty
    with pytest.raises(RuntimeError, match="dirty"):
        memory.risk({"f1": 1.0}, 0.2)


def test_experience_store_reloads_complete_episode(tmp_path: Path):
    path = tmp_path / "episodes.jsonl"
    system = build_runtime_system(feature_names=["f1"], experience_path=path)
    observation = system.normalizer.normalize({"observation_id": "reload-001", "workload_id": "sim", "features": {"f1": 1.0}, "resource_signals": {"gpu": 0.99}, "provenance": {"source_record": "reload"}})
    episode = system.controller.process(observation)
    assert episode.experience_id
    restarted = build_runtime_system(feature_names=["f1"], experience_path=path)
    assert len(restarted.experience_store.episodes) == 1
    assert restarted.experience_store.episodes[0].identity.episode_id == "reload-001"
    assert restarted.experience_store.episodes[0].provenance.raw_record_ref["observation_id"] == "reload-001"


def test_controller_has_one_authoritative_event_save():
    class SpyRepository:
        def __init__(self):
            self.saved = []

        def save(self, event):
            self.saved.append(event)
            return event

    system = build_runtime_system(feature_names=["f1"])
    spy = SpyRepository()
    system.controller.repository = spy
    observation = system.normalizer.normalize({"observation_id": "persist-001", "workload_id": "sim", "features": {"f1": 1.0}, "resource_signals": {"gpu": 0.99}})
    system.controller.process(observation)
    assert len(spy.saved) == 1


def _make_training_event():
    from src.runtime.builder import build_runtime_system
    from src.runtime.components import RuleBasedRecoveryPlanner, SimulatedRecoveryExecutor
    system = build_runtime_system(
        feature_names=["f1"],
        planner=RuleBasedRecoveryPlanner(default_action="reconfigure"),
        executor=SimulatedRecoveryExecutor({"reconfigure": True}),
    )
    observation = system.normalizer.normalize({"observation_id": "training", "workload_id": "w", "features": {"f1": 0.2}, "error": "execution error"})
    system.controller.process(observation)
    return system.failure_memory.failure_events


def test_retrieval_exposes_similarity_relevance_and_memory_version():
    system = build_runtime_system(feature_names=["f1"])
    system.failure_memory.seed_events(list(_make_training_event()))
    matches = system.failure_memory.retrieve_matches({"f1": 0.2}, 0.5)
    assert len(matches) == 1
    assert matches[0].similarity == pytest.approx(1.0)
    assert matches[0].relevant is True
    assert matches[0].memory_version == system.failure_memory.memory_version


def test_relevant_history_changes_diagnosis_and_recovery_action():
    events = _make_training_event()
    learned = build_runtime_system(
        feature_names=["f1"],
        planner=__import__("src.runtime.components", fromlist=["RuleBasedRecoveryPlanner"]).RuleBasedRecoveryPlanner(default_action="retry"),
        executor=__import__("src.runtime.components", fromlist=["SimulatedRecoveryExecutor"]).SimulatedRecoveryExecutor({"retry": False, "reconfigure": True}),
    )
    learned.failure_memory.seed_events(list(events))
    episode = learned.controller.process(learned.normalizer.normalize({"observation_id": "eval", "workload_id": "w", "features": {"f1": 0.2}, "error": "execution error"}))
    assert episode.retrieved_experiences[0].relevant is True
    assert episode.diagnosis.confidence == pytest.approx(0.8)
    assert "historical_failure_pattern" in episode.diagnosis.likely_causes
    assert episode.recovery_plan.selected_action == RecoveryAction.RECONFIGURE
    assert episode.validation.recovered is True


def test_hard_safety_constraint_overrides_historical_preference():
    events = _make_training_event()
    learned = build_runtime_system(feature_names=["f1"], planner=__import__("src.runtime.components", fromlist=["RuleBasedRecoveryPlanner"]).RuleBasedRecoveryPlanner(default_action="retry"))
    learned.failure_memory.seed_events(list(events))
    episode = learned.controller.process(learned.normalizer.normalize({"observation_id": "unsafe", "workload_id": "w", "features": {"f1": 0.2}, "error": "execution error", "environment": {"unsafe_actions": ["reconfigure"]}}))
    assert episode.recovery_plan.abstained is True
    assert episode.recovery_plan.safety_status == "rejected"
    assert episode.execution is None


def test_irrelevant_history_does_not_fabricate_diagnosis_or_action_change():
    events = _make_training_event()
    system = build_runtime_system(feature_names=["f1"], planner=__import__("src.runtime.components", fromlist=["RuleBasedRecoveryPlanner"]).RuleBasedRecoveryPlanner(default_action="retry"))
    system.failure_memory.seed_events(list(events))
    episode = system.controller.process(system.normalizer.normalize({"observation_id": "far", "workload_id": "w", "features": {"f1": 100.0}, "error": "execution error"}))
    assert episode.retrieved_experiences[0].relevant is False
    assert episode.diagnosis.confidence == pytest.approx(0.6)
    assert episode.recovery_plan.selected_action == RecoveryAction.RETRY


def test_observation_sources_preserve_source_type_and_provenance():
    from src.runtime.sources import DatasetReplaySource, DeterministicSimulatorSource, MappingEventSource
    mapping = MappingEventSource({"workload_id": "w", "features": {"f1": 1.0}}).observe()
    replay = DatasetReplaySource([{"workload_id": "w", "features": {"f1": 1.0}}], dataset_id="dataset-v1").observe()
    simulated = DeterministicSimulatorSource([{"workload_id": "w", "features": {"f1": 1.0}}], scenario_id="scenario-v1").observe()
    assert mapping.source == "structured_mapping"
    assert replay.source == "dataset_replay"
    assert replay.provenance["dataset_id"] == "dataset-v1"
    assert simulated.source == "deterministic_simulator"
    assert simulated.provenance["scenario_id"] == "scenario-v1"
    assert simulated.provenance["step"] == 1
