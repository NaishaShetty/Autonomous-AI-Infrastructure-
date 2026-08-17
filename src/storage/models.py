"""SQLAlchemy persistence model for ReliabilityEvent.

Uses the SQLAlchemy foundation validated as reusable in Phase 1 (the
Abstention Engine's ``app/db/`` layer), but rebuilt clean rather than copied:
one table, matching the canonical schema in ``src/schema/events.py`` field
for field, with no personal data and no repo-specific tenancy/auth concerns
that belonged to the old prototype's DB layer.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReliabilityEventRecord(Base):
    """Persisted row for one ReliabilityEvent."""

    __tablename__ = "reliability_events"

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    workload_id: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(32))

    context: Mapped[str] = mapped_column(JSON)  # dict[str, float] stored as JSON

    raw_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    failure_risk: Mapped[float | None] = mapped_column(Float, nullable=True)

    decision: Mapped[str] = mapped_column(String(16))
    abstained: Mapped[bool] = mapped_column(Boolean)
    is_failure: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    failure_cluster: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    outcome: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    event_metadata: Mapped[str] = mapped_column(JSON, default=dict)
