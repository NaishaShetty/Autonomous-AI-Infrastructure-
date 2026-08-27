"""Deterministic SHA-256 identifiers. Never uses Python's salted hash()."""
from __future__ import annotations

import hashlib

from .constants import FIELD_SEP


def compute_instance_id(task_id: str, record_id: str, sub_index: int = 0) -> str:
    """sha256(task_id + 0x1F + record_id + 0x1F + sub_index) as specified."""
    payload = FIELD_SEP.join([str(task_id), str(record_id), str(int(sub_index))])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    from pathlib import Path

    return sha256_bytes(Path(path).read_bytes())


def sha256_canonical_json(obj: object) -> str:
    """Hash of canonical JSON (sorted keys, UTF-8, trailing newline)."""
    import json

    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
    if not text.endswith("\n"):
        text = text + "\n"
    return sha256_bytes(text.encode("utf-8"))
