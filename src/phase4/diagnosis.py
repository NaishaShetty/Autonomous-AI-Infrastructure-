"""Phase 4.3 deterministic diagnosis over confirmed controlled-runtime failures.

The module ends at structured diagnosis. It never executes recovery or other
infrastructure actions, and it does not train a model.

Historical-memory input (Phase 4.4): ``diagnose()`` accepts an optional
``memory`` argument. When present, it is queried strictly through
``FailureMemoryStore.retrieve`` under the frozen contract in
``src/phase4/memory.py`` -- same-run records are never eligible, retrieval
is scoped to ``(workload_id, environment_id, failure_class)``, and only
records with ``recorded_at <= diagnosis_boundary`` are returned. Historical
matches are added as ``HISTORICAL_MEMORY`` evidence; they can raise
``primary_hypothesis.confidence`` by at most one tier (LOW->MEDIUM or
MEDIUM->HIGH) when memory corroborates the current-run evidence, and never
change ``causal_status`` beyond ``SUPPORTED_CAUSAL_HYPOTHESIS`` -- memory
alone cannot promote a hypothesis to ``CONFIRMED_CAUSE``. When memory is not
supplied, behavior is byte-for-byte identical to before this change
(``memory_used`` stays ``False``, ``evidence_scope`` stays
``CURRENT_RUN_ONLY``).
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime
from enum import Enum
from typing import Any,Mapping,Sequence

class CausalStatus(str,Enum): OBSERVED='OBSERVED'; CORRELATED='CORRELATED'; SUPPORTED='SUPPORTED_CAUSAL_HYPOTHESIS'; CONFIRMED='CONFIRMED_CAUSE'; UNKNOWN='UNKNOWN'
class Confidence(str,Enum): HIGH='HIGH'; MEDIUM='MEDIUM'; LOW='LOW'; UNKNOWN='UNKNOWN'
class EvidenceKind(str,Enum): CURRENT='CURRENT_OBSERVATION'; HISTORICAL='HISTORICAL_MEMORY'; DERIVED='DERIVED_INFERENCE'; POST_FAILURE='POST_FAILURE_EVIDENCE'

_CONFIDENCE_PROMOTION = {Confidence.LOW.value: Confidence.MEDIUM.value, Confidence.MEDIUM.value: Confidence.HIGH.value}

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
def _eligible_current_incident(events, failure, boundary):
    """Return only current-incident evidence available at the decision boundary.

    ``job_id`` is the canonical controlled-runtime run identity.  Diagnosis
    does not currently support a historical-memory input, so evidence from
    another run is never eligible merely because it is earlier in time.
    Workload and environment identities are additional guards when present.
    """
    run_id = str(failure['run_id'])
    workload_id = failure.get('workload_id')
    environment_id = failure.get('environment_id')
    eligible = []
    for event in events:
        timestamp = event.get('timestamp')
        event_run_id = event.get('job_id') or event.get('run_id')
        if not timestamp or str(event_run_id) != run_id or _dt(timestamp) > _dt(boundary):
            continue
        if workload_id is not None and event.get('workload_id') != workload_id:
            continue
        if environment_id is not None and event.get('environment_id') != environment_id:
            continue
        eligible.append(event)
    return sorted(eligible, key=lambda event: (event.get('timestamp') or '', event.get('event_id') or ''))

def _ev(e,signal,value,relationship):
 return Evidence(evidence_id=str(e['event_id']),observation_id=str(e['event_id']),timestamp=e.get('timestamp'),signal=signal,observed_value=value,expected_value=None,availability='AVAILABLE_AT_FAILURE',provenance=e.get('provenance',{}),relationship=relationship)

class DiagnosisEngine:
    version='phase4.4-diagnosis-memory-v1'
    def diagnose(self,failure:Mapping[str,Any],events:Sequence[Mapping[str,Any]],diagnosis_boundary:str|None=None,memory=None)->StructuredDiagnosis:
        boundary=diagnosis_boundary or str(failure['failure_timestamp']); eligible=_eligible_current_incident(events,failure,boundary)
        fid=str(failure['failure_id']); rid=str(failure['run_id']); wid=str(failure['workload_id']); env=str(failure['environment_id']); cls=str(failure['failure_class']); evidence=[]; contradictions=[]
        for e in eligible:
            if e.get('event_id') in set(failure.get('evidence_references',[])):
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
        elif cls=='NETWORK_FAILURE':
            primary_name='NETWORK_CONNECTIVITY_FAILURE'; root='UNKNOWN'; status=CausalStatus.OBSERVED.value; confidence=Confidence.HIGH.value
            h_ev=tuple(e.evidence_id for e in evidence if e.signal=='failure_class'); alts=(Hypothesis('DEPENDENCY_UNAVAILABLE',0.3,0,0,Confidence.LOW.value,CausalStatus.UNKNOWN.value,()),Hypothesis('DNS_RESOLUTION_FAILURE',0.15,0,0,Confidence.LOW.value,CausalStatus.UNKNOWN.value,()))
        else: return self._unknown(failure,boundary,f'Unsupported failure class: {cls}')
        memory_used=False; memory_version=None
        if memory is not None:
            matches=memory.retrieve(workload_id=wid,environment_id=env,failure_class=cls,exclude_run_id=rid,at_or_before=boundary)
            if matches:
                memory_used=True; memory_version=memory.memory_version
                for m in matches:
                    rec=m.record
                    evidence.append(Evidence(evidence_id=rec.memory_id,observation_id=rec.source_diagnosis_id,timestamp=rec.recorded_at,signal='historical_failure_class',observed_value=rec.failure_class,expected_value=cls,availability='AVAILABLE_AT_DECISION',provenance=rec.provenance,relationship=f'prior {cls} in same workload/environment, action={rec.action_taken}, outcome={rec.validated_outcome}, relevance={m.relevance:.4f}',kind=EvidenceKind.HISTORICAL.value))
                # Memory can corroborate (raise confidence by at most one tier) but never
                # promote causal_status past SUPPORTED_CAUSAL_HYPOTHESIS on its own -- see
                # module docstring / src/phase4/memory.py contract item 3-4.
                corroborating=sum(1 for m in matches if m.record.validated_outcome=='RECOVERED')
                if corroborating>0 and confidence in _CONFIDENCE_PROMOTION:
                    confidence=_CONFIDENCE_PROMOTION[confidence]
                if status==CausalStatus.OBSERVED.value:
                    status=CausalStatus.SUPPORTED.value
        primary=Hypothesis(primary_name,1.0,len(h_ev),0,confidence,status,h_ev)
        prov=failure.get('provenance',{}); return StructuredDiagnosis(f'diagnosis:{fid}',fid,wid,rid,env,str(boundary),boundary,primary,alts,tuple(evidence),tuple(contradictions),confidence,'CONFIRMED_FAILURE_EVIDENCE',status,root,prov,{'detector_version':'phase4.2-detector-v1','memory_used':memory_used,'memory_version':memory_version,'evidence_scope':'CURRENT_RUN_ONLY_PLUS_SCOPED_HISTORICAL_MEMORY' if memory_used else 'CURRENT_RUN_ONLY','run_id':rid,'workload_id':wid,'environment_id':env})
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
