"""Run the reliability-runtime-v1 data gate and reproducibility record.

The runner intentionally stops before training when the required operational
files are not available. It never substitutes simulator or frozen experiment
outputs for real training data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "results" / "reliability_runtime_v1"
PROTOCOL = OUT / "protocol.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    protocol_hash = sha256(PROTOCOL)
    candidates = {
        "agentrx_processed": ROOT / "data" / "processed" / "agentrx",
        "aiops_processed": ROOT / "data" / "processed" / "aiops_kpi",
        "aiops_audit": ROOT / "data" / "audit" / "aiops_kpi",
        "alibaba_processed": ROOT / "data" / "processed" / "alibaba_gpu2020",
        "alibaba_audit": ROOT / "data" / "audit" / "alibaba_gpu2020",
    }
    presence = {name: path.exists() for name, path in candidates.items()}
    data_available = any(presence.values())
    status = "ready_for_offline_training" if data_available else "data_gate_blocked"
    reason = (
        "At least one candidate data directory is present; dataset-specific loaders and leakage gates must pass before training."
        if data_available else
        "No raw, processed, or audit data directories are present in this checkout; training is prohibited."
    )
    results = {
        "experiment_id": "reliability_runtime_v1",
        "status": status,
        "training_performed": False,
        "artifact_generated": False,
        "dataset_presence": presence,
        "metrics": None,
        "calibration": None,
        "abstention": None,
        "runtime_integration": None,
        "reason": reason,
    }
    commit = git_commit()
    commit_timestamp = subprocess.check_output(["git", "show", "-s", "--format=%cI", commit], cwd=ROOT, text=True).strip()
    manifest = {
        "experiment_id": "reliability_runtime_v1",
        "protocol_version": "reliability-runtime-v1",
        "protocol_sha256": protocol_hash,
        "repository_commit": commit,
        "created_at": commit_timestamp,
        "seeds": [42],
        "software": {"python": __import__("platform").python_version()},
        "dataset_presence": presence,
        "artifact_hashes": {},
        "status": status,
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "protocol_sha256": protocol_hash, "repository_commit": manifest["repository_commit"], "dataset_presence": presence}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
