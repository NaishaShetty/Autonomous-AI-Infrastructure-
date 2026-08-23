import copy
import pytest
from src.phase4.monitoring import MonitoringState,MonitoringStateMachine,MonitoringBaseline,AnomalyDetector,FailureDetector,MonitoringEngine,DetectionEvaluator

def ev(eid,typ,ts='2026-01-01T00:00:00Z',rid='r1',payload=None):
    return {'event_id':eid,'event_type':typ,'timestamp':ts,'job_id':rid,'workload_id':'w1','environment_id':'controlled-runtime-local-environment','payload':payload or {},'provenance':{'source':'project-owned-controlled-runtime','source_record_id':eid,'timestamp_quality':'EXACT'}}

def test_monitoring_state_machine_rejects_arbitrary_transition():
    s=MonitoringStateMachine(); s.transition(MonitoringState.HEALTHY); s.transition(MonitoringState.ANOMALOUS); s.transition(MonitoringState.FAILED)
    with pytest.raises(ValueError): s.transition(MonitoringState.HEALTHY)

def test_normal_lifecycle_is_healthy_and_not_failed():
    result=MonitoringEngine().process([ev('1','execution_started'),ev('2','workload_completed','2026-01-01T00:00:01Z')])
    assert result['r1']['current_state']=='HEALTHY'

def test_high_rss_is_anomaly_not_failure():
    e=ev('1','telemetry_observed',payload={'process_rss_bytes':1024*1024*1024})
    engine=MonitoringEngine(); engine.process([e]); assert len(engine.anomalies)==1; assert not engine.failures; assert engine.states['r1']['current_state']=='ANOMALOUS'

def test_nonzero_exit_and_timeout_are_confirmed_structured_failures():
    fd=FailureDetector(); a=fd.detect(ev('1','failure_detected',payload={'failure_kind':'NONZERO_EXIT','exit_code':7})); b=fd.detect(ev('2','failure_detected','2026-01-01T00:00:01Z','r2',{'failure_kind':'TIMEOUT'}))
    assert a.failure_class=='PROCESS_NONZERO_EXIT' and a.certainty=='CONFIRMED'; assert b.failure_class=='PROCESS_TIMEOUT'

def test_unknown_or_unsupported_failure_is_not_silently_classified():
    with pytest.raises(ValueError): FailureDetector().detect(ev('1','failure_detected',payload={'failure_kind':'GPU_FAILURE'}))

def test_future_event_cannot_change_earlier_monitoring_decision():
    early=[ev('1','execution_started')]; later=early+[ev('2','failure_detected','2026-01-01T00:00:05Z',payload={'failure_kind':'NONZERO_EXIT'})]
    before=MonitoringEngine(); before.process(early,at_or_before='2026-01-01T00:00:00Z'); after=MonitoringEngine(); after.process(later,at_or_before='2026-01-01T00:00:00Z')
    assert before.states==after.states and before.failures==after.failures

def test_monitoring_replay_is_deterministic():
    events=[ev('1','execution_started'),ev('2','failure_detected','2026-01-01T00:00:01Z',payload={'failure_kind':'NONZERO_EXIT','exit_code':7})]
    e=MonitoringEngine(); assert e.replay(events)==e.replay(events)

def test_detection_metrics_are_explicit_and_unsupported_classes_are_not_scored():
    metrics=DetectionEvaluator().evaluate({'r1':'COMPLETED','r2':'FAILED'},[{'run_id':'r2'}],{})
    assert metrics['true_positives']==1 and metrics['false_positives']==0 and 'GPU_FAILURE' in metrics['unsupported_classes']
