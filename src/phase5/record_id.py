"""Deterministic, collision-resistant canonical record-ID scheme (Phase 5.2,
resolving Phase 5.1 Open Question 1).

Design goals (see PHASE5_2_DATASET_CONSTRUCTION_REPORT.md for the write-up):

- Deterministic: the same immutable lineage tuple always produces the same
  ID, on any machine, in any process, regardless of filesystem traversal
  order, dict key order, or Python's per-process salted ``hash()``.
- Collision-resistant: built from a cryptographic hash (SHA-256) over an
  explicit, ordered, delimited string -- not from concatenation alone (which
  is not collision-resistant against boundary-shifting: ``"ab"+"c"`` vs
  ``"a"+"bc"``), and not from Python's ``hash()``/``id()`` (both are
  salted/process-local and explicitly disallowed by the Phase 5.1 mandate).
- Immutable-lineage-only: the input tuple is exactly
  ``(dataset_version, source_artifact_hash, source_record_id, episode_id,
  record_type, sequence)`` -- fields that are all fixed at generation time
  from frozen source evidence, never from wall-clock time, random seeds, or
  process/thread identity.

No function in this module reads the clock, imports ``random``, or is
affected by dict/set iteration order (every join is over an already-ordered
tuple of strings).
"""
from __future__ import annotations

import hashlib
from typing import Optional

#: length (hex chars) of the truncated digest used as the public record_id.
#: 24 hex chars = 96 bits -- collision probability is negligible for a
#: dataset of this scale (birthday bound ~2^48 records before 50% collision
#: risk); the full 64-char digest is always retained in
#: ``record_id_full_digest`` for anyone who wants the untruncated value.
RECORD_ID_HEX_LEN = 24

FIELD_SEP = "\x1f"  # ASCII unit separator: never appears in any input field


def _clean(value: Optional[str]) -> str:
    """Normalize a lineage component to a canonical string.

    ``None`` becomes the literal token ``"<NONE>"`` so that a missing
    optional component is still distinguishable from an empty string and
    contributes a fixed, deterministic byte sequence to the digest.
    """
    if value is None:
        return "<NONE>"
    return str(value)


def canonical_lineage_string(
    dataset_version: str,
    source_artifact_hash: str,
    source_record_id: Optional[str],
    episode_id: str,
    record_type: str,
    sequence: int,
) -> str:
    """Build the exact, ordered, delimited string that gets hashed.

    Using an explicit separator character (ASCII unit separator, 0x1F) that
    cannot legally appear in any of these fields prevents the classic
    concatenation ambiguity (``"a" + "bc" == "ab" + "c"``).
    """
    parts = [
        _clean(dataset_version),
        _clean(source_artifact_hash),
        _clean(source_record_id),
        _clean(episode_id),
        _clean(record_type),
        str(int(sequence)),
    ]
    return FIELD_SEP.join(parts)


def compute_record_id(
    dataset_version: str,
    source_artifact_hash: str,
    source_record_id: Optional[str],
    episode_id: str,
    record_type: str,
    sequence: int = 0,
) -> str:
    """Return the deterministic record_id (truncated hex digest).

    ``sequence`` disambiguates multiple records of the same ``record_type``
    that legitimately share the same ``(episode_id, source_record_id)``
    pair (e.g. multiple ``observation`` rows within one episode) -- callers
    must pass an explicit, source-derived sequence index (e.g. the
    checkpoint index already present in the raw evidence), never an
    enumerate()-style index over a non-deterministically-ordered iterable.
    """
    lineage = canonical_lineage_string(
        dataset_version,
        source_artifact_hash,
        source_record_id,
        episode_id,
        record_type,
        sequence,
    )
    digest = hashlib.sha256(lineage.encode("utf-8")).hexdigest()
    return digest[:RECORD_ID_HEX_LEN]


def compute_record_id_full(
    dataset_version: str,
    source_artifact_hash: str,
    source_record_id: Optional[str],
    episode_id: str,
    record_type: str,
    sequence: int = 0,
) -> str:
    """Return the untruncated 64-hex-char SHA-256 digest for the same input."""
    lineage = canonical_lineage_string(
        dataset_version,
        source_artifact_hash,
        source_record_id,
        episode_id,
        record_type,
        sequence,
    )
    return hashlib.sha256(lineage.encode("utf-8")).hexdigest()


def sha256_of_file(path: str) -> str:
    """Deterministic SHA-256 of a file's exact bytes (source_artifact_hash)."""
    import pathlib

    data = pathlib.Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()
