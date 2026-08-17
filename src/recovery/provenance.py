"""Provenance stamping for Active Phase 4.3 controlled episodes.

Every episode produced anywhere in this package carries this provenance
block from generation through storage, retrieval, policy evaluation, and
the final report -- so a controlled result can never be mistaken for
observational evidence (Phase 4.3 brief section 19).
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.recovery.actions import ACTION_VOCABULARY_VERSION
from src.recovery.environment import GENERATOR_VERSION
from src.recovery.schema import RecoveryProvenance, Split
from src.recovery.taxonomy import TAXONOMY_VERSION
from src.recovery.validation import VALIDATION_RULE_VERSION

PROTOCOL_VERSION = "phase4_3_protocol_v1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def stamp_provenance(episode_id: str, seed: int, split: Split) -> RecoveryProvenance:
    return RecoveryProvenance(
        generator_version=GENERATOR_VERSION,
        scenario_taxonomy_version=TAXONOMY_VERSION,
        action_vocabulary_version=ACTION_VOCABULARY_VERSION,
        validation_rule_version=VALIDATION_RULE_VERSION,
        protocol_version=PROTOCOL_VERSION,
        split=split,
        seed=seed,
        episode_id=episode_id,
        creation_timestamp=utcnow(),
    )
