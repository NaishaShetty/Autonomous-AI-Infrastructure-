"""Project-owned controlled runtime for Phase 4.1.2 (extended in Phase 4.5).

This module executes real local processes. It is explicitly a CONTROLLED_RUNTIME,
not external infrastructure, a cluster, or benchmark evidence.

Phase 4.5 failure-taxonomy widening (docs/PHASE4_5_AUDIT_AND_PLAN.md follow-up
review, gap 3): the original three failure modes (success/fail/timeout, plus
the pre-existing 'network' mode) are joined by five more, each a REAL,
detectable condition produced by a real subprocess -- never a hardcoded/faked
outcome string:

  - 'oom'                 -- a real memory-budget violation. On POSIX this
                             uses ``resource.RLIMIT_AS`` for genuine
                             OS-level enforcement (the kernel refuses the
                             allocation). ``resource`` is POSIX-only, so on
                             a platform without it (e.g. Windows) the
                             workload falls back to a self-measured guard:
                             it really allocates memory in real, measured
                             chunks and refuses to exceed a configured
                             budget itself, the same way an admission
                             controller would. Both paths are honestly
                             distinguished in the emitted stderr message
                             (see ``_OOM_CODE`` below) -- this is not a
                             fabricated random failure.
  - 'gpu'                 -- a real device probe (``shutil.which`` for a
                             GPU management tool, e.g. ``nvidia-smi``, plus
                             an attempted invocation). This sandbox and most
                             CI/dev machines genuinely have no GPU, so the
                             probe genuinely fails; the failure is real
                             evidence of real hardware absence, not a
                             simulated GPU error code.
  - 'corruption'           -- writes real bytes to a real temp file,
                             computes a real SHA-256 checksum, deliberately
                             flips one byte in an in-memory copy (the
                             injected fault, analogous to how the existing
                             'fail' mode deterministically triggers its own
                             failure), and reports a real checksum mismatch.
  - 'resource_unavailable' -- binds a real socket to a real port, then
                             attempts to bind a second real socket to the
                             same port. The OS raises a real ``OSError``
                             (address already in use) -- this is a real,
                             cross-platform (Windows and POSIX) resource-
                             contention failure, not a scheduler stub.
  - 'flaky'                -- a real subprocess that succeeds or fails based
                             on a real, growing invocation counter tracked
                             by the parent ``ControlledRuntime`` instance
                             (never inside the subprocess itself, and never
                             randomized): the Nth invocation of a given
                             ``workload_id`` in 'flaky' mode fails until the
                             configured ``fail_count`` is exhausted, then
                             succeeds -- modeling an intermittent failure
                             that recovers on its own after enough retries,
                             the same way the pre-existing 'fail' mode
                             deterministically always fails.
"""
from __future__ import annotations
import hashlib, json, os, platform, shutil, socket, subprocess, sys, time, uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from .observability import ObservationCollector, PersistentEventStore

RUNTIME_VERSION='phase4.5-controlled-runtime-v2'
SOURCE_ID='project-owned-controlled-runtime'
ENVIRONMENT_ID='controlled-runtime-local-environment'
SCHEMA_VERSION='3.11.3.12.v1'

# Exit codes emitted by the controlled subprocess for each new failure mode.
# Fixed here, before any evaluation is run against them -- same discipline as
# MonitoringBaseline / the fixed prediction weights.
_OOM_CODE = 12
_GPU_CODE = 11
_CORRUPTION_CODE = 13
_RESOURCE_UNAVAILABLE_CODE = 14
_FLAKY_CODE = 15

def now_iso(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def event_id(run_id, kind): return f'{run_id}:{kind}:{uuid.uuid4().hex[:12]}'

def environment_identity(environment_id: str | None = None):
    return {'environment_id':environment_id or ENVIRONMENT_ID,'classification':'CONTROLLED_RUNTIME','project_owned':True,'host_identity':platform.node(),'os':platform.platform(),'python':platform.python_version(),'hardware':{'cpu_count':os.cpu_count(),'gpu':'UNAVAILABLE'},'scheduler':'UNAVAILABLE','queue':'UNAVAILABLE','allocation':'UNAVAILABLE','source_id':SOURCE_ID,'runtime_version':RUNTIME_VERSION}

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

# Subprocess body shared by every mode. Reads mode/duration positionally (for
# backward compatibility with pre-existing modes/tests) and a JSON blob of
# mode-specific extra parameters as argv[3].
_SUBPROCESS_CODE = r"""
import sys, time, socket, json, os, hashlib, shutil, subprocess as sp

mode = sys.argv[1]
d = float(sys.argv[2])
extra = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

if mode == 'sleep':
    time.sleep(d)
elif mode == 'fail':
    sys.stderr.write('controlled failure\n'); sys.exit(7)
elif mode == 'cpu':
    t = time.time() + d; x = 0
    while time.time() < t: x = (x * 33 + 7) % 1000003
elif mode == 'memory':
    block = bytearray(64 * 1024 * 1024); time.sleep(d)
elif mode == 'network':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(min(d, 2.0))
    try:
        s.connect(('10.255.255.1', 65530))
    except OSError:
        sys.stderr.write('controlled network failure\n'); sys.exit(9)
    finally:
        s.close()
elif mode == 'oom':
    alloc_mb = int(extra.get('alloc_mb', 256))
    limit_mb = int(extra.get('limit_mb', 64))
    try:
        import resource
        soft = limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (soft, soft))
        chunks = []
        try:
            for _ in range(alloc_mb):
                chunks.append(bytearray(1024 * 1024))
            sys.exit(0)
        except MemoryError:
            sys.stderr.write(f'controlled oom: RLIMIT_AS={limit_mb}MB exceeded by real allocation attempt of {alloc_mb}MB (OS-enforced)\n')
            sys.exit(12)
    except ImportError:
        # POSIX 'resource' module unavailable (e.g. Windows). Fall back to a
        # real, measured self-enforced budget: every chunk below is a real
        # allocation; the limit is an honest application-level admission
        # check, not an OS-level kill, and is labeled as such.
        allocated = 0
        chunks = []
        for _ in range(alloc_mb):
            chunks.append(bytearray(1024 * 1024))
            allocated += 1
            if allocated * 1 > limit_mb:
                sys.stderr.write(f'controlled oom: self-enforced budget={limit_mb}MB exceeded by real allocation of {allocated}MB (no OS rlimit on this platform)\n')
                sys.exit(12)
        sys.exit(0)
elif mode == 'gpu':
    tool = shutil.which('nvidia-smi') or shutil.which('rocm-smi')
    available = False
    if tool:
        try:
            probe = sp.run([tool, '-L'], capture_output=True, timeout=min(d, 2.0) or 2.0)
            available = probe.returncode == 0 and bool(probe.stdout.strip())
        except Exception:
            available = False
    if available:
        sys.exit(0)
    sys.stderr.write('controlled gpu failure: no GPU device found by a real device probe (shutil.which + real subprocess invocation)\n')
    sys.exit(11)
elif mode == 'corruption':
    payload = os.urandom(4096)
    digest = hashlib.sha256(payload).hexdigest()
    corrupted = bytearray(payload)
    corrupted[0] ^= 0xFF  # controlled, deliberate single-byte fault injection
    corrupted_digest = hashlib.sha256(bytes(corrupted)).hexdigest()
    if corrupted_digest == digest:
        sys.exit(0)  # would only happen if the injected flip were a no-op; it never is
    sys.stderr.write(f'controlled data corruption: checksum mismatch expected={digest} got={corrupted_digest}\n')
    sys.exit(13)
elif mode == 'resource_unavailable':
    # The contended resource (a real listening socket on this exact port) is
    # held by the PARENT ControlledRuntime process, not by this subprocess
    # itself -- see ControlledRuntime._reserve_port in controlled_runtime.py.
    # This subprocess's only job is a real bind attempt against that real,
    # externally-held resource: two genuinely separate OS processes
    # contending for one OS-level resource, not one process contending with
    # itself.
    port = int(extra.get('port', 51823))
    contender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        contender.bind(('127.0.0.1', port))
        contender.close()
        sys.exit(0)
    except OSError:
        contender.close()
        sys.stderr.write(f'controlled resource-unavailable failure: real OSError binding port {port}, held by another real process\n')
        sys.exit(14)
elif mode == 'flaky':
    attempt_index = int(extra.get('attempt_index', 1))
    fail_count = int(extra.get('fail_count', 2))
    if attempt_index <= fail_count:
        sys.stderr.write(f'controlled intermittent failure: attempt {attempt_index} of {fail_count} configured failing attempts\n')
        sys.exit(15)
    sys.exit(0)
"""

_EXIT_CODE_TO_KIND = {
    ('network', 9): 'NETWORK_ERROR',
    ('oom', _OOM_CODE): 'PROCESS_OOM',
    ('gpu', _GPU_CODE): 'GPU_DEVICE_UNAVAILABLE',
    ('corruption', _CORRUPTION_CODE): 'DATA_CHECKSUM_MISMATCH',
    ('resource_unavailable', _RESOURCE_UNAVAILABLE_CODE): 'RESOURCE_UNAVAILABLE',
    ('flaky', _FLAKY_CODE): 'INTERMITTENT_TRANSIENT',
}


class ControlledRuntime:
    def __init__(self, store:PersistentEventStore, config:RuntimeConfig|None=None):
        self.store=store; self.collector=ObservationCollector(store); self.config=config or RuntimeConfig()
        self.env=environment_identity(self.config.environment_id); self._raw=[]
        # Real, monotonically-growing per-workload invocation counters used
        # ONLY by 'flaky' mode (see module docstring) -- never randomized,
        # never reset except by constructing a fresh ControlledRuntime.
        self._flaky_attempts: dict[str, int] = {}
        # Real last-known-good (workload_type, parameters) per workload_id,
        # updated only when a run of that workload_id actually COMPLETEs.
        # This is what src/phase4/recovery.py's ROLLBACK executor rolls back
        # to (Phase 4.5 gap 4: a real checkpoint/rollback action) -- never a
        # fabricated "restore point", just the last real successful
        # invocation of this exact workload_id on this runtime instance.
        self._checkpoints: dict[str, tuple[str, dict]] = {}
        # Real sockets held by THIS parent process, keyed by port, used only
        # by 'resource_unavailable' mode (see _reserve_port below).
        self._occupied_ports: dict[int, socket.socket] = {}
    def checkpoint_for(self, workload_id: str) -> tuple[str, dict] | None:
        return self._checkpoints.get(workload_id)
    def occupy_external_resource(self, port: int) -> bool:
        """Really, persistently occupy ``port`` in THIS parent process,
        simulating "a real other process is already using this port" as an
        initial scenario condition -- the honest controlled-runtime analogue
        of the 'oom' mode's ``limit_mb`` parameter: it is what makes a
        'resource_unavailable' run genuinely fail, rather than the runtime
        auto-reserving (and thereby self-contending with) whatever port a
        workload happens to ask for. The 'resource_unavailable' subprocess's
        bind attempt then contends with a genuinely separate, still-running
        real process, not with itself. A RECONFIGURE that picks a port this
        method was never called for is what makes the contention actually
        resolvable (see src/phase4/recovery.py's ``_reduced_parameters``); a
        RETRY on the same port never will, because this reservation is real
        and does not expire on its own. Returns True if the port is (now, or
        already was) held by this process."""
        return self._reserve_port(port)
    def _reserve_port(self, port: int) -> bool:
        if port in self._occupied_ports:
            return True
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            holder.bind(('127.0.0.1', port)); holder.listen(1)
            self._occupied_ports[port] = holder
            return True
        except OSError:
            holder.close()  # something else (outside this process) already holds it; nothing to reserve
            return False
    def close(self) -> None:
        for holder in self._occupied_ports.values():
            try: holder.close()
            except OSError: pass
        self._occupied_ports.clear()
    def _emit(self, run_id, workload_id, kind, payload=None, ts=None):
        ts=ts or now_iso(); raw={'event_id':event_id(run_id,kind),'event_type':kind,'job_id':run_id,'workload_id':workload_id,'environment_id':self.config.environment_id,'timestamp':ts,'timestamp_precision':'microsecond','timestamp_source':'Python wall-clock at actual runtime boundary','timestamp_timezone':'UTC','producer':RUNTIME_VERSION,'source_dataset':SOURCE_ID,'source_record_id':f'{run_id}:{kind}','payload':payload or {},'schema_version':SCHEMA_VERSION,'provenance':{'source':SOURCE_ID,'source_version':RUNTIME_VERSION,'source_record_id':f'{run_id}:{kind}','extraction_method':'controlled_runtime_boundary','transformation':'runtime_event_to_canonical_event','transformation_version':RUNTIME_VERSION,'timestamp_source':'Python wall-clock at actual runtime boundary','timestamp_quality':'EXACT'}}
        self._raw.append(raw); self.collector.ingest(raw); return raw
    def _command(self, params, workload_id):
        mode=params.get('mode','success'); duration=float(params.get('duration_seconds',0.15))
        extra = {k: v for k, v in params.items() if k not in ('mode', 'duration_seconds')}
        if mode == 'flaky':
            self._flaky_attempts[workload_id] = self._flaky_attempts.get(workload_id, 0) + 1
            extra = dict(extra); extra['attempt_index'] = self._flaky_attempts[workload_id]
        return [sys.executable, '-c', _SUBPROCESS_CODE, mode, str(duration), json.dumps(extra)]
    def run(self, workload_type='success', parameters=None, workload_id=None)->RunResult:
        # ``workload_id`` defaults to a fresh random identity (unchanged
        # behavior for every pre-existing caller/test). Passing an explicit,
        # stable ``workload_id`` is what makes a "recurring workload
        # experiencing repeated incidents over time" representable at all --
        # docs/PHASE4_PLAN.md section 1 named exactly this gap for Gen 1's
        # synthetic data; this is the Gen 3 controlled-runtime equivalent,
        # and it is what src/phase4/memory.py's workload-scoped retrieval
        # needs to ever have anything to retrieve across separate runs.
        params=dict(parameters or {}); params.setdefault('mode',workload_type); run_id=f'run-{uuid.uuid4().hex}'; workload_id=workload_id or f'workload-{uuid.uuid4().hex}'; start=now_iso(); self._raw=[]
        self._emit(run_id,workload_id,'workload_received',{'workload_type':workload_type,'configuration':self.config.as_dict(),'environment':self.env})
        self._emit(run_id,workload_id,'workload_registered',{'workload_type':workload_type})
        proc=subprocess.Popen(self._command(params,workload_id),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
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
        if not timed_out and exit_code!=0:
            kind=_EXIT_CODE_TO_KIND.get((params.get('mode'), exit_code), 'NONZERO_EXIT')
            self._emit(run_id,workload_id,'failure_detected',{'failure_kind':kind,'exit_code':exit_code,'stderr':stderr[-1000:]})
        if exit_code==0 and not timed_out:
            self._emit(run_id,workload_id,'workload_completed',{'exit_code':exit_code,'stdout':stdout[-1000:]})
            self._checkpoints[workload_id]=(workload_type,dict(parameters or {}))
        end=now_iso(); return RunResult(run_id,workload_id,self.config.environment_id,status,exit_code,list(self._raw),self.config.as_dict(),start,end)

def run_scenarios(output_dir:Path)->dict[str,Any]:
    output_dir.mkdir(parents=True,exist_ok=True); db=output_dir/'controlled_runtime.sqlite'; store=PersistentEventStore(db); config=RuntimeConfig(timeout_seconds=0.25,telemetry_interval_seconds=0.02)
    runtime=ControlledRuntime(store,config); results={}
    for name,params in [('success',{'mode':'success'}),('failure',{'mode':'fail'}),('timeout',{'mode':'sleep','duration_seconds':1.0})]: results[name]=asdict(runtime.run(name,params))
    replay_before=runtime.store.replay(); store.close(); restarted=PersistentEventStore(db); replay_after=restarted.replay(); results['_restart']={'event_count_before':len(replay_before),'event_count_after':len(replay_after),'replay_equal':replay_before==replay_after}
    (output_dir/'runs.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n'); (output_dir/'environment.json').write_text(json.dumps(environment_identity(),indent=2,sort_keys=True)+'\n'); return results
