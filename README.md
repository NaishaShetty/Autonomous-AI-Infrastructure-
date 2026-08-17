# Autonomous AI Infrastructure — Unified Reliability + Failure Memory

> **Phase 3 (3.1–3.6) is frozen.** Future phases may build upon, replace,
> or extend its components, but Phase 3 protocols, results, and
> conclusions are preserved as the historical experimental baseline —
> see [`docs/PHASE3_FREEZE.md`](docs/PHASE3_FREEZE.md).

Phase 2 deliverable. A single, tested implementation combining a calibrated
confidence signal (migrated from `AI-Abstention-Engine`) and a persistent
failure-memory risk signal (migrated from `Introspective-Failure-Memory-
Model`) behind one decision policy. See `PHASE1_AUDIT_REPORT.md` for the
source-prototype audit and `PHASE2_REPORT.md` for what changed and why,
including the integration experiment's result.

## Layout

```
src/
  schema/        canonical ReliabilityEvent (pydantic) — see docs/SCHEMA.md
  storage/       SQLAlchemy persistence + repository
  reliability/   workload model + calibrated confidence
  failure_memory/  embedding, clustering, persistent storage-backed risk/retrieval
  decision/      the one authoritative decision policy
  data/          synthetic regime-drift dataset generator
  evaluation/    Phase 3.1 metrics (AUROC/AUPRC/ECE/AURC) + bootstrap CI + frozen protocol loader
  experience/    old (frozen) Phase 4.1 -- synthetic-only retrieval-precision experience store, see docs/PHASE4_1_FAILURE_MEMORY.md
  patterns/      old (frozen) Phase 4.2 -- synthetic-only failure pattern learning, see docs/PHASE4_2_FAILURE_PATTERNS.md
  failure_experience/  active Phase 4.1 -- canonical FailureExperience schema/storage/retrieval across real+synthetic sources, see docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md
  pipeline_builder.py  trains one system (workload model + calibrator + failure memory)
  api/           FastAPI demo service, built on pipeline_builder
benchmarks/      standardized risk-coverage harness + 3-baseline experiment + Phase 3.1 evaluation/leakage-audit scripts
experiments/results/  experiment outputs (JSON + plot), reproducible via benchmarks/
tests/           unit / integration / e2e
configs/         policy thresholds (policy.json), frozen Phase 3.1 protocol (phase3_1_protocol.json)
docs/            schema + architecture notes + Phase 3.1 evaluation protocol
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# .venv/bin/pip install -r requirements.txt     # macOS/Linux
```

All dependencies are pinned to exact versions verified to install cleanly
from a fresh environment (see `requirements.txt`).

## Run the tests

```bash
python -m pytest tests/ -v
```

## Reproduce the integration experiment

```bash
python benchmarks/run_baselines.py        # Baseline A vs B vs C, risk-coverage curves
python benchmarks/diagnose_risk_signal.py  # matched-coverage comparison + signal-quality diagnostics
```

Both are deterministic given the fixed seed (`SEED = 42` in
`benchmarks/run_baselines.py`) and write their output to
`experiments/results/`.

## Reproduce the Phase 3.1 evaluation (leakage audit + multi-seed baseline reproduction)

```bash
python benchmarks/phase3_1_leakage_audit.py   # 7 leakage checks against a live-built system
python benchmarks/phase3_1_evaluate.py        # AUROC/AUPRC/ECE/AURC/precision&recall, 6 seeds + bootstrap CI
```

Protocol is frozen in `configs/phase3_1_protocol.json`; full writeup in
`docs/PHASE3_1_EVALUATION_PROTOCOL.md`. Does not modify anything under
`src/pipeline_builder.py`, `src/failure_memory/`, or `src/reliability/` —
it evaluates the existing Phase 2 components under a new, stricter protocol.

## Reproduce the Phase 3.2 representation experiments

```bash
python benchmarks/phase3_2_evaluate.py   # Candidate B (raw features) + Candidate C (failure-history), same frozen protocol
```

Full writeup: `docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md`. Does not modify the Phase 3.1 protocol or any Phase 2 component; new representations live only in `src/evaluation/representations.py`, used for evaluation only (not wired into `src/decision` or the live API).

## Run the demo API

```bash
.venv/Scripts/uvicorn src.api.app:app --port 8000
```

`POST /api/analyze` with `{"context": {"f1": 0.1, "f2": -0.3, ...}}`;
`GET /api/metrics/summary` for real, computed-on-request metrics (never
mocked — see `PHASE2_REPORT.md` section 2).

## Development database

A local SQLite file is created automatically at `data/unified_dev.db` on
first use. It starts empty; no personal data or credentials are ever
seeded into it (see `PHASE1_AUDIT_REPORT.md` section 5/11 on the source
`reliability.db` issue this project deliberately avoids repeating). It is
excluded from version control via `.gitignore`.
