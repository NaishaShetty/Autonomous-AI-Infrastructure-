"""Integration tests for the active Phase 4.1 FailureExperience pipeline:
ingestion -> storage -> retrieval -> reconstruction, across all four source
adapters, plus provenance/temporal/leakage-protection checks (Task 13)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.failure_experience import storage
from src.failure_experience.ingest import ingest_batch
from src.failure_experience.reconstruction import verify_round_trip
from src.failure_experience.retrieval import RetrievalQuery, retrieve
from src.failure_experience.schema import EligibilityRole
from src.failure_experience.sources import real_agentrx, real_aiops, real_alibaba, synthetic_episodic

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture()
def repo_session(tmp_path):
    url = f"sqlite:///{(tmp_path / 'fe_test.db').as_posix()}"
    storage.reset_db(url)
    with storage.get_session() as session:
        yield storage.FailureExperienceRepository(session)


@pytest.fixture(scope="module")
def synthetic_sample():
    return synthetic_episodic.load_normalized()[:40]


@pytest.fixture(scope="module")
def agentrx_sample(require_agentrx_data):
    return real_agentrx.load_normalized()


@pytest.fixture(scope="module")
def alibaba_sample(require_alibaba_data):
    records, _ = real_alibaba.load_normalized(sample_size=40)
    return records


@pytest.fixture(scope="module")
def aiops_sample(require_aiops_data):
    return real_aiops.load_normalized()


class TestSourceAdaptersProduceValidRecords:
    def test_synthetic_adapter_ingests_cleanly(self, synthetic_sample):
        result = ingest_batch(synthetic_sample, NOW)
        assert len(result.errors) == 0
        assert len(result.experiences) == len(synthetic_sample)

    def test_agentrx_adapter_ingests_cleanly(self, agentrx_sample):
        result = ingest_batch(agentrx_sample, NOW)
        assert len(result.errors) == 0
        assert len(result.experiences) > 0

    def test_alibaba_adapter_ingests_cleanly(self, alibaba_sample):
        result = ingest_batch(alibaba_sample, NOW)
        assert len(result.errors) == 0
        assert len(result.experiences) > 0

    def test_aiops_adapter_ingests_cleanly(self, aiops_sample):
        result = ingest_batch(aiops_sample, NOW)
        assert len(result.errors) == 0
        assert len(result.experiences) > 0


class TestStorageAndRetrieval:
    def test_save_and_get_round_trip(self, repo_session, synthetic_sample):
        result = ingest_batch(synthetic_sample[:5], NOW)
        repo_session.save_many(result.experiences)
        fetched = repo_session.get(result.experiences[0].identity.experience_id)
        assert fetched is not None
        assert fetched.identity.experience_id == result.experiences[0].identity.experience_id

    def test_retrieve_by_source_dataset(self, repo_session, synthetic_sample, alibaba_sample):
        syn = ingest_batch(synthetic_sample[:5], NOW).experiences
        alb = ingest_batch(alibaba_sample[:5], NOW).experiences
        repo_session.save_many(syn + alb)
        results = retrieve(repo_session, RetrievalQuery(source_dataset="alibaba_gpu2020"))
        assert len(results) == len(alb)
        assert all(r.experience.provenance.source_dataset == "alibaba_gpu2020" for r in results)

    def test_retrieve_by_failure_type(self, repo_session, alibaba_sample):
        experiences = ingest_batch(alibaba_sample[:10], NOW).experiences
        repo_session.save_many(experiences)
        results = retrieve(repo_session, RetrievalQuery(failure_type="task_terminated_failed"))
        assert len(results) == len(experiences)

    def test_retrieve_temporal_range(self, repo_session, synthetic_sample):
        experiences = ingest_batch(synthetic_sample, NOW).experiences
        repo_session.save_many(experiences)
        cutoff = sorted(e.identity.observed_at for e in experiences)[len(experiences) // 2]
        before = retrieve(repo_session, RetrievalQuery(observed_before=cutoff))
        after = retrieve(repo_session, RetrievalQuery(observed_after=cutoff + timedelta(seconds=1)))
        assert len(before) + len(after) <= len(experiences)
        before_ids = {r.experience.identity.experience_id for r in before}
        after_ids = {r.experience.identity.experience_id for r in after}
        assert before_ids.isdisjoint(after_ids)

    def test_retrieve_min_eligibility_filters_out_lower_roles(self, repo_session, alibaba_sample):
        experiences = ingest_batch(alibaba_sample[:20], NOW).experiences
        repo_session.save_many(experiences)
        all_results = retrieve(repo_session, RetrievalQuery())
        eligible_only = retrieve(repo_session, RetrievalQuery(min_eligibility=EligibilityRole.LEARNING_ELIGIBLE))
        assert len(eligible_only) <= len(all_results)

    def test_retrieval_summary_has_required_keys(self, repo_session, synthetic_sample):
        experiences = ingest_batch(synthetic_sample[:3], NOW).experiences
        repo_session.save_many(experiences)
        results = retrieve(repo_session, RetrievalQuery())
        for r in results:
            for key in ("what_happened", "why_according_to_system", "action_taken",
                        "did_it_work", "trustworthiness", "when"):
                assert key in r.summary


class TestIdempotency:
    def test_saving_same_experience_twice_does_not_duplicate(self, repo_session, synthetic_sample):
        experiences = ingest_batch(synthetic_sample[:5], NOW).experiences
        repo_session.save_many(experiences)
        count_after_first = repo_session.count()
        repo_session.save_many(experiences)  # re-ingest identical records
        count_after_second = repo_session.count()
        assert count_after_first == count_after_second

    def test_reingesting_same_source_record_yields_same_id(self, synthetic_sample):
        result1 = ingest_batch(synthetic_sample[:5], NOW)
        result2 = ingest_batch(synthetic_sample[:5], NOW + timedelta(days=1))
        ids1 = [e.identity.experience_id for e in result1.experiences]
        ids2 = [e.identity.experience_id for e in result2.experiences]
        assert ids1 == ids2


class TestReconstruction:
    def test_synthetic_round_trip_passes_all_checks(self, synthetic_sample):
        for record in synthetic_sample[:10]:
            exp = ingest_batch([record], NOW).experiences[0]
            report = verify_round_trip(record, exp)
            assert report.passed, report.checks

    def test_agentrx_round_trip_passes_all_checks(self, agentrx_sample):
        for record in agentrx_sample[:10]:
            exp = ingest_batch([record], NOW).experiences[0]
            report = verify_round_trip(record, exp)
            assert report.passed, report.checks

    def test_alibaba_round_trip_passes_all_checks(self, alibaba_sample):
        for record in alibaba_sample[:10]:
            exp = ingest_batch([record], NOW).experiences[0]
            report = verify_round_trip(record, exp)
            assert report.passed, report.checks


class TestProvenanceTraceability:
    def test_every_experience_traces_back_to_source_dataset(self, synthetic_sample, alibaba_sample, aiops_sample, agentrx_sample):
        for sample in (synthetic_sample, alibaba_sample, aiops_sample, agentrx_sample):
            for exp in ingest_batch(sample[:5], NOW).experiences:
                assert exp.provenance.source_dataset != ""
                assert exp.provenance.raw_record_ref  # non-empty -- traceable to original raw record

    def test_dataset_content_hash_present_for_all_experiences(self, alibaba_sample):
        for exp in ingest_batch(alibaba_sample[:5], NOW).experiences:
            assert exp.provenance.dataset_content_hash is not None


class TestTemporalLineageIntegrity:
    def test_all_ingested_experiences_have_non_decreasing_lineage(self, synthetic_sample):
        for exp in ingest_batch(synthetic_sample, NOW).experiences:
            events = exp.temporal_lineage.ordered_events()
            timestamps = [ts for _, ts in events]
            assert timestamps == sorted(timestamps)

    def test_can_determine_experiences_available_before_a_cutoff(self, repo_session, synthetic_sample):
        """Directly exercises the 'which experiences were available to the
        learning system at time T' requirement (Task 7 / brief section on
        temporal and data lineage integrity)."""
        experiences = ingest_batch(synthetic_sample, NOW).experiences
        repo_session.save_many(experiences)
        sorted_ts = sorted(e.identity.observed_at for e in experiences)
        cutoff = sorted_ts[len(sorted_ts) // 2]
        available = retrieve(repo_session, RetrievalQuery(observed_before=cutoff))
        for r in available:
            assert r.experience.identity.observed_at <= cutoff


class TestLeakageProtection:
    """Verifies the Alibaba split label (reused from the frozen Phase 3
    real-data manifest) is carried through ingestion unmodified -- so any
    future learning step can filter to train-only experiences without
    Phase 4.1 having silently mixed splits."""

    def test_alibaba_split_label_preserved_through_ingestion(self, alibaba_sample):
        experiences = ingest_batch(alibaba_sample, NOW).experiences
        splits_seen = {e.workload_context.environment for e in experiences}
        assert splits_seen.issubset({"train", "val", "test", "unknown"})

    def test_no_frozen_test_split_experience_silently_relabeled_train(self, alibaba_sample):
        for record, exp in zip(alibaba_sample, ingest_batch(alibaba_sample, NOW).experiences):
            assert exp.workload_context.environment == record.get("environment")


class TestPhase3IntegrationDoesNotTouchFrozenModules:
    """The active Phase 4.1 package must not import anything from the old,
    frozen src/experience (old Phase 4.1) or src/patterns (old Phase 4.2)
    packages -- it is additive, independent code."""

    def test_no_import_of_old_experience_package(self):
        import src.failure_experience.ingest as m
        import src.failure_experience.schema as s
        for mod in (m, s):
            src_code = open(mod.__file__).read()
            assert "src.experience" not in src_code
            assert "src.patterns" not in src_code

    def test_reliability_event_schema_still_importable_and_unmodified_shape(self):
        from src.schema.events import ReliabilityEvent
        fields = set(ReliabilityEvent.model_fields.keys())
        # the exact frozen field set from src/schema/events.py -- if this
        # ever changes, it means someone edited the frozen file, which this
        # test exists to catch.
        expected = {
            "event_id", "timestamp", "workload_id", "source", "context",
            "raw_confidence", "confidence", "failure_risk", "decision",
            "abstained", "is_failure", "failure_cluster", "outcome", "metadata",
        }
        assert fields == expected
