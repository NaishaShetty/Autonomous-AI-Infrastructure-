"""Phase 4.5 gap 2 -- FailureMemoryStore is durable across a real restart.

Writes memory, closes the store (and, in the strongest variant, destroys
the Python object entirely and re-imports/reopens fresh), and confirms the
records, ``memory_version``, and the SCHEMA_VERSION-tracking table all
survive -- and that the planner's decision is still correctly influenced
after reopening, not just that raw rows are still in the file.
"""
import gc

from src.phase4.diagnosis import DiagnosisEngine
from src.phase4.memory import MEMORY_SCHEMA_VERSION, FailureMemoryStore
from src.phase4.recovery import RuleBasedRecoveryPlanner


def _ev(i, t, ts="2026-01-01T00:00:01Z", rid="r1", wid="w1", payload=None):
    return {"event_id": i, "event_type": t, "timestamp": ts, "job_id": rid, "workload_id": wid, "environment_id": "env1", "payload": payload or {}, "provenance": {"source": "test", "source_record_id": i, "timestamp_quality": "EXACT"}}


def _failure(fid="f1", cls="PROCESS_NONZERO_EXIT", rid="r1", wid="w1"):
    return {"failure_id": fid, "failure_class": cls, "run_id": rid, "workload_id": wid, "environment_id": "env1", "failure_timestamp": "2026-01-01T00:00:02Z", "evidence_references": ["fobs"], "provenance": {"source": "test", "source_record_id": "fobs", "timestamp_quality": "EXACT"}}


def test_default_in_memory_store_behaves_exactly_as_before(tmp_path):
    """No path given -- must be indistinguishable from the pre-Phase-4.5
    behavior for every existing caller/test in this repository."""
    store = FailureMemoryStore()
    assert store.path == ":memory:"
    assert store.memory_version == 0
    store.add(workload_id="w1", environment_id="env1", failure_class="PROCESS_TIMEOUT", root_cause="RUNTIME_TIMEOUT", diagnosis_confidence="HIGH", source_run_id="r1", source_diagnosis_id="d1", action_taken="retry", validated_outcome="RECOVERED", recorded_at="2026-01-01T00:00:00Z", provenance={})
    assert store.memory_version == 1
    store.close()


def test_records_and_memory_version_survive_a_real_process_style_restart(tmp_path):
    db_path = tmp_path / "memory.sqlite"

    store = FailureMemoryStore(db_path)
    store.add(workload_id="w1", environment_id="env1", failure_class="PROCESS_NONZERO_EXIT", root_cause="PROCESS_EXIT_FAILURE", diagnosis_confidence="HIGH", source_run_id="r-prior-1", source_diagnosis_id="d1", action_taken="restart", validated_outcome="NOT_RECOVERED", recorded_at="2026-01-01T00:00:00Z", provenance={"source": "test"})
    store.add(workload_id="w1", environment_id="env1", failure_class="PROCESS_NONZERO_EXIT", root_cause="PROCESS_EXIT_FAILURE", diagnosis_confidence="HIGH", source_run_id="r-prior-2", source_diagnosis_id="d2", action_taken="restart", validated_outcome="NOT_RECOVERED", recorded_at="2026-01-01T00:00:01Z", provenance={"source": "test"})
    assert store.memory_version == 2
    assert store.schema_version == MEMORY_SCHEMA_VERSION
    store.close()
    del store
    gc.collect()  # actually drop the Python object, not just close the connection

    reopened = FailureMemoryStore(db_path)
    assert reopened.memory_version == 2  # survived the restart
    assert reopened.schema_version == MEMORY_SCHEMA_VERSION

    matches = reopened.retrieve(workload_id="w1", environment_id="env1", failure_class="PROCESS_NONZERO_EXIT", exclude_run_id="r-new", at_or_before="2026-01-02T00:00:00Z")
    assert {m.record.source_run_id for m in matches} == {"r-prior-1", "r-prior-2"}

    # The reopened store must still correctly influence the planner: two
    # prior confirmed restart failures means the planner must avoid restart
    # in favor of the next candidate, exactly as it would if the process had
    # never restarted at all.
    events = [_ev("start", "execution_started", "2026-01-01T00:00:01Z", "r-new", "w1"), _ev("fobs", "failure_detected", "2026-01-01T00:00:02Z", "r-new", "w1", {"failure_kind": "NONZERO_EXIT"})]
    diagnosis = DiagnosisEngine().diagnose(_failure(rid="r-new"), events, memory=reopened)
    assert diagnosis.foundation_references["memory_used"] is True
    action = RuleBasedRecoveryPlanner().plan(diagnosis, memory=reopened)
    assert action.action_type == "retry"  # restart avoided, matching the pre-restart record
    reopened.close()


def test_schema_meta_table_is_present_and_versioned(tmp_path):
    db_path = tmp_path / "memory.sqlite"
    store = FailureMemoryStore(db_path)
    row = store._db.execute("SELECT schema_version FROM memory_schema_meta WHERE id=1").fetchone()
    assert row is not None
    assert row[0] == MEMORY_SCHEMA_VERSION
    store.close()


def test_a_future_schema_version_in_the_file_is_rejected_rather_than_silently_misread(tmp_path):
    db_path = tmp_path / "memory.sqlite"
    store = FailureMemoryStore(db_path)
    store._db.execute("UPDATE memory_schema_meta SET schema_version=?", (MEMORY_SCHEMA_VERSION + 1,))
    store._db.commit()
    store.close()

    try:
        FailureMemoryStore(db_path)
        raise AssertionError("expected a ValueError when opening a store written by a newer schema")
    except ValueError as exc:
        assert "newer schema" in str(exc)
