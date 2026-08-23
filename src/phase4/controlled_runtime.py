"""Project-owned controlled runtime for Phase 4.1.2.

This module executes real local processes. It is explicitly a CONTROLLED_RUNTIME,
not external infrastructure, a cluster, or benchmark evidence.
"""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time, uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from .observability import ObservationCollector, PersistentEventStore

RUNTIME_VERSION='phase4.1.2-controlled-runtime-v1'
SOURCE_ID='project-owned-controlled-runtime'
ENVIRONMENT_ID='controlled-runtime-local-environment'
SCHEMA_VERSION='3.11.3.12.v1'

def now_iso(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def event_id(run_id, kind): return f'{run_id}:{kind}:{uuid.uuid4().hex[:12]}'

def environment_identity():
    return {'environment_id':ENVIRONMENT_ID,'classification':'CONTROLLED_RUNTIME','project_owned':True,'host_identity':platform.node(),'os':platform.platform(),'python':platform.python_version(),'hardware':{'cpu_count':os.cpu_count(),'gpu':'UNAVAILABLE'},'scheduler':'UNAVAILABLE','queue':'UNAVAILABLE','allocation':'UNAVAILABLE','source_id':SOURCE_ID,'runtime_version':RUNTIME_VERSION}

@dataclass(frozen=True)
class RuntimeConfig:
    workload_type:str='python'
    workload_parameters:Mapping[str,Any]=None
    timeout_seconds:float|None=5.0
    telemetry_interval_seconds:float=0.05
    environment_id:str=ENVIRONMENT_ID
    source_id:str=SOURCE_ID
    instrumentation_version:str=RUNTIME_VERSION
    def __post_init__(self):
        if self.workload_parameters is None: object.__setattr__(self,'workload_parameters',{})
    def as_dict(self): return asdict(self)

@dataclass
class RunResult:
    run_id:str; workload_id:str; environment_id:str; status:str; exit_code:int|None; events:list[dict[str,Any]]; config:dict[str,Any]; collection_start:str; collection_end:str

class ControlledRuntime:
    def __init__(self, store:PersistentEventStore, config:RuntimeConfig|None=None):
        self.store=store; self.collector=ObservationCollector(store); self.config=config or RuntimeConfig()
        self.env=environment_identity(); self._raw=[]
    def _emit(self, run_id, workload_id, kind, payload=None, ts=None):
        ts=ts or now_iso(); raw={'event_id':event_id(run_id,kind),'event_type':kind,'job_id':run_id,'workload_id':workload_id,'environment_id':self.config.environment_id,'timestamp':ts,'timestamp_precision':'microsecond','timestamp_source':'Python wall-clock at actual runtime boundary','timestamp_timezone':'UTC','producer':RUNTIME_VERSION,'source_dataset':SOURCE_ID,'source_record_id':f'{run_id}:{kind}','payload':payload or {},'schema_version':SCHEMA_VERSION,'provenance':{'source':SOURCE_ID,'source_version':RUNTIME_VERSION,'source_record_id':f'{run_id}:{kind}','extraction_method':'controlled_runtime_boundary','transformation':'runtime_event_to_canonical_event','transformation_version':RUNTIME_VERSION,'timestamp_source':'Python wall-clock at actual runtime boundary','timestamp_quality':'EXACT'}}
        self._raw.append(raw); self.collector.ingest(raw); return raw
    def _command(self, params):
        mode=params.get('mode','success'); duration=float(params.get('duration_seconds',0.15))
        code="import sys,time\nmode=sys.argv[1]; d=float(sys.argv[2])\nif mode=='sleep': time.sleep(d)\nelif mode=='fail': sys.stderr.write('controlled failure\\n'); sys.exit(7)\nelif mode=='cpu':\n t=time.time()+d; x=0\n while time.time()<t: x=(x*33+7)%1000003\n"
        return [sys.executable,'-c',code,mode,str(duration)]
    def run(self, workload_type='success', parameters=None)->RunResult:
        params=dict(parameters or {}); params.setdefault('mode',workload_type); run_id=f'run-{uuid.uuid4().hex}'; workload_id=f'workload-{uuid.uuid4().hex}'; start=now_iso(); self._raw=[]
        self._emit(run_id,workload_id,'workload_received',{'workload_type':workload_type,'configuration':self.config.as_dict(),'environment':self.env})
        self._emit(run_id,workload_id,'workload_registered',{'workload_type':workload_type})
        proc=subprocess.Popen(self._command(params),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self._emit(run_id,workload_id,'execution_started',{'pid':proc.pid,'workload_type':workload_type})
        timed_out=False; telemetry_count=0; deadline=time.monotonic()+self.config.timeout_seconds if self.config.timeout_seconds is not None else None
        while proc.poll() is None:
            time.sleep(max(0.001,self.config.telemetry_interval_seconds))
            try:
                rss=None; cpu_ticks=None
                status=Path(f'/proc/{proc.pid}/status')
                if status.exists():
                    for line in status.read_text().splitlines():
                        if line.startswith('VmRSS:'): rss=int(line.split()[1])*1024
                stat=Path(f'/proc/{proc.pid}/stat')
                if stat.exists(): cpu_ticks=stat.read_text().split()[13:15]
                self._emit(run_id,workload_id,'telemetry_observed',{'pid':proc.pid,'process_rss_bytes':rss,'process_cpu_ticks':cpu_ticks,'cpu':'OBSERVED_FROM_PROC','memory':'OBSERVED_FROM_PROC','gpu':'UNAVAILABLE','scheduler':'UNAVAILABLE','queue':'UNAVAILABLE','sample_index':telemetry_count}); telemetry_count+=1
            except (FileNotFoundError,PermissionError): pass
            if deadline is not None and time.monotonic()>=deadline and proc.poll() is None:
                timed_out=True; proc.kill(); self._emit(run_id,workload_id,'failure_detected',{'failure_kind':'TIMEOUT','configured_timeout_seconds':self.config.timeout_seconds,'termination':'actual subprocess kill','pid':proc.pid}); break
        stdout,stderr=proc.communicate(); exit_code=proc.returncode; status='TIMEOUT' if timed_out else ('COMPLETED' if exit_code==0 else 'FAILED')
        if not timed_out and exit_code!=0: self._emit(run_id,workload_id,'failure_detected',{'failure_kind':'NONZERO_EXIT','exit_code':exit_code,'stderr':stderr[-1000:]})
        if exit_code==0 and not timed_out: self._emit(run_id,workload_id,'workload_completed',{'exit_code':exit_code,'stdout':stdout[-1000:]})
        end=now_iso(); return RunResult(run_id,workload_id,self.config.environment_id,status,exit_code,list(self._raw),self.config.as_dict(),start,end)

def run_scenarios(output_dir:Path)->dict[str,Any]:
    output_dir.mkdir(parents=True,exist_ok=True); db=output_dir/'controlled_runtime.sqlite'; store=PersistentEventStore(db); config=RuntimeConfig(timeout_seconds=0.25,telemetry_interval_seconds=0.02)
    runtime=ControlledRuntime(store,config); results={}
    for name,params in [('success',{'mode':'success'}),('failure',{'mode':'fail'}),('timeout',{'mode':'sleep','duration_seconds':1.0})]: results[name]=asdict(runtime.run(name,params))
    replay_before=runtime.store.replay(); store.close(); restarted=PersistentEventStore(db); replay_after=restarted.replay(); results['_restart']={'event_count_before':len(replay_before),'event_count_after':len(replay_after),'replay_equal':replay_before==replay_after}
    (output_dir/'runs.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n'); (output_dir/'environment.json').write_text(json.dumps(environment_identity(),indent=2,sort_keys=True)+'\n'); return results
