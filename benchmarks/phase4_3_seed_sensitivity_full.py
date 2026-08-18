"""Extends phase4_3_seed_sensitivity.py with the full statistical battery
(McNemar p-value, effect size, H3/H3-safety/H3-utility verdicts) per
independent dataset draw, reusing run_frozen_test/determine_verdict from
phase4_3_recovery_evaluate.py so every draw is scored identically to the
frozen protocol's own evaluation.

NOT part of the frozen protocol -- configs/phase4_3_recovery_protocol.json's
"status": "FROZEN" is untouched, and this script does not overwrite
experiments/results/phase4_3/results.json (it writes seed_sensitivity.json,
same file phase4_3_seed_sensitivity.py writes, with a richer per-draw
payload).

Each draw uses a seed offset far outside the frozen protocol's own seed
space (family_idx*10_000_000 + draw_offset), so there is zero overlap with
the frozen dataset's seeds. Reuses the frozen-protocol's selected
min_evidence=2 for every draw (this script does not re-sweep/re-select
min_evidence per draw).

Run: python benchmarks/phase4_3_seed_sensitivity_full.py
Writes experiments/results/phase4_3/seed_sensitivity.json.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.phase4_3_recovery_evaluate import determine_verdict, run_frozen_test  # noqa: E402
from src.recovery.environment import generate_scenario, transition  # noqa: E402
from src.recovery.provenance import stamp_provenance  # noqa: E402
from src.recovery.schema import ActionSelection, RecoveryEpisode, Split  # noqa: E402
from src.recovery.splits import N_TEST_PER_FAMILY, N_TRAIN_PER_FAMILY, N_VALIDATION_PER_FAMILY, all_families  # noqa: E402
from src.recovery.taxonomy import safe_candidate_actions  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_3"
FROZEN_MIN_EVIDENCE = 2  # reuses the frozen protocol's VALIDATION-selected value; not re-swept here

DRAW_OFFSETS = [1_000_000_000, 2_000_000_000, 3_000_000_000, 4_000_000_000, 5_000_000_000]
_FAMILY_BLOCK = 10_000_000


def _draw_seeds(family_idx: int, draw_offset: int, split: Split) -> list[int]:
    base = draw_offset + family_idx * _FAMILY_BLOCK
    if split == Split.TRAIN:
        start, count = 0, N_TRAIN_PER_FAMILY
    else:
        start, count = N_TRAIN_PER_FAMILY, N_TEST_PER_FAMILY
    return [base + start + i for i in range(count)]


def _exploration_select(family, seed: int):
    safe = safe_candidate_actions(family)
    rng = random.Random(f"exploration|{seed}")
    action = safe[rng.randrange(len(safe))]
    return ActionSelection(selected_action=action, policy_id="exploration_sensitivity", policy_version="v1")


def _generate_draw(draw_offset: int):
    train, test = [], []
    for idx, family in enumerate(all_families()):
        for seed in _draw_seeds(idx, draw_offset, Split.TRAIN):
            scenario = generate_scenario(family, seed)
            selection = _exploration_select(family, seed)
            trans = transition(scenario, selection.selected_action)
            train.append(RecoveryEpisode(
                episode_id=scenario.decision_context.episode_id, scenario=scenario,
                policy_selection=selection, transition=trans,
                provenance=stamp_provenance(scenario.decision_context.episode_id, seed, Split.TRAIN),
            ))
        for seed in _draw_seeds(idx, draw_offset, Split.TEST):
            scenario = generate_scenario(family, seed)
            test.append(RecoveryEpisode(
                episode_id=scenario.decision_context.episode_id, scenario=scenario,
                policy_selection=None, transition=None,
                provenance=stamp_provenance(scenario.decision_context.episode_id, seed, Split.TEST),
            ))
    return train, test


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    draws = []
    for draw_offset in DRAW_OFFSETS:
        train, test = _generate_draw(draw_offset)
        test_result = run_frozen_test(train, test, FROZEN_MIN_EVIDENCE)
        verdict = determine_verdict(test_result, leakage_audit_passed=True)

        proposed_sr = test_result["aggregates"]["proposed_empirical_recovery"]["validated_recovery_success_rate"]
        fixed_sr = test_result["aggregates"]["baseline_fixed_priority"]["validated_recovery_success_rate"]
        effect = test_result["statistics"]["effect_size_vs_fixed_priority"]
        p_value = test_result["statistics"]["mcnemar_proposed_vs_fixed_priority"]["p_value"]

        draw_record = {
            "draw_offset": draw_offset,
            "n_train": len(train),
            "n_test": len(test),
            "proposed_success_rate": proposed_sr,
            "fixed_priority_success_rate": fixed_sr,
            "effect_size": effect,
            "mcnemar_p_value": p_value,
            "h3_supported": verdict["h3_supported"],
            "h3_safety_supported": verdict["h3_safety_supported"],
            "h3_utility_supported": verdict["h3_utility_supported"],
        }
        draws.append(draw_record)
        print(f"draw_offset={draw_offset}: proposed={proposed_sr:.4f} fixed={fixed_sr:.4f} "
              f"effect={effect:+.4f} mcnemar_p={p_value:.4f} "
              f"H3={'SUPPORTED' if verdict['h3_supported'] else 'NOT SUPPORTED'} "
              f"H3-safety={'SUPPORTED' if verdict['h3_safety_supported'] else 'NOT SUPPORTED'} "
              f"H3-utility={'SUPPORTED' if verdict['h3_utility_supported'] else 'NOT SUPPORTED'}")

    effects = [d["effect_size"] for d in draws]
    summary = {
        "n_draws": len(draws),
        "min_evidence_used": FROZEN_MIN_EVIDENCE,
        "draws": draws,
        "effect_size_min": min(effects),
        "effect_size_max": max(effects),
        "effect_size_mean": sum(effects) / len(effects),
        "note": "Supplementary sensitivity analysis, NOT the frozen Phase 4.3 test result. "
                "Does not overwrite experiments/results/phase4_3/results.json's primary "
                "test_result block. Each draw uses independent scenario.seed ranges disjoint "
                "from the frozen protocol's own seed space and from every other draw; "
                "min_evidence is fixed at the frozen protocol's validation-selected value "
                "(2), not re-swept per draw.",
    }
    out_path = RESULTS_DIR / "seed_sensitivity.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\neffect_size range across {len(draws)} independent draws: "
          f"[{summary['effect_size_min']:+.4f}, {summary['effect_size_max']:+.4f}], "
          f"mean={summary['effect_size_mean']:+.4f}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
