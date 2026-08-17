"""Phase 3.6.5/3.6.6: recovery-action evaluation.

For every CRITICAL-tier sample (top 5% risk, per the acting candidate's
OWN regime-2-derived thresholds -- see ``src.evaluation.decision_policy``)
across the clean condition and Phase 3.5's three attack conditions, runs
three recovery variants:

  no_recovery       -- always rolls back to ABSTAIN (the 3.6.4 baseline)
  retry_only        -- attempts retry for feature_noise-diagnosed samples
                        only, ignoring the reconfigure branch entirely
                        (a naive, diagnosis-blind-for-dropout baseline)
  diagnosis_gated   -- the full frozen policy: retry for feature_noise,
                        reconfigure for feature_dropout, rollback for
                        clean (src.evaluation.recovery.attempt_recovery)

...for three acting candidates (B, F, BF_combined), so recovery is
compared against confidence-only and Failure-Risk-only interventions, not
reported as a standalone number.

Run: python benchmarks/phase3_6_recovery.py
Writes: experiments/results/phase3_6/recovery.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES  # noqa: E402
from src.evaluation.decision_policy import RiskTier, TierThresholds, assign_tier  # noqa: E402
from src.evaluation.diagnosis import diagnose  # noqa: E402
from src.evaluation.protocol import Phase31Protocol  # noqa: E402
from src.evaluation.recovery import RecoveryOutcome, RecoveryResult, attempt_recovery  # noqa: E402
from src.pipeline_builder import build_system  # noqa: E402

from benchmarks.phase3_1_evaluate import _t_interval  # noqa: E402
from benchmarks.phase3_3_generalization import (  # noqa: E402
    _fit_frozen_candidate,
    _reconstruct_regime2_with_confidences,
)
from benchmarks.phase3_5_attack_generalization import _condition_test_samples, load_protocol35  # noqa: E402
from benchmarks.phase3_6_complementarity import CANDIDATES, _fit_combined  # noqa: E402
from benchmarks.phase3_6_decision_policy import _regime2_scores  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase3_6"
VARIANTS = ["no_recovery", "retry_only", "diagnosis_gated"]


def _score_sample(context: dict, confidence: float, candidate_f, combined, which: str) -> float:
    b_score = 1.0 - confidence
    if which == "B_calibrated_confidence":
        return b_score
    f_score = candidate_f.risk(context, confidence)
    if which == "F_supervised_failure_risk":
        return f_score
    return combined.risk(b_score, f_score)


def _predict_and_confidence(system, context: dict):
    x = np.array([context[f] for f in FEATURE_NAMES], dtype=float)
    pred = system.workload_model.predict(x)
    calib_features = {**context, "predicted_proba": pred.predicted_proba, "margin": pred.margin, "entropy": pred.entropy}
    calib_result = system.calibrator.predict(calib_features)
    return pred, calib_result.calibrated_confidence


def _run_variant(variant: str, sample, seed, thresholds_acting, thresholds_b, condition, which, candidate_f, combined, system) -> RecoveryResult:
    diagnosed_cause = diagnose(sample.context, FEATURE_NAMES)

    if variant == "no_recovery":
        return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "none", diagnosed_cause, None, None)

    if variant == "retry_only":
        if diagnosed_cause != "feature_noise":
            return RecoveryResult(RecoveryOutcome.ROLLED_BACK, "none_not_noise", diagnosed_cause, None, None)
        # fall through to the shared retry implementation via attempt_recovery
        return attempt_recovery(
            sample, None, condition.get("attack_ordinal"), seed, FEATURE_NAMES,
            workload_predict=lambda s: system.workload_model.predict(np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)).predicted_label,
            score_fn=lambda ctx: _score_sample(ctx, _predict_and_confidence(system, ctx)[1], candidate_f, combined, which),
            b_score_fn=lambda ctx: _score_sample(ctx, _predict_and_confidence(system, ctx)[1], candidate_f, combined, "B_calibrated_confidence"),
            thresholds=thresholds_acting, b_thresholds=thresholds_b, condition_id=condition["id"],
        )

    # diagnosis_gated
    return attempt_recovery(
        sample, None, condition.get("attack_ordinal"), seed, FEATURE_NAMES,
        workload_predict=lambda s: system.workload_model.predict(np.array([s.context[f] for f in FEATURE_NAMES], dtype=float)).predicted_label,
        score_fn=lambda ctx: _score_sample(ctx, _predict_and_confidence(system, ctx)[1], candidate_f, combined, which),
        b_score_fn=lambda ctx: _score_sample(ctx, _predict_and_confidence(system, ctx)[1], candidate_f, combined, "B_calibrated_confidence"),
        thresholds=thresholds_acting, b_thresholds=thresholds_b, condition_id=condition["id"],
    )


def run_one_seed(seed: int, protocol: Phase31Protocol, protocol35: dict) -> dict:
    system = build_system(regime_sizes=protocol.regime_sizes, n_clusters=protocol.n_clusters, seed=seed)
    regime2 = _reconstruct_regime2_with_confidences(seed, protocol, system)
    candidate_f = _fit_frozen_candidate(regime2, seed)
    combined = _fit_combined(regime2, candidate_f, seed)
    regime2_scores = _regime2_scores(regime2, candidate_f, combined)
    thresholds = {name: TierThresholds.derive(regime2_scores[name]) for name in CANDIDATES}

    all_conditions = [protocol35["clean_reference_condition"]] + protocol35["attack_matrix"]

    records = []  # one row per (acting_candidate, variant, condition, sample) that was CRITICAL-tier
    for which in CANDIDATES:
        for condition in all_conditions:
            test_samples = _condition_test_samples(condition, seed, system)
            for s in test_samples:
                pred, confidence = _predict_and_confidence(system, s.context)
                score = _score_sample(s.context, confidence, candidate_f, combined, which)
                tier = assign_tier(score, thresholds[which])
                if tier != RiskTier.CRITICAL:
                    continue
                is_failure = int(pred.predicted_label != s.label)
                would_be_answer_correct = 1 - is_failure  # what ANSWER-ing this sample directly would have produced

                for variant in VARIANTS:
                    result = _run_variant(variant, s, seed, thresholds[which], thresholds["B_calibrated_confidence"], condition, which, candidate_f, combined, system)
                    records.append({
                        "acting": which,
                        "variant": variant,
                        "condition": condition["id"],
                        "is_failure": is_failure,
                        "would_be_answer_correct": would_be_answer_correct,
                        "outcome": result.outcome.value,
                        "action_taken": result.action_taken,
                        "diagnosed_cause": result.diagnosed_cause,
                        "recovered_correct": result.recovered_correct,
                    })

    return {"seed": seed, "records": records}


def _summarize(records: list[dict]) -> dict:
    n_critical = len(records)
    if n_critical == 0:
        return {"n_critical": 0}
    n_recovered = sum(1 for r in records if r["outcome"] == "RECOVERED")
    n_rolled_back = n_critical - n_recovered
    recovered_correct = [r for r in records if r["outcome"] == "RECOVERED" and r["recovered_correct"] is True]
    recovered_incorrect = [r for r in records if r["outcome"] == "RECOVERED" and r["recovered_correct"] is False]
    unnecessary = [r for r in records if r["outcome"] == "RECOVERED" and r["is_failure"] == 0]

    return {
        "n_critical": n_critical,
        "recovery_attempt_rate": n_recovered / n_critical,
        "recovery_success_rate": (len(recovered_correct) / n_recovered) if n_recovered else None,
        "recovery_failure_rate": (len(recovered_incorrect) / n_recovered) if n_recovered else None,
        "unsafe_recovery_rate": (len(recovered_incorrect) / n_recovered) if n_recovered else None,
        "no_recovery_rollback_rate": n_rolled_back / n_critical,
        "unnecessary_recovery_rate": (len(unnecessary) / n_recovered) if n_recovered else None,
        "utility_retention_after_recovery": n_recovered / n_critical,
        "baseline_utility_retention_no_recovery": 0.0,
    }


def aggregate(per_seed_records: list[list[dict]], protocol: Phase31Protocol) -> dict:
    out = {}
    for which in CANDIDATES:
        out[which] = {}
        for variant in VARIANTS:
            per_seed_summaries = []
            for records in per_seed_records:
                subset = [r for r in records if r["acting"] == which and r["variant"] == variant]
                per_seed_summaries.append(_summarize(subset))
            metric_names = ["recovery_attempt_rate", "recovery_success_rate", "recovery_failure_rate", "utility_retention_after_recovery"]
            agg_metrics = {}
            for m in metric_names:
                values = [s[m] for s in per_seed_summaries if s.get(m) is not None]
                agg_metrics[m] = _t_interval(values, 0.95) if values else {"mean": None, "n": 0}
            out[which][variant] = {"per_seed": per_seed_summaries, "aggregate": agg_metrics}
    return out


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = Phase31Protocol.load()
    protocol35 = load_protocol35()

    per_seed = [run_one_seed(seed, protocol, protocol35) for seed in protocol.seeds]
    per_seed_records = [row["records"] for row in per_seed]
    agg = aggregate(per_seed_records, protocol)

    output = {
        "meta": {"variants": VARIANTS, "candidates": CANDIDATES, "note": "Only CRITICAL-tier (top-5%) samples are recovery-eligible, per the frozen protocol."},
        "per_seed_record_counts": [{"seed": row["seed"], "n_records": len(row["records"])} for row in per_seed],
        "aggregate": agg,
    }
    (RESULTS_DIR / "recovery.json").write_text(json.dumps(output, indent=2))

    print("Phase 3.6.5/3.6.6 recovery\n")
    for which in CANDIDATES:
        print(f"=== acting candidate: {which} ===")
        for variant in VARIANTS:
            a = agg[which][variant]["aggregate"]
            sr = a["recovery_success_rate"]["mean"]
            fr = a["recovery_failure_rate"]["mean"]
            ar = a["recovery_attempt_rate"]["mean"]
            print(f"  {variant:<18} attempt_rate={ar} success_rate={sr} failure_rate={fr}")
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
