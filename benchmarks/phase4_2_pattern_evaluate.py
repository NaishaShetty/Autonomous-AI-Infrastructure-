"""Phase 4.2: failure pattern learning evaluation.

Discovers candidates from train, calibrates tiers using validation,
evaluates baselines A/B, proposed method C1, and ablation C2 on the
frozen test split (row-level), per
configs/phase4_2_pattern_protocol.json. Also runs the two secondary
descriptive analyses (temporal clustering, cause->outcome).

Run: python benchmarks/phase4_2_pattern_evaluate.py
Writes: experiments/results/phase4_2/pattern_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.patterns.discovery import (  # noqa: E402
    candidates_by_key,
    cause_outcome_report,
    discover_candidates,
    temporal_clustering_report,
)
from src.patterns.metrics import evaluate_rows, tier_level_true_structure_rate  # noqa: E402
from src.patterns.schema import EvidenceTier  # noqa: E402

PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"
PROTOCOL_PATH = ROOT / "configs" / "phase4_2_pattern_protocol.json"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_2"


def load_protocol() -> dict:
    data = json.loads(PROTOCOL_PATH.read_text())
    if not data.get("_frozen"):
        raise ValueError(f"{PROTOCOL_PATH} is not marked frozen")
    return data


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    records = json.loads((PHASE4_0_DIR / "episodes.json").read_text())
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    dataset_hash = manifest["content_hash_sha256"]
    protocol_version = "phase4_0_episodic_protocol.json"

    train_records = [r for r in records if r["split"] == "train"]
    validation_records = [r for r in records if r["split"] == "validation"]
    test_records = [r for r in records if r["split"] == "test"]
    test_critical_failures = [r for r in test_records if r["is_failure"] and r["diagnosed_cause"] is not None]

    thresholds = protocol["tier_thresholds"]
    candidates = discover_candidates(train_records, validation_records, thresholds, protocol_version, dataset_hash)
    by_key = candidates_by_key(candidates)

    methods = {
        "A_no_pattern_learning": lambda c: False,
        "B_naive_frequency_flagging": lambda c: c.n_train >= thresholds["MIN_OBSERVATIONS_FOR_TRUSTED_PURITY"],
        "C1_tiered_pattern_learning_proposed": lambda c: c.tier in (EvidenceTier.INFERRED, EvidenceTier.CONFIRMED),
        "C2_ablation_no_tiering": lambda c: (c.purity_train or 0.0) >= thresholds["TAU_INFERRED"],
    }

    method_results = {
        name: evaluate_rows(test_critical_failures, by_key, is_flagged)
        for name, is_flagged in methods.items()
    }

    tier_calibration = tier_level_true_structure_rate(test_critical_failures, by_key)

    temporal = temporal_clustering_report(records, protocol)
    cause_outcome = cause_outcome_report(train_records)

    n_covered = method_results["C1_tiered_pattern_learning_proposed"]["n_covered"]
    min_n = protocol["acceptance_criteria"]["minimum_evaluable_n"]

    output = {
        "protocol_version": protocol_version,
        "dataset_content_hash": dataset_hash,
        "n_candidates": len(candidates),
        "candidates": [
            {
                "workload_id": c.workload_id, "diagnosed_cause": c.diagnosed_cause,
                "n_train": c.n_train, "mode_condition_train": c.mode_condition_train,
                "purity_train": c.purity_train, "n_validation": c.n_validation,
                "purity_validation": c.purity_validation, "tier": c.tier.value,
            }
            for c in candidates
        ],
        "method_results": method_results,
        "tier_calibration": tier_calibration,
        "temporal_clustering": temporal,
        "cause_outcome": cause_outcome,
        "n_covered_test_rows": n_covered,
        "minimum_evaluable_n": min_n,
        "evidence_sufficient": n_covered >= min_n,
    }
    (RESULTS_DIR / "pattern_results.json").write_text(json.dumps(output, indent=2))

    print("Phase 4.2 pattern learning evaluation\n")
    print(f"Candidates discovered: {len(candidates)}")
    for c in candidates:
        print(f"  {c.workload_id:<12} {c.diagnosed_cause:<15} n_train={c.n_train} purity_train={c.purity_train:.2f} tier={c.tier.value}")
    print(f"\nn_covered_test_rows={n_covered} (minimum_evaluable_n={min_n}, evidence_sufficient={n_covered >= min_n})\n")
    for name, res in method_results.items():
        print(f"  {name:<36} precision={res['precision']} recall={res['recall']} n_flagged={res['n_flagged']}")
    print(f"\nTier calibration (true-structure rate by tier): {json.dumps(tier_calibration, indent=2)}")
    print(f"\nWrote {RESULTS_DIR / 'pattern_results.json'}")


if __name__ == "__main__":
    main()
