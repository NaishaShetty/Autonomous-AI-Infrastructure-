"""Frozen-source loading for Phase 5.2 dataset construction.

Every function here is READ-ONLY against the frozen Phase 4 evidence
directories named in PHASE5_1_SOURCE_INVENTORY.json. Nothing here writes to
any path under experiments/results/ other than what the caller
(build_dataset.py) explicitly directs into the new
phase5_dataset_construction/<timestamp>/ output directory.

Only sources classified in PHASE5_1_SOURCE_INVENTORY.json as class 1 or 2
(canonical raw / canonical derived) and structurally available as
per-episode or per-task-instance JSON/JSONL are used as record content
sources here. Aggregate-only evidence (class 2 but rolled up to
family/environment-level metrics with no retained per-record rows, e.g.
experiments/results/post_p5_remediation*/raw/*_results.json and
experiments/results/phase4_6_to_4_10/.../raw/decisions/README.json's
disclosed non-dump of per-episode Decision objects) is NOT a source of
per-record content here -- this is a genuine source-availability limitation,
disclosed in PHASE5_2_DATASET_CONSTRUCTION_REPORT.md rather than
worked around by inventing rows.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]

# --- controlled_runtime track sources (SRC-021, SRC-022) -------------------
PHASE4_4_RESULTS = REPO_ROOT / "experiments/results/phase4_4_autonomy_pipeline/results.json"
PHASE4_5_CONTINUOUS = REPO_ROOT / "experiments/results/phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl"

# --- agent_task track sources (SRC-024, real per-example raw evidence) -----
ARITHMETIC_EPISODES = REPO_ROOT / "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/episodes/arithmetic_episodes.json"
CLASSIFICATION_PREDICTIONS = REPO_ROOT / "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/classification_predictions.json"
QA_PREDICTIONS = REPO_ROOT / "experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/qa_predictions.json"

ALL_SOURCE_FILES = [
    PHASE4_4_RESULTS,
    PHASE4_5_CONTINUOUS,
    ARITHMETIC_EPISODES,
    CLASSIFICATION_PREDICTIONS,
    QA_PREDICTIONS,
]


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iter_phase4_4_episodes() -> Iterator[dict]:
    """Yields the 6 real closed-loop episodes from Phase 4.4 (earliest
    Gen-3 full-loop evidence, SRC-021). Sorted deterministically by
    ``episode`` (the source's own natural string key) so output ordering
    never depends on the source list's on-disk order."""
    data = load_json(PHASE4_4_RESULTS)
    episodes = data["closed_loop_episodes"]["episodes"]
    for ep in sorted(episodes, key=lambda e: e["episode"]):
        yield ep


def iter_phase4_5_continuous_episodes() -> Iterator[dict]:
    """Yields the 40 real continuous-mode episodes from Phase 4.5 at-scale
    evidence (SRC-022). Sorted deterministically by the source's own
    ``episode`` integer index (its natural, generation-order key)."""
    rows = load_jsonl(PHASE4_5_CONTINUOUS)
    # The file's last line is a run-level summary row (has "summary": True,
    # no "episode" key) -- it is aggregate metadata, not a per-episode
    # record, so it is excluded here (and is not itself in scope as a
    # dataset content row; its content is already covered narratively).
    episode_rows = [r for r in rows if "episode" in r and not r.get("summary")]
    for row in sorted(episode_rows, key=lambda r: r["episode"]):
        yield row


def iter_arithmetic_task_records() -> Iterator[dict]:
    """Yields the 2000 real arithmetic self-consistency task instances
    (SRC-024/SRC-010). Sorted deterministically by ``example_id``."""
    data = load_json(ARITHMETIC_EPISODES)
    for row in sorted(data, key=lambda r: r["example_id"]):
        yield row


def iter_sentiment_task_records() -> Iterator[dict]:
    """Yields the 660 real sentiment softmax-margin task instances
    (SRC-024/SRC-011). Sorted deterministically by ``example_id``."""
    data = load_json(CLASSIFICATION_PREDICTIONS)
    for row in sorted(data, key=lambda r: r["example_id"]):
        yield row


def iter_qa_task_records() -> Iterator[dict]:
    """Yields the 400 real extractive QA span-logit task instances
    (SRC-024/SRC-012). Sorted deterministically by ``example_id``."""
    data = load_json(QA_PREDICTIONS)
    for row in sorted(data, key=lambda r: r["example_id"]):
        yield row
