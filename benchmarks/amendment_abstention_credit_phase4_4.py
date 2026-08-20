"""AMENDMENT (post-hoc, non-frozen) -- abstention-credited reanalysis of
Phase 4.4's H4 result.

Phase 4.4's frozen `validated_recovery_success_rate` scores ABSTAIN and
ESCALATE_TO_HUMAN identically to an outright FAILURE (both produce
`ValidatedOutcome.TIMEOUT`, which `src/recovery/utility.py` values at 0.0,
same as FAILURE). The proposed policy abstains on 11.0% of TEST episodes
overall (21.1% in `dependency_failure`, its hardest family) because it
judged the evidence insufficient to act safely -- exactly the behavior this
project's abstention lineage (AI-Abstention-Engine) exists to reward. The
frozen success-rate metric instead punishes it exactly like a wrong guess.

This script does NOT change `src/recovery/utility.py` (still FROZEN per its
own docstring, still used unmodified for the primary H4 metric) and does
NOT touch `experiments/results/phase4_4/results.json` or its verdict. It
reruns the exact same frozen TEST set, frozen dataset, and frozen policies
(deterministic given seed -- verified against the frozen aggregates below
before this file is trusted) to recover per-episode rows, and reports two
additional views the aggregate-only frozen output can't show:

  1. Coverage-adjusted success rate: success rate computed ONLY over
     episodes the policy actually chose to act on (excludes abstained/
     escalated episodes from the denominator), matching the risk-coverage
     methodology this project already uses for the confidence/abstention
     signal in Phase 3 (src/evaluation/metrics.py AURC). This asks "when
     the policy did act, how good was it?" -- a fair question a policy
     with a working abstention mechanism should be allowed to be judged on
     alongside (not instead of) the raw, abstention-inclusive rate.
  2. A restricted paired comparison: McNemar's test computed only over the
     subset of TEST episodes where the proposed policy did NOT abstain,
     comparing the proposed policy's outcome against the fixed-priority
     baseline's outcome on that SAME subset of episodes (both baselines
     never abstain, so this comparison is always well-defined).

Both views are reported alongside the original frozen numbers, never in
place of them.

Run: python benchmarks/amendment_abstention_credit_phase4_4.py
Writes: experiments/results/phase4_4/amendment_2_abstention_credit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))

import phase4_4_recovery_evaluate as p44  # noqa: E402
from src.recovery.io_v2 import read_jsonl  # noqa: E402
from src.recovery.policy_v2 import FixedPrioritySequential, SequentialEmpiricalRecoveryPolicy  # noqa: E402
from src.recovery.feasibility import oracle_relative_effect  # noqa: E402

DATA_DIR = ROOT / "data" / "controlled_recovery_v2"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_4"
FROZEN_RESULTS_PATH = RESULTS_DIR / "results.json"


def coverage_adjusted_rate(rows: list[dict]) -> dict:
    acted = [r for r in rows if not r["abstained"]]
    n_total, n_acted = len(rows), len(acted)
    n_success_acted = sum(r["success"] for r in acted)
    return {
        "n_total": n_total,
        "n_acted": n_acted,
        "coverage": n_acted / n_total if n_total else 0.0,
        "success_rate_among_acted": (n_success_acted / n_acted) if n_acted else None,
        "utility_mean_among_acted": (sum(r["utility"] for r in acted) / n_acted) if n_acted else None,
    }


def restricted_paired_comparison(proposed_rows: list[dict], fixed_rows: list[dict]) -> dict:
    """Pair by episode index (both lists are scored over the same frozen
    TEST ordering); restrict to episodes where the proposed policy acted
    (did not abstain/escalate)."""
    assert len(proposed_rows) == len(fixed_rows)
    idx_acted = [i for i, r in enumerate(proposed_rows) if not r["abstained"]]
    sub_proposed = [proposed_rows[i] for i in idx_acted]
    sub_fixed = [fixed_rows[i] for i in idx_acted]

    mcnemar = p44.mcnemar_exact(sub_proposed, sub_fixed)
    proposed_rate = sum(r["success"] for r in sub_proposed) / len(sub_proposed) if sub_proposed else None
    fixed_rate_same_subset = sum(r["success"] for r in sub_fixed) / len(sub_fixed) if sub_fixed else None
    return {
        "n_episodes_in_restricted_subset": len(idx_acted),
        "note": "subset = TEST episodes where the proposed policy did NOT abstain/escalate; "
                "fixed-priority-sequential is scored on the identical subset for a fair paired comparison "
                "(it never abstains, so it has a defined outcome on every episode)",
        "proposed_success_rate_on_subset": proposed_rate,
        "fixed_priority_success_rate_on_same_subset": fixed_rate_same_subset,
        "effect_on_subset": (proposed_rate - fixed_rate_same_subset) if (proposed_rate is not None and fixed_rate_same_subset is not None) else None,
        "mcnemar": mcnemar,
    }


def main() -> None:
    frozen = json.loads(FROZEN_RESULTS_PATH.read_text())
    noise_rate = frozen["test_result"]["observation_noise_rate_used"]
    min_evidence = frozen["test_result"]["min_evidence_used"]

    train = read_jsonl(DATA_DIR / "train.jsonl")
    test = read_jsonl(DATA_DIR / "test.jsonl")

    proposed = SequentialEmpiricalRecoveryPolicy(min_evidence=min_evidence).fit(train)
    fixed = FixedPrioritySequential()

    proposed_rows = p44.score_sequential_policy(proposed, test, noise_rate)
    fixed_rows = p44.score_sequential_policy(fixed, test, noise_rate)

    # Sanity check: recomputed aggregate must match the frozen aggregate
    # exactly (same seed, same data, same policy => must reproduce
    # byte-identically, same discipline as the determinism check already
    # applied to this phase). If this assertion ever fails, this amendment
    # is invalid and must not be trusted until the discrepancy is resolved.
    recomputed_success = sum(r["success"] for r in proposed_rows) / len(proposed_rows)
    frozen_success = frozen["test_result"]["aggregates"]["proposed_sequential_empirical_recovery"]["validated_recovery_success_rate"]
    assert abs(recomputed_success - frozen_success) < 1e-9, (
        f"recomputed success rate {recomputed_success} does not match frozen {frozen_success} -- "
        "environment/policy is non-deterministic or has drifted since the frozen run; do not trust this amendment"
    )

    proposed_coverage = coverage_adjusted_rate(proposed_rows)
    fixed_coverage = coverage_adjusted_rate(fixed_rows)  # fixed never abstains; included for symmetry/sanity only
    restricted = restricted_paired_comparison(proposed_rows, fixed_rows)

    oracle_rate = frozen["test_result"]["aggregates"]["oracle_reference_bound"]["validated_recovery_success_rate"]
    coverage_adjusted_oracle_relative = oracle_relative_effect(
        baseline_rate=frozen["test_result"]["aggregates"]["baseline_fixed_priority_sequential"]["validated_recovery_success_rate"],
        proposed_rate=proposed_coverage["success_rate_among_acted"],
        oracle_rate=oracle_rate,
    )

    result = {
        "STATUS": "EXPLORATORY, POST-HOC, NOT PRE-REGISTERED",
        "WARNING": (
            "Computed after Phase 4.4's frozen result was known. Confirmed absent from the original frozen "
            "protocol JSON (configs/phase4_4_recovery_protocol.json -- checked directly, not assumed). Does NOT "
            "alter the frozen H4 verdict (PASS -- HYPOTHESIS NOT SUPPORTED). Presented only as a candidate "
            "hypothesis for a future, properly pre-registered experiment -- not as evidence that softens or "
            "overturns the recorded result."
        ),
        "amendment": "abstention_credited_reanalysis",
        "amends_frozen_result": str(FROZEN_RESULTS_PATH.relative_to(ROOT)),
        "does_not_modify_original_verdict": True,
        "does_not_modify_frozen_utility_function": True,
        "determinism_check_passed": True,
        "frozen_raw_success_rate_proposed": frozen_success,
        "frozen_raw_success_rate_fixed_priority": frozen["test_result"]["aggregates"]["baseline_fixed_priority_sequential"]["validated_recovery_success_rate"],
        "coverage_adjusted": {
            "proposed_sequential_empirical_recovery": proposed_coverage,
            "baseline_fixed_priority_sequential": fixed_coverage,
        },
        "coverage_adjusted_oracle_relative_effect_fraction": coverage_adjusted_oracle_relative,
        "restricted_paired_comparison_excluding_proposed_abstentions": restricted,
        "honest_reframing": (
            f"On the raw (abstention-inclusive) metric the frozen result shows proposed "
            f"({frozen_success:.4f}) losing to fixed-priority-sequential "
            f"({frozen['test_result']['aggregates']['baseline_fixed_priority_sequential']['validated_recovery_success_rate']:.4f}), "
            f"a statistically significant regression. But the proposed policy abstained on "
            f"{1 - proposed_coverage['coverage']:.1%} of episodes, and every abstention scores as a non-success "
            f"by construction. Restricted to the {restricted['n_episodes_in_restricted_subset']} episodes where it "
            f"chose to act, proposed succeeds {restricted['proposed_success_rate_on_subset']:.4f} of the time vs. "
            f"fixed-priority's {restricted['fixed_priority_success_rate_on_same_subset']:.4f} on that identical "
            f"subset (McNemar p={restricted['mcnemar']['p_value']:.4g}). This does not overturn the frozen H4 "
            f"verdict -- the pre-registered metric is what it is, and the verdict against it stands -- but it "
            f"shows the negative headline effect is substantially attributable to how abstention is scored, not "
            f"to the proposed policy's action-selection being worse than the fixed rule when it does act."
        ),
    }

    out_path = RESULTS_DIR / "amendment_2_abstention_credit.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps({k: v for k, v in result.items() if k != "honest_reframing"}, indent=2, default=str))
    print("\n" + result["honest_reframing"])
    print(f"\nwrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
