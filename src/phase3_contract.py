"""Phase 3 experiment contracts and immutable result storage.

This module is deliberately independent of the frozen V1 runtime.  It provides
only research bookkeeping and serialization primitives for future V1.1 work.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CONTRACT_FIELDS = (
    "experiment_id", "hypothesis", "baseline", "intervention", "dataset",
    "dataset_version", "split", "feature_set", "model", "calibration",
    "random_seed", "evaluation_protocol", "metrics", "software_version",
    "artifact_identity",
)
ARTIFACT_FILES = ("protocol.json", "manifest.json", "results.json", "summary.json", "report.md")


def canonical_json(value: Any) -> str:
    """Return stable JSON suitable for hashes and cross-process identifiers."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deterministic_identifier(namespace: str, value: Any, length: int = 16) -> str:
    """Create a stable identifier without Python's process-dependent ``hash``."""
    if not namespace or length < 8:
        raise ValueError("namespace must be non-empty and length must be at least 8")
    digest = hashlib.sha256(f"{namespace}|{canonical_json(value)}".encode("utf-8")).hexdigest()
    return f"{namespace}-{digest[:length]}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class ExperimentContract:
    experiment_id: str
    hypothesis: str
    baseline: str
    intervention: str
    dataset: str
    dataset_version: str
    split: str
    feature_set: str
    model: str
    calibration: str
    random_seed: int
    evaluation_protocol: str
    metrics: tuple[str, ...]
    software_version: str
    artifact_identity: str

    def __post_init__(self) -> None:
        for field in CONTRACT_FIELDS:
            value = getattr(self, field)
            if value is None or value == "" or value == ():
                raise ValueError(f"contract field '{field}' must be declared")
        if not isinstance(self.random_seed, int) or isinstance(self.random_seed, bool):
            raise TypeError("random_seed must be an integer")
        if not self.metrics or any(not isinstance(metric, str) or not metric for metric in self.metrics):
            raise ValueError("metrics must contain non-empty names")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExperimentContract":
        missing = [field for field in CONTRACT_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"missing contract fields: {', '.join(missing)}")
        values = dict(payload)
        values["metrics"] = tuple(values["metrics"])
        return cls(**{field: values[field] for field in CONTRACT_FIELDS})

    @property
    def contract_hash(self) -> str:
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


class ImmutableExperimentStore:
    """Write one experiment exactly once after it has been finalized."""

    def __init__(self, root: Path, contract: ExperimentContract) -> None:
        self.root = Path(root) / contract.experiment_id
        self.contract = contract

    @property
    def finalized_marker(self) -> Path:
        return self.root / ".finalized"

    def _ensure_writable(self) -> None:
        if self.finalized_marker.exists():
            raise FileExistsError(f"experiment is finalized: {self.contract.experiment_id}")

    def finalize(
        self,
        *,
        protocol: Mapping[str, Any],
        manifest: Mapping[str, Any],
        results: Mapping[str, Any],
        summary: Mapping[str, Any],
        report: str,
        per_seed: Mapping[int, Mapping[str, Any]] | None = None,
    ) -> Path:
        self._ensure_writable()
        self.root.mkdir(parents=True, exist_ok=False)
        payloads: dict[str, str] = {
            "protocol.json": canonical_json(dict(protocol)) + "\n",
            "manifest.json": canonical_json(dict(manifest)) + "\n",
            "results.json": canonical_json(dict(results)) + "\n",
            "summary.json": canonical_json(dict(summary)) + "\n",
            "report.md": report.rstrip() + "\n",
        }
        for filename, content in payloads.items():
            (self.root / filename).write_text(content, encoding="utf-8")
        if per_seed:
            seed_dir = self.root / "per_seed"
            seed_dir.mkdir()
            for seed, seed_result in sorted(per_seed.items()):
                (seed_dir / f"seed_{seed}.json").write_text(canonical_json(dict(seed_result)) + "\n", encoding="utf-8")
        metadata = {
            "experiment_id": self.contract.experiment_id,
            "contract_hash": self.contract.contract_hash,
            "finalized_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": {name: sha256_file(self.root / name) for name in ARTIFACT_FILES},
        }
        (self.root / ".finalized").write_text(canonical_json(metadata) + "\n", encoding="utf-8")
        return self.root


def validate_manifest(manifest: Mapping[str, Any], contract: ExperimentContract) -> None:
    """Validate the minimum identity fields before a result is accepted."""
    if manifest.get("experiment_id") != contract.experiment_id:
        raise ValueError("manifest experiment_id does not match contract")
    if manifest.get("contract_hash") != contract.contract_hash:
        raise ValueError("manifest contract_hash does not match contract")
    if manifest.get("status") not in {"planned", "completed", "finalized"}:
        raise ValueError("manifest status must be planned, completed, or finalized")
