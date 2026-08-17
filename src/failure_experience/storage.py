"""Task 8: persistent memory storage.

Architecture decision (documented per Task 8's requirement to justify, not
default to something heavier): SQLite via SQLAlchemy, the same technology
already used by ``src/storage/`` -- reusing the established pattern
(engine/session/repository split) rather than introducing a new persistence
technology. NOT a shared table with ``src.storage.models.ReliabilityEventRecord``
(that model has no slots for diagnosis/recovery/validation and is frozen,
``extra="forbid"`` at the pydantic layer) and NOT the same database file
(a separate ``data/failure_experience_dev.db`` keeps this additive layer
physically isolated from the frozen Phase 2/3 dev database -- no risk of a
migration or schema-drift touching frozen data).

One row per FailureExperience, storing the full validated object as a JSON
blob (so schema evolution/round-trip fidelity is exact and lossless) plus a
handful of indexed scalar columns that mirror hot retrieval-filter fields
(Task 10) -- avoids inventing a normalized 10-table schema for what is,
at this scale (hundreds to low thousands of experiences), a straightforward
filtered-lookup problem. No vector database, no ORM-mapped nested tables --
the smallest mechanism that gives persistence, deterministic retrieval,
provenance, versioning, temporal filtering, and testability, per Task 8.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .schema import FailureExperience

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_DB_PATH = DATA_DIR / "failure_experience_dev.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


class FailureExperienceRecord(Base):
    __tablename__ = "failure_experiences"

    experience_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    episode_id: Mapped[str] = mapped_column(String(256), index=True)
    source_dataset: Mapped[str] = mapped_column(String(128), index=True)
    workload_id: Mapped[str] = mapped_column(String(256), index=True)
    failure_type: Mapped[str] = mapped_column(String(256), index=True)
    failure_signature: Mapped[str] = mapped_column(String(64), index=True)
    affected_component: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    final_status: Mapped[str] = mapped_column(String(32), index=True)
    eligibility_role: Mapped[str] = mapped_column(String(32), index=True)
    observed_at: Mapped["str"] = mapped_column(DateTime(timezone=True), index=True)
    schema_version: Mapped[str] = mapped_column(String(32))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)  # full FailureExperience.model_dump(mode="json")


def _database_url() -> str:
    return os.environ.get("FAILURE_EXPERIENCE_DATABASE_URL", DEFAULT_DATABASE_URL)


def _make_engine(database_url: str | None = None):
    url = database_url or _database_url()
    if url.startswith("sqlite"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


_engine = _make_engine()
_SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db(database_url: str | None = None) -> None:
    global _engine, _SessionLocal
    if database_url is not None:
        _engine = _make_engine(database_url)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)


def reset_db(database_url: str | None = None) -> None:
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


def _to_record(experience: FailureExperience) -> FailureExperienceRecord:
    return FailureExperienceRecord(
        experience_id=experience.identity.experience_id,
        episode_id=experience.identity.episode_id,
        source_dataset=experience.provenance.source_dataset,
        workload_id=experience.workload_context.workload_id,
        failure_type=experience.failure.failure_type,
        failure_signature=experience.failure.failure_signature,
        affected_component=experience.failure.affected_component,
        final_status=experience.outcome.final_status.value,
        eligibility_role=experience.eligibility.role.value,
        observed_at=experience.identity.observed_at,
        schema_version=experience.schema_version,
        content_hash=experience.content_hash(),
        payload=experience.model_dump(mode="json"),
    )


class FailureExperienceRepository:
    """Idempotent write (Task 13 item 19): saving the same ``experience_id``
    twice is a merge/upsert, never a duplicate row -- re-ingesting the same
    source record is safe."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, experience: FailureExperience) -> FailureExperience:
        self._session.merge(_to_record(experience))
        self._session.flush()
        return experience

    def save_many(self, experiences: list[FailureExperience]) -> int:
        for e in experiences:
            self._session.merge(_to_record(e))
        self._session.flush()
        return len(experiences)

    def get(self, experience_id: str) -> FailureExperience | None:
        record = self._session.get(FailureExperienceRecord, experience_id)
        return FailureExperience.model_validate(record.payload) if record else None

    def all_records(self) -> list[FailureExperienceRecord]:
        return list(self._session.scalars(select(FailureExperienceRecord)).all())

    def count(self) -> int:
        return len(self.all_records())
