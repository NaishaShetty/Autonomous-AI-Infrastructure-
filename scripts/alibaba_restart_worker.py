"""Worker for two-process Alibaba artifact and failure-memory restart proof."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np

from src.runtime.builder import build_runtime_system
from src.runtime.sources import DatasetReplaySource
from src.storage.db import get_session, init_db
from src.storage.repository import EventRepository

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random"
FEATURES = ["job_start_time", "n_tasks", "n_distinct_task_names", "sum_inst_num", "mean_plan_cpu", "max_plan_cpu", "mean_plan_mem", "max_plan_mem", "mean_plan_gpu", "max_plan_gpu", "n_distinct_gpu_types", "n_instances", "n_distinct_machines", "mean_instance_start_time"]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: alibaba_restart_worker.py <A|B> <output.json>")
    mode, output = sys.argv[1], Path(sys.argv[2])
    database_url = os.environ["DATABASE_URL"]
    init_db(database_url)
    record = {"observation_id": f"restart-{mode}", "workload_id": "alibaba-restart", "features": {name: 0.0 for name in FEATURES}, "metrics": {"error_rate": 0.9, "latency_ms": 2500.0}, "provenance": {"dataset_id": "alibaba_gpu2020", "split": "random_stratified", "process": mode}}
    with get_session() as session:
        repo = EventRepository(session)
        runtime = build_runtime_system(workload_id="alibaba-restart", feature_names=FEATURES, artifact_path=ARTIFACT, expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0", experience_path=output.parent / "episodes.jsonl", repository=repo, relevance_threshold=0.5)
        observation = DatasetReplaySource([record], dataset_id="alibaba_gpu2020").observe()
        vector = np.array([observation.features.get(name, 0.0) for name in FEATURES], dtype=float)
        model_prediction = runtime.controller.assessor.workload_model.predict(vector)
        episode = runtime.controller.process(observation)
        result = {"process": mode, "observation_id": observation.observation_id, "artifact_hash": episode.reliability.artifact_hash if episode.reliability else None, "model_version": episode.reliability.model_version if episode.reliability else None, "calibrator_version": episode.reliability.calibrator_version if episode.reliability else None, "model_predicted_label": model_prediction.predicted_label, "model_predicted_proba": model_prediction.predicted_proba, "memory_risk": episode.reliability.risk if episode.reliability else None, "retrieved_experiences": len(episode.retrieved_experiences), "memory_version": runtime.failure_memory.memory_version, "memory_fitted": runtime.failure_memory.status()["fitted"], "experience_id": episode.experience_id, "validation": episode.validation.status if episode.validation else None, "runtime_training": False}
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
