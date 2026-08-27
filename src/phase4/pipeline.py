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

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .agent_calibration import AgentAutonomyDecision, AgentDecisionCalibrationProfile
from .agent_recovery import AgentExecutionResult, AgentRecoveryExecutor
from .agent_runtime import AgentTaskRuntime
from .architecture import AutonomyState, WorkloadStateMachine
from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .decision import AbstentionAwareDecisionPolicy, AutonomyDecision
from .diagnosis import DiagnosisEngine, StructuredDiagnosis
from .guardrails import RecoveryCircuitBreaker
from .learning import LearningManager, LearningUpdate
from .memory import FailureMemoryStore
from .monitoring import MonitoringBaseline, MonitoringEngine
from .prediction import AgentUncertaintyPredictor, TelemetryRiskPredictor
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
    decision: AutonomyDecision | AgentAutonomyDecision | None = None
    diagnosis: StructuredDiagnosis | None = None
    action: RecoveryAction | None = None
    safety_authorized: bool | None = None
    safety_reason: str | None = None
    execution: ExecutionResult | None = None
    validation: ValidationOutcome | None = None
    learning: LearningUpdate | None = None
    notes: list[str] = field(default_factory=list)
    # Phase 4.5 gap 1: populated only when AutonomyPipeline(..., rolling_prediction=True).
    # ``rolling_predictions`` is the full (checkpoint_time, score) series computed
    # strictly before this run's own failure boundary; ``prediction_lead_time_seconds``
    # is the real wall-clock gap between the FIRST checkpoint whose score crossed the
    # active predictor's threshold and the run's real failure timestamp -- None if the
    # predictor never fired before the failure (an honest miss, not defaulted to 0).
    rolling_predictions: list[tuple[str, float]] | None = None
    prediction_lead_time_seconds: float | None = None


@dataclass
class ContinuousRunReport:
    """Phase 4.5 gap 7 -- summary of one bounded ``run_continuous`` call.
    Deliberately does not retain every ``PipelineResult`` (that could grow
    unbounded for a long-running stream); ``episode_log`` holds one compact
    dict per episode instead, which is also exactly what gets written to
    ``metrics_log_path`` as JSON Lines -- "a lightweight JSON/metrics-log
    output", not a full observability stack."""

    episodes_run: int
    stopped_reason: str  # "max_episodes" | "max_duration_seconds" | "stream_exhausted"
    wall_clock_seconds: float
    final_state_counts: dict[str, int]
    episode_log: list[dict[str, Any]] = field(default_factory=list)


class AutonomyPipeline:
    """Ties every Phase 4 / Phase 5 component into one run of the autonomy
    state machine. Owns one ``FailureMemoryStore`` for its lifetime, so
    calling ``run_workload`` repeatedly on the same pipeline instance is how
    later incidents actually get to see earlier ones -- this is what makes
    the memory-informed planner and confidence-corroborating diagnosis
    observable end to end rather than only unit-testable in isolation."""

    def __init__(
        self,
        runtime: ControlledRuntime,
        memory: FailureMemoryStore | None = None,
        baseline: MonitoringBaseline | None = None,
        planner: RuleBasedRecoveryPlanner | None = None,
        predictor: TelemetryRiskPredictor | None = None,
        recovery_budget: RecoveryCircuitBreaker | None = None,
        rolling_prediction: bool = False,
        agent_runtime: AgentTaskRuntime | None = None,
        agent_predictor: AgentUncertaintyPredictor | None = None,
        agent_decision_policy: AgentDecisionCalibrationProfile | None = None,
    ):
        self.runtime = runtime
        self.memory = memory or FailureMemoryStore()
        self.baseline = baseline or MonitoringBaseline()
        self.predictor = predictor or TelemetryRiskPredictor(self.baseline)
        self.decision_policy = AbstentionAwareDecisionPolicy()
        self.monitor = MonitoringEngine(self.baseline)
        self.diagnoser = DiagnosisEngine()
        self.planner = planner or RuleBasedRecoveryPlanner()
        self.gate = RecoverySafetyGate()
        self.executor = ControlledRuntimeRecoveryExecutor(runtime)
        self.validator = SignalRecoveryValidator()
        self.learner = LearningManager(self.memory)
        # Phase 4.5 gap 6: independent hard cap on real recovery executions
        # per (workload_id, environment_id), on top of (not instead of) the
        # planner's own action-avoidance heuristic. See
        # src/phase4/guardrails.py for why this stays open forever once
        # tripped rather than being time-windowed.
        self.recovery_budget = recovery_budget or RecoveryCircuitBreaker(max_attempts=5)
        # Phase 4.5 gap 1: opt-in so every pre-existing test (which relies on
        # the prediction being computed exactly once, at the failure
        # boundary) keeps passing unchanged. See PipelineResult's
        # rolling_predictions / prediction_lead_time_seconds fields.
        self.rolling_prediction = rolling_prediction
        # Phase 4.5b -- optional AI/ML agent output-correctness capability.
        # Opt-in via `agent_runtime=` (mirrors `rolling_prediction`'s
        # opt-in discipline) so every pre-existing test/caller that never
        # passes it is completely unaffected; `run_agent_task` raises a
        # clear error if called without one configured.
        self.agent_runtime = agent_runtime
        self.agent_predictor = agent_predictor or AgentUncertaintyPredictor()
        self.agent_executor = AgentRecoveryExecutor(agent_runtime) if agent_runtime is not None else None
        # Phase 4.7 -- optional mechanism-aware calibrated policy for the
        # agent self-consistency signal. Opt-in (mirrors rolling_prediction
        # / agent_runtime's own opt-in discipline): when None (the
        # default), run_agent_task behaves EXACTLY as it did before this
        # change, using the generic self.decision_policy -- every existing
        # test/caller is unaffected. See src/phase4/agent_calibration.py.
        self.agent_decision_policy = agent_decision_policy

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
        # Post-P5 remediation: was strict `<` against a microsecond-
        # precision timestamp string. On a fast machine, two events
        # emitted in rapid succession (e.g. the LAST self-consistency
        # sample and the failure_detected event immediately following it)
        # can legitimately share the exact same timestamp, and strict `<`
        # then silently dropped that last, most-informative event from the
        # prediction prefix -- reproduced directly as real, non-RNG,
        # non-load-dependent run-to-run nondeterminism. `<=` matches the
        # convention every other temporal-cut boundary in this codebase
        # already uses (see `prediction.py::rolling_checkpoints`'s
        # identical `<= ts`). The `event_type != "failure_detected"` guard
        # already independently excludes the failure event itself, so this
        # cannot let the failure event's own evidence leak into its own
        # prediction.
        prediction_prefix = [e for e in result.events if e.get("event_type") != "failure_detected" and (e.get("timestamp") or "") <= failure_boundary]

        rolling_series: list[tuple[str, float]] | None = None
        lead_time_seconds: float | None = None
        if self.rolling_prediction:
            # Phase 4.5 gap 1: score at every real telemetry checkpoint that
            # occurred strictly before this run's own failure, not only once
            # at the boundary. The FIRST checkpoint whose score crosses the
            # active predictor's own calibrated threshold (falling back to
            # the fixed-weight DECISION_THRESHOLD for a predictor with no
            # calibrator, e.g. TelemetryRiskPredictor) becomes the decision
            # input -- this is what makes a real, positive lead time
            # possible, instead of only ever evaluating exactly at the
            # instant of failure.
            from .prediction import DECISION_THRESHOLD, rolling_checkpoints

            threshold_value = getattr(getattr(self.predictor, "calibrator", None), "threshold", DECISION_THRESHOLD)
            rolling_series = []
            fired_prediction = None
            fired_time = None
            for checkpoint_time, prefix in rolling_checkpoints(result.events, result.collection_start):
                if checkpoint_time >= failure_boundary:
                    continue
                candidate = self.predictor.predict_from_events(
                    job_id=result.run_id, events_prefix=prefix,
                    configured_timeout_seconds=self.runtime.config.timeout_seconds,
                    run_start_iso=result.collection_start, at_time_iso=checkpoint_time,
                    workload_type=workload_type, parameters=parameters,
                )
                rolling_series.append((checkpoint_time, candidate.score))
                if fired_prediction is None and candidate.score >= threshold_value:
                    fired_prediction, fired_time = candidate, checkpoint_time
            if fired_prediction is not None:
                prediction = fired_prediction
                lead_time_seconds = (_iso_to_dt(failure_boundary) - _iso_to_dt(fired_time)).total_seconds()
            else:
                # Never fired before the failure: fall back to the
                # boundary-time prediction exactly as the non-rolling path
                # does, so the decision layer always has something to act
                # on -- but lead_time_seconds stays None (an honest miss).
                prediction = self.predictor.predict_from_events(
                    job_id=result.run_id, events_prefix=prediction_prefix,
                    configured_timeout_seconds=self.runtime.config.timeout_seconds,
                    run_start_iso=result.collection_start, at_time_iso=failure_boundary,
                    workload_type=workload_type, parameters=parameters,
                )
        else:
            prediction = self.predictor.predict_from_events(
                job_id=result.run_id, events_prefix=prediction_prefix,
                configured_timeout_seconds=self.runtime.config.timeout_seconds,
                run_start_iso=result.collection_start, at_time_iso=failure_boundary,
                workload_type=workload_type, parameters=parameters,
            )
        sm.transition(AutonomyState.PREDICTED)
        sm.transition(AutonomyState.DECIDING)
        decision = self.decision_policy.decide(prediction)

        pr = PipelineResult(run_id=result.run_id, workload_id=result.workload_id, final_state="", state_history=[], prediction_score=prediction.score, decision=decision, notes=notes, rolling_predictions=rolling_series, prediction_lead_time_seconds=lead_time_seconds)

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

        budget = self.recovery_budget.check(result.workload_id, self.runtime.config.environment_id)
        if not budget.allowed:
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append(budget.reason)
            return pr

        sm.transition(AutonomyState.EXECUTING)
        execution = self.executor.execute(action, workload_type, parameters or {}, workload_id=result.workload_id)
        pr.execution = execution
        if execution.executed:
            self.recovery_budget.record_attempt(result.workload_id, self.runtime.config.environment_id)

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

    def run_agent_task(self, seed: int, n_samples: int | None = None, workload_id: str | None = None) -> PipelineResult:
        """Phase 4.5b -- the second gap named in the project's own
        strategic review, implemented: walks the SAME autonomy state
        machine and reuses the SAME diagnosis/planning/safety/learning
        components as ``run_workload``, but against a real AI/ML agent
        answering a real task with a ground-truth oracle
        (``src/phase4/agent_task.py`` via ``agent_runtime.py``), using a
        genuine model-output uncertainty signal (self-consistency
        disagreement, ``AgentUncertaintyPredictor``) rather than OS/process
        telemetry as the prediction input. Requires the pipeline to have
        been constructed with ``agent_runtime=AgentTaskRuntime(...)``."""
        if self.agent_runtime is None or self.agent_executor is None:
            raise ValueError("AutonomyPipeline was constructed without agent_runtime; pass agent_runtime=AgentTaskRuntime(...) to use run_agent_task")

        sm = WorkloadStateMachine()
        result = self.agent_runtime.run(seed, n_samples=n_samples, workload_id=workload_id)
        effective_n_samples = n_samples if n_samples is not None else self.agent_runtime.config.n_samples
        notes = [f"agent-task-runtime status={result.status}"]

        sm.transition(AutonomyState.OBSERVING)
        self.monitor.process(result.events)
        engine_failures = [f for f in self.monitor.failures if f["run_id"] == result.run_id]

        if not engine_failures:
            sm.transition(AutonomyState.UNKNOWN); sm.transition(AutonomyState.COMPLETED)
            return PipelineResult(
                run_id=result.run_id, workload_id=result.workload_id, final_state=sm.state.value,
                state_history=[s.value for s in sm.history],
                notes=notes + ["agent answered correctly (majority vote matched ground truth); prediction/decision/recovery loop not entered"],
            )

        failure_boundary = str(engine_failures[0]["failure_timestamp"])
        # Post-P5 remediation: was strict `<` against a microsecond-
        # precision timestamp string. On a fast machine, two events
        # emitted in rapid succession (e.g. the LAST self-consistency
        # sample and the failure_detected event immediately following it)
        # can legitimately share the exact same timestamp, and strict `<`
        # then silently dropped that last, most-informative event from the
        # prediction prefix -- reproduced directly as real, non-RNG,
        # non-load-dependent run-to-run nondeterminism. `<=` matches the
        # convention every other temporal-cut boundary in this codebase
        # already uses (see `prediction.py::rolling_checkpoints`'s
        # identical `<= ts`). The `event_type != "failure_detected"` guard
        # already independently excludes the failure event itself, so this
        # cannot let the failure event's own evidence leak into its own
        # prediction.
        prediction_prefix = [e for e in result.events if e.get("event_type") != "failure_detected" and (e.get("timestamp") or "") <= failure_boundary]

        prediction = self.agent_predictor.predict_from_events(
            job_id=result.run_id, events_prefix=prediction_prefix,
            configured_timeout_seconds=None, run_start_iso=result.collection_start, at_time_iso=failure_boundary,
        )
        sm.transition(AutonomyState.PREDICTED)
        sm.transition(AutonomyState.DECIDING)
        if self.agent_decision_policy is not None:
            # Phase 4.7 -- mechanism-aware calibrated policy. Its decision
            # is one of ANSWER/RETRY/ABSTAIN/REVIEW; ANSWER and RETRY both
            # permit the diagnosis/planning/safety/execution path below
            # (the planner is what actually picks RETRY as the concrete
            # action for an AGENT_INCORRECT_ANSWER diagnosis either way --
            # see RuleBasedRecoveryPlanner's candidate table -- so this
            # profile's ANSWER/RETRY distinction is about which confidence
            # tier justified autonomous action, not a second action-picker).
            decision = self.agent_decision_policy.decide(prediction, effective_n_samples)
        else:
            decision = self.decision_policy.decide(prediction)

        pr = PipelineResult(run_id=result.run_id, workload_id=result.workload_id, final_state="", state_history=[], prediction_score=prediction.score, decision=decision, notes=notes)

        if decision.decision == "ABSTAIN":
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append("decision layer abstained on the agent's self-consistency-derived risk signal; no diagnosis attempted")
            return pr

        entry_state = AutonomyState.DIAGNOSING if decision.decision in ("ANSWER", "RETRY") else AutonomyState.ESCALATED
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
        if not authorized or decision.decision not in ("ANSWER", "RETRY"):
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append("safety gate rejected the action, or decision was REVIEW/ABSTAIN; no execution")
            return pr

        budget = self.recovery_budget.check(result.workload_id, self.agent_runtime.config.environment_id)
        if not budget.allowed:
            sm.transition(AutonomyState.ABSTAINED); sm.transition(AutonomyState.COMPLETED)
            pr.final_state = sm.state.value; pr.state_history = [s.value for s in sm.history]
            pr.notes.append(budget.reason)
            return pr

        sm.transition(AutonomyState.EXECUTING)
        execution = self.agent_executor.execute(action, seed, effective_n_samples, workload_id=result.workload_id)
        pr.execution = execution
        if execution.executed:
            self.recovery_budget.record_attempt(result.workload_id, self.agent_runtime.config.environment_id)

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

    def run_continuous(
        self,
        workload_stream: Iterable[Mapping[str, Any]],
        *,
        max_episodes: int | None = None,
        max_duration_seconds: float | None = None,
        metrics_log_path: str | Path | None = None,
    ) -> ContinuousRunReport:
        """Phase 4.5 gap 7 -- a real bounded loop over a stream of workload
        specs, not a single one-shot call. ``workload_stream`` yields dicts
        with at least ``{"workload_type": ..., "parameters": {...}}`` and
        optionally ``"workload_id"``; it may be infinite (e.g.
        ``itertools.cycle`` over a fixed set of scenarios) -- this method is
        exactly what makes that safe to pass in, by stopping cleanly once
        ``max_episodes`` episodes have run or ``max_duration_seconds`` wall-
        clock seconds have elapsed, whichever comes first. At least one of
        the two must be set, or an infinite stream really would run
        forever."""
        if max_episodes is None and max_duration_seconds is None:
            raise ValueError("run_continuous requires at least one of max_episodes or max_duration_seconds")
        start = time.monotonic()
        episodes_run = 0
        final_state_counts: dict[str, int] = {}
        episode_log: list[dict[str, Any]] = []
        stopped_reason = "stream_exhausted"
        for item in workload_stream:
            if max_episodes is not None and episodes_run >= max_episodes:
                stopped_reason = "max_episodes"
                break
            if max_duration_seconds is not None and (time.monotonic() - start) >= max_duration_seconds:
                stopped_reason = "max_duration_seconds"
                break
            workload_type = str(item.get("workload_type") or item.get("mode"))
            parameters = dict(item.get("parameters") or {})
            workload_id = item.get("workload_id")
            result = self.run_workload(workload_type, parameters, workload_id=workload_id)
            episodes_run += 1
            final_state_counts[result.final_state] = final_state_counts.get(result.final_state, 0) + 1
            episode_log.append({
                "episode": episodes_run, "run_id": result.run_id, "workload_id": result.workload_id,
                "workload_type": workload_type, "final_state": result.final_state,
                "diagnosis_hypothesis": result.diagnosis.primary_hypothesis.name if result.diagnosis else None,
                "action": result.action.action_type if result.action else None,
                "validation": result.validation.status if result.validation else None,
                "elapsed_seconds": time.monotonic() - start,
            })
        else:
            stopped_reason = "stream_exhausted"
        # Re-check the bounds one more time in case the loop exited via
        # natural exhaustion right at (not past) a bound -- keeps the
        # reported reason accurate rather than always "stream_exhausted".
        if stopped_reason == "stream_exhausted":
            if max_episodes is not None and episodes_run >= max_episodes:
                stopped_reason = "max_episodes"
            elif max_duration_seconds is not None and (time.monotonic() - start) >= max_duration_seconds:
                stopped_reason = "max_duration_seconds"
        wall_clock_seconds = time.monotonic() - start
        if metrics_log_path is not None:
            path = Path(metrics_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w") as handle:
                for row in episode_log:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.write(json.dumps({
                    "summary": True, "episodes_run": episodes_run, "stopped_reason": stopped_reason,
                    "wall_clock_seconds": wall_clock_seconds, "final_state_counts": final_state_counts,
                }, sort_keys=True) + "\n")
        return ContinuousRunReport(
            episodes_run=episodes_run, stopped_reason=stopped_reason, wall_clock_seconds=wall_clock_seconds,
            final_state_counts=final_state_counts, episode_log=episode_log,
        )


def _failure_class_of(diagnosis: StructuredDiagnosis) -> str:
    return _failure_class_from_diagnosis(diagnosis)


def _iso_to_dt(value: str):
    from datetime import datetime

    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
