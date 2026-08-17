"""JSONL read/write for RecoveryEpisode collections, plus manifest/checksum
helpers used by the dataset generator and the reproducibility checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.recovery.schema import RecoveryEpisode


def write_jsonl(episodes: list[RecoveryEpisode], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ep in episodes:
            f.write(ep.model_dump_json() + "\n")


def read_jsonl(path: Path) -> list[RecoveryEpisode]:
    episodes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                episodes.append(RecoveryEpisode.model_validate_json(line))
    return episodes


def file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
