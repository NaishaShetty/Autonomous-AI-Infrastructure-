"""persistence -> failure memory -> risk: failures written through the
repository can be reloaded into a fresh FailureMemory instance (simulating a
new process) and still produce a risk signal."""
from __future__ import annotations

from src.failure_memory.memory import FailureMemory
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.storage.repository import EventRepository


def _failure(event_id: str, a: float, b: float) -> ReliabilityEvent:
    return ReliabilityEvent(
        event_id=event_id,
        workload_id="w-fm",
        source=EventSource.FAILURE_MEMORY,
        context={"a": a, "b": b},
        confidence=0.3,
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.INCORRECT,
    )


def test_store_persists_and_reload_from_repository_powers_risk(session_factory):
    memory = FailureMemory(["a", "b"], n_clusters=1)
    with session_factory() as session:
        repo = EventRepository(session)
        for i in range(10):
            memory.store(_failure(f"f{i}", 5.0, 5.0), repo)

    # Simulate a fresh process: a brand-new FailureMemory with no state,
    # rebuilt purely from what the repository persisted.
    fresh_memory = FailureMemory(["a", "b"], n_clusters=1)
    with session_factory() as session:
        repo = EventRepository(session)
        fresh_memory.load_from_repository(repo, workload_id="w-fm")
    fresh_memory.fit()

    assert fresh_memory.n_failures == 10
    assert fresh_memory.is_fitted
    assert fresh_memory.risk({"a": 5.0, "b": 5.0}, confidence=0.3) > fresh_memory.risk(
        {"a": -500.0, "b": -500.0}, confidence=0.3
    )


def test_non_failure_events_are_written_but_not_retained_by_failure_memory(session_factory):
    memory = FailureMemory(["a", "b"], n_clusters=1)
    ok_event = ReliabilityEvent(
        workload_id="w-fm",
        source=EventSource.RELIABILITY_ENGINE,
        context={"a": 1.0, "b": 1.0},
        confidence=0.9,
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=False,
        outcome=Outcome.CORRECT,
    )
    with session_factory() as session:
        repo = EventRepository(session)
        memory.store(ok_event, repo)
        assert repo.get(ok_event.event_id) is not None  # written through
    assert memory.n_failures == 0  # but not treated as a failure-memory entry
