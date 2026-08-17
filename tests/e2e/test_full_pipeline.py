"""End-to-end: input -> reliability analysis -> confidence -> failure-memory
lookup -> decision -> persistent event, exercised through the real API app
(FastAPI TestClient), not mocked at any layer.

Also serves as the regression test for two confirmed Phase 1 bugs, fixed in
this codebase:
  - AI-Abstention-Engine: documented GET /api/metrics 404'd; here there is
    exactly one documented metrics route and it is tested directly.
  - Introspective-Failure-Memory-Model: POST /api/control 500'd on numpy
    scalar serialization; here /api/analyze's response is asserted to be
    valid, standard JSON.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.app import app


def test_health():
    with TestClient(app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_analyze_end_to_end_persists_and_returns_valid_decision():
    with TestClient(app) as client:
        resp = client.post(
            "/api/analyze",
            json={"context": {"f1": 0.5, "f2": -0.2, "f3": 0.1, "f4": 0.0, "f5": 1.0}, "true_label": 1},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["decision"] in {"ANSWER", "ABSTAIN", "REVIEW"}
        assert 0.0 <= body["confidence"] <= 1.0
        assert body["event_id"]

        # persisted -> queryable via metrics
        metrics = client.get("/api/metrics/summary").json()
        assert metrics["event_count"] >= 1


def test_metrics_summary_is_the_one_documented_route_and_no_fake_data():
    """Confirms /api/metrics (the source repo's dead/undocumented route)
    does not exist here, and that metrics before any events are honestly
    null, not a fabricated placeholder number."""
    with TestClient(app) as client:
        assert client.get("/api/metrics").status_code == 404

        resp = client.get("/api/metrics/summary", params={"workload_id": "no-such-workload"})
        body = resp.json()
        assert body["event_count"] == 0
        assert body["answer_rate"] is None
        assert body["abstain_rate"] is None
        assert body["accuracy_on_answered"] is None
