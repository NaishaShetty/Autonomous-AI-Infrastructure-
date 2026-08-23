"""Phase 4.1 deterministic runtime observability implementation."""
from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Mapping
from src.data_foundation.foundation import CanonicalEvent,DecisionTimeSnapshot,Provenance,Availability,TimestampQuality,classify_availability,validate_event_order
from .architecture import AutonomyState,WorkloadStateMachine

class EventValidator:
    def validate(self,event:CanonicalEvent)->CanonicalEvent:
        if not event.event_id or not event.source_dataset or event.provenance is None: raise ValueError('invalid event provenance')
        return event

class EventStore:
    def __init__(self): self._events=[]
    def append(self,event:CanonicalEvent):
        EventValidator().validate(event); self._events.append(event)
    def events(self,job_id=None,at_or_before=None):
        result=[e for e in self._events if job_id is None or e.job_id==job_id]
        if at_or_before is not None:
            limit=datetime.fromisoformat(at_or_before.replace('Z','+00:00')); result=[e for e in result if e.timestamp and datetime.fromisoformat(e.timestamp.replace('Z','+00:00'))<=limit]
        return sorted(result,key=lambda e:(e.timestamp or '',e.event_id))
    def replay(self): return [e.to_dict() for e in self.events()]

class WorkloadStateStore:
    def __init__(self): self._states={}
    def state(self,job_id): return self._states.setdefault(job_id,WorkloadStateMachine())
    def transition(self,job_id,to_state): self.state(job_id).transition(to_state)

class EnvironmentStateStore:
    def __init__(self): self._items={}
    def put(self,environment_id,identity): self._items[environment_id]=dict(identity)
    def get(self,environment_id): return self._items.get(environment_id,{'status':'UNAVAILABLE'})

class ResourceStateStore(EnvironmentStateStore): pass
class SchedulerStateStore(EnvironmentStateStore): pass

class DecisionSnapshotBuilder:
    def __init__(self,store:EventStore): self.store=store
    def build(self,job_id:str,decision_time:str)->DecisionTimeSnapshot:
        all_events=self.store.events(job_id)
        if not all_events: raise ValueError('missing required evidence')
        bad=[e.event_id for e in all_events if e.timestamp is None]
        if bad: raise ValueError('timestamp-unknown information cannot enter a proven snapshot')
        events=[e for e in all_events if e.timestamp and e.timestamp<=decision_time]
        if not events: raise ValueError('missing required evidence')
        post=[e for e in all_events if e.timestamp and e.timestamp>decision_time]
        if post: raise ValueError('post-decision observation rejected')
        prov=tuple(e.provenance for e in events if e.provenance)
        return DecisionTimeSnapshot(snapshot_id=f'snapshot:{job_id}:{decision_time}',decision_time=decision_time,workload_context={'job_id':job_id},task_context={},resource_context={},scheduler_context={},queue_context={},environment_context={},recent_historical_context={'event_count':len(events)},provenance=prov,timestamp_quality=TimestampQuality.SYNCHRONIZED,availability=Availability.AT)

class ObservationCollector:
    def __init__(self,store:EventStore): self.store=store
    def ingest(self,raw:Mapping[str,Any])->CanonicalEvent:
        if raw.get('schema_version') not in (None,'3.11.3.12.v1'): raise ValueError('schema violation')
        p=raw.get('provenance') or {}; provenance=Provenance(source=str(p.get('source',raw.get('source_dataset','unknown'))),source_record_id=p.get('source_record_id',raw.get('source_record_id')),extraction_method=p.get('extraction_method','runtime_ingestion'),transformation=p.get('transformation'),transformation_version=p.get('transformation_version'),timestamp_source=p.get('timestamp_source'),timestamp_quality=TimestampQuality(p.get('timestamp_quality','UNKNOWN')),schema_version=str(raw.get('schema_version','3.11.3.12.v1')),checksum=p.get('checksum'))
        e=CanonicalEvent(event_id=str(raw['event_id']),event_type=str(raw['event_type']),job_id=raw.get('job_id'),workload_id=raw.get('workload_id'),environment_id=raw.get('environment_id'),timestamp=raw.get('timestamp'),timestamp_precision=raw.get('timestamp_precision'),timestamp_source=raw.get('timestamp_source'),timestamp_timezone=raw.get('timestamp_timezone'),ingestion_timestamp=raw.get('ingestion_timestamp'),producer=raw.get('producer'),provenance=provenance,payload=raw.get('payload',{}),schema_version=str(raw.get('schema_version','3.11.3.12.v1')),source_dataset=raw.get('source_dataset',provenance.source),source_record_id=raw.get('source_record_id'))
        self.store.append(e); return e
    def ingest_batch(self,records): return [self.ingest(r) for r in records]

class ObservationReplay:
    def __init__(self,store): self.store=store
    def serialize(self): return json.dumps(self.store.replay(),sort_keys=True,separators=(',',':'))
    def replay(self): return self.store.replay()

class ObservabilityAPI:
    def __init__(self,store,event_states=None): self.store=store; self.states=event_states or WorkloadStateStore(); self.snapshots=DecisionSnapshotBuilder(store)
    def event_history(self,job_id,at_or_before=None): return self.store.events(job_id,at_or_before)
    def decision_snapshot(self,job_id,decision_time): return self.snapshots.build(job_id,decision_time)
    def current_workload_state(self,job_id): return self.states.state(job_id).state.value
    def provenance(self,job_id,at_or_before=None): return [e.provenance for e in self.store.events(job_id,at_or_before)]
