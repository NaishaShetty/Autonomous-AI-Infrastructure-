from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.run_counterfactual_generalization import PROTOCOL, run_all, write_outputs


def test_protocol_has_three_manifestations_and_hides_latent_state():
    for mechanism, spec in PROTOCOL["latent_mechanisms"].items():
        assert len(spec["training_manifestations"]) == 2
        assert spec["evaluation_manifestation"]["id"] not in spec["training_manifestations"]
        for features in spec["training_manifestations"].values():
            assert "latent_mechanism" not in features
            assert "optimal_action" not in features
        assert "latent_mechanism" not in spec["evaluation_manifestation"]["features"]


def test_counterfactual_pair_is_same_observation_with_only_memory_changed():
    result = run_all()
    pair = result["comparisons"]["C7_counterfactual_pair"]
    assert pair["only_manipulated_variable"] == "memory_availability"
    assert len(pair["same_observation_ids"]) == 15
    assert pair["same_seeds"] == PROTOCOL["seed_list"]
    assert pair["training_memory_success"] >= pair["no_memory_success"]


def test_unseen_manifestations_are_never_in_training_memory():
    result = run_all()
    unseen = {spec["evaluation_manifestation"]["id"] for spec in PROTOCOL["latent_mechanisms"].values()}
    for row in result["records"]:
        assert row["latent_mechanism_exposed_to_runtime"] is False
        assert row["evaluation_manifestation_id"] not in row["memory_event_ids"]
        assert row["evaluation_manifestation_id"] not in unseen or row["evaluation_manifestation_in_memory"] is False


def test_baselines_are_present_and_nearest_neighbor_is_explicit():
    result = run_all()
    baselines = {row["baseline"] for row in result["records"]}
    assert baselines == set(PROTOCOL["baselines"])
    nearest = [row for row in result["records"] if row["baseline"] == "B1_nearest_neighbor"]
    assert nearest
    assert all("distance_to_training" in row for row in nearest)


def test_exact_removed_and_unseen_generalization_are_measured_separately():
    result = run_all()
    comparison = result["comparisons"]["C1_vs_C3_exact_removed"]
    assert comparison["training_memory_success"] is not None
    assert comparison["exact_removed_success"] is not None
    assert "B2_memory_planner__C3_exact_memory_removed" in result["summaries"]


def test_negative_transfer_and_safety_have_zero_executed_unsafe_actions():
    result = run_all()
    negative = result["comparisons"]["negative_transfer"]["B2_memory_planner"]
    safety = result["comparisons"]["safety"]["B2_memory_planner"]
    assert negative["episode_count"] > 0
    assert safety["unsafe_action_rate"] == 0.0
    assert safety["abstention_rate"] == 1.0


def test_distance_ladder_is_declared_and_uncertainty_does_not_improve_with_distance():
    result = run_all()
    distances = result["distance_summary"]
    assert list(distances) == ["D0_exact", "D1_near", "D2_moderate", "D3_large", "D4_unrelated"]
    assert distances["D4_unrelated"]["mean_relevance_recall"] == 0.0
    assert distances["D4_unrelated"]["mean_diagnosis_uncertainty"] >= distances["D0_exact"]["mean_diagnosis_uncertainty"]


def test_training_event_ids_are_deterministic_and_no_uuid_is_used_in_result_rows():
    result = run_all()
    ids = [event_id for row in result["records"] for event_id in row["memory_event_ids"]]
    assert ids
    assert all(event_id.startswith("cf-") for event_id in ids)
    assert all("event_id" not in row for row in result["records"])


def test_counterfactual_outputs_are_byte_reproducible(tmp_path):
    result = run_all()
    original = tmp_path / "a"
    second = tmp_path / "b"
    original.mkdir()
    second.mkdir()
    import scripts.run_counterfactual_generalization as experiment
    old_results = experiment.RESULTS
    try:
        experiment.RESULTS = original
        write_outputs(result)
        experiment.RESULTS = second
        write_outputs(run_all())
    finally:
        experiment.RESULTS = old_results
    for filename in ("protocol.json", "manifest.json", "results.json", "summary.json", "report.md"):
        assert hashlib.sha256((original / filename).read_bytes()).digest() == hashlib.sha256((second / filename).read_bytes()).digest()
    assert sorted(path.name for path in (original / "per_seed").iterdir()) == sorted(f"seed_{seed}.json" for seed in PROTOCOL["seed_list"])
