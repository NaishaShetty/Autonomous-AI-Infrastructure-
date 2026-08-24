"""Phase 4.5b -- unit coverage for AgentUncertaintyPredictor: the
"recognize when it's likely wrong" mechanism for actual AI/ML agent output.
"""
from src.phase4.prediction import AgentUncertaintyPredictor


def _sample_event(idx, running_rate):
    return {
        "event_type": "telemetry_observed",
        "payload": {"telemetry_kind": "agent_self_consistency_sample", "sample_index": idx, "running_agreement_rate": running_rate},
    }


def test_score_is_one_minus_the_most_recent_running_agreement_rate():
    predictor = AgentUncertaintyPredictor()
    events = [_sample_event(0, 1.0), _sample_event(1, 1.0), _sample_event(2, 0.667)]
    prediction = predictor.predict_from_events(
        job_id="j1", events_prefix=events, configured_timeout_seconds=None,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:01Z",
    )
    assert abs(prediction.score - (1.0 - 0.667)) < 1e-9
    assert prediction.provenance.extraction_method == "self_consistency_disagreement_rate"


def test_no_samples_observed_yet_means_lowest_honest_risk():
    predictor = AgentUncertaintyPredictor()
    prediction = predictor.predict_from_events(
        job_id="j1", events_prefix=[], configured_timeout_seconds=None,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:01Z",
    )
    assert prediction.score == 0.0


def test_ignores_process_telemetry_events_and_only_reads_agent_samples():
    predictor = AgentUncertaintyPredictor()
    events = [
        {"event_type": "telemetry_observed", "payload": {"process_rss_bytes": 999999999}},  # no telemetry_kind marker
        _sample_event(0, 0.4),
    ]
    prediction = predictor.predict_from_events(
        job_id="j1", events_prefix=events, configured_timeout_seconds=None,
        run_start_iso="2026-01-01T00:00:00Z", at_time_iso="2026-01-01T00:00:01Z",
    )
    assert abs(prediction.score - 0.6) < 1e-9
