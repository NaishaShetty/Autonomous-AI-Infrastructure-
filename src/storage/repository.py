"""Repository translating between the canonical ReliabilityEvent (pydantic)
and its persisted row (SQLAlchemy). This is the only place the two are
converted, so schema drift between "what's validated" and "what's stored"
cannot silently occur.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent

from .models import ReliabilityEventRecord


def _to_record(event: ReliabilityEvent) -> ReliabilityEventRecord:
    return ReliabilityEventRecord(
        event_id=event.event_id,
        timestamp=event.timestamp,
        workload_id=event.workload_id,
        source=event.source.value if isinstance(event.source, EventSource) else event.source,
        context=event.context,
        raw_confidence=event.raw_confidence,
        confidence=event.confidence,
        failure_risk=event.failure_risk,
        decision=event.decision.value if isinstance(event.decision, Decision) else event.decision,
        abstained=event.abstained,
        is_failure=event.is_failure,
        failure_cluster=event.failure_cluster,
        outcome=event.outcome.value if isinstance(event.outcome, Outcome) else event.outcome,
        event_metadata=event.metadata,
    )


def _from_record(record: ReliabilityEventRecord) -> ReliabilityEvent:
    ts = record.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ReliabilityEvent(
        event_id=record.event_id,
        timestamp=ts,
        workload_id=record.workload_id,
        source=EventSource(record.source),
        context=record.context,
        raw_confidence=record.raw_confidence,
        confidence=record.confidence,
        failure_risk=record.failure_risk,
        decision=Decision(record.decision),
        abstained=record.abstained,
        is_failure=record.is_failure,
        failure_cluster=record.failure_cluster,
        outcome=Outcome(record.outcome),
        metadata=record.event_metadata or {},
    )


class EventRepository:
    """Persistence-facing API used by both the reliability engine and the
    failure-memory subsystem, so neither has to know SQLAlchemy directly."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, event: ReliabilityEvent) -> ReliabilityEvent:
        record = _to_record(event)
        self._session.merge(record)
        self._session.flush()
        return event

    def save_many(self, events: list[ReliabilityEvent]) -> None:
        for event in events:
            self._session.merge(_to_record(event))
        self._session.flush()

    def get(self, event_id: str) -> ReliabilityEvent | None:
        record = self._session.get(ReliabilityEventRecord, event_id)
        return _from_record(record) if record else None

    def get_failures(
        self, workload_id: str | None = None, limit: int | None = None
    ) -> list[ReliabilityEvent]:
        stmt = select(ReliabilityEventRecord).where(ReliabilityEventRecord.is_failure.is_(True))
        if workload_id is not None:
            stmt = stmt.where(ReliabilityEventRecord.workload_id == workload_id)
        stmt = stmt.order_by(ReliabilityEventRecord.timestamp)
        if limit is not None:
            stmt = stmt.limit(limit)
        return [_from_record(r) for r in self._session.scalars(stmt).all()]

    def get_all(
        self, workload_id: str | None = None, limit: int | None = None
    ) -> list[ReliabilityEvent]:
        stmt = select(ReliabilityEventRecord)
        if workload_id is not None:
            stmt = stmt.where(ReliabilityEventRecord.workload_id == workload_id)
        stmt = stmt.order_by(ReliabilityEventRecord.timestamp)
        if limit is not None:
            stmt = stmt.limit(limit)
        return [_from_record(r) for r in self._session.scalars(stmt).all()]

    def count(self, workload_id: str | None = None) -> int:
        return len(self.get_all(workload_id=workload_id))
