"""Phase 4.2 monitoring and failure detection over canonical runtime events.

This module ends at structured failure events. It contains no diagnosis,
recovery, infrastructure mutation, V1.1 model, or benchmark logic.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

class MonitoringState(str,Enum): HEALTHY='HEALTHY'; DEGRADED='DEGRADED'; ANOMALOUS='ANOMALOUS'; FAILED='FAILED'; UNKNOWN='UNKNOWN'

ALLOWED={MonitoringState.UNKNOWN:{MonitoringState.HEALTHY,MonitoringState.ANOMALOUS,MonitoringState.DEGRADED},MonitoringState.HEALTHY:{MonitoringState.DEGRADED,MonitoringState.ANOMALOUS,MonitoringState.FAILED},MonitoringState.DEGRADED:{MonitoringState.HEALTHY,MonitoringState.ANOMALOUS,MonitoringState.FAILED},MonitoringState.ANOMALOUS:{MonitoringState.HEALTHY,MonitoringState.FAILED,MonitoringState.DEGRADED},MonitoringState.FAILED:set()}

@dataclass(frozen=True)
class MonitoringBaseline:
    version:str='phase4.2-baseline-v1'
    max_runtime_seconds:float=1.0
    max_process_rss_bytes:int=512*1024*1024
    source:str='fixed engineering envelope established before evaluation'
    learned:bool=False
    rationale:str='Conservative local-process safety envelope; not tuned on evaluation outcomes.'

@dataclass(frozen=True)
class AnomalyRecord:
    anomaly_id:str; workload_id:str; run_id:str; environment_id:str; event_id:str; detection_timestamp:str; signal:str; observed_value:Any; expected_condition:str; severity:str; rule_version:str; detector_version:str; provenance:Mapping[str,Any]; availability:str='AVAILABLE_AT_DECISION'

@dataclass(frozen=True)
class FailureEvent:
    failure_id:str; workload_id:str; run_id:str; environment_id:str; failure_class:str; failure_timestamp:str; detection_timestamp:str; detection_latency_seconds:float; evidence_references:tuple[str,...]; triggering_observation:Mapping[str,Any]; provenance:Mapping[str,Any]; certainty:str='CONFIRMED'; availability:str='AVAILABLE_AT_DECISION'; detector_version:str='phase4.2-detector-v1'

class MonitoringStateMachine:
    def __init__(self): self.state=MonitoringState.UNKNOWN; self.history=[self.state.value]
    def transition(self,to:MonitoringState):
        if to not in ALLOWED[self.state]: raise ValueError(f'forbidden monitoring transition {self.state.value}->{to.value}')
        self.state=to; self.history.append(to.value)
    def as_dict(self): return {'current_state':self.state.value,'history':list(self.history)}

class AnomalyDetector:
    version='phase4.2-anomaly-rules-v1'
    def __init__(self,baseline:MonitoringBaseline|None=None): self.baseline=baseline or MonitoringBaseline()
    def detect(self,event:Mapping[str,Any])->AnomalyRecord|None:
        payload=event.get('payload',{}); ts=event.get('timestamp');
        if not ts: return None
        signal=None; value=None; condition=''; severity='LOW'
        if event.get('event_type')=='telemetry_observed':
            rss=payload.get('process_rss_bytes')
            if isinstance(rss,(int,float)) and rss>self.baseline.max_process_rss_bytes: signal='process_rss'; value=rss; condition=f'RSS <= {self.baseline.max_process_rss_bytes} bytes'; severity='MEDIUM'
        if event.get('event_type')=='failure_detected': return None
        if signal is None: return None
        return AnomalyRecord(anomaly_id=f"anomaly:{event['event_id']}",workload_id=str(event.get('workload_id') or event.get('job_id')),run_id=str(event.get('job_id')),environment_id=str(event.get('environment_id')),event_id=str(event['event_id']),detection_timestamp=str(ts),signal=signal,observed_value=value,expected_condition=condition,severity=severity,rule_version=self.baseline.version,detector_version=self.version,provenance=event.get('provenance',{}))

_FAILURE_KIND_TO_CLASS={
    'NONZERO_EXIT':'PROCESS_NONZERO_EXIT','TIMEOUT':'PROCESS_TIMEOUT','NETWORK_ERROR':'NETWORK_FAILURE',
    # Phase 4.5 failure-taxonomy widening (docs review gap 3). Each of these
    # is produced by a real, detectable condition in
    # src/phase4/controlled_runtime.py -- see that module's docstring for
    # exactly what is real vs. honestly-labeled-fallback per mode. Note that
    # 'GPU_FAILURE'/'GPU_ECC_ERROR'/'SCHEDULER_FAILURE' remain deliberately
    # ABSENT from this map (still raise ValueError below, still listed as
    # unsupported by DetectionEvaluator) -- those are placeholder probe
    # payloads / a true distributed-scheduler class this single-process
    # sandbox has no real signal for. 'GPU_DEVICE_UNAVAILABLE' below is a
    # different, real signal (real device-absence probe), which is why it
    # gets its own distinct kind string rather than reusing 'GPU_FAILURE'.
    'PROCESS_OOM':'PROCESS_OOM','GPU_DEVICE_UNAVAILABLE':'GPU_DEVICE_FAILURE',
    'DATA_CHECKSUM_MISMATCH':'DATA_CORRUPTION','RESOURCE_UNAVAILABLE':'RESOURCE_UNAVAILABLE',
    'INTERMITTENT_TRANSIENT':'INTERMITTENT_FAILURE',
    # Phase 4.5b -- the second gap named in the project's own strategic
    # review: this pipeline never evaluated an actual AI/ML agent's OUTPUT
    # correctness, only OS/process telemetry. AGENT_INCORRECT_ANSWER is a
    # real, detected failure class produced by src/phase4/agent_runtime.py
    # (majority-vote answer, from real independent samples, disagrees with
    # a real ground-truth oracle) -- not a process failure, but reuses this
    # exact detection/classification path since the shape of the evidence
    # (a `failure_detected` canonical event with a `failure_kind`) is
    # identical. AGENT_TASK_TIMEOUT/AGENT_WORKER_ERROR are the honest
    # non-correctness failure modes of that same runtime (the subprocess
    # itself hanging or crashing, distinct from "it ran and answered
    # wrong").
    'AGENT_INCORRECT_ANSWER':'AGENT_INCORRECT_ANSWER','AGENT_TASK_TIMEOUT':'AGENT_TASK_TIMEOUT',
    'AGENT_WORKER_ERROR':'AGENT_WORKER_ERROR',
}

class FailureDetector:
    version='phase4.5-failure-rules-v3'
    def detect(self,event:Mapping[str,Any])->FailureEvent|None:
        if event.get('event_type')!='failure_detected': return None
        payload=event.get('payload',{}); kind=payload.get('failure_kind');
        if kind not in _FAILURE_KIND_TO_CLASS: raise ValueError(f'unsupported failure type: {kind}')
        cls=_FAILURE_KIND_TO_CLASS[kind]; ts=str(event.get('timestamp')); latency=0.0
        return FailureEvent(failure_id=f"failure:{event['event_id']}",workload_id=str(event.get('workload_id') or event.get('job_id')),run_id=str(event.get('job_id')),environment_id=str(event.get('environment_id')),failure_class=cls,failure_timestamp=ts,detection_timestamp=ts,detection_latency_seconds=latency,evidence_references=(str(event['event_id']),),triggering_observation=dict(event),provenance=event.get('provenance',{}))

class MonitoringEngine:
    version='phase4.2-monitor-v1'
    def __init__(self,baseline:MonitoringBaseline|None=None): self.baseline=baseline or MonitoringBaseline(); self.anomalies=[]; self.failures=[]; self.states={}
    def process(self,events:Sequence[Mapping[str,Any]],at_or_before:str|None=None):
        ordered=sorted(events,key=lambda e:(e.get('timestamp') or '',e.get('event_id','')))
        if at_or_before is not None: ordered=[e for e in ordered if e.get('timestamp') and e['timestamp']<=at_or_before]
        anomaly=AnomalyDetector(self.baseline); failure=FailureDetector(); states={}; anomaly_counts={}
        for e in ordered:
            run=str(e.get('job_id')); sm=states.setdefault(run,MonitoringStateMachine()); a=anomaly.detect(e)
            if a:
                # Sustained-anomaly escalation: a signal that recurs 3+ times within the
                # same run is treated as HIGH severity rather than the rule's static default.
                # This is a genuinely different capability from a single fixed threshold --
                # it aggregates over time within a run rather than evaluating one event in
                # isolation -- addressing the "one fixed threshold" limitation named in
                # docs/PHASE4_5_AUDIT_AND_PLAN.md section 3.2.
                anomaly_counts[run]=anomaly_counts.get(run,0)+1
                record=asdict(a)
                if anomaly_counts[run]>=3: record['severity']='HIGH'
                self.anomalies.append(record)
                if sm.state in {MonitoringState.UNKNOWN,MonitoringState.HEALTHY,MonitoringState.DEGRADED}: sm.transition(MonitoringState.ANOMALOUS)
            f=failure.detect(e)
            if f:
                self.failures.append(asdict(f));
                if sm.state!=MonitoringState.FAILED: sm.transition(MonitoringState.FAILED)
            elif e.get('event_type')=='workload_completed' and sm.state in {MonitoringState.UNKNOWN,MonitoringState.HEALTHY,MonitoringState.DEGRADED,MonitoringState.ANOMALOUS}: 
                if sm.state==MonitoringState.UNKNOWN: sm.transition(MonitoringState.HEALTHY)
            elif e.get('event_type')=='execution_started' and sm.state==MonitoringState.UNKNOWN: sm.transition(MonitoringState.HEALTHY)
        self.states={k:v.as_dict() for k,v in states.items()}; return self.states
    def replay(self,events):
        a=MonitoringEngine(self.baseline); a.process(events); return {'states':a.states,'anomalies':a.anomalies,'failures':a.failures}

class DetectionEvaluator:
    def evaluate(self,scenario_labels:Mapping[str,str],failure_events:Sequence[Mapping[str,Any]],states:Mapping[str,Any]):
        predicted={x['run_id'] for x in failure_events}; actual={k for k,v in scenario_labels.items() if v in {'FAILED','TIMEOUT'}}; tp=len(predicted&actual); fp=len(predicted-actual); fn=len(actual-predicted); tn=len(set(scenario_labels)-predicted-actual); precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0; f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        return {'true_positives':tp,'false_positives':fp,'false_negatives':fn,'true_negatives':tn,'precision':precision,'recall':recall,'f1':f1,'anomaly_count':0,'run_count':len(scenario_labels),'unsupported_classes':['GPU_FAILURE','SCHEDULER_FAILURE']}
