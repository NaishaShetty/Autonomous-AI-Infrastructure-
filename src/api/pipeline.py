"""The single, real inference->decision->persistence pipeline.

Both the live API (this package) and the benchmark harness
(``benchmarks/run_baselines.py``) call this same class. Phase 1 found the
Introspective-Failure-Memory-Model's live API returned hardcoded/mocked
values that diverged from what its own offline scripts actually computed
(PHASE1_AUDIT_REPORT.md section 3: "the live dashboard's risk-coverage chart
... is hardcoded ... not computed from that real experiment"). Sharing one
pipeline object between the API and the benchmark script makes that class of
bug structurally impossible here -- there is only one implementation of
"what does the system predict," not one for the demo and a different one
for the paper.
"""
from __future__ import annotations

import numpy as np

from src.decision.policy import DecisionMode, DecisionPolicy
from src.failure_memory.memory import FailureMemory
from src.reliability.calibrator import ConfidenceCalibrator
from src.reliability.workload_model import WorkloadModel
from src.schema.events import Decision, EventSource, Outcome, ReliabilityEvent
from src.storage.repository import EventRepository


class ReliabilityPipeline:
    """Wires workload model -> calibrator -> failure memory -> decision
    policy -> persistence into one call. All fitted components must be
    provided already-trained (see ``benchmarks/run_baselines.py`` for how
    they are trained); this class does not train anything itself."""

    def __init__(
        self,
        workload_model: WorkloadModel,
        calibrator: ConfidenceCalibrator,
        failure_memory: FailureMemory,
        policy: DecisionPolicy,
        feature_names: list[str],
        workload_id: str = "default-workload",
        mode: DecisionMode = DecisionMode.COMBINED,
    ):
        self.workload_model = workload_model
        self.calibrator = calibrator
        self.failure_memory = failure_memory
        self.policy = policy
        self.feature_names = feature_names
        self.workload_id = workload_id
        self.mode = mode

    def analyze(
        self,
        context: dict[str, float],
        repository: EventRepository | None = None,
        true_label: int | None = None,
    ) -> ReliabilityEvent:
        x = np.array([context.get(name, 0.0) for name in self.feature_names], dtype=float)
        prediction = self.workload_model.predict(x)

        calib_features = {
            **context,
            "predicted_proba": prediction.predicted_proba,
            "margin": prediction.margin,
            "entropy": prediction.entropy,
        }
        calibration = self.calibrator.predict(calib_features)

        risk = None
        if self.mode in (DecisionMode.RISK_ONLY, DecisionMode.COMBINED):
            risk = self.failure_memory.risk(context, calibration.calibrated_confidence)

        decision, _score = self.policy.decide(
            confidence=calibration.calibrated_confidence, risk=risk, mode=self.mode
        )

        outcome = Outcome.UNKNOWN
        is_failure = False
        if true_label is not None and decision == Decision.ANSWER:
            correct = prediction.predicted_label == true_label
            outcome = Outcome.CORRECT if correct else Outcome.INCORRECT
            is_failure = not correct
        elif true_label is not None and decision != Decision.ANSWER:
            # An abstention/review on a case we *could* have gotten wrong is
            # not itself a "failure" to store -- only confirmed wrong
            # ANSWERs are; see src/schema/events.py docstring on is_failure.
            is_failure = False

        event = ReliabilityEvent(
            workload_id=self.workload_id,
            source=EventSource.RELIABILITY_ENGINE,
            context=context,
            raw_confidence=calibration.raw_confidence,
            confidence=calibration.calibrated_confidence,
            failure_risk=risk,
            decision=decision,
            abstained=decision != Decision.ANSWER,
            is_failure=is_failure,
            outcome=outcome,
            metadata={"predicted_label": prediction.predicted_label, "mode": self.mode.value},
        )

        if repository is not None:
            repository.save(event)
            if is_failure:
                self.failure_memory.store(event, repository, persist=False)
                # Lifecycle: store() only marks the memory dirty (see
                # FailureMemory docstring) -- rebuild here so the next
                # request's risk() reflects this failure. A failed rebuild
                # leaves the previous valid clustering state in place.
                self.failure_memory.maybe_rebuild()

        return event
