"""Post-hoc sensitivity analysis for Active Phase 4.3 (NOT part of the
frozen protocol -- configs/phase4_3_recovery_protocol.json's "status":
"FROZEN" is untouched by this script, and this script does not overwrite
experiments/results/phase4_3/results.json).

Purpose: after fixing the hash()-seeding bug in src/recovery/environment.py
(see docs/PHASE4_3_RECOVERY_LEARNING.md, "hash() determinism bug"), report
the DISTRIBUTION of the primary effect size (proposed vs. fixed-priority
baseline) across several independent dataset draws, each using a disjoint
block of scenario.seed values (NOT PYTHONHASHSEED -- genuinely different
generator seeds), to check whether the frozen draw's near-zero effect size
is representative or an outlier.

Each draw regenerates its own train/validation/test split in-memory (same
per-family counts as the frozen protocol: 300/100/180), using a seed offset
far outside the frozen protocol's own seed space (family_idx*10_000_000 +
offset, max ~30_000_580) so there is zero overlap with the frozen dataset's
seeds.

Writes experiments/results/phase4_3/seed_sensitivity.json (a new,
clearly-separate file; does not touch results.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.recovery.environment import generate_scenario, transition  # noqa: E402
from src.recovery.policy import EmpiricalRecoveryPolicy, FixedPriorityPolicy  # noqa: E402
from src.recovery.provenance import stamp_provenance  # noqa: E402
from src.recovery.schema import ActionSelection, RecoveryEpisode, Split  # noqa: E402
from src.recovery.splits import N_TEST_PER_FAMILY, N_TRAIN_PER_FAMILY, N_VALIDATION_PER_FAMILY, all_families  # noqa: E402
from src.recovery.taxonomy import safe_candidate_actions  # noqa: E402

import random  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_3"

# Disjoint from the frozen protocol's own seed space (max seed there is
# ~3*10_000_000 + 300+100+180 = 30_000_580). Each draw gets its own
# 10-family-block-sized offset, far away from that and from each other.
DRAW_OFFSETS = [1_000_000_000, 2_000_000_000, 3_000_000_000, 4_000_000_000, 5_000_000_000]
_FAMILY_BLOCK = 10_000_000


def _draw_seeds(family_idx: int, draw_offset: int, split: Split) -> list[int]:
    base = draw_offset + family_idx * _FAMILY_BLOCK
    if split == Split.TRAIN:
        start, count = 0, N_TRAIN_PER_FAMILY
    elif split == Split.VALIDATION:
        start, count = N_TRAIN_PER_FAMILY, N_VALIDATION_PER_FAMILY
    else:
        start, count = N_TRAIN_PER_FAMILY + N_VALIDATION_PER_FAMILY, N_TEST_PER_FAMILY
    return [base + start + i for i in range(count)]


def _exploration_select(family, seed: int):
    safe = safe_candidate_actions(family)
    rng = random.Random(f"exploration|{seed}")
    return safe[rng.randrange(len(safe))]


def _generate_draw(draw_offset: int):
    train, validation, test = [], [], []
    for idx, family in enumerate(all_families()):
        for seed in _draw_seeds(idx, draw_offset, Split.TRAIN):
            scenario = generate_scenario(family, seed)
            action = _exploration_select(family, seed)
            trans = transition(scenario, action)
            selection = ActionSelection(selected_action=action, policy_id="exploration_sensitivity", policy_version="v1")
            train.append(RecoveryEpisode(
                episode_id=scenario.decision_context.episode_id, scenario=scenario,
                policy_selection=selection, transition=trans,
                provenance=stamp_provenance(scenario.decision_context.episode_id, seed, Split.TRAIN),
            ))
        for seed in _draw_seeds(idx, draw_offset, Split.TEST):
            scenario = generate_scenario(family, seed)
            test.append(scenario)
    return train, test


def _score(policy, scenarios) -> dict:
    n, n_success = 0, 0
    rows = []
    for scenario in scenarios:
        selection = policy.select_action(scenario.decision_context)
        trans = transition(scenario, selection.selected_action)
        n += 1
        success = trans.outcome.value == "success"
        n_success += success
        rows.append(success)
    return {"n": n, "success_rate": n_success / n, "rows": rows}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    draws = []
    for draw_offset in DRAW_OFFSETS:
        train, test_scenarios = _generate_draw(draw_offset)
        proposed = EmpiricalRecoveryPolicy(min_evidence=2).fit(train)  # reuses the frozen-protocol's selected min_evidence
        fixed = FixedPriorityPolicy()
        proposed_result = _score(proposed, test_scenarios)
        fixed_result = _score(fixed, test_scenarios)
        effect = proposed_result["success_rate"] - fixed_result["success_rate"]
        draws.append({
            "draw_offset": draw_offset,
            "n_test": proposed_result["n"],
            "proposed_success_rate": proposed_result["success_rate"],
            "fixed_priority_success_rate": fixed_result["success_rate"],
            "effect_size": effect,
        })
        print(f"draw_offset={draw_offset}: proposed={proposed_result['success_rate']:.4f} "
              f"fixed={fixed_result['success_rate']:.4f} effect={effect:+.4f}")

    effects = [d["effect_size"] for d in draws]
    summary = {
        "n_draws": len(draws),
        "draws": draws,
        "effect_size_min": min(effects),
        "effect_size_max": max(effects),
        "effect_size_mean": sum(effects) / len(effects),
        "note": "Supplementary sensitivity analysis, NOT the frozen Phase 4.3 test result. "
                "Does not overwrite experiments/results/phase4_3/results.json. "
                "Each draw uses independent scenario.seed ranges disjoint from the frozen "
                "protocol's own seed space and from every other draw.",
    }
    out_path = RESULTS_DIR / "seed_sensitivity.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\neffect_size range across {len(draws)} independent draws: "
          f"[{summary['effect_size_min']:+.4f}, {summary['effect_size_max']:+.4f}], "
          f"mean={summary['effect_size_mean']:+.4f}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
