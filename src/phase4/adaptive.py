"""Phase 4.5 gap 5 -- a real adaptive mechanism, not just outcome logging.

``src/phase4/learning.py``'s ``LearningManager`` already writes every closed
episode's outcome to ``FailureMemoryStore``. Before this module, the only
thing that ever *read* those outcomes back to change behavior was
``RuleBasedRecoveryPlanner``'s binary avoidance rule (skip an action once it
has accumulated >= N confirmed failures with zero successes) -- a threshold,
not a model, and it never distinguishes "this action recovers 10% of the
time" from "this action recovers 49% of the time"; both look identical to
that rule until the harder one crosses the same fixed failure count.

``AdaptiveRecoveryPlanner`` is a real online mechanism: for every candidate
action that survives the (unchanged) avoidance filter, it ranks candidates by
``FailureMemoryStore.action_success_estimate`` -- a Beta(1, 1)-smoothed
success-rate estimate that is recomputed from the current durable record set
on every call, so it updates immediately as new validated outcomes are
recorded. This is deliberately implemented as a SEPARATE planner class
rather than a change to ``RuleBasedRecoveryPlanner`` itself: every existing
test in ``tests/unit/test_phase44_recovery.py`` and
``tests/integration/test_phase44_pipeline.py`` exercises the declared-order
fallback behavior of ``RuleBasedRecoveryPlanner`` and must keep passing
unchanged (see docs/PHASE4_5_AUDIT_AND_PLAN.md's own "adapt, don't rebuild"
discipline, applied here to avoid breaking a working, tested component while
adding new capability next to it). ``AutonomyPipeline`` accepts
``AdaptiveRecoveryPlanner`` via its existing ``planner=`` constructor
argument -- it is not the default, but it is the same production code path,
not a demo-only shim.
"""
from __future__ import annotations

from .recovery import RuleBasedRecoveryPlanner, _CANDIDATES, _EXECUTABLE, _failure_class_from_diagnosis, ACTIONS
from src.recovery.actions import is_unsafe
from src.recovery.schema import ActionId
from .architecture import RecoveryAction
from .recovery import _provenance


class AdaptiveRecoveryPlanner(RuleBasedRecoveryPlanner):
    """Ranks the candidate actions that survive the avoidance filter by a
    real, online-updated success-rate estimate instead of always taking the
    first declared-order survivor. With zero evidence for every candidate
    (the common case early on), every estimate is the same neutral 0.5 and
    ties are broken by declared order -- so this behaves identically to
    ``RuleBasedRecoveryPlanner`` until there is actually evidence to act on,
    which is what makes it safe to introduce without re-deriving every
    existing planner test."""

    version = "phase4.5-adaptive-planner-v1"

    def plan(self, diagnosis, memory=None, min_failures_before_avoidance: int = 2) -> RecoveryAction:
        if memory is None:
            # No memory at all: there is nothing to adapt on, so fall back
            # to the exact base-class behavior (first safe declared
            # candidate) rather than inventing a ranking from nothing.
            return super().plan(diagnosis, memory=memory, min_failures_before_avoidance=min_failures_before_avoidance)

        failure_class = _failure_class_from_diagnosis(diagnosis)
        candidates = _CANDIDATES.get(failure_class, (ActionId.ABSTAIN,))
        survivors: list[ActionId] = []
        for candidate in candidates:
            if is_unsafe(candidate):
                continue
            if candidate in (ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN):
                break  # only rank genuinely executable actions; escalate/abstain stay last-resort
            successes, total = memory.prior_outcome_rate(
                workload_id=diagnosis.workload_id, environment_id=diagnosis.environment_id,
                failure_class=failure_class, action=candidate.value,
                exclude_run_id=diagnosis.run_id, at_or_before=diagnosis.diagnosis_boundary,
            )
            if total >= min_failures_before_avoidance and successes == 0:
                continue  # same avoidance rule as the base class
            survivors.append(candidate)

        if not survivors:
            # Nothing executable survived; delegate to the base class so the
            # exact same escalate/abstain fallback logic and rationale text
            # is produced in exactly one place.
            return super().plan(diagnosis, memory=memory, min_failures_before_avoidance=min_failures_before_avoidance)

        scored = [
            (
                candidate,
                memory.action_success_estimate(
                    workload_id=diagnosis.workload_id, environment_id=diagnosis.environment_id,
                    failure_class=failure_class, action=candidate.value,
                    exclude_run_id=diagnosis.run_id, at_or_before=diagnosis.diagnosis_boundary,
                ),
            )
            for candidate in survivors
        ]
        best_estimate = max(estimate for _, estimate in scored)
        # Ties (including the common "no evidence yet, everyone at 0.5"
        # case) resolve to the first declared-order survivor with that
        # score, matching the base planner's default behavior exactly.
        chosen = next(candidate for candidate, estimate in scored if estimate == best_estimate)
        spec = ACTIONS[chosen]
        rationale = (
            f"selected {chosen.value} for {failure_class} via adaptive online success-rate ranking "
            f"(estimate={best_estimate:.4f} over {len(scored)} surviving candidate(s): "
            + ", ".join(f"{c.value}={e:.4f}" for c, e in scored) + ")"
        )
        return RecoveryAction(
            action_id=f"recovery-action:{diagnosis.diagnosis_id}:{chosen.value}",
            action_type=chosen.value,
            preconditions=(f"diagnosis={diagnosis.diagnosis_id}",),
            expected_effect=rationale,
            risk=spec.safety_classification.value.upper(),
            cost=str(spec.base_cost),
            reversible=spec.reversibility in ("reversible", "partially_reversible"),
            authorization_required=True,
            validation_requirements=("independent_post_execution_event_check",),
            provenance=_provenance("phase4-adaptive-recovery-planner"),
        )
