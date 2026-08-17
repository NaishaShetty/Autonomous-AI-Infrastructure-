"""Loader for the frozen Phase 3.1 evaluation protocol
(``configs/phase3_1_protocol.json``). This module contains no experiment
logic -- it only parses and validates the config so every script that needs
the protocol (the evaluator, the leakage audit, tests) reads it the same
way and cannot silently diverge on a seed list or coverage grid.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "configs" / "phase3_1_protocol.json"


@dataclass
class BootstrapConfig:
    n_resamples: int
    confidence_level: float
    seed: int


@dataclass
class Phase31Protocol:
    regime_sizes: tuple[int, ...]
    n_clusters: int
    seeds: list[int]
    primary_seed: int
    coverage_operating_points: list[float]
    calibration_bins: int
    bootstrap: BootstrapConfig
    raw: dict

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PROTOCOL_PATH) -> "Phase31Protocol":
        data = json.loads(Path(path).read_text())
        if data.get("primary_seed") not in data.get("seeds", []):
            raise ValueError("primary_seed must be a member of seeds -- protocol config is inconsistent")
        return cls(
            regime_sizes=tuple(data["regime_sizes"]),
            n_clusters=data["n_clusters"],
            seeds=list(data["seeds"]),
            primary_seed=data["primary_seed"],
            coverage_operating_points=list(data["coverage_operating_points"]),
            calibration_bins=data["calibration_bins"],
            bootstrap=BootstrapConfig(
                n_resamples=data["bootstrap"]["n_resamples"],
                confidence_level=data["bootstrap"]["confidence_level"],
                seed=data["bootstrap"]["seed"],
            ),
            raw=data,
        )
