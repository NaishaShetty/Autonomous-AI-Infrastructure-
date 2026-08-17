import numpy as np

from src.failure_memory.memory import FailureMemory
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent


def _failure_event(a: float, b: float, confidence: float = 0.3) -> ReliabilityEvent:
    return ReliabilityEvent(
        workload_id="w",
        source=EventSource.FAILURE_MEMORY,
        context={"a": a, "b": b},
        confidence=confidence,
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.INCORRECT,
    )


def test_risk_is_zero_when_unfitted():
    memory = FailureMemory(["a", "b"], n_clusters=2)
    assert memory.risk({"a": 1.0, "b": 1.0}, confidence=0.5) == 0.0


def test_fit_with_no_failures_leaves_memory_unfitted():
    memory = FailureMemory(["a", "b"], n_clusters=2)
    memory.fit()
    assert not memory.is_fitted
    assert memory.risk({"a": 0.0, "b": 0.0}, confidence=0.5) == 0.0


def test_risk_near_a_known_failure_cluster_is_higher_than_far_away():
    memory = FailureMemory(["a", "b"], n_clusters=1, sigma=1.0)
    memory._failure_events = [_failure_event(10.0, 10.0) for _ in range(10)]
    memory.fit()
    assert memory.is_fitted

    near_risk = memory.risk({"a": 10.0, "b": 10.0}, confidence=0.3)
    far_risk = memory.risk({"a": -500.0, "b": -500.0}, confidence=0.3)
    assert 0.0 <= far_risk <= near_risk <= 1.0
    assert near_risk > far_risk


def test_retrieve_returns_k_nearest_ascending_distance():
    memory = FailureMemory(["a", "b"], n_clusters=2)
    memory._failure_events = [_failure_event(float(i), float(i)) for i in range(10)]
    memory.fit()
    results = memory.retrieve({"a": 3.0, "b": 3.0}, confidence=0.3, k=3)
    assert len(results) == 3
    distances = [d for _, d in results]
    assert distances == sorted(distances)


def test_retrieve_empty_before_fit():
    memory = FailureMemory(["a", "b"], n_clusters=2)
    assert memory.retrieve({"a": 0.0, "b": 0.0}, confidence=0.5) == []


def test_cluster_of_returns_none_when_unfitted():
    memory = FailureMemory(["a", "b"], n_clusters=2)
    assert memory.cluster_of({"a": 0.0, "b": 0.0}, confidence=0.5) is None
