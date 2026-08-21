"""Run the deterministic autonomous runtime integration demonstration.

This is an architectural integration proof, not a production-performance
claim. It uses the explicitly labeled simulated recovery executor.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.runtime.builder import build_runtime_system


def _record(episode):
    matches = [item for item in episode.retrieved_experiences if getattr(item, "relevant", False)]
    return {
        "risk": episode.reliability.risk if episode.reliability else None,
        "reliability_confidence": episode.reliability.confidence if episode.reliability else None,
        "diagnosis_confidence": episode.diagnosis.confidence if episode.diagnosis else None,
        "uncertainty": episode.diagnosis.uncertainty if episode.diagnosis else None,
        "retrieved": len(episode.retrieved_experiences),
        "relevant": len(matches),
        "similarities": [getattr(item, "similarity", None) for item in episode.retrieved_experiences],
        "candidates": [action.value for action in episode.recovery_plan.candidate_actions] if episode.recovery_plan else [],
        "action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
        "abstained": bool(episode.recovery_plan and episode.recovery_plan.abstained),
        "safety": episode.recovery_plan.safety_status if episode.recovery_plan else None,
        "execution": episode.execution.success if episode.execution else None,
        "validation": episode.validation.status if episode.validation else None,
        "memory_before": episode.memory_version_before,
        "memory_after": episode.memory_version_after,
    }


def main() -> None:
    with TemporaryDirectory(prefix="autonomous-runtime-demo-") as directory:
        system = build_runtime_system(feature_names=["f1"], experience_path=Path(directory) / "episodes.jsonl")
        records = []
        for episode_id in ("episode-001", "episode-002"):
            observation = system.normalizer.normalize({
                "observation_id": episode_id,
                "workload_id": "demo-workload",
                "features": {"f1": 1.0},
                "resource_signals": {"gpu_utilization": 0.99},
                "source": "deterministic_simulator",
                "provenance": {"scenario": "repeated_resource_failure", "run": episode_id},
            })
            episode = system.controller.process(observation)
            record = _record(episode)
            records.append(record)
            print(f"Episode {episode_id}")
            print(f"  state: {episode.state.value}")
            print(f"  reliability: risk={record['risk']} confidence={record['reliability_confidence']}")
            print(f"  retrieval: {record['retrieved']} total, {record['relevant']} relevant, similarities={record['similarities']}")
            print(f"  diagnosis: confidence={record['diagnosis_confidence']} uncertainty={record['uncertainty']}")
            print(f"  recovery: candidates={record['candidates']} selected={record['action']}")
            print(f"  safety={record['safety']} abstained={record['abstained']} execution={record['execution']} validation={record['validation']}")
            print(f"  memory version: {record['memory_before']} -> {record['memory_after']}")

        first, second = records
        print("Influence deltas: second episode minus first episode")
        print(f"  risk_delta: {second['risk'] - first['risk']}")
        print(f"  diagnosis_confidence_delta: {second['diagnosis_confidence'] - first['diagnosis_confidence']}")
        print(f"  uncertainty_delta: {second['uncertainty'] - first['uncertainty']}")
        print(f"  retrieval_delta: {second['retrieved'] - first['retrieved']}")
        print(f"  relevant_retrieval_delta: {second['relevant'] - first['relevant']}")
        print(f"  action_changed: {second['action'] != first['action']}")
        print(f"  outcome_changed: {second['validation'] != first['validation']}")
        print("Interpretation: retrieval and diagnosis evidence are measurable; this two-episode demonstration is not a statistical performance claim.")


if __name__ == "__main__":
    main()
