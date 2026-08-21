"""Canonical runtime reliability/observability smoke proof.

This is bounded simulator evidence only. It does not claim production
self-healing, live connector availability, or statistical performance.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.runtime.builder import build_runtime_system
from src.runtime.sources import DeterministicSimulatorSource


def main() -> None:
    with TemporaryDirectory(prefix="runtime-reliability-smoke-") as directory:
        system = build_runtime_system(
            workload_id="smoke-workload",
            feature_names=["f1"],
            experience_path=Path(directory) / "episodes.jsonl",
            max_attempts=1,
        )
        source = DeterministicSimulatorSource(
            [{
                "observation_id": "smoke-001",
                "workload_id": "smoke-workload",
                "features": {"f1": 1.0},
                "metrics": {"error_rate": 0.9},
                "latency_seconds": 2.5,
                "throughput_per_second": 0.2,
                "resource_signals": {"cpu_utilization": 0.99},
                "model_confidence": 0.41,
                "deployment_id": "sim-deployment-1",
            }],
            scenario_id="observed_failure_abstention_recovery",
        )
        observation = source.observe()
        episode = system.controller.process(observation)
        assert observation.source_type.value == "simulator"
        assert episode.detection is not None and episode.detection.detected
        assert episode.reliability is not None and episode.reliability.decision == "ABSTAIN"
        assert episode.diagnosis is not None
        assert episode.recovery_plan is not None
        assert episode.validation is not None
        assert episode.experience_id is not None
        assert episode.event is not None
        assert episode.event.metadata["observation_source_type"] == "simulator"
        assert episode.event.metadata["detection_provenance"]["observation_id"] == "smoke-001"
        print({
            "source": observation.source_type.value,
            "detected": episode.detection.detected,
            "reliability_decision": episode.reliability.decision,
            "artifact_hash": episode.reliability.artifact_hash,
            "diagnosed": episode.diagnosis.failure_type is not None,
            "recovery_action": episode.recovery_plan.selected_action.value,
            "validation": episode.validation.status,
            "experience_id": episode.experience_id,
            "bounded_evidence": True,
        })


if __name__ == "__main__":
    main()
