"""FROZEN split methodology for Active Phase 4.3 (brief section 20).

Grouping unit: the RecoveryScenario (1:1 with episode in this
single-decision environment, schema.py). Splits are assigned by disjoint
SEED RANGES per (family, split) fixed before any generation runs -- this is
stronger than post-hoc random assignment because it makes cross-split
duplication structurally impossible to introduce by accident (a seed, and
therefore its scenario_id, belongs to exactly one split by construction),
and it makes the split deterministically reproducible from the protocol
alone (no split manifest randomness to record beyond these ranges).

Per-family counts were sized from the sample-size methodology
(``sample_size.py``): TRAIN=300, VALIDATION=100, TEST=180 per family
(4 families -> 1200 / 400 / 720 total = 2320 episodes).
"""
from __future__ import annotations

from src.recovery.schema import ScenarioFamily, Split

SPLIT_METHODOLOGY_VERSION = "phase4_3_splits_v1"

N_TRAIN_PER_FAMILY = 300
N_VALIDATION_PER_FAMILY = 100
N_TEST_PER_FAMILY = 180

# Disjoint seed blocks per family, each large enough to hold its split with
# generous headroom, and non-overlapping across families and across splits
# within a family. Family index * 10_000_000 keeps families from ever
# colliding even if a per-family block were misconfigured.
_FAMILY_BLOCK = 10_000_000
_SPLIT_OFFSETS = {
    Split.TRAIN: (0, N_TRAIN_PER_FAMILY),
    Split.VALIDATION: (N_TRAIN_PER_FAMILY, N_VALIDATION_PER_FAMILY),
    Split.TEST: (N_TRAIN_PER_FAMILY + N_VALIDATION_PER_FAMILY, N_TEST_PER_FAMILY),
}

_FAMILIES = [
    ScenarioFamily.RESOURCE_EXHAUSTION,
    ScenarioFamily.TRANSIENT_FAILURE,
    ScenarioFamily.CONFIGURATION_FAILURE,
    ScenarioFamily.DEPENDENCY_FAILURE,
]


def seeds_for(family: ScenarioFamily, split: Split) -> list[int]:
    family_idx = _FAMILIES.index(family)
    base = family_idx * _FAMILY_BLOCK
    start_offset, count = _SPLIT_OFFSETS[split]
    return [base + start_offset + i for i in range(count)]


def all_families() -> list[ScenarioFamily]:
    return list(_FAMILIES)


def all_splits() -> list[Split]:
    return [Split.TRAIN, Split.VALIDATION, Split.TEST]
