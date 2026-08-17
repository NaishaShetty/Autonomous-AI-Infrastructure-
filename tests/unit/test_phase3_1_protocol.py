from src.evaluation.protocol import Phase31Protocol


def test_protocol_loads_from_frozen_config():
    protocol = Phase31Protocol.load()
    assert protocol.primary_seed in protocol.seeds
    assert len(protocol.seeds) == len(set(protocol.seeds))  # no duplicate seeds
    assert all(0.0 < c <= 1.0 for c in protocol.coverage_operating_points)
    assert protocol.bootstrap.n_resamples > 0
    assert 0.0 < protocol.bootstrap.confidence_level < 1.0
    assert len(protocol.regime_sizes) >= 5


def test_protocol_matches_phase2_defaults_unchanged():
    """Regression guard: Phase 3.1 must reproduce, not redesign, the Phase 2
    benchmark. If this fails, someone changed the frozen dataset config."""
    from src.pipeline_builder import DEFAULT_REGIME_SIZES

    protocol = Phase31Protocol.load()
    assert protocol.regime_sizes == DEFAULT_REGIME_SIZES
    assert protocol.n_clusters == 3
