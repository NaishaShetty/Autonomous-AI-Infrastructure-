"""FROZEN split methodology for Active Phase 4.4.

Grouping unit: the RecoveryScenarioV2 (1:1 with episode). Splits are
assigned by disjoint SEED RANGES per (family, split), same methodology as
Phase 4.3's ``src.recovery.splits`` (untouched, frozen artifact) -- disjoint
seed ranges make cross-split duplication structurally impossible rather
than merely checked post-hoc.

Seed space is offset by ``_PHASE4_4_BASE`` (10^12), far outside Phase
4.3's own seed space (max ~3*10^7 across its 4 families' TRAIN+VALIDATION+
TEST blocks -- see src/recovery/splits.py), so there is zero risk of
accidental collision between the two phases' generated datasets even
though they are never compared directly.

Per-family counts are set in ``benchmarks/phase4_4_generate_dataset.py``
after Step 5's independently recomputed sample-size floor (this module
only defines the seed-range mechanics, not the counts).
"""
from __future__ import annotations

from src.recovery.schema import ScenarioFamily, Split

SPLIT_METHODOLOGY_V2_VERSION = "phase4_4_splits_v1"

_PHASE4_4_BASE = 1_000_000_000_000
_FAMILY_BLOCK = 100_000_000

_FAMILIES = [
    ScenarioFamily.RESOURCE_EXHAUSTION,
    ScenarioFamily.TRANSIENT_FAILURE,
    ScenarioFamily.CONFIGURATION_FAILURE,
    ScenarioFamily.DEPENDENCY_FAILURE,
]


def seeds_for(family: ScenarioFamily, split: Split, n_train: int, n_validation: int, n_test: int) -> list[int]:
    family_idx = _FAMILIES.index(family)
    base = _PHASE4_4_BASE + family_idx * _FAMILY_BLOCK
    offsets = {
        Split.TRAIN: (0, n_train),
        Split.VALIDATION: (n_train, n_validation),
        Split.TEST: (n_train + n_validation, n_test),
    }
    start_offset, count = offsets[split]
    return [base + start_offset + i for i in range(count)]


def all_families() -> list[ScenarioFamily]:
    return list(_FAMILIES)


def all_splits() -> list[Split]:
    return [Split.TRAIN, Split.VALIDATION, Split.TEST]
