"""Active Phase 4.4 -- STEP 9 (final part): independent-seed sensitivity
analysis, built in from the start (unlike Phase 4.3, where this was added
post-hoc after the primary result).

Draws 4 additional independent TRAIN/TEST sets using scenario.seed ranges
completely disjoint from the frozen protocol's own seed space (a dedicated
high offset block per draw) and from each other, re-runs the full frozen
evaluation (reusing run_frozen_test/determine_verdict from
phase4_4_recovery_evaluate.py so every draw is scored identically to the
primary frozen result), and reports the effect-size range.

Does NOT overwrite experiments/results/phase4_4/results.json (the primary
frozen record) or configs/phase4_4_recovery_protocol.json (still FROZEN).
Reuses the frozen observation_noise_rate=0.05 and min_evidence=2 for every
draw -- neither is re-swept per draw.

Run: PYTHONHASHSEED=0 python benchmarks/phase4_4_seed_sensitivity.py
Writes experiments/results/phase4_4/seed_sensitivity.json.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.phase4_4_recovery_evaluate import MIN_EVIDENCE, determine_verdict, run_frozen_test  # noqa: E402
from src.recovery.actions import ACTION_VOCABULARY_VERSION  # noqa: E402
from src.recovery.environment_v2 import (  # noqa: E402
    GENERATOR_V2_VERSION,
    classify_outcome,
    generate_scenario_v2,
    make_step2_context,
    run_step1,
    run_step2,
)
from src.recovery.schema import ActionId, Split  # noqa: E402
from src.recovery.schema_v2 import ActionSelectionV2, RecoveryEpisodeV2, RecoveryProvenanceV2  # noqa: E402
from src.recovery.splits_v2 import all_families  # noqa: E402
from src.recovery.taxonomy import TAXONOMY_VERSION, safe_candidate_actions  # noqa: E402
from src.recovery.validation import VALIDATION_RULE_VERSION  # noqa: E402

RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_4"
CONFIG_PATH = ROOT / "configs" / "phase4_4_recovery_protocol.json"

N_TRAIN_PER_FAMILY = 400
N_TEST_PER_FAMILY = 175

# Disjoint from splits_v2's own seed space (base 1_000_000_000_000,
# family blocks of 100_000_000) and from phase4_4_noise_sweep.py's sweep
# block -- each draw gets its own multi-trillion offset, far outside any
# range used elsewhere in this phase.
DRAW_OFFSETS = [5_000_000_000_000, 6_000_000_000_000, 7_000_000_000_000, 8_000_000_000_000]
_FAMILY_BLOCK = 100_000_000


def _draw_seeds(family_idx: int, draw_offset: int, is_train: bool) -> list[int]:
    base = draw_offset + family_idx * _FAMILY_BLOCK
    if is_train:
        return [base + i for i in range(N_TRAIN_PER_FAMILY)]
    return [base + N_TRAIN_PER_FAMILY + i for i in range(N_TEST_PER_FAMILY)]


def _prov(episode_id, seed, split):
    from datetime import datetime, timezone
    return RecoveryProvenanceV2(
        generator_version=GENERATOR_V2_VERSION, scenario_taxonomy_version=TAXONOMY_VERSION,
        action_vocabulary_version=ACTION_VOCABULARY_VERSION, validation_rule_version=VALIDATION_RULE_VERSION,
        protocol_version="phase4_4_protocol_v1", split=split, seed=seed, episode_id=episode_id,
        creation_timestamp=datetime.now(timezone.utc),
    )


def _generate_draw(draw_offset: int, noise_rate: float):
    train, test = [], []
    for idx, family in enumerate(all_families()):
        for seed in _draw_seeds(idx, draw_offset, is_train=True):
            scenario = generate_scenario_v2(family, seed)
            safe = safe_candidate_actions(family)
            rng1 = random.Random(f"sensitivity_exploration1|{seed}")
            a1 = safe[rng1.randrange(len(safe))]
            sel1 = ActionSelectionV2(selected_action=a1, policy_id="sensitivity_exploration", policy_version="v1", step=1)
            t1, terminal = run_step1(scenario, a1, noise_rate)
            episode_id = scenario.step1_context.episode_id
            if terminal:
                train.append(RecoveryEpisodeV2(
                    episode_id=episode_id, scenario=scenario, step1_selection=sel1, step1_transition=t1,
                    outcome_class=classify_outcome(t1, True, a1, None, None), provenance=_prov(episode_id, seed, Split.TRAIN),
                ))
                continue
            ctx2 = make_step2_context(scenario, a1, t1.observation)
            rng2 = random.Random(f"sensitivity_exploration2|{seed}")
            a2 = safe[rng2.randrange(len(safe))]
            sel2 = ActionSelectionV2(selected_action=a2, policy_id="sensitivity_exploration", policy_version="v1", step=2)
            t2 = run_step2(scenario, a2)
            train.append(RecoveryEpisodeV2(
                episode_id=episode_id, scenario=scenario, step1_selection=sel1, step1_transition=t1,
                step2_context=ctx2, step2_selection=sel2, step2_transition=t2,
                outcome_class=classify_outcome(t1, False, a1, t2, a2), provenance=_prov(episode_id, seed, Split.TRAIN),
            ))
        for seed in _draw_seeds(idx, draw_offset, is_train=False):
            scenario = generate_scenario_v2(family, seed)
            episode_id = scenario.step1_context.episode_id
            test.append(RecoveryEpisodeV2(episode_id=episode_id, scenario=scenario, provenance=_prov(episode_id, seed, Split.TEST)))
    return train, test


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG_PATH.read_text())
    noise_rate = config["environment"]["observation_signal"]["observation_noise_rate"]

    draws = []
    for draw_offset in DRAW_OFFSETS:
        train, test = _generate_draw(draw_offset, noise_rate)
        test_result = run_frozen_test(train, test, noise_rate)
        verdict = determine_verdict(test_result, leakage_audit_passed=True)

        proposed_sr = test_result["aggregates"]["proposed_sequential_empirical_recovery"]["validated_recovery_success_rate"]
        fixed_sr = test_result["aggregates"]["baseline_fixed_priority_sequential"]["validated_recovery_success_rate"]
        effect = test_result["statistics"]["effect_size_vs_fixed_priority_sequential"]
        p_value = test_result["statistics"]["mcnemar_proposed_vs_fixed_priority_sequential"]["p_value"]
        unsafe = test_result["aggregates"]["proposed_sequential_empirical_recovery"]["unsafe_action_rate"]

        draws.append({
            "draw_offset": draw_offset, "n_train": len(train), "n_test": len(test),
            "proposed_success_rate": proposed_sr, "fixed_priority_sequential_success_rate": fixed_sr,
            "effect_size": effect, "mcnemar_p_value": p_value, "unsafe_action_rate": unsafe,
            "h4_supported": verdict["h4_supported"], "h4_safety_supported": verdict["h4_safety_supported"],
            "h4_utility_supported": verdict["h4_utility_supported"],
        })
        print(f"draw_offset={draw_offset}: proposed={proposed_sr:.4f} fixed={fixed_sr:.4f} "
              f"effect={effect:+.4f} mcnemar_p={p_value:.4f} unsafe={unsafe:.4f} "
              f"H4={'SUPPORTED' if verdict['h4_supported'] else 'NOT SUPPORTED'}")

    effects = [d["effect_size"] for d in draws]
    summary = {
        "n_draws": len(draws), "min_evidence_used": MIN_EVIDENCE, "observation_noise_rate_used": noise_rate,
        "draws": draws,
        "effect_size_min": min(effects), "effect_size_max": max(effects), "effect_size_mean": sum(effects) / len(effects),
        "note": "Supplementary sensitivity analysis, NOT the frozen Phase 4.4 primary TEST result "
                "(experiments/results/phase4_4/results.json is untouched by this script). Each draw uses "
                "scenario.seed ranges disjoint from the frozen protocol's own seed space and from every "
                "other draw. min_evidence and observation_noise_rate are fixed at their frozen values, not "
                "re-swept per draw. Built in from the start of Phase 4.4 (not added post-hoc, unlike 4.3).",
    }
    out_path = RESULTS_DIR / "seed_sensitivity.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\neffect_size range across {len(draws)} independent draws: "
          f"[{summary['effect_size_min']:+.4f}, {summary['effect_size_max']:+.4f}], mean={summary['effect_size_mean']:+.4f}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
