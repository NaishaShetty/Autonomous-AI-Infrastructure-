"""Phase 4.1: failure-experience retrieval evaluation.

Builds an ExperienceStore from Phase 4.0's train-split failures only,
evaluates 3 retrieval methods (A_no_memory_random, B_recency_only,
C_similarity_proposed) against 3 query groups (all_test, known_combo_test,
novel_combo_test) at k in {1,3,5}, per
configs/phase4_1_experience_protocol.json (frozen before this script was
run). Also runs the validation-only decay_lambda ablation.

Run: python benchmarks/phase4_1_retrieval_evaluate.py
Writes: experiments/results/phase4_1/retrieval_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data.synthetic import FEATURE_NAMES  # noqa: E402
from src.experience.metrics import count_relevant_in_store, precision_at_k, recall_at_k  # noqa: E402
from src.experience.schema import experience_from_episode_record  # noqa: E402
from src.experience.store import build_store_from_episode_records  # noqa: E402

PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"
PROTOCOL_PATH = ROOT / "configs" / "phase4_1_experience_protocol.json"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_1"


def load_protocol() -> dict:
    data = json.loads(PROTOCOL_PATH.read_text())
    if not data.get("_frozen"):
        raise ValueError(f"{PROTOCOL_PATH} is not marked frozen")
    return data


def _bootstrap_mean_ci(values: list[float], n_resamples: int, seed: int, confidence_level: float) -> dict:
    """Percentile bootstrap over a 1-D array of per-query metric values.
    New, small utility -- see configs/phase4_1_experience_protocol.json's
    bootstrap.method note on why this does not reuse
    src.evaluation.bootstrap.bootstrap_ci (different signature/use case)."""
    arr = np.array(values, dtype=float)
    n = len(arr)
    point_estimate = float(arr.mean()) if n else None
    if n == 0:
        return {"point_estimate": None, "n": 0, "ci_low": None, "ci_high": None}
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        means.append(arr[idx].mean())
    alpha = 1.0 - confidence_level
    ci_low = float(np.percentile(means, 100 * (alpha / 2)))
    ci_high = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return {"point_estimate": point_estimate, "n": n, "ci_low": ci_low, "ci_high": ci_high}


def _query_groups(records: list[dict], protocol: dict) -> dict:
    test_failures = [r for r in records if r["split"] == "test" and r["is_failure"]]
    return {
        "all_test": test_failures,
        "known_combo_test": [r for r in test_failures if not r["is_novel_combo"]],
        "novel_combo_test": [r for r in test_failures if r["is_novel_combo"]],
    }


def _retrieve(store, method: str, query, k: int, seed: int):
    if method == "A_no_memory_random":
        return store.retrieve_random(query, k, seed=seed)
    if method == "B_recency_only":
        return store.retrieve_recency(query, k)
    if method == "C_similarity_proposed":
        return store.retrieve_similarity(query, k, decay_lambda=0.0)
    raise ValueError(method)


def evaluate_group(store, group_records: list[dict], protocol: dict, protocol_version: str, dataset_hash: str) -> dict:
    methods = list(protocol["retrieval_methods"].keys())
    k_values = protocol["k_values"]
    seed = protocol["random_baseline_seed"]
    store_experiences = store.experiences

    out = {m: {str(k): {"precision": [], "recall": []} for k in k_values} for m in methods}

    for r in group_records:
        exp = experience_from_episode_record(r, protocol_version, dataset_hash)
        query = exp.decision_time_query()
        condition_id = exp.provenance.condition_id  # evaluation-only, used here directly, never via query
        total_relevant = count_relevant_in_store(store_experiences, condition_id)

        for method in methods:
            for k in k_values:
                retrieved = _retrieve(store, method, query, k, seed)
                p = precision_at_k(retrieved, condition_id, k)
                rc = recall_at_k(retrieved, condition_id, k, total_relevant)
                if p is not None:
                    out[method][str(k)]["precision"].append(p)
                if rc is not None:
                    out[method][str(k)]["recall"].append(rc)

    bootstrap_cfg = protocol["bootstrap"]
    summary = {}
    for method in methods:
        summary[method] = {}
        for k in k_values:
            prec = out[method][str(k)]["precision"]
            rec = out[method][str(k)]["recall"]
            summary[method][str(k)] = {
                "precision_at_k": _bootstrap_mean_ci(prec, bootstrap_cfg["n_resamples"], bootstrap_cfg["seed"], bootstrap_cfg["confidence_level"]),
                "recall_at_k": _bootstrap_mean_ci(rec, bootstrap_cfg["n_resamples"], bootstrap_cfg["seed"], bootstrap_cfg["confidence_level"]),
            }
    return summary


def evaluate_decay_ablation(store, validation_records: list[dict], protocol: dict, protocol_version: str, dataset_hash: str) -> dict:
    """Validation-split-only, per protocol's decay_ablation block."""
    val_failures = [r for r in validation_records if r["is_failure"]]
    k_values = protocol["k_values"]
    out = {}
    for lam in protocol["decay_ablation"]["decay_lambda_values"]:
        precisions_by_k = {str(k): [] for k in k_values}
        for r in val_failures:
            exp = experience_from_episode_record(r, protocol_version, dataset_hash)
            query = exp.decision_time_query()
            condition_id = exp.provenance.condition_id
            for k in k_values:
                retrieved = store.retrieve_similarity(query, k, decay_lambda=lam)
                p = precision_at_k(retrieved, condition_id, k)
                if p is not None:
                    precisions_by_k[str(k)].append(p)
        out[str(lam)] = {k: (float(np.mean(v)) if v else None) for k, v in precisions_by_k.items()}
    return out


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    records = json.loads((PHASE4_0_DIR / "episodes.json").read_text())
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    dataset_hash = manifest["content_hash_sha256"]
    protocol_version = "phase4_0_episodic_protocol.json"

    store = build_store_from_episode_records(
        records, FEATURE_NAMES, protocol_version, dataset_hash, split="train",
    )

    groups = _query_groups(records, protocol)
    group_results = {
        name: evaluate_group(store, group_records, protocol, protocol_version, dataset_hash)
        for name, group_records in groups.items()
    }

    validation_records = [r for r in records if r["split"] == "validation"]
    decay_ablation = evaluate_decay_ablation(store, validation_records, protocol, protocol_version, dataset_hash)

    output = {
        "store_size": len(store),
        "store_content_hash": store.content_hash(),
        "dataset_content_hash": dataset_hash,
        "protocol_version": protocol_version,
        "query_group_sizes": {name: len(recs) for name, recs in groups.items()},
        "results_by_group": group_results,
        "decay_ablation_validation_only": decay_ablation,
    }
    (RESULTS_DIR / "retrieval_results.json").write_text(json.dumps(output, indent=2))

    print("Phase 4.1 retrieval evaluation\n")
    print(f"Store size (train-split failures): {len(store)}")
    for name, recs in groups.items():
        print(f"Query group '{name}': n={len(recs)}")
    print()
    for group_name, methods in group_results.items():
        print(f"=== group: {group_name} ===")
        for method, by_k in methods.items():
            for k, m in by_k.items():
                p = m["precision_at_k"]
                print(f"  {method:<22} k={k}  precision@k mean={p['point_estimate']} n={p['n']} CI=[{p['ci_low']}, {p['ci_high']}]")
    print(f"\nWrote {RESULTS_DIR / 'retrieval_results.json'}")


if __name__ == "__main__":
    main()
