"""Phase 3.4: consolidated comparison of every already-established
failure-risk candidate under the SAME frozen Phase 3.1 protocol.

This is NOT a model-development script. It fits, trains, or tunes nothing.
It loads the already-written, already-frozen result artifacts from Phase
3.1 (``experiments/results/phase3_1``), Phase 3.2
(``experiments/results/phase3_2``), and Phase 3.2C
(``experiments/results/phase3_2c``) -- all of which were produced by
running the SAME six predetermined seeds through the SAME
``src.pipeline_builder.build_system`` call under the SAME
``configs/phase3_1_protocol.json`` -- verifies they actually agree with the
frozen protocol and with each other where they should be identical
(same-seed test-set size/prevalence, Candidate C vs Experiment C), and
recombines them into one consolidated table with per-seed paired
comparisons, aggregate cross-seed statistics, and bootstrap within-seed
statistics for the primary seed.

Does NOT modify ``configs/phase3_1_protocol.json``,
``src/evaluation/{metrics,bootstrap,protocol}.py``,
``benchmarks/phase3_1_evaluate.py``, ``benchmarks/phase3_2_evaluate.py``,
``benchmarks/phase3_2c_ablation.py``, ``benchmarks/phase3_3_generalization
.py``, ``src/pipeline_builder.py``, ``src/failure_memory/``, or
``src/evaluation/representations.py``. See docs/PHASE3_4_COMPARISON.md.

Run: python benchmarks/phase3_4_compare.py
Writes:
  experiments/results/phase3_4/comparison.json
  docs/PHASE3_4_COMPARISON.md is written separately (not by this script) --
  the numbers below are meant to be read out of comparison.json when
  updating that document.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402  -- reused, not reimplemented
from src.evaluation.protocol import Phase31Protocol  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_4"

P31_DIR = ROOT / "experiments" / "results" / "phase3_1"
P32_DIR = ROOT / "experiments" / "results" / "phase3_2"
P32C_DIR = ROOT / "experiments" / "results" / "phase3_2c"

SCALAR_METRICS = ["auroc", "auprc", "aurc"]

# Every candidate compared in Phase 3.4, sourced from an already-frozen
# Phase 3.1/3.2/3.2C result file -- NOTHING here is rerun or refit.
# ``duplicate_of`` marks candidates whose implementation is byte-identical
# to another candidate already in this table (per the Phase 3.4 brief
# section 9: "do not pretend they are independent systems").
CANDIDATES = [
    {
        "id": "A_no_signal",
        "label": "No signal",
        "source_phase": "phase3_2",
        "source_key": "A_no_signal",
        "lineage": "Phase 3.1 baseline A, reproduced identically (same protocol/seeds) inside Phase 3.2. Constant score = empirical failure prevalence measured on regime 2 (train-side).",
        "duplicate_of": None,
    },
    {
        "id": "B_calibrated_confidence",
        "label": "Calibrated confidence",
        "source_phase": "phase3_2",
        "source_key": "B_calibrated_confidence",
        "lineage": "Phase 3.1 baseline B: 1 - ConfidenceCalibrator.predict(...).calibrated_confidence. The strongest established predictive reference prior to Phase 3.4.",
        "duplicate_of": None,
    },
    {
        "id": "C_failure_memory",
        "label": "Original Phase 2 Failure Memory",
        "source_phase": "phase3_2",
        "source_key": "control_phase2_failure_memory",
        "lineage": "Phase 3.1 baseline C / Phase 3.2 control. Unmodified Phase 2 KMeans + Gaussian-kernel similarity score. Official Failure Memory control baseline.",
        "duplicate_of": None,
    },
    {
        "id": "D_raw_features",
        "label": "Candidate B -- raw structured features",
        "source_phase": "phase3_2",
        "source_key": "candidate_raw_features",
        "lineage": "Phase 3.2 Candidate B: KMeans clustering directly on raw structured features (RawFeatureFailureRisk).",
        "duplicate_of": None,
    },
    {
        "id": "E_failure_history_supervised",
        "label": "Candidate C -- failure-history representation + supervised classifier",
        "source_phase": "phase3_2",
        "source_key": "candidate_failure_history",
        "lineage": "Phase 3.2 Candidate C (FailureHistoryRiskModel: rich k-NN failure-history features + logistic regression).",
        "duplicate_of": "E_failure_history_supervised_control",
    },
    {
        "id": "E_failure_history_supervised_control",
        "label": "Phase 3.2C Experiment C (positive control, reproduces Candidate C)",
        "source_phase": "phase3_2c",
        "source_key": "experiment_C_control",
        "lineage": "Phase 3.2C Experiment C: documented as an EXACT, unmodified reproduction of Phase 3.2 Candidate C, included in that ablation study as its own positive control.",
        "duplicate_of": "E_failure_history_supervised",
    },
    {
        "id": "F_supervised_failure_risk",
        "label": "Supervised Failure Risk (Phase 3.2C Experiment B -- selected candidate)",
        "source_phase": "phase3_2c",
        "source_key": "experiment_B_old_repr_supervised",
        "lineage": "Phase 3.2C Experiment B: old Phase 2 PCA representation + supervised logistic regression (Phase2RepresentationSupervisedRisk). Isolated the mechanism (classifier, not representation) and was selected as the Phase 3.3 generalization candidate.",
        "duplicate_of": None,
    },
]

# Candidates actually distinct from a scientific standpoint -- used for any
# "how many independent systems ..." style counting so duplicates are not
# double counted.
DISTINCT_CANDIDATE_IDS = [c["id"] for c in CANDIDATES if c["duplicate_of"] != "E_failure_history_supervised"]

# Comparators every candidate is checked against, per-seed, per the Phase
# 3.4 brief section 11.
COMPARATORS = ["A_no_signal", "C_failure_memory", "B_calibrated_confidence"]


class ProtocolDiscrepancyError(RuntimeError):
    """Raised when a stored result file's protocol_config does not match
    the currently-loaded frozen protocol. Per the Phase 3.4 brief section
    21: STOP and document, do not silently proceed or overwrite."""


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _assert_protocol_matches(stored_meta: dict, protocol: Phase31Protocol, source_name: str) -> None:
    stored = stored_meta["protocol_config"]
    current = protocol.raw
    if stored != current:
        raise ProtocolDiscrepancyError(
            f"{source_name}'s stored protocol_config does not match the currently-loaded "
            f"configs/phase3_1_protocol.json. Phase 3.4 must not silently reconcile this -- "
            f"investigate whether the protocol file was edited after {source_name} was produced."
        )


def load_sources(protocol: Phase31Protocol) -> dict:
    sources = {
        "phase3_1": {
            "per_seed": _load_json(P31_DIR / "per_seed_results.json"),
            "aggregate": _load_json(P31_DIR / "aggregate_results.json"),
            "bootstrap": _load_json(P31_DIR / "bootstrap_ci_primary_seed.json"),
        },
        "phase3_2": {
            "per_seed": _load_json(P32_DIR / "per_seed_results.json"),
            "aggregate": _load_json(P32_DIR / "aggregate_results.json"),
            "bootstrap": _load_json(P32_DIR / "bootstrap_ci_primary_seed.json"),
        },
        "phase3_2c": {
            "per_seed": _load_json(P32C_DIR / "per_seed_results.json"),
            "aggregate": _load_json(P32C_DIR / "aggregate_results.json"),
            "bootstrap": _load_json(P32C_DIR / "bootstrap_ci_primary_seed.json"),
        },
    }
    for name, bundle in sources.items():
        _assert_protocol_matches(bundle["per_seed"]["meta"], protocol, name)
        _assert_protocol_matches(bundle["aggregate"]["meta"], protocol, name)
    return sources


def _per_seed_metric_rows(sources: dict, candidate: dict) -> dict[int, dict]:
    """Returns {seed: results_dict} for one candidate, read directly out of
    the already-frozen per_seed_results.json for its source phase. No
    recomputation of scores -- these are the exact stored values."""
    bundle = sources[candidate["source_phase"]]["per_seed"]["per_seed"]
    out = {}
    for row in bundle:
        out[row["seed"]] = row["results"][candidate["source_key"]]
    return out


def _assert_test_sets_aligned(sources: dict, protocol: Phase31Protocol) -> None:
    """Every source's per-seed n_test_samples/test_failure_prevalence must
    match exactly for the same seed -- this is what makes per-seed values
    across phase3_1/phase3_2/phase3_2c directly, validly paired (same
    y_fail vector per seed, since same seed + same frozen protocol +
    deterministic build_system produce byte-identical regimes 3+4)."""
    rows = {
        name: {r["seed"]: (r["n_test_samples"], r["test_failure_prevalence"]) for r in sources[name]["per_seed"]["per_seed"]}
        for name in sources
    }
    for seed in protocol.seeds:
        values = {name: rows[name][seed] for name in rows}
        if len(set(values.values())) != 1:
            raise ProtocolDiscrepancyError(
                f"seed {seed}: test-set size/prevalence differs across source phases ({values}) -- "
                "per-seed comparisons across phases would not be validly paired."
            )


def _assert_duplicate_candidates_match(sources: dict) -> dict:
    """Confirms Candidate C (Phase 3.2) and Experiment C (Phase 3.2C) --
    documented as the exact same implementation -- actually produce
    identical per-seed AUROC. This is a consistency check on stored
    results, not a new computation."""
    c_rows = _per_seed_metric_rows(sources, next(c for c in CANDIDATES if c["id"] == "E_failure_history_supervised"))
    e_rows = _per_seed_metric_rows(sources, next(c for c in CANDIDATES if c["id"] == "E_failure_history_supervised_control"))
    mismatches = {
        seed: (c_rows[seed]["auroc"], e_rows[seed]["auroc"])
        for seed in c_rows
        if abs(c_rows[seed]["auroc"] - e_rows[seed]["auroc"]) > 1e-9
    }
    return {"identical": len(mismatches) == 0, "mismatches": mismatches}


def build_candidate_table(sources: dict, protocol: Phase31Protocol) -> dict:
    table = {}
    for candidate in CANDIDATES:
        per_seed = _per_seed_metric_rows(sources, candidate)
        ordered_seeds = protocol.seeds

        recomputed_aggregate = {}
        for m in SCALAR_METRICS:
            recomputed_aggregate[m] = _t_interval([per_seed[s][m] for s in ordered_seeds], 0.95)
        ece_values = [per_seed[s]["ece"] for s in ordered_seeds]
        if all(v is not None for v in ece_values):
            recomputed_aggregate["ece"] = _t_interval(ece_values, 0.95)
            ece_meaningful = True
        else:
            recomputed_aggregate["ece"] = None
            ece_meaningful = False

        recomputed_aggregate["precision_recall_at_coverage"] = []
        for i, cov in enumerate(protocol.coverage_operating_points):
            precisions = [per_seed[s]["precision_recall_at_coverage"][i]["precision"] for s in ordered_seeds]
            recalls = [per_seed[s]["precision_recall_at_coverage"][i]["recall"] for s in ordered_seeds]
            recomputed_aggregate["precision_recall_at_coverage"].append(
                {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
            )

        # Cross-check against the stored aggregate_results.json for this
        # candidate's source phase -- must match to float precision. A
        # mismatch means Phase 3.4's read of per-seed data disagrees with
        # what the original phase computed; that is a discrepancy to STOP
        # on, not paper over.
        stored_agg = sources[candidate["source_phase"]]["aggregate"]["aggregate"][candidate["source_key"]]
        for m in SCALAR_METRICS:
            stored_mean = stored_agg[m]["mean"]
            recomputed_mean = recomputed_aggregate[m]["mean"]
            if stored_mean is not None and recomputed_mean is not None and abs(stored_mean - recomputed_mean) > 1e-9:
                raise ProtocolDiscrepancyError(
                    f"{candidate['id']}.{m}: recomputed aggregate ({recomputed_mean}) disagrees with stored "
                    f"{candidate['source_phase']} aggregate_results.json ({stored_mean})."
                )

        bootstrap_source = sources[candidate["source_phase"]]["bootstrap"]["results"].get(candidate["source_key"])
        bootstrap = None
        if bootstrap_source is not None:
            bootstrap = {
                "auroc": bootstrap_source.get("auroc"),
                "auprc": bootstrap_source.get("auprc"),
                "note": "Within-primary-seed (seed=%d) bootstrap sampling uncertainty -- NOT cross-seed variability. Only auroc/auprc were bootstrapped by the source phase script." % protocol.primary_seed,
            }

        table[candidate["id"]] = {
            "label": candidate["label"],
            "lineage": candidate["lineage"],
            "duplicate_of": candidate["duplicate_of"],
            "source_phase": candidate["source_phase"],
            "source_key": candidate["source_key"],
            "ece_meaningful": ece_meaningful,
            "per_seed": {s: per_seed[s] for s in ordered_seeds},
            "aggregate_cross_seed": recomputed_aggregate,
            "bootstrap_within_seed_primary": bootstrap,
        }
    return table


def per_seed_paired_comparisons(table: dict, protocol: Phase31Protocol) -> dict:
    """Section 11 of the Phase 3.4 brief: for every candidate, versus each
    comparator, count how many of the 6 predetermined seeds it beats on
    AUROC, and report the mean paired AUROC difference with a Student-t CI
    over the 6 paired per-seed differences. This is a DESCRIPTIVE interval
    on the paired differences, not a hypothesis test -- with n=6 seeds, no
    inferential test (t-test, sign test, Wilcoxon) has meaningful power,
    and none is computed here."""
    out = {}
    for cand_id, cand in table.items():
        out[cand_id] = {}
        for comparator_id in COMPARATORS:
            if comparator_id == cand_id:
                continue
            comparator = table[comparator_id]
            diffs = []
            wins = 0
            per_seed_detail = []
            for seed in protocol.seeds:
                cand_auroc = cand["per_seed"][seed]["auroc"]
                comp_auroc = comparator["per_seed"][seed]["auroc"]
                if cand_auroc is None or comp_auroc is None:
                    continue
                diff = cand_auroc - comp_auroc
                diffs.append(diff)
                wins += int(diff > 0)
                per_seed_detail.append({"seed": seed, "candidate_auroc": cand_auroc, "comparator_auroc": comp_auroc, "diff": diff})
            out[cand_id][comparator_id] = {
                "wins": wins,
                "n_seeds": len(diffs),
                "beats_on_all_seeds": wins == len(diffs) and len(diffs) > 0,
                "mean_paired_auroc_diff": _t_interval(diffs, 0.95),
                "per_seed": per_seed_detail,
                "caveat": "n=6 paired differences -- interval estimate only, no significance test performed.",
            }
    return out


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()  # frozen, unmodified

    sources = load_sources(protocol)
    _assert_test_sets_aligned(sources, protocol)
    duplicate_check = _assert_duplicate_candidates_match(sources)

    table = build_candidate_table(sources, protocol)
    comparisons = per_seed_paired_comparisons(table, protocol)

    meta = {
        "protocol_config": protocol.raw,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "note": (
            "Phase 3.4 performs NO new fitting/training. Every candidate's per-seed scores were "
            "produced by Phase 3.1/3.2/3.2C, reused here unmodified. This script only re-aggregates, "
            "cross-checks, and pairs already-computed results."
        ),
        "candidate_C_experiment_C_duplicate_check": duplicate_check,
        "distinct_candidate_ids": DISTINCT_CANDIDATE_IDS,
        "comparators": COMPARATORS,
    }

    output = {"meta": meta, "candidates": table, "per_seed_paired_comparisons": comparisons}
    (RESULTS_DIR / "comparison.json").write_text(json.dumps(output, indent=2))

    # -- console summary --------------------------------------------------
    print(f"Phase 3.4 comparison -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    print(f"{'Candidate':<45} {'AUROC (mean, 95% CI)':<28} {'AURC (mean, lower better)':<28}")
    for cand_id, cand in table.items():
        a = cand["aggregate_cross_seed"]["auroc"]
        c = cand["aggregate_cross_seed"]["aurc"]
        a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
        c_s = f"{c['mean']:.4f}" if c["mean"] is not None else "n/a"
        dup = " (duplicate)" if cand["duplicate_of"] else ""
        print(f"{cand['label'][:44]:<45} {a_s:<28} {c_s:<28}{dup}")

    print(f"\nCandidate C / Experiment C identical per-seed AUROC: {duplicate_check['identical']}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
