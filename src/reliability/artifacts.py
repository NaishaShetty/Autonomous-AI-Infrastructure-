"""Versioned reliability model/calibrator artifacts.

This module deliberately separates offline serialization from runtime loading.
The runtime loader never fits a model, and invalid artifacts raise a typed error
so callers can fail safely to an abstaining configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pickle
from typing import Any, Mapping


class ArtifactValidationError(ValueError):
    """Raised when a reliability artifact is missing, incompatible, or unsafe."""


@dataclass(frozen=True)
class ReliabilityArtifactManifest:
    artifact_version: str
    model_id: str
    model_version: str
    calibrator_version: str
    feature_schema_version: str
    feature_names: tuple[str, ...]
    training_dataset_id: str
    validation_dataset_id: str
    evaluation_dataset_id: str
    training_timestamp: str
    repository_commit: str
    protocol_version: str
    protocol_hash: str
    evaluation_metrics: Mapping[str, float]
    calibration_metrics: Mapping[str, float]
    model_sha256: str
    calibrator_sha256: str
    artifact_sha256: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_version": self.artifact_version,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "calibrator_version": self.calibrator_version,
            "feature_schema_version": self.feature_schema_version,
            "feature_names": list(self.feature_names),
            "training_dataset_id": self.training_dataset_id,
            "validation_dataset_id": self.validation_dataset_id,
            "evaluation_dataset_id": self.evaluation_dataset_id,
            "training_timestamp": self.training_timestamp,
            "repository_commit": self.repository_commit,
            "protocol_version": self.protocol_version,
            "protocol_hash": self.protocol_hash,
            "evaluation_metrics": dict(self.evaluation_metrics),
            "calibration_metrics": dict(self.calibration_metrics),
            "model_sha256": self.model_sha256,
            "calibrator_sha256": self.calibrator_sha256,
            "artifact_sha256": self.artifact_sha256,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ReliabilityArtifactManifest":
        required = {
            "artifact_version", "model_id", "model_version", "calibrator_version",
            "feature_schema_version", "feature_names", "training_dataset_id",
            "validation_dataset_id", "evaluation_dataset_id", "training_timestamp",
            "repository_commit", "protocol_version", "protocol_hash",
            "evaluation_metrics", "calibration_metrics", "model_sha256",
            "calibrator_sha256", "artifact_sha256", "created_at",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ArtifactValidationError(f"artifact manifest missing fields: {missing}")
        return cls(
            artifact_version=str(value["artifact_version"]),
            model_id=str(value["model_id"]),
            model_version=str(value["model_version"]),
            calibrator_version=str(value["calibrator_version"]),
            feature_schema_version=str(value["feature_schema_version"]),
            feature_names=tuple(str(item) for item in value["feature_names"]),
            training_dataset_id=str(value["training_dataset_id"]),
            validation_dataset_id=str(value["validation_dataset_id"]),
            evaluation_dataset_id=str(value["evaluation_dataset_id"]),
            training_timestamp=str(value["training_timestamp"]),
            repository_commit=str(value["repository_commit"]),
            protocol_version=str(value["protocol_version"]),
            protocol_hash=str(value["protocol_hash"]),
            evaluation_metrics=dict(value["evaluation_metrics"]),
            calibration_metrics=dict(value["calibration_metrics"]),
            model_sha256=str(value["model_sha256"]),
            calibrator_sha256=str(value["calibrator_sha256"]),
            artifact_sha256=str(value["artifact_sha256"]),
            created_at=str(value["created_at"]),
        )


@dataclass(frozen=True)
class LoadedReliabilityArtifact:
    model: Any
    calibrator: Any
    manifest: ReliabilityArtifactManifest


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_manifest(manifest: ReliabilityArtifactManifest) -> None:
    if not manifest.training_dataset_id or not manifest.validation_dataset_id or not manifest.evaluation_dataset_id:
        raise ArtifactValidationError("training, validation, and evaluation dataset identities are required")
    dataset_ids = {manifest.training_dataset_id, manifest.validation_dataset_id, manifest.evaluation_dataset_id}
    if len(dataset_ids) != 3:
        raise ArtifactValidationError("training, validation, and evaluation dataset identities must be disjoint")
    if not manifest.model_sha256 or not manifest.calibrator_sha256 or not manifest.artifact_sha256:
        raise ArtifactValidationError("artifact hashes are required")
    if not manifest.repository_commit or not manifest.protocol_hash:
        raise ArtifactValidationError("repository commit and protocol hash are required")


def save_reliability_artifact(
    output_dir: str | Path,
    model: Any,
    calibrator: Any,
    *,
    artifact_version: str,
    model_id: str,
    model_version: str,
    calibrator_version: str,
    feature_schema_version: str,
    feature_names: list[str],
    training_dataset_id: str,
    validation_dataset_id: str,
    evaluation_dataset_id: str,
    training_timestamp: str,
    repository_commit: str,
    protocol_version: str,
    protocol_hash: str,
    evaluation_metrics: Mapping[str, float],
    calibration_metrics: Mapping[str, float],
    created_at: str | None = None,
) -> ReliabilityArtifactManifest:
    """Serialize already-trained objects with required provenance metadata.

    Training must happen outside this function. The function refuses overlapping
    dataset identities so evaluation data cannot silently enter artifact creation.
    """
    dataset_ids = {training_dataset_id, validation_dataset_id, evaluation_dataset_id}
    if len(dataset_ids) != 3:
        raise ArtifactValidationError("training, validation, and evaluation dataset identities must be disjoint")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model_path = output / "model.pkl"
    calibrator_path = output / "calibrator.pkl"
    with model_path.open("wb") as handle:
        pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with calibrator_path.open("wb") as handle:
        pickle.dump(calibrator, handle, protocol=pickle.HIGHEST_PROTOCOL)
    model_hash = _sha256(model_path)
    calibrator_hash = _sha256(calibrator_path)
    artifact_hash = hashlib.sha256((model_hash + calibrator_hash).encode()).hexdigest()
    manifest = ReliabilityArtifactManifest(
        artifact_version=artifact_version,
        model_id=model_id,
        model_version=model_version,
        calibrator_version=calibrator_version,
        feature_schema_version=feature_schema_version,
        feature_names=tuple(feature_names),
        training_dataset_id=training_dataset_id,
        validation_dataset_id=validation_dataset_id,
        evaluation_dataset_id=evaluation_dataset_id,
        training_timestamp=training_timestamp,
        repository_commit=repository_commit,
        protocol_version=protocol_version,
        protocol_hash=protocol_hash,
        evaluation_metrics=dict(evaluation_metrics),
        calibration_metrics=dict(calibration_metrics),
        model_sha256=model_hash,
        calibrator_sha256=calibrator_hash,
        artifact_sha256=artifact_hash,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
    )
    _validate_manifest(manifest)
    (output / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n")
    return manifest


def load_reliability_artifact(path: str | Path, *, expected_feature_names: list[str] | None = None, expected_artifact_version: str | None = None, expected_model_version: str | None = None, expected_calibrator_version: str | None = None) -> LoadedReliabilityArtifact:
    """Validate and load an artifact without fitting or mutating its objects."""
    directory = Path(path)
    manifest_path = directory / "manifest.json"
    model_path = directory / "model.pkl"
    calibrator_path = directory / "calibrator.pkl"
    if not directory.is_dir() or not manifest_path.is_file() or not model_path.is_file() or not calibrator_path.is_file():
        raise ArtifactValidationError("artifact directory must contain manifest.json, model.pkl, and calibrator.pkl")
    try:
        manifest = ReliabilityArtifactManifest.from_dict(json.loads(manifest_path.read_text()))
        _validate_manifest(manifest)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, ArtifactValidationError):
            raise
        raise ArtifactValidationError(f"invalid artifact manifest: {exc}") from exc
    if expected_feature_names is not None and tuple(expected_feature_names) != manifest.feature_names:
        raise ArtifactValidationError("artifact feature schema does not match runtime feature names")
    if expected_artifact_version is not None and manifest.artifact_version != expected_artifact_version:
        raise ArtifactValidationError("artifact version is incompatible with the runtime")
    if expected_model_version is not None and manifest.model_version != expected_model_version:
        raise ArtifactValidationError("model version is incompatible with the runtime")
    if expected_calibrator_version is not None and manifest.calibrator_version != expected_calibrator_version:
        raise ArtifactValidationError("calibrator version is incompatible with the runtime")
    if _sha256(model_path) != manifest.model_sha256 or _sha256(calibrator_path) != manifest.calibrator_sha256:
        raise ArtifactValidationError("artifact component hash mismatch")
    actual_artifact_hash = hashlib.sha256((manifest.model_sha256 + manifest.calibrator_sha256).encode()).hexdigest()
    if actual_artifact_hash != manifest.artifact_sha256:
        raise ArtifactValidationError("artifact hash mismatch")
    try:
        with model_path.open("rb") as handle:
            model = pickle.load(handle)
        with calibrator_path.open("rb") as handle:
            calibrator = pickle.load(handle)
    except Exception as exc:  # noqa: BLE001 - safe loader converts all deserialization errors
        raise ArtifactValidationError(f"artifact deserialization failed: {exc}") from exc
    return LoadedReliabilityArtifact(model=model, calibrator=calibrator, manifest=manifest)
