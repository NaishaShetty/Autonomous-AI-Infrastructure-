"""Post-P5 remediation, Step 4 -- P4 environment generalization
re-evaluation. Implements exactly the protocol pre-registered in
``experiments/results/post_p5_remediation/<TIMESTAMP>/protocol/P4_STEP4_PROTOCOL.md``.

Model A: replication of the pre-existing Phase 4.9 zero-shot evaluation
(fixed-baseline-normalized RSS). Model B: same features plus
``rss_ratio_env_normalized`` (P4-W2). Both frozen on the development
environment (baseline_cpu) only, then evaluated zero-shot on all three
environments.

Usage:
    python scripts/run_p4_step4_environment_generalization.py <run_dir>
"""
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.environments import ALL_ENVIRONMENTS, BASELINE_CPU, EnvironmentProfile
from src.phase4.monitoring import MonitoringBaseline
from src.phase4.observability import PersistentEventStore
from src.phase4.prediction import extract_features, rolling_checkpoints
from src.phase4.prediction_eval_v2 import BIMODAL_FAMILY_MODES, compute_metrics
from src.phase4.prediction_features_env import extract_features_env_aware
from src.phase4.prediction_training import CorpusRow, _dt, _xy, calibrate_threshold

DEV_TRAIN_SEEDS = range(0, 500)
DEV_VAL_SEEDS = range(500_000, 500_150)
TEST_SEEDS = range(900_000, 900_150)


@dataclass(frozen=True)
class CorpusRowEnv(CorpusRow):
    features_a: tuple = ()
    features_b: tuple = ()


def generate_dual_corpus_for_environment(env: EnvironmentProfile, seeds, split: str) -> list[CorpusRowEnv]:
    """Generates ONE real corpus per environment (one real subprocess run
    per seed -- Model A and Model B are computed from the SAME real events,
    never from two separately-generated corpora, so any difference between
    them is purely the feature representation, never sampling noise)."""
    baseline = MonitoringBaseline()
    rows: list[CorpusRowEnv] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        config = RuntimeConfig(environment_id=env.environment_id, **env.runtime_config_kwargs)
        runtime = ControlledRuntime(store, config)
        for seed in seeds:
            workload_type, params = env.scenario_fn(seed)
            params = dict(params)
            occupy = params.pop("_occupy", None)
            if occupy:
                runtime.occupy_external_resource(int(params["port"]))
            workload_id = f"{env.environment_id}-{split}-seed-{seed}"
            mode = str(params.get("mode") or workload_type)
            result = runtime.run(workload_type, params, workload_id=workload_id)
            failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
            label = 1 if failure_events else 0
            failure_class = str(failure_events[0]["payload"].get("failure_kind")) if failure_events else None
            failure_ts = _dt(str(failure_events[0]["timestamp"])) if failure_events else None
            for idx, (checkpoint_time, prefix) in enumerate(rolling_checkpoints(result.events, result.collection_start)):
                if failure_ts is not None and _dt(checkpoint_time) >= failure_ts:
                    continue
                feats_a = extract_features(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                feats_b = extract_features_env_aware(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                ttf = (failure_ts - _dt(checkpoint_time)).total_seconds() if failure_ts is not None else None
                rows.append(CorpusRowEnv(
                    seed=seed, split=split, run_id=result.run_id, workload_id=workload_id,
                    failure_class=failure_class, label=label, checkpoint_index=idx,
                    checkpoint_time=checkpoint_time, time_to_failure_seconds=ttf,
                    features=feats_a.as_vector(), mode=mode,
                    features_a=feats_a.as_vector(), features_b=feats_b.as_vector(),
                ))
        store.close()
    return rows


def _rows_with_features(rows, which):
    return [CorpusRow(seed=r.seed, split=r.split, run_id=r.run_id, workload_id=r.workload_id, failure_class=r.failure_class, label=r.label, checkpoint_index=r.checkpoint_index, checkpoint_time=r.checkpoint_time, time_to_failure_seconds=r.time_to_failure_seconds, features=(r.features_a if which == "A" else r.features_b), mode=r.mode) for r in rows]


def _fit_and_eval(train_rows, val_rows, test_by_env, mode):
    train_sel = [r for r in train_rows if r.mode == mode]
    val_sel = [r for r in val_rows if r.mode == mode]
    if len(set(r.label for r in train_sel)) < 2:
        return {"status": "NOT_PREDICTABLE_ON_DEV_SPLIT"}
    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    x_train, y_train = _xy(train_sel)
    model.fit(x_train, y_train)
    threshold = calibrate_threshold(model, val_sel)
    per_env = {}
    for env_id, rows in test_by_env.items():
        env_rows = [r for r in rows if r.mode == mode]
        if len(set(r.label for r in env_rows)) < 2:
            per_env[env_id] = {"status": "NOT_PREDICTABLE_SINGLE_CLASS_IN_THIS_ENVIRONMENT", "n_rows": len(env_rows)}
            continue
        per_env[env_id] = {"status": "EVALUATED", "metrics": compute_metrics(model, threshold, env_rows)}
    dev_auroc = per_env.get(BASELINE_CPU.environment_id, {}).get("metrics", {}).get("auroc")
    degradation = {}
    for env in ALL_ENVIRONMENTS:
        if env.role == "development":
            continue
        other = per_env.get(env.environment_id, {}).get("metrics", {}).get("auroc")
        degradation[env.environment_id] = (dev_auroc - other) if (dev_auroc is not None and other is not None) else None
    return {"status": "EVALUATED", "threshold": threshold, "n_train_rows": len(train_sel), "per_environment": per_env, "auroc_degradation_from_dev": degradation}


def main(run_dir: Path) -> None:
    print("generating DEVELOPMENT train+validation corpus (baseline_cpu)...")
    dev_train = generate_dual_corpus_for_environment(BASELINE_CPU, DEV_TRAIN_SEEDS, "train")
    dev_val = generate_dual_corpus_for_environment(BASELINE_CPU, DEV_VAL_SEEDS, "validation")

    print("generating TEST corpora for all three environments...")
    test_by_env_raw = {env.environment_id: generate_dual_corpus_for_environment(env, TEST_SEEDS, "test") for env in ALL_ENVIRONMENTS}

    results = {"model_a": {}, "model_b": {}}
    for which, key in (("A", "model_a"), ("B", "model_b")):
        train_rows = _rows_with_features(dev_train, which)
        val_rows = _rows_with_features(dev_val, which)
        test_by_env = {env_id: _rows_with_features(rows, which) for env_id, rows in test_by_env_raw.items()}
        for mode in BIMODAL_FAMILY_MODES:
            print(f"fitting Model {which} for family={mode}...")
            results[key][mode] = _fit_and_eval(train_rows, val_rows, test_by_env, mode)

    out = {
        "environments": {env.environment_id: env.as_dict() for env in ALL_ENVIRONMENTS},
        "dev_seed_ranges": {"train": [DEV_TRAIN_SEEDS.start, DEV_TRAIN_SEEDS.stop], "validation": [DEV_VAL_SEEDS.start, DEV_VAL_SEEDS.stop]},
        "test_seed_range": [TEST_SEEDS.start, TEST_SEEDS.stop],
        "results": results,
    }
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw" / "p4_step4_results.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("wrote raw/p4_step4_results.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
