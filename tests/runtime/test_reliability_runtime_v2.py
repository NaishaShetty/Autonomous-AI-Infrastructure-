from __future__ import annotations

from pathlib import Path

from src.runtime.builder import build_runtime_system
from src.runtime.sources import DatasetReplaySource

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random"
FEATURES = ["job_start_time", "n_tasks", "n_distinct_task_names", "sum_inst_num", "mean_plan_cpu", "max_plan_cpu", "mean_plan_mem", "max_plan_mem", "mean_plan_gpu", "max_plan_gpu", "n_distinct_gpu_types", "n_instances", "n_distinct_machines", "mean_instance_start_time"]


def test_alibaba_artifact_replay_persists_provenance(tmp_path):
    record = {"observation_id": "test-alibaba-v2", "workload_id": "alibaba-gpu2020-job-risk", "features": {name: 0.0 for name in FEATURES}, "metrics": {"error_rate": 0.9}, "provenance": {"dataset_id": "alibaba_gpu2020", "split": "random_stratified"}}
    system = build_runtime_system(workload_id="alibaba-gpu2020-job-risk", feature_names=FEATURES, artifact_path=ARTIFACT, expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0", experience_path=tmp_path / "episodes.jsonl")
    observation = DatasetReplaySource([record], dataset_id="alibaba_gpu2020").observe()
    episode = system.controller.process(observation)
    assert observation.source_type.value == "dataset_replay"
    assert episode.detection.detected
    assert episode.reliability is not None
    assert episode.reliability.artifact_hash
    assert episode.reliability.model_id == "alibaba-gpu2020-job-risk-logistic"
    assert 0.0 <= episode.reliability.confidence <= 1.0
    assert 0.0 <= episode.reliability.uncertainty <= 1.0
    assert episode.event is not None
    assert episode.event.metadata["observation_source_type"] == "dataset_replay"
    assert episode.event.metadata["reliability_provenance"]["artifact_loaded"] is True
    assert episode.event.metadata["artifact_hash"] == episode.reliability.artifact_hash
