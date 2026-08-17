"""Active Phase 4.3 -- STEPs 11-20: baselines, proposed mechanism,
uncertainty/abstention, TRAIN fit, VALIDATION-only hyperparameter freeze,
ONE-SHOT frozen TEST evaluation, statistics, and pre-registered ablations.

Discipline enforced here (matches configs/phase4_3_recovery_protocol.json):
- min_evidence is swept and selected on VALIDATION ONLY (function
  ``select_min_evidence_on_validation``), before TEST is ever touched.
- TEST is read and scored exactly once, in ``run_frozen_test``.
- Oracle is used only as a reference bound (never scored as a competing
  policy for H3).

Writes experiments/results/phase4_3/results.json.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scipy import stats as scipy_stats  # noqa: E402

from src.recovery.environment import oracle_best_action, transition  # noqa: E402
from src.recovery.io import read_jsonl  # noqa: E402
from src.recovery.policy import (  # noqa: E402
    EmpiricalRecoveryPolicy,
    FixedPriorityPolicy,
    FrequencyOnlyPolicy,
    RandomValidPolicy,
    UnmaskedUtilityPolicy,
    make_family_only_policy,
    make_no_abstention_policy,
)
from src.recovery.schema import ActionSelection, RecoveryEpisode, ScenarioFamily, Split, ValidatedOutcome  # noqa: E402
from src.recovery.utility import recovery_utility  # noqa: E402
from src.recovery.sample_size import MINIMUM_N_TEST_TOTAL  # noqa: E402
from src.recovery.actions import is_unsafe  # noqa: E402

DATA_DIR = ROOT / "data" / "controlled_recovery"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_3"

MIN_EVIDENCE_SWEEP = [2, 3, 5, 8, 12, 20]
UNSAFE_RATE_THRESHOLD = 0.00
MIN_EFFECT_SIZE = 0.15
ALPHA = 0.05


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _resolve(scenario, action):
    return transition(scenario, action)


def score_policy_on_scenarios(policy, episodes: list[RecoveryEpisode]) -> list[dict]:
    """For each unresolved scenario episode, ask the policy to select an
    action, resolve it via the environment, and return a per-episode row.
    This is where VALIDATION/TEST scenarios actually get "used" -- their
    outcome is computed fresh per policy, never read off a pre-baked label."""
    rows = []
    for ep in episodes:
        ctx = ep.scenario.decision_context
        selection = policy.select_action(ctx)
        trans = _resolve(ep.scenario, selection.selected_action)
        rows.append({
            "episode_id": ep.episode_id,
            "family": ep.scenario.family.value,
            "selected_action": selection.selected_action.value,
            "abstained": selection.abstained,
            "outcome": trans.outcome.value,
            "unsafe_action_taken": trans.unsafe_action_taken,
            "success": trans.outcome == ValidatedOutcome.SUCCESS,
            "partial": trans.outcome == ValidatedOutcome.PARTIAL_SUCCESS,
            "utility": recovery_utility(trans.outcome, trans.recovery_cost, trans.recovery_latency_seconds),
            "latency": trans.recovery_latency_seconds,
            "cost": trans.recovery_cost,
        })
    return rows


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {}
    return {
        "n_episodes": n,
        "validated_recovery_success_rate": sum(r["success"] for r in rows) / n,
        "unsafe_action_rate": sum(r["unsafe_action_taken"] for r in rows) / n,
        "recovery_utility_mean": sum(r["utility"] for r in rows) / n,
        "abstention_rate": sum(r["abstained"] for r in rows) / n,
        "partial_recovery_rate": sum(r["partial"] for r in rows) / n,
        "recovery_latency_mean_seconds": sum(r["latency"] for r in rows) / n,
        "recovery_cost_mean": sum(r["cost"] for r in rows) / n,
    }


def per_family(rows: list[dict]) -> dict:
    out = {}
    for fam in {r["family"] for r in rows}:
        out[fam] = aggregate([r for r in rows if r["family"] == fam])
    return out


def wilson_interval(successes: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = scipy_stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def bootstrap_diff_ci(rows_a: list[dict], rows_b: list[dict], key: str = "success", n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Paired bootstrap on the success-rate DIFFERENCE (a - b), episode-aligned."""
    assert len(rows_a) == len(rows_b)
    rng = random.Random(seed)
    n = len(rows_a)
    idx_pool = list(range(n))
    diffs = []
    a_vals = [1.0 if r[key] else 0.0 for r in rows_a]
    b_vals = [1.0 if r[key] else 0.0 for r in rows_b]
    for _ in range(n_boot):
        sample = [rng.randrange(n) for _ in range(n)]
        a_mean = sum(a_vals[i] for i in sample) / n
        b_mean = sum(b_vals[i] for i in sample) / n
        diffs.append(a_mean - b_mean)
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot) - 1]
    return (lo, hi)


def mcnemar_exact(rows_a: list[dict], rows_b: list[dict], key: str = "success") -> dict:
    """Paired exact McNemar test on episode-aligned binary outcomes."""
    assert len(rows_a) == len(rows_b)
    a_only = b_only = both = neither = 0
    for ra, rb in zip(rows_a, rows_b):
        av, bv = bool(ra[key]), bool(rb[key])
        if av and not bv:
            a_only += 1
        elif bv and not av:
            b_only += 1
        elif av and bv:
            both += 1
        else:
            neither += 1
    n_discordant = a_only + b_only
    if n_discordant == 0:
        p_value = 1.0
    else:
        result = scipy_stats.binomtest(min(a_only, b_only), n_discordant, 0.5, alternative="two-sided")
        p_value = result.pvalue
    return {"a_only": a_only, "b_only": b_only, "both": both, "neither": neither,
            "n_discordant": n_discordant, "p_value": p_value}


def holm_bonferroni(p_values: dict[str, float], alpha: float = ALPHA) -> dict[str, dict]:
    """Standard Holm step-down procedure: sorted ascending p-values,
    threshold alpha/(m-i) for the i-th (0-indexed); once one comparison
    fails to clear its threshold, it and every later (larger-p) comparison
    is marked not-significant."""
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    still_rejecting = True
    for i, (name, p) in enumerate(items):
        threshold = alpha / (m - i)
        significant = still_rejecting and p < threshold
        if not significant:
            still_rejecting = False
        out[name] = {"p_value": p, "holm_threshold": threshold, "significant": significant}
    return out


# ---------------------------------------------------------------------------
# STEP 17: select min_evidence on VALIDATION only
# ---------------------------------------------------------------------------


def select_min_evidence_on_validation(train, validation) -> dict:
    sweep_results = []
    for me in MIN_EVIDENCE_SWEEP:
        policy = EmpiricalRecoveryPolicy(min_evidence=me).fit(train)
        rows = score_policy_on_scenarios(policy, validation)
        agg = aggregate(rows)
        sweep_results.append({"min_evidence": me, **agg})
    # frozen selection rule: maximize validated_recovery_success_rate,
    # break ties by lower unsafe_action_rate then lower min_evidence (simplest model)
    best = max(sweep_results, key=lambda r: (r["validated_recovery_success_rate"], -r["unsafe_action_rate"], -r["min_evidence"]))
    return {"sweep": sweep_results, "selected_min_evidence": best["min_evidence"]}


# ---------------------------------------------------------------------------
# STEP 19: frozen test evaluation (run exactly once)
# ---------------------------------------------------------------------------


def run_frozen_test(train, test, min_evidence: int) -> dict:
    policies = {
        "baseline_fixed_priority": FixedPriorityPolicy(),
        "baseline_random_valid": RandomValidPolicy(),
        "proposed_empirical_recovery": EmpiricalRecoveryPolicy(min_evidence=min_evidence).fit(train),
        "ablation_frequency_only": FrequencyOnlyPolicy().fit(train),
        "ablation_no_abstention": make_no_abstention_policy(min_evidence=min_evidence).fit(train),
        "ablation_family_only": make_family_only_policy(min_evidence=min_evidence).fit(train),
    }
    rows_by_policy = {name: score_policy_on_scenarios(p, test) for name, p in policies.items()}

    # safety ablation: unmasked utility wraps the fitted proposed policy
    inner = policies["proposed_empirical_recovery"]
    unmasked = UnmaskedUtilityPolicy(inner)
    rows_by_policy["ablation_unmasked_utility"] = score_policy_on_scenarios(unmasked, test)

    # oracle reference bound (uses hidden_cause; NEVER a competitor for H3)
    oracle_rows = []
    for ep in test:
        best_action = oracle_best_action(ep.scenario)
        trans = _resolve(ep.scenario, best_action)
        oracle_rows.append({
            "episode_id": ep.episode_id, "family": ep.scenario.family.value,
            "selected_action": best_action.value, "abstained": False,
            "outcome": trans.outcome.value, "unsafe_action_taken": trans.unsafe_action_taken,
            "success": trans.outcome == ValidatedOutcome.SUCCESS,
            "partial": trans.outcome == ValidatedOutcome.PARTIAL_SUCCESS,
            "utility": recovery_utility(trans.outcome, trans.recovery_cost, trans.recovery_latency_seconds),
            "latency": trans.recovery_latency_seconds, "cost": trans.recovery_cost,
        })
    rows_by_policy["oracle_reference_bound"] = oracle_rows

    aggregates = {name: aggregate(rows) for name, rows in rows_by_policy.items()}
    per_family_aggregates = {name: per_family(rows) for name, rows in rows_by_policy.items()}

    # primary statistical comparison: proposed vs baseline_fixed_priority
    proposed_rows = rows_by_policy["proposed_empirical_recovery"]
    fixed_rows = rows_by_policy["baseline_fixed_priority"]
    random_rows = rows_by_policy["baseline_random_valid"]

    mcnemar_vs_fixed = mcnemar_exact(proposed_rows, fixed_rows, key="success")
    mcnemar_vs_random = mcnemar_exact(proposed_rows, random_rows, key="success")

    p_success = aggregates["proposed_empirical_recovery"]["validated_recovery_success_rate"]
    n_success = sum(r["success"] for r in proposed_rows)
    ci_proposed = wilson_interval(n_success, len(proposed_rows))
    n_success_fixed = sum(r["success"] for r in fixed_rows)
    ci_fixed = wilson_interval(n_success_fixed, len(fixed_rows))

    diff_ci_vs_fixed = bootstrap_diff_ci(proposed_rows, fixed_rows, key="success")
    diff_ci_vs_random = bootstrap_diff_ci(proposed_rows, random_rows, key="success")

    p_values = {"vs_fixed_priority": mcnemar_vs_fixed["p_value"], "vs_random_valid": mcnemar_vs_random["p_value"]}
    holm = holm_bonferroni(p_values)

    effect_size_vs_fixed = aggregates["proposed_empirical_recovery"]["validated_recovery_success_rate"] - aggregates["baseline_fixed_priority"]["validated_recovery_success_rate"]

    return {
        "min_evidence_used": min_evidence,
        "n_test_total": len(test),
        "minimum_n_test_required": MINIMUM_N_TEST_TOTAL,
        "sample_size_requirement_met": len(test) >= MINIMUM_N_TEST_TOTAL,
        "aggregates": aggregates,
        "per_family": per_family_aggregates,
        "statistics": {
            "wilson_95ci_proposed_success_rate": ci_proposed,
            "wilson_95ci_fixed_priority_success_rate": ci_fixed,
            "mcnemar_proposed_vs_fixed_priority": mcnemar_vs_fixed,
            "mcnemar_proposed_vs_random_valid": mcnemar_vs_random,
            "bootstrap_95ci_diff_proposed_minus_fixed": diff_ci_vs_fixed,
            "bootstrap_95ci_diff_proposed_minus_random": diff_ci_vs_random,
            "holm_bonferroni": holm,
            "effect_size_vs_fixed_priority": effect_size_vs_fixed,
            "min_effect_size_required": MIN_EFFECT_SIZE,
        },
    }


# ---------------------------------------------------------------------------
# Verdict logic (frozen acceptance criteria, brief section 41)
# ---------------------------------------------------------------------------


def determine_verdict(test_result: dict, leakage_audit_passed: bool) -> dict:
    reasons = []
    if not leakage_audit_passed:
        return {"verdict": "FAIL", "reasons": ["leakage audit did not pass 100%"]}

    if not test_result["sample_size_requirement_met"]:
        return {"verdict": "INCONCLUSIVE", "reasons": [
            f"n_test_total={test_result['n_test_total']} < minimum_n_test_required={test_result['minimum_n_test_required']}"]}

    proposed_unsafe = test_result["aggregates"]["proposed_empirical_recovery"]["unsafe_action_rate"]
    h3_safety_supported = proposed_unsafe <= UNSAFE_RATE_THRESHOLD
    reasons.append(f"H3-SAFETY: proposed unsafe_action_rate={proposed_unsafe:.4f} <= threshold={UNSAFE_RATE_THRESHOLD} -> {'SUPPORTED' if h3_safety_supported else 'NOT SUPPORTED'}")

    effect = test_result["statistics"]["effect_size_vs_fixed_priority"]
    p_value = test_result["statistics"]["mcnemar_proposed_vs_fixed_priority"]["p_value"]
    significant = test_result["statistics"]["holm_bonferroni"].get("vs_fixed_priority", {}).get("significant", False)
    effect_meets_min = effect >= test_result["statistics"]["min_effect_size_required"]
    h3_supported = significant and effect_meets_min
    reasons.append(f"H3: effect_size={effect:.4f} (min required {test_result['statistics']['min_effect_size_required']}), "
                    f"mcnemar p={p_value:.4f}, holm-significant={significant} -> {'SUPPORTED' if h3_supported else 'NOT SUPPORTED'}")

    proposed_utility = test_result["aggregates"]["proposed_empirical_recovery"]["recovery_utility_mean"]
    fixed_utility = test_result["aggregates"]["baseline_fixed_priority"]["recovery_utility_mean"]
    h3_utility_supported = proposed_utility >= fixed_utility
    reasons.append(f"H3-UTILITY: proposed_utility_mean={proposed_utility:.4f} vs fixed_priority_utility_mean={fixed_utility:.4f} -> {'SUPPORTED' if h3_utility_supported else 'NOT SUPPORTED'}")

    if not h3_safety_supported:
        verdict = "FAIL"
        reasons.append("H3-SAFETY failing is treated as FAIL, not merely INCONCLUSIVE, per the frozen protocol's zero-tolerance unsafe-rate threshold.")
    elif h3_supported:
        verdict = "PASS"
    else:
        verdict = "PASS"
        reasons.append("PASS -- HYPOTHESIS NOT SUPPORTED: the experiment was valid, adequately powered, and pre-registered; H3 itself was not confirmed on this evidence. This is a valid negative research result, not an implementation failure.")

    return {"verdict": verdict, "h3_supported": h3_supported, "h3_safety_supported": h3_safety_supported,
            "h3_utility_supported": h3_utility_supported, "reasons": reasons}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    train = read_jsonl(DATA_DIR / "train.jsonl")
    validation = read_jsonl(DATA_DIR / "validation.jsonl")
    test = read_jsonl(DATA_DIR / "test.jsonl")

    print(f"train={len(train)} validation={len(validation)} test={len(test)}")

    print("\n== STEP 17: selecting min_evidence on VALIDATION only ==")
    val_selection = select_min_evidence_on_validation(train, validation)
    for row in val_selection["sweep"]:
        print(f"  min_evidence={row['min_evidence']:>3}  success_rate={row['validated_recovery_success_rate']:.3f}  "
              f"unsafe_rate={row['unsafe_action_rate']:.3f}  abstention_rate={row['abstention_rate']:.3f}")
    frozen_min_evidence = val_selection["selected_min_evidence"]
    print(f"FROZEN min_evidence = {frozen_min_evidence}")

    leakage_audit_path = RESULTS_DIR / "leakage_audit.json"
    leakage_audit_passed = False
    if leakage_audit_path.exists():
        la = json.loads(leakage_audit_path.read_text())
        leakage_audit_passed = la["n_passed"] == la["n_checks"]

    print("\n== STEP 19: FROZEN TEST evaluation (run exactly once) ==")
    test_result = run_frozen_test(train, test, frozen_min_evidence)
    for name, agg in test_result["aggregates"].items():
        print(f"  {name:32s} success={agg['validated_recovery_success_rate']:.3f} "
              f"unsafe={agg['unsafe_action_rate']:.3f} utility={agg['recovery_utility_mean']:.3f} "
              f"abstain={agg['abstention_rate']:.3f}")

    verdict = determine_verdict(test_result, leakage_audit_passed)
    print("\n== VERDICT ==")
    print(verdict["verdict"])
    for r in verdict.get("reasons", []):
        print(f"  - {r}")

    output = {
        "milestone": "ACTIVE_PHASE_4_3_RECOVERY_LEARNING_AND_EVALUATION",
        "evidence_type": "CONTROLLED",
        "dataset": {"n_train": len(train), "n_validation": len(validation), "n_test": len(test)},
        "validation_hyperparameter_selection": val_selection,
        "test_result": test_result,
        "leakage_audit_passed": leakage_audit_passed,
        "verdict": verdict,
    }
    out_path = RESULTS_DIR / "results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
