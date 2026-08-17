"""Phase 4.2.9: the four evidence tiers and the pattern-candidate
representation.

**Pattern vocabulary (fixed here, matches
configs/phase4_2_pattern_protocol.json)**: a candidate pattern is keyed by
``(workload_id, diagnosed_cause)`` -- ``diagnosed_cause`` is the
decision-time-observable proxy for the underlying condition (a
deterministic function of ``context``, via the frozen
``src.evaluation.diagnosis.diagnose``, per Phase 3.6). The claim under
test for each candidate is a SYMPTOM -> CAUSE relationship: "does this
diagnosed_cause, for this workload, reliably correspond to one particular
true condition_id?" ``condition_id`` (Phase 4.0's generator ground truth)
is used to construct and evaluate this claim, but is NEVER exposed through
``PatternQuery`` -- exactly the same decision-time/evaluation-only split
Phase 4.1 enforced (src/experience/schema.py).

**Four evidence tiers**, mutually exclusive, assigned by
``src.patterns.discovery.assign_tier``:

- ``OBSERVED``: the candidate recurred (n_train >= MIN_OBSERVATIONS) but
  its train-split purity does not exceed the INFERRED threshold -- a bare
  recurrence fact with no established directional relationship.
- ``INFERRED``: train-split purity clears the INFERRED threshold, but not
  the (higher, replication-requiring) CONFIRMED bar.
- ``CONFIRMED``: train-split purity clears the CONFIRMED threshold AND
  the SAME relationship independently replicates on validation-split
  occurrences of the identical candidate key (calibration use of
  validation data, permitted per docs/PHASE4_PLAN.md section 3).
- ``UNCERTAIN``: n_train below MIN_OBSERVATIONS is not even a candidate
  (excluded); n_train at or just above the floor, but too small to trust
  any purity estimate (below CONFIRMED_MIN_N and the train purity itself
  does not clear INFERRED) falls here explicitly, rather than being
  silently folded into OBSERVED -- see discovery.py's precedence rule for
  the exact boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EvidenceTier(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class PatternQuery:
    """The ONLY information pattern APPLICATION (looking up a candidate's
    tier for a new incident) may condition on -- decision-time-observable,
    no condition_id, no outcome. Mirrors src.experience.schema.
    DecisionTimeQuery's structural role for Phase 4.1."""

    workload_id: str
    diagnosed_cause: Optional[str]


@dataclass(frozen=True)
class PatternCandidate:
    """One (workload_id, diagnosed_cause) candidate's full evidence
    record -- discovery (train) stats, calibration (validation) stats,
    and its assigned tier. ``mode_condition_train`` and both purity
    figures are constructed FROM condition_id ground truth during
    discovery/calibration (permitted -- see module docstring); they are
    never exposed via PatternQuery."""

    workload_id: str
    diagnosed_cause: Optional[str]
    n_train: int
    mode_condition_train: Optional[str]
    purity_train: Optional[float]
    n_validation: int
    purity_validation: Optional[float]  # purity of TRAIN's mode_condition on validation occurrences of this key; None if n_validation == 0
    tier: EvidenceTier
    protocol_version: str
    dataset_content_hash: str

    def query(self) -> PatternQuery:
        return PatternQuery(workload_id=self.workload_id, diagnosed_cause=self.diagnosed_cause)
