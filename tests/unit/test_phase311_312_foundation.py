import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.data_foundation.foundation import (
    Availability,
    CanonicalBatchAdapter,
    CanonicalEvent,
    DecisionTimeContract,
    DecisionTimeSnapshot,
    EnvironmentIdentity,
    EnvironmentRegistry,
    Provenance,
    TimestampQuality,
    classify_availability,
    make_split_contract,
    validate_event_order,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/results/v1_1/data_foundation/3_11_3_12"


def prov():
    return Provenance(source="synthetic/test-only", source_record_id="r1", timestamp_quality=TimestampQuality.EXACT)


def test_foundation_artifacts_and_all_canonical_schemas_exist():
    assert (OUT / "protocol/phase311_312_protocol.json").exists()
    assert len(list((OUT / "schemas").glob("*.json"))) == 10
    assert (OUT / "registry/environment_registry.json").exists()
    assert (OUT / "coverage/observability_coverage.csv").exists()
    assert (OUT / "source_evaluation/source_acceptance_matrix.csv").exists()


def test_protocol_freezes_v1_and_forbids_model_experimentation():
    protocol = json.loads((OUT / "protocol/phase311_312_protocol.json").read_text())
    assert protocol["frozen_v1_commit"] == "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
    assert protocol["no_model_training"] is True
    assert protocol["no_v1_1_creation"] is True
    assert protocol["no_external_silent_merge"] is True


def test_event_schema_requires_provenance_and_rejects_unknown_event_type():
    event = CanonicalEvent(event_id="e1", event_type="prediction_generated", timestamp="2026-01-01T00:00:00Z", provenance=prov())
    assert event.to_dict()["event_type"] == "prediction_generated"
    with pytest.raises(ValueError):
        CanonicalEvent(event_id="e2", event_type="invented_event", provenance=prov())
    with pytest.raises(ValueError):
        CanonicalEvent(event_id="e3", event_type="prediction_generated", timestamp="2026-01-01T00:00:00", provenance=prov())


def test_decision_time_contract_and_snapshot_boundary():
    contract = DecisionTimeContract("2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", "2026-01-01T00:00:02Z", timestamp_quality=TimestampQuality.SYNCHRONIZED)
    assert contract.validate()
    with pytest.raises(ValueError):
        DecisionTimeContract("2026-01-01T00:00:02Z", "2026-01-01T00:00:01Z", "2026-01-01T00:00:00Z").validate()
    snap = DecisionTimeSnapshot("s1", "2026-01-01T00:00:02Z", workload_context={"class":"test"}, provenance=(prov(),), timestamp_quality=TimestampQuality.EXACT, availability=Availability.AT)
    assert snap.snapshot_id == "s1"
    with pytest.raises(ValueError):
        DecisionTimeSnapshot("s2", "2026-01-01T00:00:02Z", provenance=(prov(),), availability=Availability.AFTER)


def test_availability_and_event_order_are_explicit_and_non_reordering():
    assert classify_availability("2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z") == Availability.BEFORE
    assert classify_availability(None, "2026-01-01T00:00:01Z") == Availability.UNKNOWN
    events = [CanonicalEvent("a", "workload_received", timestamp="2026-01-01T00:00:02Z", provenance=prov()), CanonicalEvent("b", "prediction_generated", timestamp="2026-01-01T00:00:01Z", provenance=prov())]
    assert validate_event_order(events) == ["INVALID_ORDER:workload_received>prediction_generated"]


def test_registry_uniqueness_and_adapter_provenance():
    reg = EnvironmentRegistry()
    reg.register(EnvironmentIdentity("env-test", "synthetic/test-only", "unit-test"))
    with pytest.raises(ValueError):
        reg.register(EnvironmentIdentity("env-test", "synthetic/test-only", "unit-test"))
    events = CanonicalBatchAdapter("synthetic/test-only").normalize([{"event_id":"e1","event_type":"workload_received","source_record_id":"raw-1"}])
    assert events[0].provenance.source == "synthetic/test-only"
    assert events[0].source_dataset == "synthetic/test-only"


def test_split_contracts_prevent_contamination_and_are_not_executed():
    split = make_split_contract("env", ["A"], ["A"], ["B"], "ENVIRONMENT_HOLDOUT")
    assert split["status"] == "CONTRACT_ONLY_NOT_EXECUTED"
    with pytest.raises(ValueError):
        make_split_contract("bad", ["A"], [], ["A"], "ENVIRONMENT_HOLDOUT")


def test_alibaba_is_metadata_only_and_external_sources_deferred():
    source = pd.read_csv(OUT / "source_evaluation/source_acceptance_matrix.csv")
    assert "CANONICAL CONTROL / DO NOT MERGE" in set(source.decision)
    assert "DEFERRED — NOT INTEGRATED" in set(source.decision)
    collection = json.loads((OUT / "artifacts/collection_identity.json").read_text())
    assert collection["status"] == "FOUNDATION_ONLY_NOT_FINAL_BENCHMARK"


def test_quality_and_coverage_are_honest_about_missing_runtime_observability():
    quality = json.loads((OUT / "quality/timestamps/timestamp_quality.json").read_text())
    assert quality["status"] == "PARTIAL"
    cov = pd.read_csv(OUT / "coverage/observability_coverage.csv")
    assert cov.iloc[0]["decision_time_coverage"] == "INSUFFICIENT"
    assert cov.iloc[0]["scheduler_state_coverage"] == "UNAVAILABLE"


def test_hashes_are_present_after_finalization():
    assert (OUT / ".finalized").exists()
    hashes = json.loads((OUT / ".finalized").read_text())
    assert hashes
    for rel, expected in hashes.items():
        path = OUT / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
