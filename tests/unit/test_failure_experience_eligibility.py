"""Unit tests for src/failure_experience/eligibility.py (Task 6)."""
from __future__ import annotations

from datetime import datetime, timezone

from src.failure_experience.eligibility import assess
from src.failure_experience.schema import (
    Diagnosis,
    DiagnosisSource,
    EligibilityRole,
    Observations,
    OutcomeInfo,
    Provenance,
    RecoveryStatus,
    TemporalLineage,
    ValidationInfo,
    ValidationResult,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _full_provenance() -> Provenance:
    return Provenance(
        source_dataset="unit_test", detector_version="v1", diagnosis_component_version="v1",
        recovery_policy_version="v1", validation_component_version="v1", source_workload="w1",
        ingestion_timestamp=NOW,
    )


def _rich_observations() -> Observations:
    return Observations(
        telemetry={"cpu": 0.9}, resource_metrics={"mem": 0.5}, performance_metrics={"latency": 4.2},
        log_events=["error"], anomaly_signals={"z": 3.0}, system_state={"replicas": 3},
    )


class TestExcluded:
    def test_data_integrity_failure_excludes(self):
        result = assess(
            Observations(), Diagnosis(), "not_observed", ValidationInfo(), OutcomeInfo(),
            Provenance(source_dataset="x", ingestion_timestamp=NOW), TemporalLineage(observation_ts=NOW),
            data_integrity=False,
        )
        assert result.role == EligibilityRole.EXCLUDED

    def test_no_temporal_lineage_excludes(self):
        result = assess(
            Observations(), Diagnosis(), "not_observed", ValidationInfo(), OutcomeInfo(),
            Provenance(source_dataset="x", ingestion_timestamp=NOW), TemporalLineage(),
        )
        assert result.role == EligibilityRole.EXCLUDED


class TestQuarantined:
    def test_zero_observation_completeness_quarantined(self):
        result = assess(
            Observations(), Diagnosis(), "not_observed", ValidationInfo(), OutcomeInfo(),
            Provenance(source_dataset="x", ingestion_timestamp=NOW), TemporalLineage(observation_ts=NOW),
        )
        assert result.role == EligibilityRole.QUARANTINED


class TestLearningEligible:
    def test_full_evidence_and_validated_outcome_is_learning_eligible(self):
        diag = Diagnosis(suspected_cause="cause_a", confidence=0.8, source=DiagnosisSource.AUTOMATED_SYSTEM)
        validation = ValidationInfo(validation_result=ValidationResult.PASSED, validated_cause="cause_a")
        outcome = OutcomeInfo(recovery_success=True, final_status="success")
        result = assess(
            _rich_observations(), diag, "attempted", validation, outcome, _full_provenance(),
            TemporalLineage(observation_ts=NOW),
        )
        assert result.role == EligibilityRole.LEARNING_ELIGIBLE
        assert result.diagnosis_status == "validated"

    def test_thin_observations_not_learning_eligible_even_if_validated(self):
        diag = Diagnosis(suspected_cause="cause_a", confidence=0.8, source=DiagnosisSource.AUTOMATED_SYSTEM)
        validation = ValidationInfo(validation_result=ValidationResult.PASSED, validated_cause="cause_a")
        outcome = OutcomeInfo(recovery_success=True, final_status="success")
        result = assess(
            Observations(), diag, "attempted", validation, outcome, _full_provenance(),
            TemporalLineage(observation_ts=NOW),
        )
        assert result.role != EligibilityRole.LEARNING_ELIGIBLE


class TestContradictedDiagnosis:
    """Task 5: a contradicted diagnosis must remain visible (VALIDATED_USABLE),
    not be silently excluded -- future learning must be able to see it."""

    def test_contradicted_diagnosis_is_validated_usable_not_excluded(self):
        diag = Diagnosis(suspected_cause="configuration_error", confidence=0.7, source=DiagnosisSource.AUTOMATED_SYSTEM)
        validation = ValidationInfo(validation_result=ValidationResult.FAILED, validated_cause="memory_exhaustion")
        outcome = OutcomeInfo(recovery_success=False, final_status="failure")
        result = assess(
            _rich_observations(), diag, "attempted", validation, outcome, _full_provenance(),
            TemporalLineage(observation_ts=NOW),
        )
        assert result.diagnosis_status == "contradicted"
        assert result.role == EligibilityRole.VALIDATED_USABLE
        assert result.role != EligibilityRole.EXCLUDED


class TestNotAttemptedDiagnosisIsNotContradicted:
    def test_no_diagnosis_attempted_status(self):
        result = assess(
            _rich_observations(), Diagnosis(), "not_observed", ValidationInfo(), OutcomeInfo(),
            _full_provenance(), TemporalLineage(observation_ts=NOW),
        )
        assert result.diagnosis_status == "not_attempted"


class TestAbstentionAndRollbackRepresentable:
    def test_abstained_outcome_assessable(self):
        outcome = OutcomeInfo(final_status="abstained")
        result = assess(
            _rich_observations(), Diagnosis(), "not_attempted", ValidationInfo(), outcome,
            _full_provenance(), TemporalLineage(observation_ts=NOW),
        )
        assert result.role in (EligibilityRole.STORED, EligibilityRole.QUARANTINED, EligibilityRole.VALIDATED_USABLE)

    def test_rollback_recovery_status_assessable(self):
        result = assess(
            _rich_observations(), Diagnosis(), RecoveryStatus.ATTEMPTED.value,
            ValidationInfo(validation_result=ValidationResult.PARTIAL),
            OutcomeInfo(final_status="rolled_back"), _full_provenance(), TemporalLineage(observation_ts=NOW),
        )
        assert result.validation_status == ValidationResult.PARTIAL
