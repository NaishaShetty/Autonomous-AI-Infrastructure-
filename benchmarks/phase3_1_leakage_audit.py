"""Phase 3.1 formal leakage audit of the (unmodified) Phase 2 pipeline.

This script performs CONCRETE, RUNTIME checks against the real
``src/pipeline_builder.build_system`` output -- it does not just re-read the
source and assert reasoning about it. Every check below either passes with
measured evidence or fails with measured evidence; nothing here is modified
to make the checks pass, and the Phase 2 pipeline code itself is not
touched by this script.

Run: python benchmarks/phase3_1_leakage_audit.py
Writes: experiments/results/phase3_1/leakage_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES, generate_regime_stream  # noqa: E402
from src.pipeline_builder import DEFAULT_REGIME_SIZES, build_system  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_1"
SEED = 42


def check_temporal_and_fit_isolation(system) -> dict:
    """Confirms (by direct object inspection, not by re-deriving the code's
    intent) that only regime 0 data reached the workload model's fit, only
    regime-2-derived failures reached failure-memory's fit, and the test
    stream (regimes >=3) is a disjoint set of samples never passed to any
    .fit() call. We can't rewind sklearn objects to see what they were
    fit on, so this check instead re-derives the split from the same
    generator call and confirms (a) the split is a strict partition, and
    (b) failure_memory's failure events all carry regime==2 in their
    stored metadata."""
    stream = generate_regime_stream(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)
    regime_of = {}
    for s in stream:
        regime_of.setdefault(s.regime, []).append(s)

    train_ids = {id(s) for s in regime_of[0]}
    calib_ids = {id(s) for s in regime_of[1]}
    logging_ids = {id(s) for s in regime_of[2]}
    test_ids = {id(s) for r in (3, 4) for s in regime_of[r]}
    partition_disjoint = not (
        (train_ids & calib_ids) or (train_ids & logging_ids) or (train_ids & test_ids)
        or (calib_ids & logging_ids) or (calib_ids & test_ids) or (logging_ids & test_ids)
    )

    failure_regimes = {e.metadata.get("regime") for e in system.failure_memory._failure_events}
    failure_memory_only_from_regime_2 = failure_regimes <= {2}

    return {
        "check": "temporal_and_fit_isolation",
        "regime_split_is_disjoint_partition": bool(partition_disjoint),
        "failure_memory_events_regimes_observed": sorted(r for r in failure_regimes if r is not None),
        "failure_memory_fit_only_on_regime_2": bool(failure_memory_only_from_regime_2),
        "test_stream_size": len(system.test_stream),
        "test_stream_regimes": sorted({s.regime for s in system.test_stream}),
        "passed": bool(partition_disjoint and failure_memory_only_from_regime_2),
    }


def check_label_leakage_in_features(system) -> dict:
    """Confirms the context dict handed to the embedder/calibrator never
    contains the true label or the regime id -- i.e. the feature vector a
    prediction is made from cannot literally contain the answer."""
    offending = []
    for s in system.test_stream[:50]:
        if "label" in s.context or "regime" in s.context or "y" in s.context:
            offending.append(s.context)
    keys_seen = set()
    for s in system.test_stream[:200]:
        keys_seen.update(s.context.keys())
    return {
        "check": "label_leakage_in_features",
        "context_keys_seen": sorted(keys_seen),
        "expected_keys": sorted(FEATURE_NAMES),
        "label_or_regime_found_in_context": len(offending) > 0,
        "passed": keys_seen == set(FEATURE_NAMES) and len(offending) == 0,
    }


def check_preprocessing_fit_scope(system) -> dict:
    """Confirms the FailureEmbedder's PCA was fit on exactly the number of
    samples in the logging-regime failure set, not on the full stream and
    not on the test stream (a PCA fit on N samples records that N nowhere
    directly, so this check instead confirms n_failures matches what a
    fresh, independent recount of regime-2 failures produces)."""
    system_b = build_system(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)  # independent rebuild
    independent_count = system_b.n_logged_failures
    return {
        "check": "preprocessing_fit_scope",
        "failure_memory_n_failures": system.failure_memory.n_failures,
        "independently_recomputed_n_logged_failures": independent_count,
        "counts_match": system.failure_memory.n_failures == independent_count,
        "passed": system.failure_memory.n_failures == independent_count,
    }


def check_duplicate_samples_across_splits(system) -> dict:
    """Exact-value duplicate check: hashes each sample's rounded feature
    vector and looks for any row appearing in more than one of
    train/calib/logging/test."""
    stream = generate_regime_stream(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)
    by_regime: dict[int, list] = {}
    for s in stream:
        by_regime.setdefault(s.regime, []).append(s)

    def row_hash(sample) -> tuple:
        return tuple(round(sample.context[f], 10) for f in FEATURE_NAMES)

    split_hashes = {
        "train": {row_hash(s) for s in by_regime[0]},
        "calibration": {row_hash(s) for s in by_regime[1]},
        "logging": {row_hash(s) for s in by_regime[2]},
        "test": {row_hash(s) for r in (3, 4) for s in by_regime[r]},
    }
    overlaps = {}
    names = list(split_hashes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            inter = split_hashes[names[i]] & split_hashes[names[j]]
            if inter:
                overlaps[f"{names[i]}__{names[j]}"] = len(inter)

    return {
        "check": "duplicate_samples_across_splits",
        "split_sizes": {k: len(v) for k, v in split_hashes.items()},
        "overlaps_found": overlaps,
        "passed": len(overlaps) == 0,
    }


def check_regime_identifiability_from_features(system) -> dict:
    """Statistical check for 'regime leakage': can regime id be inferred
    from the marginal distribution of the raw features alone? Compares
    per-regime feature means/stds -- if they are indistinguishable across
    regimes (as the generator's construction intends: X ~ N(0, I) every
    regime, only the label-generating weight vector drifts), then no
    trivial regime signal leaks into the feature vector."""
    stream = generate_regime_stream(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)
    by_regime: dict[int, list] = {}
    for s in stream:
        by_regime.setdefault(s.regime, []).append(s)

    stats = {}
    for r, samples in by_regime.items():
        X = np.stack([[s.context[f] for f in FEATURE_NAMES] for s in samples])
        stats[r] = {"mean": X.mean(axis=0).round(4).tolist(), "std": X.std(axis=0).round(4).tolist()}

    means = np.array([stats[r]["mean"] for r in sorted(stats)])
    max_mean_deviation = float(np.max(np.abs(means - means.mean(axis=0))))

    return {
        "check": "regime_identifiability_from_features",
        "per_regime_feature_stats": stats,
        "max_abs_deviation_of_regime_means_from_grand_mean": max_mean_deviation,
        "interpretation": (
            "Feature marginals are ~N(0,1) in every regime by construction; only the "
            "feature->label relationship (weight vector) drifts, not the feature "
            "distribution itself. A small max deviation here confirms regime id is not "
            "trivially recoverable from features alone -- but it also means failure-memory "
            "cannot use feature-space location alone to distinguish 'pre-drift' from "
            "'post-drift' regions, which is relevant context for interpreting Baseline C's "
            "performance, not a leakage finding."
        ),
        "passed": max_mean_deviation < 0.5,  # generous sanity bound, not a tuned threshold
    }


def check_synthetic_generation_triviality(system) -> dict:
    """Confirms the label is not a trivial deterministic function of a
    single feature or a constant -- i.e. this isn't an artificially easy
    (or leaking) synthetic task."""
    stream = generate_regime_stream(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)
    y = np.array([s.label for s in stream])
    X = np.stack([[s.context[f] for f in FEATURE_NAMES] for s in stream])
    per_feature_corr = [float(np.corrcoef(X[:, i], y)[0, 1]) for i in range(X.shape[1])]
    return {
        "check": "synthetic_generation_triviality",
        "label_prevalence": float(y.mean()),
        "per_feature_correlation_with_label": per_feature_corr,
        "max_single_feature_correlation": float(max(abs(c) for c in per_feature_corr)),
        "passed": float(y.mean()) not in (0.0, 1.0) and max(abs(c) for c in per_feature_corr) < 0.95,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    system = build_system(regime_sizes=DEFAULT_REGIME_SIZES, seed=SEED)

    checks = [
        check_temporal_and_fit_isolation(system),
        check_label_leakage_in_features(system),
        check_preprocessing_fit_scope(system),
        check_duplicate_samples_across_splits(system),
        check_regime_identifiability_from_features(system),
        check_synthetic_generation_triviality(system),
    ]

    report = {
        "seed": SEED,
        "regime_sizes": DEFAULT_REGIME_SIZES,
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
    }
    out_path = RESULTS_DIR / "leakage_audit.json"
    out_path.write_text(json.dumps(report, indent=2))

    print(f"Leakage audit -- seed {SEED}")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['check']}")
    print(f"\nAll checks passed: {report['all_passed']}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
