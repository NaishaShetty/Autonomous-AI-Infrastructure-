"""Phase 4 architecture and system contracts.

Contracts only: no V1 modification and no direct model-to-infrastructure path.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence
from src.data_foundation.foundation import CanonicalEvent, DecisionTimeSnapshot, Provenance, Availability

class AutonomyState(str, Enum):
    RECEIVED='RECEIVED'; OBSERVING='OBSERVING'; PREDICTED='PREDICTED'; DECIDING='DECIDING'; REQUESTING_EVIDENCE='REQUESTING_EVIDENCE'; ABSTAINED='ABSTAINED'; ESCALATED='ESCALATED'; DIAGNOSING='DIAGNOSING'; PLANNING='PLANNING'; SAFETY_CHECK='SAFETY_CHECK'; EXECUTING='EXECUTING'; VALIDATING='VALIDATING'; RECOVERED='RECOVERED'; NOT_RECOVERED='NOT_RECOVERED'; UNKNOWN='UNKNOWN'; COMPLETED='COMPLETED'

TERMINAL={AutonomyState.RECOVERED,AutonomyState.NOT_RECOVERED,AutonomyState.UNKNOWN,AutonomyState.COMPLETED}
ALLOWED={
 AutonomyState.RECEIVED:{AutonomyState.OBSERVING}, AutonomyState.OBSERVING:{AutonomyState.PREDICTED,AutonomyState.REQUESTING_EVIDENCE,AutonomyState.UNKNOWN},
 AutonomyState.PREDICTED:{AutonomyState.DECIDING}, AutonomyState.DECIDING:{AutonomyState.ABSTAINED,AutonomyState.ESCALATED,AutonomyState.DIAGNOSING,AutonomyState.REQUESTING_EVIDENCE},
 AutonomyState.REQUESTING_EVIDENCE:{AutonomyState.OBSERVING,AutonomyState.ESCALATED}, AutonomyState.ABSTAINED:{AutonomyState.COMPLETED}, AutonomyState.ESCALATED:{AutonomyState.COMPLETED,AutonomyState.DIAGNOSING},
 AutonomyState.DIAGNOSING:{AutonomyState.PLANNING,AutonomyState.ESCALATED,AutonomyState.UNKNOWN}, AutonomyState.PLANNING:{AutonomyState.SAFETY_CHECK},
 AutonomyState.SAFETY_CHECK:{AutonomyState.EXECUTING,AutonomyState.ABSTAINED,AutonomyState.ESCALATED}, AutonomyState.EXECUTING:{AutonomyState.VALIDATING,AutonomyState.UNKNOWN},
 AutonomyState.VALIDATING:{AutonomyState.RECOVERED,AutonomyState.NOT_RECOVERED,AutonomyState.UNKNOWN}, AutonomyState.RECOVERED:{AutonomyState.COMPLETED}, AutonomyState.NOT_RECOVERED:{AutonomyState.DIAGNOSING,AutonomyState.COMPLETED}, AutonomyState.UNKNOWN:{AutonomyState.COMPLETED}, AutonomyState.COMPLETED:set()
}

class SystemError(str,Enum):
 INVALID_INPUT='invalid input'; SCHEMA_VIOLATION='schema violation'; TIMESTAMP_VIOLATION='timestamp violation'; PROVENANCE_VIOLATION='provenance violation'; MISSING_EVIDENCE='missing required evidence'; STALE_STATE='stale state'; UNAVAILABLE_OBSERVATION='unavailable observation'; UNSAFE_ACTION='unsafe action'; EXECUTION_FAILURE='execution failure'; VALIDATION_FAILURE='validation failure'; UNKNOWN_OUTCOME='unknown outcome'; INTERNAL='internal system failure'

@dataclass(frozen=True)
class Prediction:
    prediction_id:str; job_id:str; snapshot_id:str; decision_time:str; score:float; provenance:Provenance
@dataclass(frozen=True)
class Decision:
    decision_id:str; prediction_id:str; action:str; rationale:str; safety_status:str; provenance:Provenance
@dataclass(frozen=True)
class Diagnosis:
    diagnosis_id:str; suspected_cause:str|None; alternative_causes:tuple[str,...]=(); evidence:tuple[Mapping[str,Any],...]=(); contradictory_evidence:tuple[Mapping[str,Any],...]=(); confidence:float|None=None; timestamp:str|None=None; provenance:Provenance|None=None
@dataclass(frozen=True)
class RecoveryAction:
    action_id:str; action_type:str; preconditions:tuple[str,...]=(); expected_effect:str=''; risk:str='UNKNOWN'; cost:str='UNKNOWN'; reversible:bool=False; authorization_required:bool=True; validation_requirements:tuple[str,...]=(); provenance:Provenance|None=None
@dataclass(frozen=True)
class ValidationOutcome:
    status:str; evidence:tuple[Mapping[str,Any],...]=(); timestamp:str|None=None; provenance:Provenance|None=None

class ObservabilityPort(Protocol):
    def current_snapshot(self, job_id:str, decision_time:str)->DecisionTimeSnapshot: ...
class PredictionPort(Protocol):
    def predict(self, snapshot:DecisionTimeSnapshot)->Prediction: ...
class DecisionPolicyPort(Protocol):
    def decide(self, prediction:Prediction)->Decision: ...
class DiagnosisPort(Protocol):
    def diagnose(self, events:Sequence[CanonicalEvent])->Diagnosis: ...
class PlannerPort(Protocol):
    def plan(self, diagnosis:Diagnosis)->RecoveryAction: ...
class SafetyGatePort(Protocol):
    def authorize(self, action:RecoveryAction, decision:Decision)->bool: ...
class ExecutorPort(Protocol):
    def execute(self, action:RecoveryAction)->Mapping[str,Any]: ...
class ValidatorPort(Protocol):
    def validate(self, execution:Mapping[str,Any])->ValidationOutcome: ...

class WorkloadStateMachine:
    def __init__(self): self.state=AutonomyState.RECEIVED; self.history=[self.state]
    def transition(self,to_state:AutonomyState)->None:
        if to_state not in ALLOWED[self.state]: raise ValueError(f'forbidden transition {self.state.value}->{to_state.value}')
        self.state=to_state; self.history.append(to_state)
    def can_transition(self,to_state:AutonomyState)->bool: return to_state in ALLOWED[self.state]

class SafetyGate:
    """Requires an explicit authorization boundary; score alone cannot execute."""
    def authorize(self, action:RecoveryAction, decision:Decision)->bool:
        if action.authorization_required and decision.safety_status != 'AUTHORIZED': return False
        return action.action_type in {'RETRY','RESCHEDULE','RECONFIGURE','RESOURCE_ADJUST','ROLLBACK','RETRAIN','REDEPLOY','ESCALATE','ABSTAIN'}

def ensure_decision_snapshot(snapshot:DecisionTimeSnapshot)->None:
    if snapshot.availability not in {Availability.BEFORE,Availability.AT}: raise ValueError(SystemError.TIMESTAMP_VIOLATION.value)
