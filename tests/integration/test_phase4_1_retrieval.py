"""Integration tests for Phase 4.1: runs the actual leakage-audit checks
(not a re-description) plus store/retrieval behavior against the real
Phase 4.0 dataset. Mirrors tests/integration/test_phase4_0_episodic.py
and tests/integration/test_phase3_6_leakage.py's pattern."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.data.synthetic import FEATURE_NAMES
from src.experience.schema import DecisionTimeQuery, experience_from_episode_record
from src.experience.store import ExperienceStore, build_store_from_episode_records
from src.storage.repository import EventRepository

from benchmarks.phase4_1_leakage_audit import (
    check_decision_time_query_type_excludes_ground_truth,
    check_no_test_or_validation_row_reachable_from_store,
    check_retrieval_on_empty_store_returns_empty_not_error,
    check_store_build_is_deterministic,
    check_store_contains_only_failures,
    check_store_contains_only_train_split,
)

ROOT = Path(__file__).resolve().parents[2]
PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"


def _require_phase4_0_data():
    path = PHASE4_0_DIR / "episodes.json"
    if not path.exists():
        pytest.skip("Phase 4.0 dataset not generated; run benchmarks/phase4_0_generate_episodes.py first")
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    records = json.loads(path.read_text())
    return records, manifest["content_hash_sha256"]


def test_store_contains_only_train_split():
    records, dataset_hash = _require_phase4_0_data()
    assert check_store_contains_only_train_split(records, dataset_hash)["passed"]


def test_store_contains_only_failures():
    records, dataset_hash = _require_phase4_0_data()
    assert check_store_contains_only_failures(records, dataset_hash)["passed"]


def test_decision_time_query_type_excludes_ground_truth():
    assert check_decision_time_query_type_excludes_ground_truth()["passed"]


def test_store_build_is_deterministic():
    records, dataset_hash = _require_phase4_0_data()
    assert check_store_build_is_deterministic(records, dataset_hash)["passed"]


def test_no_validation_or_test_row_reachable_from_store():
    records, dataset_hash = _require_phase4_0_data()
    assert check_no_test_or_validation_row_reachable_from_store(records, dataset_hash)["passed"]


def test_retrieval_on_empty_store_returns_empty_not_error():
    assert check_retrieval_on_empty_store_returns_empty_not_error()["passed"]


def test_full_audit_all_passed():
    report_path = ROOT / "experiments" / "results" / "phase4_1" / "leakage_audit.json"
    if not report_path.exists():
        subprocess.run(["python", "benchmarks/phase4_1_leakage_audit.py"], cwd=ROOT, check=True)
    report = json.loads(report_path.read_text())
    assert report["all_passed"] is True


def test_similarity_retrieval_prefers_closer_context():
    """Behavioral sanity check: given two stored experiences, one with a
    context identical to the query and one far away, similarity retrieval
    at k=1 must return the identical one -- not a tautology (random/
    recency baselines would not reliably do this)."""
    store = ExperienceStore(FEATURE_NAMES)
    near_record = {
        "step": 0, "occurrence_ordinal": 0, "sample_index_in_occurrence": 0,
        "workload_id": "w", "condition_id": "clean", "is_novel_combo": False, "split": "train",
        "occurrence_count_for_combo": 1,
        "context": {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0},
        "true_label": 1, "predicted_label": 0, "confidence": 0.5, "b_risk_score": 0.5,
        "tier": "HIGH", "decision": "ABSTAIN", "is_failure": True, "outcome": "INCORRECT",
        "diagnosed_cause": "clean", "recovery_attempted": False, "recovery_action": None,
        "recovery_outcome": None, "recovery_correct": None,
    }
    far_record = {**near_record, "step": 1, "context": {"f1": 5.0, "f2": 5.0, "f3": 5.0, "f4": 5.0, "f5": 5.0}, "confidence": 0.9}
    store.add(experience_from_episode_record(near_record, "v", "hash"))
    store.add(experience_from_episode_record(far_record, "v", "hash"))
    store.fit_embedder()

    query = DecisionTimeQuery(context={"f1": 0.01, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0}, confidence=0.5, workload_id="w", tier="HIGH", diagnosed_cause="clean")
    retrieved = store.retrieve_similarity(query, k=1)
    assert len(retrieved) == 1
    assert retrieved[0].event.context["f1"] == 0.0  # the near record, not the far one


def test_recency_retrieval_returns_most_recent_step_first():
    store = ExperienceStore(FEATURE_NAMES)
    base = {
        "occurrence_ordinal": 0, "sample_index_in_occurrence": 0,
        "workload_id": "w", "condition_id": "clean", "is_novel_combo": False, "split": "train",
        "occurrence_count_for_combo": 1,
        "context": {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0},
        "true_label": 1, "predicted_label": 0, "confidence": 0.5, "b_risk_score": 0.5,
        "tier": "HIGH", "decision": "ABSTAIN", "is_failure": True, "outcome": "INCORRECT",
        "diagnosed_cause": "clean", "recovery_attempted": False, "recovery_action": None,
        "recovery_outcome": None, "recovery_correct": None,
    }
    for step in [3, 1, 7, 2]:
        store.add(experience_from_episode_record({**base, "step": step}, "v", "hash"))
    query = DecisionTimeQuery(context=base["context"], confidence=0.5, workload_id="w", tier="HIGH", diagnosed_cause="clean")
    retrieved = store.retrieve_recency(query, k=2)
    assert [e.provenance.step for e in retrieved] == [7, 3]


def test_random_retrieval_is_deterministic_given_seed():
    store = ExperienceStore(FEATURE_NAMES)
    base = {
        "occurrence_ordinal": 0, "sample_index_in_occurrence": 0,
        "workload_id": "w", "condition_id": "clean", "is_novel_combo": False, "split": "train",
        "occurrence_count_for_combo": 1,
        "context": {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0},
        "true_label": 1, "predicted_label": 0, "confidence": 0.5, "b_risk_score": 0.5,
        "tier": "HIGH", "decision": "ABSTAIN", "is_failure": True, "outcome": "INCORRECT",
        "diagnosed_cause": "clean", "recovery_attempted": False, "recovery_action": None,
        "recovery_outcome": None, "recovery_correct": None,
    }
    for step in range(10):
        store.add(experience_from_episode_record({**base, "step": step}, "v", "hash"))
    query = DecisionTimeQuery(context=base["context"], confidence=0.5, workload_id="w", tier="HIGH", diagnosed_cause="clean")
    a = [e.event.event_id for e in store.retrieve_random(query, k=3, seed=7)]
    b = [e.event.event_id for e in store.retrieve_random(query, k=3, seed=7)]
    assert a == b


def test_decay_lambda_requires_query_step():
    store = ExperienceStore(FEATURE_NAMES)
    base = {
        "occurrence_ordinal": 0, "sample_index_in_occurrence": 0, "step": 0,
        "workload_id": "w", "condition_id": "clean", "is_novel_combo": False, "split": "train",
        "occurrence_count_for_combo": 1,
        "context": {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0},
        "true_label": 1, "predicted_label": 0, "confidence": 0.5, "b_risk_score": 0.5,
        "tier": "HIGH", "decision": "ABSTAIN", "is_failure": True, "outcome": "INCORRECT",
        "diagnosed_cause": "clean", "recovery_attempted": False, "recovery_action": None,
        "recovery_outcome": None, "recovery_correct": None,
    }
    store.add(experience_from_episode_record(base, "v", "hash"))
    store.fit_embedder()
    query = DecisionTimeQuery(context=base["context"], confidence=0.5, workload_id="w", tier="HIGH", diagnosed_cause="clean", step=None)
    with pytest.raises(ValueError):
        store.retrieve_similarity(query, k=1, decay_lambda=0.1)


def test_persist_round_trips_reliability_event_through_repository(session_factory):
    records, dataset_hash = _require_phase4_0_data()
    store = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    small = ExperienceStore(FEATURE_NAMES)
    small.add_many(store.experiences[:5])

    with session_factory() as session:
        repo = EventRepository(session)
        small.persist(repo)

    with session_factory() as session:
        repo = EventRepository(session)
        reloaded = [repo.get(e.event.event_id) for e in small.experiences]
    assert all(r is not None for r in reloaded)
    assert {r.event_id for r in reloaded} == {e.event.event_id for e in small.experiences}
    assert all(r.metadata.get("condition_id") for r in reloaded)
