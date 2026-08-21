"""Canonical autonomous runtime controller."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.storage.repository import EventRepository

from .contracts import (
    DiagnosisEngine,
    FailureDetector,
    FailureMemoryPort,
    LearningManager,
    Observation,
    RecoveryExecutor,
    RecoveryPlanner,
    RecoveryValidator,
    ReliabilityAssessor,
    RuntimeEpisode,
    RuntimeState,
)


class RuntimeController:
    """One explicit, bounded control loop.

    The controller owns orchestration and state transitions. Components own
    their stage-specific behavior. Recovery attempts are bounded and every
    action is validated independently of executor status.
    """

    def __init__(self, detector: FailureDetector, assessor: ReliabilityAssessor, memory: FailureMemoryPort, diagnosis: DiagnosisEngine, planner: RecoveryPlanner, executor: RecoveryExecutor, validator: RecoveryValidator, experience_store: Any, learning_manager: LearningManager, repository: EventRepository | None = None, workload_id: str = "default-workload", max_attempts: int = 1, relevance_threshold: float = 0.5):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self.detector = detector
        self.assessor = assessor
        self.memory = memory
        self.diagnosis_engine = diagnosis
        self.planner = planner
        self.executor = executor
        self.validator = validator
        self.experience_store = experience_store
        self.learning_manager = learning_manager
        self.repository = repository
        self.workload_id = workload_id
        self.max_attempts = max_attempts
        self.relevance_threshold = relevance_threshold

    def process(self, observation: Observation, *, true_label: int | None = None) -> RuntimeEpisode:
        episode = RuntimeEpisode(observation=observation)
        detection = self.detector.detect(observation)
        episode.detection = detection
        episode.transition_to(RuntimeState.DETECTED, "observation evaluated by failure detector")
        retrieved: list[Any] = []
        if detection.detected:
            retrieve_matches = getattr(self.memory, "retrieve_matches", None)
            retrieved = retrieve_matches(dict(observation.features), 0.5, k=5, min_similarity=self.relevance_threshold) if retrieve_matches else self.memory.retrieve(dict(observation.features), 0.5, k=5)
        episode.retrieved_experiences = retrieved
        episode.transition_to(RuntimeState.ASSESSING, "reliability assessment started")
        reliability = self.assessor.assess(observation, retrieved)
        episode.reliability = reliability

        evaluation_failure = false_if_none(true_label is not None and reliability.predicted_label != true_label)
        if not detection.detected and reliability.decision == Decision.ABSTAIN.value and not evaluation_failure:
            episode.transition_to(RuntimeState.ABSTAINED, "reliability policy abstained without an observed workload failure")
            self._persist_compatibility_event(episode, is_failure=False, outcome=Outcome.UNKNOWN)
            return episode
        needs_recovery = detection.detected or evaluation_failure
        if not needs_recovery:
            episode.transition_to(RuntimeState.LEARNED, "healthy answer requires no recovery")
            self._persist_compatibility_event(episode, is_failure=False, outcome=Outcome.UNKNOWN)
            return episode

        if reliability.decision == Decision.ABSTAIN.value and not detection.detected:
            episode.transition_to(RuntimeState.ABSTAINED, "reliability policy abstained")
        diagnosis = self.diagnosis_engine.diagnose(observation, detection, reliability, retrieved)
        episode.diagnosis = diagnosis
        episode.transition_to(RuntimeState.DIAGNOSED, "diagnosis recorded with uncertainty")
        failed_actions: list[str] = []
        plan = self.planner.plan(diagnosis, reliability, retrieved, {**dict(observation.environment), "failed_actions": failed_actions})
        episode.recovery_plan = plan
        episode.transition_to(RuntimeState.RECOVERY_PLANNED, "recovery plan passed through safety and feasibility gates")

        if plan.abstained:
            episode.transition_to(RuntimeState.ESCALATED, "recovery was unsafe or lacked sufficient evidence")
            self._persist_compatibility_event(episode, is_failure=True, outcome=Outcome.INCORRECT)
            self._learn(episode)
            return episode

        for attempt in range(1, self.max_attempts + 1):
            episode.transition_to(RuntimeState.RECOVERY_EXECUTING, f"executing recovery attempt {attempt}")
            execution = self.executor.execute(plan, observation, attempt=attempt)
            episode.execution = execution
            episode.executions.append(execution)
            episode.action_history.append(plan.selected_action)
            episode.transition_to(RuntimeState.RECOVERY_VALIDATING, "executor result requires independent validation")
            validation = self.validator.validate(observation, reliability, execution)
            episode.validation = validation
            episode.validations.append(validation)
            if validation.recovered is True:
                episode.transition_to(RuntimeState.RECOVERED, "validator confirmed recovery")
                break
            failed_actions.append(plan.selected_action.value)
            if attempt == self.max_attempts:
                episode.transition_to(RuntimeState.RECOVERY_FAILED, "maximum recovery attempts exhausted")
                break
            plan = self.planner.plan(diagnosis, reliability, retrieved, {**dict(observation.environment), "failed_actions": failed_actions, "attempt_history": [action.value for action in episode.action_history]})
            episode.recovery_plan = plan
            episode.transition_to(RuntimeState.RECOVERY_PLANNED, f"replanned after failed recovery attempt {attempt}")
            if plan.abstained:
                episode.transition_to(RuntimeState.ESCALATED, "no safe alternative recovery remained")
                break
        self._persist_compatibility_event(episode, is_failure=True, outcome=Outcome.CORRECT if episode.validation and episode.validation.recovered is True else Outcome.INCORRECT)
        self._learn(episode)
        return episode

    def _persist_compatibility_event(self, episode: RuntimeEpisode, *, is_failure: bool, outcome: Outcome) -> None:
        reliability = episode.reliability
        event = ReliabilityEvent(
            workload_id=episode.observation.workload_id or self.workload_id,
            source=EventSource.RELIABILITY_ENGINE,
            context=dict(episode.observation.features),
            raw_confidence=reliability.confidence if reliability else None,
            confidence=reliability.confidence,
            failure_risk=reliability.risk if reliability else None,
            decision=Decision(reliability.decision) if reliability else Decision.REVIEW,
            abstained=bool(reliability and reliability.decision != Decision.ANSWER.value),
            is_failure=is_failure,
            outcome=outcome,
            metadata={
                "runtime_state": episode.state.value,
                "observation_id": episode.observation.observation_id,
                "retrieved_experience_count": len(episode.retrieved_experiences),
                "relevant_experience_count": sum(1 for item in episode.retrieved_experiences if bool(getattr(item, "relevant", False))),
                "diagnosis": asdict(episode.diagnosis) if episode.diagnosis else None,
                "recovery_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
                "validation_status": episode.validation.status if episode.validation else None,
                "action_history": [action.value for action in episode.action_history],
                "validation_history": [validation.status for validation in episode.validations],
                "simulator_outcomes": [dict(execution.workload_state) for execution in episode.executions],
            },
        )
        episode.event = event
        if self.repository is not None:
            self.repository.save(event)

    def _learn(self, episode: RuntimeEpisode) -> None:
        episode.memory_version_before = getattr(self.memory, "memory_version", None)
        episode.experience_id = self.experience_store.save_episode(episode)
        episode.learning_update = self.learning_manager.update(episode)
        episode.memory_version_after = getattr(self.memory, "memory_version", None)
        if episode.state in (RuntimeState.RECOVERED, RuntimeState.RECOVERY_FAILED, RuntimeState.ESCALATED):
            episode.transition_to(RuntimeState.LEARNED, "complete episode stored and learning update applied")


def false_if_none(value: bool) -> bool:
    return bool(value)
