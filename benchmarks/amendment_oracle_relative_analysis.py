"""AMENDMENT (post-hoc, non-frozen) -- oracle-relative reanalysis of Phase
4.3 and Phase 4.4's headline effect sizes.

Written after review found that both phases pre-registered a minimum
meaningful effect of 0.15 without checking it against the headroom actually
available between each phase's strongest baseline and its own oracle
reference bound (see src/recovery/feasibility.py for the full rationale).
This script does NOT rerun any policy, does NOT touch either phase's
frozen `results.json`, and does NOT change either phase's PASS / HYPOTHESIS
NOT SUPPORTED verdict -- those verdicts were reached correctly against
their own pre-registration and stand as recorded. It ADDS a second,
headroom-normalized view of the same frozen numbers, and a retroactive
feasibility check, as a deviations-log amendment.

Run: python benchmarks/amendment_oracle_relative_analysis.py
Writes:
  experiments/results/phase4_3/amendment_1_oracle_relative_effect.json
  experiments/results/phase4_4/amendment_1_oracle_relative_effect.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.recovery.feasibility import check_feasibility, oracle_relative_effect  # noqa: E402


def analyze(phase_dir: str, proposed_key: str, baseline_key: str, required_effect: float) -> dict:
    results_path = ROOT / "experiments" / "results" / phase_dir / "results.json"
    data = json.loads(results_path.read_text())
    agg = data["test_result"]["aggregates"]

    proposed_rate = agg[proposed_key]["validated_recovery_success_rate"]
    baseline_rate = agg[baseline_key]["validated_recovery_success_rate"]
    oracle_rate = agg["oracle_reference_bound"]["validated_recovery_success_rate"]

    feasibility = check_feasibility(baseline_rate=baseline_rate, oracle_rate=oracle_rate, required_min_effect=required_effect)
    frac_captured = oracle_relative_effect(baseline_rate=baseline_rate, proposed_rate=proposed_rate, oracle_rate=oracle_rate)

    raw_effect = proposed_rate - baseline_rate
    original_verdict = data["verdict"]

    return {
        "STATUS": "EXPLORATORY, POST-HOC, NOT PRE-REGISTERED",
        "WARNING": (
            "Computed after the frozen result was known. Confirmed absent from the original frozen protocol JSON "
            "(configs/phase4_3_recovery_protocol.json, configs/phase4_4_recovery_protocol.json -- checked directly, "
            "not assumed). Does NOT alter the frozen verdict (PASS -- HYPOTHESIS NOT SUPPORTED). Presented only as "
            "a candidate hypothesis for a future, properly pre-registered experiment -- not as evidence that "
            "softens or overturns the recorded result."
        ),
        "amendment": "oracle_relative_effect_size_reanalysis",
        "amends_frozen_result": str(results_path.relative_to(ROOT)),
        "does_not_modify_original_verdict": True,
        "original_verdict_recorded": original_verdict.get("verdict") if isinstance(original_verdict, dict) else original_verdict,
        "baseline_policy": baseline_key,
        "proposed_policy": proposed_key,
        "baseline_rate": baseline_rate,
        "proposed_rate": proposed_rate,
        "oracle_rate": oracle_rate,
        "raw_effect_vs_baseline": raw_effect,
        "required_min_effect_as_frozen": required_effect,
        "feasibility_check": {
            "headroom_available": feasibility.headroom,
            "headroom_ratio_to_required_effect": feasibility.headroom_ratio,
            "was_required_effect_reachable_by_any_policy": feasibility.feasible,
            "summary": feasibility.summary(),
        },
        "oracle_relative_effect": {
            "fraction_of_headroom_captured_by_proposed": frac_captured,
            "interpretation": (
                "fraction of the reachable improvement (oracle - baseline) that the proposed policy actually "
                "captured; None if oracle == baseline (no headroom existed at all)"
            ),
        },
        "honest_reframing": (
            f"The frozen verdict correctly reports the proposed policy did not clear the pre-registered "
            f"{required_effect:.2f} absolute-point bar. But only {feasibility.headroom:.4f} points of headroom "
            f"existed between baseline ({baseline_rate:.4f}) and oracle ({oracle_rate:.4f}) in the first place -- "
            f"{feasibility.headroom_ratio:.1%} of what was required. No policy, including a perfect one, could "
            f"have passed this gate. The proposed policy captured "
            f"{'N/A' if frac_captured is None else f'{frac_captured:.1%}'} of the headroom that did exist."
        ),
    }


def main() -> None:
    phase_3 = analyze(
        phase_dir="phase4_3",
        proposed_key="proposed_empirical_recovery",
        baseline_key="baseline_fixed_priority",
        required_effect=0.15,
    )
    phase_4 = analyze(
        phase_dir="phase4_4",
        proposed_key="proposed_sequential_empirical_recovery",
        baseline_key="baseline_fixed_priority_sequential",
        required_effect=0.15,
    )

    for phase_dir, result in (("phase4_3", phase_3), ("phase4_4", phase_4)):
        out_path = ROOT / "experiments" / "results" / phase_dir / "amendment_1_oracle_relative_effect.json"
        out_path.write_text(json.dumps(result, indent=2))
        print(f"=== {phase_dir} ===")
        print(result["feasibility_check"]["summary"])
        frac = result["oracle_relative_effect"]["fraction_of_headroom_captured_by_proposed"]
        print(f"  fraction of headroom captured by proposed policy: {frac if frac is None else f'{frac:.1%}'}")
        print(f"  wrote {out_path.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
