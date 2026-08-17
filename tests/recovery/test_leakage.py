from __future__ import annotations

import inspect

from src.recovery.environment import generate_scenario
from src.recovery.io import read_jsonl
from src.recovery.policy import EmpiricalRecoveryPolicy, FixedPriorityPolicy, RandomValidPolicy
from src.recovery.schema import DecisionContext, ScenarioFamily, Split
from src.recovery.splits import all_families, all_splits, seeds_for
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "controlled_recovery"


def test_decision_context_schema_has_no_ground_truth_fields():
    fields = set(DecisionContext.model_fields.keys())
    forbidden = {"hidden_cause", "outcome", "transition", "validation_result", "oracle_best_action"}
    assert fields.isdisjoint(forbidden)


def test_policy_select_action_signatures_take_only_decision_context():
    """Structural check: every policy's select_action accepts exactly a
    DecisionContext (plus self) -- no back-door parameter for ground truth."""
    for cls in (FixedPriorityPolicy, RandomValidPolicy, EmpiricalRecoveryPolicy):
        sig = inspect.signature(cls.select_action)
        params = [p for p in sig.parameters if p != "self"]
        assert params == ["ctx"], f"{cls.__name__}.select_action has unexpected params: {params}"


def test_seed_ranges_disjoint_across_splits_and_families():
    seen: dict[int, tuple] = {}
    for family in all_families():
        for split in all_splits():
            for seed in seeds_for(family, split):
                assert seed not in seen, f"seed {seed} reused: {seen[seed]} vs {(family, split)}"
                seen[seed] = (family, split)


def test_generated_split_files_have_no_id_overlap():
    if not DATA_DIR.exists():
        return  # dataset not generated in this environment; generation is tested separately
    ids_by_split = {}
    for split in all_splits():
        path = DATA_DIR / f"{split.value}.jsonl"
        if not path.exists():
            return
        episodes = read_jsonl(path)
        ids_by_split[split.value] = {ep.episode_id for ep in episodes}
    train, val, test = ids_by_split["train"], ids_by_split["validation"], ids_by_split["test"]
    assert train.isdisjoint(val)
    assert train.isdisjoint(test)
    assert val.isdisjoint(test)


def test_validation_and_test_episodes_are_unresolved_at_generation_time():
    """VALIDATION/TEST are frozen as scenario-only manifests -- no
    pre-baked action/outcome that could let a policy config be silently
    tuned against ground truth via the file itself."""
    if not DATA_DIR.exists():
        return
    for split_name in ("validation", "test"):
        path = DATA_DIR / f"{split_name}.jsonl"
        if not path.exists():
            return
        episodes = read_jsonl(path)
        assert episodes, f"{split_name} split is empty"
        assert all(ep.policy_selection is None and ep.transition is None for ep in episodes)


def test_train_episodes_are_resolved():
    path = DATA_DIR / "train.jsonl"
    if not path.exists():
        return
    episodes = read_jsonl(path)
    assert episodes
    assert all(ep.policy_selection is not None and ep.transition is not None for ep in episodes)


def test_all_provenance_source_type_controlled():
    if not DATA_DIR.exists():
        return
    for split in all_splits():
        path = DATA_DIR / f"{split.value}.jsonl"
        if not path.exists():
            return
        for ep in read_jsonl(path):
            assert ep.provenance.source_type.value == "controlled"


def test_non_vacuous_contamination_check():
    """A real leakage-audit test must be capable of FAILING when
    contamination is deliberately introduced -- otherwise it is vacuous
    (brief section 31, item 10). Here we assert the schema itself rejects
    a hand-crafted contamination attempt, proving the guard is load-bearing,
    not decorative."""
    from pydantic import ValidationError
    scenario = generate_scenario(ScenarioFamily.RESOURCE_EXHAUSTION, seed=1)
    payload = scenario.decision_context.model_dump()
    payload["hidden_cause"] = scenario.hidden_cause  # attempt contamination
    try:
        DecisionContext(**payload)
        assert False, "contamination attempt should have been rejected by extra='forbid'"
    except ValidationError:
        pass
