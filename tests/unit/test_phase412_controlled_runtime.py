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


def test_resource_unavailable_gets_a_real_preflight_probe_before_the_subprocess_runs(tmp_path):
    """P3-W2 (post-P5 remediation): resource_unavailable had NO telemetry
    window at all -- the outcome is decided within microseconds of process
    start. The parent now performs a real, independently-timed pre-flight
    bind() probe on the same port before the child is even spawned, so a
    genuine decision-time signal exists. Verify it fires, is correctly
    timestamped before execution_started, and honestly reflects real port
    contention state (both the free and the occupied case)."""
    import socket as _socket
    store = PersistentEventStore(tmp_path / 'events.sqlite')
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=2, telemetry_interval_seconds=0.01))

    # Case 1: port genuinely free -> probe must say available.
    free_port = 48765
    result_ok = runtime.run('resource_unavailable', {'mode': 'resource_unavailable', 'port': free_port}, workload_id='w-free')
    probes_ok = [e for e in result_ok.events if e['payload'].get('telemetry_kind') == 'resource_preflight_probe']
    assert len(probes_ok) == 1
    assert probes_ok[0]['payload']['resource_available'] is True
    exec_started_ts = next(e['timestamp'] for e in result_ok.events if e['event_type'] == 'execution_started')
    assert probes_ok[0]['timestamp'] <= exec_started_ts  # real precursor: strictly before/at execution start

    # Case 2: port genuinely occupied by a separate real socket -> probe must say unavailable.
    occupied_port = 48766
    runtime.occupy_external_resource(occupied_port)
    result_bad = runtime.run('resource_unavailable', {'mode': 'resource_unavailable', 'port': occupied_port}, workload_id='w-occupied')
    probes_bad = [e for e in result_bad.events if e['payload'].get('telemetry_kind') == 'resource_preflight_probe']
    assert len(probes_bad) == 1
    assert probes_bad[0]['payload']['resource_available'] is False
    assert result_bad.exit_code == 14  # RESOURCE_UNAVAILABLE exit code -- probe matches the real outcome
    runtime.close()
    store.close()


def test_telemetry_reports_real_process_rss_cross_platform(tmp_path):
    """Regression test (post-P5 remediation, P3-W1/P3-W2): telemetry
    collection used to read /proc/{pid}/status directly, a POSIX-only path
    that silently never exists on Windows -- so process_rss_bytes (and
    every downstream feature derived from it: rss_ratio, anomaly_rate,
    rss_growth_rate) was `None` for every telemetry sample on any Windows
    host, with no error raised. A workload that allocates real, measurable
    memory (well above noise) must show at least one telemetry sample with
    a real positive process_rss_bytes on THIS platform, whatever it is."""
    store = PersistentEventStore(tmp_path / 'events.sqlite')
    runtime = ControlledRuntime(store, RuntimeConfig(timeout_seconds=2, telemetry_interval_seconds=0.01))
    result = runtime.run('oom', {'mode': 'oom', 'alloc_mb': 200, 'limit_mb': 4096})
    telemetry = [e for e in result.events if e['event_type'] == 'telemetry_observed']
    assert telemetry, "expected at least one telemetry_observed event"
    rss_values = [e['payload'].get('process_rss_bytes') for e in telemetry]
    assert any(isinstance(v, (int, float)) and v > 0 for v in rss_values), (
        f"process_rss_bytes was never a real positive value across {len(telemetry)} samples: {rss_values}"
    )
    store.close()
