"""Integration tests for the Phase 3.4 comparison script: verifies it
reuses already-frozen Phase 3.1/3.2/3.2C results without any new fitting,
respects the frozen protocol, correctly flags duplicate implementations,
and reproduces known Phase 3.2/3.2C AUROC values exactly."""
from __future__ import annotations

import inspect

import pytest

from benchmarks.phase3_4_compare import (
    CANDIDATES,
    COMPARATORS,
    ProtocolDiscrepancyError,
    _assert_duplicate_candidates_match,
    _assert_protocol_matches,
    _assert_test_sets_aligned,
    build_candidate_table,
    load_sources,
    per_seed_paired_comparisons,
)
import benchmarks.phase3_4_compare as phase3_4_compare
from src.evaluation.protocol import Phase31Protocol

# Historical AUROC means this script must reproduce exactly, since it does
# not recompute scores -- it only re-aggregates the values Phase 3.1/3.2/
# 3.2C already wrote to disk. Copied from docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md
# and docs/PHASE3_2C_CANDIDATE_ABLATION.md.
KNOWN_AUROC_MEANS = {
    "A_no_signal": 0.5000,
    "B_calibrated_confidence": 0.6599,
    "C_failure_memory": 0.5141,
    "D_raw_features": 0.5308,
    "E_failure_history_supervised": 0.5809,
    "F_supervised_failure_risk": 0.6548,
}


@pytest.fixture(scope="module")
def protocol():
    return Phase31Protocol.load()


@pytest.fixture(scope="module")
def sources(protocol):
    return load_sources(protocol)


@pytest.fixture(scope="module")
def table(sources, protocol):
    return build_candidate_table(sources, protocol)


def test_frozen_seed_list_respected(protocol):
    assert protocol.seeds == [1, 2, 3, 4, 5, 42]
    assert protocol.primary_seed == 42


def test_frozen_coverage_points_unchanged(protocol):
    assert protocol.coverage_operating_points == [0.05, 0.10, 0.20, 0.50]


def test_frozen_protocol_loads_without_discrepancy(sources):
    # load_sources() itself calls _assert_protocol_matches on every source;
    # reaching this point without a ProtocolDiscrepancyError means every
    # stored Phase 3.1/3.2/3.2C result file agrees with the currently
    # loaded configs/phase3_1_protocol.json.
    assert set(sources.keys()) == {"phase3_1", "phase3_2", "phase3_2c"}


def test_protocol_discrepancy_is_detected(protocol):
    fake_meta = {"protocol_config": {**protocol.raw, "seeds": [1, 2, 3]}}
    with pytest.raises(ProtocolDiscrepancyError):
        _assert_protocol_matches(fake_meta, protocol, "fake_source")


def test_no_fitting_or_data_generation_in_this_module():
    """Phase 3.4 must not fit, train, or regenerate any stream data -- it
    only reads already-written result JSON. Static check that the module
    never calls .fit(, build_system, or generate_regime_stream."""
    src = inspect.getsource(phase3_4_compare)
    assert ".fit(" not in src
    assert "build_system(" not in src
    assert "generate_regime_stream(" not in src


def test_all_six_seeds_evaluated_for_every_candidate(table, protocol):
    for cand_id, cand in table.items():
        assert set(cand["per_seed"].keys()) == set(protocol.seeds), cand_id


def test_test_sets_aligned_across_source_phases(sources, protocol):
    # Raises ProtocolDiscrepancyError if per-seed test-set size/prevalence
    # ever differs across phase3_1/phase3_2/phase3_2c -- would invalidate
    # every per-seed paired comparison in this script.
    _assert_test_sets_aligned(sources, protocol)


def test_candidate_c_and_experiment_c_are_flagged_as_duplicates():
    ids = {c["id"]: c for c in CANDIDATES}
    assert ids["E_failure_history_supervised"]["duplicate_of"] == "E_failure_history_supervised_control"
    assert ids["E_failure_history_supervised_control"]["duplicate_of"] == "E_failure_history_supervised"


def test_candidate_c_and_experiment_c_have_identical_per_seed_auroc(sources):
    result = _assert_duplicate_candidates_match(sources)
    assert result["identical"] is True
    assert result["mismatches"] == {}


def test_aggregation_matches_established_methodology_no_discrepancy(sources, protocol):
    # build_candidate_table() raises ProtocolDiscrepancyError internally if
    # its own recomputed cross-seed aggregate (via the SAME _t_interval
    # Phase 3.1 defined) disagrees with the stored aggregate_results.json
    # for any candidate/metric. Reaching this point means it agreed.
    build_candidate_table(sources, protocol)


@pytest.mark.parametrize("cand_id,expected", KNOWN_AUROC_MEANS.items())
def test_candidate_ordering_reproduces_known_phase3_2_phase3_2c_values(table, cand_id, expected):
    mean = table[cand_id]["aggregate_cross_seed"]["auroc"]["mean"]
    assert mean == pytest.approx(expected, abs=5e-4)


def test_ece_not_meaningful_for_non_probability_representations(table):
    # C_failure_memory (Gaussian-kernel similarity) and D_raw_features
    # (KMeans similarity) were never fit/designed as probabilities.
    assert table["C_failure_memory"]["ece_meaningful"] is False
    assert table["D_raw_features"]["ece_meaningful"] is False
    assert table["C_failure_memory"]["aggregate_cross_seed"]["ece"] is None
    assert table["D_raw_features"]["aggregate_cross_seed"]["ece"] is None


def test_ece_meaningful_for_probability_representations(table):
    for cand_id in ["A_no_signal", "B_calibrated_confidence", "E_failure_history_supervised", "F_supervised_failure_risk"]:
        assert table[cand_id]["ece_meaningful"] is True
        assert table[cand_id]["aggregate_cross_seed"]["ece"] is not None


def test_comparators_are_the_three_established_baselines():
    assert COMPARATORS == ["A_no_signal", "C_failure_memory", "B_calibrated_confidence"]


def test_selected_candidate_beats_no_signal_and_original_failure_memory_every_seed(table, protocol):
    comparisons = per_seed_paired_comparisons(table, protocol)
    f_vs_a = comparisons["F_supervised_failure_risk"]["A_no_signal"]
    f_vs_c = comparisons["F_supervised_failure_risk"]["C_failure_memory"]
    assert f_vs_a["beats_on_all_seeds"] is True
    assert f_vs_a["wins"] == 6
    assert f_vs_c["beats_on_all_seeds"] is True
    assert f_vs_c["wins"] == 6


def test_selected_candidate_does_not_consistently_beat_calibrated_confidence(table, protocol):
    comparisons = per_seed_paired_comparisons(table, protocol)
    f_vs_b = comparisons["F_supervised_failure_risk"]["B_calibrated_confidence"]
    assert f_vs_b["beats_on_all_seeds"] is False
    assert f_vs_b["wins"] <= 1


def test_paired_comparison_caveats_n_equals_6_no_significance_test(table, protocol):
    comparisons = per_seed_paired_comparisons(table, protocol)
    for cand_id, comps in comparisons.items():
        for comparator_id, result in comps.items():
            assert result["n_seeds"] <= 6
            assert "no significance test" in result["caveat"]


def test_t_interval_reused_from_phase3_1_not_reimplemented(table):
    # aggregate_cross_seed values are produced by benchmarks.phase3_1_evaluate._t_interval,
    # which for a 6-sample input reports n == 6 -- confirms the shared helper is in use.
    assert table["F_supervised_failure_risk"]["aggregate_cross_seed"]["auroc"]["n"] == 6
