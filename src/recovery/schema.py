"""Frozen schema for Active Phase 4.3 controlled recovery episodes.

Design mirrors ``src.failure_experience.schema`` (Active Phase 4.1, PASS):
frozen pydantic models, explicit enums for closed outcome sets, and a hard
separation between what a policy may see at decision time
(``DecisionContext``) and what only the environment/evaluator may see
(``hidden_cause`` on ``RecoveryScenario``, everything on ``Transition``).

Every episode this schema can represent is CONTROLLED data (see
``SourceType``) -- this is enforced structurally: ``Provenance.source_type``
has no "real"/"observational" member at all in this schema version.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "4.3.0-controlled"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """Every record produced by src.recovery is one of these -- never
    "real" or "observational". This is the permanent evidence-type guard
    required by the Phase 4.3 brief (research integrity, section 5/38)."""

    CONTROLLED = "controlled"


class ScenarioFamily(str, Enum):
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TRANSIENT_FAILURE = "transient_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    DEPENDENCY_FAILURE = "dependency_failure"


class SafetyClass(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"


class ActionId(str, Enum):
    RETRY = "retry"
    RESTART = "restart"
    ROLLBACK = "rollback"
    RECONFIGURE = "reconfigure"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    ABSTAIN = "abstain"
    FORCE_RESTART = "force_restart"  # the one UNSAFE action in the frozen vocabulary


class ValidatedOutcome(str, Enum):
    """The closed outcome set every episode's validated outcome must fall
    into (Phase 4.3 brief section 13)."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    UNSAFE = "unsafe"
    TIMEOUT = "timeout"
    UNRECOVERABLE = "unrecoverable"


class Split(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


# ---------------------------------------------------------------------------
# Decision-time context -- the ONLY information a policy may condition on.
# ---------------------------------------------------------------------------


class DecisionContext(_Frozen):
    """Everything a recovery-selection policy is allowed to see before it
    picks an action. Deliberately excludes ``hidden_cause`` and anything
    about the outcome -- see docs/PHASE4_3_RECOVERY_LEARNING.md section 11
    (decision-time information boundary) and the leakage audit
    (benchmarks/phase4_3_recovery_leakage_audit.py) which asserts this
    type never carries a ``hidden_cause`` or outcome field, by construction
    (pydantic ``extra="forbid"``, no such field declared)."""

    scenario_id: str
    episode_id: str
    family: ScenarioFamily
    symptom_pattern: str            # noisy bucketed signal, NOT a deterministic function of hidden_cause
    severity: str                   # "low" | "medium" | "high", noisy
    workload_type: str
    candidate_actions: list[ActionId]


class RecoveryScenario(_Frozen):
    """The full scenario, including ground truth. ``hidden_cause`` and the
    truth table used to compute outcomes are available to the environment
    and to the frozen-protocol/oracle code path only -- never passed to a
    policy's ``select_action`` call. See ``DecisionContext`` above."""

    scenario_id: str
    family: ScenarioFamily
    hidden_cause: str
    decision_context: DecisionContext
    seed: int
    generator_version: str
    scenario_taxonomy_version: str


class Transition(_Frozen):
    """The environment's deterministic-given-seed transition result for one
    (scenario, action) pair. Never visible to the policy before it acts."""

    outcome: ValidatedOutcome
    unsafe_action_taken: bool
    recovery_latency_seconds: float
    recovery_cost: float
    validation_window_seconds: float
    partial: bool


class ActionSelection(_Frozen):
    """What a policy actually returns for one decision point."""

    selected_action: ActionId
    policy_id: str
    policy_version: str
    confidence: Optional[float] = None
    abstained: bool = False
    rationale: str = ""
    estimated_utility: dict[str, float] = Field(default_factory=dict)


class RecoveryProvenance(_Frozen):
    source_type: SourceType = SourceType.CONTROLLED
    generator_version: str
    scenario_taxonomy_version: str
    action_vocabulary_version: str
    validation_rule_version: str
    protocol_version: str
    schema_version: str = SCHEMA_VERSION
    split: Split
    seed: int
    episode_id: str
    creation_timestamp: datetime


class RecoveryEpisode(_Frozen):
    """One complete, frozen, controlled recovery episode: a scenario, the
    action a given policy selected, and the validated transition/outcome.
    This is the unit of analysis (Phase 4.3 brief section 9)."""

    episode_id: str
    scenario: RecoveryScenario
    policy_selection: Optional[ActionSelection] = None
    transition: Optional[Transition] = None
    provenance: RecoveryProvenance
    schema_version: str = SCHEMA_VERSION

    def content_hash(self) -> str:
        payload = self.model_dump_json(exclude={"provenance": {"creation_timestamp"}})
        return hashlib.sha256(payload.encode()).hexdigest()

    @model_validator(mode="after")
    def _scenario_episode_id_consistent(self) -> "RecoveryEpisode":
        if self.scenario.decision_context.episode_id != self.episode_id:
            raise ValueError("episode_id mismatch between RecoveryEpisode and its DecisionContext")
        return self
