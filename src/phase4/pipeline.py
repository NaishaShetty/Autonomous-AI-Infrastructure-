"""Phase 4.4 / Phase 5 -- the end-to-end autonomy pipeline.

This is the piece that did not exist anywhere in the repository before this
change: a single orchestrator that actually drives ``AutonomyState`` (defined
in ``src/phase4/architecture.py`` since the Phase 4 restart, but never
implemented) from ``RECEIVED`` through observation, prediction, abstention-
aware decision, diagnosis (with scoped historical memory), planning, the
safety gate, real (not simulated) recovery execution for retry/restart, and
independent validation, then learns from the outcome.

State transitions below are exactly the ones ``ALLOWED`` in
``src/phase4/architecture.py`` -- this module does not add new transitions,
it is the first caller that actually walks the existing state machine
end to end. ``docs/PHASE4_5_AUDIT_AND_PLAN.md`` sections 5-6 describe the
target; this is the implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .architecture import AutonomyState, WorkloadStateMachine
from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .decision import AbstentionAwareDecisionPolicy, AutonomyDecision
from .diagnosis import DiagnosisEngine, StructuredDiagnosis
from .learning import LearningManager, LearningUpdate
from .memory import FailureMemoryStore
from .monitoring import MonitoringBaseline, MonitoringEngine
from .prediction import TelemetryRiskPredictor
from .recovery import (
    ControlledRuntimeRecoveryExecutor,
    ExecutionResult,
    RecoverySafetyGate,
    RuleBasedRecoveryPlanner,
    SignalRecoveryValidator,
    _failure_class_from_diagnosis,
)
from .architecture import RecoveryAction, ValidationOutcome

PIPELINE_VERSION = "phase4.4-pipeline-v1"


@dataclass
class PipelineResult:
    run_id: str
    workload_id: str
    final_state: str
    state_history: list[str]
    prediction_score: float | None = None
    decision: AutonomyDecision | None = None
    diagnosis: StructuredDiagnosis | None = None
    action: RecoveryAction | None = None
    safety_authorized: bool | None = None
    safety_reason: str | None = None
    execution: ExecutionResult | None = None
    validation: ValidationOutcome | None = None
    learning: LearningUpdate | None = None
    notes: list[str] = field(default_factory=list)


class AutonomyPipeline:
    """Ties every Phase 4 / Phase 5 component into one run of the autonomy
    state machine. Owns one ``FailureMemoryStore`` for its lifetime, so
    calling ``run_workload`` repeatedly on the same pipeline instance is how
    later incidents actually get to see earlier ones -- this is what makes
    the memory-informed planner and confidence-corroborating diagnosis
    observable end to end rather than only unit-testable in isolation."""

    def __init__(self, runtime: ControlledRuntime, memory: FailureMemoryStore | None = None, baseline: MonitoringBaseline | None = None):
        self.runtime = runtime
        self.memory = memory or FailureMemoryStore()
        self.baseline = baseline or MonitoringBaseline()
        self.predictor = TelemetryRiskPredictor(self.baseline)
        self.decision_policy = AbstentionAwareDecisionPolicy()
        self.monitor = MonitoringEngine(self.baseline)
        self.diagnoser = DiagnosisEngine()
        self.planner = RuleBasedRecoveryPlanner()
        self.gate = RecoverySafetyGate()
        self.executor = ControlledRuntimeRecoveryExecutor(runtime)
        self.validator = SignalRecoveryValidator()
        self.learner = LearningManager(self.memory)

    def run_workload(self, workload_type: str, parameters: Mapping[str, Any] | None = None, workload_id: str | None = None) -> PipelineResult:
        sm = WorkloadStateMachine()
        result = self.runtime.run(workload_type, dict(parameters or {}), workload_id=workload_id)
        notes = [f"controlled-runtime status={result.status}"]

        sm.transition(AutonomyState.OBSERVING)

        # Detection is retrospective and legitimately sees the whole run --
        # that is its job. Prediction must not: it is only meaningful if it
        # only ever sees events strictly BEFORE the failure it is trying to
        # anticipate, so it is computed on a boundary-cut prefix, never on
        # the complete post-hoc event list. See src/phase4/prediction.py and
        # tests/unit/test_phase44_prediction.py for the leakage guard this
        # mirrors (the same discipline as the diagnosis current-run-only fix).
        self.monitor.process(result.events)
        engine_failures = [f for f in self.monitor.failures if f["run_id"] == result.run_id]

        if not engine_failures:
            # Nothing failed. There is nothing for the decision layer to
            # gate and nothing to diagnose -- OBSERVING->UNKNOWN->COMPLETED
            # is the only allowed path back to a terminal state without
            # invoking PREDICTED/DECIDING, which this state machine reserves
            # for "something happened that needs a trust decision."
            sm.transition(AutonomyState.UNKNOWN); sm.transition(AutonomyState.COMPLETED)
            pr = PipelineResult(run_id=result.run_id, workload_id=result.workload_id, final_state=sm.state.value, state_history=[s.value for s in sm.history], notes=notes + ["no confirmed failure on this run; prediction/decision/recovery loop not entered"])
            return pr

        failure_boundary = str(engine_failures[0]["failure_timestamp"])
        prediction_prefix = [e for e in result.events if e.get("event_type") != "failure_detected" and (e.get("timestamp") or "") < failure_boundary]
        prediction = self.predictor.predict_from_events(
            job_id=result.run_id, events_prefix=prediction_prefix,
            configured_timeout_seconds=self.runtime.config.timeout_seconds,
            run_start_iso=result.collection_start, at_time_iso=failure_boundary,
        )
        sm.transition(AutonomyState.PREDICTED)
        sm.transition(AutonomyState.DECIDING)
        decision = self.decision_policy.decide(prediction)

        pr = PipelineResult(run_id=result.run_id, workload_id=result.workload_id, final_state="", state_history=[], prediction_score=prediction.score, decision=decision, notes=notes)

        if decision.decision == "ABSTAIN":
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append("decision layer abstained on the pre-failure risk signal; no diagnosis attempted, per DECIDING->ABSTAINED being a direct allowed transition")
            return pr

        entry_state = AutonomyState.DIAGNOSING if decision.decision == "ANSWER" else AutonomyState.ESCALATED
        sm.transition(entry_state)
        if entry_state == AutonomyState.ESCALATED:
            sm.transition(AutonomyState.DIAGNOSING)

        diagnosis = self.diagnoser.diagnose(engine_failures[0], result.events, memory=self.memory)
        pr.diagnosis = diagnosis

        if diagnosis.primary_hypothesis.name == "UNKNOWN":
            sm.transition(AutonomyState.ESCALATED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append("diagnosis produced no hypothesis; escalating rather than planning against nothing")
            return pr

        sm.transition(AutonomyState.PLANNING)
        action = self.planner.plan(diagnosis, memory=self.memory)
        pr.action = action

        sm.transition(AutonomyState.SAFETY_CHECK)
        authorized, reason = self.gate.authorize(action, diagnosis)
        pr.safety_authorized, pr.safety_reason = authorized, reason
        # A REVIEW-band decision never reaches autonomous execution, even if
        # the safety gate would have authorized the action on its own merits
        # -- SAFETY_CHECK->ABSTAINED is an allowed transition precisely for
        # this case.
        if not authorized or decision.decision == "REVIEW":
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append("safety gate rejected the action, or decision was REVIEW; no execution")
            return pr

        sm.transition(AutonomyState.EXECUTING)
        execution = self.executor.execute(action, workload_type, parameters or {})
        pr.execution = execution

        sm.transition(AutonomyState.VALIDATING)
        validation = self.validator.validate(execution)
        pr.validation = validation

        failure_class = _failure_class_of(diagnosis)
        learning = self.learner.record(diagnosis, action, validation, failure_class, recorded_at=result.collection_end)
        pr.learning = learning

        if validation.status == "RECOVERED":
            sm.transition(AutonomyState.RECOVERED)
        elif validation.status == "NOT_RECOVERED":
            sm.transition(AutonomyState.NOT_RECOVERED)
        else:
            sm.transition(AutonomyState.UNKNOWN)
        sm.transition(AutonomyState.COMPLETED)

        pr.final_state = sm.state.value
        pr.state_history = [s.value for s in sm.history]
        return pr


def _failure_class_of(diagnosis: StructuredDiagnosis) -> str:
    return _failure_class_from_diagnosis(diagnosis)
