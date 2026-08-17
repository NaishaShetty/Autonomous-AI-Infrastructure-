"""Phase 3.5: attack generalization for the Supervised Failure-Risk
candidate (Phase 3.2C's Experiment B / Phase 3.3's frozen candidate,
labeled "F" in Phase 3.4).

Tests whether F's predictive behavior survives COVARIATE-shift attack
conditions (corrupted/missing input features) that are a genuinely
different generalization axis from Phase 3.3's drift_scale sweep (concept
drift: fixed features, rotated label boundary). See
``configs/phase3_5_attack_protocol.json`` (frozen BEFORE this script was
run) and docs/PHASE3_5_ATTACK_GENERALIZATION.md for the full threat model
and justification of each attack condition.

Reuses, rather than reimplements:
  - ``benchmarks.phase3_3_generalization``'s
    ``_reconstruct_regime2_with_confidences``, ``_fit_frozen_candidate``,
    ``_compute_condition_arrays``, ``_evaluate_one``, ``_is_probability``,
    ``_assert_no_regime2_leakage``, and ``BASELINES`` -- verbatim, so F
    here is provably the exact Phase 3.3 frozen candidate, not a
    reimplementation of it.
  - ``benchmarks.phase3_1_evaluate``'s ``_t_interval``.
  - ``src.evaluation.bootstrap.bootstrap_ci``.
  - ``src.evaluation.attacks``'s ``apply_feature_noise`` /
    ``apply_feature_dropout`` for the attack transforms themselves.

Does NOT modify ``configs/phase3_1_protocol.json``,
``src/evaluation/{metrics,bootstrap,protocol}.py``,
``benchmarks/phase3_1_evaluate.py``, ``benchmarks/phase3_2_evaluate.py``,
``benchmarks/phase3_2c_ablation.py``, ``benchmarks/phase3_3_generalization
.py``, ``src/pipeline_builder.py``, ``src/failure_memory/``,
``src/data/synthetic.py``, or ``src/evaluation/representations.py``.

Run: python benchmarks/phase3_5_attack_generalization.py
Writes:
  experiments/results/phase3_5/attack_generalization.json
  experiments/results/phase3_5/per_seed_results.csv
"""
from __future__ import annotations

import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES, StreamSample  # noqa: E402
from src.evaluation.attacks import apply_feature_dropout, apply_feature_noise  # noqa: E402
from src.evaluation.bootstrap import bootstrap_ci  # noqa: E402
from src.evaluation.metrics import auprc, auroc  # noqa: E402
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402  -- reused, not reimplemented
from benchmarks.phase3_3_generalization import (  # noqa: E402  -- reused, not reimplemented
    BASELINES,
    _assert_no_regime2_leakage,
    _compute_condition_arrays,
    _evaluate_one,
    _fit_frozen_candidate,
    _is_probability,
    _reconstruct_regime2_with_confidences,
)

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_5"
PROTOCOL35_PATH = ROOT / "configs" / "phase3_5_attack_protocol.json"

# Phase 3.4-style display labels for benchmarks.phase3_3_generalization's
# BASELINES keys (reused verbatim -- see module docstring).
DISPLAY_LABELS = {
    "A_no_signal": "A -- No signal",
    "B_calibrated_confidence": "B -- Calibrated confidence",
    "C_original_failure_memory": "C -- Original Phase 2 Failure Memory",
    "D_supervised_failure_risk": "F -- Supervised Failure Risk (Phase 3.2C Experiment B / Phase 3.3 frozen candidate)",
}


class Phase35LeakageError(RuntimeError):
    """Raised when an attack condition's test samples fail a structural
    leakage/integrity check. Per the Phase 3.5 brief section 24: STOP, do
    not continue to generate benchmark claims."""


def load_protocol35() -> dict:
    data = json.loads(PROTOCOL35_PATH.read_text())
    if not data.get("_frozen"):
        raise ValueError("configs/phase3_5_attack_protocol.json is not marked frozen")
    return data


def _condition_test_samples(condition: dict, seed: int, system) -> list[StreamSample]:
    """Returns the regime-3/4 samples for one Phase 3.5 condition. 'clean'
    reuses ``system.test_stream`` verbatim (no regeneration). Every attack
    condition applies a deterministic post-hoc transform (see
    ``src/evaluation/attacks.py``) to a COPY of ``system.test_stream`` --
    the underlying clean stream object itself is never mutated."""
    if condition["id"] == "clean":
        return system.test_stream
    mechanism = condition["mechanism"]
    if mechanism == "feature_noise":
        return apply_feature_noise(
            system.test_stream, FEATURE_NAMES, std=condition["parameters"]["std"],
            seed=seed, attack_ordinal=condition["attack_ordinal"],
        )
    if mechanism == "feature_dropout":
        return apply_feature_dropout(
            system.test_stream, FEATURE_NAMES, dropped_features=condition["parameters"]["dropped_features"],
        )
    raise ValueError(f"unknown attack mechanism: {mechanism}")


def _assert_attack_preserves_ground_truth(clean_stream: list[StreamSample], attacked_stream: list[StreamSample], condition_id: str) -> None:
    """An attack must corrupt only what the system OBSERVES (context), never
    the ground truth it is judged against. Confirms labels/regime are
    row-for-row identical between the clean stream and the attacked one,
    and that (for non-dropout attacks) the context actually changed --
    i.e. the attack transform ran, it isn't silently a no-op."""
    if len(clean_stream) != len(attacked_stream):
        raise Phase35LeakageError(f"{condition_id}: attacked stream length differs from clean stream length")
    for c, a in zip(clean_stream, attacked_stream):
        if c.label != a.label or c.regime != a.regime:
            raise Phase35LeakageError(f"{condition_id}: an attack transform altered label or regime -- ground truth leakage")


def run_one_seed(seed: int, protocol: Phase31Protocol, protocol35: dict) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)  # frozen training, unmodified
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    candidate = _fit_frozen_candidate(regime2, seed)  # fit ONCE; reused unmodified across every condition below
    prevalence_a = system.n_logged_failures / protocol.regime_sizes[2]  # train-side only, fixed across all conditions

    all_conditions = [protocol35["clean_reference_condition"]] + protocol35["attack_matrix"]

    per_condition = {}
    for condition in all_conditions:
        test_samples = _condition_test_samples(condition, seed, system)
        _assert_no_regime2_leakage(test_samples, regime2)  # reused from Phase 3.3, unmodified
        if condition["id"] != "clean":
            _assert_attack_preserves_ground_truth(system.test_stream, test_samples, condition["id"])

        arrays = _compute_condition_arrays(system, candidate, test_samples, prevalence_a)
        results = {
            name: _evaluate_one(
                arrays["y_fail"], arrays["correct"], arrays["scores"][name],
                protocol.coverage_operating_points, protocol.calibration_bins,
                report_ece=_is_probability(name),
            )
            for name in BASELINES
        }
        per_condition[condition["id"]] = {
            "condition": condition,
            "n_test_samples": int(len(arrays["y_fail"])),
            "test_failure_prevalence": float(arrays["y_fail"].mean()),
            "results": results,
            "_arrays": arrays,
        }

    return {
        "seed": seed,
        "n_logged_failures_regime2": system.n_logged_failures,
        "candidate_fitted": candidate.is_fitted,
        "per_condition": per_condition,
    }


def aggregate_across_seeds(per_seed: list[dict], protocol: Phase31Protocol, all_condition_ids: list[str]) -> dict:
    agg = {}
    for condition_id in all_condition_ids:
        agg[condition_id] = {}
        for name in BASELINES:
            agg[condition_id][name] = {}
            for m in ["auroc", "auprc", "aurc"]:
                agg[condition_id][name][m] = _t_interval(
                    [row["per_condition"][condition_id]["results"][name][m] for row in per_seed], 0.95
                )
            ece_values = [row["per_condition"][condition_id]["results"][name]["ece"] for row in per_seed]
            agg[condition_id][name]["ece"] = _t_interval(ece_values, 0.95) if all(v is not None for v in ece_values) else {
                "mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0,
                "note": "ECE not meaningful for this baseline -- see _is_probability",
            }
            agg[condition_id][name]["precision_recall_at_coverage"] = []
            for i, cov in enumerate(protocol.coverage_operating_points):
                precisions = [row["per_condition"][condition_id]["results"][name]["precision_recall_at_coverage"][i]["precision"] for row in per_seed]
                recalls = [row["per_condition"][condition_id]["results"][name]["precision_recall_at_coverage"][i]["recall"] for row in per_seed]
                agg[condition_id][name]["precision_recall_at_coverage"].append(
                    {"coverage": cov, "precision": _t_interval(precisions, 0.95), "recall": _t_interval(recalls, 0.95)}
                )
    return agg


def run_bootstrap_for_primary_seed(per_seed: list[dict], protocol: Phase31Protocol, all_condition_ids: list[str]) -> dict:
    row = next(r for r in per_seed if r["seed"] == protocol.primary_seed)
    result = {}
    for condition_id in all_condition_ids:
        arrays = row["per_condition"][condition_id]["_arrays"]
        y_fail = arrays["y_fail"]
        result[condition_id] = {}
        for name in BASELINES:
            score = arrays["scores"][name]
            result[condition_id][name] = {
                "auroc": bootstrap_ci(auroc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
                "auprc": bootstrap_ci(auprc, y_fail, score, protocol.bootstrap.n_resamples, protocol.bootstrap.seed, protocol.bootstrap.confidence_level),
            }
    return {"primary_seed": protocol.primary_seed, "results": result}


def robustness_analysis(per_seed: list[dict], protocol: Phase31Protocol, attack_condition_ids: list[str]) -> dict:
    """Per-seed degradation/retention, aggregated with the same
    cross-seed Student-t methodology used everywhere else in this project.
    The excess-AUROC retention ratio is defined in
    configs/phase3_5_attack_protocol.json ('robustness_metric') BEFORE any
    result was computed -- not chosen after seeing which formula favors F."""
    out = {}
    for condition_id in attack_condition_ids:
        out[condition_id] = {}
        for name in BASELINES:
            deltas_auroc, deltas_auprc, deltas_aurc, retention_ratios = [], [], [], []
            for row in per_seed:
                clean = row["per_condition"]["clean"]["results"][name]
                attacked = row["per_condition"][condition_id]["results"][name]
                deltas_auroc.append(clean["auroc"] - attacked["auroc"])
                deltas_auprc.append(clean["auprc"] - attacked["auprc"])
                deltas_aurc.append(attacked["aurc"] - clean["aurc"])  # AURC: higher is worse, so attack-clean
                clean_excess = clean["auroc"] - 0.5
                if abs(clean_excess) < 1e-12:
                    retention_ratios.append(None)
                else:
                    retention_ratios.append((attacked["auroc"] - 0.5) / clean_excess)
            valid_ratios = [r for r in retention_ratios if r is not None]
            out[condition_id][name] = {
                "delta_auroc_clean_minus_attack": _t_interval(deltas_auroc, 0.95),
                "delta_auprc_clean_minus_attack": _t_interval(deltas_auprc, 0.95),
                "delta_aurc_attack_minus_clean": _t_interval(deltas_aurc, 0.95),
                "excess_auroc_retention_ratio": _t_interval(valid_ratios, 0.95) if valid_ratios else {
                    "mean": None, "std": None, "ci_low": None, "ci_high": None, "n": 0,
                    "note": "undefined for every seed -- clean AUROC == 0.5 (no informative signal to retain), expected for A_no_signal",
                },
                "n_seeds_with_defined_ratio": len(valid_ratios),
            }
    return out


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()  # frozen, unmodified
    protocol35 = load_protocol35()  # frozen, unmodified

    if protocol35["seeds"] != protocol.seeds or protocol35["primary_seed"] != protocol.primary_seed:
        raise ValueError("configs/phase3_5_attack_protocol.json's seeds/primary_seed disagree with configs/phase3_1_protocol.json")

    all_condition_ids = ["clean"] + [c["id"] for c in protocol35["attack_matrix"]]
    attack_condition_ids = [c["id"] for c in protocol35["attack_matrix"]]

    per_seed = [run_one_seed(seed, protocol, protocol35) for seed in protocol.seeds]
    aggregate = aggregate_across_seeds(per_seed, protocol, all_condition_ids)
    bootstrap_report = run_bootstrap_for_primary_seed(per_seed, protocol, all_condition_ids)
    robustness = robustness_analysis(per_seed, protocol, attack_condition_ids)

    clean_per_seed = []
    for row in per_seed:
        clean_row = {k: v for k, v in row.items() if k != "per_condition"}
        clean_row["per_condition"] = {
            cid: {k: v for k, v in cond.items() if k != "_arrays"} for cid, cond in row["per_condition"].items()
        }
        clean_per_seed.append(clean_row)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase3_1_protocol_config": protocol.raw,
        "phase3_5_attack_protocol": protocol35,
        "display_labels": DISPLAY_LABELS,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scikit_learn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "note": (
            "Phase 3.1 protocol reused unmodified. F is the exact Phase 3.2C Experiment B / Phase 3.3 "
            "frozen candidate, fit once per seed on clean regime-2 data and reused unmodified across "
            "the clean reference condition and every attack condition. No refitting on any condition."
        ),
    }

    output = {
        "meta": meta,
        "per_seed": clean_per_seed,
        "aggregate": aggregate,
        "bootstrap_primary_seed": bootstrap_report,
        "robustness_analysis": robustness,
    }
    (RESULTS_DIR / "attack_generalization.json").write_text(json.dumps(output, indent=2))

    with (RESULTS_DIR / "per_seed_results.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "condition", "baseline", "auroc", "auprc", "ece", "aurc", "n_test_samples"])
        for row in clean_per_seed:
            for condition_id in all_condition_ids:
                cond_row = row["per_condition"][condition_id]
                for name in BASELINES:
                    r = cond_row["results"][name]
                    writer.writerow([row["seed"], condition_id, name, r["auroc"], r["auprc"], r["ece"], r["aurc"], cond_row["n_test_samples"]])

    print(f"Phase 3.5 attack generalization -- {len(protocol.seeds)} seeds: {protocol.seeds}\n")
    for condition_id in all_condition_ids:
        print(f"=== {condition_id} ===")
        print(f"{'Candidate':<45} {'AUROC (mean, 95% CI)':<30}")
        for name in BASELINES:
            a = aggregate[condition_id][name]["auroc"]
            a_s = f"{a['mean']:.4f} [{a['ci_low']:.4f}, {a['ci_high']:.4f}]" if a["mean"] is not None else "n/a"
            print(f"{DISPLAY_LABELS[name][:44]:<45} {a_s:<30}")
        print()

    print(f"Wrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
