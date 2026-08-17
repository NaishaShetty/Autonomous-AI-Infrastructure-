"""Canonical reliability/failure event schema for the unified system.

This is the single representation shared by the reliability (confidence)
subsystem and the failure-memory subsystem. Phase 1 found the two source
prototypes used incompatible, ad-hoc representations:

- AI-Abstention-Engine mixed a 0-1 scale and a 0-100 scale for the same
  concept ("trust_score"), which is the root cause of the
  ``global_reliability_score: 189.61`` bug documented in
  ``PHASE1_AUDIT_REPORT.md`` section 2/5.
- Introspective-Failure-Memory-Model represented a "failure" as a bespoke
  4-vector (2 PCA components + 2 confidence-derived scalars) computed over a
  fixed 5-dim synthetic feature vector, with no persisted schema at all
  (in-memory only).

This module fixes both problems: confidence is ALWAYS a float in [0.0, 1.0]
internally (presentation-layer code is responsible for any 0-100 conversion,
see :func:`confidence_to_percent`), and every event -- whether it represents
a successful prediction, an abstention, or a stored failure -- is an
instance of the same ``ReliabilityEvent`` model, validated at construction
time.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Decision(str, Enum):
    """The unified decision policy's output. Deliberately a small, closed
    set -- Phase 1 found the source Abstention Engine had accreted 5 decision
    labels (ANSWER/REVIEW/REQUEST_MORE_EVIDENCE/ESCALATE/ABSTAIN) produced by
    10 overlapping "strategies". We collapse to the 3 states actually needed
    to answer the Phase 2 research question.
    """

    ANSWER = "ANSWER"
    ABSTAIN = "ABSTAIN"
    REVIEW = "REVIEW"


class Outcome(str, Enum):
    """Ground-truth correctness of an ANSWER decision, when known.

    Populated by benchmark/evaluation code (label is known) or by later
    feedback in a real deployment; left UNKNOWN for live events where no
    ground truth is available yet.
    """

    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    UNKNOWN = "UNKNOWN"


class EventSource(str, Enum):
    """Which subsystem produced this event -- used only for provenance /
    filtering, never for changing validation rules."""

    RELIABILITY_ENGINE = "reliability_engine"
    FAILURE_MEMORY = "failure_memory"
    BENCHMARK = "benchmark"


def confidence_to_percent(confidence: float) -> float:
    """The one place a 0-1 confidence is converted to a 0-100 display value.

    Presentation code must call this rather than re-deriving the conversion,
    so there is exactly one scale internally and exactly one conversion at
    the boundary -- the discrepancy that caused the Phase 1
    ``global_reliability_score: 189.61`` bug cannot recur if this rule is
    followed.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence must be in [0.0, 1.0], got {confidence}")
    return round(confidence * 100.0, 2)


class ReliabilityEvent(BaseModel):
    """One inference/reliability event, and (when applicable) the failure
    information associated with it.

    Field reference
    ----------------
    event_id            required, str (uuid4 hex). Primary key.
    timestamp            required, tz-aware UTC datetime.
    workload_id           required, str. Identifies the model/workload that produced
                          the prediction (e.g. "synthetic-classifier-v1").
    source                required, EventSource. Which subsystem logged this event.
    context               required, dict[str, float]. The structured numeric feature
                          vector describing the input. This is the canonical
                          replacement for the Abstention Engine's ad-hoc "structured
                          features" and the Failure Memory's fixed 5-dim synthetic
                          vector -- any producer may supply any named float features,
                          consumers (embedding/calibration) declare which keys they
                          need.
    raw_confidence         optional, float in [0,1]. Pre-calibration model confidence
                          (e.g. max predicted-class probability), if available.
    confidence            required, float in [0,1]. The single canonical, calibrated
                          confidence value. ALWAYS 0-1 -- never 0-100.
    failure_risk          optional, float in [0,1]. Failure-memory's similarity-based
                          risk signal for this context, if computed.
    decision              required, Decision. The policy's output.
    abstained             required, bool. Derived convenience flag, must equal
                          ``decision != Decision.ANSWER`` (validated).
    is_failure             required, bool. True if this event represents a confirmed
                          model failure (wrong prediction on a labeled example, or an
                          abstention/escalation). Failure-memory only stores events
                          where this is True.
    failure_cluster        optional, int. Cluster id assigned by failure-memory, if
                          this event has been clustered.
    outcome                required, Outcome. CORRECT/INCORRECT/UNKNOWN.
    metadata               optional, dict. Free-form, non-validated extra info
                          (e.g. provider name, query text hash). Must never contain
                          raw personal data -- see PHASE1_AUDIT_REPORT.md section 5/11
                          on the committed reliability.db credential leak this project
                          explicitly avoids repeating.
    """

    model_config = ConfigDict(use_enum_values=False, extra="forbid")

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workload_id: str
    source: EventSource

    context: dict[str, float]

    raw_confidence: Optional[float] = None
    confidence: float
    failure_risk: Optional[float] = None

    decision: Decision
    abstained: bool
    is_failure: bool = False
    failure_cluster: Optional[int] = None

    outcome: Outcome = Outcome.UNKNOWN
    metadata: dict = Field(default_factory=dict)

    @field_validator("confidence", "raw_confidence", "failure_risk")
    @classmethod
    def _validate_unit_interval(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"value must be in [0.0, 1.0], got {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def _validate_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("abstained")
    @classmethod
    def _validate_abstained_matches_decision(cls, v: bool, info) -> bool:
        decision = info.data.get("decision")
        if decision is not None:
            expected = decision != Decision.ANSWER
            if v != expected:
                raise ValueError(
                    f"abstained={v} is inconsistent with decision={decision}; "
                    f"expected abstained={expected}"
                )
        return v

    def as_percent(self) -> float:
        """Convenience: this event's confidence on a 0-100 display scale."""
        return confidence_to_percent(self.confidence)
