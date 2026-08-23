import json
from pathlib import Path
import pytest
from src.phase4.controlled_runtime import ControlledRuntime,RuntimeConfig,environment_identity,run_scenarios,SOURCE_ID,ENVIRONMENT_ID
from src.phase4.observability import PersistentEventStore,ObservationReplay,ObservabilityAPI

def test_successful_real_process_emits_lifecycle_and_telemetry(tmp_path):
    store=PersistentEventStore(tmp_path/'events.sqlite'); r=ControlledRuntime(store,RuntimeConfig(timeout_seconds=2,telemetry_interval_seconds=0.01)).run('success',{'mode':'cpu','duration_seconds':0.05})
    types=[e['event_type'] for e in r.events]
    assert r.status=='COMPLETED' and r.exit_code==0
    assert {'workload_received','workload_registered','execution_started','telemetry_observed','workload_completed'} <= set(types)
    assert all(e['provenance']['source']==SOURCE_ID for e in r.events)
    store.close()

def test_actual_nonzero_process_failure_is_recorded(tmp_path):
    store=PersistentEventStore(tmp_path/'events.sqlite'); r=ControlledRuntime(store,RuntimeConfig(timeout_seconds=2)).run('failure',{'mode':'fail'})
    assert r.status=='FAILED' and r.exit_code==7
    failures=[e for e in r.events if e['event_type']=='failure_detected']
    assert failures and failures[0]['payload']['failure_kind']=='NONZERO_EXIT'
    store.close()

def test_actual_timeout_terminates_process_and_records_timeout(tmp_path):
    store=PersistentEventStore(tmp_path/'events.sqlite'); r=ControlledRuntime(store,RuntimeConfig(timeout_seconds=0.05,telemetry_interval_seconds=0.01)).run('timeout',{'mode':'sleep','duration_seconds':2})
    assert r.status=='TIMEOUT'
    assert any(e['payload'].get('failure_kind')=='TIMEOUT' for e in r.events if e['event_type']=='failure_detected')
    store.close()

def test_restart_and_persistent_replay_are_identical(tmp_path):
    db=tmp_path/'events.sqlite'; store=PersistentEventStore(db); r=ControlledRuntime(store,RuntimeConfig(timeout_seconds=2)).run('success',{'mode':'success'}); before=ObservationReplay(store).serialize(); store.close()
    restarted=PersistentEventStore(db); assert ObservationReplay(restarted).serialize()==before; assert len(restarted.events(r.run_id))==len(r.events); restarted.close()

def test_environment_is_controlled_and_missing_cluster_state_is_explicit():
    env=environment_identity(); assert env['classification']=='CONTROLLED_RUNTIME'; assert env['project_owned'] is True; assert env['scheduler']=='UNAVAILABLE'; assert env['queue']=='UNAVAILABLE'; assert env['environment_id']==ENVIRONMENT_ID

def test_scenario_runner_produces_all_engineering_scenarios(tmp_path):
    result=run_scenarios(tmp_path); assert result['success']['status']=='COMPLETED'; assert result['failure']['status']=='FAILED'; assert result['timeout']['status']=='TIMEOUT'; assert result['_restart']['replay_equal'] is True
