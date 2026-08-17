from __future__ import annotations

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
