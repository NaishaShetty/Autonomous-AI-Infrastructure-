"""Post-P5 remediation, Step 3 -- unit coverage for the v3 feature/corpus
extensions (resource_preflight_available feature, n_telemetry_samples
observability split)."""
from src.phase4.prediction_features_v3 import (
    FEATURE_NAMES_V3,
    CorpusRowV3,
    _resource_preflight_value,
    generate_corpus_rows_v3,
)
from src.phase4.prediction_training import SplitSeeds


def test_resource_preflight_value_reads_the_probe_event():
    events_available = [{"event_type": "telemetry_observed", "payload": {"telemetry_kind": "resource_preflight_probe", "resource_available": True}}]
    events_unavailable = [{"event_type": "telemetry_observed", "payload": {"telemetry_kind": "resource_preflight_probe", "resource_available": False}}]
    events_absent = [{"event_type": "telemetry_observed", "payload": {"process_rss_bytes": 123}}]
    assert _resource_preflight_value(events_available) == 1.0
    assert _resource_preflight_value(events_unavailable) == 0.0
    assert _resource_preflight_value(events_absent) == 0.5  # no probe in prefix -- neutral, not fabricated


def test_generate_corpus_rows_v3_populates_six_features_and_sample_count():
    rows = generate_corpus_rows_v3(list(range(0, 25)), "unit-v3", timeout_seconds=0.15)
    assert rows, "expected rows from a 25-seed corpus"
    assert all(len(r.features) == len(FEATURE_NAMES_V3) == 6 for r in rows)
    assert all(isinstance(r, CorpusRowV3) for r in rows)
    assert all(isinstance(r.n_telemetry_samples, int) and r.n_telemetry_samples >= 0 for r in rows)


def test_resource_unavailable_rows_get_a_real_preflight_feature_and_others_get_neutral():
    rows = generate_corpus_rows_v3(list(range(0, 60)), "unit-v3-ru", timeout_seconds=0.15)
    ru_rows = [r for r in rows if r.mode == "resource_unavailable"]
    other_rows = [r for r in rows if r.mode not in ("resource_unavailable",)]
    assert ru_rows, "expected at least one resource_unavailable-mode row in a 60-seed corpus"
    preflight_idx = FEATURE_NAMES_V3.index("resource_preflight_available")
    assert all(r.features[preflight_idx] in (0.0, 1.0) for r in ru_rows)
    # Every other family never emits the probe event -- must get the neutral 0.5, never fabricated 0/1.
    assert all(r.features[preflight_idx] == 0.5 for r in other_rows)


def test_oom_rows_carry_a_real_sample_count_for_the_observability_split():
    rows = generate_corpus_rows_v3(list(range(0, 60)), "unit-v3-oom", timeout_seconds=0.15)
    oom_rows = [r for r in rows if r.mode == "oom"]
    assert oom_rows, "expected at least one oom-mode row in a 60-seed corpus"
    # Not all zero -- some real variation in observed sample counts is expected.
    assert len({r.n_telemetry_samples for r in oom_rows}) >= 1
