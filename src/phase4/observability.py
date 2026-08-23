"""Phase 4.1 deterministic runtime observability implementation."""
from __future__ import annotations
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
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

class PersistentEventStore(EventStore):
    """Append-only durable store for normalized canonical events.

    Raw source identity and normalized canonical representation are stored
    separately. Existing event IDs are immutable and duplicate ingestion fails.
    SQLite is deliberately local and deterministic; no distributed layer is
    introduced for this foundation phase.
    """
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path)
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.execute('CREATE TABLE IF NOT EXISTS canonical_events (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, event_timestamp TEXT, event_json TEXT NOT NULL, raw_source_json TEXT NOT NULL, ingested_at TEXT NOT NULL)')
        self._db.commit()
        super().__init__()
        for (event_json,) in self._db.execute('SELECT event_json FROM canonical_events ORDER BY event_timestamp, event_id'):
            self._events.append(_event_from_dict(json.loads(event_json)))

    def append(self, event: CanonicalEvent, raw_source: Mapping[str, Any] | None = None):
        EventValidator().validate(event)
        if self._db.execute('SELECT 1 FROM canonical_events WHERE event_id=?', (event.event_id,)).fetchone():
            raise ValueError(f'duplicate event_id: {event.event_id}')
        payload=json.dumps(event.to_dict(), sort_keys=True, separators=(',', ':'))
        raw=json.dumps(dict(raw_source or event.to_dict()), sort_keys=True, separators=(',', ':'))
        self._db.execute('INSERT INTO canonical_events(event_id,event_type,event_timestamp,event_json,raw_source_json,ingested_at) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)', (event.event_id,event.event_type,event.timestamp,payload,raw))
        self._db.commit(); self._events.append(event)

    def close(self): self._db.close()
    def raw_source(self, event_id: str) -> Mapping[str, Any]:
        row=self._db.execute('SELECT raw_source_json FROM canonical_events WHERE event_id=?',(event_id,)).fetchone()
        if row is None: raise KeyError(event_id)
        return json.loads(row[0])


def _event_from_dict(value: Mapping[str, Any]) -> CanonicalEvent:
    p=value.get('provenance') or {}
    provenance=Provenance(source=str(p.get('source','unknown')),source_version=p.get('source_version'),source_record_id=p.get('source_record_id'),extraction_method=p.get('extraction_method'),transformation=p.get('transformation'),transformation_version=p.get('transformation_version'),timestamp_source=p.get('timestamp_source'),timestamp_quality=TimestampQuality(p.get('timestamp_quality','UNKNOWN')),schema_version=str(p.get('schema_version','3.11.3.12.v1')),ingestion_time=p.get('ingestion_time'),processing_time=p.get('processing_time'),checksum=p.get('checksum'))
    return CanonicalEvent(event_id=str(value['event_id']),event_type=str(value['event_type']),entity_id=value.get('entity_id'),workload_id=value.get('workload_id'),job_id=value.get('job_id'),task_id=value.get('task_id'),environment_id=value.get('environment_id'),cluster_id=value.get('cluster_id'),node_id=value.get('node_id'),resource_id=value.get('resource_id'),timestamp=value.get('timestamp'),timestamp_precision=value.get('timestamp_precision'),timestamp_source=value.get('timestamp_source'),timestamp_timezone=value.get('timestamp_timezone'),ingestion_timestamp=value.get('ingestion_timestamp'),producer=value.get('producer'),provenance=provenance,payload=value.get('payload',{}),schema_version=str(value.get('schema_version','3.11.3.12.v1')),event_version=str(value.get('event_version','1')),parent_event_id=value.get('parent_event_id'),correlation_id=value.get('correlation_id'),source_dataset=value.get('source_dataset'),source_record_id=value.get('source_record_id'))


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
        p=raw.get('provenance') or {}
        mandatory=('source','source_record_id','timestamp_quality')
        if any(not p.get(k) for k in mandatory): raise ValueError('provenance violation')
        provenance=Provenance(source=str(p['source']),source_version=p.get('source_version'),source_record_id=str(p['source_record_id']),extraction_method=str(p.get('extraction_method','runtime_ingestion')),transformation=p.get('transformation'),transformation_version=p.get('transformation_version'),timestamp_source=p.get('timestamp_source'),timestamp_quality=TimestampQuality(p['timestamp_quality']),schema_version=str(raw.get('schema_version','3.11.3.12.v1')),checksum=p.get('checksum'))
        e=CanonicalEvent(event_id=str(raw['event_id']),event_type=str(raw['event_type']),job_id=raw.get('job_id'),workload_id=raw.get('workload_id'),environment_id=raw.get('environment_id'),timestamp=raw.get('timestamp'),timestamp_precision=raw.get('timestamp_precision'),timestamp_source=raw.get('timestamp_source'),timestamp_timezone=raw.get('timestamp_timezone'),ingestion_timestamp=raw.get('ingestion_timestamp'),producer=raw.get('producer'),provenance=provenance,payload=raw.get('payload',{}),schema_version=str(raw.get('schema_version','3.11.3.12.v1')),source_dataset=raw.get('source_dataset',provenance.source),source_record_id=raw.get('source_record_id'))
        if isinstance(self.store, PersistentEventStore): self.store.append(e, raw_source=raw)
        else: self.store.append(e)
        return e
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
