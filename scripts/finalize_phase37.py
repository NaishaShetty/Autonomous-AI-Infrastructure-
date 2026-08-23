"""Finalize the Phase 3.7 candidate-discovery design artifacts immutably."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/v1_1/candidate_discovery/3_7"
MARKER = OUT / ".finalized"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if MARKER.exists():
        raise SystemExit("Phase 3.7 is already finalized; refusing overwrite")
    files = sorted(
        p for p in OUT.rglob("*")
        if p.is_file() and p.name not in {".finalized", "manifest.json"}
    )
    if not files:
        raise SystemExit("No Phase 3.7 artifacts found")
    manifest = {
        "experiment_id": "phase37_v11_candidate_discovery_design",
        "phase": "3.7",
        "status": "PREREGISTERED_DESIGN_ONLY",
        "v1_status": "FROZEN",
        "decision": "V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET",
        "primary_architecture": "RELIABILITY/DECISION ARCHITECTURE",
        "selected_candidates": ["candidate_a", "candidate_c"],
        "candidate_screening_executed": False,
        "files": {str(p.relative_to(OUT)): sha256(p) for p in files},
    }
    (OUT / "hashes/manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    marker = {str(p.relative_to(OUT)): sha256(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != ".finalized"}
    MARKER.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n")
    print(f"finalized {len(marker)} files")


if __name__ == "__main__":
    main()
