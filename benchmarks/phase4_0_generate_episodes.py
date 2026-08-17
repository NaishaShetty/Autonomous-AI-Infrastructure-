"""Phase 4.0: generate the episodic incident stream and write it to disk.

Reuses src.data.episodic.generate_episode_stream (which itself reuses
Phase 3's frozen build_system/attacks/decision_policy/diagnosis/recovery
machinery read-only -- see that module's docstring and
configs/phase4_0_episodic_protocol.json). Does not modify any Phase 3
frozen file.

Run: python benchmarks/phase4_0_generate_episodes.py
Writes:
  experiments/results/phase4_0/episodes.json       (full per-step records)
  experiments/results/phase4_0/manifest.json        (provenance + summary counts)
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import scipy  # noqa: E402
import sklearn  # noqa: E402

from src.data.episodic import generate_episode_stream, load_protocol  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_0"


def _content_hash(records: list) -> str:
    payload = json.dumps(records, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    dataset = generate_episode_stream(protocol)
    records = dataset.to_records()

    by_split = {"train": 0, "validation": 0, "test": 0}
    by_combo_split = {}
    for r in records:
        by_split[r["split"]] += 1
        key = f'{r["workload_id"]}|{r["condition_id"]}'
        by_combo_split.setdefault(key, {"train": 0, "validation": 0, "test": 0})
        by_combo_split[key][r["split"]] += 1

    n_critical = sum(1 for r in records if r["tier"] == "CRITICAL")
    n_recovered = sum(1 for r in records if r["recovery_outcome"] == "RECOVERED")

    manifest = {
        "protocol_path": "configs/phase4_0_episodic_protocol.json",
        "n_steps": len(records),
        "n_workloads": len(dataset.workload_ids),
        "n_known_combos": len(dataset.known_combos),
        "n_novel_combos": len(dataset.novel_combos),
        "split_counts": by_split,
        "split_counts_by_combo": by_combo_split,
        "n_critical_tier": n_critical,
        "n_recovery_attempts": n_critical,
        "n_recovered": n_recovered,
        "content_hash_sha256": _content_hash(records),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    (RESULTS_DIR / "episodes.json").write_text(json.dumps(records, indent=2))
    (RESULTS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Generated {len(records)} episode steps across {len(dataset.workload_ids)} workloads")
    print(f"  known combos: {len(dataset.known_combos)}, novel combos: {len(dataset.novel_combos)}")
    print(f"  split counts: {by_split}")
    print(f"  CRITICAL-tier: {n_critical}, recovered: {n_recovered}")
    print(f"  content hash: {manifest['content_hash_sha256']}")
    print(f"Wrote {RESULTS_DIR / 'episodes.json'} and {RESULTS_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
