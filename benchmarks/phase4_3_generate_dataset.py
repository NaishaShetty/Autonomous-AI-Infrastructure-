"""Active Phase 4.3 -- STEP 7/9/10: generate the controlled recovery
dataset and freeze train/validation/test manifests.

TRAIN is generated as a resolved historical corpus: for each TRAIN seed, a
dedicated EXPLORATION policy (uniform-random over safe candidate actions --
NOT the RandomValidPolicy baseline used at evaluation time, deliberately a
separate rng namespace, though algorithmically identical) selects an action
and the environment resolves the outcome, exactly as a logged historical
FailureExperience corpus would look. This is what
``src.recovery.policy.EmpiricalRecoveryPolicy.fit`` learns from.

VALIDATION and TEST are frozen as UNRESOLVED scenario manifests (decision
context only, no action/outcome baked in) -- each candidate policy
configuration selects its own action against these scenarios at evaluation
time, and the environment resolves the outcome then. This is what makes
VALIDATION usable for a real hyperparameter sweep and TEST usable for a
one-shot frozen evaluation of arbitrary candidate policies, rather than
being tied to one specific policy's choices at generation time.

Run: python benchmarks/phase4_3_generate_dataset.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from src.recovery.actions import ACTION_VOCABULARY_VERSION
from src.recovery.environment import GENERATOR_VERSION, generate_scenario, transition
from src.recovery.io import file_checksum, write_jsonl
from src.recovery.provenance import PROTOCOL_VERSION, stamp_provenance
from src.recovery.schema import ActionSelection, RecoveryEpisode, Split
from src.recovery.splits import all_families, all_splits, seeds_for
from src.recovery.taxonomy import TAXONOMY_VERSION, safe_candidate_actions
from src.recovery.validation import VALIDATION_RULE_VERSION

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "controlled_recovery"

EXPLORATION_POLICY_ID = "exploration_uniform_random"
EXPLORATION_POLICY_VERSION = "v1"


def _exploration_select(family, ctx, seed: int):
    safe = safe_candidate_actions(family)
    rng = random.Random(f"exploration|{seed}")
    action = safe[rng.randrange(len(safe))]
    return ActionSelection(
        selected_action=action, policy_id=EXPLORATION_POLICY_ID, policy_version=EXPLORATION_POLICY_VERSION,
        rationale="uniform-random exploration over safe candidate actions (historical corpus generation)",
    )


def generate_split(split: Split) -> list[RecoveryEpisode]:
    episodes: list[RecoveryEpisode] = []
    for family in all_families():
        for seed in seeds_for(family, split):
            scenario = generate_scenario(family, seed)
            provenance = stamp_provenance(scenario.decision_context.episode_id, seed, split)

            if split == Split.TRAIN:
                selection = _exploration_select(family, scenario.decision_context, seed)
                trans = transition(scenario, selection.selected_action)
                episodes.append(RecoveryEpisode(
                    episode_id=scenario.decision_context.episode_id,
                    scenario=scenario, policy_selection=selection, transition=trans,
                    provenance=provenance,
                ))
            else:
                episodes.append(RecoveryEpisode(
                    episode_id=scenario.decision_context.episode_id,
                    scenario=scenario, policy_selection=None, transition=None,
                    provenance=provenance,
                ))
    return episodes


def main() -> None:
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "generator_version": GENERATOR_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "action_vocabulary_version": ACTION_VOCABULARY_VERSION,
        "validation_rule_version": VALIDATION_RULE_VERSION,
        "splits": {},
    }

    all_ids = set()
    for split in all_splits():
        episodes = generate_split(split)

        ids = {ep.episode_id for ep in episodes}
        assert len(ids) == len(episodes), f"duplicate episode_id within {split.value} split"
        assert ids.isdisjoint(all_ids), f"episode_id collision across splits at {split.value} -- split isolation violated"
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
            "resolved": split == Split.TRAIN,
        }
        print(f"{split.value}: {len(episodes)} episodes -> {out_path}")

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest -> {manifest_path}")


if __name__ == "__main__":
    main()
