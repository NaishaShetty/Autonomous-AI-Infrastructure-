"""Measure bounded local controller overhead for the v2 artifact path."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
import time

from src.runtime.builder import build_runtime_system
from src.runtime.sources import DatasetReplaySource

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random"
FEATURES = ["job_start_time", "n_tasks", "n_distinct_task_names", "sum_inst_num", "mean_plan_cpu", "max_plan_cpu", "mean_plan_mem", "max_plan_mem", "mean_plan_gpu", "max_plan_gpu", "n_distinct_gpu_types", "n_instances", "n_distinct_machines", "mean_instance_start_time"]


def measure(system, n=50):
    values = []
    for i in range(n):
        obs = DatasetReplaySource([{"observation_id": f"overhead-{i}", "workload_id": "overhead", "features": {name: 0.0 for name in FEATURES}, "metrics": {"error_rate": 0.0}}], dataset_id="alibaba_gpu2020").observe()
        start = time.perf_counter(); system.controller.process(obs); values.append((time.perf_counter() - start) * 1000.0)
    ordered = sorted(values)
    return {"count": n, "median_ms": median(values), "p95_ms": ordered[int(0.95 * (n - 1))], "min_ms": min(values), "max_ms": max(values)}


def main():
    with TemporaryDirectory(prefix="v2-overhead-") as d:
        safe = build_runtime_system(workload_id="overhead", feature_names=FEATURES, experience_path=Path(d) / "safe.jsonl")
        loaded = build_runtime_system(workload_id="overhead", feature_names=FEATURES, artifact_path=ARTIFACT, expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0", experience_path=Path(d) / "loaded.jsonl")
        safe_stats, loaded_stats = measure(safe), measure(loaded)
    result = {"scope": "local sandbox controller timing; not a production benchmark", "safe_fallback": safe_stats, "artifact_loaded": loaded_stats, "median_delta_ms": loaded_stats["median_ms"] - safe_stats["median_ms"], "training_at_runtime": False}
    out = ROOT / "experiments/results/reliability_runtime_v2/logs/runtime_overhead.json"; out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__": main()
