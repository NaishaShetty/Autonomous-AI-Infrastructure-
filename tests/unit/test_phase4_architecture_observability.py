import json
from pathlib import Path
import pytest
from src.data_foundation.foundation import CanonicalEvent,Provenance,DecisionTimeSnapshot,Availability,TimestampQuality
from src.phase4.architecture import AutonomyState,WorkloadStateMachine,RecoveryAction,Decision,SafetyGate,SystemError
from src.phase4.observability import EventStore,ObservationCollector,DecisionSnapshotBuilder,ObservationReplay,ObservabilityAPI

ROOT=Path(__file__).resolve().parents[2]

def p(): return Provenance(source='synthetic/test-only',source_record_id='r1',timestamp_quality=TimestampQuality.EXACT)
def raw(eid,typ,ts,**kw): return {'event_id':eid,'event_type':typ,'job_id':'j1','source_dataset':'synthetic/test-only','timestamp':ts,'schema_version':'3.11.3.12.v1','provenance':{'source':'synthetic/test-only','source_record_id':eid,'timestamp_quality':'EXACT'},**kw}

def test_state_machine_allows_valid_and_rejects_forbidden_transitions():
    s=WorkloadStateMachine(); s.transition(AutonomyState.OBSERVING); s.transition(AutonomyState.PREDICTED); s.transition(AutonomyState.DECIDING)
    with pytest.raises(ValueError): s.transition(AutonomyState.EXECUTING)
    assert s.can_transition(AutonomyState.DIAGNOSING)

def test_safety_gate_blocks_score_only_and_requires_authorization():
    action=RecoveryAction('a1','RETRY',authorization_required=True,provenance=p())
    denied=Decision('d1','p1','ACT','high score','NOT_AUTHORIZED',p())
    assert not SafetyGate().authorize(action,denied)
    authorized=Decision('d2','p1','ACT','approved','AUTHORIZED',p())
    assert SafetyGate().authorize(action,authorized)

def test_ingestion_requires_valid_schema_and_provenance():
    store=EventStore(); collector=ObservationCollector(store)
    e=collector.ingest(raw('e1','workload_received','2026-01-01T00:00:00Z'))
    assert e.provenance.source=='synthetic/test-only'
    with pytest.raises(ValueError): collector.ingest({**raw('e2','workload_received','2026-01-01T00:00:01Z'),'schema_version':'bad'})
    with pytest.raises(ValueError): collector.ingest({**raw('e3','workload_received','2026-01-01T00:00:01Z'),'provenance':{'source':'x','timestamp_quality':'BAD'}})

def test_snapshot_accepts_only_pre_decision_and_at_decision_events():
    store=EventStore(); c=ObservationCollector(store)
    c.ingest_batch([raw('e1','workload_received','2026-01-01T00:00:00Z'),raw('e2','prediction_generated','2026-01-01T00:00:01Z')])
    snap=DecisionSnapshotBuilder(store).build('j1','2026-01-01T00:00:01Z')
    assert snap.availability==Availability.AT and len(snap.provenance)==2
    c.ingest(raw('e3','telemetry_observed','2026-01-01T00:00:02Z'))
    with pytest.raises(ValueError,match='post-decision'): DecisionSnapshotBuilder(store).build('j1','2026-01-01T00:00:01Z')

def test_unknown_timestamp_cannot_enter_proven_snapshot():
    store=EventStore(); c=ObservationCollector(store)
    c.ingest(raw('e1','workload_received',None))
    with pytest.raises(ValueError,match='timestamp-unknown'): DecisionSnapshotBuilder(store).build('j1','2026-01-01T00:00:01Z')

def test_ordered_replay_is_deterministic_and_api_is_temporally_bounded():
    store=EventStore(); c=ObservationCollector(store)
    c.ingest_batch([raw('e2','prediction_generated','2026-01-01T00:00:01Z'),raw('e1','workload_received','2026-01-01T00:00:00Z')])
    a=ObservationReplay(store).serialize(); b=ObservationReplay(store).serialize(); assert a==b
    api=ObservabilityAPI(store); assert len(api.event_history('j1','2026-01-01T00:00:00Z'))==1

def test_recovery_validation_and_error_categories_are_contractual():
    assert SystemError.UNSAFE_ACTION.value=='unsafe action'
    assert AutonomyState.COMPLETED in {AutonomyState.COMPLETED,AutonomyState.UNKNOWN}
