"""Shared helpers for source adapters."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

# Several source datasets have no usable wall-clock timestamp (AgentRx's
# "timestamp": "MISSING", the synthetic Phase 4.0 episodes' logical `step`
# integer). Rather than fabricate a fake-but-plausible-looking real
# timestamp, every such case is anchored to this fixed, documented epoch,
# offset deterministically -- so temporal *ordering* within one source is
# still meaningful (and testable) without pretending to be wall-clock time.
SYNTHETIC_TIME_EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)


def deterministic_offset_seconds(key: str, modulus_seconds: int = 365 * 24 * 3600) -> int:
    """Deterministic, reproducible pseudo-time offset derived from a
    stable string key (never random) -- used only for sources with no real
    timestamp, so record ordering is at least internally consistent and
    ingestion is reproducible run to run."""
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:8], 16) % modulus_seconds


def synthetic_timestamp(key: str) -> datetime:
    return SYNTHETIC_TIME_EPOCH + timedelta(seconds=deterministic_offset_seconds(key))
