from __future__ import annotations

from pathlib import Path

from src.runtime.components import SimulatedRecoveryExecutor

from scripts.run_generalization import PROTOCOL, run, summarize


def test_generalization_protocol_declares_multiple_seeds_and_is_versioned():
    assert PROTOCOL["protocol_version"] == "runtime-generalization-v1"
    assert len(PROTOCOL["seed_list"]) >= 3
    assert PROTOCOL["simulator_version"] == "simulator-v2"
    assert PROTOCOL["relevance_threshold"] == 0.5


def test_stochastic_executor_reproduces_for_same_seed():
    probabilities = {"failure": {"retry": 0.5}}
    first = SimulatedRecoveryExecutor(outcome_probabilities=probabilities, seed=19)
    second = SimulatedRecoveryExecutor(outcome_probabilities=probabilities, seed=19)
    assert [first._rng.random() for _ in range(8)] == [second._rng.random() for _ in range(8)]


def test_related_memory_retrieves_relevant_context_without_exact_replay():
    rows = run("C1_relevant_memory")
    summary = summarize(rows)
    assert summary["mean_relevant_retrieval_count"] > 0
    assert summary["mean_relevance_recall"] == 1.0
    assert any(row["match_mode"] == "related" for row in rows)
    assert any(row["retrieved_failure_classes"] for row in rows)


def test_irrelevant_memory_is_retrieved_but_not_used_as_relevant_evidence():
    summary = summarize(run("C2_irrelevant_memory"))
    assert summary["mean_retrieval_count"] > 0
    assert summary["mean_relevant_retrieval_count"] == 0
    assert summary["mean_relevance_recall"] == 0.0


def test_conflicting_memories_prefer_abstention_over_latest_memory():
    summary = summarize(run("C3_conflicting_memory"))
    assert summary["abstention_rate"] == 1.0
    assert summary["unsafe_action_rate"] == 0.0


def test_negative_experience_avoids_failed_retry_and_replans_boundedly():
    summary = summarize(run("C4_negative_experience"))
    assert summary["mean_relevant_retrieval_count"] > 0
    assert summary["action_counts"].get("retry", 0) == 0
    assert summary["multi_step_rate"] > 0
    assert summary["mean_recovery_attempts"] <= PROTOCOL["max_recovery_attempts"]


def test_safety_conflict_rejects_historically_successful_unsafe_action():
    summary = summarize(run("C5_safety_conflict"))
    assert summary["abstention_rate"] == 1.0
    assert summary["unsafe_action_rate"] == 0.0


def test_multi_step_recovery_is_bounded_and_records_failed_first_attempts():
    summary = summarize(run("C6_multi_step"))
    assert summary["multi_step_rate"] > 0
    assert summary["failed_first_attempt_rate"] > 0
    assert summary["mean_recovery_attempts"] <= PROTOCOL["max_recovery_attempts"]


def test_exact_and_related_results_are_reported_separately():
    exact = summarize(run("C1_relevant_memory", mode="exact"))
    related = summarize(run("C1_relevant_memory", mode="related"))
    assert exact["episode_count"] == related["episode_count"]
    assert exact["mean_relevance_recall"] == 1.0
    assert related["mean_relevance_recall"] == 1.0
