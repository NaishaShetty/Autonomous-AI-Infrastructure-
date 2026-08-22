"""Regression tests for the P0 failure-memory lifecycle bug:

    ``FailureMemory.store()`` set ``_fitted = False`` (clustering state
    marked stale) but nothing in the live pipeline reliably refit it before
    the *next* request -- so ``risk()`` returned 0.0 / "no signal" forever
    after the first failure, even though real failure history existed.

These tests exercise the fixed lifecycle: STORE -> MARK DIRTY -> REBUILD ->
VALIDATE -> ATOMICALLY PROMOTE -> SERVE, both directly against
``FailureMemory`` and through ``src.api.pipeline.ReliabilityPipeline`` (the
same code path the live API uses), per docs section 3's required test list:

  1. initial memory works
  2. a failure is recorded
  3. subsequent inference actually uses the newly recorded failure
  4. risk changes appropriately when relevant historical failures exist
  5. a failed memory rebuild does not destroy the previous valid model
  6. restart/reload restores memory correctly
     (see tests/integration/test_startup_persistence.py for the full
     process-restart version of #6 through the live ``build_default_pipeline``)
"""
from __future__ import annotations

import pytest

from src.decision.policy import DecisionMode, DecisionPolicy
from src.failure_memory.memory import FailureMemory
from src.reliability.calibrator import CalibrationResult
from src.reliability.workload_model import WorkloadPrediction
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.storage.repository import EventRepository
from src.api.pipeline import ReliabilityPipeline


class _FixedWorkloadModel:
    """Always predicts label 0 with high, fixed confidence -- lets tests
    control is_failure deterministically via the ``true_label`` passed to
    ``analyze()`` instead of depending on a trained classifier's output."""

    def predict(self, x) -> WorkloadPrediction:
        return WorkloadPrediction(predicted_label=0, predicted_proba=0.95, margin=0.9, entropy=0.05)


class _FixedCalibrator:
    def __init__(self, confidence: float = 0.95):
        self.confidence = confidence

    def predict(self, features) -> CalibrationResult:
        return CalibrationResult(raw_confidence=self.confidence, calibrated_confidence=self.confidence)


def _make_pipeline(n_clusters: int = 1, confidence: float = 0.95) -> ReliabilityPipeline:
    return ReliabilityPipeline(
        workload_model=_FixedWorkloadModel(),
        calibrator=_FixedCalibrator(confidence),
        failure_memory=FailureMemory(["a", "b"], n_clusters=n_clusters, sigma=1.0),
        policy=DecisionPolicy(),
        feature_names=["a", "b"],
        workload_id="w-lifecycle",
        mode=DecisionMode.COMBINED,
    )


def _failure_event(a: float, b: float, event_id: str) -> ReliabilityEvent:
    return ReliabilityEvent(
        event_id=event_id,
        workload_id="w-lifecycle",
        source=EventSource.FAILURE_MEMORY,
        context={"a": a, "b": b},
        confidence=0.3,
        decision=Decision.ANSWER,
        abstained=False,
        is_failure=True,
        outcome=Outcome.INCORRECT,
    )


# 1. initial memory works -----------------------------------------------------
def test_initial_memory_has_no_signal_and_does_not_crash(session_factory):
    pipeline = _make_pipeline()
    with session_factory() as session:
        repo = EventRepository(session)
        event = pipeline.analyze({"a": 1.0, "b": 1.0}, repository=repo)
    assert event.failure_risk == 0.0
    assert pipeline.failure_memory.status()["fitted"] is False


# 2 & 3. a failure is recorded, and the *next* request actually uses it -----
def test_stored_failure_is_reflected_in_the_next_two_requests(session_factory):
    """This is the exact bug scenario from the spec: request 1 stores a
    failure: request 2 and request 3 must NOT come back with risk 0.0."""
    pipeline = _make_pipeline()
    ctx = {"a": 10.0, "b": 10.0}

    with session_factory() as session:
        repo = EventRepository(session)
        # Request 1: force a failure (predicted label 0, true label 1).
        event1 = pipeline.analyze(ctx, repository=repo, true_label=1)
        assert event1.is_failure is True
        assert pipeline.failure_memory.status()["fitted"] is True
        assert pipeline.failure_memory.status()["version"] == 1

        # Request 2: same context, no ground truth (ordinary live inference).
        event2 = pipeline.analyze(ctx, repository=repo)
        # Request 3: repeat.
        event3 = pipeline.analyze(ctx, repository=repo)

    assert event2.failure_risk is not None and event2.failure_risk > 0.0
    assert event3.failure_risk is not None and event3.failure_risk > 0.0


# 4. risk changes appropriately when relevant history exists -----------------
def test_risk_is_higher_near_known_failure_history_than_far_away(session_factory):
    pipeline = _make_pipeline()
    with session_factory() as session:
        repo = EventRepository(session)
        for i in range(6):
            pipeline.analyze({"a": 10.0 + i * 0.01, "b": 10.0 + i * 0.01}, repository=repo, true_label=1)

        near = pipeline.analyze({"a": 10.0, "b": 10.0}, repository=repo)
        far = pipeline.analyze({"a": -500.0, "b": -500.0}, repository=repo)

    assert near.failure_risk > far.failure_risk


# 5. a failed rebuild does not destroy the previous valid model --------------
def test_failed_rebuild_preserves_previous_valid_model(monkeypatch):
    memory = FailureMemory(["a", "b"], n_clusters=1, sigma=1.0)
    for i in range(5):
        memory._failure_events.append(_failure_event(10.0, 10.0, f"f{i}"))
    memory._dirty = True
    assert memory.rebuild() is True
    assert memory.status()["version"] == 1
    risk_before = memory.risk({"a": 10.0, "b": 10.0}, confidence=0.3)
    assert risk_before > 0.0

    # A new failure arrives, but the next rebuild attempt blows up.
    memory._failure_events.append(_failure_event(11.0, 11.0, "f-new"))
    memory._dirty = True

    def _boom(self, failure_events):
        raise RuntimeError("simulated rebuild failure")

    monkeypatch.setattr(FailureMemory, "_fit_new_state", _boom)
    assert memory.rebuild() is False

    status = memory.status()
    assert status["fitted"] is True  # previous state still active
    assert status["version"] == 1  # promotion did not happen
    assert status["dirty"] is True  # eligible to retry later
    assert "simulated rebuild failure" in status["last_rebuild_error"]

    risk_after_failed_rebuild = memory.risk({"a": 10.0, "b": 10.0}, confidence=0.3)
    assert risk_after_failed_rebuild == pytest.approx(risk_before)


# 6. restart/reload restores memory correctly (memory-level; see
#    test_startup_persistence.py for the full process-restart version) -----
def test_merge_from_repository_is_additive_and_rebuild_uses_merged_history(session_factory):
    with session_factory() as session:
        repo = EventRepository(session)
        for i in range(5):
            repo.save(_failure_event(10.0, 10.0, f"persisted-{i}"))

    memory = FailureMemory(["a", "b"], n_clusters=2, sigma=1.0)
    # Simulate an in-process baseline the live memory already had (e.g. a
    # synthetic training pass) before merging in persisted history -- a
    # separate cluster from the persisted failures, not the same one.
    memory._failure_events.append(_failure_event(0.0, 0.0, "baseline-0"))

    with session_factory() as session:
        repo = EventRepository(session)
        added = memory.merge_from_repository(repo, workload_id="w-lifecycle")

    assert added == 5
    assert memory.n_failures == 6  # baseline preserved, not replaced
    assert memory.is_dirty is True
    assert memory.rebuild() is True
    assert memory.status()["fitted"] is True

    near = memory.risk({"a": 10.0, "b": 10.0}, confidence=0.3)
    far = memory.risk({"a": 5000.0, "b": 5000.0}, confidence=0.3)
    assert near > far
