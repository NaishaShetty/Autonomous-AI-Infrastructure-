from __future__ import annotations

import pytest

from src.reliability.artifacts import ArtifactValidationError, load_reliability_artifact, save_reliability_artifact
from src.runtime.builder import build_runtime_system
from src.runtime.components import ObservationFailureDetector
from src.runtime.observation import MappingEventNormalizer
from src.runtime.sources import DatasetReplaySource, SyntheticTestSource


def test_normalizer_preserves_rich_telemetry_and_source_type() -> None:
    observation = MappingEventNormalizer().normalize({
        "workload_id": "w",
        "features": {"f1": 1},
        "latency_seconds": 1.2,
        "throughput_per_second": 5,
        "model_confidence": 0.7,
        "deployment_id": "d1",
        "source": "live",
    })
    assert observation.source_type.value == "live"
    assert observation.throughput_per_second == 5.0
    assert observation.model_confidence == 0.7
    assert observation.provenance["source_type"] == "live"


def test_replay_and_synthetic_sources_share_contract() -> None:
    replay = DatasetReplaySource([{"workload_id": "w", "features": {"f1": 1}}], "agentrx-v1")
    synthetic = SyntheticTestSource([{"workload_id": "w", "features": {"f1": 1}}])
    assert replay.observe().source_type.value == "dataset_replay"
    assert synthetic.observe().source_type.value == "synthetic_test"


def test_detector_keeps_detection_separate_and_records_provenance() -> None:
    observation = MappingEventNormalizer().normalize({
        "observation_id": "o1",
        "workload_id": "w",
        "features": {},
        "latency_seconds": 2.0,
        "throughput_per_second": 0.1,
        "source": "synthetic_test",
    })
    result = ObservationFailureDetector(latency_seconds_threshold=1.0, throughput_floor=0.5).detect(observation)
    assert result.detected
    assert result.failure_type == "latency_failure"
    assert result.detection_type == "declared_thresholds_and_errors"
    assert result.provenance["observation_id"] == "o1"


def test_artifact_round_trip_and_disjoint_dataset_guard(tmp_path) -> None:
    manifest = save_reliability_artifact(
        tmp_path / "artifact",
        {"model": "offline"},
        {"calibrator": "offline"},
        artifact_version="rel-1",
        model_id="m1",
        model_version="1.0",
        calibrator_version="1.0",
        feature_schema_version="features-v1",
        feature_names=["f1"],
        training_dataset_id="train-a",
        validation_dataset_id="validation-b",
        evaluation_dataset_id="evaluation-c",
        training_timestamp="2026-08-21T00:00:00+00:00",
        repository_commit="abc123",
        protocol_version="protocol-v1",
        protocol_hash="protocol-hash",
        evaluation_metrics={"accuracy": 0.8},
        calibration_metrics={"ece": 0.1},
    )
    loaded = load_reliability_artifact(tmp_path / "artifact", expected_feature_names=["f1"])
    assert loaded.manifest.artifact_sha256 == manifest.artifact_sha256
    assert loaded.model == {"model": "offline"}
    with pytest.raises(ArtifactValidationError):
        save_reliability_artifact(
            tmp_path / "bad",
            object(),
            object(),
            artifact_version="rel-1", model_id="m1", model_version="1", calibrator_version="1",
            feature_schema_version="v1", feature_names=["f1"], training_dataset_id="same",
            validation_dataset_id="same", evaluation_dataset_id="eval", training_timestamp="t",
            repository_commit="abc", protocol_version="p", protocol_hash="h",
            evaluation_metrics={}, calibration_metrics={},
        )


def test_default_runtime_does_not_train_and_abstains() -> None:
    system = build_runtime_system(feature_names=["f1"])
    episode = system.controller.process(system.normalizer.normalize({"features": {"f1": 1}, "source": "synthetic_test"}))
    assert episode.reliability is not None
    assert episode.reliability.model_id == "unconfigured"
    assert episode.reliability.decision == "ABSTAIN"
