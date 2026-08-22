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
from dataclasses import asdict
import os

from fastapi import FastAPI, HTTPException

from src.schema.events import Outcome
from src.storage.db import get_session, init_db
from src.storage.repository import EventRepository

from .train import build_default_runtime

_runtime = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _runtime
    init_db()
    artifact_path = os.environ.get("RELIABILITY_ARTIFACT_PATH")
    with get_session() as session:
        repo = EventRepository(session)
        _runtime = build_default_runtime(
            artifact_path=artifact_path,
            repository=repo,
        )
    yield


app = FastAPI(title="Autonomous AI Infrastructure -- Closed-Loop Runtime", lifespan=_lifespan)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(payload: dict) -> dict:
    """Process a structured observation through the canonical runtime.

    ``context`` remains an evaluation/API compatibility alias for ``features``.
    ``true_label`` is evaluation-only and is never required for autonomous
    observation, diagnosis, recovery, validation, or learning.
    """
    if _runtime is None:
        raise HTTPException(status_code=503, detail="runtime not initialized")
    raw = dict(payload)
    true_label = raw.pop("true_label", None)
    try:
        observation = _runtime.normalizer.normalize(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with get_session() as session:
        _runtime.controller.repository = EventRepository(session)
        episode = _runtime.controller.process(observation, true_label=true_label)
    if episode.event is None:
        raise HTTPException(status_code=500, detail="runtime did not produce a compatibility event")
    response = episode.event.model_dump(mode="json")
    response["runtime"] = {
        "state": episode.state.value,
        "observation_id": observation.observation_id,
        "source": observation.source,
        "source_type": observation.source_type.value,
        "provenance": dict(observation.provenance),
        "detection": asdict(episode.detection) if episode.detection else None,
        "reliability": asdict(episode.reliability) if episode.reliability else None,
        "transitions": [t.to_state.value for t in episode.transitions],
        "retrieved_experience_count": len(episode.retrieved_experiences),
        "diagnosis": episode.diagnosis.__dict__ if episode.diagnosis else None,
        "recovery_action": episode.recovery_plan.selected_action.value if episode.recovery_plan else None,
        "validation": episode.validation.status if episode.validation else None,
        "experience_id": episode.experience_id,
        "learning_update": episode.learning_update,
    }
    return response


@app.get("/api/memory/status")
def memory_status() -> dict:
    """Observable failure-memory state -- real values read off the live
    ``FailureMemory`` instance, never fabricated. Lets a caller verify that
    a stored failure actually became usable (``fitted``/``version``) rather
    than trusting an unobservable internal flag."""
    if _runtime is None:
        raise HTTPException(status_code=503, detail="runtime not initialized")
    return _runtime.failure_memory.status()


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
