from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.phase3_contract import (
    ImmutableExperimentStore,
    ExperimentContract,
    deterministic_identifier,
    validate_manifest,
)


def contract() -> ExperimentContract:
    return ExperimentContract(
        experiment_id="reliability-model-audit",
        hypothesis="A candidate model improves calibrated risk without increasing unsafe decisions.",
        baseline="frozen-v1.0",
        intervention="audit-only-placeholder",
        dataset="declared-dataset",
        dataset_version="v1",
        split="declared-split",
        feature_set="declared-features",
        model="declared-model",
        calibration="declared-calibration",
        random_seed=7,
        evaluation_protocol="phase3-evaluation-contract-v1",
        metrics=("auroc", "brier", "unsafe_action_rate"),
        software_version="test",
        artifact_identity="artifact-sha256:declared",
    )


def test_identifier_is_stable_for_mapping_order() -> None:
    left = deterministic_identifier("experiment", {"b": 2, "a": 1})
    right = deterministic_identifier("experiment", {"a": 1, "b": 2})
    assert left == right
    assert left.startswith("experiment-")


def test_contract_round_trip_and_hash_are_stable() -> None:
    original = contract()
    restored = ExperimentContract.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original
    assert restored.contract_hash == original.contract_hash


def test_contract_requires_all_fields() -> None:
    payload = contract().to_dict()
    del payload["calibration"]
    with pytest.raises(ValueError, match="calibration"):
        ExperimentContract.from_dict(payload)


def test_manifest_validation() -> None:
    current = contract()
    manifest = {"experiment_id": current.experiment_id, "contract_hash": current.contract_hash, "status": "planned"}
    validate_manifest(manifest, current)
    with pytest.raises(ValueError, match="contract_hash"):
        validate_manifest({**manifest, "contract_hash": "wrong"}, current)


def test_finalization_serializes_expected_artifacts_and_is_immutable(tmp_path: Path) -> None:
    current = contract()
    store = ImmutableExperimentStore(tmp_path, current)
    path = store.finalize(
        protocol={"contract": current.to_dict()},
        manifest={"experiment_id": current.experiment_id, "contract_hash": current.contract_hash, "status": "finalized"},
        results={"status": "not_run"},
        summary={"decision": "pending"},
        report="# Reserved experiment result",
        per_seed={7: {"status": "not_run"}},
    )
    assert {p.name for p in path.iterdir()} == {
        ".finalized", "protocol.json", "manifest.json", "results.json", "summary.json", "report.md", "per_seed"
    }
    with pytest.raises(FileExistsError, match="finalized"):
        store.finalize(protocol={}, manifest={}, results={}, summary={}, report="")
