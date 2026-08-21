"""Construction of the canonical runtime from explicit components."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.decision.policy import DecisionMode, DecisionPolicy
from src.failure_memory.memory import FailureMemory

from .components import EvidenceDiagnosisEngine, ObservationFailureDetector, RuleBasedRecoveryPlanner, SignalRecoveryValidator, SimulatedRecoveryExecutor
from .experience import JsonExperienceStore
from .learning import RuntimeLearningManager
from .observation import MappingEventNormalizer
from .controller import RuntimeController


class UnconfiguredReliabilityAssessor:
    """Honest runtime fallback when no workload model artifact is configured."""

    def assess(self, observation, retrieved=()):
        from .contracts import ReliabilityAssessment
        return ReliabilityAssessment(confidence=0.5, risk=0.0, decision="ABSTAIN", fused_score=0.0, uncertainty=1.0, predicted_label=None, model_id="unconfigured", model_version="none", calibrator_version="none", training_data_id=None, configuration={"safe_default": True})


@dataclass
class RuntimeSystem:
    controller: RuntimeController
    normalizer: MappingEventNormalizer
    failure_memory: FailureMemory
    experience_store: JsonExperienceStore


def build_runtime_system(*, workload_id: str = "default-workload", feature_names: list[str] | None = None, workload_model: Any | None = None, calibrator: Any | None = None, failure_memory: FailureMemory | None = None, policy: DecisionPolicy | None = None, diagnosis=None, planner=None, executor=None, validator=None, experience_path: str | Path | None = None, repository=None, max_attempts: int = 1, relevance_threshold: float = 0.5, model_id: str = "injected-workload-model", model_version: str = "unknown", calibrator_version: str = "unknown", training_data_id: str = "unknown", model_configuration: dict[str, Any] | None = None) -> RuntimeSystem:
    """Build the runtime from explicit dependencies.

    No dataset is loaded and no model is trained here. A caller that has
    trained, versioned model/calibrator artifacts may inject them. Without
    those artifacts, the runtime remains operational but honestly abstains
    rather than silently manufacturing a model from benchmark data.
    """
    names = list(feature_names or [])
    memory = failure_memory or FailureMemory(names or ["failure_signal"])
    if workload_model is not None and calibrator is not None:
        from .components import ModelReliabilityAssessor
        assessor = ModelReliabilityAssessor(workload_model, calibrator, memory, policy or DecisionPolicy(), names, DecisionMode.COMBINED, model_id=model_id, model_version=model_version, calibrator_version=calibrator_version, training_data_id=training_data_id, configuration=model_configuration)
    else:
        assessor = UnconfiguredReliabilityAssessor()
    experience_store = JsonExperienceStore(experience_path)
    controller = RuntimeController(
        detector=ObservationFailureDetector(),
        assessor=assessor,
        memory=memory,
        diagnosis=diagnosis or EvidenceDiagnosisEngine(),
        planner=planner or RuleBasedRecoveryPlanner(),
        executor=executor or SimulatedRecoveryExecutor(),
        validator=validator or SignalRecoveryValidator(),
        experience_store=experience_store,
        learning_manager=RuntimeLearningManager(memory),
        repository=repository,
        workload_id=workload_id,
        max_attempts=max_attempts,
        relevance_threshold=relevance_threshold,
    )
    return RuntimeSystem(controller=controller, normalizer=MappingEventNormalizer(), failure_memory=memory, experience_store=experience_store)
