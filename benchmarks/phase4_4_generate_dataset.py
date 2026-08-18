"""Active Phase 4.4 -- STEP 6: generate the controlled 2-step recovery
dataset and freeze TRAIN/VALIDATION/TEST manifests.

TRAIN is resolved via uniform-random exploration over the 2-step action
space (both steps) -- for each TRAIN seed, an exploration policy picks a
safe step-1 action, the environment resolves it; if the episode continues,
the exploration policy also picks a safe step-2 action and the environment
resolves that too. This produces genuine 2-step historical experience for
``SequentialEmpiricalRecoveryPolicy.fit`` (protocol section 8).

VALIDATION and TEST are frozen as UNRESOLVED step-1-only scenario
manifests (same principle as 4.3) -- each candidate policy selects its own
step-1 (and, if applicable, step-2) actions against these scenarios at
evaluation time.

TEST size: independently recomputed floor (Step 5) = 173 per arm; set to
4x that floor = 692, i.e. 175/family x 4 families = 700 (>= 4x692... see
below) -- rounded to N_TEST_PER_FAMILY=175 (700 total, 4.05x the 173 floor).

Run: PYTHONHASHSEED=0 python benchmarks/phase4_4_generate_dataset.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.recovery.actions import ACTION_VOCABULARY_VERSION  # noqa: E402
from src.recovery.environment_v2 import (  # noqa: E402
    GENERATOR_V2_VERSION,
    classify_outcome,
    generate_scenario_v2,
    make_step2_context,
    run_step1,
    run_step2,
)
from src.recovery.io_v2 import file_checksum, write_jsonl  # noqa: E402
from src.recovery.sample_size_v2 import MINIMUM_N_TEST_TOTAL  # noqa: E402
from src.recovery.schema import ActionId, Split  # noqa: E402
from src.recovery.schema_v2 import ActionSelectionV2, RecoveryEpisodeV2, SCHEMA_V2_VERSION  # noqa: E402
from src.recovery.splits_v2 import SPLIT_METHODOLOGY_V2_VERSION, all_families, all_splits, seeds_for  # noqa: E402
from src.recovery.taxonomy import TAXONOMY_VERSION, safe_candidate_actions  # noqa: E402
from src.recovery.validation import VALIDATION_RULE_VERSION  # noqa: E402

OUT_DIR = ROOT / "data" / "controlled_recovery_v2"
CONFIG_PATH = ROOT / "configs" / "phase4_4_recovery_protocol.json"

EXPLORATION_POLICY_ID = "exploration_uniform_random_v2"
EXPLORATION_POLICY_VERSION = "v1"

N_TRAIN_PER_FAMILY = 400
N_VALIDATION_PER_FAMILY = 150
N_TEST_PER_FAMILY = 175  # 700 total = 4.05x the independently recomputed 173 floor (Step 5)

PROTOCOL_VERSION = "phase4_4_protocol_v1"


def _observation_noise_rate() -> float:
    config = json.loads(CONFIG_PATH.read_text())
    rate = config["environment"]["observation_signal"]["observation_noise_rate"]
    status = config["environment"]["observation_signal"]["observation_noise_rate_status"]
    if rate is None or status != "FROZEN_POST_VALIDATION_SWEEP":
        raise RuntimeError("observation_noise_rate is not frozen -- run benchmarks/phase4_4_noise_sweep.py (Step 3) first")
    return rate


def _exploration_action(family, seed: int, step: int, candidates: list[ActionId]) -> ActionId:
    safe = [a for a in candidates if a in set(safe_candidate_actions(family))]
    rng = random.Random(f"exploration_v2|{seed}|step{step}")
    return safe[rng.randrange(len(safe))]


def _stamp_provenance(episode_id: str, seed: int, split: Split):
    from datetime import datetime, timezone
    from src.recovery.schema_v2 import RecoveryProvenanceV2
    return RecoveryProvenanceV2(
        generator_version=GENERATOR_V2_VERSION,
        scenario_taxonomy_version=TAXONOMY_VERSION,
        action_vocabulary_version=ACTION_VOCABULARY_VERSION,
        validation_rule_version=VALIDATION_RULE_VERSION,
        protocol_version=PROTOCOL_VERSION,
        split=split,
        seed=seed,
        episode_id=episode_id,
        creation_timestamp=datetime.now(timezone.utc),
    )


def generate_split(split: Split, noise_rate: float) -> list[RecoveryEpisodeV2]:
    episodes: list[RecoveryEpisodeV2] = []
    counts = {Split.TRAIN: N_TRAIN_PER_FAMILY, Split.VALIDATION: N_VALIDATION_PER_FAMILY, Split.TEST: N_TEST_PER_FAMILY}
    for family in all_families():
        for seed in seeds_for(family, split, N_TRAIN_PER_FAMILY, N_VALIDATION_PER_FAMILY, N_TEST_PER_FAMILY):
            scenario = generate_scenario_v2(family, seed)
            provenance = _stamp_provenance(scenario.step1_context.episode_id, seed, split)

            if split != Split.TRAIN:
                episodes.append(RecoveryEpisodeV2(
                    episode_id=scenario.step1_context.episode_id, scenario=scenario, provenance=provenance,
                ))
                continue

            a1 = _exploration_action(family, seed, 1, scenario.step1_context.candidate_actions)
            sel1 = ActionSelectionV2(
                selected_action=a1, policy_id=EXPLORATION_POLICY_ID, policy_version=EXPLORATION_POLICY_VERSION, step=1,
                rationale="uniform-random exploration (historical corpus generation)",
            )
            t1, terminal = run_step1(scenario, a1, noise_rate)

            if terminal:
                outcome_class = classify_outcome(t1, True, a1, None, None)
                episodes.append(RecoveryEpisodeV2(
                    episode_id=scenario.step1_context.episode_id, scenario=scenario,
                    step1_selection=sel1, step1_transition=t1, outcome_class=outcome_class, provenance=provenance,
                ))
                continue

            ctx2 = make_step2_context(scenario, a1, t1.observation)
            a2 = _exploration_action(family, seed, 2, ctx2.candidate_actions)
            sel2 = ActionSelectionV2(
                selected_action=a2, policy_id=EXPLORATION_POLICY_ID, policy_version=EXPLORATION_POLICY_VERSION, step=2,
                rationale="uniform-random exploration (historical corpus generation)",
            )
            t2 = run_step2(scenario, a2)
            outcome_class = classify_outcome(t1, False, a1, t2, a2)
            episodes.append(RecoveryEpisodeV2(
                episode_id=scenario.step1_context.episode_id, scenario=scenario,
                step1_selection=sel1, step1_transition=t1, step2_context=ctx2,
                step2_selection=sel2, step2_transition=t2, outcome_class=outcome_class, provenance=provenance,
            ))
    return episodes


def main() -> None:
    noise_rate = _observation_noise_rate()
    print(f"using frozen observation_noise_rate={noise_rate}")

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generator_version": GENERATOR_V2_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "action_vocabulary_version": ACTION_VOCABULARY_VERSION,
        "validation_rule_version": VALIDATION_RULE_VERSION,
        "split_methodology_version": SPLIT_METHODOLOGY_V2_VERSION,
        "observation_noise_rate": noise_rate,
        "minimum_n_test_required": MINIMUM_N_TEST_TOTAL,
        "splits": {},
    }

    all_ids = set()
    for split in all_splits():
        episodes = generate_split(split, noise_rate)
        ids = {ep.episode_id for ep in episodes}
        assert len(ids) == len(episodes), f"duplicate episode_id within {split.value} split"
        assert ids.isdisjoint(all_ids), f"episode_id collision across splits at {split.value}"
        all_ids |= ids

        out_path = OUT_DIR / f"{split.value}.jsonl"
        write_jsonl(episodes, out_path)
        manifest["splits"][split.value] = {
            "n_episodes": len(episodes),
            "n_per_family": {
                fam.value: sum(1 for ep in episodes if ep.scenario.family == fam)
                for fam in {ep.scenario.family for ep in episodes}
            },
            "file": out_path.name,
            "sha256": file_checksum(out_path),
            "resolved_step1": split == Split.TRAIN,
        }
        print(f"{split.value}: {len(episodes)} episodes -> {out_path}")

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest -> {manifest_path}")
    print(f"TEST total={manifest['splits']['test']['n_episodes']}, "
          f"minimum_required={MINIMUM_N_TEST_TOTAL}, "
          f"multiplier={manifest['splits']['test']['n_episodes'] / MINIMUM_N_TEST_TOTAL:.2f}x")


if __name__ == "__main__":
    main()
