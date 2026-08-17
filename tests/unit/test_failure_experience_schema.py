"""Unit tests for src/failure_experience/schema.py (active Phase 4.1)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.failure_experience.schema import (
    Diagnosis,
    DiagnosisSource,
    EligibilityAssessment,
    EligibilityRole,
    FailureExperience,
    FailureInfo,
    FinalStatus,
    Identity,
    LifecycleStatus,
    Observations,
    OutcomeInfo,
    Provenance,
    RecoveryInfo,
    RecoveryStatus,
    TemporalLineage,
    ValidationInfo,
    ValidationResult,
    WorkloadContext,
    deterministic_experience_id,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _minimal_eligibility() -> EligibilityAssessment:
    return EligibilityAssessment(
        observation_completeness=0.0, provenance_completeness=0.0,
        diagnosis_status="not_attempted", outcome_certainty="unknown",
        validation_status=ValidationResult.NOT_PERFORMED, data_integrity=True,
        temporal_validity=True, role=EligibilityRole.STORED,
    )


def _minimal_experience(**overrides) -> FailureExperience:
    defaults = dict(
        identity=Identity(experience_id="e1", episode_id="ep1", observed_at=NOW, created_at=NOW),
        workload_context=WorkloadContext(workload_id="w1", workload_type="test"),
        observations=Observations(),
        failure=FailureInfo(failure_type="ft", failure_signature="sig1"),
        diagnosis=Diagnosis(),
        recovery=RecoveryInfo(),
        validation=ValidationInfo(),
        outcome=OutcomeInfo(),
        provenance=Provenance(source_dataset="unit_test", ingestion_timestamp=NOW),
        temporal_lineage=TemporalLineage(observation_ts=NOW),
        eligibility=_minimal_eligibility(),
    )
    defaults.update(overrides)
    return FailureExperience(**defaults)


class TestRequiredFields:
    def test_minimal_experience_constructs(self):
        exp = _minimal_experience()
        assert exp.identity.experience_id == "e1"

    def test_missing_workload_id_rejected(self):
        with pytest.raises(ValidationError):
            WorkloadContext(workload_type="test")  # workload_id required

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            FailureInfo(failure_type="ft", failure_signature="s", bogus_field="x")


class TestOptionalFields:
    def test_diagnosis_defaults_to_not_attempted(self):
        d = Diagnosis()
        assert d.source == DiagnosisSource.NOT_ATTEMPTED
        assert d.suspected_cause is None

    def test_recovery_defaults_to_not_observed(self):
        r = RecoveryInfo()
        assert r.status == RecoveryStatus.NOT_OBSERVED

    def test_optional_fields_can_be_omitted_without_error(self):
        exp = _minimal_experience()
        assert exp.workload_context.model_id is None
        assert exp.failure.severity is None


class TestInvalidRecords:
    def test_diagnosis_confidence_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Diagnosis(confidence=1.5)

    def test_diagnosis_confidence_negative_rejected(self):
        with pytest.raises(ValidationError):
            Diagnosis(confidence=-0.1)

    def test_frozen_experience_cannot_be_mutated(self):
        exp = _minimal_experience()
        with pytest.raises(ValidationError):
            exp.identity = Identity(experience_id="e2", episode_id="ep2", observed_at=NOW, created_at=NOW)


class TestObservationInterpretationSeparation:
    """Task 3: observed facts and system interpretations must be
    distinguishable types, not merged into one record."""

    def test_observations_and_diagnosis_are_distinct_types(self):
        obs = Observations(telemetry={"cpu": 0.97})
        diag = Diagnosis(suspected_cause="resource_exhaustion", confidence=0.87,
                          source=DiagnosisSource.AUTOMATED_SYSTEM)
        assert not hasattr(obs, "suspected_cause")
        assert not hasattr(diag, "telemetry")

    def test_diagnosis_is_not_treated_as_ground_truth_field(self):
        """A Diagnosis object carries no field asserting it IS correct --
        only ValidationInfo.validated_cause (a separate object, filled in
        later, if ever) can confirm/contradict it."""
        diag = Diagnosis(suspected_cause="config_error", confidence=0.6,
                          source=DiagnosisSource.AUTOMATED_SYSTEM)
        assert diag.later_validated is None  # unknown until a ValidationInfo says otherwise


class TestFailedDiagnosisPreservation:
    """Task 5: an incorrect initial diagnosis must not be overwritten by a
    later-validated cause -- both must coexist on the record."""

    def test_contradicted_diagnosis_is_preserved_not_overwritten(self):
        diag = Diagnosis(suspected_cause="configuration_error", confidence=0.7,
                          source=DiagnosisSource.AUTOMATED_SYSTEM)
        validation = ValidationInfo(validation_result=ValidationResult.FAILED,
                                     validated_cause="memory_exhaustion")
        exp = _minimal_experience(diagnosis=diag, validation=validation)
        assert exp.diagnosis.suspected_cause == "configuration_error"
        assert exp.validation.validated_cause == "memory_exhaustion"
        assert exp.diagnosis.suspected_cause != exp.validation.validated_cause


class TestOutcomeRepresentationDiversity:
    """Task 4: success, failure, abstention, rollback, retry must all be
    representable and distinguishable -- not collapsed into one label."""

    @pytest.mark.parametrize("status", list(FinalStatus))
    def test_every_final_status_is_constructible(self, status):
        outcome = OutcomeInfo(final_status=status)
        assert outcome.final_status == status

    def test_same_action_different_context_can_have_different_outcomes(self):
        """Failure A + restart -> success; Failure B + restart -> failure --
        both must be representable as distinct FailureExperience objects
        with the SAME recovery.selected_action."""
        recovery = RecoveryInfo(status=RecoveryStatus.ATTEMPTED, selected_action="restart")
        success_exp = _minimal_experience(
            recovery=recovery, outcome=OutcomeInfo(recovery_success=True, final_status=FinalStatus.SUCCESS),
        )
        failure_exp = _minimal_experience(
            recovery=recovery, outcome=OutcomeInfo(recovery_success=False, final_status=FinalStatus.FAILURE),
        )
        assert success_exp.recovery.selected_action == failure_exp.recovery.selected_action
        assert success_exp.outcome.final_status != failure_exp.outcome.final_status


class TestTemporalLineage:
    def test_monotonic_lineage_accepted(self):
        t0 = NOW
        lineage = TemporalLineage(
            observation_ts=t0, detection_ts=t0 + timedelta(seconds=1),
            diagnosis_ts=t0 + timedelta(seconds=2), outcome_ts=t0 + timedelta(seconds=5),
        )
        assert len(lineage.ordered_events()) == 4

    def test_out_of_order_lineage_rejected(self):
        t0 = NOW
        with pytest.raises(ValidationError):
            TemporalLineage(observation_ts=t0, detection_ts=t0 - timedelta(seconds=1))

    def test_partial_lineage_allowed(self):
        lineage = TemporalLineage(observation_ts=NOW)
        assert len(lineage.ordered_events()) == 1


class TestDeterministicIds:
    def test_deterministic_experience_id_is_reproducible(self):
        id1 = deterministic_experience_id("src", "ep1", "occ1")
        id2 = deterministic_experience_id("src", "ep1", "occ1")
        assert id1 == id2

    def test_deterministic_experience_id_differs_for_different_input(self):
        id1 = deterministic_experience_id("src", "ep1", "occ1")
        id2 = deterministic_experience_id("src", "ep1", "occ2")
        assert id1 != id2


class TestContentHash:
    def test_content_hash_deterministic(self):
        exp1 = _minimal_experience()
        exp2 = _minimal_experience()
        assert exp1.content_hash() == exp2.content_hash()

    def test_content_hash_differs_for_different_content(self):
        exp1 = _minimal_experience()
        exp2 = _minimal_experience(failure=FailureInfo(failure_type="other", failure_signature="sig2"))
        assert exp1.content_hash() != exp2.content_hash()

    def test_content_hash_ignores_ingestion_timestamp(self):
        """Two experiences ingested at different wall-clock times but with
        identical substantive content should hash identically -- otherwise
        idempotent re-ingestion could never be detected."""
        exp1 = _minimal_experience(provenance=Provenance(source_dataset="unit_test", ingestion_timestamp=NOW))
        later = NOW + timedelta(days=1)
        exp2 = _minimal_experience(provenance=Provenance(source_dataset="unit_test", ingestion_timestamp=later))
        assert exp1.content_hash() == exp2.content_hash()
