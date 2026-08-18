"""FROZEN schema for Active Phase 4.4 controlled sequential recovery episodes.

Extends the Phase 4.3 schema (``src.recovery.schema``, untouched -- Phase
4.3's frozen artifact) to a 2-step decision setting. Reuses every enum that
is unchanged by the Phase 4.4 protocol (``ActionId``, ``ScenarioFamily``,
``ValidatedOutcome``, ``Split``, ``SourceType``) directly from
``src.recovery.schema`` rather than redefining them -- the action
vocabulary, failure families, and outcome set are explicitly frozen
unchanged (docs/PHASE4_4_PROTOCOL.md sections 3, 10).

New in this module only what section 3/4 of the protocol actually adds:
- ``ObservationSignal``: the ternary step-1 noisy signal.
- ``DecisionContextV2``: step-1 fields, PLUS step1_action/step1_observation
  (populated only at step 2, ``None`` at step 1). Strict schema
  (``extra="forbid"``) -- constructing one with ``hidden_cause`` or
  ``step2_outcome`` must raise, per section 4's contamination-test
  requirement (see tests/recovery/test_schema_v2.py, written and passing
  before any policy code was written against this schema).
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.recovery.schema import (
    ActionId,
    ScenarioFamily,
    SourceType,
    Split,
    ValidatedOutcome,
)

SCHEMA_V2_VERSION = "4.4.0-controlled-sequential"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ObservationSignal(str, Enum):
    """The ternary step-1 noisy observation (protocol section 3)."""

    IMPROVED = "improved"
    NO_CHANGE = "no_change"
    WORSENED = "worsened"


class EpisodeOutcomeClass(str, Enum):
    """Terminal condition an episode actually ended in (protocol section 3)."""

    SUCCESS_STEP1 = "success_step1"
    SUCCESS_STEP2 = "success_step2"
    BUDGET_EXHAUSTED = "budget_exhausted"
    ABSTAIN_OR_ESCALATE = "abstain_or_escalate"


# ---------------------------------------------------------------------------
# Decision-time context -- the ONLY information a policy may condition on.
# ---------------------------------------------------------------------------


class DecisionContextV2(_Frozen):
    """Everything a sequential recovery policy may see before it acts.

    At step 1: ``step1_action`` and ``step1_observation`` are both ``None``.
    At step 2: both are populated with what actually happened at step 1.
    Deliberately excludes (and structurally cannot carry, via
    ``extra="forbid"`` + no such field declared): ``hidden_cause``, this
    episode's ``final_outcome``, ``step2_outcome`` before it occurs, or any
    information from another episode (protocol section 4 / config
    ``decision_context_boundary.forbidden``).
    """

    scenario_id: str
    episode_id: str
    family: ScenarioFamily
    symptom_pattern: str
    severity: str
    workload_type: str
    candidate_actions: list[ActionId]
    step: int  # 1 or 2
    step1_action: Optional[ActionId] = None
    step1_observation: Optional[ObservationSignal] = None

    @model_validator(mode="after")
    def _step_consistency(self) -> "DecisionContextV2":
        if self.step not in (1, 2):
            raise ValueError("step must be 1 or 2")
        if self.step == 1:
            if self.step1_action is not None or self.step1_observation is not None:
                raise ValueError("step1_action/step1_observation must be None at step 1")
        else:
            if self.step1_action is None or self.step1_observation is None:
                raise ValueError("step1_action/step1_observation must be populated at step 2")
        return self


class RecoveryScenarioV2(_Frozen):
    """The full 2-step scenario including ground truth. ``hidden_cause`` and
    the environment's ground-truth tables are visible only to
    ``src.recovery.environment_v2`` and the oracle/audit code path -- never
    passed to a policy's ``select_action`` call (same boundary as 4.3,
    src/recovery/schema.py's ``RecoveryScenario``)."""

    scenario_id: str
    family: ScenarioFamily
    hidden_cause: str
    step1_context: DecisionContextV2
    seed: int
    generator_version: str
    scenario_taxonomy_version: str


class StepTransition(_Frozen):
    """One step's environment-resolved outcome. Never visible to the policy
    before it acts at that step."""

    outcome: ValidatedOutcome
    unsafe_action_taken: bool
    recovery_latency_seconds: float
    recovery_cost: float
    validation_window_seconds: float
    partial: bool
    observation: Optional[ObservationSignal] = None  # noisy signal shown to the policy before step 2; None on the final step


class ActionSelectionV2(_Frozen):
    """What a policy returns for one decision point (step 1 or step 2)."""

    selected_action: ActionId
    policy_id: str
    policy_version: str
    step: int
    confidence: Optional[float] = None
    abstained: bool = False
    rationale: str = ""
    estimated_utility: dict[str, float] = Field(default_factory=dict)


class RecoveryProvenanceV2(_Frozen):
    source_type: SourceType = SourceType.CONTROLLED
    generator_version: str
    scenario_taxonomy_version: str
    action_vocabulary_version: str
    validation_rule_version: str
    protocol_version: str
    schema_version: str = SCHEMA_V2_VERSION
    split: Split
    seed: int
    episode_id: str
    creation_timestamp: datetime


class RecoveryEpisodeV2(_Frozen):
    """One complete, frozen, controlled 2-step recovery episode.

    ``step2_context``/``step2_selection``/``step2_transition`` are ``None``
    whenever the episode terminated at step 1 (success or abstain/escalate)
    -- the budget is at most 2 steps, not always exactly 2 (protocol
    section 3, terminal conditions).
    """

    episode_id: str
    scenario: RecoveryScenarioV2
    step1_selection: Optional[ActionSelectionV2] = None
    step1_transition: Optional[StepTransition] = None
    step2_context: Optional[DecisionContextV2] = None
    step2_selection: Optional[ActionSelectionV2] = None
    step2_transition: Optional[StepTransition] = None
    outcome_class: Optional[EpisodeOutcomeClass] = None
    provenance: RecoveryProvenanceV2
    schema_version: str = SCHEMA_V2_VERSION

    def content_hash(self) -> str:
        payload = self.model_dump_json(exclude={"provenance": {"creation_timestamp"}})
        return hashlib.sha256(payload.encode()).hexdigest()

    @model_validator(mode="after")
    def _scenario_episode_id_consistent(self) -> "RecoveryEpisodeV2":
        if self.scenario.step1_context.episode_id != self.episode_id:
            raise ValueError("episode_id mismatch between RecoveryEpisodeV2 and its step1 DecisionContext")
        if self.step2_context is not None and self.step2_context.episode_id != self.episode_id:
            raise ValueError("episode_id mismatch between RecoveryEpisodeV2 and its step2 DecisionContext")
        return self
