"""Phase 4.8, Priority 3D -- ONE frozen feature-improvement attempt
(rss_growth_rate added to the original 4 features), evaluated on the SAME
3 replicate seed blocks as the baseline run
(scripts/run_phase4_8_prediction_evaluation.py), using the SAME
evaluate_family harness (prediction_eval_v2.py) -- only the corpus
generator differs (5-feature extraction instead of 4). Run once; the
comparison below IS the frozen result, not iterated further.

Usage:
    python scripts/run_phase4_8b_feature_improvement_check.py <output_dir>
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.phase4.prediction_eval_v2 import ALL_EVALUATED_MODES, evaluate_family
from src.phase4.prediction_features_v2 import generate_corpus_v2
from src.phase4.prediction_training import SplitSeeds

TIMEOUT_SECONDS = 0.15
TRAIN_N, VAL_N, TEST_N = 500, 150, 150
REPLICATE_SEED_OFFSETS = [0, 100_000, 200_000]  # identical to the baseline run


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
        print(f"[replicate {i+1}/3] generating 5-feature corpus...")
        corpus = generate_corpus_v2(seeds, timeout_seconds=TIMEOUT_SECONDS)
        families = {}
        for mode, failure_class in ALL_EVALUATED_MODES.items():
            fe = evaluate_family(mode, failure_class, corpus)
            families[mode] = {
                "status": fe.status,
                "metrics": fe.metrics,
            }
            if fe.status == "EVALUATED":
                print(f"  {mode:22s} auroc={fe.metrics['auroc']}")
            else:
                print(f"  {mode:22s} {fe.status}")
        replicate_reports.append({"seed_offset": offset, "families": families})

    aggregated = {}
    for mode in ALL_EVALUATED_MODES:
        aurocs = [r["families"][mode]["metrics"]["auroc"] for r in replicate_reports
                  if r["families"][mode]["status"] == "EVALUATED" and r["families"][mode]["metrics"]["auroc"] is not None]
        aggregated[mode] = {
            "n_replicates_evaluated": len(aurocs),
            "auroc_mean": statistics.mean(aurocs) if aurocs else None,
            "auroc_stdev": statistics.stdev(aurocs) if len(aurocs) > 1 else None,
            "auroc_values": aurocs,
        }

    out = {
        "feature_set": "5-feature (original 4 + rss_growth_rate)",
        "protocol": {"train_n": TRAIN_N, "validation_n": VAL_N, "test_n": TEST_N, "replicate_seed_offsets": REPLICATE_SEED_OFFSETS},
        "aggregated_by_family": aggregated,
        "replicates": replicate_reports,
    }
    (output_dir / "evaluation" / "prediction_feature_improvement_check.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(aggregated, indent=2, default=str))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
