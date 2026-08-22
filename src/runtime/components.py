"""Small deterministic implementations of the canonical runtime contracts."""
from __future__ import annotations

from datetime import datetime, timezone
from math import fsum, isclose
import random
from typing import Any, Mapping, Sequence

import numpy as np

from src.decision.policy import DecisionMode, DecisionPolicy
from src.failure_memory.memory import FailureMemory
from src.reliability.calibrator import ConfidenceCalibrator
from src.reliability.workload_model import WorkloadModel

from .contracts import (
    DiagnosisResult,
    DetectionResult,
    ExecutionResult,
    Observation,
    RecoveryAction,
    RecoveryPlan,
    ReliabilityAssessment,
    ValidationResult,
)


class ObservationFailureDetector:
    """Detect failures from explicit observed error/resource signals only."""

    def __init__(self, error_rate_threshold: float = 0.5, resource_threshold: float = 0.95, latency_seconds_threshold: float | None = None, throughput_floor: float | None = None, detector_version: str = "observation-detector-v2"):
        self.error_rate_threshold = error_rate_threshold
        self.resource_threshold = resource_threshold
        self.latency_seconds_threshold = latency_seconds_threshold
        self.throughput_floor = throughput_floor
        self.detector_version = detector_version

    def detect(self, observation: Observation) -> DetectionResult:
        evidence: list[str] = []
        failure_type: str | None = None
        if observation.error:
            evidence.append("observation.error")
            failure_type = "execution_error"
        error_rate = observation.metrics.get("error_rate")
        if error_rate is not None and error_rate >= self.error_rate_threshold:
            evidence.append("metrics.error_rate")
            failure_type = failure_type or "error_rate_failure"
        if self.latency_seconds_threshold is not None and observation.latency_seconds is not None and observation.latency_seconds >= self.latency_seconds_threshold:
            evidence.append("observation.latency_seconds")
            failure_type = failure_type or "latency_failure"
        if self.throughput_floor is not None and observation.throughput_per_second is not None and observation.throughput_per_second <= self.throughput_floor:
            evidence.append("observation.throughput_per_second")
            failure_type = failure_type or "throughput_failure"
        for name, value in observation.resource_signals.items():
            if value >= self.resource_threshold:
                evidence.append(f"resource_signals.{name}")
                failure_type = failure_type or "resource_exhaustion"
        for name, value in observation.failure_indicators.items():
            if value >= 1.0:
                evidence.append(f"failure_indicators.{name}")
                failure_type = failure_type or "declared_failure_indicator"
        return DetectionResult(
            detected=bool(evidence),
            failure_type=failure_type,
            severity="high" if len(evidence) > 1 else ("medium" if evidence else None),
            evidence=tuple(evidence),
            uncertainty=0.0 if evidence else 1.0,
            detection_type="declared_thresholds_and_errors",
            detector_version=self.detector_version,
            provenance={"observation_id": observation.observation_id, "source_type": observation.source_type.value},
        )


class ModelReliabilityAssessor:
    """Adapter around the existing workload model, calibrator, memory, and policy."""

    def __init__(self, workload_model: WorkloadModel, calibrator: ConfidenceCalibrator, failure_memory: FailureMemory, policy: DecisionPolicy, feature_names: list[str], mode: DecisionMode = DecisionMode.COMBINED, *, model_id: str = "injected-workload-model", model_version: str = "unknown", calibrator_version: str = "unknown", training_data_id: str = "unknown", configuration: Mapping[str, Any] | None = None, artifact_hash: str | None = None):
        self.workload_model = workload_model
        self.calibrator = calibrator
        self.failure_memory = failure_memory
        self.policy = policy
        self.feature_names = feature_names
        self.mode = mode
        self.model_id = model_id
        self.model_version = model_version
        self.calibrator_version = calibrator_version
        self.training_data_id = training_data_id
        self.configuration = dict(configuration or {})
        self.artifact_hash = artifact_hash

    def assess(self, observation: Observation, retrieved: Sequence[Any] = ()) -> ReliabilityAssessment:
        context = dict(observation.features)
        x = np.array([context.get(name, 0.0) for name in self.feature_names], dtype=float)
        prediction = self.workload_model.predict(x)
        calibration = self.calibrator.predict({
            **context,
            "predicted_label": prediction.predicted_label,
            "predicted_proba": prediction.predicted_proba,
            "margin": prediction.margin,
            "entropy": prediction.entropy,
        })
        risk = None
        if self.mode in (DecisionMode.RISK_ONLY, DecisionMode.COMBINED):
            risk = self.failure_memory.risk(context, calibration.calibrated_confidence)
        decision, score = self.policy.decide(calibration.calibrated_confidence, risk, self.mode)
        return ReliabilityAssessment(
            confidence=calibration.calibrated_confidence,
            risk=risk,
            decision=decision.value,
            fused_score=score,
            uncertainty=float(np.clip(1.0 - calibration.calibrated_confidence, 0.0, 1.0)),
            predicted_label=prediction.predicted_label,
            model_id=self.model_id,
            model_version=self.model_version,
            calibrator_version=self.calibrator_version,
            training_data_id=self.training_data_id,
            configuration=self.configuration,
            artifact_hash=self.artifact_hash,
            provenance={
                "observation_id": observation.observation_id,
                "source_type": observation.source_type.value,
                "model_id": self.model_id,
                "artifact_loaded": self.artifact_hash is not None,
            },
        )


class EvidenceDiagnosisEngine:
    """Correlation-aware diagnosis based only on observed and retrieved evidence."""

    def diagnose(self, observation: Observation, detection: DetectionResult, reliability: ReliabilityAssessment, retrieved: Sequence[Any] = ()) -> DiagnosisResult:
        if not detection.detected:
            return DiagnosisResult(None, confidence=0.0, uncertainty=1.0, evidence=("no_failure_detected",))
        relevant: list[Any] = []
        evidence: list[str] = list(detection.evidence)
        for item in retrieved:
            match = item
            event = getattr(match, "event", match[0] if isinstance(match, tuple) else match)
            is_relevant = bool(getattr(match, "relevant", False))
            if is_relevant:
                relevant.append(match)
                event_id = getattr(event, "event_id", "unknown")
                similarity = getattr(match, "similarity", None)
                evidence.append(f"historical_experience:{event_id}:similarity={similarity:.3f}" if similarity is not None else f"historical_experience:{event_id}")
        ids = tuple(str(getattr(getattr(match, "event", match[0] if isinstance(match, tuple) else match), "event_id", "unknown")) for match in relevant)
        confidence = min(1.0, 0.5 + 0.1 * len(detection.evidence) + (0.2 if relevant else 0.0))
        return DiagnosisResult(
            failure_type=detection.failure_type,
            likely_causes=tuple(detection.evidence) + (("historical_failure_pattern",) if relevant else ()),
            confidence=confidence,
            uncertainty=1.0 - confidence,
            supporting_experience_ids=ids,
            evidence=tuple(evidence),
        )


class RuleBasedRecoveryPlanner:
    """Interpretable planner with evidence-aware ranking and hard safety gates."""

    def __init__(self, minimum_confidence: float = 0.6, require_evidence: bool = False, default_action: RecoveryAction = RecoveryAction.RETRY, abstain_on_conflict: bool = True):
        self.minimum_confidence = minimum_confidence
        self.require_evidence = require_evidence
        self.default_action = RecoveryAction(default_action)
        self.abstain_on_conflict = abstain_on_conflict

    def plan(self, diagnosis: DiagnosisResult, reliability: ReliabilityAssessment, retrieved: Sequence[Any] = (), operational_context: Mapping[str, Any] | None = None) -> RecoveryPlan:
        context = operational_context or {}
        relevant = [item for item in retrieved if bool(getattr(item, "relevant", False))]
        if diagnosis.confidence < self.minimum_confidence or diagnosis.uncertainty > 0.5:
            return RecoveryPlan((RecoveryAction.ABSTAIN,), RecoveryAction.ABSTAIN, 0.0, "insufficient diagnosis confidence", "not_approved", "insufficient_evidence", abstained=True)
        if self.require_evidence and not relevant:
            return RecoveryPlan((RecoveryAction.ABSTAIN,), RecoveryAction.ABSTAIN, 0.0, "no relevant historical recovery evidence", "not_approved", "insufficient_evidence", abstained=True)
        attempted = {str(value) for value in context.get("failed_actions", ())}
        fallback_order = (self.default_action, RecoveryAction.RECONFIGURE, RecoveryAction.ROLLBACK, RecoveryAction.RETRY, RecoveryAction.REDEPLOY, RecoveryAction.RETRAIN)
        contributions: dict[RecoveryAction, list[tuple[str, float]]] = {}
        for match in relevant:
            event = getattr(match, "event", None)
            metadata = getattr(event, "metadata", {}) if event is not None else {}
            raw_action = metadata.get("recovery_action")
            if raw_action not in {candidate.value for candidate in RecoveryAction}:
                continue
            action = RecoveryAction(raw_action)
            if action in (RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE):
                continue
            validation = str(metadata.get("validation_status", ""))
            sign = 1.0 if validation == "RECOVERED" else -1.0 if validation in {"FAILED", "UNCERTAIN"} else 0.0
            similarity = float(getattr(match, "similarity", 0.0))
            event_confidence = float(getattr(event, "confidence", 0.5) or 0.5)
            event_id = str(getattr(event, "event_id", "unknown"))
            contributions.setdefault(action, []).append((event_id, sign * similarity * event_confidence))
        action_scores = {action: fsum(value for _, value in sorted(values, key=lambda item: item[0])) for action, values in contributions.items()}
        action_evidence = {action: [event_id for event_id, _ in sorted(values, key=lambda item: item[0])] for action, values in contributions.items()}

        positive = {action: score for action, score in action_scores.items() if score > 0 and action.value not in attempted}
        if positive:
            best_score = max(positive.values())
            best = [action for action, score in positive.items() if isclose(score, best_score, rel_tol=1e-12, abs_tol=1e-12)]
            if len(best) == 1:
                action = best[0]
                rationale = f"selected {action.value} from outcome-weighted relevant experience ({', '.join(action_evidence[action])})"
            else:
                action = RecoveryAction.ABSTAIN
                rationale = "conflicting relevant actions have equal positive evidence"
        else:
            available = [candidate for candidate in fallback_order if candidate.value not in attempted and action_scores.get(candidate, 0.0) >= 0]
            action = available[0] if available else RecoveryAction.ABSTAIN
            rationale = f"selected {action.value} from bounded fallback policy" if action is not RecoveryAction.ABSTAIN else "all available actions are failed or unsupported"
            if self.abstain_on_conflict and relevant and action is self.default_action and action_scores.get(action, 0.0) < 0:
                action = RecoveryAction.ABSTAIN
                rationale = "relevant negative experience conflicts with the default action"

        if diagnosis.failure_type == "resource_exhaustion" and not relevant and self.default_action is RecoveryAction.RETRY:
            action = RecoveryAction.RECONFIGURE
            rationale = "selected reconfigure from observed resource-exhaustion baseline"
        if context.get("unsafe_actions") and action.value in set(context["unsafe_actions"]):
            return RecoveryPlan((RecoveryAction.ABSTAIN,), RecoveryAction.ABSTAIN, 0.0, "candidate rejected by hard safety constraint", "rejected", "unsafe", abstained=True)
        if action in (RecoveryAction.ABSTAIN, RecoveryAction.ESCALATE):
            return RecoveryPlan((action,), action, 0.0, rationale, "not_approved", "insufficient_or_conflicting_evidence", abstained=True, escalated=action is RecoveryAction.ESCALATE)
        return RecoveryPlan((action,), action, diagnosis.confidence, rationale, "approved", "feasible")


class SimulatedRecoveryExecutor:
    """Deterministic simulator adapter; never represents production execution."""

    def __init__(self, outcome_by_action: Mapping[str, bool] | None = None, outcome_probabilities: Mapping[str, Mapping[str, float]] | None = None, seed: int = 0, simulator_version: str = "simulator-v2"):
        self.outcome_by_action = dict(outcome_by_action or {})
        self.outcome_probabilities = {str(failure): dict(actions) for failure, actions in (outcome_probabilities or {}).items()}
        self.seed = seed
        self.simulator_version = simulator_version
        self._rng = random.Random(seed)

    def execute(self, plan: RecoveryPlan, observation: Observation, attempt: int = 1) -> ExecutionResult:
        started = datetime.now(timezone.utc)
        if plan.abstained:
            return ExecutionResult(plan.selected_action, started, datetime.now(timezone.utc), "simulated", False, error="recovery abstained", attempt=attempt)
        failure_class = str(observation.environment.get("failure_class", observation.metadata.get("failure_class", "default")))
        probability = None
        draw = None
        if failure_class in self.outcome_probabilities and plan.selected_action.value in self.outcome_probabilities[failure_class]:
            probability = float(self.outcome_probabilities[failure_class][plan.selected_action.value])
            draw = self._rng.random()
            success = draw < probability
        else:
            success = bool(self.outcome_by_action.get(plan.selected_action.value, True))
        state = {"failure_present": not success, "failure_class": failure_class, "action": plan.selected_action.value, "probability": probability, "draw": draw, "seed": self.seed, "simulator_version": self.simulator_version}
        return ExecutionResult(plan.selected_action, started, datetime.now(timezone.utc), "simulated", success, workload_state=state, error=None if success else "simulated action failed", attempt=attempt)


class SignalRecoveryValidator:
    """Validates workload state independently from executor return status."""

    def validate(self, observation: Observation, reliability: ReliabilityAssessment, execution: ExecutionResult) -> ValidationResult:
        failure_present = execution.workload_state.get("failure_present")
        if failure_present is True:
            status = "FAILED"
            recovered: bool | None = False
        elif failure_present is False and execution.success:
            status = "RECOVERED"
            recovered = True
        else:
            status = "UNCERTAIN"
            recovered = None
        return ValidationResult(status, recovered, reliability.fused_score, reliability.fused_score if recovered else None, metrics={"execution_success": float(execution.success)}, rationale="validated from simulated workload state, not executor status alone")
