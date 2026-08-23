"""Run Phase 4.2 monitoring over persisted controlled-runtime events."""
from pathlib import Path
import json
from src.phase4.observability import PersistentEventStore
from src.phase4.monitoring import MonitoringEngine,DetectionEvaluator
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1]
 db=root/'experiments/results/v1_1/phase4_controlled_runtime/4_1_2/controlled_runtime.sqlite'
 out=root/'experiments/results/v1_1/phase_monitoring_failure_detection/4_2'; out.mkdir(parents=True,exist_ok=True)
 store=PersistentEventStore(db); events=store.replay(); engine=MonitoringEngine(); states=engine.process(events)
 labels={'run-'+x.split(':')[1]: 'UNKNOWN' for x in []}
 runs=json.loads((root/'experiments/results/v1_1/phase_controlled_runtime/4_1_2/runs.json').read_text()) if (root/'experiments/results/v1_1/phase_controlled_runtime/4_1_2/runs.json').exists() else None
 # Derive labels directly from persisted run IDs and event evidence.
 for e in events:
  rid=str(e.get('job_id')); labels.setdefault(rid,'COMPLETED')
  if e.get('event_type')=='failure_detected': labels[rid]='TIMEOUT' if e.get('payload',{}).get('failure_kind')=='TIMEOUT' else 'FAILED'
 metrics=DetectionEvaluator().evaluate(labels,engine.failures,states); result={'states':states,'anomalies':engine.anomalies,'failures':engine.failures,'metrics':metrics,'baseline':engine.baseline.__dict__,'event_count':len(events),'controlled_runtime':True}
 (out/'monitoring_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'event_count':len(events),'states':states,'failures':len(engine.failures),'anomalies':len(engine.anomalies),'metrics':metrics},indent=2))
