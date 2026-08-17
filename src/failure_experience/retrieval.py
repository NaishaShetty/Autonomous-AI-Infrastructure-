"""Task 10: retrieval interface.

Deliberately filter-based, not semantic/vector retrieval (Task 10 says not
to over-engineer this yet) -- a ``RetrievalQuery`` composes any subset of
the dimensions the brief lists (failure signature, failure type, workload
context, affected component, temporal range, outcome, eligibility,
provenance), applied in-memory over whatever a ``FailureExperienceRepository``
returns. This keeps the retrieval mechanism swappable later (Phase 4.2+ can
add embedding-based ranking on top without changing this interface's
contract) without committing to one now.

Every result is a ``RetrievalResult`` -- the FailureExperience plus an
explicit ``summary`` dict answering the six questions Task 10 requires an
answer for ("what happened, why, what action, did it work, how trustworthy,
when").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .schema import EligibilityRole, FailureExperience
from .storage import FailureExperienceRepository


@dataclass(frozen=True)
class RetrievalQuery:
    failure_signature: Optional[str] = None
    failure_type: Optional[str] = None
    workload_id: Optional[str] = None
    affected_component: Optional[str] = None
    source_dataset: Optional[str] = None
    final_status: Optional[str] = None
    min_eligibility: Optional[EligibilityRole] = None  # matches this role or LEARNING_ELIGIBLE only
    observed_after: Optional[datetime] = None
    observed_before: Optional[datetime] = None
    limit: Optional[int] = None


def summarize(experience: FailureExperience) -> dict:
    return {
        "what_happened": {
            "failure_type": experience.failure.failure_type,
            "affected_component": experience.failure.affected_component,
            "severity": experience.failure.severity,
        },
        "why_according_to_system": {
            "suspected_cause": experience.diagnosis.suspected_cause,
            "diagnosis_source": experience.diagnosis.source.value,
            "diagnosis_confidence": experience.diagnosis.confidence,
            "diagnosis_status": experience.eligibility.diagnosis_status,
        },
        "action_taken": {
            "status": experience.recovery.status.value,
            "selected_action": experience.recovery.selected_action,
        },
        "did_it_work": {
            "final_status": experience.outcome.final_status.value,
            "recovery_success": experience.outcome.recovery_success,
            "task_success": experience.outcome.task_success,
        },
        "trustworthiness": {
            "eligibility_role": experience.eligibility.role.value,
            "observation_completeness": experience.eligibility.observation_completeness,
            "provenance_completeness": experience.eligibility.provenance_completeness,
        },
        "when": {
            "observed_at": experience.identity.observed_at.isoformat(),
            "lifecycle_status": experience.identity.lifecycle_status.value,
        },
    }


@dataclass(frozen=True)
class RetrievalResult:
    experience: FailureExperience
    summary: dict


_ELIGIBLE_ORDER = [
    EligibilityRole.EXCLUDED, EligibilityRole.QUARANTINED, EligibilityRole.STORED,
    EligibilityRole.VALIDATED_USABLE, EligibilityRole.LEARNING_ELIGIBLE,
]


def _meets_min_eligibility(role: EligibilityRole, minimum: EligibilityRole) -> bool:
    return _ELIGIBLE_ORDER.index(role) >= _ELIGIBLE_ORDER.index(minimum)


def retrieve(repository: FailureExperienceRepository, query: RetrievalQuery) -> list[RetrievalResult]:
    results: list[FailureExperience] = []
    for record in repository.all_records():
        if query.failure_signature is not None and record.failure_signature != query.failure_signature:
            continue
        if query.failure_type is not None and record.failure_type != query.failure_type:
            continue
        if query.workload_id is not None and record.workload_id != query.workload_id:
            continue
        if query.affected_component is not None and record.affected_component != query.affected_component:
            continue
        if query.source_dataset is not None and record.source_dataset != query.source_dataset:
            continue
        if query.final_status is not None and record.final_status != query.final_status:
            continue
        observed_at = record.observed_at
        if observed_at.tzinfo is None:
            from datetime import timezone
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if query.observed_after is not None and observed_at < query.observed_after:
            continue
        if query.observed_before is not None and observed_at > query.observed_before:
            continue
        experience = FailureExperience.model_validate(record.payload)
        if query.min_eligibility is not None and not _meets_min_eligibility(experience.eligibility.role, query.min_eligibility):
            continue
        results.append(experience)

    results.sort(key=lambda e: e.identity.observed_at)
    if query.limit is not None:
        results = results[: query.limit]
    return [RetrievalResult(experience=e, summary=summarize(e)) for e in results]
