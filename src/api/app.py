"""Minimal FastAPI surface over the unified pipeline.

Fixes, in the unified codebase, two live bugs Phase 1 confirmed in the
source repos:

- Numpy-scalar JSON-serialization 500 error (Introspective-Failure-Memory-
  Model, ``POST /api/control``): every numeric value returned here passes
  through ``ReliabilityEvent`` (a pydantic model) before serialization, and
  every value written into that model is cast to a native Python
  float/int/bool in ``src/reliability`` and ``src/failure_memory`` -- there
  is no path for a numpy scalar to reach the response.
- Dead/undocumented metrics route (AI-Abstention-Engine, docs referenced a
  ``GET /api/metrics`` that returned 404): this app defines exactly one
  metrics endpoint, ``GET /api/metrics/summary``, and that is the only one
  referenced anywhere in this project's docs.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.decision.policy import DecisionMode
from src.schema.events import Outcome
from src.storage.db import get_session, init_db
from src.storage.repository import EventRepository

from .pipeline import ReliabilityPipeline
from .train import build_default_pipeline

_pipeline: ReliabilityPipeline | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _pipeline
    init_db()
    _pipeline = build_default_pipeline()
    yield


app = FastAPI(title="Autonomous AI Infrastructure -- Unified Reliability API", lifespan=_lifespan)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(payload: dict) -> dict:
    """``payload`` must contain a ``context`` dict of named numeric
    features. Optional ``true_label`` (int) is accepted only for
    demo/benchmark use to log outcome; a real deployment would not have it
    at request time."""
    assert _pipeline is not None, "pipeline not initialized"
    context = {k: float(v) for k, v in payload.get("context", {}).items()}
    true_label = payload.get("true_label")
    with get_session() as session:
        repo = EventRepository(session)
        event = _pipeline.analyze(context, repository=repo, true_label=true_label)
        return event.model_dump(mode="json")


@app.get("/api/metrics/summary")
def metrics_summary(workload_id: str | None = None) -> dict:
    """Real, computed-on-request metrics -- never a hardcoded/mocked value.
    If a metric can't be computed (e.g. no events yet), it is reported as
    ``null``, not a fabricated number (PHASE1_AUDIT_REPORT.md section 2.11)."""
    with get_session() as session:
        repo = EventRepository(session)
        events = repo.get_all(workload_id=workload_id)

    if not events:
        return {"event_count": 0, "answer_rate": None, "abstain_rate": None, "accuracy_on_answered": None}

    n = len(events)
    n_answered = sum(1 for e in events if e.decision.value == "ANSWER")
    n_abstained = sum(1 for e in events if e.abstained)
    answered_with_outcome = [e for e in events if e.decision.value == "ANSWER" and e.outcome != Outcome.UNKNOWN]
    n_correct = sum(1 for e in answered_with_outcome if e.outcome == Outcome.CORRECT)

    return {
        "event_count": n,
        "answer_rate": n_answered / n,
        "abstain_rate": n_abstained / n,
        "accuracy_on_answered": (n_correct / len(answered_with_outcome)) if answered_with_outcome else None,
    }
