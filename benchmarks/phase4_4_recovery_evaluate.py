"""Active Phase 4.4 -- STEP 9: run the frozen TEST evaluation ONCE, compute
H4/H4-SAFETY/H4-UTILITY/H4-ABSTENTION/H4-ABLATION.

Deterministic given the frozen dataset + frozen observation_noise_rate --
no RNG state persists across runs. Run 3x to confirm byte-identical output
(the same discipline as Phase 4.3's hash()-bug determinism check, and this
phase's own environment_v2.py note about avoiding hash()-seeded RNG).

Run: PYTHONHASHSEED=0 python benchmarks/phase4_4_recovery_evaluate.py
Writes experiments/results/phase4_4/results.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scipy import stats as scipy_stats  # noqa: E402

from src.recovery.environment_v2 import make_step2_context, oracle_best_action_v2, run_step1, run_step2  # noqa: E402
from src.recovery.io_v2 import read_jsonl  # noqa: E402
from src.recovery.policy import EmpiricalRecoveryPolicy as V1EmpiricalRecoveryPolicy  # noqa: E402
from src.recovery.policy_v2 import (  # noqa: E402
    FixedPrioritySequential,
    RandomValidSequential,
    SequentialEmpiricalRecoveryPolicy,
    SequentialEmpiricalRecoveryPolicyNoAbstention,
    SingleStepEmpirical,
)
from src.recovery.schema import ScenarioFamily, ValidatedOutcome  # noqa: E402
from src.recovery.utility import recovery_utility  # noqa: E402
from src.recovery.sample_size_v2 import MINIMUM_N_TEST_TOTAL  # noqa: E402

DATA_DIR = ROOT / "data" / "controlled_recovery_v2"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_4"
CONFIG_PATH = ROOT / "configs" / "phase4_4_recovery_protocol.json"

MIN_EVIDENCE = 2  # REUSES Phase 4.3's own VALIDATION-selected min_evidence (experiments/results/phase4_3/results.json:
# "selected_min_evidence": 2) -- NOT re-guessed here. Protocol section 6 says the proposed policy uses "the same
# Laplace-smoothing approach as 4.3", and configs/phase4_4_recovery_protocol.json names ONLY observation_noise_rate
# as the value still to be set by a VALIDATION sweep -- min_evidence is not listed as an open hyperparameter for
# this phase, so it is carried forward from 4.3's already-frozen VALIDATION selection rather than hardcoding an
# arbitrary new default. (A first pass at 5 produced a 32% abstention rate that traced back to exactly this --
# an unjustified guess, not a finding -- and was corrected before this evaluation was treated as final.)
UNSAFE_RATE_THRESHOLD = 0.00
MIN_EFFECT_SIZE = 0.15
ALPHA = 0.05


def _noise_rate() -> float:
    config = json.loads(CONFIG_PATH.read_text())
    return config["environment"]["observation_signal"]["observation_noise_rate"]


def _v1_ctx(ctx1):
    from src.recovery.schema import DecisionContext as DecisionContextV1
    return DecisionContextV1(
        scenario_id=ctx1.scenario_id, episode_id=ctx1.episode_id, family=ctx1.family,
        symptom_pattern=ctx1.symptom_pattern, severity=ctx1.severity, workload_type=ctx1.workload_type,
        candidate_actions=ctx1.candidate_actions,
    )


def score_sequential_policy(policy, episodes, noise_rate: float, is_single_step: bool = False) -> list[dict]:
    rows = []
    for ep in episodes:
        scenario = ep.scenario
        ctx1 = scenario.step1_context
        sel1 = policy.select_step1(ctx1)
        t1, terminal = run_step1(scenario, sel1.selected_action, noise_rate)

        if is_single_step:
            # forced single-step: never takes step 2, regardless of terminal
            rows.append(_row(ep.episode_id, scenario.family.value, sel1.selected_action.value,
                              sel1.abstained, t1, n_steps=1))
            continue

        if terminal:
            rows.append(_row(ep.episode_id, scenario.family.value, sel1.selected_action.value,
                              sel1.abstained, t1, n_steps=1))
            continue

        ctx2 = make_step2_context(scenario, sel1.selected_action, t1.observation)
        sel2 = policy.select_step2(ctx2)
        t2 = run_step2(scenario, sel2.selected_action)
        rows.append(_row(ep.episode_id, scenario.family.value, sel2.selected_action.value,
                          sel2.abstained, t2, n_steps=2))
    return rows


def _row(episode_id, family, selected_action, abstained, trans, n_steps: int) -> dict:
    return {
        "episode_id": episode_id, "family": family, "selected_action": selected_action, "abstained": abstained,
        "outcome": trans.outcome.value, "unsafe_action_taken": trans.unsafe_action_taken,
        "success": trans.outcome == ValidatedOutcome.SUCCESS, "partial": trans.outcome == ValidatedOutcome.PARTIAL_SUCCESS,
        "utility": recovery_utility(trans.outcome, trans.recovery_cost, trans.recovery_latency_seconds),
        "latency": trans.recovery_latency_seconds, "cost": trans.recovery_cost, "n_steps": n_steps,
    }


def score_oracle(episodes) -> list[dict]:
    rows = []
    for ep in episodes:
        scenario = ep.scenario
        best_action = oracle_best_action_v2(scenario)
        t1, terminal = run_step1(scenario, best_action, observation_noise_rate=0.0)  # oracle sees no noise, reference bound only
        if terminal:
            rows.append(_row(ep.episode_id, scenario.family.value, best_action.value, False, t1, n_steps=1))
            continue
        ctx2 = make_step2_context(scenario, best_action, t1.observation)
        best_action2 = oracle_best_action_v2(scenario)
        t2 = run_step2(scenario, best_action2)
        rows.append(_row(ep.episode_id, scenario.family.value, best_action2.value, False, t2, n_steps=2))
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
        "mean_n_steps": sum(r["n_steps"] for r in rows) / n,
    }


def per_family(rows: list[dict]) -> dict:
    return {fam: aggregate([r for r in rows if r["family"] == fam]) for fam in {r["family"] for r in rows}}


def mcnemar_exact(rows_a, rows_b, key="success") -> dict:
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
    p_value = 1.0 if n_discordant == 0 else scipy_stats.binomtest(min(a_only, b_only), n_discordant, 0.5, alternative="two-sided").pvalue
    return {"a_only": a_only, "b_only": b_only, "both": both, "neither": neither, "n_discordant": n_discordant, "p_value": p_value}


def holm_bonferroni(p_values: dict[str, float], alpha: float = ALPHA) -> dict[str, dict]:
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


def run_frozen_test(train, test, noise_rate: float) -> dict:
    v1_inner = V1EmpiricalRecoveryPolicy(min_evidence=MIN_EVIDENCE)
    v1_train_episodes = []
    from src.recovery.schema import ActionSelection, RecoveryEpisode, Split
    from src.recovery.provenance import stamp_provenance as v1_stamp
    for ep in train:
        if ep.step1_selection is None or ep.step1_transition is None:
            continue
        v1_ctx = _v1_ctx(ep.scenario.step1_context)
        v1_sel = ActionSelection(selected_action=ep.step1_selection.selected_action, policy_id="v2_train_reuse", policy_version="v1")
        v1_scenario = _fake_v1_scenario(ep.scenario, v1_ctx)
        v1_transition = _to_v1_transition(ep.step1_transition)
        v1_train_episodes.append(RecoveryEpisode(
            episode_id=ep.episode_id, scenario=v1_scenario, policy_selection=v1_sel, transition=v1_transition,
            provenance=v1_stamp(ep.episode_id, ep.provenance.seed, Split.TRAIN),
        ))
    v1_inner.fit(v1_train_episodes)

    policies = {
        "baseline_fixed_priority_sequential": (FixedPrioritySequential(), False),
        "baseline_random_valid_sequential": (RandomValidSequential(), False),
        "proposed_sequential_empirical_recovery": (SequentialEmpiricalRecoveryPolicy(min_evidence=MIN_EVIDENCE).fit(train), False),
        "single_step_empirical_ablation": (SingleStepEmpirical(v1_inner), True),
        "proposed_no_abstention": (SequentialEmpiricalRecoveryPolicyNoAbstention(min_evidence=MIN_EVIDENCE).fit(train), False),
    }
    rows_by_policy = {name: score_sequential_policy(p, test, noise_rate, is_single_step=single)
                       for name, (p, single) in policies.items()}
    rows_by_policy["oracle_reference_bound"] = score_oracle(test)

    aggregates = {name: aggregate(rows) for name, rows in rows_by_policy.items()}
    per_family_aggregates = {name: per_family(rows) for name, rows in rows_by_policy.items()}

    proposed_rows = rows_by_policy["proposed_sequential_empirical_recovery"]
    fixed_rows = rows_by_policy["baseline_fixed_priority_sequential"]
    random_rows = rows_by_policy["baseline_random_valid_sequential"]
    single_step_rows = rows_by_policy["single_step_empirical_ablation"]

    mcnemar_vs_fixed = mcnemar_exact(proposed_rows, fixed_rows)
    mcnemar_vs_random = mcnemar_exact(proposed_rows, random_rows)
    mcnemar_vs_single_step = mcnemar_exact(proposed_rows, single_step_rows)

    p_values = {"vs_fixed_priority_sequential": mcnemar_vs_fixed["p_value"], "vs_random_valid_sequential": mcnemar_vs_random["p_value"]}
    holm = holm_bonferroni(p_values)

    effect_vs_fixed = aggregates["proposed_sequential_empirical_recovery"]["validated_recovery_success_rate"] - aggregates["baseline_fixed_priority_sequential"]["validated_recovery_success_rate"]
    effect_vs_single_step = aggregates["proposed_sequential_empirical_recovery"]["validated_recovery_success_rate"] - aggregates["single_step_empirical_ablation"]["validated_recovery_success_rate"]

    # H4-ABSTENTION: dependency_failure family only
    dep_proposed = [r for r in proposed_rows if r["family"] == "dependency_failure"]
    dep_no_abstention = [r for r in rows_by_policy["proposed_no_abstention"] if r["family"] == "dependency_failure"]
    proposed_dep_abstain_rate = sum(r["abstained"] for r in dep_proposed) / len(dep_proposed) if dep_proposed else 0.0
    fixed_dep_rows = [r for r in fixed_rows if r["family"] == "dependency_failure"]
    fixed_dep_abstain_rate = sum(r["abstained"] for r in fixed_dep_rows) / len(fixed_dep_rows) if fixed_dep_rows else 0.0

    other_families = ["resource_exhaustion", "transient_failure", "configuration_failure"]
    proposed_other_rows = [r for r in proposed_rows if r["family"] in other_families]
    no_abstention_other_rows = [r for r in rows_by_policy["proposed_no_abstention"] if r["family"] in other_families]
    proposed_other_utility = sum(r["utility"] for r in proposed_other_rows) / len(proposed_other_rows) if proposed_other_rows else 0.0
    no_abstention_other_utility = sum(r["utility"] for r in no_abstention_other_rows) / len(no_abstention_other_rows) if no_abstention_other_rows else 0.0

    return {
        "min_evidence_used": MIN_EVIDENCE,
        "observation_noise_rate_used": noise_rate,
        "n_test_total": len(test),
        "minimum_n_test_required": MINIMUM_N_TEST_TOTAL,
        "sample_size_requirement_met": len(test) >= MINIMUM_N_TEST_TOTAL,
        "aggregates": aggregates,
        "per_family": per_family_aggregates,
        "statistics": {
            "mcnemar_proposed_vs_fixed_priority_sequential": mcnemar_vs_fixed,
            "mcnemar_proposed_vs_random_valid_sequential": mcnemar_vs_random,
            "mcnemar_proposed_vs_single_step_empirical": mcnemar_vs_single_step,
            "holm_bonferroni": holm,
            "effect_size_vs_fixed_priority_sequential": effect_vs_fixed,
            "effect_size_vs_single_step_empirical_ablation": effect_vs_single_step,
            "min_effect_size_required": MIN_EFFECT_SIZE,
        },
        "h4_abstention": {
            "scope_family": "dependency_failure",
            "proposed_abstain_rate_dependency_failure": proposed_dep_abstain_rate,
            "fixed_priority_no_abstention_baseline_abstain_rate_dependency_failure": fixed_dep_abstain_rate,
            "abstain_rate_higher_than_no_abstention_fixed": proposed_dep_abstain_rate > fixed_dep_abstain_rate,
            "proposed_utility_other_families": proposed_other_utility,
            "proposed_no_abstention_variant_utility_other_families": no_abstention_other_utility,
            "no_utility_regression_on_other_families": proposed_other_utility >= no_abstention_other_utility,
        },
    }


def _to_v1_transition(step_transition):
    from src.recovery.schema import Transition as TransitionV1
    return TransitionV1(
        outcome=step_transition.outcome, unsafe_action_taken=step_transition.unsafe_action_taken,
        recovery_latency_seconds=step_transition.recovery_latency_seconds, recovery_cost=step_transition.recovery_cost,
        validation_window_seconds=step_transition.validation_window_seconds, partial=step_transition.partial,
    )


def _fake_v1_scenario(scenario_v2, v1_ctx):
    from src.recovery.schema import RecoveryScenario as RecoveryScenarioV1
    return RecoveryScenarioV1(
        scenario_id=scenario_v2.scenario_id, family=scenario_v2.family, hidden_cause=scenario_v2.hidden_cause,
        decision_context=v1_ctx, seed=scenario_v2.seed, generator_version=scenario_v2.generator_version,
        scenario_taxonomy_version=scenario_v2.scenario_taxonomy_version,
    )


def determine_verdict(test_result: dict, leakage_audit_passed: bool) -> dict:
    reasons = []
    if not leakage_audit_passed:
        return {"verdict": "FAIL", "reasons": ["leakage audit did not pass 100%"]}
    if not test_result["sample_size_requirement_met"]:
        return {"verdict": "INCONCLUSIVE", "reasons": [f"n_test_total={test_result['n_test_total']} < minimum_n_test_required={test_result['minimum_n_test_required']}"]}

    proposed_unsafe = test_result["aggregates"]["proposed_sequential_empirical_recovery"]["unsafe_action_rate"]
    h4_safety = proposed_unsafe <= UNSAFE_RATE_THRESHOLD
    reasons.append(f"H4-SAFETY: unsafe_action_rate={proposed_unsafe:.4f} <= {UNSAFE_RATE_THRESHOLD} -> {'SUPPORTED' if h4_safety else 'NOT SUPPORTED'}")

    effect = test_result["statistics"]["effect_size_vs_fixed_priority_sequential"]
    significant = test_result["statistics"]["holm_bonferroni"].get("vs_fixed_priority_sequential", {}).get("significant", False)
    effect_meets_min = effect >= test_result["statistics"]["min_effect_size_required"]
    h4 = significant and effect_meets_min
    reasons.append(f"H4: effect_size={effect:+.4f} (min {test_result['statistics']['min_effect_size_required']}), holm-significant={significant} -> {'SUPPORTED' if h4 else 'NOT SUPPORTED'}")

    proposed_u = test_result["aggregates"]["proposed_sequential_empirical_recovery"]["recovery_utility_mean"]
    fixed_u = test_result["aggregates"]["baseline_fixed_priority_sequential"]["recovery_utility_mean"]
    h4_utility = proposed_u >= fixed_u
    reasons.append(f"H4-UTILITY: proposed={proposed_u:.4f} vs fixed_priority_sequential={fixed_u:.4f} -> {'SUPPORTED' if h4_utility else 'NOT SUPPORTED'}")

    h4a = test_result["h4_abstention"]
    h4_abstention = h4a["abstain_rate_higher_than_no_abstention_fixed"] and h4a["no_utility_regression_on_other_families"]
    reasons.append(f"H4-ABSTENTION: abstain_rate {h4a['proposed_abstain_rate_dependency_failure']:.4f} vs "
                    f"{h4a['fixed_priority_no_abstention_baseline_abstain_rate_dependency_failure']:.4f}, "
                    f"other-family utility {h4a['proposed_utility_other_families']:.4f} vs "
                    f"{h4a['proposed_no_abstention_variant_utility_other_families']:.4f} -> {'SUPPORTED' if h4_abstention else 'NOT SUPPORTED'}")

    effect_ablation = test_result["statistics"]["effect_size_vs_single_step_empirical_ablation"]
    h4_ablation = effect_ablation >= MIN_EFFECT_SIZE
    reasons.append(f"H4-ABLATION (informational): effect_size_vs_single_step={effect_ablation:+.4f} (min {MIN_EFFECT_SIZE}) -> "
                    f"{'SUPPORTED' if h4_ablation else 'NOT SUPPORTED'} (gate_type=informational_not_pass_fail)")

    if not h4_safety:
        verdict = "FAIL"
        reasons.append("H4-SAFETY failing is treated as FAIL, per the frozen zero-tolerance unsafe-rate threshold.")
    else:
        verdict = "PASS"
        if not h4:
            reasons.append("PASS -- HYPOTHESIS NOT SUPPORTED: the experiment was valid, adequately powered, "
                            "and pre-registered; H4 itself was not confirmed on this evidence. Valid negative result.")

    return {"verdict": verdict, "h4_supported": h4, "h4_safety_supported": h4_safety, "h4_utility_supported": h4_utility,
            "h4_abstention_supported": h4_abstention, "h4_ablation_supported": h4_ablation, "reasons": reasons}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    noise_rate = _noise_rate()
    train = read_jsonl(DATA_DIR / "train.jsonl")
    validation = read_jsonl(DATA_DIR / "validation.jsonl")
    test = read_jsonl(DATA_DIR / "test.jsonl")
    print(f"train={len(train)} validation={len(validation)} test={len(test)} noise_rate={noise_rate}")

    leakage_audit_path = RESULTS_DIR / "leakage_audit.json"
    leakage_audit_passed = False
    if leakage_audit_path.exists():
        la = json.loads(leakage_audit_path.read_text())
        leakage_audit_passed = la["n_passed"] == la["n_checks"]

    print("\n== STEP 9: FROZEN TEST evaluation (run exactly once for the primary record) ==")
    test_result = run_frozen_test(train, test, noise_rate)
    for name, agg in test_result["aggregates"].items():
        print(f"  {name:42s} success={agg['validated_recovery_success_rate']:.3f} unsafe={agg['unsafe_action_rate']:.3f} "
              f"utility={agg['recovery_utility_mean']:.3f} abstain={agg['abstention_rate']:.3f}")

    verdict = determine_verdict(test_result, leakage_audit_passed)
    print("\n== VERDICT ==")
    print(verdict["verdict"])
    for r in verdict["reasons"]:
        print(f"  - {r}")

    output = {
        "milestone": "ACTIVE_PHASE_4_4_SEQUENTIAL_RECOVERY_WITH_ABSTENTION",
        "evidence_type": "CONTROLLED",
        "dataset": {"n_train": len(train), "n_validation": len(validation), "n_test": len(test)},
        "test_result": test_result,
        "leakage_audit_passed": leakage_audit_passed,
        "verdict": verdict,
    }
    out_path = RESULTS_DIR / "results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
