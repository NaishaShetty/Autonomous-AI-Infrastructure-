"""Phase 4.4 / Phase 5 -- concrete Planner / SafetyGate / Executor / Validator.

Per Decision A of ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` ("adapt, don't
rebuild"), this module reuses the existing, frozen, tested Gen 2 safety
vocabulary (``src.recovery.actions``, ``src.recovery.schema.ActionId``)
rather than inventing a second one. What is new here is the adapter that
connects that vocabulary to the Gen 3 controlled-runtime contracts defined
in ``src/phase4/architecture.py`` (``PlannerPort``, ``SafetyGatePort``,
``ExecutorPort``, ``ValidatorPort``) -- none of which had an implementation
before this change.

Execution is real, not simulated, for RETRY and RESTART: both re-invoke
``ControlledRuntime.run`` against the same controlled, project-owned
subprocess boundary the rest of Phase 4 already uses for observation. This
stays inside the project's existing safety envelope (a local subprocess this
runtime already owns and can kill) rather than claiming any production
executor, which ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` section 5.A explicitly
says must not be added without a separate safety review. ROLLBACK,
RECONFIGURE, and FORCE_RESTART are declared but have no executor
implementation -- there is no persistent deployment/configuration target in
this repository to roll back or reconfigure, and inventing one to look
complete would be exactly the kind of fabricated capability this project's
own audits have repeatedly flagged and corrected. The planner never selects
them.

Validation is independent of the executor by construction: ``SignalRecoveryValidator``
re-runs ``MonitoringEngine`` over the *new* run's own raw events and derives
recovery success from that, never from a status string the executor
reports. A deliberately-lying executor is exercised in
``tests/unit/test_phase44_recovery.py`` to prove this.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.recovery.actions import ACTIONS, is_unsafe
from src.recovery.schema import ActionId

from .architecture import RecoveryAction, ValidationOutcome
from .controlled_runtime import ControlledRuntime
from .monitoring import MonitoringEngine
from src.data_foundation.foundation import Provenance, TimestampQuality

RECOVERY_ADAPTER_VERSION = "phase4.4-recovery-adapter-v1"

# Ordered candidate actions per failure class, most-preferred first. Frozen
# alongside this module -- do not reorder based on which action "won" in an
# evaluation run (research-integrity precedent: src/recovery/taxonomy.py's
# own header comment makes the same commitment for its action vocabulary).
_CANDIDATES: dict[str, tuple[ActionId, ...]] = {
    "PROCESS_TIMEOUT": (ActionId.RETRY, ActionId.RESTART, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
    "PROCESS_NONZERO_EXIT": (ActionId.RESTART, ActionId.RETRY, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
    "NETWORK_FAILURE": (ActionId.RETRY, ActionId.ESCALATE_TO_HUMAN, ActionId.ABSTAIN),
}
_EXECUTABLE = {ActionId.RETRY, ActionId.RESTART}


def _provenance(source: str) -> Provenance:
    return Provenance(source=source, source_version=RECOVERY_ADAPTER_VERSION, timestamp_quality=TimestampQuality.EXACT)


class RuleBasedRecoveryPlanner:
    """Concrete ``PlannerPort`` implementation. Memory-informed: an action
    already seen to fail repeatedly for this exact (workload, environment,
    failure_class) is skipped in favor of the next candidate, per the
    ``FailureMemoryStore.prior_outcome_rate`` contract."""

    version = "phase4.4-planner-v1"

    def plan(self, diagnosis, memory=None, min_failures_before_avoidance: int = 2) -> RecoveryAction:
        failure_class = _failure_class_from_diagnosis(diagnosis)
        candidates = _CANDIDATES.get(failure_class, (ActionId.ABSTAIN,))
        chosen = ActionId.ABSTAIN
        rationale = "no safe, memory-clean candidate action was available; abstaining"
        for candidate in candidates:
            if is_unsafe(candidate):
                continue  # defense in depth; none of _CANDIDATES should ever include an unsafe action
            if candidate == ActionId.ESCALATE_TO_HUMAN or candidate == ActionId.ABSTAIN:
                chosen, rationale = candidate, f"no executable action for {failure_class} cleared memory-avoidance; falling back to {candidate.value}"
                break
            if memory is not None:
                successes, total = memory.prior_outcome_rate(
                    workload_id=diagnosis.workload_id,
                    environment_id=diagnosis.environment_id,
                    failure_class=failure_class,
                    action=candidate.value,
                    exclude_run_id=diagnosis.run_id,
                    at_or_before=diagnosis.diagnosis_boundary,
                )
                if total >= min_failures_before_avoidance and successes == 0:
                    continue  # this action has a clean track record of NOT working here; try the next one
            chosen, rationale = candidate, f"selected {candidate.value} for {failure_class} (memory-informed)" if memory is not None else f"selected {candidate.value} for {failure_class} (no memory available)"
            break
        spec = ACTIONS[chosen]
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
            provenance=_provenance("phase4-recovery-planner"),
        )


def _failure_class_from_diagnosis(diagnosis) -> str:
    # StructuredDiagnosis does not carry failure_class directly; it is
    # recoverable from foundation_references or the primary hypothesis name.
    name = diagnosis.primary_hypothesis.name
    if name == "RUNTIME_TIMEOUT":
        return "PROCESS_TIMEOUT"
    if name == "PROCESS_EXIT_FAILURE":
        return "PROCESS_NONZERO_EXIT"
    if name == "NETWORK_CONNECTIVITY_FAILURE":
        return "NETWORK_FAILURE"
    return "UNKNOWN"


class RecoverySafetyGate:
    """Concrete ``SafetyGatePort`` implementation. Fail-closed: authorizes
    only actions that are (a) not classified UNSAFE in the frozen Gen 2
    vocabulary and (b) a declared candidate for the diagnosis's failure
    class. Anything else -- including a planner bug that somehow proposes an
    action outside its own candidate list -- is rejected, never executed."""

    version = "phase4.4-safety-gate-v1"

    def authorize(self, action: RecoveryAction, diagnosis) -> tuple[bool, str]:
        try:
            action_id = ActionId(action.action_type)
        except ValueError:
            return False, f"unknown action_type {action.action_type!r}; rejecting fail-closed"
        if is_unsafe(action_id):
            return False, f"{action_id.value} is classified UNSAFE in src.recovery.actions; rejecting"
        failure_class = _failure_class_from_diagnosis(diagnosis)
        allowed = _CANDIDATES.get(failure_class, ())
        if action_id not in allowed:
            return False, f"{action_id.value} is not a declared candidate for {failure_class}; rejecting"
        return True, f"{action_id.value} is SAFE and a declared candidate for {failure_class}; authorized"


@dataclass(frozen=True)
class ExecutionResult:
    action_type: str
    executed: bool
    run_result: Any | None  # RunResult from a re-invoked ControlledRuntime, or None if not executed
    note: str


class ControlledRuntimeRecoveryExecutor:
    """Concrete ``ExecutorPort`` implementation. RETRY and RESTART are
    executed for real, by re-invoking ``ControlledRuntime.run`` with the
    original workload's parameters (see module docstring for the safety
    scoping of this decision). All other authorized action types are
    recorded as not-executed rather than faked."""

    version = "phase4.4-executor-v1"

    def __init__(self, runtime: ControlledRuntime):
        self.runtime = runtime

    def execute(self, action: RecoveryAction, original_workload_type: str, original_parameters: Mapping[str, Any]) -> ExecutionResult:
        action_id = ActionId(action.action_type)
        if action_id not in _EXECUTABLE:
            return ExecutionResult(action_type=action_id.value, executed=False, run_result=None, note=f"{action_id.value} has no executor in this repository; recorded as not-executed rather than simulated")
        result = self.runtime.run(original_workload_type, dict(original_parameters))
        return ExecutionResult(action_type=action_id.value, executed=True, run_result=result, note=f"re-invoked ControlledRuntime.run for {action_id.value}")


class SignalRecoveryValidator:
    """Concrete ``ValidatorPort`` implementation. Independent of the
    executor: derives the outcome by re-running ``MonitoringEngine`` over
    the new run's own raw events, never from ``execution.note`` or any
    self-reported status. See ``tests/unit/test_phase44_recovery.py::test_validator_catches_a_lying_executor``."""

    version = "phase4.4-validator-v1"

    def validate(self, execution: ExecutionResult) -> ValidationOutcome:
        if not execution.executed or execution.run_result is None:
            return ValidationOutcome(status="NOT_EXECUTED", evidence=(), provenance=_provenance("phase4-recovery-validator"))
        events = list(execution.run_result.events)
        engine = MonitoringEngine()
        engine.process(events)
        if engine.failures:
            return ValidationOutcome(status="NOT_RECOVERED", evidence=tuple({"failure": f} for f in engine.failures), provenance=_provenance("phase4-recovery-validator"))
        completed = any(e.get("event_type") == "workload_completed" for e in events)
        if completed:
            return ValidationOutcome(status="RECOVERED", evidence=({"run_status": execution.run_result.status},), provenance=_provenance("phase4-recovery-validator"))
        return ValidationOutcome(status="UNKNOWN", evidence=({"run_status": execution.run_result.status},), provenance=_provenance("phase4-recovery-validator"))
