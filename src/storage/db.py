"""Database engine/session management.

Default target is a clean, sanitized local SQLite dev database at
``data/unified_dev.db`` (created empty, never seeded with real credentials
or personal data -- see PHASE1_AUDIT_REPORT.md section 5/11 on the
``reliability.db`` committed-credential issue this project deliberately does
not repeat). Override with the ``DATABASE_URL`` env var for any other
backend SQLAlchemy supports.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_DB_PATH = DATA_DIR / "unified_dev.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def _make_engine(database_url: str | None = None):
    url = database_url or _database_url()
    if url.startswith("sqlite"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


_engine = _make_engine()
_SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db(database_url: str | None = None) -> None:
    """Create all tables if they don't already exist. Idempotent."""
    global _engine, _SessionLocal
    if database_url is not None:
        _engine = _make_engine(database_url)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)


def reset_db(database_url: str | None = None) -> None:
    """Drop and recreate all tables. Used by tests and benchmark runs that
    need a clean slate -- never touches any file other than the configured
    dev/test database."""
    global _engine, _SessionLocal
    if database_url is not None:
        _engine = _make_engine(database_url)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)


@contextmanager
def get_session() -> Session:
    init_db()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
