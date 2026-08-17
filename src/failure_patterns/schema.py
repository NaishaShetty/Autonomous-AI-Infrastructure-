"""ACTIVE Phase 4.2 pattern representation.

Built fresh against ``src.failure_experience`` concepts and the frozen
``configs/phase4_2_active_pattern_protocol.json``, not against the old,
historical ``src/patterns/schema.py`` (never imported here -- see that
module's docstring and ``docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md`` for why
its exact candidate key/metric do not transfer).

Two candidate shapes are represented:

- ``PatternCandidate`` (Pattern Type 1, Alibaba primary): a
  ``(task_name, gpu_type)`` context with train/validation/test rate
  evidence and a frozen :class:`EvidenceTier`.
- ``DescriptiveAssociation`` (Pattern Type 2, AIOps/AgentRx): a recurring
  association key with a bare occurrence count -- no train/test boundary,
  no tier beyond OBSERVED (no dataset here has a frozen split for these
  two sources, so CONFIRMED is structurally unreachable; see the
  protocol's ``descriptive_only_sources`` block).

``PatternQuery`` is the ONLY structural type "pattern application" code
may use to look a candidate up -- it deliberately cannot carry
observed-outcome/rate/label information, mirroring the decision-time /
evaluation-only split the old Phase 4.2 (via its own ``PatternQuery``) and
active Phase 4.1 (via ``DecisionTimeQuery``) both already enforce. This is
a structural leakage guard, not a convention: attempting to construct a
``PatternQuery`` with a rate/outcome field is a ``TypeError`` at
instantiation time because no such field exists on the dataclass.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EvidenceTier(str, Enum):
    """OBSERVED = recurrence exists. INFERRED = recurrence + train-split
    rate elevation clears the frozen margin. CONFIRMED = INFERRED AND the
    same elevation independently replicates on validation-split
    occurrences of the identical key. UNCERTAIN = recurs but n_train is
    below the trusted-sample floor. See the frozen protocol's
    ``evidence_tiers.assignment_precedence`` for the exact rule."""

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class PatternQuery:
    """The ONLY information pattern APPLICATION may condition on --
    decision-time-observable, structurally excludes any rate/outcome/
    label field. A caller wanting to know "what does discovery believe
    about this context" may only ever construct one of these two fields;
    there is no third field to smuggle a rate or label through."""

    task_name: str
    gpu_type: str


@dataclass(frozen=True)
class PatternCandidate:
    """One ``(task_name, gpu_type)`` candidate's full evidence record --
    discovery (train) stats, calibration (validation) stats, and its
    frozen tier. Rate/count fields below are DISCOVERY/EVALUATION-ONLY
    information: they are computed FROM observed Failed/Terminated/
    Running labels during discovery/calibration (permitted -- see the
    protocol's ``evaluation_sequence``), and are never exposed through
    :class:`PatternQuery`."""

    task_name: str
    gpu_type: str
    n_train: int
    train_rate: Optional[float]
    train_baseline_rate: Optional[float]
    n_validation: int
    validation_rate: Optional[float]
    validation_baseline_rate: Optional[float]
    tier: EvidenceTier
    protocol_version: str
    dataset_content_hash: str
    split_name: str

    def query(self) -> PatternQuery:
        return PatternQuery(task_name=self.task_name, gpu_type=self.gpu_type)

    @property
    def train_elevation(self) -> Optional[float]:
        if self.train_rate is None or self.train_baseline_rate is None:
            return None
        return self.train_rate - self.train_baseline_rate

    @property
    def validation_elevation(self) -> Optional[float]:
        if self.validation_rate is None or self.validation_baseline_rate is None:
            return None
        return self.validation_rate - self.validation_baseline_rate


@dataclass(frozen=True)
class AlibabaTestOutcome:
    """Evaluation-only record produced during the frozen, one-time
    test-split pass -- never constructed before ``step_4_test_evaluation``
    in the frozen protocol, and never fed back into discovery/validation
    decisions."""

    task_name: str
    gpu_type: str
    n_test: int
    test_rate: Optional[float]
    test_baseline_rate: Optional[float]

    @property
    def test_elevated(self) -> Optional[bool]:
        if self.test_rate is None or self.test_baseline_rate is None:
            return None
        return (self.test_rate - self.test_baseline_rate) >= 0.0  # margin applied by caller


@dataclass(frozen=True)
class DescriptiveAssociation:
    """Pattern Type 2 (AIOps / AgentRx): a recurring association key with
    a bare occurrence count. No train/validation/test boundary exists for
    either source (no frozen split), so this type carries no rate/tier
    fields beyond a simple OBSERVED/not-a-candidate distinction -- it is
    structurally incapable of reaching CONFIRMED, by design, not omission.
    """

    dataset: str
    key: tuple
    count: int
    is_candidate: bool  # count >= minimum_evidence_n
