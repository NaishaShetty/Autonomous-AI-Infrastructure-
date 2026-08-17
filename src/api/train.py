from __future__ import annotations

from src.decision.policy import DecisionMode, DecisionPolicy
from src.pipeline_builder import build_system

from .pipeline import ReliabilityPipeline


def build_default_pipeline() -> ReliabilityPipeline:
    """Builds the demo pipeline used by the live API on startup. Uses the
    same ``build_system`` training procedure as the benchmark harness (see
    ``src/pipeline_builder.py`` docstring) so the API never diverges from
    what the benchmarks report."""
    system = build_system()
    return ReliabilityPipeline(
        workload_model=system.workload_model,
        calibrator=system.calibrator,
        failure_memory=system.failure_memory,
        policy=DecisionPolicy(),
        feature_names=system.feature_names,
        workload_id="synthetic-regime-stream",
        mode=DecisionMode.COMBINED,
    )
