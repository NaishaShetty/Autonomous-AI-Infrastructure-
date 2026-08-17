"""Unit tests for src/failure_experience/ingest.py (Task 9)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.failure_experience.ingest import IngestionError, ingest_batch, ingest_record

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _valid_record(**overrides) -> dict:
    base = dict(
        source_dataset="unit_test", episode_id="ep1", occurrence_key="occ1", observed_at=NOW,
        workload_id="w1", workload_type="test_workload", failure_type="test_failure",
        diagnosis_source="not_attempted", recovery_status="not_observed",
        validation_result="not_performed", outcome_final_status="failure",
    )
    base.update(overrides)
    return base


class TestValidRecords:
    def test_minimal_valid_record_ingests(self):
        exp = ingest_record(_valid_record(), NOW)
        assert exp.identity.episode_id == "ep1"

    def test_deterministic_id_reproducible_across_calls(self):
        exp1 = ingest_record(_valid_record(), NOW)
        exp2 = ingest_record(_valid_record(), NOW)
        assert exp1.identity.experience_id == exp2.identity.experience_id

    def test_full_record_with_all_optional_fields(self):
        record = _valid_record(
            telemetry={"cpu": 0.97}, diagnosis_suspected_cause="resource_exhaustion",
            diagnosis_confidence=0.87, diagnosis_source="automated_system",
            recovery_status="attempted", recovery_selected_action="restart",
            validation_result="passed", outcome_recovery_success=True, outcome_final_status="success",
        )
        exp = ingest_record(record, NOW)
        assert exp.diagnosis.confidence == 0.87
        assert exp.recovery.selected_action == "restart"


class TestMissingRequiredFields:
    def test_missing_source_dataset_raises_ingestion_error(self):
        record = _valid_record()
        del record["source_dataset"]
        with pytest.raises(IngestionError):
            ingest_record(record, NOW)

    def test_missing_multiple_required_fields_lists_all(self):
        record = _valid_record()
        del record["workload_id"]
        del record["failure_type"]
        with pytest.raises(IngestionError, match="workload_id"):
            ingest_record(record, NOW)


class TestInvalidRecords:
    def test_invalid_enum_value_raises_ingestion_error(self):
        record = _valid_record(diagnosis_source="not_a_real_source")
        with pytest.raises(IngestionError):
            ingest_record(record, NOW)

    def test_out_of_range_confidence_raises_ingestion_error(self):
        record = _valid_record(diagnosis_confidence=5.0, diagnosis_source="automated_system")
        with pytest.raises(IngestionError):
            ingest_record(record, NOW)

    def test_out_of_order_temporal_lineage_raises_ingestion_error(self):
        from datetime import timedelta
        record = _valid_record(temporal={
            "observation_ts": NOW, "detection_ts": NOW - timedelta(seconds=10),
        })
        with pytest.raises(IngestionError):
            ingest_record(record, NOW)


class TestBatchIngestionDoesNotCrashOnPartialFailure:
    def test_batch_with_one_bad_record_still_ingests_the_rest(self):
        good = _valid_record(episode_id="good1", occurrence_key="o1")
        bad = _valid_record(episode_id="bad1", occurrence_key="o2")
        del bad["failure_type"]
        result = ingest_batch([good, bad], NOW)
        assert len(result.experiences) == 1
        assert len(result.errors) == 1
        assert result.errors[0]["record_ref"] == "bad1"

    def test_empty_batch(self):
        result = ingest_batch([], NOW)
        assert result.total == 0


class TestFailureSignatureDeterminism:
    def test_same_failure_type_component_workload_same_signature(self):
        exp1 = ingest_record(_valid_record(episode_id="e1", occurrence_key="o1"), NOW)
        exp2 = ingest_record(_valid_record(episode_id="e2", occurrence_key="o2"), NOW)
        assert exp1.failure.failure_signature == exp2.failure.failure_signature

    def test_different_failure_type_different_signature(self):
        exp1 = ingest_record(_valid_record(episode_id="e1", occurrence_key="o1", failure_type="a"), NOW)
        exp2 = ingest_record(_valid_record(episode_id="e2", occurrence_key="o2", failure_type="b"), NOW)
        assert exp1.failure.failure_signature != exp2.failure.failure_signature


class TestLifecycleInference:
    def test_detection_only_record_gets_detected_status(self):
        exp = ingest_record(_valid_record(), NOW)
        assert exp.identity.lifecycle_status.value == "detected"

    def test_validated_record_gets_validated_status(self):
        record = _valid_record(
            diagnosis_source="automated_system", diagnosis_suspected_cause="x",
            recovery_status="attempted", recovery_selected_action="retry",
            validation_result="passed",
        )
        exp = ingest_record(record, NOW)
        assert exp.identity.lifecycle_status.value == "validated"
