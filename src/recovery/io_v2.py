"""JSONL read/write for RecoveryEpisodeV2 collections (Active Phase 4.4).
Mirrors src.recovery.io (untouched, Phase 4.3's frozen artifact) for the v2
schema; not a modification of that module, a parallel one."""
from __future__ import annotations

import hashlib
from pathlib import Path

from src.recovery.schema_v2 import RecoveryEpisodeV2


def write_jsonl(episodes: list[RecoveryEpisodeV2], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ep in episodes:
            f.write(ep.model_dump_json() + "\n")


def read_jsonl(path: Path) -> list[RecoveryEpisodeV2]:
    episodes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                episodes.append(RecoveryEpisodeV2.model_validate_json(line))
    return episodes


def file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
