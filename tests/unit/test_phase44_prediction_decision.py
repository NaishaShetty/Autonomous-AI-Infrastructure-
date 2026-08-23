from src.phase4.prediction import TelemetryRiskPredictor, extract_features
from src.phase4.decision import AbstentionAwareDecisionPolicy
from src.phase4.monitoring import MonitoringBaseline
from src.phase4.architecture import Prediction
from src.data_foundation.foundation import Provenance, TimestampQuality


def telemetry(ts, rss):
    return {'event_type': 'telemetry_observed', 'timestamp': ts, 'payload': {'process_rss_bytes': rss}}


def test_features_are_zero_for_empty_healthy_prefix():
    baseline = MonitoringBaseline()
    features = extract_features([], baseline, configured_timeout_seconds=1.0, run_start_iso='2026-01-01T00:00:00Z', at_time_iso='2026-01-01T00:00:00Z')
    assert features.rss_ratio == 0.0 and features.anomaly_rate == 0.0 and features.elapsed_ratio == 0.0


def test_rss_ratio_and_anomaly_rate_respond_to_over_threshold_samples():
    baseline = MonitoringBaseline(max_process_rss_bytes=1000)
    events = [telemetry('2026-01-01T00:00:00Z', 500), telemetry('2026-01-01T00:00:01Z', 2000)]
    features = extract_features(events, baseline, configured_timeout_seconds=None, run_start_iso='2026-01-01T00:00:00Z', at_time_iso='2026-01-01T00:00:01Z')
    assert features.rss_ratio == 1.0  # clipped at 1.0 even though raw ratio is 2.0
    assert features.anomaly_rate == 0.5  # 1 of 2 samples over threshold


def test_elapsed_ratio_grows_toward_configured_timeout():
    baseline = MonitoringBaseline()
    features = extract_features([], baseline, configured_timeout_seconds=10.0, run_start_iso='2026-01-01T00:00:00Z', at_time_iso='2026-01-01T00:00:05Z')
    assert features.elapsed_ratio == 0.5


def test_predictor_score_is_bounded_and_deterministic():
    predictor = TelemetryRiskPredictor(MonitoringBaseline(max_process_rss_bytes=1000))
    events = [telemetry('2026-01-01T00:00:00Z', 5000)]
    p1 = predictor.predict_from_events('job-1', events, configured_timeout_seconds=10.0, run_start_iso='2026-01-01T00:00:00Z', at_time_iso='2026-01-01T00:00:05Z')
    p2 = predictor.predict_from_events('job-1', events, configured_timeout_seconds=10.0, run_start_iso='2026-01-01T00:00:00Z', at_time_iso='2026-01-01T00:00:05Z')
    assert 0.0 <= p1.score <= 1.0
    assert p1.score == p2.score  # deterministic, not a trained/random model


def _prediction(score):
    return Prediction(prediction_id='p', job_id='j', snapshot_id='s', decision_time='2026-01-01T00:00:00Z', score=score, provenance=Provenance(source='test', timestamp_quality=TimestampQuality.EXACT))


def test_decision_policy_answers_on_low_risk():
    result = AbstentionAwareDecisionPolicy().decide(_prediction(0.05))
    assert result.decision == 'ANSWER'
    assert result.next_state == 'DIAGNOSING'


def test_decision_policy_abstains_on_high_risk():
    result = AbstentionAwareDecisionPolicy().decide(_prediction(0.95))
    assert result.decision == 'ABSTAIN'
    assert result.next_state == 'ABSTAINED'


def test_decision_policy_reviews_uncertain_band():
    result = AbstentionAwareDecisionPolicy().decide(_prediction(0.5))
    assert result.decision == 'REVIEW'
    assert result.next_state == 'ESCALATED'
