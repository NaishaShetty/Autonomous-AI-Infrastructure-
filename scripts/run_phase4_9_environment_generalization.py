"""Phase 4.9 -- Priority 4: does the Phase 4.8 prediction methodology's
(mostly-negative) finding, and any real per-family signal it does have,
transfer to genuinely different controlled environments? Fit/calibrate
ONLY on the development environment (baseline_cpu); evaluate the SAME
frozen models zero-shot on the held-out (memory_constrained) and
robustness (dependency_network_constrained) environments, for every
bimodal family. No held-out/robustness data ever influences training,
threshold selection, or feature choice.

Usage:
    python scripts/run_phase4_9_environment_generalization.py <output_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.phase4.environments import ALL_ENVIRONMENTS, BASELINE_CPU, DEPENDENCY_NETWORK_CONSTRAINED, MEMORY_CONSTRAINED, generate_corpus_rows_for_environment
from src.phase4.prediction_eval_v2 import BIMODAL_FAMILY_MODES, compute_metrics
from src.phase4.prediction_training import _xy, calibrate_threshold

DEV_TRAIN_N, DEV_VAL_N = 500, 150
EVAL_TEST_N = 150
DEV_TRAIN_SEEDS = range(0, DEV_TRAIN_N)
DEV_VAL_SEEDS = range(500_000, 500_000 + DEV_VAL_N)
# Disjoint from the dev seeds and from each other -- each environment's
# test population is generated under that environment's OWN scenario
# generator/RuntimeConfig, so a seed number alone does not determine the
# workload; the environment does.
TEST_SEEDS = range(900_000, 900_000 + EVAL_TEST_N)


def main(output_dir: Path) -> None:
    assert output_dir.exists(), f"output_dir must already exist: {output_dir}"

    print("generating DEVELOPMENT environment train+validation corpus (baseline_cpu)...")
    dev_train = generate_corpus_rows_for_environment(BASELINE_CPU, DEV_TRAIN_SEEDS, "train")
    dev_val = generate_corpus_rows_for_environment(BASELINE_CPU, DEV_VAL_SEEDS, "validation")

    print("generating TEST corpora for all three environments (baseline/held-out/robustness)...")
    test_by_env = {
        env.environment_id: generate_corpus_rows_for_environment(env, TEST_SEEDS, "test")
        for env in ALL_ENVIRONMENTS
    }

    results = {}
    for mode, failure_class in BIMODAL_FAMILY_MODES.items():
        train_rows = [r for r in dev_train if r.mode == mode]
        val_rows = [r for r in dev_val if r.mode == mode]
        if len(set(r.label for r in train_rows)) < 2:
            results[mode] = {"status": "NOT_PREDICTABLE_ON_DEV_SPLIT"}
            continue

        model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
        x_train, y_train = _xy(train_rows)
        model.fit(x_train, y_train)
        threshold = calibrate_threshold(model, val_rows)

        per_env = {}
        for env in ALL_ENVIRONMENTS:
            env_rows = [r for r in test_by_env[env.environment_id] if r.mode == mode]
            if len(set(r.label for r in env_rows)) < 2:
                per_env[env.environment_id] = {"status": "NOT_PREDICTABLE_SINGLE_CLASS_IN_THIS_ENVIRONMENT", "n_rows": len(env_rows)}
                continue
            per_env[env.environment_id] = {"status": "EVALUATED", "role": env.role, "metrics": compute_metrics(model, threshold, env_rows)}

        dev_auroc = per_env[BASELINE_CPU.environment_id].get("metrics", {}).get("auroc")
        degradation = {}
        for env in ALL_ENVIRONMENTS:
            if env.role == "development":
                continue
            other_auroc = per_env[env.environment_id].get("metrics", {}).get("auroc")
            degradation[env.environment_id] = (
                (dev_auroc - other_auroc) if (dev_auroc is not None and other_auroc is not None) else None
            )

        results[mode] = {
            "status": "EVALUATED", "failure_class": failure_class, "threshold": threshold,
            "n_dev_train_rows": len(train_rows), "n_dev_validation_rows": len(val_rows),
            "per_environment": per_env, "auroc_degradation_from_dev": degradation,
        }

    out = {
        "environments": {env.environment_id: env.as_dict() for env in ALL_ENVIRONMENTS},
        "dev_seed_ranges": {"train": [DEV_TRAIN_SEEDS.start, DEV_TRAIN_SEEDS.stop], "validation": [DEV_VAL_SEEDS.start, DEV_VAL_SEEDS.stop]},
        "test_seed_range": [TEST_SEEDS.start, TEST_SEEDS.stop],
        "results_by_family": results,
    }
    (output_dir / "evaluation" / "generalization_metrics.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(results, indent=2, default=str))
    print("done.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
