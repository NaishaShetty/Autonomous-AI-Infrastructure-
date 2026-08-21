"""Construction boundaries for experiment systems and the live runtime."""
from __future__ import annotations

from src.pipeline_builder import build_system as build_synthetic_experiment_system
from src.runtime.builder import RuntimeSystem, build_runtime_system


def build_default_runtime(*, artifact_path: str | None = None) -> RuntimeSystem:
    """Build an explicit runtime without training from benchmark data.

    Deployments or simulations may inject versioned model/calibrator artifacts
    through ``build_runtime_system``. The API default has no hidden training
    dependency and therefore abstains honestly until a model is configured.
    """
    return build_runtime_system(workload_id="runtime-default", feature_names=["f1", "f2", "f3", "f4", "f5"], artifact_path=artifact_path)


def build_default_pipeline() -> RuntimeSystem:
    """Compatibility name retained for callers migrating to RuntimeSystem."""
    return build_default_runtime()


# Historical research name remains explicit and available to benchmarks.
build_system = build_synthetic_experiment_system
