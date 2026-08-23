"""Phase 4.3 deterministic diagnosis over confirmed controlled-runtime failures.

The module ends at structured diagnosis. It never executes recovery or other
infrastructure actions, and it does not train a model.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime
from enum import Enum
from typing import Any,Mapping,Sequence

class CausalStatus(str,Enum): OBSERVED='OBSERVED'; CORRELATED='CORRELATED'; SUPPORTED='SUPPORTED_CAUSAL_HYPOTHESIS'; CONFIRMED='CONFIRMED_CAUSE'; UNKNOWN='UNKNOWN'
class Confidence(str,Enum): HIGH='HIGH'; MEDIUM='MEDIUM'; LOW='LOW'; UNKNOWN='UNKNOWN'
class EvidenceKind(str,Enum): CURRENT='CURRENT_OBSERVATION'; HISTORICAL='HISTORICAL_MEMORY'; DERIVED='DERIVED_INFERENCE'; POST_FAILURE='POST_FAILURE_EVIDENCE'

@dataclass(frozen=True)
class Evidence:
    evidence_id:str; observation_id:str; timestamp:str|None; signal:str; observed_value:Any; expected_value:Any; availability:str; provenance:Mapping[str,Any]; relationship:str; kind:str=EvidenceKind.CURRENT.value

@dataclass(frozen=True)
class Hypothesis:
    name:str; score:float; evidence_count:int; contradiction_count:int; confidence:str; causal_status:str; evidence_ids:tuple[str,...]; contradictory_evidence_ids:tuple[str,...]=()

@dataclass(frozen=True)
class StructuredDiagnosis:
    diagnosis_id:str; failure_id:str; workload_id:str; run_id:str; environment_id:str; diagnosis_timestamp:str; diagnosis_boundary:str; primary_hypothesis:Hypothesis; alternative_hypotheses:tuple[Hypothesis,...]; evidence:tuple[Evidence,...]; contradictory_evidence:tuple[Evidence,...]; confidence:str; certainty:str; causal_status:str; root_cause:str; provenance:Mapping[str,Any]; foundation_references:Mapping[str,Any]; diagnosis_method:str='deterministic-causal-rules-v1'; memory_used:bool=False
    def to_dict(self):
        x=asdict(self); x['primary_hypothesis']=asdict(self.primary_hypothesis); x['alternative_hypotheses']=[asdict(h) for h in self.alternative_hypotheses]; x['evidence']=[asdict(e) for e in self.evidence]; x['contradictory_evidence']=[asdict(e) for e in self.contradictory_evidence]; return x

def _dt(x): return datetime.fromisoformat(str(x).replace('Z','+00:00'))
def _eligible(events,boundary): return [e for e in events if e.get('timestamp') and _dt(e['timestamp'])<=_dt(boundary)]

def _ev(e,signal,value,relationship):
 return Evidence(evidence_id=str(e['event_id']),observation_id=str(e['event_id']),timestamp=e.get('timestamp'),signal=signal,observed_value=value,expected_value=None,availability='AVAILABLE_AT_FAILURE',provenance=e.get('provenance',{}),relationship=relationship)

class DiagnosisEngine:
    version='phase4.3-diagnosis-v1'
    def diagnose(self,failure:Mapping[str,Any],events:Sequence[Mapping[str,Any]],diagnosis_boundary:str|None=None)->StructuredDiagnosis:
        boundary=diagnosis_boundary or str(failure['failure_timestamp']); eligible=_eligible(events,boundary)
        fid=str(failure['failure_id']); rid=str(failure['run_id']); wid=str(failure['workload_id']); env=str(failure['environment_id']); cls=str(failure['failure_class']); evidence=[]; contradictions=[]
        for e in eligible:
            if e.get('event_id') in set(failure.get('evidence_references',[])) or e.get('event_type')=='failure_detected':
                p=e.get('payload',{}); kind=p.get('failure_kind'); evidence.append(_ev(e,'failure_class',kind, 'direct failure observation'))
            elif e.get('event_type')=='execution_started': evidence.append(_ev(e,'execution_started',True,'establishes process was launched'))
            elif e.get('event_type')=='telemetry_observed':
                p=e.get('payload',{}); evidence.append(_ev(e,'process_telemetry',{'rss':p.get('process_rss_bytes'),'cpu_ticks':p.get('process_cpu_ticks')},'pre-failure runtime context'))
        if not evidence: return self._unknown(failure,boundary,'No eligible evidence was available at diagnosis boundary')
        if cls=='PROCESS_TIMEOUT':
            primary_name='RUNTIME_TIMEOUT'; root='UNKNOWN'; status=CausalStatus.SUPPORTED.value; confidence=Confidence.HIGH.value
            h_ev=tuple(e.evidence_id for e in evidence if e.signal=='failure_class'); alts=(Hypothesis('EXCESSIVE_RUNTIME',0.4,0,0,Confidence.MEDIUM.value,CausalStatus.CORRELATED.value,h_ev),Hypothesis('RESOURCE_PRESSURE',0.2,0,0,Confidence.LOW.value,CausalStatus.UNKNOWN.value,()))
        elif cls=='PROCESS_NONZERO_EXIT':
            primary_name='PROCESS_EXIT_FAILURE'; root='UNKNOWN'; status=CausalStatus.OBSERVED.value; confidence=Confidence.HIGH.value
            h_ev=tuple(e.evidence_id for e in evidence if e.signal=='failure_class'); alts=(Hypothesis('WORKLOAD_CONFIGURATION',0.2,0,0,Confidence.LOW.value,CausalStatus.UNKNOWN.value,()),Hypothesis('RESOURCE_PRESSURE',0.1,0,0,Confidence.LOW.value,CausalStatus.UNKNOWN.value,()))
        else: return self._unknown(failure,boundary,f'Unsupported failure class: {cls}')
        primary=Hypothesis(primary_name,1.0,len(h_ev),0,confidence,status,h_ev)
        prov=failure.get('provenance',{}); return StructuredDiagnosis(f'diagnosis:{fid}',fid,wid,rid,env,str(boundary),boundary,primary,alts,tuple(evidence),tuple(contradictions),confidence,'CONFIRMED_FAILURE_EVIDENCE',status,root,prov,{'detector_version':'phase4.2-detector-v1','memory_used':False})
    def _unknown(self,failure,boundary,reason):
        h=Hypothesis('UNKNOWN',0.0,0,0,Confidence.UNKNOWN.value,CausalStatus.UNKNOWN.value,())
        return StructuredDiagnosis(f"diagnosis:{failure['failure_id']}",str(failure['failure_id']),str(failure.get('workload_id')),str(failure.get('run_id')),str(failure.get('environment_id')),str(boundary),str(boundary),h,(),(),(),Confidence.UNKNOWN.value,'CONFIRMED_FAILURE_EVIDENCE',CausalStatus.UNKNOWN.value,'UNKNOWN',failure.get('provenance',{}),{'reason':reason,'memory_used':False})
    def replay(self,failure,events,boundary=None): return self.diagnose(failure,events,boundary).to_dict()

class DiagnosisAPI:
    def __init__(self,diagnoses): self._items={d['diagnosis_id']:d for d in diagnoses}
    def get(self,diagnosis_id): return self._items.get(diagnosis_id)
    def evidence(self,diagnosis_id):
        d=self.get(diagnosis_id); return [] if d is None else d.get('evidence',[])
    def alternatives(self,diagnosis_id):
        d=self.get(diagnosis_id); return [] if d is None else d.get('alternative_hypotheses',[])
    def history(self): return list(self._items.values())
