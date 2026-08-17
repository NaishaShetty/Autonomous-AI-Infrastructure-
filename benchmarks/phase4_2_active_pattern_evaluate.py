"""ACTIVE Phase 4.2 -- runs the full evaluation sequence for H2-Alibaba
(discovery -> validation-confirmation -> one-time frozen test evaluation,
baselines A/B/C/C'/C'', metrics, tier calibration, ablations), the
descriptive-only AIOps/AgentRx analyses, and the synthetic
methodological-validation sanity pass.

Follows the frozen protocol's ``evaluation_sequence`` exactly -- test rows
are read into memory only inside the single ``step_4_test_evaluation``
block below, never earlier. Writes all results under
``experiments/results/phase4_2_active/``.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.failure_experience.ingest import ingest_batch  # noqa: E402
from src.failure_experience.sources import real_agentrx, real_aiops  # noqa: E402
from src.failure_patterns import discovery_alibaba as da  # noqa: E402
from src.failure_patterns import discovery_descriptive as dd  # noqa: E402
from src.failure_patterns import metrics as pm  # noqa: E402
from src.failure_patterns.schema import EvidenceTier  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_2_active"
INGESTION_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Alibaba (H2-Alibaba, primary)
# ---------------------------------------------------------------------------

def run_alibaba(protocol: dict, split_name: str) -> dict:
    all_rows = da.load_population(split_name=split_name)
    train_rows = [r for r in all_rows if r["split"] == "train"]
    val_rows = [r for r in all_rows if r["split"] == "val"]
    test_rows = [r for r in all_rows if r["split"] == "test"]
    unknown = [r for r in all_rows if r["split"] == "unknown"]

    # STEP 1: discovery (train only)
    discovered = da.discover(train_rows, protocol)
    # STEP 2: validation confirmation (validation only)
    confirmed = da.confirm(discovered, val_rows, protocol)
    # STEP 3: freeze
    content_hash = da.dataset_content_hash()
    candidates = da.to_candidates(confirmed, protocol_version="phase4_2_active_v1", dataset_content_hash=content_hash, split_name=split_name)

    tier_counts = {}
    for t in EvidenceTier:
        tier_counts[t.value] = sum(1 for c in candidates if c.tier == t)

    # STEP 4: frozen test evaluation, touched exactly once
    test_outcomes = da.evaluate_test(candidates, test_rows, protocol)
    all_test_cands = da.all_test_candidates(test_rows, protocol)

    thresholds = protocol["minimum_evidence_thresholds"]
    margin_cfg = protocol["rate_elevation_criterion"]
    n_min_candidate = thresholds["N_MIN_CANDIDATE"]
    n_min_trusted = thresholds["N_MIN_TRUSTED"]
    margin_train = margin_cfg["MARGIN_TRAIN"]

    flags = {
        "A_no_pattern_learning": pm.flag_baseline_a(candidates),
        "B_naive_frequency_flagging": pm.flag_baseline_b(candidates, n_min_trusted),
        "C_proposed_tiered_rate_elevation": pm.flag_method_c(candidates),
        "C_prime_ablation_flat_threshold_no_n_floor": pm.flag_ablation_c_prime(candidates, n_min_candidate, margin_train),
        "C_double_prime_ablation_confirmed_only": pm.flag_ablation_c_double_prime(candidates),
    }

    metric_results = {
        name: pm.rate_elevation_metrics(flagged, test_outcomes, all_test_cands, margin_train)
        for name, flagged in flags.items()
    }

    tier_cal = pm.tier_calibration(candidates, test_outcomes, margin_train)

    n_evaluable_test_candidates = len(all_test_cands)
    min_n = protocol["acceptance_criteria"]["minimum_evaluable_n"]

    return {
        "split_name": split_name,
        "row_counts": {"train": len(train_rows), "val": len(val_rows), "test": len(test_rows), "unknown": len(unknown), "total": len(all_rows)},
        "train_baseline_failure_rate": (sum(1 for r in train_rows if r["status"] == "Failed") / len(train_rows)) if train_rows else None,
        "val_baseline_failure_rate": (sum(1 for r in val_rows if r["status"] == "Failed") / len(val_rows)) if val_rows else None,
        "test_baseline_failure_rate": (sum(1 for r in test_rows if r["status"] == "Failed") / len(test_rows)) if test_rows else None,
        "n_candidates_after_train_discovery": len(discovered),
        "n_candidates_after_validation_confirmation": len(candidates),
        "tier_counts": tier_counts,
        "n_evaluable_test_candidates": n_evaluable_test_candidates,
        "minimum_evaluable_n": min_n,
        "minimum_evaluable_n_met": n_evaluable_test_candidates >= min_n,
        "candidates": [
            {
                "task_name": c.task_name, "gpu_type": c.gpu_type, "tier": c.tier.value,
                "n_train": c.n_train, "train_rate": c.train_rate, "train_baseline_rate": c.train_baseline_rate,
                "train_elevation": c.train_elevation,
                "n_validation": c.n_validation, "validation_rate": c.validation_rate,
                "validation_baseline_rate": c.validation_baseline_rate, "validation_elevation": c.validation_elevation,
            }
            for c in sorted(candidates, key=lambda c: (-c.n_train, c.task_name, c.gpu_type))
        ],
        "baseline_flags_count": {name: len(flagged) for name, flagged in flags.items()},
        "metrics": metric_results,
        "tier_calibration": tier_cal,
    }


def run_n_min_trusted_sweep(protocol: dict, split_name: str = "temporal") -> dict:
    """Sensitivity sweep over N_MIN_TRUSTED -- labeled explicitly as a
    sweep, not a tuning procedure. The primary protocol's N_MIN_TRUSTED=20
    is not changed regardless of this sweep's outcome."""
    all_rows = da.load_population(split_name=split_name)
    train_rows = [r for r in all_rows if r["split"] == "train"]
    val_rows = [r for r in all_rows if r["split"] == "val"]
    test_rows = [r for r in all_rows if r["split"] == "test"]
    all_test_cands = da.all_test_candidates(test_rows, protocol)
    margin_train = protocol["rate_elevation_criterion"]["MARGIN_TRAIN"]

    sweep_values = next(a["values"] for a in protocol["ablations"] if a["name"] == "N_MIN_TRUSTED_sweep")
    results = {}
    for n_min_trusted in sweep_values:
        sweep_protocol = json.loads(json.dumps(protocol))
        sweep_protocol["minimum_evidence_thresholds"]["N_MIN_TRUSTED"] = n_min_trusted
        discovered = da.discover(train_rows, sweep_protocol)
        confirmed = da.confirm(discovered, val_rows, sweep_protocol)
        content_hash = da.dataset_content_hash()
        candidates = da.to_candidates(confirmed, "phase4_2_active_v1_sweep", content_hash, split_name)
        test_outcomes = da.evaluate_test(candidates, test_rows, sweep_protocol)
        flagged = pm.flag_method_c(candidates)
        m = pm.rate_elevation_metrics(flagged, test_outcomes, all_test_cands, margin_train)
        results[str(n_min_trusted)] = {"n_candidates": len(candidates), **m}
    return results


def run_pattern_stability(protocol: dict, split_name: str = "temporal") -> dict:
    """Ablation-adjacent robustness check: split train into two
    temporally-contiguous halves (by row order within the train split,
    which for the temporal split reflects trace-relative time), rediscover
    independently on each half, and report what fraction of the full-train
    candidate set has the same tier on both halves."""
    all_rows = da.load_population(split_name=split_name)
    train_rows = [r for r in all_rows if r["split"] == "train"]
    mid = len(train_rows) // 2
    half_a, half_b = train_rows[:mid], train_rows[mid:]

    def tiers_for(rows: list[dict]) -> dict:
        d = da.discover(rows, protocol)
        return {k: v["provisional_tier"].value for k, v in d.items()}

    tiers_a = tiers_for(half_a)
    tiers_b = tiers_for(half_b)
    common_keys = set(tiers_a) & set(tiers_b)
    stable = sum(1 for k in common_keys if tiers_a[k] == tiers_b[k])
    return {
        "n_candidates_half_a": len(tiers_a),
        "n_candidates_half_b": len(tiers_b),
        "n_common_candidates": len(common_keys),
        "n_stable_tier": stable,
        "stability_rate": (stable / len(common_keys)) if common_keys else None,
    }


# ---------------------------------------------------------------------------
# AIOps / AgentRx descriptive
# ---------------------------------------------------------------------------

def run_aiops_descriptive(protocol: dict) -> dict:
    cfg = protocol["descriptive_only_sources"]["aiops"]
    normalized = real_aiops.load_normalized()
    result = ingest_batch(normalized, INGESTION_TS)
    experiences = result.experiences

    associations = dd.aiops_recurrence(experiences, min_evidence_n=cfg["minimum_evidence_n"])
    candidates = [a for a in associations if a.is_candidate]
    temporal = dd.aiops_temporal_clustering(experiences)

    return {
        "n_experiences_ingested": len(experiences),
        "n_ingestion_errors": len(result.errors),
        "n_distinct_entity_fault_keys": len(associations),
        "n_recurring_candidates_n_geq_2": len(candidates),
        "recurring_associations": sorted(
            [{"entity": a.key[0], "fault_desrcibtion": a.key[1], "count": a.count} for a in candidates],
            key=lambda r: -r["count"],
        ),
        "occurrence_count_distribution": sorted([a.count for a in associations], reverse=True),
        "temporal_clustering": temporal,
        "label": "DESCRIPTIVE / EXPLORATORY -- no frozen train/test split exists for AIOps; no precision/recall claim is made.",
    }


def run_agentrx_descriptive(protocol: dict) -> dict:
    cfg = protocol["descriptive_only_sources"]["agentrx"]
    normalized = real_agentrx.load_normalized()
    result = ingest_batch(normalized, INGESTION_TS)
    experiences = result.experiences

    r = dd.agentrx_recurrence(experiences, min_evidence_n=cfg["minimum_evidence_n"])
    single = [a for a in r["single_label_domain_primary_category"] if a.is_candidate]
    multi = [a for a in r["multi_label_domain_any_category"] if a.is_candidate]

    return {
        "n_experiences_ingested": len(experiences),
        "n_ingestion_errors": len(result.errors),
        "domains": r["domains"],
        "categories_per_domain": r["categories_per_domain"],
        "single_label_recurring_associations": sorted(
            [{"domain": a.key[0], "primary_failure_category": a.key[1], "count": a.count} for a in single],
            key=lambda x: -x["count"],
        ),
        "multi_label_recurring_associations": sorted(
            [{"domain": a.key[0], "failure_category": a.key[1], "count": a.count} for a in multi],
            key=lambda x: -x["count"],
        ),
        "temporal_clustering": r["temporal_clustering"],
        "temporal_clustering_reason": r["temporal_clustering_reason"],
        "label": "DESCRIPTIVE / EXPLORATORY -- behavioral/agent failure-mode recurrence, NOT infrastructure failure patterns (AgentRx has no telemetry). No frozen split exists; no precision/recall claim is made.",
    }


# ---------------------------------------------------------------------------
# Synthetic methodological validation (NOT a hypothesis-bearing result)
# ---------------------------------------------------------------------------

def run_synthetic_methodological_validation(protocol: dict) -> dict:
    """Runs the SAME generic discover()/confirm()/evaluate_test() mechanism
    against the frozen Phase 4.0 synthetic episode stream, reshaped into
    the same (task_name, gpu_type, status, split) row contract used for
    Alibaba (workload_id -> task_name-analog, condition_id -> gpu_type-
    analog, is_failure -> status). This is a sanity/regression check of
    the MECHANISM's implementation correctness on a dataset whose
    generator-assigned structure is known -- it is NOT a Phase 4.2
    hypothesis result and must never be read as one (see the protocol's
    ``synthetic_data_role`` block)."""
    episodes_path = ROOT / "experiments" / "results" / "phase4_0" / "episodes.json"
    with open(episodes_path) as f:
        episodes = json.load(f)

    rows = [
        {
            "task_name": e["workload_id"],
            "gpu_type": e["condition_id"] or "clean",
            "status": "Failed" if e["is_failure"] else "Terminated",
            "split": e["split"],
        }
        for e in episodes
    ]
    train_rows = [r for r in rows if r["split"] == "train"]
    val_rows = [r for r in rows if r["split"] == "val"]
    test_rows = [r for r in rows if r["split"] == "test"]

    # The synthetic protocol thresholds differ in scale from Alibaba's (960
    # rows total vs 11750) -- use a scaled-down copy for this sanity check
    # only; this does not alter the frozen Alibaba protocol in any way.
    synth_protocol = json.loads(json.dumps(protocol))
    synth_protocol["minimum_evidence_thresholds"]["N_MIN_CANDIDATE"] = 2
    synth_protocol["minimum_evidence_thresholds"]["N_MIN_TRUSTED"] = 5
    synth_protocol["rate_elevation_criterion"]["N_MIN_VALIDATION"] = 1

    discovered = da.discover(train_rows, synth_protocol)
    confirmed = da.confirm(discovered, val_rows, synth_protocol)

    tier_counts = {}
    for t in EvidenceTier:
        tier_counts[t.value] = sum(1 for v in confirmed.values() if v["tier"] == t)

    # Known-answer sanity check: condition_id != "clean" rows are, by the
    # Phase 4.0 generator's own design, the induced-failure conditions --
    # every (workload_id, condition_id) candidate with condition_id!="clean"
    # is expected to show train-split elevation over the (workload_id,
    # "clean") baseline population. Checked descriptively, not asserted as
    # a metric.
    non_clean_candidates = [k for k in confirmed if k[1] != "clean"]
    non_clean_elevated = [
        k for k in non_clean_candidates
        if confirmed[k]["train_rate"] is not None and confirmed[k]["train_baseline_rate"] is not None
        and confirmed[k]["train_rate"] > confirmed[k]["train_baseline_rate"]
    ]

    return {
        "note": "METHODOLOGICAL VALIDATION ONLY -- not a Phase 4.2 real-data hypothesis result. Uses the frozen, read-only experiments/results/phase4_0/episodes.json (960 rows).",
        "n_rows_total": len(rows),
        "n_candidates_discovered": len(discovered),
        "n_candidates_after_confirmation": len(confirmed),
        "tier_counts": tier_counts,
        "n_non_clean_condition_candidates": len(non_clean_candidates),
        "n_non_clean_condition_candidates_with_train_elevation": len(non_clean_elevated),
        "sanity_interpretation": (
            "Non-'clean' condition_id candidates are, by the generator's own design, the "
            "induced-failure conditions and are expected to show train-split rate elevation "
            "over their workload's clean baseline more often than chance. This is reported "
            "descriptively as a mechanism sanity check, not as evidence for any active Phase "
            "4.2 hypothesis (synthetic data is not a source of real-world evidence, per the "
            "frozen protocol)."
        ),
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = da.load_protocol()
    protocol_hash = hashlib.sha256(da.PROTOCOL_PATH.read_bytes()).hexdigest()

    print("Running Alibaba H2 primary evaluation (temporal split)...")
    alibaba_primary = run_alibaba(protocol, "temporal")
    alibaba_primary["protocol_content_hash_sha256"] = protocol_hash
    with open(RESULTS_DIR / "pattern_results_alibaba.json", "w") as f:
        json.dump(alibaba_primary, f, indent=2, default=str)

    print("Running Alibaba H2 sensitivity check (random-stratified split)...")
    alibaba_sensitivity = run_alibaba(protocol, "random_stratified")
    with open(RESULTS_DIR / "pattern_results_alibaba_random_stratified_sensitivity.json", "w") as f:
        json.dump(alibaba_sensitivity, f, indent=2, default=str)

    print("Running N_MIN_TRUSTED sweep ablation...")
    sweep = run_n_min_trusted_sweep(protocol)
    with open(RESULTS_DIR / "ablation_n_min_trusted_sweep.json", "w") as f:
        json.dump(sweep, f, indent=2, default=str)

    print("Running pattern-stability ablation...")
    stability = run_pattern_stability(protocol)
    with open(RESULTS_DIR / "ablation_pattern_stability.json", "w") as f:
        json.dump(stability, f, indent=2, default=str)

    print("Running AIOps descriptive analysis...")
    aiops = run_aiops_descriptive(protocol)
    with open(RESULTS_DIR / "descriptive_aiops.json", "w") as f:
        json.dump(aiops, f, indent=2, default=str)

    print("Running AgentRx descriptive analysis...")
    agentrx = run_agentrx_descriptive(protocol)
    with open(RESULTS_DIR / "descriptive_agentrx.json", "w") as f:
        json.dump(agentrx, f, indent=2, default=str)

    print("Running synthetic methodological validation...")
    synthetic = run_synthetic_methodological_validation(protocol)
    with open(RESULTS_DIR / "synthetic_methodological_validation.json", "w") as f:
        json.dump(synthetic, f, indent=2, default=str)

    summary = {
        "alibaba_primary_temporal": {
            "n_evaluable_test_candidates": alibaba_primary["n_evaluable_test_candidates"],
            "minimum_evaluable_n": alibaba_primary["minimum_evaluable_n"],
            "minimum_evaluable_n_met": alibaba_primary["minimum_evaluable_n_met"],
            "tier_counts": alibaba_primary["tier_counts"],
            "method_C_metrics": alibaba_primary["metrics"]["C_proposed_tiered_rate_elevation"],
            "baseline_B_metrics": alibaba_primary["metrics"]["B_naive_frequency_flagging"],
        },
        "alibaba_random_stratified_sensitivity": {
            "n_evaluable_test_candidates": alibaba_sensitivity["n_evaluable_test_candidates"],
            "method_C_metrics": alibaba_sensitivity["metrics"]["C_proposed_tiered_rate_elevation"],
        },
        "aiops_n_recurring_candidates": aiops["n_recurring_candidates_n_geq_2"],
        "agentrx_n_domains": len(agentrx["domains"]),
        "synthetic_validation_tier_counts": synthetic["tier_counts"],
    }
    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(json.dumps(summary, indent=2, default=str))
    print(f"\nAll results written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
