"""Recovery-selection policies for Active Phase 4.4: baselines, the
proposed sequential mechanism, and the single-step ablation.

DECISION-TIME BOUNDARY: every ``select_step1``/``select_step2`` below takes
only a ``DecisionContextV2`` (schema_v2.py, ``extra="forbid"``, no
``hidden_cause``, no future information).

``FixedPrioritySequential`` below was authored using ONLY the protocol
document's domain reasoning (section 5, item 1) and the frozen action
vocabulary/taxonomy module (``src.recovery.taxonomy``, which encodes family
structure and candidate actions but NOT the ground-truth outcome
probabilities -- those live in ``src.recovery.environment._OUTCOME_TABLE``,
which this module does not import). It was written and committed BEFORE
any TRAIN/VALIDATION/TEST data for Phase 4.4 was generated or viewed (see
the Step 4 commit in git history, which lands before
benchmarks/phase4_4_generate_dataset.py's dataset-generation commit).
"""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from src.recovery.actions import ACTIONS, is_unsafe
from src.recovery.schema import ActionId, ScenarioFamily
from src.recovery.schema_v2 import ActionSelectionV2, DecisionContextV2, ObservationSignal, RecoveryEpisodeV2
from src.recovery.taxonomy import safe_candidate_actions

POLICY_V2_MODULE_VERSION = "phase4_4_policy_v1"

_SUCCESS_VALUE = 1.0
_PARTIAL_VALUE = 0.5


def _expected_utility(p_success: float, p_partial: float, action: ActionId) -> float:
    spec = ACTIONS[action]
    expected_outcome_value = p_success * _SUCCESS_VALUE + p_partial * _PARTIAL_VALUE
    return expected_outcome_value - 0.02 * spec.base_cost - 0.001 * spec.base_latency_seconds


# ---------------------------------------------------------------------------
# Baseline 1 (primary comparator): FixedPrioritySequential
# ---------------------------------------------------------------------------
#
# Domain reasoning (authored before viewing any generated Phase 4.4 data):
#
# - RESOURCE_EXHAUSTION: a restart clears in-memory state, which is the
#   generally correct first move for a resource-pressure symptom regardless
#   of whether the true cause turns out to be a slow leak or a transient
#   spike -- retrying without clearing state rarely helps a resource
#   problem. Step 1: RESTART. If step 1 didn't fully resolve it: an
#   IMPROVED/NO_CHANGE reading means restart was plausibly on the right
#   track (partially worked, or at least didn't make it worse) -- retry the
#   same restart once more (a fresh restart can still help if the first one
#   raced with the leak). A WORSENED reading suggests restarting is not the
#   fix -- fall back to plain RETRY.
# - TRANSIENT_FAILURE: transient failures are, by definition, often
#   self-resolving -- RETRY is the cheap, low-disruption first move,
#   escalating to a RESTART (clears more state, appropriate if the
#   dependency looks properly stuck) only if the observation says retrying
#   didn't help or made it worse.
# - CONFIGURATION_FAILURE: this family has a genuine two-sided ambiguity
#   (bad recent change vs. stale config) that a single first action cannot
#   resolve -- RECONFIGURE (targeted fix, appropriate for a recent bad
#   change) is the reasonable first guess since it is the more common
#   failure mode operationally (a fresh bad change is more common than a
#   config silently going stale). If the step-1 observation says WORSENED
#   or NO_CHANGE, that is exactly the situation where a different lever is
#   warranted -- switch to ROLLBACK (appropriate if the cause is instead a
#   stale/previously-good config that reconfiguring under uncertainty
#   didn't fix). If IMPROVED, stay the course and retry RECONFIGURE.
# - DEPENDENCY_FAILURE: this family's own step-1 default already leans
#   conservative (RETRY, since ESCALATE_TO_HUMAN/ABSTAIN are always
#   available and FORCE_RESTART is unsafe and excluded entirely). If step 1
#   didn't work, retrying blind a second time against a downstream
#   dependency that may still be down risks nothing new -- ABSTAIN (wait
#   and re-observe) is the safer second move than repeating an action that
#   already failed once against what may be a genuine outage, unless the
#   signal says IMPROVED (in which case the dependency is recovering on its
#   own -- retry once more to catch it).

_STEP1_ACTION: dict[ScenarioFamily, ActionId] = {
    ScenarioFamily.RESOURCE_EXHAUSTION: ActionId.RESTART,
    ScenarioFamily.TRANSIENT_FAILURE: ActionId.RETRY,
    ScenarioFamily.CONFIGURATION_FAILURE: ActionId.RECONFIGURE,
    ScenarioFamily.DEPENDENCY_FAILURE: ActionId.RETRY,
}


def _fixed_priority_sequential_step2(family: ScenarioFamily, step1_action: ActionId, observation: ObservationSignal) -> ActionId:
    if family == ScenarioFamily.RESOURCE_EXHAUSTION:
        return step1_action if observation != ObservationSignal.WORSENED else ActionId.RETRY
    if family == ScenarioFamily.TRANSIENT_FAILURE:
        return step1_action if observation != ObservationSignal.WORSENED else ActionId.RESTART
    if family == ScenarioFamily.CONFIGURATION_FAILURE:
        return ActionId.ROLLBACK if observation in (ObservationSignal.WORSENED, ObservationSignal.NO_CHANGE) else step1_action
    if family == ScenarioFamily.DEPENDENCY_FAILURE:
        return ActionId.RETRY if observation == ObservationSignal.IMPROVED else ActionId.ABSTAIN
    raise ValueError(f"unhandled family {family}")


class FixedPrioritySequential:
    """Baseline 1 (primary comparator): a hand-written rule that DOES
    condition on the step-1 observation. Authored before viewing any
    generated data (see module docstring)."""

    policy_id = "baseline_fixed_priority_sequential"
    policy_version = "v1"

    def select_step1(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        action = _STEP1_ACTION[ctx.family]
        if action not in ctx.candidate_actions:
            action = safe_candidate_actions(ctx.family)[0]
        return ActionSelectionV2(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version, step=1,
            rationale=f"fixed step-1 priority for {ctx.family.value}",
        )

    def select_step2(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        if ctx.step1_action is None or ctx.step1_observation is None:
            raise ValueError("select_step2 requires step1_action/step1_observation populated")
        action = _fixed_priority_sequential_step2(ctx.family, ctx.step1_action, ctx.step1_observation)
        safe = set(safe_candidate_actions(ctx.family))
        if action not in safe or action not in ctx.candidate_actions:
            action = ActionId.ESCALATE_TO_HUMAN if ActionId.ESCALATE_TO_HUMAN in ctx.candidate_actions else safe_candidate_actions(ctx.family)[0]
        return ActionSelectionV2(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version, step=2,
            rationale=f"fixed step-2 rule conditioning on step1_action={ctx.step1_action.value}, "
                      f"step1_observation={ctx.step1_observation.value}",
        )


# ---------------------------------------------------------------------------
# Baseline 2 (lower bound): RandomValidSequential
# ---------------------------------------------------------------------------


class RandomValidSequential:
    """Baseline 2: uniform-random safe action at each step, independent of
    history. Per-episode-and-step-derived RNG for reproducibility."""

    policy_id = "baseline_random_valid_sequential"
    policy_version = "v1"

    def _pick(self, ctx: DecisionContextV2) -> ActionId:
        safe = [a for a in ctx.candidate_actions if a in set(safe_candidate_actions(ctx.family))]
        rng = random.Random(f"{self.policy_id}|{ctx.episode_id}|step{ctx.step}")
        return safe[rng.randrange(len(safe))]

    def select_step1(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        action = self._pick(ctx)
        return ActionSelectionV2(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version, step=1,
            rationale="uniform-random over safe candidate actions",
        )

    def select_step2(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        action = self._pick(ctx)
        return ActionSelectionV2(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version, step=2,
            rationale="uniform-random over safe candidate actions (history-independent)",
        )


# ---------------------------------------------------------------------------
# Baseline 4 (ablation comparator): SingleStepEmpirical
# ---------------------------------------------------------------------------
# Wraps Phase 4.3's EmpiricalRecoveryPolicy (imported, not duplicated) via
# src.recovery.policy, forced to terminate after step 1 -- used only for
# H4-ABLATION.


class SingleStepEmpirical:
    """Baseline 4: Phase 4.3's trained EmpiricalRecoveryPolicy, applied once
    at step 1, then forced to terminate regardless of outcome (no step 2).
    Isolates whether a two-step proposed-policy win comes from genuine
    history-conditioning or merely from having a second attempt
    (H4-ABLATION)."""

    policy_id = "single_step_empirical_ablation"
    policy_version = "v1"

    def __init__(self, inner):
        """``inner``: a fitted ``src.recovery.policy.EmpiricalRecoveryPolicy``."""
        self.inner = inner

    def select_step1(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        from src.recovery.schema import DecisionContext as DecisionContextV1
        v1_ctx = DecisionContextV1(
            scenario_id=ctx.scenario_id, episode_id=ctx.episode_id, family=ctx.family,
            symptom_pattern=ctx.symptom_pattern, severity=ctx.severity, workload_type=ctx.workload_type,
            candidate_actions=ctx.candidate_actions,
        )
        v1_selection = self.inner.select_action(v1_ctx)
        return ActionSelectionV2(
            selected_action=v1_selection.selected_action, policy_id=self.policy_id, policy_version=self.policy_version,
            step=1, confidence=v1_selection.confidence, abstained=v1_selection.abstained,
            rationale=f"phase4.3 EmpiricalRecoveryPolicy (forced single-step): {v1_selection.rationale}",
            estimated_utility=v1_selection.estimated_utility,
        )

    # No select_step2: this baseline never takes a step 2 by construction.


# ---------------------------------------------------------------------------
# Proposed mechanism: sequential empirical success-rate policy
# ---------------------------------------------------------------------------


@dataclass
class _Stat:
    successes: float = 0.0
    partials: float = 0.0
    trials: int = 0


class SequentialEmpiricalRecoveryPolicy:
    """The proposed context-aware mechanism (protocol section 6).

    Retrieval/backoff hierarchy at step 2 (most to least specific):
      1. (family, symptom, severity, step1_action, step1_observation, action)
      2. (family, symptom, step1_action, step1_observation, action)
      3. (family, step1_action, step1_observation, action)
      4. (family, symptom, severity, action)   [ignores step-1 history]
      5. (family, action)
    Step 1 uses the SAME hierarchy Phase 4.3 used (no step-1 history
    exists yet): (family, symptom, severity, action) -> (family, action).
    Laplace(+1,+1,+2) smoothing throughout, same as 4.3. Abstains
    (min_evidence gate) exactly as 4.3's EmpiricalRecoveryPolicy does. No
    RL, sequence models, or neural architectures (protocol section 6).
    """

    policy_id = "proposed_sequential_empirical_recovery"
    policy_version = "v1"

    def __init__(self, min_evidence: int = 5):
        self.min_evidence = min_evidence
        self._step1_fine: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step1_coarse: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step2_finest: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step2_mid: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step2_history_only: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step2_no_history_fine: dict[tuple, _Stat] = defaultdict(_Stat)
        self._step2_coarse: dict[tuple, _Stat] = defaultdict(_Stat)
        self._fitted = False

    def fit(self, train_episodes: list[RecoveryEpisodeV2]) -> "SequentialEmpiricalRecoveryPolicy":
        for ep in train_episodes:
            if ep.step1_selection is None or ep.step1_transition is None:
                continue
            ctx1 = ep.scenario.step1_context
            a1 = ep.step1_selection.selected_action
            fine1 = (ctx1.family.value, ctx1.symptom_pattern, ctx1.severity, a1.value)
            coarse1 = (ctx1.family.value, a1.value)
            s1_success = 1.0 if ep.step1_transition.outcome.value == "success" else 0.0
            s1_partial = 1.0 if ep.step1_transition.outcome.value == "partial_success" else 0.0
            for table, key in ((self._step1_fine, fine1), (self._step1_coarse, coarse1)):
                st = table[key]
                st.successes += s1_success
                st.partials += s1_partial
                st.trials += 1

            if ep.step2_context is None or ep.step2_selection is None or ep.step2_transition is None:
                continue
            ctx2 = ep.step2_context
            a2 = ep.step2_selection.selected_action
            obs = ctx2.step1_observation.value
            finest = (ctx2.family.value, ctx2.symptom_pattern, ctx2.severity, a1.value, obs, a2.value)
            mid = (ctx2.family.value, ctx2.symptom_pattern, a1.value, obs, a2.value)
            hist_only = (ctx2.family.value, a1.value, obs, a2.value)
            no_hist_fine = (ctx2.family.value, ctx2.symptom_pattern, ctx2.severity, a2.value)
            coarse2 = (ctx2.family.value, a2.value)
            s2_success = 1.0 if ep.step2_transition.outcome.value == "success" else 0.0
            s2_partial = 1.0 if ep.step2_transition.outcome.value == "partial_success" else 0.0
            for table, key in (
                (self._step2_finest, finest), (self._step2_mid, mid), (self._step2_history_only, hist_only),
                (self._step2_no_history_fine, no_hist_fine), (self._step2_coarse, coarse2),
            ):
                st = table[key]
                st.successes += s2_success
                st.partials += s2_partial
                st.trials += 1
        self._fitted = True
        return self

    def _lookup_step1(self, ctx: DecisionContextV2, action: ActionId) -> tuple[float, float, int]:
        for stat in (
            self._step1_fine[(ctx.family.value, ctx.symptom_pattern, ctx.severity, action.value)],
            self._step1_coarse[(ctx.family.value, action.value)],
        ):
            if stat.trials > 0:
                n = stat.trials
                return (stat.successes + 1) / (n + 2), (stat.partials + 1) / (n + 2), n
        return 0.5, 0.25, 0

    def _lookup_step2(self, ctx: DecisionContextV2, action: ActionId) -> tuple[float, float, int]:
        obs = ctx.step1_observation.value
        a1 = ctx.step1_action.value
        candidates = [
            self._step2_finest[(ctx.family.value, ctx.symptom_pattern, ctx.severity, a1, obs, action.value)],
            self._step2_mid[(ctx.family.value, ctx.symptom_pattern, a1, obs, action.value)],
            self._step2_history_only[(ctx.family.value, a1, obs, action.value)],
            self._step2_no_history_fine[(ctx.family.value, ctx.symptom_pattern, ctx.severity, action.value)],
            self._step2_coarse[(ctx.family.value, action.value)],
        ]
        for stat in candidates:
            if stat.trials > 0:
                n = stat.trials
                return (stat.successes + 1) / (n + 2), (stat.partials + 1) / (n + 2), n
        return 0.5, 0.25, 0

    def _select(self, ctx: DecisionContextV2, lookup) -> ActionSelectionV2:
        if not self._fitted:
            raise RuntimeError("SequentialEmpiricalRecoveryPolicy.select called before fit()")
        safe = set(safe_candidate_actions(ctx.family))
        scored = []
        for action in ctx.candidate_actions:
            if action not in safe:
                continue
            p_success, p_partial, n = lookup(ctx, action)
            eu = _expected_utility(p_success, p_partial, action)
            scored.append((eu, n, action))
        scored.sort(key=lambda t: t[0], reverse=True)
        best_eu, best_n, best_action = scored[0]

        if best_n < self.min_evidence:
            fallback = ActionId.ABSTAIN if ActionId.ABSTAIN in ctx.candidate_actions else ActionId.ESCALATE_TO_HUMAN
            return ActionSelectionV2(
                selected_action=fallback, policy_id=self.policy_id, policy_version=self.policy_version, step=ctx.step,
                confidence=best_n / max(1, self.min_evidence), abstained=True,
                rationale=f"insufficient evidence (n={best_n} < min_evidence={self.min_evidence}) for best candidate {best_action.value}",
                estimated_utility={a.value: eu for eu, n, a in scored},
            )
        return ActionSelectionV2(
            selected_action=best_action, policy_id=self.policy_id, policy_version=self.policy_version, step=ctx.step,
            confidence=min(1.0, best_n / max(1, self.min_evidence)), abstained=False,
            rationale=f"max expected utility ({best_eu:.3f}) with n={best_n} supporting examples",
            estimated_utility={a.value: eu for eu, n, a in scored},
        )

    def select_step1(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        return self._select(ctx, self._lookup_step1)

    def select_step2(self, ctx: DecisionContextV2) -> ActionSelectionV2:
        return self._select(ctx, self._lookup_step2)


class SequentialEmpiricalRecoveryPolicyNoAbstention(SequentialEmpiricalRecoveryPolicy):
    """H4-ABSTENTION comparator: identical mechanism, abstention disabled
    (never falls back to ABSTAIN/ESCALATE_TO_HUMAN for insufficient
    evidence -- always takes the best-scoring action instead)."""

    policy_id = "proposed_sequential_empirical_recovery_no_abstention"

    def _select(self, ctx: DecisionContextV2, lookup) -> ActionSelectionV2:
        if not self._fitted:
            raise RuntimeError("SequentialEmpiricalRecoveryPolicyNoAbstention.select called before fit()")
        safe = set(safe_candidate_actions(ctx.family))
        scored = []
        for action in ctx.candidate_actions:
            if action not in safe:
                continue
            p_success, p_partial, n = lookup(ctx, action)
            eu = _expected_utility(p_success, p_partial, action)
            scored.append((eu, n, action))
        scored.sort(key=lambda t: t[0], reverse=True)
        best_eu, best_n, best_action = scored[0]
        return ActionSelectionV2(
            selected_action=best_action, policy_id=self.policy_id, policy_version=self.policy_version, step=ctx.step,
            confidence=min(1.0, best_n / max(1, self.min_evidence)), abstained=False,
            rationale=f"max expected utility ({best_eu:.3f}) with n={best_n} supporting examples (abstention disabled)",
            estimated_utility={a.value: eu for eu, n, a in scored},
        )
