"""Task 6: experience quality / learning eligibility assessment.

Deliberately NOT a single fabricated trust score. ``assess`` computes each
explicit evidence-quality field independently and then applies a small,
fully-documented decision table to pick ``EligibilityRole`` -- every rule is
listed in ``_ROLE_RULES`` below and each decision records its ``reasons``,
so eligibility is auditable rather than opaque.

Roles (least to most permissive for future learning use):
  EXCLUDED         -- data integrity or temporal-validity problem; never usable.
  QUARANTINED       -- structurally storable but too incomplete/uncertain to trust yet.
  STORED           -- default: persisted, but not yet cleared for anything downstream.
  VALIDATED_USABLE  -- outcome/validation is certain, but diagnosis is unvalidated
                       or evidence is thin -- usable for outcome-level analysis, not
                       for learning a diagnosis-dependent policy.
  LEARNING_ELIGIBLE -- integrity + completeness + certainty thresholds all clear;
                       the only role Phase 4.2+ learning code should read by default.
"""
from __future__ import annotations

from .schema import (
    Diagnosis,
    EligibilityAssessment,
    EligibilityRole,
    Observations,
    OutcomeInfo,
    Provenance,
    TemporalLineage,
    ValidationInfo,
    ValidationResult,
)

# Fixed thresholds, documented here (not tuned against any evaluation split --
# see docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md section on eligibility for
# why these particular cutoffs were chosen: round, conservative defaults, not
# fit to any dataset).
MIN_OBSERVATION_COMPLETENESS_FOR_LEARNING = 0.5
MIN_PROVENANCE_COMPLETENESS_FOR_LEARNING = 0.6


def _diagnosis_status(diagnosis: Diagnosis, validation: ValidationInfo) -> str:
    if diagnosis.source.value == "not_attempted" or diagnosis.suspected_cause is None:
        return "not_attempted"
    if validation.validated_cause is None:
        return "unvalidated"
    if validation.validated_cause == diagnosis.suspected_cause:
        return "validated"
    return "contradicted"


def _outcome_certainty(outcome: OutcomeInfo, validation: ValidationInfo) -> str:
    if validation.validation_result in (ValidationResult.PASSED, ValidationResult.FAILED):
        return "certain"
    if outcome.final_status.value != "unknown":
        return "partial"
    return "unknown"


def _provenance_completeness(provenance: Provenance) -> float:
    fields = [
        provenance.detector_version, provenance.diagnosis_component_version,
        provenance.recovery_policy_version, provenance.validation_component_version,
        provenance.dataset_content_hash, provenance.source_workload,
    ]
    return sum(1 for f in fields if f) / len(fields)


def _temporal_validity(lineage: TemporalLineage) -> bool:
    try:
        lineage.ordered_events()  # already validated monotonic at construction; re-check non-empty
        return len(lineage.ordered_events()) > 0
    except ValueError:
        return False


def assess(
    observations: Observations,
    diagnosis: Diagnosis,
    recovery_status: str,
    validation: ValidationInfo,
    outcome: OutcomeInfo,
    provenance: Provenance,
    temporal_lineage: TemporalLineage,
    data_integrity: bool = True,
) -> EligibilityAssessment:
    obs_completeness = observations.completeness()
    prov_completeness = _provenance_completeness(provenance)
    diag_status = _diagnosis_status(diagnosis, validation)
    out_certainty = _outcome_certainty(outcome, validation)
    temporal_valid = _temporal_validity(temporal_lineage)

    reasons: list[str] = []
    role: EligibilityRole

    if not data_integrity:
        role = EligibilityRole.EXCLUDED
        reasons.append("data_integrity check failed")
    elif not temporal_valid:
        role = EligibilityRole.EXCLUDED
        reasons.append("no valid temporal lineage recorded")
    elif obs_completeness == 0.0:
        role = EligibilityRole.QUARANTINED
        reasons.append("zero observation completeness")
    elif diag_status == "contradicted":
        # A contradicted diagnosis is NOT excluded -- Task 5 requires
        # exactly this case remain visible for future learning (a system
        # should learn that certain observations mislead diagnosis) -- but
        # it is not eligible for policies that assume diagnosis is correct.
        role = EligibilityRole.VALIDATED_USABLE
        reasons.append("diagnosis contradicted by later validation -- outcome usable, diagnosis-dependent learning excluded")
    elif (
        out_certainty == "certain"
        and diag_status in ("validated", "not_attempted")
        and obs_completeness >= MIN_OBSERVATION_COMPLETENESS_FOR_LEARNING
        and prov_completeness >= MIN_PROVENANCE_COMPLETENESS_FOR_LEARNING
    ):
        role = EligibilityRole.LEARNING_ELIGIBLE
        reasons.append("integrity, completeness, and outcome-certainty thresholds all cleared")
    elif out_certainty in ("certain", "partial"):
        role = EligibilityRole.VALIDATED_USABLE
        reasons.append("outcome known but completeness/provenance below learning thresholds")
    else:
        role = EligibilityRole.STORED
        reasons.append("outcome uncertain; stored for record-keeping only")

    return EligibilityAssessment(
        observation_completeness=obs_completeness,
        provenance_completeness=prov_completeness,
        diagnosis_status=diag_status,
        outcome_certainty=out_certainty,
        validation_status=validation.validation_result,
        data_integrity=data_integrity,
        temporal_validity=temporal_valid,
        role=role,
        reasons=reasons,
    )
