"""reliability event -> persistence, and persistence survives a simulated
process restart (new engine/session pointed at the same sqlite file).

This is the regression test for the Phase 1 finding that Failure Memory's
storage was "in-memory only ... restart loses all history"
(PHASE1_AUDIT_REPORT.md sections 3, 5)."""
from __future__ import annotations

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.storage.db import init_db
from src.storage.repository import EventRepository


def _event(event_id: str | None = None, is_failure: bool = False) -> ReliabilityEvent:
    kwargs = dict(
        workload_id="w1",
        source=EventSource.RELIABILITY_ENGINE,
        context={"f1": 1.0, "f2": 2.0},
        confidence=0.42,
        decision=Decision.ANSWER if not is_failure else Decision.ANSWER,
        abstained=False,
        is_failure=is_failure,
        outcome=Outcome.INCORRECT if is_failure else Outcome.CORRECT,
    )
    if event_id is not None:
        kwargs["event_id"] = event_id
    return ReliabilityEvent(**kwargs)


def test_save_and_get_roundtrip(session_factory):
    with session_factory() as session:
        repo = EventRepository(session)
        event = _event()
        repo.save(event)

    with session_factory() as session:
        repo = EventRepository(session)
        fetched = repo.get(event.event_id)
    assert fetched is not None
    assert fetched.event_id == event.event_id
    assert fetched.confidence == event.confidence
    assert fetched.context == event.context


def test_persistence_survives_new_engine_against_same_db_file(tmp_path, session_factory):
    """Simulates a process restart: re-point the db module at the same
    sqlite file via a fresh init_db() call and confirm the row is still
    there."""
    url = f"sqlite:///{(tmp_path / 'restart_test.db').as_posix()}"
    init_db(url)
    from src.storage.db import get_session

    with get_session() as session:
        EventRepository(session).save(_event(event_id="restart-marker"))

    # Simulate restart: re-init against the identical URL (a fresh engine).
    init_db(url)
    with get_session() as session:
        fetched = EventRepository(session).get("restart-marker")
    assert fetched is not None
    assert fetched.event_id == "restart-marker"


def test_get_failures_filters_correctly(session_factory):
    with session_factory() as session:
        repo = EventRepository(session)
        repo.save(_event(event_id="ok-1", is_failure=False))
        repo.save(_event(event_id="fail-1", is_failure=True))
        repo.save(_event(event_id="fail-2", is_failure=True))

    with session_factory() as session:
        repo = EventRepository(session)
        failures = repo.get_failures(workload_id="w1")
    ids = {e.event_id for e in failures}
    assert ids == {"fail-1", "fail-2"}


def test_save_many_and_count(session_factory):
    with session_factory() as session:
        repo = EventRepository(session)
        events = [_event(event_id=f"e{i}") for i in range(5)]
        repo.save_many(events)

    with session_factory() as session:
        repo = EventRepository(session)
        assert repo.count(workload_id="w1") == 5
