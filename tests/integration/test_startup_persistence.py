"""Regression test for the P0 bug: SQLite persistence survives a process
restart, but the live ``FailureMemory`` was rebuilt independently on every
startup (purely from the synthetic training pass in
``src/pipeline_builder.py``) and never reloaded persisted failure history --
so "memory survives restart" was only true of the database row, not of the
actual learned memory state the live API serves risk from.

This drives the real startup path, ``src.api.train.build_default_pipeline``
(the exact function ``src/api/app.py``'s FastAPI lifespan calls), across two
simulated process lifetimes pointed at the same on-disk SQLite file.
"""
from __future__ import annotations

from src.api.train import WORKLOAD_ID, build_default_pipeline
from src.storage.db import get_session, init_db
from src.storage.repository import EventRepository


def test_failure_memory_survives_simulated_restart(tmp_path):
    url = f"sqlite:///{(tmp_path / 'startup_restart.db').as_posix()}"
    init_db(url)

    # -- "process 1" ----------------------------------------------------
    with get_session() as session:
        repo = EventRepository(session)
        pipeline_1 = build_default_pipeline(repository=repo)

    baseline_version = pipeline_1.failure_memory.status()["version"]
    baseline_n_failures = pipeline_1.failure_memory.status()["n_failure_events"]

    # Probe candidate contexts (real inference through the real trained
    # model, not a stub) until one confidently ANSWERs -- only a confirmed
    # ANSWER can become a "failure" (see src/api/pipeline.py) -- then force
    # a confirmed failure there via the opposite true_label.
    probe_context = None
    forced_true_label = None
    for magnitude in (0.0, 1.0, -1.0, 2.0, -2.0, 3.0, -3.0, 5.0, -5.0, 8.0, -8.0):
        candidate = {f: magnitude for f in pipeline_1.feature_names}
        with get_session() as session:
            repo = EventRepository(session)
            probe = pipeline_1.analyze(candidate, repository=repo)
        if probe.decision.value == "ANSWER":
            probe_context = candidate
            forced_true_label = 1 - probe.metadata["predicted_label"]
            break
    assert probe_context is not None, "no candidate context reached an ANSWER decision"

    with get_session() as session:
        repo = EventRepository(session)
        failure_event = pipeline_1.analyze(probe_context, repository=repo, true_label=forced_true_label)
    assert failure_event.is_failure is True

    status_after_failure = pipeline_1.failure_memory.status()
    assert status_after_failure["n_failure_events"] == baseline_n_failures + 1
    assert status_after_failure["fitted"] is True

    # -- simulated restart: fresh process, same DB file ------------------
    init_db(url)  # re-init against the identical URL, as app.py's lifespan does
    with get_session() as session:
        repo = EventRepository(session)
        pipeline_2 = build_default_pipeline(repository=repo)

    status_2 = pipeline_2.failure_memory.status()
    # The persisted failure (workload_id=WORKLOAD_ID) must have been merged
    # into the freshly-trained baseline, not silently dropped.
    assert status_2["n_failure_events"] >= baseline_n_failures + 1
    assert status_2["fitted"] is True

    with get_session() as session:
        repo = EventRepository(session)
        events = repo.get_failures(workload_id=WORKLOAD_ID)
    assert failure_event.event_id in {e.event_id for e in events}

    # The reloaded memory must actually use the historical failure: risk at
    # the exact previously-failed context must be strictly positive.
    with get_session() as session:
        repo = EventRepository(session)
        replay = pipeline_2.analyze(probe_context, repository=repo)
    assert replay.failure_risk is not None and replay.failure_risk > 0.0
