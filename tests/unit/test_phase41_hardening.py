import json
from pathlib import Path
import pytest
from src.data_foundation.foundation import Availability
from src.phase4.observability import ObservationCollector, PersistentEventStore, DecisionSnapshotBuilder, ObservationReplay, ObservabilityAPI


def raw(eid, typ, ts, job='j1'):
    return {'event_id':eid,'event_type':typ,'job_id':job,'source_dataset':'controlled-runtime/synthetic-test-only','timestamp':ts,'schema_version':'3.11.3.12.v1','provenance':{'source':'controlled-runtime/synthetic-test-only','source_record_id':'raw-'+eid,'extraction_method':'controlled-runtime','transformation':'canonical-normalization','transformation_version':'v1','timestamp_source':'clock','timestamp_quality':'EXACT'},'payload':{'fixture':'SYNTHETIC / TEST ONLY'}}


def test_persistent_store_roundtrip_restart_and_raw_boundary(tmp_path):
    path=tmp_path/'events.sqlite'
    store=PersistentEventStore(path); c=ObservationCollector(store)
    c.ingest(raw('e1','workload_received','2026-01-01T00:00:00Z')); c.ingest(raw('e2','prediction_generated','2026-01-01T00:00:01Z'))
    before=ObservationReplay(store).serialize(); assert store.raw_source('e1')['provenance']['source_record_id']=='raw-e1'; store.close()
    restarted=PersistentEventStore(path); after=ObservationReplay(restarted).serialize()
    assert before==after
    snap=DecisionSnapshotBuilder(restarted).build('j1','2026-01-01T00:00:01Z'); assert snap.availability==Availability.AT
    restarted.close()


def test_persistent_store_rejects_duplicate_ids_and_malformed_provenance(tmp_path):
    store=PersistentEventStore(tmp_path/'events.sqlite'); c=ObservationCollector(store); c.ingest(raw('e1','workload_received','2026-01-01T00:00:00Z'))
    with pytest.raises(ValueError,match='duplicate'): c.ingest(raw('e1','workload_received','2026-01-01T00:00:00Z'))
    with pytest.raises(ValueError): c.ingest({**raw('e2','workload_received','2026-01-01T00:00:02Z'),'provenance':{'source':'x','timestamp_quality':'EXACT'}})
    store.close()


def test_persistent_replay_and_api_remain_temporally_bounded(tmp_path):
    store=PersistentEventStore(tmp_path/'events.sqlite'); c=ObservationCollector(store)
    c.ingest_batch([raw('e1','workload_received','2026-01-01T00:00:00Z'),raw('e2','prediction_generated','2026-01-01T00:00:01Z'),raw('e3','telemetry_observed','2026-01-01T00:00:02Z')])
    api=ObservabilityAPI(store); assert [x.event_id for x in api.event_history('j1','2026-01-01T00:00:01Z')]==['e1','e2']
    with pytest.raises(ValueError,match='post-decision'): api.decision_snapshot('j1','2026-01-01T00:00:01Z')
    store.close()
