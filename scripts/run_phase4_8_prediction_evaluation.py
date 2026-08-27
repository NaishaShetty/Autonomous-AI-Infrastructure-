"""Phase 4.8 -- Priority 3: valid, leak-free, per-failure-class prediction
evaluation with negative controls, replicated across multiple DISJOINT
seed-range blocks (frozen before this script is ever run) so the reported
numbers are a distribution, not one arbitrarily-chosen split's point
estimate.

Why replicated: an early single-split run (train=0-1200, val=20000-20300,
test=40000-40300) produced AUROC ~0.51 for the `cpu` (timeout) family --
much lower than the ~0.636 previously reported in
PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md for the same family.
Sanity-checking with the EXISTING, unmodified
``prediction_training.train_and_persist_scope_router`` on the exact same
seed range reproduced the same ~0.51 figure -- confirming this is real
seed-range sensitivity in the underlying data/model, not a bug in the new
evaluation code. Reporting a single point estimate would hide that
sensitivity; reporting a distribution across several disjoint seed blocks
does not.

Usage:
    python scripts/run_phase4_8_prediction_evaluation.py <output_dir>
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.phase4.prediction_eval_v2 import ALL_EVALUATED_MODES, evaluate_all_families
from src.phase4.prediction_training import SplitSeeds

TIMEOUT_SECONDS = 0.15
TRAIN_N, VAL_N, TEST_N = 500, 150, 150
N_REPLICATES = 3
# Frozen, disjoint seed blocks per replicate. Each replicate's own
# train/validation/test blocks are themselves disjoint (SplitSeeds), and
# no seed is reused across replicates either -- every one of the
# 3 * (500+150+150) = 2400 seeds below is used exactly once.
REPLICATE_SEED_OFFSETS = [0, 100_000, 200_000]


def _seeds_for_replicate(offset: int) -> SplitSeeds:
    return SplitSeeds(
        train=range(offset, offset + TRAIN_N),
        validation=range(offset + 500_000, offset + 500_000 + VAL_N),
        test=range(offset + 900_000, offset + 900_000 + TEST_N),
    )


def main(output_dir: Path) -> None:
    assert output_dir.exists(), f"output_dir must already exist: {output_dir}"
    replicate_reports = []
    for i, offset in enumerate(REPLICATE_SEED_OFFSETS):
        seeds = _seeds_for_replicate(offset)
        print(f"[replicate {i+1}/{N_REPLICATES}] train={seeds.train} val={seeds.validation} test={seeds.test}")
        report = evaluate_all_families(seeds, timeout_seconds=TIMEOUT_SECONDS)
        report["split_seeds"] = {
            "train": [seeds.train.start, seeds.train.stop],
            "validation": [seeds.validation.start, seeds.validation.stop],
            "test": [seeds.test.start, seeds.test.stop],
        }
        replicate_reports.append(report)
        for mode, fam in report["families"].items():
            if fam["status"] == "EVALUATED":
                m, sc = fam["metrics"], fam["shuffled_control_metrics"]
                print(f"  {mode:22s} auroc={m['auroc']} shuffled_auroc={sc['auroc'] if sc else None}")
            else:
                print(f"  {mode:22s} {fam['status']}")

    aggregated = {}
    for mode in ALL_EVALUATED_MODES:
        statuses = [r["families"][mode]["status"] for r in replicate_reports]
        if all(s == "NOT_PREDICTABLE_SINGLE_CLASS" for s in statuses):
            aggregated[mode] = {"status": "NOT_PREDICTABLE_SINGLE_CLASS", "n_replicates": len(statuses)}
            continue
        real_aurocs = [r["families"][mode]["metrics"]["auroc"] for r in replicate_reports
                       if r["families"][mode]["status"] == "EVALUATED" and r["families"][mode]["metrics"]["auroc"] is not None]
        shuffled_aurocs = [r["families"][mode]["shuffled_control_metrics"]["auroc"] for r in replicate_reports
                            if r["families"][mode]["status"] == "EVALUATED" and r["families"][mode]["shuffled_control_metrics"]
                            and r["families"][mode]["shuffled_control_metrics"]["auroc"] is not None]
        aggregated[mode] = {
            "status": "EVALUATED",
            "n_replicates_evaluated": len(real_aurocs),
            "real_auroc_mean": statistics.mean(real_aurocs) if real_aurocs else None,
            "real_auroc_stdev": statistics.stdev(real_aurocs) if len(real_aurocs) > 1 else None,
            "real_auroc_values": real_aurocs,
            "shuffled_auroc_mean": statistics.mean(shuffled_aurocs) if shuffled_aurocs else None,
            "shuffled_auroc_values": shuffled_aurocs,
            "real_minus_shuffled_mean": (statistics.mean(real_aurocs) - statistics.mean(shuffled_aurocs)) if real_aurocs and shuffled_aurocs else None,
        }

    out = {
        "protocol": {
            "n_replicates": N_REPLICATES, "train_n": TRAIN_N, "validation_n": VAL_N, "test_n": TEST_N,
            "replicate_seed_offsets": REPLICATE_SEED_OFFSETS, "timeout_seconds": TIMEOUT_SECONDS,
        },
        "aggregated_by_family": aggregated,
        "replicates": replicate_reports,
    }
    (output_dir / "evaluation" / "prediction_metrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(aggregated, indent=2, default=str))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
