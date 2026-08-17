"""Recovery-selection policies for Active Phase 4.3: baselines, the proposed
context-aware mechanism, and pre-registered ablations.

DECISION-TIME BOUNDARY: every ``select_action`` below takes only a
``DecisionContext`` (no ``hidden_cause``, no outcome, no future information
-- see schema.py). ``EmpiricalRecoveryPolicy.fit`` consumes completed TRAIN
``RecoveryEpisode`` objects (which do carry ``transition``/outcome, because
they are already-resolved historical experience, exactly like a real
``FailureExperience`` retrieval corpus) but never sees the hidden cause of
the episode currently being decided.

Proposed-mechanism choice (brief section 23): the simplest mechanism that
is still scientifically meaningful -- an experience-based empirical
success-rate lookup with a symptom-bucket backoff hierarchy and an explicit
evidence-count abstention rule. No reinforcement learning, no neural
network (brief section 39: don't over-engineer the first mechanism).
"""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from src.recovery.actions import ACTIONS, is_unsafe
from src.recovery.schema import ActionId, ActionSelection, DecisionContext, RecoveryEpisode, ScenarioFamily
from src.recovery.taxonomy import TAXONOMY, safe_candidate_actions
from src.recovery.utility import recovery_utility

POLICY_MODULE_VERSION = "phase4_3_policy_v1"

# Estimated outcome value used when RANKING actions before an outcome is
# known (decision time) -- NOT the same as utility.recovery_utility, which
# scores an already-observed outcome. This is the policy's own internal
# expected-utility estimate, built only from estimated success/partial
# rates and each action's *nominal* (pre-outcome) cost/latency.
_SUCCESS_VALUE = 1.0
_PARTIAL_VALUE = 0.5
_FAILURE_VALUE = 0.0


def _expected_utility(p_success: float, p_partial: float, action: ActionId) -> float:
    spec = ACTIONS[action]
    expected_outcome_value = p_success * _SUCCESS_VALUE + p_partial * _PARTIAL_VALUE
    return expected_outcome_value - 0.02 * spec.base_cost - 0.001 * spec.base_latency_seconds


# ---------------------------------------------------------------------------
# Baseline A: fixed rule-based priority policy
# ---------------------------------------------------------------------------

FIXED_PRIORITY: dict[ScenarioFamily, list[ActionId]] = {
    ScenarioFamily.RESOURCE_EXHAUSTION: [ActionId.RESTART, ActionId.RETRY, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN],
    ScenarioFamily.TRANSIENT_FAILURE: [ActionId.RETRY, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN],
    ScenarioFamily.CONFIGURATION_FAILURE: [ActionId.RECONFIGURE, ActionId.ROLLBACK, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN],
    ScenarioFamily.DEPENDENCY_FAILURE: [ActionId.RETRY, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN],
}


class FixedPriorityPolicy:
    """Baseline A: a fixed, non-learning priority order per family, frozen
    before any evaluation (domain-heuristic, not fit to data)."""

    policy_id = "baseline_fixed_priority"
    policy_version = "v1"

    def select_action(self, ctx: DecisionContext) -> ActionSelection:
        order = FIXED_PRIORITY[ctx.family]
        safe = set(safe_candidate_actions(ctx.family))
        for action in order:
            if action in ctx.candidate_actions and action in safe:
                return ActionSelection(
                    selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version,
                    rationale=f"first-available in fixed priority order for {ctx.family.value}",
                )
        raise RuntimeError(f"FixedPriorityPolicy found no safe action for {ctx}")


# ---------------------------------------------------------------------------
# Baseline B: random valid (safe) action
# ---------------------------------------------------------------------------


class RandomValidPolicy:
    """Baseline B: uniform-random among safe candidate actions. Uses a
    per-episode-derived RNG (not global random state) so evaluation is
    reproducible given the episode id."""

    policy_id = "baseline_random_valid"
    policy_version = "v1"

    def select_action(self, ctx: DecisionContext) -> ActionSelection:
        safe = [a for a in ctx.candidate_actions if a in set(safe_candidate_actions(ctx.family))]
        rng = random.Random(f"{self.policy_id}|{ctx.episode_id}")
        action = safe[rng.randrange(len(safe))]
        return ActionSelection(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version,
            rationale="uniform-random over safe candidate actions",
        )


# ---------------------------------------------------------------------------
# Proposed mechanism: experience-based empirical success-rate policy
# ---------------------------------------------------------------------------


@dataclass
class _Stat:
    successes: float = 0.0
    partials: float = 0.0
    trials: int = 0


class EmpiricalRecoveryPolicy:
    """The proposed context-aware recovery-selection mechanism.

    Retrieval/backoff hierarchy (most to least specific):
      1. (family, symptom_pattern, severity, action)
      2. (family, symptom_pattern, action)
      3. (family, action)
    Falls back to the least specific bucket with any evidence; if NO bucket
    has evidence >= ``min_evidence`` for the *best-looking* action, the
    policy abstains (or escalates if ABSTAIN is not a candidate) rather than
    guessing -- brief section 24, "do not force an action when evidence is
    insufficient". ``min_evidence`` is selected on VALIDATION, not TEST
    (brief section 17, "use VALIDATION for all pre-test policy decisions").
    """

    policy_id = "proposed_empirical_recovery"
    policy_version = "v1"

    def __init__(self, min_evidence: int = 5, use_context: bool = True, allow_abstention: bool = True):
        self.min_evidence = min_evidence
        self.use_context = use_context
        self.allow_abstention = allow_abstention
        self._fine: dict[tuple, _Stat] = defaultdict(_Stat)
        self._mid: dict[tuple, _Stat] = defaultdict(_Stat)
        self._coarse: dict[tuple, _Stat] = defaultdict(_Stat)
        self._fitted = False

    def fit(self, train_episodes: list[RecoveryEpisode]) -> "EmpiricalRecoveryPolicy":
        for ep in train_episodes:
            if ep.transition is None or ep.policy_selection is None:
                continue
            ctx = ep.scenario.decision_context
            action = ep.policy_selection.selected_action
            fine_key = (ctx.family.value, ctx.symptom_pattern, ctx.severity, action.value)
            mid_key = (ctx.family.value, ctx.symptom_pattern, action.value)
            coarse_key = (ctx.family.value, action.value)
            is_success = 1.0 if ep.transition.outcome.value == "success" else 0.0
            is_partial = 1.0 if ep.transition.outcome.value == "partial_success" else 0.0
            for table, key in ((self._fine, fine_key), (self._mid, mid_key), (self._coarse, coarse_key)):
                stat = table[key]
                stat.successes += is_success
                stat.partials += is_partial
                stat.trials += 1
        self._fitted = True
        return self

    def _lookup(self, ctx: DecisionContext, action: ActionId) -> tuple[float, float, int]:
        """Returns (p_success, p_partial, evidence_n) using the most
        specific bucket with any evidence; Laplace(+1,+1,+2) smoothing."""
        candidates = []
        if self.use_context:
            candidates.append(self._fine[(ctx.family.value, ctx.symptom_pattern, ctx.severity, action.value)])
            candidates.append(self._mid[(ctx.family.value, ctx.symptom_pattern, action.value)])
        candidates.append(self._coarse[(ctx.family.value, action.value)])

        for stat in candidates:
            if stat.trials > 0:
                n = stat.trials
                p_success = (stat.successes + 1) / (n + 2)
                p_partial = (stat.partials + 1) / (n + 2)
                return p_success, p_partial, n
        return 0.5, 0.25, 0  # no evidence anywhere: uninformative prior, n=0 triggers abstention

    def select_action(self, ctx: DecisionContext) -> ActionSelection:
        if not self._fitted:
            raise RuntimeError("EmpiricalRecoveryPolicy.select_action called before fit()")
        safe = set(safe_candidate_actions(ctx.family))
        scored = []
        for action in ctx.candidate_actions:
            if action not in safe:
                continue
            p_success, p_partial, n = self._lookup(ctx, action)
            eu = _expected_utility(p_success, p_partial, action)
            scored.append((eu, n, action, p_success, p_partial))
        scored.sort(key=lambda t: t[0], reverse=True)
        best_eu, best_n, best_action, p_success, p_partial = scored[0]

        if self.allow_abstention and best_n < self.min_evidence:
            fallback = ActionId.ABSTAIN if ActionId.ABSTAIN in ctx.candidate_actions else ActionId.ESCALATE_TO_HUMAN
            return ActionSelection(
                selected_action=fallback, policy_id=self.policy_id, policy_version=self.policy_version,
                confidence=best_n / max(1, self.min_evidence), abstained=True,
                rationale=f"insufficient evidence (n={best_n} < min_evidence={self.min_evidence}) for best candidate {best_action.value}",
                estimated_utility={a.value: eu for eu, n, a, ps, pp in scored},
            )

        return ActionSelection(
            selected_action=best_action, policy_id=self.policy_id, policy_version=self.policy_version,
            confidence=min(1.0, best_n / max(1, self.min_evidence)), abstained=False,
            rationale=f"max expected utility ({best_eu:.3f}) with n={best_n} supporting examples",
            estimated_utility={a.value: eu for eu, n, a, ps, pp in scored},
        )


# ---------------------------------------------------------------------------
# Ablation variants (pre-registered, brief section 30)
# ---------------------------------------------------------------------------


class FrequencyOnlyPolicy:
    """Ablation B: "memory without outcome information" -- picks the action
    most frequently *taken* in TRAIN for this bucket, ignoring whether it
    succeeded. Uses the same retrieval buckets as the proposed policy but
    only trials counts, not success counts."""

    policy_id = "ablation_frequency_only"
    policy_version = "v1"

    def __init__(self):
        self._counts: dict[tuple, dict[ActionId, int]] = defaultdict(lambda: defaultdict(int))
        self._fitted = False

    def fit(self, train_episodes: list[RecoveryEpisode]) -> "FrequencyOnlyPolicy":
        for ep in train_episodes:
            if ep.policy_selection is None:
                continue
            ctx = ep.scenario.decision_context
            key = (ctx.family.value,)
            self._counts[key][ep.policy_selection.selected_action] += 1
        self._fitted = True
        return self

    def select_action(self, ctx: DecisionContext) -> ActionSelection:
        if not self._fitted:
            raise RuntimeError("FrequencyOnlyPolicy.select_action called before fit()")
        safe = set(safe_candidate_actions(ctx.family))
        counts = self._counts[(ctx.family.value,)]
        ranked = sorted((a for a in ctx.candidate_actions if a in safe), key=lambda a: counts.get(a, 0), reverse=True)
        action = ranked[0] if ranked and counts.get(ranked[0], 0) > 0 else FIXED_PRIORITY[ctx.family][0]
        return ActionSelection(
            selected_action=action, policy_id=self.policy_id, policy_version=self.policy_version,
            rationale="most frequently taken action in TRAIN for this family (outcome-blind)",
        )


class UnmaskedUtilityPolicy:
    """Safety ablation: identical to ``EmpiricalRecoveryPolicy`` except it
    does NOT restrict candidates to safe actions -- included only to
    measure what the unsafe-action rate WOULD be without the safety mask
    every other policy in this module applies by construction. Never used
    as a competing baseline for H3; used only for the safety-ablation
    metric in the final report."""

    policy_id = "ablation_unmasked_utility"
    policy_version = "v1"

    def __init__(self, inner: EmpiricalRecoveryPolicy):
        self.inner = inner

    def select_action(self, ctx: DecisionContext) -> ActionSelection:
        scored = []
        for action in ctx.candidate_actions:  # NOTE: no safety filter here, deliberately
            p_success, p_partial, n = self.inner._lookup(ctx, action)
            eu = _expected_utility(p_success, p_partial, action)
            scored.append((eu, n, action))
        scored.sort(key=lambda t: t[0], reverse=True)
        best_eu, best_n, best_action = scored[0]
        return ActionSelection(
            selected_action=best_action, policy_id=self.policy_id, policy_version=self.policy_version,
            confidence=min(1.0, best_n / max(1, self.inner.min_evidence)),
            rationale="max expected utility WITHOUT safety masking (ablation only)",
        )


def make_family_only_policy(min_evidence: int = 5) -> EmpiricalRecoveryPolicy:
    """Ablation D: no context (family-level stats only)."""
    return EmpiricalRecoveryPolicy(min_evidence=min_evidence, use_context=False)


def make_no_abstention_policy(min_evidence: int = 5) -> EmpiricalRecoveryPolicy:
    """Ablation C: uncertainty-aware selection with abstention disabled."""
    return EmpiricalRecoveryPolicy(min_evidence=min_evidence, allow_abstention=False)
