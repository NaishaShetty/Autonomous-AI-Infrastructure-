"""Phase 4.8, Priority 3D -- unit coverage for the one bounded 5-feature
extension attempted after the baseline evaluation methodology was
validated."""
from src.phase4.monitoring import MonitoringBaseline
from src.phase4.prediction_features_v2 import FEATURE_NAMES_V2, extract_features_v2, generate_corpus_v2
from src.phase4.prediction_training import SplitSeeds


def _telemetry(ts, rss):
    return {"event_type": "telemetry_observed", "timestamp": ts, "payload": {"process_rss_bytes": rss}}


def test_feature_names_v2_extends_the_original_four():
    assert FEATURE_NAMES_V2[:4] == ("rss_ratio", "anomaly_rate", "elapsed_ratio", "sample_count_ratio")
    assert FEATURE_NAMES_V2[4] == "rss_growth_rate"


def test_rss_growth_rate_is_zero_with_fewer_than_two_telemetry_samples():
    baseline = MonitoringBaseline()
    events = [_telemetry("2020-01-01T00:00:00Z", 1000)]
    features = extract_features_v2(events, baseline, 1.0, "2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z")
    assert features.rss_growth_rate == 0.0
    assert len(features.as_vector()) == 5


def test_rss_growth_rate_reflects_a_real_positive_delta_between_last_two_samples():
    baseline = MonitoringBaseline()
    events = [
        _telemetry("2020-01-01T00:00:00.000Z", 1000),
        _telemetry("2020-01-01T00:00:00.100Z", 1000 + baseline.max_process_rss_bytes // 2),
    ]
    features = extract_features_v2(events, baseline, 1.0, "2020-01-01T00:00:00.000Z", "2020-01-01T00:00:00.100Z")
    assert features.rss_growth_rate > 0.0


def test_generate_corpus_v2_produces_five_dimensional_feature_rows():
    seeds = SplitSeeds(train=range(0, 30), validation=range(2000, 2010), test=range(4000, 4010))
    corpus = generate_corpus_v2(seeds, timeout_seconds=0.15)
    assert corpus["train"]
    for row in corpus["train"][:5]:
        assert len(row.features) == 5
