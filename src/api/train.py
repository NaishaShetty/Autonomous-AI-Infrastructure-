"""Construction boundaries for experiment systems and the live runtime."""
from __future__ import annotations

from src.decision.policy import DecisionMode, DecisionPolicy
from src.pipeline_builder import build_system as build_synthetic_experiment_system
from src.runtime.builder import RuntimeSystem, build_runtime_system
from src.storage.repository import EventRepository

from .pipeline import ReliabilityPipeline

WORKLOAD_ID = "synthetic-regime-stream"

def build_default_runtime(*, artifact_path: str | None = None, repository: EventRepository | None = None) -> RuntimeSystem:
    """Build an explicit runtime without training from benchmark data.

    Deployments or simulations may inject versioned model/calibrator artifacts
    through ``build_runtime_system``. The API default has no hidden training
    dependency and therefore abstains honestly until a model is configured.
    """
    return build_runtime_system(
        workload_id="runtime-default",
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        artifact_path=artifact_path,
        repository=repository,
    )


def build_default_pipeline(repository: EventRepository | None = None) -> ReliabilityPipeline:
    """Build the trained synthetic pipeline used by legacy benchmarks."""
    system = build_synthetic_experiment_system()
    failure_memory = system.failure_memory
    if repository is not None:
        failure_memory.merge_from_repository(repository, workload_id=WORKLOAD_ID)
        if failure_memory.is_dirty:
            failure_memory.rebuild()
    return ReliabilityPipeline(
        workload_model=system.workload_model,
        calibrator=system.calibrator,
        failure_memory=failure_memory,
        policy=DecisionPolicy(),
        feature_names=system.feature_names,
        workload_id=WORKLOAD_ID,
        mode=DecisionMode.COMBINED,
    )


# Historical research name remains explicit and available to benchmarks.
build_system = build_synthetic_experiment_system
