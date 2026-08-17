"""Phase 4.1.2: the experience representation.

Built ON src.schema.events.ReliabilityEvent (reused, not duplicated) --
per docs/PHASE4_PLAN.md section 0, most of the field list Phase 4.1 needs
already exists there (workload_id, context, confidence, failure_risk,
decision, outcome, metadata). What ReliabilityEvent does NOT carry is the
episodic-specific provenance Phase 4.0 generated (which occurrence, which
split, the ground-truth condition label, recovery trace) -- that lives in
a separate ``EpisodeProvenance`` sidecar, not stuffed into
ReliabilityEvent's free-form ``metadata`` as the source of truth (a copy
is mirrored into ``metadata`` only so the ReliabilityEvent half round-trips
through the existing, frozen ``EventRepository`` unchanged).

The decision-time / outcome-only / evaluation-only split is enforced
STRUCTURALLY, not just by convention: ``DecisionTimeQuery`` is the only
type retrieval functions accept, and it has no field through which
``condition_id`` (the Phase 4.0 ground-truth corruption label) or any
outcome field could reach a retrieval computation. See
src/experience/retrieval.py.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent


def deterministic_event_id(step: int, workload_id: str, condition_id: str) -> str:
    """Deterministic, reproducible event_id (fits the frozen
    ReliabilityEventRecord.event_id column, String(32)) -- NOT a random
    uuid4, so rebuilding a store from the same episode records always
    produces byte-identical event_ids (required for the content-hash
    versioning in EpisodeProvenance.content_hash / ExperienceStore.content_hash)."""
    raw = f"{step}|{workload_id}|{condition_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@dataclass(frozen=True)
class EpisodeProvenance:
    """Everything Phase 4.0 knows about one episode step that
    ReliabilityEvent has no field for. ``condition_id`` is Phase 4.0's own
    ground truth (which corruption mechanism was applied) -- it is
    EVALUATION-ONLY: the generator recorded it because it chose the
    condition, not because a live system could observe it directly. It
    must never be passed into a retrieval query (see DecisionTimeQuery)."""

    workload_id: str
    condition_id: str  # ground truth -- evaluation-only, see module docstring
    occurrence_ordinal: int
    step: int
    split: str
    is_novel_combo: bool
    tier: str
    diagnosed_cause: Optional[str]  # decision-time-available: a deterministic fn of context (src.evaluation.diagnosis)
    recovery_action: Optional[str]  # outcome-only (recovery only runs after tiering, and its result is post-hoc)
    recovery_outcome: Optional[str]
    recovery_correct: Optional[bool]
    protocol_version: str
    dataset_content_hash: str

    def to_metadata_dict(self) -> dict:
        """Mirrored into ReliabilityEvent.metadata for persistence through
        the frozen EventRepository -- see module docstring. This mirror is
        NOT the source of truth (EpisodeProvenance is); it exists only so
        the ReliabilityEvent half can round-trip through storage."""
        return {
            "condition_id": self.condition_id,
            "occurrence_ordinal": self.occurrence_ordinal,
            "step": self.step,
            "split": self.split,
            "is_novel_combo": self.is_novel_combo,
            "tier": self.tier,
            "diagnosed_cause": self.diagnosed_cause,
            "recovery_action": self.recovery_action,
            "recovery_outcome": self.recovery_outcome,
            "recovery_correct": self.recovery_correct,
            "protocol_version": self.protocol_version,
            "dataset_content_hash": self.dataset_content_hash,
        }


@dataclass(frozen=True)
class DecisionTimeQuery:
    """The ONLY information a retrieval mechanism may condition on --
    everything a live system could plausibly know about the current
    incident BEFORE its outcome is checked. No ``condition_id``, no
    ``true_label``, no ``outcome``, no ``recovery_*`` field exists on this
    type -- retrieval code that only accepts a DecisionTimeQuery cannot
    leak them even by mistake (structural prevention, not just a
    docstring promise -- see tests/unit/test_experience_schema.py::
    test_decision_time_query_has_no_outcome_or_ground_truth_fields)."""

    context: dict
    confidence: float
    workload_id: str
    tier: str
    diagnosed_cause: Optional[str]
    step: Optional[int] = None  # the querying incident's own logical time, for recency scoring only


@dataclass(frozen=True)
class Experience:
    """One stored failure incident: a ReliabilityEvent (reused schema) +
    its EpisodeProvenance sidecar."""

    event: ReliabilityEvent
    provenance: EpisodeProvenance

    def decision_time_query(self) -> DecisionTimeQuery:
        return DecisionTimeQuery(
            context=dict(self.event.context),
            confidence=self.event.confidence,
            workload_id=self.event.workload_id,
            tier=self.provenance.tier,
            diagnosed_cause=self.provenance.diagnosed_cause,
            step=self.provenance.step,
        )


def experience_from_episode_record(
    record: dict, protocol_version: str, dataset_content_hash: str
) -> Experience:
    """Builds one Experience from a Phase 4.0 EpisodeStep dict (as written
    by benchmarks/phase4_0_generate_episodes.py / read from
    experiments/results/phase4_0/episodes.json)."""
    event = ReliabilityEvent(
        event_id=deterministic_event_id(record["step"], record["workload_id"], record["condition_id"]),
        workload_id=record["workload_id"],
        source=EventSource.BENCHMARK,
        context=dict(record["context"]),
        raw_confidence=None,
        confidence=float(record["confidence"]),
        failure_risk=float(record["b_risk_score"]),
        decision=Decision(record["decision"]),
        abstained=record["decision"] != Decision.ANSWER.value,
        is_failure=bool(record["is_failure"]),
        failure_cluster=None,
        outcome=Outcome(record["outcome"]),
        metadata={},
    )
    provenance = EpisodeProvenance(
        workload_id=record["workload_id"],
        condition_id=record["condition_id"],
        occurrence_ordinal=record["occurrence_ordinal"],
        step=record["step"],
        split=record["split"],
        is_novel_combo=record["is_novel_combo"],
        tier=record["tier"],
        diagnosed_cause=record.get("diagnosed_cause"),
        recovery_action=record.get("recovery_action"),
        recovery_outcome=record.get("recovery_outcome"),
        recovery_correct=record.get("recovery_correct"),
        protocol_version=protocol_version,
        dataset_content_hash=dataset_content_hash,
    )
    event = event.model_copy(update={"metadata": provenance.to_metadata_dict()})
    return Experience(event=event, provenance=provenance)
