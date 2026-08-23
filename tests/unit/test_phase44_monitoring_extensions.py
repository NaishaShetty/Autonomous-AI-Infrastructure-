from src.phase4.monitoring import MonitoringEngine, MonitoringBaseline, FailureDetector, DetectionEvaluator


def ev(i, t, ts, rid='r1', payload=None):
    return {'event_id': i, 'event_type': t, 'timestamp': ts, 'job_id': rid, 'workload_id': 'w1', 'environment_id': 'env1', 'payload': payload or {}, 'provenance': {'source': 'test', 'source_record_id': i, 'timestamp_quality': 'EXACT'}}


def test_network_error_is_detected_as_network_failure_class():
    events = [ev('f', 'failure_detected', '2026-01-01T00:00:00Z', payload={'failure_kind': 'NETWORK_ERROR', 'exit_code': 9})]
    failure_event = FailureDetector().detect(events[0])
    assert failure_event.failure_class == 'NETWORK_FAILURE'


def test_unsupported_failure_kind_still_raises():
    import pytest
    with pytest.raises(ValueError):
        FailureDetector().detect(ev('f', 'failure_detected', '2026-01-01T00:00:00Z', payload={'failure_kind': 'GPU_ECC_ERROR'}))


def test_sustained_anomaly_escalates_to_high_severity():
    baseline = MonitoringBaseline(max_process_rss_bytes=100)
    events = [ev(f't{i}', 'telemetry_observed', f'2026-01-01T00:00:0{i}Z', payload={'process_rss_bytes': 1000}) for i in range(4)]
    engine = MonitoringEngine(baseline)
    engine.process(events)
    severities = [a['severity'] for a in engine.anomalies]
    assert severities[:2] == ['MEDIUM', 'MEDIUM']
    assert severities[2] == 'HIGH' and severities[3] == 'HIGH'


def test_single_anomaly_stays_medium():
    baseline = MonitoringBaseline(max_process_rss_bytes=100)
    events = [ev('t0', 'telemetry_observed', '2026-01-01T00:00:00Z', payload={'process_rss_bytes': 1000})]
    engine = MonitoringEngine(baseline)
    engine.process(events)
    assert engine.anomalies[0]['severity'] == 'MEDIUM'


def test_network_failure_is_no_longer_in_unsupported_classes_but_gpu_and_scheduler_still_are():
    metrics = DetectionEvaluator().evaluate({}, [], {})
    assert 'NETWORK_FAILURE' not in metrics['unsupported_classes']
    assert 'GPU_FAILURE' in metrics['unsupported_classes']
    assert 'SCHEDULER_FAILURE' in metrics['unsupported_classes']
