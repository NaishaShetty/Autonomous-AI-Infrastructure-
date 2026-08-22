"""Replay one acquired Alibaba job through the canonical runtime artifact path."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.real_data.phase3_1_rd_alibaba_evaluate import build_feature_matrix, NUMERIC_COLS
from src.runtime.builder import build_runtime_system
from src.runtime.sources import DatasetReplaySource

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "experiments/results/reliability_runtime_v2/artifacts/random"
SPLITS = ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json"


def main() -> None:
    df = build_feature_matrix()
    sample_id = json.loads(SPLITS.read_text())["test"][0]
    row = df[df.job_name == sample_id].iloc[0]
    record = {
        "observation_id": f"alibaba-replay-{sample_id}",
        "workload_id": "alibaba-gpu2020-job-risk",
        "features": {name: float(row[name]) if row[name] == row[name] else 0.0 for name in NUMERIC_COLS},
        "metrics": {"error_rate": 0.9},
        "provenance": {"dataset_id": "alibaba_gpu2020", "split": "random_stratified", "role": "evaluation_replay"},
    }
    with TemporaryDirectory(prefix="alibaba-v2-replay-") as directory:
        system = build_runtime_system(workload_id="alibaba-gpu2020-job-risk", feature_names=NUMERIC_COLS, artifact_path=ARTIFACT, expected_artifact_version="reliability-runtime-v2-artifact-1", expected_model_version="v2.0.0", expected_calibrator_version="isotonic-v2.0.0", experience_path=Path(directory) / "episodes.jsonl")
        observation = DatasetReplaySource([record], dataset_id="alibaba_gpu2020").observe()
        episode = system.controller.process(observation)
        assert observation.source_type.value == "dataset_replay"
        assert episode.detection.detected
        assert episode.reliability is not None and episode.reliability.artifact_hash
        assert episode.event is not None
        assert episode.event.metadata["reliability_provenance"]["artifact_loaded"] is True
        trace = {"source_type": observation.source_type.value, "source_provenance": dict(observation.provenance), "detection_provenance": dict(episode.detection.provenance), "reliability_provenance": dict(episode.reliability.provenance), "artifact_hash": episode.reliability.artifact_hash, "model_id": episode.reliability.model_id, "model_version": episode.reliability.model_version, "calibrator_version": episode.reliability.calibrator_version, "risk": episode.reliability.risk, "uncertainty": episode.reliability.uncertainty, "decision": episode.reliability.decision, "episode_id": observation.observation_id, "diagnosis": episode.diagnosis.failure_type if episode.diagnosis else None, "recovery_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None, "validation": episode.validation.status if episode.validation else None, "experience_id": episode.experience_id, "bounded_replay_evidence": True}
    log = ROOT / "experiments/results/reliability_runtime_v2/logs/runtime_replay.json"
    log.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    print(json.dumps(trace, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
