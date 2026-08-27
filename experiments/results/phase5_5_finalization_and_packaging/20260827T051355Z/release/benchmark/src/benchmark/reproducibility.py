"""Reproducibility metadata per PHASE5_3_REPRODUCIBILITY_PROTOCOL.md.

Every run records: benchmark/dataset/schema/protocol/metric/baseline
versions, git commit, Python version, dependency versions, platform
(coarsened), seeds, source dataset hashes, and a benchmark-config hash. No
Python hash() is used anywhere in this package.
"""
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from .constants import (
    BASELINE_VERSION,
    BENCHMARK_VERSION,
    BOOTSTRAP_SEED,
    DATASET_VERSION,
    IMPLEMENTATION_VERSION,
    METRIC_VERSION,
    PROTOCOL_VERSION,
    REPO_ROOT,
    SCHEMA_VERSION,
)
from .ids import sha256_canonical_json


def _dep_version(name: str) -> str | None:
    try:
        mod = __import__(name)
        return getattr(mod, "__version__", None)
    except Exception:
        return None


def git_commit(repo_root: Path = REPO_ROOT) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None


def git_status_clean(repo_root: Path = REPO_ROOT) -> dict:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        return {"clean": len(lines) == 0, "n_changed_or_untracked": len(lines)}
    except Exception:
        return {"clean": None, "n_changed_or_untracked": None}


def platform_string() -> str:
    # Coarsened per PHASE5_1_PUBLICATION_BOUNDARY.md host-identity exclusion:
    # OS family + release, never platform.node() (hostname).
    return f"{platform.system()}-{platform.release()}-{platform.machine()}"


def collect_reproducibility_metadata(*, config: dict) -> dict:
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "metric_version": METRIC_VERSION,
        "baseline_version": BASELINE_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "code_commit": git_commit(),
        "git_status": git_status_clean(),
        "python_version": sys.version,
        "platform": platform_string(),
        "dependency_versions": {
            "numpy": _dep_version("numpy"),
            "scipy": _dep_version("scipy"),
            "sklearn": _dep_version("sklearn"),
            "pandas": _dep_version("pandas"),
        },
        "bootstrap_seed": BOOTSTRAP_SEED,
        "config_hash": sha256_canonical_json(config),
        "no_python_hash_used": True,
        "no_filesystem_order_dependence": True,
    }
