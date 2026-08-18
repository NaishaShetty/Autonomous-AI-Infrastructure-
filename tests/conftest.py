from __future__ import annotations

from pathlib import Path

import pytest

from src.storage import db as db_module
from src.storage.db import reset_db


@pytest.fixture()
def session_factory(tmp_path):
    """A fresh, isolated SQLite database per test -- never the dev/demo
    database, and definitely never any committed personal data (see
    PHASE1_AUDIT_REPORT.md section 5/11)."""
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    reset_db(url)
    yield db_module.get_session


# ---------------------------------------------------------------------------
# Real-dataset gating (AgentRx / AIOps 2020 / Alibaba GPU 2020).
#
# These raw/processed files are gitignored (see /data/ in .gitignore) and are
# not shipped with the repo -- they must be fetched and regenerated locally
# per docs/DATA_SETUP.md. Tests that need them request one of the
# require_*_data fixtures below instead of calling the loader directly, so a
# clean checkout without local data setup gets a clear, itemized pytest SKIP
# ("real dataset 'X' not present locally, see docs/DATA_SETUP.md") instead of
# a bare FileNotFoundError.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

REAL_DATA_MARKER_PATHS = {
    "alibaba_gpu2020": REPO_ROOT / "data" / "processed" / "alibaba_gpu2020" / "task_table.main_sample.csv",
    "aiops_kpi": REPO_ROOT / "data" / "audit" / "aiops_kpi" / "positive_windows.json",
    "agentrx": REPO_ROOT / "data" / "processed" / "agentrx" / "tau_retail_joined.jsonl",
}


def _skip_if_missing(dataset_name: str) -> None:
    path = REAL_DATA_MARKER_PATHS[dataset_name]
    if not path.exists():
        pytest.skip(
            f"real dataset '{dataset_name}' not present locally "
            f"(expected {path.relative_to(REPO_ROOT)}), see docs/DATA_SETUP.md"
        )


@pytest.fixture(scope="session")
def require_alibaba_data():
    _skip_if_missing("alibaba_gpu2020")


@pytest.fixture(scope="session")
def require_aiops_data():
    _skip_if_missing("aiops_kpi")


@pytest.fixture(scope="session")
def require_agentrx_data():
    _skip_if_missing("agentrx")
