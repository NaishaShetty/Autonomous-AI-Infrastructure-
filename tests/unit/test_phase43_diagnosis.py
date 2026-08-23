import pytest
from src.phase4.diagnosis import DiagnosisEngine,DiagnosisAPI,CausalStatus,Confidence

def ev(i,t,ts='2026-01-01T00:00:00Z',rid='r1',payload=None): return {'event_id':i,'event_type':t,'timestamp':ts,'job_id':rid,'workload_id':'w1','environment_id':'controlled-runtime-local-environment','payload':payload or {},'provenance':{'source':'project-owned-controlled-runtime','source_record_id':i,'timestamp_quality':'EXACT'}}
def failure(i='f1',cls='PROCESS_NONZERO_EXIT',rid='r1',ts='2026-01-01T00:00:02Z',payload=None): return {'failure_id':i,'failure_class':cls,'run_id':rid,'workload_id':'w1','environment_id':'controlled-runtime-local-environment','failure_timestamp':ts,'evidence_references':['fobs'],'provenance':{'source':'project-owned-controlled-runtime','source_record_id':'fobs','timestamp_quality':'EXACT'},'triggering_observation':payload or {}}

def test_nonzero_exit_is_observed_but_deeper_root_cause_unknown():
 d=DiagnosisEngine().diagnose(failure(),[ev('start','execution_started','2026-01-01T00:00:01Z'),ev('fobs','failure_detected','2026-01-01T00:00:02Z',payload={'failure_kind':'NONZERO_EXIT','exit_code':7})])
 assert d.primary_hypothesis.name=='PROCESS_EXIT_FAILURE'; assert d.causal_status==CausalStatus.OBSERVED.value; assert d.root_cause=='UNKNOWN'; assert d.confidence==Confidence.HIGH.value

def test_timeout_has_evidence_backed_hypothesis_not_automatic_deeper_cause():
 f=failure('f2','PROCESS_TIMEOUT','r2','2026-01-01T00:00:02Z'); es=[ev('start','execution_started','2026-01-01T00:00:00Z','r2'),ev('fobs','failure_detected','2026-01-01T00:00:02Z','r2',{'failure_kind':'TIMEOUT','configured_timeout_seconds':2,'termination':'actual subprocess kill'})]
 d=DiagnosisEngine().diagnose(f,es); assert d.primary_hypothesis.name=='RUNTIME_TIMEOUT'; assert d.causal_status==CausalStatus.SUPPORTED.value; assert d.root_cause=='UNKNOWN'; assert d.evidence

def test_future_events_do_not_change_boundary_diagnosis():
 f=failure(); early=[ev('start','execution_started','2026-01-01T00:00:01Z'),ev('fobs','failure_detected','2026-01-01T00:00:02Z',payload={'failure_kind':'NONZERO_EXIT'})]; future=early+[ev('later','workload_completed','2026-01-01T00:00:04Z')]
 assert DiagnosisEngine().replay(f,early)==DiagnosisEngine().replay(f,future,boundary='2026-01-01T00:00:02Z')

def test_unknown_when_no_eligible_evidence():
 d=DiagnosisEngine().diagnose(failure(),[ev('later','failure_detected','2026-01-01T00:00:03Z',payload={'failure_kind':'NONZERO_EXIT'})],diagnosis_boundary='2026-01-01T00:00:02Z'); assert d.primary_hypothesis.name=='UNKNOWN'; assert d.root_cause=='UNKNOWN'

def test_invalid_unsupported_failure_is_unknown_not_invented():
 d=DiagnosisEngine().diagnose(failure(cls='GPU_FAILURE'),[ev('fobs','failure_detected',payload={'failure_kind':'GPU_FAILURE'})]); assert d.primary_hypothesis.name=='UNKNOWN'

def test_provenance_and_evidence_references_are_preserved():
 d=DiagnosisEngine().diagnose(failure(),[ev('fobs','failure_detected',payload={'failure_kind':'NONZERO_EXIT','exit_code':7})]); assert d.provenance['source']=='project-owned-controlled-runtime'; assert d.evidence[0].observation_id=='fobs'

def test_api_retrieves_diagnosis_evidence_alternatives_and_history():
 d=DiagnosisEngine().diagnose(failure(),[ev('fobs','failure_detected',payload={'failure_kind':'NONZERO_EXIT'})]).to_dict(); api=DiagnosisAPI([d]); assert api.get(d['diagnosis_id'])==d; assert api.evidence(d['diagnosis_id']); assert api.alternatives(d['diagnosis_id']); assert len(api.history())==1
