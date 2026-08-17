# Project History — Consolidated Documentation

> **This file replaces the individual documents previously under `docs/` and the root-level `PHASE1_AUDIT_REPORT.md` / `PHASE2_REPORT.md`.** It was assembled by concatenating each original document's content verbatim (no wording changed, no numbers altered, no verdicts reworded) behind a status banner, so the full research record remains intact in one place instead of scattered across ~30 files. See `README.md` for the current project layout and setup instructions.

## How to read this document

Three status labels appear on every section:

- **FROZEN HISTORICAL** — a completed, sealed research artifact. Its content is reproduced exactly as originally written; nothing below is edited, corrected, or reinterpreted to match later findings, per this project's own research-integrity rule (see the Phase 3 Freeze and Phase 3.6 Real-Data Decision sections).
- **ACTIVE / CURRENT** — the current, in-force implementation and its documentation.
- **PLANNING (not yet implemented)** — a research plan that has NOT been implemented yet.

### Project timeline (how the phases relate)

```
Phase 1 (prototype audit) -> Phase 2 (migration/integration)
  -> Phase 3.1-3.6 (synthetic data) -> FROZEN (Phase 3 Freeze)
  -> OLD Phase 4.0/4.1/4.2 (synthetic data) -> FROZEN
       (Phase 4.1: H1 PARTIALLY SUPPORTED: Phase 4.2: H2 INCONCLUSIVE)
  -> Real-data expansion (AgentRx, AIOps 2020, Alibaba GPU 2020)
  -> Revised real-data Phase 3.1-3.6 -> FROZEN (Real-Data 3.6 Decision)
  -> [deliberate pause to reassess Phase 4 against the new evidence]
  -> ACTIVE Phase 4.1 (src/failure_experience/) -> PASS
  -> ACTIVE Phase 4.2 plan -> awaiting implementation approval
```

The OLD Phase 4.1/4.2 verdicts are never rewritten by the ACTIVE Phase 4.1/4.2 work — they are independent findings on independent (synthetic-only) data, kept exactly as originally recorded, immediately below in this same document.

## Table of contents

- [PHASE1 AUDIT REPORT](#phase1-audit-report) — *FROZEN HISTORICAL* — Audit of the two source prototypes (AI-Abstention-Engine, Introspective-Failure-Memory-Model) before any migration.
- [PHASE2 REPORT](#phase2-report) — *FROZEN HISTORICAL* — Migration/integration of the two prototypes into one unified system; Phase 2 deliverable.
- [SCHEMA](#schema) — *FROZEN HISTORICAL* — The canonical ReliabilityEvent schema reference (still in active use, unmodified since Phase 1/2).
- [PHASE3 1 EVALUATION PROTOCOL](#phase3-1-evaluation-protocol) — *FROZEN HISTORICAL* — Phase 3.1 frozen evaluation protocol (synthetic data).
- [PHASE3 2 REPRESENTATION EXPERIMENTS](#phase3-2-representation-experiments) — *FROZEN HISTORICAL* — Phase 3.2 representation experiments (synthetic data).
- [PHASE3 2C CANDIDATE ABLATION](#phase3-2c-candidate-ablation) — *FROZEN HISTORICAL* — Phase 3.2C candidate representation ablation (synthetic data).
- [PHASE3 3 GENERALIZATION](#phase3-3-generalization) — *FROZEN HISTORICAL* — Phase 3.3 generalization evaluation (synthetic data).
- [PHASE3 4 COMPARISON](#phase3-4-comparison) — *FROZEN HISTORICAL* — Phase 3.4 comparison of representations/signals (synthetic data).
- [PHASE3 5 ATTACK GENERALIZATION](#phase3-5-attack-generalization) — *FROZEN HISTORICAL* — Phase 3.5 attack-generalization evaluation (synthetic data).
- [PHASE3 6 DIAGNOSIS ABSTENTION RECOVERY](#phase3-6-diagnosis-abstention-recovery) — *FROZEN HISTORICAL* — Phase 3.6 diagnosis/abstention/recovery study (synthetic data).
- [PHASE3 FREEZE](#phase3-freeze) — *FROZEN HISTORICAL* — Formal freeze declaration sealing Phase 3.1-3.6 (synthetic-data track) as historical baseline.
- [PHASE4 0 EPISODIC DATA](#phase4-0-episodic-data) — *FROZEN HISTORICAL* — Old Phase 4.0: synthetic episodic incident-stream generator.
- [PHASE4 1 FAILURE MEMORY](#phase4-1-failure-memory) — *FROZEN HISTORICAL* — OLD Phase 4.1: synthetic-only failure memory / experience retrieval (H1 PARTIALLY SUPPORTED). Superseded in role, not in content, by the ACTIVE Phase 4.1 later in this document -- see the Active Phase 4 Reassessment section for the relationship.
- [PHASE4 2 FAILURE PATTERNS](#phase4-2-failure-patterns) — *FROZEN HISTORICAL* — OLD Phase 4.2: synthetic-only failure pattern learning (H2 INCONCLUSIVE). This verdict is NOT changed anywhere in this document.
- [PHASE3 REAL DATA FEASIBILITY AUDIT](#phase3-real-data-feasibility-audit) — *FROZEN HISTORICAL* — Feasibility audit for expanding into real datasets (AgentRx, AIOps 2020, Alibaba GPU 2020).
- [PHASE3 REAL DATA ALIBABA SENSOR LEAKAGE GATE](#phase3-real-data-alibaba-sensor-leakage-gate) — *FROZEN HISTORICAL* — Leakage gate specifically for Alibaba sensor-derived features.
- [PHASE3 REAL DATA CLEANING REPORT](#phase3-real-data-cleaning-report) — *FROZEN HISTORICAL* — Real-data cleaning report (Alibaba/AIOps/AgentRx).
- [PHASE3 REAL DATA AIOPS PROTOCOL](#phase3-real-data-aiops-protocol) — *FROZEN HISTORICAL* — AIOps 2020 real-data extraction/evaluation protocol.
- [PHASE3 REAL DATA AIOPS NEGATIVE WINDOW PROTOCOL](#phase3-real-data-aiops-negative-window-protocol) — *FROZEN HISTORICAL* — AIOps negative-window (non-fault) sampling protocol.
- [PHASE3 REAL DATA AIOPS PREPARATION COMPLETE](#phase3-real-data-aiops-preparation-complete) — *FROZEN HISTORICAL* — AIOps real-data preparation completion record.
- [PHASE3 REAL DATA PROTOCOL](#phase3-real-data-protocol) — *FROZEN HISTORICAL* — The overall frozen real-data Phase 3 protocol (all three datasets).
- [PHASE3 REAL DATA 3 1 REPORT](#phase3-real-data-3-1-report) — *FROZEN HISTORICAL* — Real-data Phase 3.1 (detection) report.
- [PHASE3 REAL DATA 3 2 REPORT](#phase3-real-data-3-2-report) — *FROZEN HISTORICAL* — Real-data Phase 3.2 (representation) report.
- [PHASE3 REAL DATA 3 3 REPORT](#phase3-real-data-3-3-report) — *FROZEN HISTORICAL* — Real-data Phase 3.3 (generalization/distribution-shift) report.
- [PHASE3 REAL DATA 3 4 REPORT](#phase3-real-data-3-4-report) — *FROZEN HISTORICAL* — Real-data Phase 3.4 (comparison) report.
- [PHASE3 REAL DATA 3 5 REPORT](#phase3-real-data-3-5-report) — *FROZEN HISTORICAL* — Real-data Phase 3.5 (attack/generalization) report.
- [PHASE3 REAL DATA 3 6 DECISION](#phase3-real-data-3-6-decision) — *FROZEN HISTORICAL* — Real-data Phase 3.6 final decision synthesis -- the document that triggered the Phase 4 pause/reassessment.
- [PHASE3 REAL DATA COMPARISON](#phase3-real-data-comparison) — *FROZEN HISTORICAL* — Cross-dataset real-data comparison summary.
- [PHASE4 PLAN](#phase4-plan) — *ACTIVE (amended)* — The Phase 4 master plan. Sections 0-10 are the original frozen plan; Section 11 is an additive amendment covering the real-data-driven Phase 4 reboot. Nothing in sections 0-10 was rewritten.
- [PHASE4 1 ACTIVE FAILURE EXPERIENCE](#phase4-1-active-failure-experience) — *ACTIVE / CURRENT* — ACTIVE Phase 4.1: the current FailureExperience representation/memory substrate, built on real + synthetic data. Status: PASS.
- [PHASE4 2 ACTIVE PLAN](#phase4-2-active-plan) — *PLANNING (not yet implemented)* — ACTIVE Phase 4.2 plan: reassessment and research plan for failure pattern learning on the post-real-data foundation. Planning only -- awaiting approval, not yet implemented.


---

<a id="phase1-audit-report"></a>
# PHASE1 AUDIT REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `PHASE1_AUDIT_REPORT.md`  
**Role:** Audit of the two source prototypes (AI-Abstention-Engine, Introspective-Failure-Memory-Model) before any migration.

# Phase 1 — Audit & Baseline of Existing AI/ML Prototypes

**Scope:** `NaishaShetty/AI-Abstention-Engine` and `NaishaShetty/Introspective-Failure-Memory-Model`, both cloned fresh into `C:\Autonomous AI infrastructure\` and audited in their original, unmodified state (any environment fix used to get something running is called out explicitly as a *temporary reproduction fix*, never applied to the repos).

**Method:** Two independent audits were run in parallel — full repo inventory, architecture tracing via file:line references, docs-vs-code discrepancy checks, live installation + test/experiment execution, code-quality review, and a per-component reuse classification. Nothing below is asserted without a corresponding read file or executed command.

---

## 1. Executive Summary

Both repositories are **working, non-trivial prototypes**, not empty scaffolding — but both also **oversell themselves relative to what the code does**, in different ways.

**AI Abstention Engine** is a full-stack FastAPI + React service (~9,700 backend LOC) with one genuine ML component (an XGBoost + DeBERTa + isotonic-regression calibrator) wrapped in a much larger orchestrator that mostly overrides the calibrator's output with hardcoded per-query-class threshold rules. It runs, and 15/15 tests pass, but only after fixing an undeclared dependency (`python-jose`) not listed in `requirements.txt`. Live testing surfaced a real, reproducible bug: the system's own "global reliability score" computes to **189.61 on a documented 0–100 scale**, caused by two different confidence scales (0–1 vs 0–100) being averaged together. A trivial factual query ("What is the capital of France?") **abstains by default** because live provider calls are disabled unless API keys are configured — and the response simultaneously reports `trust_score: 0.0` and an explanation string saying "Confidence 61%" for the same request. Two orphaned files (`experiments/simulate_failures.py`, `app/core/model.py`) target an endpoint (`/api/predict`) and a model class that have zero live callers — leftovers from an earlier prototype. A `README`-documented `GET /api/metrics` endpoint returns 404; the real routes are named differently. A committed `reliability.db` contains the repo owner's real email addresses and password hashes — leftover personal dev state checked into git, not curated demo data.

**Introspective Failure Memory Model** is a smaller, more focused prototype (~1,560 backend LOC) built entirely on scikit-learn (PCA + KMeans + LogisticRegression) — no deep learning despite the "embedding" and "anticipatory" terminology in its docs. Its one clean, independently-reproducible result is real: a risk-coverage curve showing abstention reduces error from a baseline of 35.44% to ~7–8% at 15–20% coverage, reproduced exactly from a clean environment. But the live FastAPI dashboard's risk-coverage chart and "specialist gain" endpoint are **hardcoded/mocked**, not computed from that real experiment (`# Mocked for UI` in the source), and the repo's own experiments show that its headline "continuous improvement via cluster specialists" idea **makes predictions worse**, directly contradicting a claim in its own core-concepts doc. A live, reproducible 500 error exists in the step/streaming endpoint due to unserialized numpy types. There are **no tests, no CI, and no persistence layer** (all failure history is in-memory and lost on restart) in this repo.

**Both repos share the same infrastructure gaps**: no CI/CD, no Docker, no dependency pinning, no linting, and (for the Abstention Engine) thin test coverage that validates isolated scoring functions rather than full-pipeline default behavior. Neither is production-ready, but both contain real, reusable ideas — an ML confidence calibrator in one, a validated abstention/coverage curve and a lightweight failure-clustering scheme in the other — that are legitimate seeds for the target Autonomous AI Infrastructure, provided the hardcoded/mocked parts are replaced with real computation and the two abstention/decision logics (there are effectively three across both repos) are unified into one.

---

## 2. AI Abstention Engine Audit

### Repository structure
36 backend `.py` files (~9,684 LOC), largest: `app/core/reliability/engine.py` (2,695 lines, the orchestrator), `app/api/routes.py` (1,799 lines). 4 experiment scripts, 3 test files (181 LOC), React/Vite frontend (~3,928 LOC, prebuilt `dist/` present), `docs/platform_guide.md`, two paper drafts, an `ops/observability/` folder of Prometheus/Grafana/OTel *config files*. No CI, no Docker, only a `render.yaml` deploy target, no linting config.

### Architecture (traced end-to-end)
`POST /api/analyze` → `ReliabilityEngine.analyze_query` (`engine.py:1556-2130`):
1. **Query classification** — pure keyword/regex heuristics (`_classify_query`, `engine.py:503`) sort the query into types (`simple_math`, `medical`, `legal`, `high_risk`, etc.).
2. **Arithmetic fast path** — a restricted AST evaluator short-circuits math queries directly to an answer.
3. **Retrieval** — a *real* DuckDuckGo HTML scrape (`rag_retrieval.py:175-195`), regex-parsed, fragile to markup changes; vector-DB clients (Chroma/Qdrant/Weaviate/Pinecone) are imported but never actually called.
4. **Provider routing** — picks from a hardcoded catalog of 9 providers with hand-set strength/safety/cost numbers (`providers.py:23-33`); if `ENABLE_LIVE_PROVIDER_CALLS` is unset (the default), it fabricates a canned offline string instead of calling a real LLM.
5. **"Self-consistency"** — calls the (offline, canned) provider function 3× and cosine-compares the results; in default offline mode all 3 calls return identical text, so this signal is a near-constant ~100% regardless of query difficulty.
6. **10 "abstention strategies"** (`strategies.py`) — all hand-tuned linear re-weightings of the same handful of upstream heuristic scores, not independently trained methods.
7. **Decision** — `services/reliability_engine.py:decide` applies a rule table keyed by query class with hardcoded confidence floors/ceilings (e.g., medical/legal/financial floor at `abstain_floor=48`; simple_math floors at 99% confidence) that **override** the one real ML signal for most classes.

### The abstention mechanism, precisely
- **Uncertainty/confidence** is genuinely ML-derived in exactly one place: `ReliabilityCalibrator` (`calibration.py:142-508`) — 18 structured features + a DeBERTa-v3-small mean-pooled embedding → XGBoost (240 trees) → isotonic regression calibration. No pretrained artifact is committed; on first use it **synchronously self-trains** in-request on ~820 synthetic, template-generated examples (confirmed live: first non-arithmetic request took long enough to download DeBERTa from Hugging Face and fit XGBoost).
- **Abstention itself is rule-based, not learned or conformal.** Two abstention implementations coexist: `app/core/abstention.py:abstain_decision`, explicitly self-documented as a legacy compatibility shim with **zero live callers** outside its own test; and the real live path, `services/reliability_engine.py:decide`, a nested if/elif tree over hardcoded per-class thresholds.
- **Calibration exists but is undermined**: isotonic regression calibrates the XGBoost probability, but the orchestrator then clamps that calibrated probability into hardcoded per-class floor/ceiling bands anyway (`services/reliability_engine.py:214-223`), so the "calibrated" number is frequently overridden by policy regardless of what the model actually learned.
- **After abstention**: the system returns an `ABSTAIN`/`ESCALATE`/`REQUEST_MORE_EVIDENCE`/`REVIEW`/`ANSWER` label plus an explanation string; there is no downstream retry/escalation orchestration in this repo (that's presumably meant for a later phase).
- Net effect: **hybrid but policy-dominant** — one real learned+calibrated signal, wrapped in a much larger hardcoded rule engine that frequently overrides it.

### Evaluation
No proper accuracy/coverage/selective-risk benchmark exists against ground truth in this repo — `reports/public_benchmark_report.md` presents fixed numbers as if independently validated, but they are a stale snapshot of one prior run against the committed `reliability.db`, not reproducible from a fresh clone. Live recomputation of `GET /api/metrics/summary` against the same DB returned `global_reliability_score: 189.61`, exceeding the documented 0–100 scale — a confirmed bug (root cause: `trust_score` is written on two incompatible scales — 100.0 for the arithmetic fast path vs. a 0–1 clamp elsewhere — and both are averaged together in `summarize()`). No proper selective-accuracy/risk-coverage curve is computed anywhere in this repo (unlike the Failure Memory repo, which does have one).

---

## 3. Introspective Failure Memory Model Audit

### Repository structure
11 root-level `.py` files (~1,559 LOC), a Vite+TS frontend (`frontend-v2`, ~1,412 LOC), `IFM_CORE_CONCEPTS.md` + `README.md` (~160 lines), unpinned `requirements.txt` (8 deps: scikit-learn, matplotlib, numpy, fastapi, uvicorn, websockets, pandas, python-multipart — no torch, no FAISS, no sentence-transformers). **No tests, no CI, no Docker, no lint config** — confirmed absent by exhaustive search, not inferred.

### Architecture — the actual failure → representation → storage → retrieval → analysis → output pipeline
- **Representation** (`failure_embedding.py:4-27`): a 2-component `sklearn.PCA` fit on 5-dim synthetic features, plus two deterministic scalars derived from the model's own predicted probability (`confidence = 2*|p-0.5|`, `margin = |p-0.5|`) → a 4-vector embedding. Not a semantic/learned embedding despite the name — linear PCA on synthetic features.
- **Storage** (`failure_memory.py:5-21`): purely in-memory `defaultdict`/`deque`, no DB, no file persistence — restart loses all history.
- **Retrieval** (`failure_memory.py`, `anticipatory_confidence.py:102-103`): offline batch `KMeans(n_clusters=3)`, and at inference a Gaussian-kernel similarity to the (fixed, small) set of 3 cluster centroids — brute-force, trivially cheap only because there are 3 clusters; no incremental re-clustering.
- **Diagnosis attempt**: `evaluate_cluster_specialists.py` / `failure_memory_system_comparison.py` train per-cluster `LogisticRegression` "specialist" correctors. Both experiments **confirm specialists make predictions worse** than plain abstention (see reproduction table) — a genuine, reproduced negative result, honestly reported in the README's own "Negative Result" section.
- **"Anticipatory confidence"** (`anticipatory_confidence.py`): a **fixed-coefficient heuristic**, not a trained predictive model — `risk = Σ_clusters similarity(embedding, centroid) × min(recent_activity/cap, 1.0)`, then `confidence_adjusted = confidence × (1 − 0.4 × risk)`. All constants (β=0.4, σ=1.0, activity cap=10) are hand-picked, untuned, and duplicated (not centralized) across 5+ files.
- **Models used**: LogisticRegression (primary + specialists), KMeans (clustering), PCA (embedding) — all scikit-learn, no deep learning, consistent with `requirements.txt`.
- **`api.py`** (298 lines, FastAPI): traced live. `GET /api/risk-coverage` **returns a hardcoded closed-form curve**, explicitly commented `"we'll provide a static representative curve"` — not derived from the real `risk_coverage_curve.py` computation. `GET /api/specialists` returns a hardcoded `"gain_estimate": "12.4%"` string, commented `# Mocked for UI`, directly contradicting the repo's own measured result that specialists *hurt* accuracy. `POST /api/upload` accepts a CSV but ignores it (comment: "simulate acknowledgment"). A live, reproducible **HTTP 500** occurs on `POST /api/control {"step": true}` due to numpy scalar types leaking into FastAPI's JSON encoder — this would break the WebSocket stream (`/ws/stream`), which calls the same code path every 0.2s.

### Evaluation — reproduced
The risk-coverage curve **was independently reproduced exactly**, matching the README's published table (baseline error 35.44%; 15% coverage → 8.05% error; 20% coverage → 7.14% error). This is the one fully-substantiated, real result in either repository. The specialist-correction negative result was also independently reproduced (naive correction error 32.00%, cluster-specialist correction 30.54%/41.32% depending on script, vs. abstention's 3.64% at 13% coverage — abstention is unambiguously the better strategy in this codebase's own numbers).

---

## 4. Reproduction Results

| # | Experiment | Repo | Environment | Original Reported | Reproduced | Runtime | Status | Problems |
|---|---|---|---|---|---|---|---|---|
| 1 | `pytest tests/` | Abstention Engine | Python 3.11, fresh venv | N/A (no reported baseline) | **15/15 passed** | 188.9s (dominated by cold-start calibrator training) | Reproduced, with caveat | Required installing `python-jose` manually — **not listed in `requirements.txt`**, a genuine reproduction blocker for anyone following the README verbatim. `bcrypt`/`cryptography`/`matplotlib` also imported but absent from requirements (silently satisfied here via transitive deps). |
| 2 | `POST /api/analyze` (arithmetic) | Abstention Engine | live uvicorn instance | N/A | `42`, confidence 99.9, `ANSWER` | instant | Reproduced | None |
| 3 | `POST /api/analyze` (basic factual, no API keys) | Abstention Engine | live uvicorn instance | N/A | `ABSTAIN` on "capital of France?", `trust_score: 0.0` vs. explanation text "Confidence 61%" | seconds | Reproduced (bug confirmed) | Internally inconsistent confidence reporting; abstains on trivial factual query by default |
| 4 | `GET /api/metrics/summary` | Abstention Engine | live, against committed `reliability.db` | `reports/public_benchmark_report.md`: "78.57" | **189.61** | instant | **Failed to reproduce reported number; confirmed scale bug** | 0–1 vs 0–100 trust-score scales averaged together |
| 5 | `GET /api/metrics` | Abstention Engine | live | Documented as the Prometheus-style endpoint | **404** | instant | Failed | Endpoint does not exist; real routes are `/api/metrics/summary`, `/api/metrics/dashboard`, `/api/metrics/stream` |
| 6 | `experiments/simulate_failures.py` | Abstention Engine | inspected, not run against live app | N/A | Targets `/api/predict`, which doesn't exist | n/a | Failed (orphaned) | Confirmed zero callers of `SimpleClassifier` anywhere in `app/`; leftover from an earlier prototype |
| 7 | `python synthetic_failure_dataset.py` | Failure Memory | Python 3.11, fresh venv | N/A | 50,000 samples generated, 5 regimes | 0.47s | Reproduced | None |
| 8 | `python train_base_and_log_failures.py` | Failure Memory | same venv | N/A | Base accuracy 64.3%, 188 confident failures logged | 3.0s | Reproduced | None |
| 9 | `python failure_memory_system_comparison.py` | Failure Memory | same venv | README: correction underperforms abstention | naive=0.3200, cluster-correction=0.3054, **abstention=0.0364** @13.08% coverage, baseline=0.3544 | 8.95s | **Reproduced** | None |
| 10 | `python evaluate_cluster_specialists.py` | Failure Memory | same venv | README: negative result | Combined error 0.4132, **worse than baseline** 0.3544 | 21.3s (unvectorized, slow) | **Reproduced** | Inefficient nested-loop recomputation of embeddings |
| 11 | `python risk_coverage_curve.py` | Failure Memory | same venv | README table (baseline 35.44%, 15%→8.05%, 20%→7.14%) | **Exact match** | 6.45s | **Reproduced exactly** | None |
| 12 | `python anticipatory_confidence.py` | Failure Memory | same venv | N/A (no aggregate metric claimed in-script) | Per-sample trace only, no validated predictive-accuracy metric | 5.9s | Ran, but no evaluable claim to reproduce | Script itself computes no aggregate accuracy for "predicting failure before it happens" |
| 13 | pytest / any test suite | Failure Memory | — | N/A | **No test files exist anywhere in the repo** | n/a | **Not applicable — confirmed gap** | No tests to run |
| 14 | `POST /api/control {"step": true}` | Failure Memory | live uvicorn instance | N/A | **HTTP 500** | — | Failed (bug confirmed) | numpy scalar type not JSON-serializable; affects the WebSocket stream too |
| 15 | `GET /api/risk-coverage` | Failure Memory | live uvicorn instance | Implied to reflect item 11's curve | Hardcoded static formula, not derived from live/real computation | instant | **Reproduces a number, but not the claimed computation** | Source code comment confirms this is intentional ("static representative curve") |

**No results were fabricated.** Where a script could not be run (e.g., `experiments/plot_risk.py` in the Abstention Engine, blocked on an undeclared `matplotlib` dependency that happened to be present transitively but is not guaranteed) or where a claim had no corresponding computation to reproduce, that is stated explicitly above rather than guessed.

---

## 5. Engineering Quality Assessment

Common to both repos:
- **Zero dependency pinning** — every `requirements.txt` entry is a bare package name. Already caused observed drift (torch 2.13 / transformers 5.15 resolved fresh, versions that likely didn't exist when the code was written).
- **No CI/CD, no linting/formatting config, no coverage tooling** in either repo.
- **Magic numbers / hand-tuned constants** scattered and duplicated across files rather than centralized as config — abstention thresholds in both repos, anticipatory-confidence coefficients in Failure Memory, per-query-class floors/ceilings and strategy weights in Abstention Engine — with no ablation or calibration study backing the specific values.
- **Mocked/hardcoded values presented as live data** in both frontends/APIs — Failure Memory's `/api/risk-coverage` and `/api/specialists`, and (less severely) Abstention Engine's stale benchmark report.

Abstention Engine specific:
- Confirmed missing dependencies (`python-jose`, `bcrypt`, `cryptography`, `matplotlib` not declared).
- Confirmed live bug: trust-score scale inconsistency (0–1 vs 0–100) corrupting the aggregate reliability score.
- Orphaned code: `app/core/model.py` (`SimpleClassifier`), `experiments/simulate_failures.py`, `experiments/train_model.py` — zero live callers, targets a nonexistent endpoint.
- `render.yaml` declares `DATABASE_URL=sqlite:///./abstention.db` while the actual codebase default and committed file are `reliability.db` — a deployed instance would silently start from a fresh, empty, ephemeral DB, diverging from local dev.
- Hardcoded dev secrets (`JWT_SECRET` default, Fernet key derived from it) — fine for local dev, a real risk if deployed without overriding env vars.
- `reliability.db`, containing real personal email addresses and password hashes, is committed to git and has grown across multiple commits — this is leftover personal state, not sanitized demo data, and should not ship in any migrated repo.
- Test coverage is real (15/15 passing) but shallow relative to default runtime behavior — unit tests construct favorable synthetic inputs for the scoring functions and don't exercise the actual default (no-API-key) end-to-end behavior that produced the "ABSTAIN on trivial factual query" and confidence-inconsistency bugs found in live testing.
- CORS wide open (`allow_origins=["*"]`, `allow_credentials=True`) — acceptable for local demo, a concern if deployed as-is.

Failure Memory specific:
- **No tests at all** — the most significant gap in this repo relative to the Abstention Engine.
- In-memory-only storage — cannot survive a restart, cannot run multiple workers/replicas — architecturally incompatible with any real production "self-healing" use unless replaced.
- Live, reproducible 500 error in the step/stream endpoint (numpy JSON serialization) — would break continuous operation, not just a one-off demo query.
- Unvectorized embedding computation causes redundant recomputation and the slowest script in either repo (21s vs. 6-9s for structurally similar scripts) — a scalability red flag if the dataset ever grows beyond synthetic toy size.
- `api.py:207` hardcodes `dataset_size: 10000` in one endpoint while `initialize_system()` actually uses 3,000 samples — an internal inconsistency independent of the more serious mocked-data issues above.

Overall assessment: both are **credible research prototypes with at least one real, load-bearing piece of engineering** (Abstention Engine's calibrator; Failure Memory's risk-coverage result), but neither is close to production-grade — normal and expected for a Phase 1 baseline, not a surprise finding.

---

## 6. Infrastructure Assessment

| | AI Abstention Engine | Introspective Failure Memory Model |
|---|---|---|
| README | Present, but contains claims that don't match code (see §2/§3 discrepancy tables) | Present, mostly accurate; one internal contradiction with its own core-concepts doc |
| Architecture docs | `docs/platform_guide.md`, `paper/*.md` — useful but mix implemented and aspirational content without clearly separating them | `IFM_CORE_CONCEPTS.md` — shorter, but contains the specialist-improvement claim contradicted by the repo's own experiments |
| Setup instructions | `requirements.txt` (incomplete — see §5), `setup_frontend.bat` | `requirements.txt` (complete and installs cleanly), `install_dependencies.bat`, `start_app.bat` |
| API docs | None beyond code | None beyond code |
| Unit/integration tests | 3 files, 15 tests, real coverage of scoring/classification logic, thin coverage of full-pipeline default behavior | **None** |
| Test coverage tooling | None | None |
| Docker | **None** | **None** |
| docker-compose | **None** | **None** |
| Deployment config | `render.yaml` (Render.com, has a DB-path bug, no persistent disk declared) | None (implied Render deployment via code comments, unverified externally, no config file present) |
| CI (GitHub Actions etc.) | **None** | **None** |
| Linting/formatting | **None** | **None** for Python; TS has compiler config only, no ESLint/Prettier |
| Observability | Config files only (`ops/observability/`: Prometheus scrape config, Grafana JSON, OTel YAML) — not wired to any real exporter in the running app | None |

Both repos are at the same infrastructure maturity level: **functional application code, essentially zero delivery/operations tooling.** This is expected for research prototypes and is a primary gap the unified system must close.

---

## 7. Reusability Matrix

| Component | Repository | Decision | Reason | Future Role |
|---|---|---|---|---|
| `ReliabilityCalibrator` (XGBoost+DeBERTa+isotonic) | Abstention Engine | **Reuse** (with caveats) | Only genuinely learned, calibrated signal in either repo; sound train/val/calibrate structure and graceful degrade path | Core uncertainty-estimation component for the new system's abstention module, once trained on real labeled outcomes and shipped with a committed artifact |
| `ReliabilityEngine` orchestrator (`engine.py`) + `strategies.py` | Abstention Engine | **Refactor** | Sound pipeline shape (classify→retrieve→route→score→decide→persist), but 10 "strategies" are cosmetic re-weightings and hardcoded floors override the learned signal | Becomes the shape of the new system's decision orchestrator, but strategy count/complexity should shrink and stop overriding the calibrator |
| `app/core/abstention.py` legacy shim | Abstention Engine | **Discard** | Explicitly self-described dead compatibility layer, zero live callers outside its own test | None — remove to avoid ambiguity about which abstention logic is authoritative |
| `app/db/` models/session | Abstention Engine | **Reuse** | Reasonable SQLAlchemy schema for an event-log system | Basis for the new system's failure/decision event store, migrate off SQLite |
| `providers.py` (routing + live/offline LLM calls) | Abstention Engine | **Refactor** | Useful abstraction (multi-provider catalog), but hardcoded scoring constants and silent offline-canned-text fallback need real config and clearer failure signaling | Provider abstraction layer for whichever LLM(s) the unified system calls |
| `rag_retrieval.py` (DuckDuckGo scrape) | Abstention Engine | **Replace** | Fragile, ToS-risky, single point of failure; vector-DB integration is imported but unused | Replace with a real, licensed retrieval/vector-DB integration if retrieval-grounding is needed downstream |
| `experiments/simulate_failures.py`, `experiments/train_model.py`, `app/core/model.py` | Abstention Engine | **Discard** | Confirmed orphaned — zero callers, target a nonexistent endpoint | None |
| `reliability.db` (committed) | Abstention Engine | **Discard** | Contains real personal credentials/dev state, not curated data | Must not migrate; replace with sanitized fixtures if seed data is needed |
| Frontend (`frontend/`) | Abstention Engine | **Reuse** | Modern React/Vite stack, well-pinned deps, genuinely wired to real backend endpoints | UI shell for the unified dashboard, pending backend contract changes |
| `failure_embedding.py` (PCA + confidence embedding) | Failure Memory | **Refactor** | Sound minimal concept, but PCA-only and single-sample-only API won't generalize or scale | Generalize to a pluggable/batchable embedding interface |
| `failure_memory.py` (in-memory KMeans store) | Failure Memory | **Refactor** | Reasonable clustering/temporal-activity concept, but no persistence, no re-fitting | Reimplement with a real persistence layer (DB) as the new system's failure store |
| `anticipatory_confidence.py` | Failure Memory | **Refactor/Replace** | Most novel idea in either repo (temporal risk discounting), but implemented as an untrained, hand-tuned heuristic with no validation metric | Worth keeping conceptually; needs a proper trained/validated risk-forecasting model before being trusted operationally |
| `risk_coverage_curve.py` / `plot_risk_coverage_curve.py` / `synthetic_failure_dataset.py` / `train_base_and_log_failures.py` | Failure Memory | **Reuse** | Ran cleanly, cross-validated, exactly matches published numbers | Keep as the synthetic-benchmark harness pattern for evaluating the unified abstention module, extend to non-synthetic data later |
| `evaluate_cluster_specialists.py` / `failure_memory_system_comparison.py` | Failure Memory | **Reuse (as evidence), Refactor (perf)** | Correctly and reproducibly show specialist-correction underperforms abstention — valuable negative result | Keep as a regression-style benchmark that any future "correction" idea must beat |
| `api.py` (FastAPI) | Failure Memory | **Refactor** | Structurally fine, but a live 500 bug and two hardcoded/mocked endpoints misrepresent themselves as computed | Fix numpy serialization bug and rewire mocked endpoints to real computation before reuse |
| `frontend-v2` | Failure Memory | **Reuse (UI shell), Discard (fake data wiring)** | Reasonable dashboard shell, but hardcodes fallback formulas and static stat tiles independent of backend | Rewire to real backend output once `api.py` stops returning synthetic formulas |
| Docs (`docs/platform_guide.md`, `paper/*`, `reports/public_benchmark_report.md`, `IFM_CORE_CONCEPTS.md`, both READMEs) | Both | **Refactor** | Useful design-intent material, but contain unreproducible numbers, dead endpoint references, and at least one internal self-contradiction | Regenerate from live, reproducible runs; clearly separate "implemented" vs "aspirational" |

---

## 8. Integration Analysis

### What exists today vs. what must be built

**What exists today:**
- The Abstention Engine already produces a per-query decision (`ANSWER`/`REVIEW`/`REQUEST_MORE_EVIDENCE`/`ESCALATE`/`ABSTAIN`) plus a calibrated confidence score and a persisted `ReliabilityEvent`/`AuditTrail` row per request.
- The Failure Memory model already produces a per-failure cluster assignment, a similarity-based "risk" score, and (separately, in experiments only — not wired to its own live API) a validated observation that plain abstention beats attempted auto-correction.
- Both systems independently implement the *concept* of "confidence" and "abstention," but with **incompatible representations**: Abstention Engine's confidence is a 0–100 (mostly) calibrated probability tied to LLM query semantics; Failure Memory's confidence is a 0–1 raw classifier probability tied to a small synthetic feature vector, further adjusted by a heuristic "anticipatory risk" term. These are not currently interoperable.

**Interfaces needed (to be built, not present today):**
- **Abstention Engine → Failure Memory**: every `ABSTAIN`/`ESCALATE` decision (and ideally every low-confidence `ANSWER`) should be emitted as a structured "failure/uncertain-event" record — currently the Abstention Engine's `ReliabilityEvent` schema and the Failure Memory's failure representation (PCA embedding of features+confidence) are different shapes and would need a shared schema (e.g., a canonical `FailureRecord{query_features, confidence, decision, context, timestamp}`).
- **Failure Memory → Abstention Engine**: retrieval of similar past failures and their cluster-level "anticipatory risk" should feed back into the Abstention Engine's confidence aggregation as one more signal — today there is no code path connecting the two repos at all; this must be built from scratch.
- **Shared concepts, currently duplicated with different implementations**: both repos independently implement "confidence," "abstention/decision thresholding," and "risk-coverage evaluation." The unified system should have exactly one of each, not one per subsystem.
- **Conflicting assumptions**: Abstention Engine assumes rich, semantic, LLM-generated text queries with retrieval; Failure Memory assumes small numeric feature vectors from a synthetic classifier. Bridging these requires either (a) generalizing Failure Memory's embedding to accept the Abstention Engine's richer feature/confidence outputs as its input "x," which is architecturally straightforward given `failure_embedding.py`'s simple interface, or (b) treating Failure Memory purely as a downstream analytics/clustering layer over Abstention Engine's already-computed confidence and metadata, which requires less rework.
- **Duplicate functionality to consolidate**: both repos have their own abstention-threshold logic and their own "risk/coverage" evaluation script — recommend keeping the Abstention Engine's calibrator + Failure Memory's risk-coverage harness, discarding the Abstention Engine's redundant legacy shim and the duplicate threshold logic in `services/reliability_engine.py`'s hardcoded floors in favor of one policy layer informed by both signals.
- **Architectural incompatibility to resolve**: Failure Memory's in-memory-only storage cannot support the always-on monitoring loop implied by the target architecture (`AI/ML Workload → Observability → ... → Recovery Orchestration`); it must be backed by the same persistent store the Abstention Engine already uses (`app/db/`) before any integration is meaningful.

The `Observability/Monitoring`, `Anomaly & Failure Detection`, `Diagnosis/Decision`, and `Recovery Orchestration` stages in the target architecture diagram **do not exist in either repo today** — both prototypes cover only the "Abstention" and "Failure Memory" boxes in that diagram, confirming this is genuinely a Phase 1 audit of two components, not a near-complete system.

---

## 9. Baseline Metrics

| Dimension | AI Abstention Engine | Introspective Failure Memory Model |
|---|---|---|
| **Functionality** | Full request→decision pipeline works end-to-end (verified live); one real ML signal, mostly overridden by hardcoded rules | Full failure→embed→cluster→risk pipeline works end-to-end (verified live); one validated result (risk-coverage curve), one confirmed-negative result (specialist correction) |
| **Performance (measured)** | Arithmetic path: instant. Non-arithmetic first request: ~seconds to minutes (cold-start calibrator training when no artifact is cached). No selective-risk/coverage curve exists for this repo. | Risk-coverage curve, reproduced: baseline error 35.44% → 7.14% error at 20% coverage. Specialist correction confirmed to *increase* error (30.5–41.3% vs. 35.4% baseline) — a validated negative result, not a weakness of the audit. |
| **Limitations** | Abstention decision is rule-based, not conformal/learned; two incompatible confidence scales cause a scoring bug (189.61/100 reproduced); no live-network-independent retrieval story; offline "self-consistency" carries no real signal | No persistence (in-memory only); no tests; live 500 bug on the streaming path; dashboard risk-coverage/specialist numbers are hardcoded, not computed |
| **Reproducibility** | Partial — tests pass but only after fixing an undeclared dependency; benchmark report numbers not reproducible from a fresh clone; unpinned deps | Good for the offline scripts (exact match to published numbers from a clean environment); poor for the live dashboard (hardcoded, so "reproducing" it just re-displays a constant) |
| **Engineering maturity** | Moderate — real auth, DB, tests, multi-provider abstraction, but no CI/Docker/pinning, and a live scoring bug | Lower — no tests, no persistence, but smaller/simpler surface area with less to go wrong; one live bug found |

These baselines are what any future integrated system must beat — in particular, the Failure Memory repo's 35.44%→7.14% risk-coverage improvement is the clearest existing bar for "does abstention help," and the Abstention Engine's 189.61 scoring bug and rule-override behavior are the clearest existing bar for "is confidence actually calibrated end-to-end" (currently: no).

---

## 10. Migration Plan

| Component | Migrate as-is | Refactor | Rewrite | Notes |
|---|---|---|---|---|
| `ReliabilityCalibrator` (`calibration.py`) | Core model architecture | Retraining pipeline to use real labeled outcomes instead of synthetic bootstrap; ship a committed artifact | — | Retain XGBoost+isotonic approach; add offline/cached artifact loading so cold start doesn't block a request |
| `ReliabilityEngine` orchestrator | Pipeline shape (classify→retrieve→route→score→decide→persist) | Collapse 10 "strategies" into a smaller, justified set; remove hardcoded floor/ceiling overrides of the calibrated score | Policy layer that combines calibrator output + Failure Memory risk signal | Interfaces needed: a single `decide(confidence, risk, context) -> Decision` function shared by both subsystems |
| `app/db/` schema | Table design | Migrate off SQLite to a real DB for the unified system; add Alembic migrations | — | Extend schema with a `FailureRecord` table compatible with Failure Memory's embedding output |
| `failure_embedding.py` / `failure_memory.py` | Clustering concept | Generalize embedding interface to accept batched, arbitrary-dimension input (not fixed 5-dim synthetic features); back storage with the DB above | Persistence layer | Dependency to remove: none needed (scikit-learn stays); dependency to add: shared DB client |
| `anticipatory_confidence.py` | — | — | Replace heuristic with a trained, validated risk-forecasting model with a measured predictive-accuracy metric (e.g., AUROC of "risk" vs. actual near-term failure) | This is the most valuable open research question flagged by the audit |
| `risk_coverage_curve.py` benchmark harness | As-is | Extend to non-synthetic data once available | — | Keep as the standard evaluation script for any future abstention policy change |
| Both `api.py`/`routes.py` FastAPI layers | Route surface | Fix the confirmed bugs (numpy serialization 500, trust-score scale bug, dead `/api/metrics` reference); remove all `# Mocked for UI` responses | Unified single API surface combining both repos' endpoints | Tests needed: full-pipeline default-config tests (no API keys, cold-start), not just isolated scoring-function tests |
| Frontends | UI components/shell | Rewire to real, non-mocked backend responses | — | Both frontends are reasonable starting shells |
| Docs/paper material | — | Regenerate all numeric claims from live runs; separate implemented vs. aspirational sections explicitly | New unified architecture doc | Remove the `IFM_CORE_CONCEPTS.md` claim contradicted by its own experiments, or caveat it as explored-and-rejected |
| `experiments/simulate_failures.py`, `experiments/train_model.py`, `app/core/model.py`, committed `reliability.db` | — | — | — | **Do not migrate** — discard entirely (orphaned code / personal credential leakage) |

**Technical debt to address before/during migration**: dependency pinning in both repos (currently zero), adding CI (tests currently only run manually and one repo's suite requires an undocumented dependency fix to even import), removing all hardcoded/mocked API responses, and resolving the confidence-scale incompatibility between the two repos before any shared decision function can be written.

**Completely missing and must be built from scratch in later phases**: observability/monitoring ingestion, anomaly/failure *detection* (as opposed to post-hoc failure *storage*), automated diagnosis beyond simple clustering, and the entire recovery orchestration layer (retry/rollback/reconfiguration/retraining/redeployment) — none of this exists in either repo today.

---

## 11. Phase 1 Risks and Gaps

1. **Confidence-scale bug is live and reproducible** (Abstention Engine `global_reliability_score: 189.61` instead of a 0–100 value) — must be fixed before this metric can be trusted for any Phase 2 comparison baseline.
2. **Both dashboards contain hardcoded/mocked values presented as live computation** — any future stakeholder demo or paper figure sourced from either live app's UI must be re-verified against the actual underlying script, not trusted at face value.
3. **No shared confidence/failure representation exists between the two repos** — integration work in Phase 2 will require designing this schema before any code-level wiring can happen; this is nontrivial design work, not a mechanical merge.
4. **Zero tests in Failure Memory, thin full-pipeline coverage in Abstention Engine** — regressions during refactoring in Phase 2 will not be caught automatically without new test investment.
5. **No CI/CD or Docker in either repo** — reproducibility currently depends entirely on a human following (incomplete) setup instructions correctly.
6. **Personal credentials committed to git** (`reliability.db` in Abstention Engine) — should be scrubbed/rotated and excluded before any repo is made more widely shared or public, and definitely not migrated into the unified repo as-is.
7. **`anticipatory_confidence.py`'s "prediction" is unvalidated** — there is currently no metric anywhere in either repo proving the anticipatory-risk heuristic actually predicts failures before they occur; this is a research gap, not just an engineering one.
8. **Retrieval in the Abstention Engine depends on scraping DuckDuckGo HTML** — fragile and possibly ToS-risky at any real traffic volume; a real dependency risk for anything downstream that assumes retrieval will keep working.
9. **In-memory-only storage in Failure Memory** is fundamentally incompatible with the "continuously monitor" framing of the target system — this is an architecture gap, not a bug, and needs a deliberate persistence design decision in Phase 2.

---

## 12. Recommended Phase 2

Based on the evidence gathered, Phase 2 should **not** attempt full integration yet. It should instead close the gaps that make integration well-defined:

1. **Fix the four confirmed live bugs** (Abstention Engine's trust-score scale bug and dead `/api/metrics` route; Failure Memory's numpy-serialization 500 and its two mocked endpoints) — cheap, high-confidence fixes that remove noise before any further design work.
2. **Design and implement one canonical `FailureRecord`/confidence schema** shared by both systems, and migrate the Failure Memory embedding pipeline to consume the Abstention Engine's `ReliabilityEvent` fields as its input feature vector (replacing the current 5-dim synthetic-feature assumption) — this is the single highest-leverage integration step identified above.
3. **Replace Failure Memory's in-memory store with the Abstention Engine's existing SQLAlchemy/DB layer**, extended with a `FailureRecord` table — resolves the persistence gap and gives both systems one shared data plane.
4. **Turn `risk_coverage_curve.py` into the standard evaluation harness** for the unified confidence/abstention signal (Abstention Engine's calibrator output re-evaluated through this proven methodology), establishing a single, trustworthy baseline metric going forward, replacing the currently-unreliable `public_benchmark_report.md` numbers.
5. **Only after 1–4**, prototype the actual signal fusion (Failure Memory's cluster-similarity "risk" feeding into the Abstention Engine's `decide()` as one more input) and measure whether it improves the risk-coverage curve versus the Abstention Engine's calibrator alone — this directly tests whether combining the two prototypes is actually additive, rather than assuming it.

Explicitly out of scope for Phase 2: building the Observability/Monitoring, Anomaly Detection, or Recovery Orchestration layers from the target architecture diagram — those depend on having one trustworthy, integrated confidence+failure-memory signal first, which is what Phase 2 should produce.


---

<a id="phase2-report"></a>
# PHASE2 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `PHASE2_REPORT.md`  
**Role:** Migration/integration of the two prototypes into one unified system; Phase 2 deliverable.

# Phase 2 — Foundation & Integration

**Scope:** build one unified, tested, persistent Reliability + Failure Memory subsystem from the two audited prototypes, and answer experimentally whether historical failure information improves abstention beyond calibrated confidence alone. All code lives under `C:\Autonomous AI infrastructure\` in `src/`, `tests/`, `benchmarks/`, `experiments/`, `configs/`, `docs/`. The two source prototype clones (`AI-Abstention-Engine/`, `Introspective-Failure-Memory-Model/`) have been deleted from this workspace after migration was verified — they remain available on GitHub as historical references, per the Phase 2 brief.

---

## 1. Phase 2 Summary

Phase 1 found two working but flawed prototypes: a real, calibrated ML confidence signal buried inside a rule-heavy orchestrator with a live confidence-scale bug (Abstention Engine), and a genuinely-reproducible risk-coverage result sitting behind a hardcoded/mocked live API with no persistence or tests (Failure Memory). Phase 2 rebuilt the reusable core of both — the calibrator concept and the clustering/risk concept — as two modules of one codebase, unified them behind a single canonical event schema and a single decision policy, backed them with real persistent storage, and ran the actual integration experiment the whole exercise was for: does adding Failure Memory's risk signal to the calibrator improve selective prediction? The experiment ran cleanly, on a controlled synthetic benchmark, and produced a clear, diagnosed answer (§11) — not a fabricated success and not a shrug.

## 2. Stabilization Results

Every confirmed Phase 1 bug/gap is addressed by construction in the unified codebase (not by patching the old repos, which were never modified):

| Phase 1 issue | Status | Where addressed |
|---|---|---|
| Confidence 0-1 vs 0-100 mixing → `global_reliability_score: 189.61` | **Fixed** | `src/schema/events.py` enforces `confidence ∈ [0,1]` at construction (pydantic `ValidationError` on violation); regression test `tests/unit/test_schema.py::test_confidence_over_100_scale_is_rejected` constructs the literal bad value 189.61 and asserts rejection |
| Missing `python-jose`/other undeclared deps | **N/A by design** | Auth was not migrated (see §5 — discarded, out of Phase 2 scope); `requirements.txt` here lists exact pinned versions of every package actually imported, verified by a clean install + full test run in a fresh venv |
| Orphaned code (`app/core/model.py`, `experiments/simulate_failures.py`) | **Not migrated** | Verified by construction — nothing in `src/` imports or reimplements these; confirmed no dead-endpoint references exist (`grep` for old repo paths in `src/`, `tests/`, `benchmarks/` returns only provenance comments, no imports — see §12) |
| `GET /api/metrics` documented but 404s | **Fixed** | `src/api/app.py` defines exactly one metrics route, `GET /api/metrics/summary`; test `tests/e2e/test_full_pipeline.py::test_metrics_summary_is_the_one_documented_route_and_no_fake_data` asserts `/api/metrics` (the old dead route) is 404 and the real route works |
| Committed `reliability.db` with personal credentials | **Not migrated** | Never copied; unified dev DB (`data/unified_dev.db`) is created empty by SQLAlchemy on first use, gitignored, and every test uses an isolated `tmp_path` SQLite file (`tests/conftest.py`) |
| Numpy scalar JSON-serialization 500 (Failure Memory `/api/control`) | **Fixed** | Every numeric value is cast to native Python `float`/`int` before entering `ReliabilityEvent` (`src/reliability`, `src/failure_memory`, `src/api/pipeline.py`); regression test `tests/unit/test_schema.py::test_event_is_json_serializable_without_numpy_leakage` feeds numpy scalars in and asserts clean `json.dumps` round-trip |
| Hardcoded/mocked `/api/risk-coverage`, `/api/specialists` | **Fixed** | `src/api/app.py` has no mocked endpoints; `/api/metrics/summary` returns `null` for metrics it cannot compute rather than a fabricated number; the benchmark script (`benchmarks/run_baselines.py`) and the live API share the exact same `ReliabilityPipeline`/training code (`src/pipeline_builder.py`), so a live-vs-paper divergence is structurally impossible |
| Failure Memory: no tests | **Fixed** | 41 tests total across unit/integration/e2e, including dedicated failure-memory coverage (`tests/unit/test_failure_memory.py`, `tests/unit/test_embedding.py`, `tests/integration/test_failure_memory_persistence.py`) |
| Failure Memory: in-memory-only storage | **Fixed** | `src/storage/` (SQLAlchemy) persists every event; `tests/integration/test_persistence_pipeline.py::test_persistence_survives_new_engine_against_same_db_file` simulates a process restart and confirms data survives |
| 10 overlapping abstention "strategies" + a dead compatibility shim | **Replaced** | One `DecisionPolicy` (`src/decision/policy.py`), three configurable fusion modes, no dead code |
| `anticipatory_confidence.py`, unvalidated heuristic | **Isolated, not used** | Migrated to `src/failure_memory/anticipatory.py`, explicitly marked EXPERIMENTAL, not imported by `src/decision` or `src/api`, not part of the Baseline A/B/C comparison |

## 3. Unified Architecture

```
                    Workload input (context: dict[str, float])
                              │
                              ▼
                    WorkloadModel.predict()      (src/reliability/workload_model.py)
                              │  predicted_label, predicted_proba, margin, entropy
                              ▼
                    ConfidenceCalibrator.predict()  (src/reliability/calibrator.py)
                              │  calibrated confidence ∈ [0,1]
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
   FailureMemory.risk(context, conf)   (context, confidence)
   (src/failure_memory/memory.py)            │
                │  risk ∈ [0,1]              │
                └─────────────┬─────────────┘
                              ▼
                DecisionPolicy.decide(confidence, risk, mode)
                        (src/decision/policy.py)
                              │  ANSWER / ABSTAIN / REVIEW
                              ▼
                  ReliabilityEvent (src/schema/events.py)
                              │
                              ▼
                EventRepository.save()  →  SQLite (src/storage/)
                              │
                              ▼
                FailureMemory.store() (if is_failure)  → re-fit on next batch
```

`src/pipeline_builder.py` trains the three fitted components (workload model, calibrator, failure memory) once from the synthetic regime-drift dataset (`src/data/synthetic.py`) and is the single training procedure shared by the live API (`src/api/train.py`) and the benchmark harness (`benchmarks/run_baselines.py`) — eliminating the live-demo-vs-paper divergence Phase 1 found in the Failure Memory prototype.

## 4. Canonical Data Model

Full field-by-field documentation: [`docs/SCHEMA.md`](docs/SCHEMA.md). Summary: one pydantic model, `ReliabilityEvent` (`src/schema/events.py`), used by every subsystem and persisted verbatim via `src/storage/`. Confidence, raw confidence, and failure risk are all validated to `[0.0, 1.0]` at construction — the single change that makes the Phase 1 scale-mixing bug structurally impossible to reintroduce. `Decision` is a closed 3-value enum (`ANSWER`/`ABSTAIN`/`REVIEW`), replacing the source Abstention Engine's 5 overlapping decision labels.

## 5. Migration Record

| Component | Source | Decision | What changed |
|---|---|---|---|
| Calibrated confidence (structured features → classifier → isotonic calibration) | Abstention Engine `calibration.py` | **Refactored & migrated** | Kept the structured-features → classifier → isotonic-calibration shape (`src/reliability/calibrator.py`); dropped the DeBERTa text-embedding branch — Phase 1 flagged it as a fragile, network-dependent cold-start cost, and Phase 2's workloads are structured/numeric, giving the text branch nothing to encode |
| Failure representation (PCA + confidence-derived scalars) | Failure Memory `failure_embedding.py` | **Refactored & migrated** | Generalized to a canonical `context: dict[str, float]` input instead of a hardcoded 5-dim array; added a real batch API (`embed_batch`) — the source's single-sample-only API was the direct cause of the slowest script in either Phase 1 repo |
| Clustering + similarity risk | Failure Memory `failure_memory.py`, `anticipatory_confidence.py`'s Gaussian-kernel term | **Refactored & migrated** | Persistent (`src/failure_memory/memory.py`, backed by `src/storage/`) instead of in-memory-only; cluster count and kernel width are constructor parameters in one place instead of duplicated literals across 5+ files |
| Recency-weighted "anticipatory" risk adjustment | Failure Memory `anticipatory_confidence.py` | **Isolated, not integrated** | Migrated verbatim as `src/failure_memory/anticipatory.py`, explicitly labeled experimental, excluded from the decision policy and from the Baseline A/B/C comparison, per Phase 2 brief §2.6 |
| Abstention/decision logic (10 strategies + legacy shim) | Abstention Engine `strategies.py`, `services/reliability_engine.py`, `app/core/abstention.py` | **Discarded, rewritten** | Replaced by one `DecisionPolicy` (`src/decision/policy.py`) with 3 explicit fusion modes and one threshold rule, used identically across all three Baselines |
| DB layer (SQLAlchemy foundation) | Abstention Engine `app/db/` | **Refactored, not copied** | New schema matching the canonical event model exactly (`src/storage/models.py`), no tenancy/auth concerns carried over |
| `reliability.db` (committed personal data) | Abstention Engine | **Discarded** | Never copied; unified dev DB starts empty |
| `app/core/model.py`, `experiments/simulate_failures.py` | Abstention Engine | **Discarded** | Confirmed orphaned in Phase 1 (zero callers, target a nonexistent endpoint); not migrated |
| Auth/JWT/multi-tenant routes, DuckDuckGo retrieval, provider routing | Abstention Engine | **Discarded (out of scope)** | Phase 2 brief explicitly excludes observability/recovery/agent features; these belonged to the LLM-query use case the Abstention Engine targeted, not the structured-workload reliability core this phase builds |
| Risk-coverage evaluation methodology | Failure Memory `risk_coverage_curve.py` | **Migrated as the standard harness** | `benchmarks/risk_coverage.py` — same coverage-sweep protocol, generalized to score any of the three systems |
| Synthetic regime-drift dataset generator | Failure Memory `synthetic_failure_dataset.py` | **Refactored & migrated** | `src/data/synthetic.py` — parameterized regime count/size/drift instead of hardcoded 5×10,000 |
| Frontends (`frontend/`, `frontend-v2/`) | Both | **Discarded (out of scope)** | Phase 2 brief scopes UI work out; no frontend was rebuilt |

## 6. Persistence Design

One SQLAlchemy table, `reliability_events` (`src/storage/models.py`), mirrors the canonical schema field-for-field — there is no separate "failure" table, because a failure is just a `ReliabilityEvent` with `is_failure=True`. `EventRepository` (`src/storage/repository.py`) is the only code that translates between the pydantic model and the ORM row, so schema drift between "what's validated" and "what's stored" cannot occur silently.

`FailureMemory.store(event, repository)` writes every event through to the shared store, but only retains failures (`is_failure=True`) in its own clustering view — `retrieve()`/`risk()` operate over the failure subset. `FailureMemory.load_from_repository()` rebuilds this view from persisted data, which is how the persistence-survives-restart guarantee is verified (`tests/integration/test_persistence_pipeline.py`, `test_failure_memory_persistence.py`): a brand-new `FailureMemory` instance, with no in-process state, reloads 10 previously-stored failures from the DB and reproduces the same risk signal.

Default backend is SQLite at `data/unified_dev.db` (gitignored, created empty, never seeded with personal data); `DATABASE_URL` env var switches to any SQLAlchemy-supported backend without code changes.

## 7. Unified Decision Logic

`DecisionPolicy.decide(confidence, risk, mode)` (`src/decision/policy.py`) computes one fused `[0,1]` "trustworthiness" score and applies one threshold rule regardless of mode:

- `score ≥ answer_threshold` → **ANSWER**
- `score < abstain_threshold` → **ABSTAIN**
- otherwise → **REVIEW**

Three modes select how the score is computed from the available signal(s) — this is what makes the Baseline A/B/C comparison fair: the threshold logic is identical, only the input differs.

- **CONFIDENCE_ONLY** (Baseline A): `score = confidence`
- **RISK_ONLY** (Baseline B): `score = 1 − risk`
- **COMBINED** (System C): `score = clip(confidence − risk_weight × risk, 0, 1)`

Thresholds and `risk_weight` live in one place (`PolicyConfig`, loadable from `configs/policy.json`), fixed *a priori* (`answer_threshold=0.70`, `abstain_threshold=0.40`, `risk_weight=0.50`) before the test-set evaluation — not tuned against test results, per the Phase 2 brief's explicit instruction not to optimize against the test set.

## 8. Test Results

```
python -m pytest tests/ -v
...
41 passed, 3 warnings in 5.87s   (0 failures, 0 errors, run from a clean checkout with the old repos already removed)
```

| Layer | Files | What's covered |
|---|---|---|
| Unit (17 tests) | `test_schema.py`, `test_decision_policy.py`, `test_embedding.py`, `test_failure_memory.py`, `test_calibrator.py` | Confidence-bound validation (incl. the literal 189.61 regression case), numpy-serialization safety, decision-policy threshold/mode logic, embedding batch-vs-single consistency, failure-memory risk/retrieve/cluster behavior before and after fitting, calibrator output bounds and a statistical sanity check (top-quartile confidence correct more often than bottom-quartile) |
| Integration (9 tests) | `test_persistence_pipeline.py`, `test_failure_memory_persistence.py`, `test_decision_fusion.py` | Event save/get roundtrip, **persistence survives a simulated process restart**, failure filtering, failure memory reload-from-DB reproducing its risk signal, all three decision modes exercised through a real trained system |
| E2E (3 tests) | `test_full_pipeline.py` | Full FastAPI app: health check, `POST /api/analyze` → real decision → persisted → visible in `/api/metrics/summary`; confirms the dead `/api/metrics` route is gone and metrics are honestly `null` before any data exists |

No hardcoded/fabricated test data was used to force passes — the calibrator and decision-policy tests use real trained models on synthetic data with a fixed seed, and every persistence test round-trips through an actual (temp, isolated) SQLite file.

## 9. Benchmark Methodology

Documented in full in `benchmarks/risk_coverage.py`'s module docstring; summarized here per the Phase 2 brief's requirement to state dataset/split/model/threshold/protocol/seed/metrics explicitly:

- **Dataset**: `src/data/synthetic.py`, a 5-regime synthetic binary-classification stream with concept drift (each regime's true decision boundary rotates away from regime 0's, proportional to regime index) — this is what makes failure-memory's premise (the model accumulates a nonrandom failure pattern after training) meaningful to test at all. Sizes: `(3000, 1500, 1500, 1500, 1500)`.
- **Split**: regime 0 → trains `WorkloadModel`; regime 1 → trains `ConfidenceCalibrator`; regime 2 → a "logging pass" that runs the frozen workload model + calibrator and records every wrong `ANSWER` as a failure, used to fit `FailureMemory`; regimes 3+4 (3000 samples) → held out, never used for fitting anything — this is what is scored.
- **Model**: `LogisticRegression` workload model; `GradientBoostingClassifier` (100 trees, depth 3) + isotonic regression calibrator; `KMeans` (k=3) over a 4-dim PCA+confidence embedding for failure memory.
- **Threshold/policy**: `PolicyConfig(answer_threshold=0.70, abstain_threshold=0.40, risk_weight=0.50)`, fixed before evaluation.
- **Protocol**: for each system, rank the held-out test stream by its fused score descending, sweep coverage 5%→100% in 5-point steps, report selective risk (1 − accuracy) among the accepted fraction at each level; separately report the fixed-threshold operating point (what the system would actually do in production).
- **Seed**: `42`, deterministic (`np.random.default_rng(seed)` throughout — no unseeded randomness in the training or evaluation path).
- **Metrics**: coverage, selective risk, abstention rate, accuracy-on-accepted — no metric was added beyond what the source repos' own methodology justified.

Reproduce with:
```
python benchmarks/run_baselines.py
python benchmarks/diagnose_risk_signal.py
```

## 10. Baseline Comparison

**Fixed operating point** (each system's own `PolicyConfig` thresholds applied to its own score — note the systems accept different fractions of the test stream, so this table alone is not a fair head-to-head; see the matched-coverage table below for that):

| System | Coverage | Selective Risk | Abstention Rate | Accuracy on Answered |
|---|---:|---:|---:|---:|
| Calibrator only (A) | 0.6343 | 0.2785 | 0.3657 | 0.7215 |
| Failure Memory only (B) | 0.3350 | 0.3174 | 0.6650 | 0.6826 |
| Combined (C) | 0.2763 | 0.2207 | 0.7237 | 0.7793 |

Baseline error with no abstention at all: **0.3333** (3000 held-out test samples).

**Matched-coverage comparison** (the methodologically correct comparison — same acceptance fraction for every system, from `experiments/results/baseline_comparison.json`'s full swept curve):

| Coverage | A: Calibrator only | B: Failure Memory only | C: Combined |
|---:|---:|---:|---:|
| 0.10 | **0.1400** | 0.3600 | 0.2133 |
| 0.20 | **0.1667** | 0.3217 | 0.2083 |
| 0.30 | **0.2078** | 0.3278 | 0.2267 |
| 0.40 | **0.2200** | 0.3158 | 0.2475 |
| 0.50 | **0.2420** | 0.3200 | 0.2687 |
| 0.60 | **0.2694** | 0.3183 | 0.2856 |
| 0.70 | **0.2905** | 0.3233 | 0.2962 |
| 0.80 | **0.3029** | 0.3275 | 0.3029 |
| 0.90 | **0.3178** | 0.3293 | 0.3219 |

**At every matched coverage level, Calibrator-only (A) has the lowest or tied-lowest selective risk.** Combined (C) is worse than A at every level except a near-tie at 0.80 coverage; Failure-Memory-only (B) is worse than both A and C everywhere and barely beats the no-abstention baseline (0.3333) even at high coverage.

## 11. Integration Findings

> **Does Failure Memory actually improve the calibrated abstention system? No — in this experiment, adding the failure-memory risk signal made selective prediction worse, not better, at every matched coverage level.**

This is a genuine negative result, diagnosed rather than just observed (`experiments/results/risk_signal_diagnosis.json`):

- **The failure-memory risk signal carries almost no information about actual failure.** Its correlation with `incorrect` on the held-out test stream is **0.031** — indistinguishable from noise. By contrast, calibrated confidence correlates with `correct` at **0.200** — meaningfully informative, though modest.
- **A weight sensitivity sweep confirms this monotonically**: at matched coverage (0.2 / 0.5 / 0.8), selective risk gets *strictly worse* as `risk_weight` increases from 0.0 (pure calibrator) to 1.0 (pure risk-discounted), at every coverage level except 0.8 where it's flat:

  | risk_weight | risk@cov=0.2 | risk@cov=0.5 | risk@cov=0.8 |
  |---:|---:|---:|---:|
  | 0.00 (= Baseline A) | 0.1667 | 0.2420 | 0.3029 |
  | 0.10 | 0.1817 | 0.2400 | 0.3071 |
  | 0.25 | 0.1867 | 0.2487 | 0.3042 |
  | 0.50 (System C default) | 0.2083 | 0.2687 | 0.3029 |
  | 0.75 | 0.2150 | 0.2807 | 0.3050 |
  | 1.00 | 0.2350 | 0.2853 | 0.3079 |

  There is no `risk_weight > 0` that beats `risk_weight = 0` at coverage 0.2 or 0.5 in this experiment; blending in the failure-memory signal only adds noise.

**Why this likely happened**: the failure-memory embedding is a 4-dimensional projection (2 PCA components over 5 raw features, plus 2 confidence-derived scalars) clustered into only 3 groups, fit on 407 failures logged from a single post-drift regime. The held-out test regimes (3 and 4) have drifted further still, so the failure clusters learned from regime 2 are a poor geometric match for where regime 3/4's failures actually occur — the clustering captures *where failures happened during logging*, not a generalizable pattern that predicts *where they will happen next* under continued drift. This is analogous to, and consistent with, Phase 1's own finding that the source Failure Memory repo's "cluster specialist" correction idea made predictions worse (PHASE1_AUDIT_REPORT.md §3, §7) — both results point to the same underlying weakness: this style of small-cluster, low-dimensional failure representation does not generalize well beyond the exact distribution it was logged from.

This was not the hoped-for headline result, but it is the honest one, obtained without adjusting thresholds or evaluation protocol after seeing test-set numbers (thresholds were fixed before the test-stream evaluation; the sensitivity sweep is reported in full, not cherry-picked to a favorable weight).

## 12. Remaining Limitations

- **Independence verified by static analysis, not by a live directory-removal test.** A `mv`-based independence check was attempted but blocked by a Windows file-lock (permission denied on the old repo directories); independence was instead confirmed by (a) grepping `src/`, `tests/`, `benchmarks/` for any reference to the old repo paths — the only matches are provenance comments, no imports or file-path couplings — and (b) actually deleting both directories and re-running the full test suite and benchmark afterward, both of which passed cleanly. This is strong evidence but not identical to the originally-planned rename-then-test procedure.
- **Synthetic data only.** Per Phase 1's own caveat about the source repos, this remains a controlled synthetic benchmark (regime-drift binary classification), not a real-world workload. The integration finding (§11) is specific to this data-generating process and this failure-memory representation; it should not be read as "failure memory never helps," only as "this implementation of it did not help here."
- **Failure-memory representation is minimal by design** (2D PCA + 2 confidence scalars, 3 clusters) — matching the source prototype's scope. A higher-capacity or differently-structured representation (e.g., directly on raw features rather than PCA-reduced, or density-based rather than KMeans) might correlate better with future failures; this was not attempted, per the Phase 2 brief's instruction not to spend the phase building a new prediction model.
- **`anticipatory.py` remains genuinely unvalidated** — isolated and unused by design (§2), not because it was tested and found lacking.
- **No real LLM/text workload was rebuilt.** The Abstention Engine's retrieval, multi-provider routing, and auth layers were deliberately discarded as out of Phase 2 scope (per the brief's explicit exclusions); the unified system currently only supports structured/numeric workloads.
- **Deprecation warning**: `starlette.testclient` + `httpx` combination is marked deprecated upstream (cosmetic only, does not affect test correctness).
- **No CI configured yet** — per the brief's explicit instruction not to build full CI/CD in this phase; reproducibility instead rests on pinned dependencies, a fixed seed, and documented commands (§9, README.md).

## 13. Phase 3 Recommendation

Based on the diagnosed negative result in §11, Phase 3 should **not** proceed to building Observability/Detection/Recovery layers on top of the current failure-memory risk signal as-is — that would build automation on a signal just shown to be near-noise. Instead:

1. **Improve the failure representation before trying integration again.** Test whether a higher-dimensional embedding (skip the PCA reduction; cluster directly on the calibrator's own structured features), a larger/continuously-updated failure log (rather than one fixed logging-regime snapshot), or a density-ratio/anomaly-score approach (rather than distance-to-KMeans-centroid) produces a risk signal with materially higher correlation with actual incorrectness than the 0.031 measured here. Treat "correlation with incorrect > confidence's own correlation with correct" as the bar for even considering re-integration.
2. **Only then re-run the exact `benchmarks/run_baselines.py` / `diagnose_risk_signal.py` protocol** already built in this phase — the harness doesn't need to change, only the failure-memory implementation feeding it does. This keeps the comparison apples-to-apples with Phase 2's baseline.
3. **Validate `anticipatory.py`'s recency-weighting properly** if pursued at all: define a predictive-accuracy metric (e.g., AUROC of anticipated risk vs. actual near-term failure occurrence) before considering it for the live policy, per the Phase 2 brief's own caution.
4. **Only after a failure-memory signal clears step 1's bar** should Phase 3 begin layering Observability/Monitoring and Anomaly Detection on top, since those layers' value depends on having a trustworthy signal to act on — building them first would be automating around noise.


---

<a id="schema"></a>
# SCHEMA
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/SCHEMA.md`  
**Role:** The canonical ReliabilityEvent schema reference (still in active use, unmodified since Phase 1/2).

# Canonical Reliability/Failure Event Schema

Defined in [`src/schema/events.py`](../src/schema/events.py) as the pydantic
model `ReliabilityEvent`. This is the single representation shared by the
reliability (confidence) subsystem and the failure-memory subsystem — see
`PHASE1_AUDIT_REPORT.md` sections 2/3/8 for why the two source prototypes'
incompatible representations made this necessary.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | `str` | auto (uuid4 hex) | Primary key |
| `timestamp` | `datetime` (tz-aware, UTC) | auto | Coerced to UTC if naive |
| `workload_id` | `str` | yes | Identifies the monitored model/workload |
| `source` | `EventSource` enum | yes | `reliability_engine` \| `failure_memory` \| `benchmark` |
| `context` | `dict[str, float]` | yes | Structured numeric feature vector describing the input. Canonical replacement for both source repos' ad-hoc feature representations. |
| `raw_confidence` | `float \| None` | no | Pre-calibration confidence, `[0.0, 1.0]` |
| `confidence` | `float` | yes | Calibrated confidence. **Always `[0.0, 1.0]`, never 0-100.** |
| `failure_risk` | `float \| None` | no | Failure-memory's similarity-based risk, `[0.0, 1.0]` |
| `decision` | `Decision` enum | yes | `ANSWER` \| `ABSTAIN` \| `REVIEW` |
| `abstained` | `bool` | yes | Must equal `decision != ANSWER` (validated) |
| `is_failure` | `bool` | default `False` | True only for confirmed wrong `ANSWER`s; failure-memory stores only these |
| `failure_cluster` | `int \| None` | no | Assigned by failure-memory clustering |
| `outcome` | `Outcome` enum | default `UNKNOWN` | `CORRECT` \| `INCORRECT` \| `UNKNOWN` |
| `metadata` | `dict` | default `{}` | Free-form provenance only — must never contain personal data (see `PHASE1_AUDIT_REPORT.md` section 5/11 on the `reliability.db` credential leak this project does not repeat) |

## Validation rules

- `confidence`, `raw_confidence`, `failure_risk` — must lie in `[0.0, 1.0]`. This is a regression guard for the Phase 1 `global_reliability_score: 189.61` bug: any code path that hands a 0-100-scale number to this model raises `ValidationError` immediately instead of silently corrupting an aggregate metric. See `tests/unit/test_schema.py::test_confidence_over_100_scale_is_rejected`.
- `abstained` must be consistent with `decision`.
- `timestamp` is normalized to UTC.
- The model is `extra="forbid"` — an unexpected field is a schema violation, not silently dropped or accepted.

## Presentation-layer conversion

`confidence_to_percent(confidence: float) -> float` is the *only* place a
0-1 confidence is converted to a 0-100 display value. Presentation code
(dashboards, reports) must call this rather than re-deriving the conversion.


---

<a id="phase3-1-evaluation-protocol"></a>
# PHASE3 1 EVALUATION PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_1_EVALUATION_PROTOCOL.md`  
**Role:** Phase 3.1 frozen evaluation protocol (synthetic data).

# Phase 3.1 — Evaluation Protocol and Baseline Reproduction

Status: **frozen**. This document and `configs/phase3_1_protocol.json` were written before any Phase 3.1 result existed. Reproduce with:

```bash
python benchmarks/phase3_1_leakage_audit.py
python benchmarks/phase3_1_evaluate.py
```

Both are deterministic given the seeds in `configs/phase3_1_protocol.json` and write machine-readable output to `experiments/results/phase3_1/`.

---

## 1. Prediction Task

**What is currently predicted, precisely:** for a single workload inference event, given the input features and the (frozen, already-trained) workload model's own output statistics for that event, will this particular prediction turn out to be **wrong**?

- **Prediction unit**: one inference event (one row of `src/data/synthetic.py`'s regime stream — one classification call).
- **Prediction horizon**: **none**. This is the critical gap to name explicitly, per this phase's instruction not to overstate what the system does. The current architecture makes no claim about *when in the future* a failure will occur, over what time window, or how many events ahead. It scores "is this specific, already-happening inference likely to be wrong," using only information available at the moment that inference is made. It does not forecast an upcoming failure before the triggering input arrives, does not predict an aggregate future failure *rate*, and does not use any temporal/sequential structure (samples within a regime are i.i.d. draws, not a literal time series with elapsed time between them).
- **Failure definition**: `workload_model.predict(x).predicted_label != true_label`, exactly as defined in `src/pipeline_builder.py`'s failure-logging pass and reproduced identically for test-set scoring in `benchmarks/phase3_1_evaluate.py::_compute_test_arrays`. This is unchanged from Phase 2 — not silently redefined for Phase 3.1.
- **Positive class** (`y_fail = 1`): the workload model's prediction is wrong.
- **Negative class** (`y_fail = 0`): the workload model's prediction is correct.
- **Available features at prediction time**: the sample's raw context (`f1..f5`) and the frozen workload model's own output statistics for that same sample (`predicted_proba`, `margin`, `entropy`) — all computable the instant the input arrives, before the true label is known.
- **Unavailable / future information**: the true label itself; any information from regimes not yet fit/observed (regimes 3+4, the test set, are never used to fit anything — see §4).
- **When the prediction is made**: immediately, from the input alone.
- **When the failure outcome becomes known**: immediately after, in this synthetic harness (the true label is available the instant it's needed for scoring). This is itself a simplification worth naming: a real deployment typically has label latency (ground truth arrives late or not at all for many predictions); this benchmark does not model that.

**The gap Phase 3 must eventually address**: the system Phase 2 and 3.1 evaluate is an **instantaneous failure classifier**, not a **future failure predictor** in the sense the eventual Phase 3 research question ("can Failure Memory predict future failures") implies. Whether historical failure information can anticipate failures *before* they happen (i.e., using cluster/recency information to say "the next N events from this region of feature space are elevated-risk") is not evaluated here and is not established by anything in Phase 2 or 3.1. `src/failure_memory/anticipatory.py` gestures at a recency-weighted version of this but remains explicitly unvalidated and unused (per Phase 2's decision, unchanged here).

## 2. Dataset

`src/data/synthetic.py::generate_regime_stream` — 5 synthetic binary-classification regimes, feature vectors `f1..f5 ~ N(0, I)` every regime (i.i.d., regime-independent marginal), true label generated from a logistic function of a regime-specific weight vector that rotates away from regime 0's by `drift_scale * regime_index`. Regime sizes: `(3000, 1500, 1500, 1500, 1500)` — unchanged from Phase 2's `DEFAULT_REGIME_SIZES`, frozen in `configs/phase3_1_protocol.json`. This remains synthetic data; nothing in this phase claims real-world generalization (see §11).

## 3. Split Strategy

Unchanged from Phase 2 (`src/pipeline_builder.build_system`), mapped explicitly onto train/validation/test terminology:

| Regime | Role | Used for |
|---|---|---|
| 0 | **Train** | Fits `WorkloadModel` (frozen afterward) |
| 1 | **Validation (calibration)** | Fits `ConfidenceCalibrator` |
| 2 | **Validation (failure logging)** | Runs the frozen workload model + calibrator, logs wrong predictions as failures, fits `FailureMemory`'s embedding + KMeans |
| 3, 4 (concatenated) | **Test — untouched** | Never used to fit anything. Scored once per seed. |

**Note on "validation" here**: regimes 1 and 2 are used to *fit* auxiliary components, not to *select among alternative configurations* — Phase 2/3.1 do not perform any hyperparameter search or model selection against regime 1/2 performance. This means there is currently no leakage risk from that direction, but it also means the train/validation split does not yet do the job a validation set is normally for (guarding against overfitting a choice). If Phase 3.2 introduces tuning (e.g. cluster count, kernel width), a genuine validation-based selection step will need to be added then — flagged here, not fixed now, per this phase's scope.

## 4. Leakage Audit

Full machine-readable report: `experiments/results/phase3_1/leakage_audit.json`, produced by `benchmarks/phase3_1_leakage_audit.py`, which runs each check against a real, live-built system rather than reasoning about the code in the abstract.

| Check | Method | Result |
|---|---|---|
| **Temporal leakage / fit isolation** | Re-derive the regime split from the same generator call; confirm it's a strict disjoint partition; confirm every failure-memory training event's stored `regime` metadata is `2` (never 3 or 4) | **PASS** — partition disjoint; failure memory fit only on regime-2 data |
| **Label leakage** | Inspect every context dict handed to the embedder/calibrator for `label`/`regime`/`y` keys | **PASS** — context contains exactly `{f1..f5}`, nothing else |
| **Preprocessing (PCA) leakage** | Independently rebuild the system and confirm the failure count used to fit `FailureEmbedder`'s PCA matches an independent recount of regime-2 failures | **PASS** — counts match |
| **Clustering leakage** | Same isolation check as temporal leakage — KMeans is fit inside `FailureMemory.fit()`, called only on the events accumulated during the regime-2 logging pass; the test stream is never passed to `.fit()` anywhere in `src/pipeline_builder.py` | **PASS** — confirmed by direct code inspection (§ "Audit" below) and by the temporal-leakage runtime check |
| **Regime leakage** | Compare per-regime feature means/stds; the generator constructs `f1..f5 ~ N(0,I)` identically every regime (only the label-generating weight vector drifts) | **PASS** — max per-regime mean deviation from grand mean was small (well under the sanity bound); regime id is not trivially recoverable from features. **Important nuance, not a leakage finding**: because feature *marginals* don't shift but the *decision boundary* does, failure-memory's clusters (located in feature space from regime-2 failures) have no statistical reason to align with where regime-3/4's failures occur — this is the likely mechanism behind the weak signal reported in §10, not a data leak. |
| **Duplicate/sample leakage** | Hash every sample's rounded feature vector; check for any hash appearing in more than one split | **PASS** — zero overlaps found between train/calibration/logging/test |
| **Synthetic-generation triviality** | Check label prevalence isn't degenerate (all-0/all-1) and no single feature has near-1.0 correlation with the label | **PASS** — prevalence and per-feature correlations are all in a non-trivial range |

**Overall: no leakage found across any of the seven checks, for the seed(s) tested.** This is a genuinely-checked negative result, not an assumption — every check above ran real code against a real built system and recorded its actual output in `leakage_audit.json`, and is also exercised as a pytest regression (`tests/integration/test_phase3_1_leakage.py`) so a future code change that introduces leakage would fail the test suite.

**Threat to validity this audit does NOT cover**: the leakage audit was run in depth for seed 42 (and the disjointness/regime-metadata checks are additionally exercised at small scale across several seeds via the pytest regression suite), not independently re-run in full for all 6 protocol seeds as a standalone script. Given the checks are structural (they test *how the code is wired*, not something that varies with the random draw), this is a low-risk gap, but it is named here rather than silently assumed away.

## 5. Metrics

All implemented fresh in `src/evaluation/metrics.py` (new in Phase 3.1; Phase 2's `benchmarks/risk_coverage.py` is imported unchanged, not reimplemented):

- **AUROC** (`sklearn.metrics.roc_auc_score`): ranking quality of the failure-risk score against `y_fail`, prevalence-independent. Returns `None` (not a fabricated 0.5/1.0) if a resample/seed happens to contain only one class.
- **AUPRC** (`sklearn.metrics.average_precision_score`): ranking quality weighted toward the positive (failure) class; more sensitive to class-prevalence differences than AUROC, read alongside it rather than in isolation.
- **Calibration — Expected Calibration Error (ECE)**: standard equal-width 10-bin ECE, `src/evaluation/metrics.py::expected_calibration_error`. Computed for all three baselines, including Failure Memory's raw similarity-kernel output, which was never fit/designed to be a calibrated probability — reported anyway as an honest diagnostic (a large ECE there is expected and informative, not a bug).
- **AURC** (Area Under the Risk-Coverage curve): reuses Phase 2's unmodified `risk_coverage_curve` (5%–100% coverage, 5-point steps), trapezoidally integrated. Lower is better. Documented as an approximation over `[0.05, 1.0]`, not extrapolated to coverage 0.
- **Precision / Recall at operating points**: see §6.
- **Confidence intervals**: see §5b.

### 5b. Confidence Intervals

Two distinct sources of uncertainty are reported, not conflated:

1. **Cross-seed variability** (`benchmarks/phase3_1_evaluate.py::_t_interval`): each metric is computed once per predetermined seed (§7), then a Student-t interval (appropriate for the small n=6 sample of seeds, rather than a normal approximation) is computed over the 6 point estimates. This captures sensitivity to the random data-generating draw.
2. **Within-seed bootstrap** (`src/evaluation/bootstrap.py::bootstrap_ci`): for the primary seed (42) only, a nonparametric percentile bootstrap resamples the (y_fail, score) test-set rows with replacement. Documented parameters: **2000 resamples**, **95% confidence level**, **bootstrap seed 0** (fixed, in `configs/phase3_1_protocol.json`), percentile aggregation (2.5th/97.5th percentile of the resampled-metric distribution). This captures finite-test-set sampling uncertainty for one fixed data draw. Resamples that degenerate to a single class (undefined AUROC) are counted (`n_degenerate_resamples`) and excluded from the interval, not silently zeroed.

No false precision is claimed: both intervals are reported with their method named, and neither is used interchangeably with the other.

## 6. Operating Points

Defined **before** any test-set evaluation ran, as fixed **coverage fractions** (not score thresholds fit to maximize a test metric): `{5%, 10%, 20%, 50%}` of the test set, flagged as "high risk" by ranking on each baseline's own score. Precision = fraction of flagged samples that are true failures; recall = fraction of all true failures captured within the flagged set. This sidesteps the classic failure mode of picking a threshold after seeing which one looks best on the test set — the coverage level is the a priori decision (e.g. "we are willing to review the riskiest 10% of predictions"), not the resulting score cutoff.

## 7. Random Seeds

Predetermined list, written into `configs/phase3_1_protocol.json` before any Phase 3.1 run: **`[1, 2, 3, 4, 5, 42]`**. `1`–`5` are a plain sequential convention; `42` is retained for continuity with the original single-seed Phase 2 result. No seed was added, removed, or swapped after inspecting results — the committed config file's timestamp/content is the evidence for this claim. Primary seed for the bootstrap analysis: **42**.

## 8. Baselines

| Baseline | Definition | Fit on |
|---|---|---|
| **A — No failure signal** | Constant score = empirical failure prevalence measured on the regime-2 logging set (i.e., "predict the base rate, ignore the input entirely") | Regime 2 (train-side) |
| **B — Calibrated confidence** | `1 − ConfidenceCalibrator.predict(...).calibrated_confidence` (Phase 2's isotonic-calibrated confidence, unmodified) | Regime 1 |
| **C — Phase 2 Failure Memory** | `FailureMemory.risk(context, confidence)` (Phase 2's unmodified KMeans + Gaussian-kernel similarity score) | Regime 2 |

Baseline A is not a strawman — it is the correct anchor for "no signal": its AUROC must be exactly 0.5 by construction (a constant score cannot discriminate), which also serves as a sanity check on the evaluation code itself (verified: it is exactly 0.5000 for every seed, see §10, and asserted by `tests/integration/test_phase3_1_pipeline.py::test_no_signal_baseline_auroc_is_always_exactly_half_across_seeds`).

## 9. Reproducibility

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # exact pinned versions
python benchmarks/phase3_1_leakage_audit.py     # -> experiments/results/phase3_1/leakage_audit.json
python benchmarks/phase3_1_evaluate.py          # -> experiments/results/phase3_1/{per_seed_results.json,.csv, aggregate_results.json, bootstrap_ci_primary_seed.json}
python -m pytest tests/ -v                      # 70 tests, includes Phase 3.1 evaluation-infra + leakage regressions
```

Every output JSON embeds: full protocol config, UTC timestamp, and `python`/`numpy`/`scikit-learn`/`scipy` versions (`benchmarks/phase3_1_evaluate.py::main`'s `meta` block) — dataset "version" is the frozen `regime_sizes` + seed list in `configs/phase3_1_protocol.json` itself (there is no external dataset file to version; the generator is deterministic and committed).

## 10. Results

All numbers below are read directly from `experiments/results/phase3_1/` — none are hand-typed estimates.

### Per-seed (AUROC / AUPRC / ECE / AURC)

| Baseline | Seed | AUROC | AUPRC | ECE | AURC |
|---|---:|---:|---:|---:|---:|
| A — No signal | 1 | 0.5000 | 0.3423 | 0.0883 | 0.2973 |
| B — Calibrated confidence | 1 | 0.6302 | 0.4310 | 0.0517 | 0.2622 |
| C — Failure Memory | 1 | 0.5165 | 0.3579 | 0.2300 | 0.3318 |
| A — No signal | 2 | 0.5000 | 0.2493 | 0.0747 | 0.2724 |
| B — Calibrated confidence | 2 | 0.6917 | 0.3758 | 0.0596 | 0.1533 |
| C — Failure Memory | 2 | 0.5373 | 0.2830 | 0.2455 | 0.2379 |
| A — No signal | 3 | 0.5000 | 0.2010 | 0.0350 | 0.2091 |
| B — Calibrated confidence | 3 | 0.7208 | 0.3377 | 0.0622 | 0.1045 |
| C — Failure Memory | 3 | 0.4729 | 0.1966 | 0.2963 | 0.2178 |
| A — No signal | 4 | 0.5000 | 0.3330 | 0.1097 | 0.3721 |
| B — Calibrated confidence | 4 | 0.6251 | 0.4191 | 0.1537 | 0.2550 |
| C — Failure Memory | 4 | 0.5226 | 0.3580 | 0.2161 | 0.3271 |
| A — No signal | 5 | 0.5000 | 0.2243 | 0.0223 | 0.2027 |
| B — Calibrated confidence | 5 | 0.6628 | 0.3207 | 0.0457 | 0.1444 |
| C — Failure Memory | 5 | 0.5160 | 0.2354 | 0.2627 | 0.2189 |
| A — No signal | 42 | 0.5000 | 0.3333 | 0.0620 | 0.2660 |
| B — Calibrated confidence | 42 | 0.6289 | 0.4164 | 0.1206 | 0.2453 |
| C — Failure Memory | 42 | 0.5193 | 0.3519 | 0.1916 | 0.3264 |

No run was excluded, rerun, or omitted. All 6 seeds × 3 baselines = 18 rows are exactly what `experiments/results/phase3_1/per_seed_results.csv` contains.

### Aggregate (mean, std, 95% Student-t CI across the 6 seeds)

| Baseline | AUROC | AUPRC | ECE | AURC (lower better) |
|---|---|---|---|---|
| A — No signal | 0.5000 ± 0.0000 [0.5000, 0.5000] | 0.2806 ± 0.0630 [0.2145, 0.3466] | 0.0653 ± 0.0327 [0.0310, 0.0997] | 0.2699 ± 0.0623 [0.2045, 0.3354] |
| B — Calibrated confidence | **0.6599 ± 0.0395 [0.6185, 0.7013]** | **0.3835 ± 0.0463 [0.3349, 0.4320]** | 0.0823 ± 0.0442 [0.0359, 0.1286] | **0.1941 ± 0.0680 [0.1227, 0.2655]** |
| C — Failure Memory | 0.5141 ± 0.0217 [0.4914, 0.5368] | 0.2971 ± 0.0700 [0.2237, 0.3706] | 0.2404 ± 0.0367 [0.2019, 0.2788] | 0.2767 ± 0.0572 [0.2166, 0.3367] |

**Baseline C's 95% CI for AUROC, `[0.4914, 0.5368]`, contains 0.5001 — the theoretical no-discrimination value — for every one of the 6 predetermined seeds' aggregate.** This is the single most important number in this report.

### Precision / Recall at predetermined coverage operating points (mean across 6 seeds)

| Coverage | A precision / recall | B precision / recall | C precision / recall |
|---:|---|---|---|
| 5% | 0.2622 / 0.0480 | **0.4356 / 0.0795** | 0.3211 / 0.0570 |
| 10% | 0.2572 / 0.0935 | **0.4400 / 0.1619** | 0.3167 / 0.1126 |
| 20% | 0.2631 / 0.1898 | **0.4156 / 0.3024** | 0.3100 / 0.2202 |
| 50% | 0.2711 / 0.4880 | **0.3783 / 0.6849** | 0.2900 / 0.5144 |

C is numerically above A at every coverage point here, a smaller and less consistent gap than AUROC's near-total overlap with 0.5 would suggest — read this table as a secondary, more prevalence-sensitive view, not as contradicting the AUROC finding (see §11).

### Bootstrap CI, primary seed 42 only (2000 resamples, 95%, method in §5b)

| Baseline | AUROC point [95% CI] | AUPRC point [95% CI] |
|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.3333 [0.3160, 0.3503] |
| B — Calibrated confidence | 0.6289 [0.6069, 0.6484] | 0.4164 [0.3905, 0.4438] |
| C — Failure Memory | 0.5193 **[0.4969, 0.5413]** | 0.3519 [0.3287, 0.3782] |

Consistent with the cross-seed result: even within a single fixed test set, Failure Memory's AUROC confidence interval spans 0.5.

### Was the Phase 2 baseline reproducible?

**Yes, directionally, and the new protocol sharpens rather than contradicts it.** Phase 2's finding (`PHASE2_REPORT.md` §11) was that Failure Memory's risk score correlated with actual incorrectness at only `0.031` (Pearson), versus confidence's `0.200`, and that blending risk into confidence made matched-coverage selective risk *worse*, not better. Phase 3.1's AUROC-based, multi-seed, confidence-interval-backed protocol reproduces the same qualitative ordering (B strictly best on every metric; C statistically indistinguishable from A on the prevalence-independent AUROC metric) — and additionally shows this is stable across 6 independent seeds, not an artifact of the original seed=42 draw.

## 11. Validity Issues

- **Synthetic data only** — this evaluates one specific synthetic regime-drift generator, not real workload data. No generalization claim beyond this benchmark is made or implied.
- **AUROC vs AUPRC/precision-recall tension** — Failure Memory's AUROC is statistically indistinguishable from the no-signal baseline, but its AUPRC and coverage-level precision/recall are consistently, if modestly, above the no-signal baseline's. This is not a contradiction (AUPRC/precision are prevalence-sensitive and can shift with class balance in ways AUROC does not), but it means the honest summary is "very weak, inconsistent signal, not conclusively zero" rather than "provably zero." Phase 3.2 should not treat AUROC alone as the final word.
- **Regime 1/2 are not a true model-selection validation set** — see §3. No hyperparameter or representation choice was tuned against them in Phase 2 or here; this is a structural note for Phase 3.2, not a flaw in Phase 3.1 itself.
- **Leakage audit depth** — full structural checks ran for seed 42 in detail and were additionally spot-checked across several small-scale seeds via the pytest suite (§4), but were not independently re-run as the full standalone script for all 6 protocol seeds.
- **ECE on a non-probabilistic score (Baseline C)** is reported despite Failure Memory's risk output never having been fit as a calibrated probability — the resulting large ECE (~0.24) should be read as "this score is far from a calibrated probability," which is expected, not as evidence of a broken calibration *procedure* (there isn't one to break).
- **No real label-latency / temporal-forecast modeling** — see §1's "gap" discussion. This benchmark cannot, as constructed, answer whether failure memory could anticipate a failure before it happens; it only measures same-instant failure classification.
- **AURC's coverage grid starts at 5%, not 0%** — inherited from the unmodified Phase 2 harness; the reported AURC is an approximation over `[0.05, 1.0]`, stated explicitly rather than silently treated as the full `[0, 1]` integral.

## 12. Decision Readiness

**Is the evaluation protocol ready for Phase 3.2? Yes, with the caveats in §11 carried forward explicitly.**

The protocol is deterministic, leakage-checked (7 checks, all passed, with runtime evidence and regression tests), reports honest uncertainty via two distinct, correctly-labeled methods, defines operating points before touching test results, and reproduces Phase 2's qualitative finding with substantially more rigor (multi-seed, AUROC/AUPRC/ECE/AURC, confidence intervals) rather than contradicting or "fixing" it.

**Is Phase 3.2 (improving Failure Memory) scientifically justified by what Phase 3.1 found? Not yet, in the sense of "the current representation is worth tuning further."** The evidence says the current KMeans/PCA/Gaussian-kernel representation carries a AUROC statistically indistinguishable from no signal, replicated across 6 seeds and within-seed bootstrap. Per the Phase 3.1 brief's own instruction, this document does not recommend proceeding automatically into representation changes — that decision belongs to whoever reads this report next, informed by the fact that any future representation change should be judged against this exact frozen protocol (same seeds, same metrics, same leakage checks) to be comparable at all.


---

<a id="phase3-2-representation-experiments"></a>
# PHASE3 2 REPRESENTATION EXPERIMENTS
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md`  
**Role:** Phase 3.2 representation experiments (synthetic data).

# Phase 3.2 — Controlled Failure Representation Experiments

Status: complete. Stops here — no Phase 3.3 work performed. Reproduce with:

```bash
python benchmarks/phase3_2_evaluate.py
python -m pytest tests/ -v
```

Nothing under `configs/phase3_1_protocol.json`, `src/evaluation/{metrics,bootstrap,protocol}.py`, `benchmarks/phase3_1_evaluate.py`, `src/pipeline_builder.py`, or `src/failure_memory/` was modified. New code lives in `src/evaluation/representations.py` and `benchmarks/phase3_2_evaluate.py`, and is imported nowhere outside evaluation/tests.

---

## 1. Research Question

Phase 3.1 found the Phase 2 Failure Memory representation (PCA → 3-cluster KMeans → Gaussian-kernel similarity) statistically indistinguishable from a no-signal baseline (AUROC 95% CI `[0.4914, 0.5368]`, spanning 0.5, across 6 seeds). Phase 3.1 also identified a plausible mechanism: feature distributions are stable across regimes while the feature→label decision boundary drifts, so a representation built on feature-space proximity to a small number of failure cluster centroids has no statistical reason to transfer to a rotated boundary.

**Question**: is that poor result caused by the *representation* (PCA + coarse 3-centroid clustering), or is historical failure information fundamentally uninformative for this task? A small, predetermined set of alternative representations is tested against the same frozen protocol to find out.

## 2. Hypotheses

- **H1**: the current feature-space representation is poorly matched to regime drift, and a representation incorporating additional failure-history information (not just distance to 3 coarse centroids) may provide stronger transferable failure-risk signal.
- **H0**: alternative representations do not provide meaningful predictive improvement over the Phase 2 Failure Memory baseline under the frozen evaluation protocol.

Both are evaluated without an expectation that H1 wins — see §9 for how the actual results split between the two candidates.

## 3. Candidate Representations

| Candidate | What it is | Why it was selected |
|---|---|---|
| **A (control)** | Phase 2's unmodified `FailureMemory`: PCA(2) → KMeans(3) → Gaussian-kernel similarity to nearest centroid | The official Phase 3.1 result. Not reimplemented — the actual `src.failure_memory.memory.FailureMemory` object is used, exactly as Phase 3.1 used it. |
| **B — raw structured features** | Same KMeans(3) + Gaussian-kernel mechanism as the control, but clustering directly on `[f1..f5, confidence_signal, margin]` (7-dim) instead of `[pca0, pca1, confidence_signal, margin]` (4-dim) | Isolates one question: is PCA destroying information the clustering mechanism could otherwise use? Everything else (n_clusters, kernel width, downstream formula) held identical to the control. No extra normalization was added — `f1..f5 ~ N(0,I)` in every regime by the generator's own construction (independently confirmed in the Phase 3.1 leakage audit), so raw features are already unit-scale; introducing a scaler would be an unjustified transformation per the Phase 3.2 brief. |
| **C — failure-history features** | 3 explicit statistics — (1) distance to the k=5th nearest logged historical failure, (2) count of historical failures within a fixed radius (local density), (3) mean calibrated confidence of the k nearest historical failures — fed into a `LogisticRegression` | Tests whether a continuous, less-lossy summary of the failure log (versus 3 coarse centroids) carries more signal. All 3 features are computable at prediction time from information already available (raw context + the historical failure log); none uses the true label of the sample being scored. |
| **D — temporal/recency** | Not executed — see §3b | Investigated first; the benchmark does not support it validly (below). |

No other representations were tried. No hyperparameter sweep was run over Candidate B/C's parameters (`n_clusters=3` for B, matching the control exactly; `k_neighbors=5` for C, a single round-number choice made before any evaluation, not selected by trying several values and keeping the best).

### 3b. Candidate D — why it was not executed

Per the brief's explicit instruction to check before fabricating a temporal signal: `src/data/synthetic.py::StreamSample` has **no timestamp field** (`context`, `label`, `regime` only), and `generate_regime_stream` builds each regime's `X`/`p`/`y` via single vectorized `rng` calls, then appends samples in a plain index loop — row order is array index, not elapsed time, and carries no sequential dependence between consecutive samples (confirmed by reading the generator directly, reproduced as `benchmarks/phase3_2_evaluate.py::candidate_d_temporal_analysis()`, and covered by `tests/integration/test_phase3_2_pipeline.py::test_candidate_d_reports_negative_finding_not_fabricated_results`).

**Conclusion, as required by the brief: "Temporal representation cannot be validly evaluated under the current benchmark."** A controlled temporal extension (real timestamps, drift that evolves continuously rather than only at fixed regime boundaries) would be needed first — that is a benchmark-design requirement for a future phase, not something Phase 3.2 introduces.

### 3c. Alternative clustering method (brief §4) — not added

The brief authorizes testing one clustering alternative to KMeans, but only if justified by the representation experiments. Candidate C's result (§9) shows the effective fix was **avoiding lossy compression into a small fixed number of cluster centroids at all** — moving to a continuous k-NN-based local density/distance summary, not swapping which clustering algorithm produces the centroids. Candidate B (same KMeans mechanism, different input space) shows only a marginal, largely-not-significant change from the control (§9), which is further evidence the *clustering step itself* (rather than the specific algorithm) is where information is lost. Testing e.g. DBSCAN or a Gaussian mixture in place of KMeans would probe a highly similar hypothesis to what Candidate C already resolved. Per the brief's "do not add one merely for completeness," **no additional clustering algorithm was evaluated.**

## 4. Data and Fitting Boundaries

| Component | Fit on | Notes |
|---|---|---|
| `WorkloadModel` | Regime 0 | Unchanged from Phase 2/3.1, reused via `build_system` |
| `ConfidenceCalibrator` | Regime 1 | Unchanged |
| Control (`FailureMemory`) | Regime 2 failures only | Unchanged — via `build_system` exactly as Phase 3.1 called it |
| Candidate B (`RawFeatureFailureRisk`) | Regime 2 failures only | Same failure set the control uses — regime 2 is regenerated deterministically via the same `generate_regime_stream(seed=...)` call `build_system` makes internally (byte-identical given the same seed; **not new data**), and the reconstructed failure count is asserted equal to `build_system`'s own `n_logged_failures` every run (`benchmarks/phase3_2_evaluate.py::_fit_candidates`) |
| Candidate C (`FailureHistoryRiskModel`) | k-NN reference set: regime-2 failures only. Logistic regression training set: **all** of regime 2 (successes and failures) | This is the one deliberate methodological difference from A/B, stated explicitly per the brief's requirement: regime 2 is legitimately train-side data for both framings; using its non-failure examples too (to teach the model what a *non*-risky region looks like) is a different, more supervised use of the same permitted data, not a boundary violation. |
| All candidates, test scoring | Regimes 3+4, **untouched by any `fit()` call** | Verified structurally (`tests/integration/test_phase3_2_pipeline.py::test_candidates_never_see_test_stream_during_fit`, hash-based disjointness check) and by construction (`_reconstruct_regime2` asserts every reconstructed sample has `regime == 2`) |

No candidate's hyperparameters, feature set, or fitting procedure were chosen by looking at regimes 3/4 performance. `n_clusters=3` and `k_neighbors=5` were fixed before any test-set number was computed.

## 5. Experimental Protocol

Frozen Phase 3.1 protocol, reused without modification: seeds `[1, 2, 3, 4, 5, 42]`, coverage operating points `{5%, 10%, 20%, 50%}`, metrics AUROC/AUPRC/ECE/AURC + precision/recall at each coverage point, cross-seed Student-t 95% CI, within-primary-seed (42) bootstrap 95% CI (2000 resamples, seed 0). `configs/phase3_1_protocol.json` was read (`Phase31Protocol.load()`), never edited.

**Calibration-metric discipline (brief §7)**: ECE is reported only where a representation's output has an actual probabilistic interpretation — `is_probability=True` for the no-signal baseline (a constant equal to an empirical prevalence), calibrated confidence (isotonic-fit, Phase 2), and Candidate C (fit via logistic regression against the true failure label). ECE is explicitly `null`/`n/a` for the control and Candidate B, whose Gaussian-kernel similarity output was never fit or designed to be a calibrated probability — reported as `None`, not manufactured (`src/evaluation/representations.py`'s `is_probability` flag on each class; enforced by `tests/integration/test_phase3_2_pipeline.py::test_ece_not_reported_for_non_probabilistic_representations`).

## 6. Results (per seed)

All 6 seeds × 5 representations = 30 rows, none omitted, none rerun. Full data: `experiments/results/phase3_2/per_seed_results.csv`.

| Representation | Seed | AUROC | AUPRC | ECE | AURC |
|---|---:|---:|---:|---:|---:|
| A — No signal | 1 | 0.5000 | 0.3423 | 0.0883 | 0.2973 |
| B — Calibrated confidence | 1 | 0.6302 | 0.4310 | 0.0517 | 0.2622 |
| Control — Phase 2 Failure Memory | 1 | 0.5165 | 0.3579 | n/a | 0.3318 |
| Candidate B — Raw features | 1 | 0.5031 | 0.3461 | n/a | 0.3404 |
| Candidate C — Failure history | 1 | 0.5370 | 0.3745 | 0.1594 | 0.3141 |
| A — No signal | 2 | 0.5000 | 0.2493 | 0.0747 | 0.2724 |
| B — Calibrated confidence | 2 | 0.6917 | 0.3758 | 0.0596 | 0.1533 |
| Control — Phase 2 Failure Memory | 2 | 0.5373 | 0.2830 | n/a | 0.2379 |
| Candidate B — Raw features | 2 | 0.5798 | 0.3162 | n/a | 0.2117 |
| Candidate C — Failure history | 2 | 0.6258 | 0.3407 | 0.0785 | 0.1804 |
| A — No signal | 3 | 0.5000 | 0.2010 | 0.0350 | 0.2091 |
| B — Calibrated confidence | 3 | 0.7208 | 0.3377 | 0.0622 | 0.1045 |
| Control — Phase 2 Failure Memory | 3 | 0.4729 | 0.1966 | n/a | 0.2178 |
| Candidate B — Raw features | 3 | 0.5066 | 0.2047 | n/a | 0.2016 |
| Candidate C — Failure history | 3 | 0.5668 | 0.2367 | 0.0955 | 0.1721 |
| A — No signal | 4 | 0.5000 | 0.3330 | 0.1097 | 0.3721 |
| B — Calibrated confidence | 4 | 0.6251 | 0.4191 | 0.1537 | 0.2550 |
| Control — Phase 2 Failure Memory | 4 | 0.5226 | 0.3580 | n/a | 0.3271 |
| Candidate B — Raw features | 4 | 0.5334 | 0.3690 | n/a | 0.3149 |
| Candidate C — Failure history | 4 | 0.5981 | 0.4022 | 0.1176 | 0.2643 |
| A — No signal | 5 | 0.5000 | 0.2243 | 0.0223 | 0.2027 |
| B — Calibrated confidence | 5 | 0.6628 | 0.3207 | 0.0457 | 0.1444 |
| Control — Phase 2 Failure Memory | 5 | 0.5160 | 0.2354 | n/a | 0.2189 |
| Candidate B — Raw features | 5 | 0.5251 | 0.2474 | n/a | 0.2141 |
| Candidate C — Failure history | 5 | 0.5977 | 0.2934 | 0.0860 | 0.1723 |
| A — No signal | 42 | 0.5000 | 0.3333 | 0.0620 | 0.2660 |
| B — Calibrated confidence | 42 | 0.6289 | 0.4164 | 0.1206 | 0.2453 |
| Control — Phase 2 Failure Memory | 42 | 0.5193 | 0.3519 | n/a | 0.3264 |
| Candidate B — Raw features | 42 | 0.5368 | 0.3697 | n/a | 0.3103 |
| Candidate C — Failure history | 42 | 0.5599 | 0.3783 | 0.1283 | 0.2932 |

**Candidate C (failure-history) beats the control at every one of the 6 seeds, with no exceptions** (1: 0.537 vs 0.5165; 2: 0.6258 vs 0.5373; 3: 0.5668 vs 0.4729; 4: 0.5981 vs 0.5226; 5: 0.5977 vs 0.5160; 42: 0.5599 vs 0.5193). Candidate B (raw features) beats the control at 5 of 6 seeds, essentially ties at seed 1 (0.5031 vs 0.5165 — slightly *worse*).

## 7. Aggregate Results (mean ± std, 95% Student-t CI across 6 seeds)

| Representation | AUROC | AUPRC | ECE | AURC (lower better) |
|---|---|---|---|---|
| A — No signal | 0.5000 ± 0.0000 [0.5000, 0.5000] | 0.2806 ± 0.0630 [0.2145, 0.3466] | 0.0653 [0.0310, 0.0997] | 0.2699 [0.2045, 0.3354] |
| B — Calibrated confidence | **0.6599 ± 0.0395 [0.6185, 0.7013]** | **0.3835 ± 0.0463 [0.3349, 0.4320]** | 0.0823 [0.0359, 0.1286] | **0.1941 [0.1227, 0.2655]** |
| Control — Phase 2 Failure Memory | 0.5141 ± 0.0217 [0.4914, 0.5368] | 0.2971 ± 0.0700 [0.2237, 0.3706] | n/a | 0.2767 [0.2166, 0.3367] |
| Candidate B — Raw features | 0.5308 ± 0.0233 [0.5018, 0.5598] | 0.3089 ± 0.0673 [0.2354, 0.3823] | n/a | 0.2655 [0.1997, 0.3313] |
| Candidate C — Failure history | 0.5809 ± 0.0271 [0.5472, 0.6146] | 0.3376 ± 0.0655 [0.2664, 0.4089] | 0.1109 (single-bin-diagnostic; not directly comparable to A/B's ECE — see §9) | 0.2327 [0.1642, 0.3013] |

Precision/recall at predetermined coverage points (mean across 6 seeds):

| Coverage | A | B — Confidence | Control | Candidate B — Raw | Candidate C — History |
|---:|---|---|---|---|---|
| 5% | 0.2622 / 0.0480 | **0.4356 / 0.0795** | 0.3211 / 0.0570 | 0.3456 / 0.0608 | 0.3756 / 0.0679 |
| 10% | 0.2572 / 0.0935 | **0.4400 / 0.1619** | 0.3167 / 0.1126 | 0.3522 / 0.1267 | 0.3783 / 0.1376 |
| 20% | 0.2631 / 0.1898 | **0.4156 / 0.3024** | 0.3100 / 0.2202 | 0.3197 / 0.2301 | 0.3614 / 0.2607 |
| 50% | 0.2711 / 0.4880 | **0.3783 / 0.6849** | 0.2900 / 0.5144 | 0.2971 / 0.5302 | 0.3223 / 0.5787 |

Ordering is consistent: Confidence > Candidate C (History) > Candidate B (Raw) > Control > No signal, at every coverage level, on both precision and recall.

**Within-primary-seed (42) bootstrap AUROC, 2000 resamples**: Control `[0.4969, 0.5413]` (includes 0.5); Candidate B `[0.5149, 0.5586]` (excludes 0.5); Candidate C `[0.5387, 0.5805]` (clearly excludes 0.5). Consistent with the cross-seed picture.

## 8. Comparison With Phase 3.1

- **vs. no-signal (AUROC 0.5000)**: Candidate C's 95% CI `[0.5472, 0.6146]` is clearly and entirely above 0.5 — a genuine, non-trivial discrimination signal that the Phase 3.1 control never demonstrated. Candidate B's CI `[0.5018, 0.5598]` barely clears 0.5 (lower bound 0.5018) — a much weaker, borderline claim.
- **vs. calibrated confidence (AUROC 0.6599)**: neither candidate approaches it. Candidate C closes roughly a third of the gap between no-signal (0.50) and confidence (0.66) — meaningfully better than the control's near-zero closure, but confidence remains the strongest signal by a clear margin on every metric.
- **vs. control (Phase 2 Failure Memory, AUROC 0.5141)**: Candidate C is unambiguously, consistently better (every seed, both cross-seed and within-seed intervals). Candidate B is marginally, less consistently better.

## 9. Failure Analysis

**Why did Candidate C work where the control didn't?** The control compresses the entire regime-2 failure log into 3 KMeans centroids and scores new inputs only by distance to the *nearest* of those 3 points. Candidate C instead keeps the individual failure examples and computes a k-NN-based local density/distance/confidence summary — a continuous, much less lossy description of "how surrounded by historical failures is this input," plus a supervised logistic-regression step that learns how that summary actually relates to the true failure/success label on regime 2 (rather than an unlearned, fixed-form Gaussian kernel). Both changes plausibly matter; this experiment does not cleanly separate "less lossy geometric summary" from "the fact that a supervised classifier was fit on top of it," and that is a real limitation of this comparison, not a hidden result being glossed over.

**Why did Candidate B only marginally help?** Dropping PCA alone (keeping the same lossy 3-centroid compression) barely moved the needle (control 0.5141 → 0.5308 mean AUROC). This suggests **PCA was not the primary bottleneck** — the coarse clustering step was. This directly informed the decision in §3c not to chase a different clustering algorithm: the evidence points at "too much compression," not "wrong compression algorithm."

**Is Candidate C's improvement stable and meaningful, or a fluke?** Stable: positive at all 6 seeds, cross-seed CI excludes 0.5, within-seed bootstrap CI excludes 0.5. Meaningful in the narrow sense of "a real, non-zero, reproducible signal" — yes. Meaningful in the sense of "ready to replace or augment calibrated confidence" — **no**: it remains well below confidence's AUROC (0.58 vs 0.66) and its improvement over the control, while consistent, is modest in absolute terms (+0.067 mean AUROC). A candidate moving AUROC from 0.514 to 0.525 would have been the brief's explicit example of "technically improved, practically not yet meaningful" — Candidate C's actual improvement (0.514 → 0.581) is larger than that illustrative example, which is why this report treats it as a genuine, if modest, positive finding rather than noise, but the reader should weigh "genuine and modest" rather than "solved."

**Candidate C's ECE (0.1109) is worse than confidence's (0.0823)** despite both being legitimate probabilities — the logistic regression was fit on only 3 features from a few hundred regime-2 failures and is a much simpler/less-tuned model than the calibrator; this is expected and not a contradiction of its AUROC result (ranking quality and calibration quality are different properties).

## 10. Complexity / Tradeoffs

| | Control | Candidate B (Raw) | Candidate C (History) |
|---|---|---|---|
| Additional features | — | none (same features, different transform) | 3 engineered features (k-NN distance, local density, neighbor-confidence) |
| Additional computation | — | none (removes PCA transform step, net simpler) | k-NN index build + query per prediction, O(n_failures) per query without an ANN index; plus a logistic regression fit |
| Additional parameters | — | none | `k_neighbors` (=5, fixed a priori) + logistic regression's own 3 coefficients + intercept |
| Additional dependencies | — | none (drops a dependency: PCA) | `sklearn.neighbors.NearestNeighbors`, `sklearn.linear_model.LogisticRegression` (both already transitive deps of scikit-learn, no new package) |
| Interpretability | KMeans centroid distance (already fairly opaque) | Same mechanism, easier to inspect (features are the original units, not PCA components) | More interpretable in one sense (3 named, meaningful features) but the logistic weights add a second layer versus the control's parameter-free kernel |
| Reproducibility | Deterministic given seed | Deterministic given seed | Deterministic given seed; more moving parts (2 fitted objects: NN index + classifier) than the control's 1 (KMeans) |

Per the brief's complexity principle: **Candidate C is not free** — it adds a k-NN structure and a supervised classifier where the control had one unsupervised clustering step. Given its improvement is real but modest and still far below calibrated confidence, this report does **not** recommend adopting it as a production replacement for the control on the strength of this result alone; it recommends treating it as evidence that the *representation family* (continuous failure-history statistics, not coarse clustering) is worth further, more careful investigation — see §12/Question 7.

## 11. Threats to Validity

- **Synthetic data only** — all results are specific to this regime-drift generator; no claim of generalization to real workloads is made (per the brief's explicit warning, §12 there).
- **No genuine temporal structure exists in this benchmark** — Candidate D could not be tested at all; this remains an open gap for the underlying benchmark, not something this phase's results can speak to.
- **Candidate C confounds two changes at once** (less-lossy geometric summary + a supervised-fit downstream model) — this experiment cannot attribute the improvement cleanly between the two; a cleaner ablation (e.g., a supervised classifier on the *same* PCA+centroid-distance feature the control uses, versus the same k-NN features with an unlearned heuristic combination instead of logistic regression) was not run, per the brief's instruction to keep the candidate set small and not chase an algorithm zoo.
- **ECE is not comparable across representations with different feature/model complexity** — Candidate C's 0.1109 and confidence's 0.0823 are each legitimate but reflect very different model sophistication; treat as a diagnostic per-representation number, not a ranked leaderboard entry.
- **`k_neighbors=5` was not swept** — a different fixed value might change Candidate C's result; no sweep was run (per the brief's explicit instruction against hyperparameter tuning in this phase), so this specific number is not claimed to be optimal, only "a reasonable a-priori choice that was not tuned against test performance."
- **The generalization warning applies in full**: these results describe performance under the current held-out synthetic regime evaluation (regimes 3+4 of this specific generator) — not evidence about real workload families or genuinely different distributions.

## 12. Phase 3.2 Decision

**🟡 Inconclusive** (leaning toward a real but modest signal for Candidate C; no useful signal from Candidate B).

Rationale: Candidate C demonstrates a stable, leakage-free, statistically-non-trivial improvement over the Phase 2 control (95% CI excludes 0.5 both cross-seed and within-seed, positive at every one of 6 seeds) — this is not nothing, and rules out "failure history is definitely useless" as a conclusion. But the improvement is modest in absolute terms, remains well below calibrated confidence, confounds two simultaneous representation changes, and has not been tested for practical significance beyond AUROC/AUPRC/AURC movement (e.g. no downstream decision-quality experiment). This does not meet the bar for 🟢 ("meaningful and sufficiently stable improvement" ready to act on), but it is well past 🔴 ("no useful representation found") given Candidate C's result. Candidate B alone would have been 🔴 or borderline 🟡; Candidate C's clearer result is why the phase as a whole lands at 🟡 rather than 🔴.

---

## Required Final Decision Logic

**Q1 — Did any alternative representation outperform the Phase 2 Failure Memory baseline?**
Yes. Both candidates did on mean AUROC; Candidate C's advantage is consistent and stable, Candidate B's is smaller and less consistent (worse than control at 1 of 6 seeds).

**Q2 — Is that improvement statistically and practically meaningful?**
Statistically: yes for Candidate C (CI excludes 0.5 both cross-seed and within-seed; positive at every seed). Practically: partially — real and reproducible, but modest in absolute size and far from calibrated confidence's performance; not yet meaningful enough to justify a production change.

**Q3 — Does it outperform the no-signal baseline convincingly?**
Candidate C: yes, convincingly by the AUROC-CI standard (entirely above 0.5). Candidate B: only marginally (CI lower bound 0.5018, barely above 0.5).

**Q4 — How does it compare with calibrated confidence?**
Both candidates remain clearly below calibrated confidence on every metric (AUROC 0.58/0.53 vs 0.66; AURC 0.233/0.266 vs 0.194). Calibrated confidence remains the strongest single signal found in this project to date.

**Q5 — Is the improvement stable across the six predetermined seeds?**
Candidate C: yes, positive at all 6 seeds, no reversals. Candidate B: mostly yes, one near-tie/slight-reversal at seed 1.

**Q6 — Did any candidate require test-set tuning or otherwise compromise the protocol?**
No. All fitting used only regimes 0-2; hyperparameters (`n_clusters=3` for B, matching the control; `k_neighbors=5` for C) were fixed before any test evaluation ran; verified structurally by disjointness tests (`tests/integration/test_phase3_2_pipeline.py`) and by the `_fit_candidates` assertion that reconstructed regime-2 failure counts match `build_system`'s own count.

**Q7 — Does the evidence justify another iteration?**
A narrowly-scoped one: yes, specifically to disentangle Candidate C's two confounded changes (representation richness vs. supervised fitting) with a cleaner ablation, before considering any further investment. It does **not** justify broad hyperparameter tuning, an algorithm zoo, or integrating Candidate C into any decision path — those remain out of scope until a cleaner, confirmatory result exists. This report stops here; the decision to run that next narrow experiment (or not) is left to whoever reads this, per the brief's instruction not to proceed automatically.


---

<a id="phase3-2c-candidate-ablation"></a>
# PHASE3 2C CANDIDATE ABLATION
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_2C_CANDIDATE_ABLATION.md`  
**Role:** Phase 3.2C candidate representation ablation (synthetic data).

# Phase 3.2 Follow-Up: Candidate C Ablation Study

## 1. Research Question

Phase 3.2's Candidate C (rich k-NN failure-history features → logistic
regression) beat the Phase 2 Failure Memory control at all six predetermined
seeds, with a 95% CI excluding 0.5 (AUROC = 0.5809 [0.5472, 0.6146]). But
Candidate C changed two things simultaneously relative to the control:

1. **Representation**: coarse 3-centroid KMeans summary → richer k-NN
   failure-history features.
2. **Learning mechanism**: fixed Gaussian-kernel similarity → supervised
   logistic regression.

This follow-up asks: **which of these two changes actually caused the
improvement** — the richer representation (H1), the supervised learner
(H2), their interaction (H3), or is the original result not robust to a
cleaner decomposition (H0)?

## 2. Existing Evidence (not rerun)

Copied verbatim from Phase 3.1/3.2 — these are fixed historical reference
points, not reproduced by this study:

| Representation | AUROC (mean, 95% CI) |
|---|---|
| No signal | 0.5000 |
| Phase 2 Failure Memory (control) | 0.5141 [0.4914, 0.5368] |
| Candidate B — raw-feature KMeans | 0.5308 [0.5018, 0.5598] |
| Candidate C — failure-history + LR | 0.5809 [0.5472, 0.6146] |
| Calibrated confidence | 0.6599 |

## 3. Ablation Design

All three experiments share the same 3 k-NN failure-history features from
Candidate C, unless noted otherwise:

- `knn_distance_failure` — Euclidean distance to the k-th (k=5) nearest
  logged historical failure.
- `local_failure_density` — count of logged failures within a fixed radius
  (median k-NN distance among the failure set itself).
- `confidence_of_nearest_failures` — mean calibrated confidence of the k
  nearest logged failures.

Feature computation was factored into one shared class,
`_FailureHistoryFeaturizer` (`src/evaluation/representations.py`), used by
both Experiment A and Experiment C so the two experiments are *provably*
computing identical numbers — the only thing allowed to differ between them
is how those numbers are combined into a score.

**Experiment A — rich representation, fixed/unlearned scoring**
(`FixedRuleFailureHistoryRisk`). Standardizes each of the 3 features
(scaler fit on regime-2 data only), then combines with equal (1/3) weight
and a sign fixed by the feature's own definition — never by looking at
test performance:
- `knn_distance_failure`: closer → more risk → sign −1.
- `local_failure_density`: more nearby failures → more risk → sign +1.
- `confidence_of_nearest_failures`: nearby historical failures that
  occurred at *high* confidence indicate the calibrator is fooled in this
  region → more risk → sign +1.

`score = mean(sign_i · z_i)`. This is a ranking score, not a probability
(`is_probability = False`); ECE is not reported (`N/A`), per the frozen
calibration-discipline rule. No weight, sign, or threshold was chosen after
looking at any AUROC number.

**Experiment B — old (Phase 2) representation, supervised learning**
(`Phase2RepresentationSupervisedRisk`). Reuses
`src.failure_memory.embedding.FailureEmbedder` **unmodified and imported**,
exactly as Phase 2's `FailureMemory.fit` uses it: 2-component PCA fit on
the regime-2 failure contexts only, producing a 4-dim embedding (2 PCA
components + confidence-signal + margin). That embedding is then fed into
a `LogisticRegression` with the same configuration Candidate C uses
(`max_iter=1000`), fit on all of regime 2 (successes and failures), so the
supervised-fitting convention matches Experiment C exactly and the *only*
difference between B and C is the representation.

**Experiment C — Candidate C, reproduced unchanged**
(`FailureHistoryRiskModel`). Same k=5, same feature definitions (now
delegated to the shared featurizer, computing the identical formulas that
existed before this study), same fitting data, same classifier
configuration. This is the positive control for the ablation.

No hyperparameter (k, LR parameters, scoring weights, thresholds) was
swept. No new seeds, representations, or clustering algorithms were
introduced.

## 4. Leakage Controls

- Regimes 0/1/2 are used for fitting (workload model / calibrator /
  failure-history representation & any supervised fitting); regimes 3+4
  are the untouched test stream, exactly as the frozen Phase 3.1 protocol
  defines.
- Experiment A's per-feature standardization (mean/scale) is fit only on
  the regime-2 sample set passed into `fit()` — verified by
  `test_experiment_a_standardization_fit_only_on_regime2_contexts`, which
  confirms querying an extreme out-of-distribution point does not change
  the stored mean/scale.
- Experiment B's PCA is fit only on the regime-2 *failure* contexts (not
  all of regime 2, not test data) — verified by
  `test_experiment_b_pca_fit_only_on_failure_contexts` (two different
  failure sets against the same regime-2 successes/failures produce
  different embeddings) and
  `test_standardization_and_scalers_fit_only_on_regime2` (the fitted PCA's
  `n_samples_` equals exactly the regime-2 failure count).
- `test_experiments_never_see_test_stream_during_fit` hashes every regime-2
  context and every test-stream context and asserts the two sets are
  disjoint.
- `test_experiment_a_uses_identical_features_to_candidate_c` confirms
  Experiment A and Experiment C compute byte-identical raw features for
  the same query.
- `test_experiment_c_exactly_reproduces_phase3_2_candidate_c` runs the
  original Phase 3.2 evaluator's Candidate C path and this follow-up's
  Experiment C path on the same seed/protocol and asserts identical scores
  and AUROC.
- 27 new unit/integration tests pass (`tests/unit/test_phase3_2c_ablation_representations.py`,
  `tests/integration/test_phase3_2c_ablation_pipeline.py`); all 92
  pre-existing tests continue to pass unmodified (119 total).

## 5. Results — All Seeds

| Seed | Experiment | AUROC | AUPRC | ECE | AURC |
|---|---|---|---|---|---|
| 1 | A (fixed rule) | 0.4681 | 0.3224 | N/A | 0.3698 |
| 1 | B (old repr. + LR) | 0.6325 | 0.4444 | 0.0896 | 0.2546 |
| 1 | C (control) | 0.5370 | 0.3745 | 0.1594 | 0.3141 |
| 2 | A (fixed rule) | 0.5485 | 0.2686 | N/A | 0.2265 |
| 2 | B (old repr. + LR) | 0.6875 | 0.3823 | 0.0780 | 0.1589 |
| 2 | C (control) | 0.6258 | 0.3407 | 0.0785 | 0.1804 |
| 3 | A (fixed rule) | 0.4970 | 0.1947 | N/A | 0.2041 |
| 3 | B (old repr. + LR) | 0.7106 | 0.3672 | 0.0473 | 0.1114 |
| 3 | C (control) | 0.5668 | 0.2367 | 0.0955 | 0.1721 |
| 4 | A (fixed rule) | 0.5082 | 0.3314 | N/A | 0.3331 |
| 4 | B (old repr. + LR) | 0.6188 | 0.4190 | 0.1218 | 0.2600 |
| 4 | C (control) | 0.5981 | 0.4022 | 0.1176 | 0.2643 |
| 5 | A (fixed rule) | 0.5078 | 0.2191 | N/A | 0.2192 |
| 5 | B (old repr. + LR) | 0.6547 | 0.3171 | 0.0227 | 0.1462 |
| 5 | C (control) | 0.5977 | 0.2934 | 0.0860 | 0.1723 |
| 42 (primary) | A (fixed rule) | 0.5142 | 0.3307 | N/A | 0.3205 |
| 42 (primary) | B (old repr. + LR) | 0.6249 | 0.4171 | 0.0922 | 0.2520 |
| 42 (primary) | C (control) | 0.5599 | 0.3783 | 0.1283 | 0.2932 |

No seed was rerun or omitted.

## 6. Aggregate Results (mean, std, 95% cross-seed Student-t CI)

| Experiment | AUROC | AUPRC | AURC (lower=better) |
|---|---|---|---|
| A — fixed rule | 0.5073 ± 0.0260, CI [0.4800, 0.5346] | 0.2778 ± 0.0602 | 0.2789 ± 0.0705 |
| B — old repr. + LR | 0.6548 ± 0.0371, CI [0.6159, 0.6938] | 0.3912 ± 0.0457 | 0.1972 ± 0.0658 |
| C — control | 0.5809 ± 0.0321, CI [0.5472, 0.6146] | 0.3376 ± 0.0622 | 0.2327 ± 0.0653 |

Precision/recall at fixed coverage points (mean, n=6 seeds):

| Coverage | A precision / recall | B precision / recall | C precision / recall |
|---|---|---|---|
| 5% | 0.193 / 0.034 | 0.438 / 0.081 | 0.376 / 0.068 |
| 10% | 0.236 / 0.085 | 0.427 / 0.157 | 0.378 / 0.138 |
| 20% | 0.281 / 0.200 | 0.416 / 0.303 | 0.361 / 0.261 |
| 50% | 0.291 / 0.522 | 0.377 / 0.682 | 0.322 / 0.579 |

Bootstrap CI (primary seed 42, within-seed sampling uncertainty, n=2000
resamples):

| Experiment | AUROC point estimate | Bootstrap 95% CI |
|---|---|---|
| A | 0.5142 | [0.4926, 0.5345] |
| B | 0.6249 | [0.6031, 0.6452] |
| C | 0.5599 | [0.5387, 0.5805] |

Experiment C's Experiment-level AUROC (0.5809 mean, 0.5599 at seed 42) is
identical to the originally reported Phase 3.2 Candidate C numbers to full
floating-point precision (confirmed by
`test_experiment_c_exactly_reproduces_phase3_2_candidate_c`), not merely
"close."

## 7. Comparison

- **A vs. no-signal (0.5000)**: A's CI [0.4800, 0.5346] contains 0.5 —
  statistically indistinguishable from no signal at the cross-seed level.
  One of six seeds (seed 1) is *below* 0.5.
- **A vs. Phase 2 control (0.5141 [0.4914, 0.5368])**: heavily overlapping
  CIs — A does not clearly beat the original control either.
- **B vs. Candidate C (0.5809 [0.5472, 0.6146])**: B's CI [0.6159, 0.6938]
  is entirely above C's CI, at every one of the six seeds individually
  (0.6325>0.5370, 0.6875>0.6258, 0.7106>0.5668, 0.6188>0.5981,
  0.6547>0.5977, 0.6249>0.5599). B is a clear, consistent improvement over
  the thing it is meant to be a decomposition of.
- **B vs. calibrated confidence (0.6599)**: B's CI [0.6159, 0.6938]
  contains 0.6599 — B is statistically indistinguishable from calibrated
  confidence on this benchmark, using only failure-memory information
  (the calibrator's own confidence output is not one of the two inputs to
  B's embedding beyond the derived confidence/margin features already
  present in Phase 2's embedder).

## 8. Causal Interpretation

This maps onto **Case 2** from the pre-registered decision structure:

```
Experiment A ≈ Control (no signal / Phase 2 control)
Experiment B ≈ or exceeds Candidate C
```

**The evidence supports H2 (supervised-learning effect) as the primary
driver of Candidate C's improvement, not H1 (representation effect).**

The richer k-NN failure-history representation, combined with a
non-trained, semantically-motivated scoring rule, produces essentially no
usable ranking signal (AUROC ≈ 0.51, CI crossing 0.5, one seed even below
0.5). The same three features, run through a logistic regression instead
(Experiment C = the original Candidate C), reach AUROC ≈ 0.58. But
swapping in the *old*, lossier PCA-based representation and keeping only
the supervised learner (Experiment B) does not lose the improvement — it
*exceeds* Candidate C's own result (0.65 vs. 0.58) and gets statistically
close to calibrated confidence (0.66).

This is a stronger and more specific finding than "both contribute"
(Case 3): the representation richness Candidate C added is not carrying
the signal on its own, and is not even necessary — a supervised classifier
fit on the OLD representation outperforms the supervised classifier fit on
the NEW representation. The interaction hypothesis (H3, Case 4) is not
supported either, since B alone (old representation + learning)
reproduces and exceeds the target effect without needing the richer
features at all.

This finding does **not** support treating Candidate C's specific feature
engineering as the reason failure-history information helps. It supports
treating the shift from a fixed similarity kernel to a supervised
classifier as the operative change — and suggests that shift may work even
better on the *existing*, cheaper Phase 2 representation than on the newer,
more complex one Phase 3.2 built.

## 9. Complexity

Experiment B is *simpler* than Candidate C along two axes: it reuses an
already-existing, already-tested component (`FailureEmbedder`) rather than
introducing new k-NN infrastructure (a `NearestNeighbors` index, a
density-radius computation, and 3 hand-engineered features), and it
performs *better*. If a supervised failure-risk model is worth building at
all, this ablation gives no evidence that the richer k-NN feature
engineering Candidate C introduced is worth its added complexity relative
to just fitting a classifier on the representation already in the
codebase. The complexity that *is* justified by this ablation is the shift
from an unlearned similarity kernel to a supervised classifier, which is a
small, well-understood addition (a single `LogisticRegression.fit` call on
already-available features), not the new representation infrastructure.

## 10. Threats to Validity

Carried forward unchanged from Phase 3.1/3.2, still unresolved here:

- Synthetic data only — the regime-drift generator's feature/label
  relationship is a fabricated, controlled setting, not a real workload.
- No genuine temporal structure — row order within a regime carries no
  elapsed-time semantics (confirmed again in Phase 3.2; not re-examined
  by this ablation, which does not touch Candidate D).
- No real-workload validation of any of these representations or
  classifiers.
- Current benchmark limitations (regime sizes, coverage grid, calibration
  bin count) are all inherited from the frozen Phase 3.1 protocol and were
  not re-examined here, by design.
- This ablation adds one further caveat specific to itself: Experiment B's
  apparent superiority over Candidate C is measured on the same synthetic
  benchmark that produced Candidate C's original result. Neither Candidate
  C nor Experiment B has been validated on non-synthetic data — the
  "supervised learning helps" finding is a finding about this benchmark,
  not a general claim about failure-history modeling.

## 11. Decision

**🟢 Clear mechanism.** The ablation isolates the two changes cleanly:
Experiment A (representation alone) collapses to no-signal levels at every
seed-level comparison, Experiment B (learning alone, old representation)
reproduces and exceeds Candidate C's effect at every one of the six
seeds, and Experiment C exactly reproduces the original Phase 3.2 result
bit-for-bit. This is not a "higher AUROC therefore green" call — it is
green because the pattern across A/B/C, checked seed-by-seed rather than
only in aggregate, unambiguously attributes the effect to the supervised
classifier rather than the richer representation, without needing an
interaction explanation.

## 12. Final Questions

1. **Can Candidate C's improvement be reproduced?** Yes, exactly — bit-for-bit identical to the original Phase 3.2 numbers.
2. **Does the richer representation help without supervised learning?** No. Experiment A (AUROC 0.5073, CI [0.4800, 0.5346]) is statistically indistinguishable from no signal, with one seed below 0.5.
3. **Does supervised learning help without the richer representation?** Yes, substantially. Experiment B (AUROC 0.6548, CI [0.6159, 0.6938]) exceeds Candidate C itself, at all six seeds.
4. **Do both components contribute?** Not in an additive/necessary sense. The representation's contribution appears to be near zero on its own; the learning mechanism appears sufficient by itself (and works better on the older, simpler representation than the newer one).
5. **Which component appears primarily responsible?** The supervised-learning mechanism (H2).
6. **Is the effect stable across all six predetermined seeds?** Yes for B vs. C — B beats C at every seed individually, not just in aggregate. A's near-null result is also consistent across seeds (only seed 1 dips below 0.5, well within CI).
7. **Does it remain meaningfully better than the Phase 2 control (0.5141)?** Experiment B, yes, clearly (0.6548 vs. 0.5141, non-overlapping CIs). Experiment A, no.
8. **How large is the remaining gap to calibrated confidence (0.6599)?** For Experiment B, negligible — 0.0051 AUROC, well within B's own CI, which contains 0.6599.
9. **Is the added complexity justified by the observed gain?** Not the k-NN representation's complexity specifically — Experiment B gets a larger gain with less new machinery by reusing the existing PCA-based representation. The supervised-learning addition itself is simple and appears justified.
10. **What should the next research step be?** Investigate why a supervised classifier on the OLD (PCA) representation outperforms one on the NEW (k-NN) representation — e.g. whether the k-NN features are noisier, redundant with what PCA already captures, or whether the fixed k=5 is a poor fit for this representation specifically (note: this would be a new, explicitly scoped experiment, not an unscoped hyperparameter sweep). Per the stop condition below, this is a recommendation for a future phase, not something this study proceeds to.

## Stop Condition

This ablation study stops here. No integration into autonomous
decision-making, no recovery-action wiring, no deployment, no
hyperparameter optimization, no temporal modeling, no real-workload
testing, no additional clustering algorithms, and no automatic
continuation into a "Phase 3.3" were performed. `src/decision/`,
`src/api/`, `src/pipeline_builder.py`, `src/failure_memory/`, and
`configs/phase3_1_protocol.json` were not modified.


---

<a id="phase3-3-generalization"></a>
# PHASE3 3 GENERALIZATION
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_3_GENERALIZATION.md`  
**Role:** Phase 3.3 generalization evaluation (synthetic data).

# Phase 3.3: Generalization and Robustness Validation

## 1. Research Question

Phase 3.2C identified the Supervised Failure-Risk candidate (existing Phase
2 PCA representation + logistic regression) as the source of Candidate C's
improvement, reaching AUROC 0.6548 [0.6159, 0.6938] on the frozen Phase
3.1/3.2C benchmark — statistically indistinguishable from calibrated
confidence (0.6599 [0.6185, 0.7013]). That result was discovered and
measured on a single benchmark condition (regimes 3+4 at the training
drift strength). This phase asks: **does that signal survive evaluation on
conditions the candidate was never fit on**, without retuning it to look
good on them?

## 2. Candidate Being Tested (frozen, unmodified)

`Phase2RepresentationSupervisedRisk` (`src/evaluation/representations.py`,
unchanged since Phase 3.2C):

- Representation: `src.failure_memory.embedding.FailureEmbedder` — 2-component
  PCA fit on regime-2 **failure** contexts only, producing a 4-dim
  embedding (2 PCA components + `2·|confidence−0.5|` + `|confidence−0.5|`).
- Classifier: `sklearn.linear_model.LogisticRegression(max_iter=1000,
  random_state=seed)`, fit on the embedding of **all** of regime 2
  (successes and failures), target = the sample's own failure/success
  outcome.
- No hyperparameter (PCA components, LR regularization, max_iter) was
  changed from Phase 3.2C. No new preprocessing was added. The fitting
  procedure (`_fit_frozen_candidate` in
  `benchmarks/phase3_3_generalization.py`) is called **exactly once per
  seed**, before any generalization condition is evaluated, and its output
  object is reused unmodified across every condition — verified by
  `test_candidate_fit_exactly_once_and_reused_across_conditions` and
  `test_no_fit_method_called_inside_condition_loop` (AST-level check that
  `.fit(` never appears in the condition-evaluation code path).

## 3. Reading the Generator First

Before designing any "unseen condition," `src/data/synthetic.py` was read
directly (not assumed). Key facts, verified empirically (see the tests
below, not just derived from source reading):

- `generate_regime_stream(regime_sizes, drift_scale=0.35, seed)` draws a
  base weight vector `base_w`, then per regime `regime_idx`, a drift vector
  `drift ~ N(0, drift_scale·regime_idx)`, sets `w = base_w + drift`, and
  generates that regime's features `X ~ N(0, I)` and labels
  `y ~ Bernoulli(sigmoid(X·w))`.
- **`X` (the raw feature draws) does not depend on `drift_scale`.** For a
  fixed seed and `regime_sizes`, calling the generator with two different
  `drift_scale` values produces **byte-identical `X` at every regime**,
  because `rng.normal(scale=s, size=n)` draws the same number of underlying
  random variates regardless of `s`, so the RNG stream position — and
  hence every subsequent `X` draw — is unaffected by `drift_scale`. Only
  `w` (via `drift`), and therefore `y`, differs. Confirmed directly:
  `test_features_invariant_to_drift_scale_but_labels_are_not`.
- **Regime 0 (training) is fully `drift_scale`-invariant**: `regime_idx=0`
  makes `drift_scale·0 = 0` regardless of `drift_scale`, so `w = base_w`
  and both `X` and `y` are identical across every `drift_scale` value at
  regime 0. Confirmed: `test_regime0_training_data_is_fully_drift_scale_invariant`.
- `src.pipeline_builder.build_system` never exposes `drift_scale` — it
  always calls the generator with the library default (0.35). Every prior
  phase's training condition, and this phase's frozen candidate's fitting
  condition, is therefore unaffected by anything this study does.
- `configs/phase3_1_protocol.json` has no drift-related field; `drift_scale`
  was never previously fixed by any protocol document, so introducing it as
  a new, explicitly-documented axis does not conflict with anything frozen.

**Consequence for what "unseen" means here**: `drift_scale` is the only
parameter this generator exposes that produces a genuinely different
failure-generating relationship without being fabricated. Varying it at the
test regimes (3+4) while regimes 0/1/2 stay at the fixed training value
produces a condition where the **input distribution is unchanged** but the
**decision boundary — and therefore which inputs are failures — differs**
from anything the model fit on. This is a **concept-drift generalization
test under a fixed covariate distribution**, not a covariate-shift test;
the report does not claim more than that. Given this, the brief's Test A
("unseen regime conditions") and Test B ("unseen drift strength") collapse
into the same mechanism for this generator — there is no second, independent
lever available without modifying the frozen generator, which this phase
does not do.

## 4. Generalization Conditions (fixed before running any evaluation)

| id | kind | `drift_scale` | rationale |
|---|---|---|---|
| `original_benchmark` | in-distribution reference | 0.35 | `system.test_stream` reused verbatim — the unmodified Phase 3.1/3.2C benchmark. Not regenerated. |
| `unseen_weaker_drift` | unseen | 0.175 (0.5× training) | Decision boundary at test regimes rotated *less* from the training boundary than the model ever fit on. |
| `unseen_stronger_drift` | unseen | 0.70 (2× training) | Decision boundary at test regimes rotated *more* from the training boundary than the model ever fit on. |

The 0.5×/2× factors were chosen for interpretability (symmetric on a log
scale around the training value) before any AUROC was computed under
either condition, and were not adjusted afterward. No other drift value
was tried and discarded.

Sanity check confirming the mechanism behaves as expected (not tuned, just
verified): frozen workload-model failure rate on regime 3+4 at seed 42 is
25.3% at weaker drift, 33.3% at the training drift (matches the original
benchmark exactly), and 42.4% at stronger drift — monotonically increasing
with `drift_scale`, as the boundary-rotation mechanism predicts.

## 5. Data/Fitting Boundaries

For every seed:

```
Regime 0 (train)   -> workload model            [fixed drift_scale=0.35, unchanged]
Regime 1 (calib)   -> confidence calibrator      [fixed drift_scale=0.35, unchanged]
Regime 2 (log/fit) -> original Failure Memory (C) and Supervised Failure-Risk (D)
                       [fixed drift_scale=0.35, unchanged — fit ONCE]
Regimes 3+4        -> evaluation ONLY, one independently-generated stream per
                       condition (original_benchmark reuses system.test_stream;
                       unseen conditions call generate_regime_stream with a
                       different drift_scale) — NEVER used for fitting anything.
```

No model is refit, re-selected, or re-thresholded per condition. Baseline
A's prevalence constant is computed once from regime 2 at the training
drift and reused unchanged across every condition (never derived from test
data). `_assert_no_regime2_leakage` hashes every regime-2 context and every
condition's test contexts and asserts the sets are disjoint, run inside
every seed's evaluation (not just as a one-off audit script). No separate
validation split was needed beyond the existing regime-1 calibration step,
because no model selection or hyperparameter choice happens anywhere in
this phase — the candidate is entirely frozen from Phase 3.2C.

## 6. Experimental Protocol

- Seeds: `[1, 2, 3, 4, 5, 42]` (frozen `configs/phase3_1_protocol.json`,
  unchanged; all six reported, none dropped or added).
- Metrics: AUROC, AUPRC, AURC, ECE (only for genuine probabilities —
  Failure Memory's similarity score is never reported as ECE, per the
  Phase 3.1/3.2/3.2C calibration-discipline rule), precision/recall at
  fixed coverage 5%/10%/20%/50%.
- Cross-seed CI: Student-t 95% interval over the 6 per-seed point
  estimates (reused `_t_interval` from `benchmarks/phase3_1_evaluate.py`,
  not reimplemented).
- Within-seed CI: nonparametric percentile bootstrap (n=2000 resamples) at
  primary seed 42, reused `bootstrap_ci` unchanged.
- Baselines evaluated under every condition: A (no signal), B (calibrated
  confidence), C (original Phase 2 Failure Memory), D (Supervised
  Failure-Risk candidate).

## 7. Results — All Seeds, All Conditions

AUROC / AUPRC / AURC per seed (ECE omitted from this table for space; C's
ECE is always `N/A` — non-probabilistic score — and is reported in the
full JSON):

| Seed | Condition | A | B (confidence) | C (orig. memory) | D (candidate) |
|---|---|---|---|---|---|
| 1 | original | 0.5000 | 0.6302 | 0.5165 | 0.6325 |
| 1 | weaker | 0.5000 | 0.6655 | 0.5105 | 0.6721 |
| 1 | stronger | 0.5000 | 0.5790 | 0.5174 | 0.5789 |
| 2 | original | 0.5000 | 0.6917 | 0.5373 | 0.6875 |
| 2 | weaker | 0.5000 | 0.7437 | 0.5503 | 0.7329 |
| 2 | stronger | 0.5000 | 0.6200 | 0.5335 | 0.6197 |
| 3 | original | 0.5000 | 0.7208 | 0.4729 | 0.7106 |
| 3 | weaker | 0.5000 | 0.7595 | 0.4951 | 0.7527 |
| 3 | stronger | 0.5000 | 0.6325 | 0.4746 | 0.6262 |
| 4 | original | 0.5000 | 0.6251 | 0.5226 | 0.6188 |
| 4 | weaker | 0.5000 | 0.6873 | 0.5425 | 0.6814 |
| 4 | stronger | 0.5000 | 0.5841 | 0.4936 | 0.5794 |
| 5 | original | 0.5000 | 0.6628 | 0.5160 | 0.6547 |
| 5 | weaker | 0.5000 | 0.6882 | 0.5197 | 0.6837 |
| 5 | stronger | 0.5000 | 0.6303 | 0.5112 | 0.6242 |
| 42 (primary) | original | 0.5000 | 0.6289 | 0.5193 | 0.6249 |
| 42 (primary) | weaker | 0.5000 | 0.6681 | 0.5260 | 0.6668 |
| 42 (primary) | stronger | 0.5000 | 0.5874 | 0.5193 | 0.5838 |

No seed or condition was omitted or rerun. Note seed 3's original Failure
Memory (C) AUROC is *below* 0.5 (0.4729) in all three conditions — a
failure mode discussed in section 10.

`original_benchmark` values above are, by construction, identical to
Phase 3.2C's original benchmark and Experiment B numbers (confirmed by
`test_candidate_d_matches_phase3_2c_experiment_b_on_original_benchmark` /
`test_experiment_c_exactly_reproduces_phase3_2_candidate_c`-style checks).

## 8. Aggregate Results (mean, 95% cross-seed Student-t CI)

| Condition | A | B (confidence) | C (orig. memory) | D (candidate) |
|---|---|---|---|---|
| original_benchmark | 0.5000 [0.5000,0.5000] | 0.6599 [0.6185,0.7013] | 0.5141 [0.4914,0.5368] | 0.6548 [0.6159,0.6938] |
| unseen_weaker_drift | 0.5000 [0.5000,0.5000] | 0.7021 [0.6602,0.7439] | 0.5240 [0.5026,0.5454] | 0.6983 [0.6609,0.7356] |
| unseen_stronger_drift | 0.5000 [0.5000,0.5000] | 0.6055 [0.5796,0.6314] | 0.5083 [0.4862,0.5303] | 0.6021 [0.5773,0.6268] |

AUPRC / AURC (mean):

| Condition | B AUPRC / AURC | D AUPRC / AURC |
|---|---|---|
| original | 0.3835 / 0.1941 | 0.3912 / 0.1972 |
| weaker | 0.3474 / 0.1310 | 0.3558 / 0.1324 |
| stronger | 0.4226 / 0.2859 | 0.4265 / 0.2881 |

Bootstrap 95% CI, primary seed 42 (n=2000 resamples):

| Condition | B AUROC (point, CI) | D AUROC (point, CI) |
|---|---|---|
| original | 0.6289 [0.6069, 0.6484] | 0.6249 [0.6031, 0.6452] |
| weaker | 0.6681 [0.6473, 0.6886] | 0.6668 [0.6453, 0.6875] |
| stronger | 0.5874 [0.5672, 0.6071] | 0.5838 [0.5631, 0.6039] |

Precision/recall at fixed coverage (mean; B vs. D):

| Condition | Coverage | B precision/recall | D precision/recall |
|---|---|---|---|
| original | 5% | 0.436 / 0.080 | 0.438 / 0.081 |
| original | 10% | 0.440 / 0.162 | 0.427 / 0.157 |
| original | 20% | 0.416 / 0.302 | 0.416 / 0.303 |
| original | 50% | 0.378 / 0.685 | 0.377 / 0.682 |
| weaker | 5% | 0.393 / 0.089 | 0.390 / 0.090 |
| weaker | 10% | 0.398 / 0.182 | 0.389 / 0.178 |
| weaker | 20% | 0.376 / 0.342 | 0.383 / 0.349 |
| weaker | 50% | 0.336 / 0.757 | 0.333 / 0.751 |
| stronger | 5% | 0.473 / 0.068 | 0.468 / 0.067 |
| stronger | 10% | 0.476 / 0.138 | 0.457 / 0.132 |
| stronger | 20% | 0.452 / 0.260 | 0.450 / 0.258 |
| stronger | 50% | 0.423 / 0.606 | 0.422 / 0.605 |

## 9. Baseline Comparison

- **D vs. A (no signal)**: D's CI is entirely above 0.5 in every condition
  (lowest bound 0.5773 at stronger drift). Never approaches, let alone
  crosses, no-signal.
- **D vs. C (original Failure Memory)**: D's CI is entirely above C's CI in
  every condition (e.g. stronger drift: D [0.5773, 0.6268] vs. C
  [0.4862, 0.5303] — no overlap). This holds at every individual seed too,
  not just in aggregate.
- **D vs. B (calibrated confidence) — the central comparison**: D tracks B
  extremely closely in every condition, at every seed. Aggregate gap
  (B − D): +0.0051 (original), +0.0038 (weaker), +0.0034 (stronger) — D is
  consistently *very slightly* below confidence, never meaningfully behind,
  and their CIs overlap almost completely in all three conditions. At the
  per-seed level, D exceeds B once (seed 1, both original and weaker
  conditions by ~0.002–0.007) and is otherwise fractionally below B by
  0.001–0.01 AUROC. No seed or condition shows a reversal large enough to
  suggest the ranking is unstable — the D/B gap itself is stable, not the
  identity of which one wins.

## 10. Failure/Degradation Analysis

Degradation relative to the original benchmark (`original − condition`,
positive = the original benchmark was easier):

| Baseline | original → weaker (improvement) | original → stronger (degradation) |
|---|---|---|
| B (confidence) | −0.0422 (improves) | +0.0544 |
| D (candidate) | −0.0435 (improves) | +0.0527 |
| C (orig. memory) | −0.0099 (improves) | +0.0058 |

D's degradation under stronger drift (0.0527) is essentially identical to
B's (0.0544) — the candidate does not degrade faster than the strongest
available signal. No robustness threshold was defined in advance beyond
"does not fall to no-signal and does not fall below the original Failure
Memory" (section 7 of the brief) — that threshold is met in every
condition, so no separate acceptable/unacceptable cutoff was needed for
interpretation.

**Where the mechanism does show a weak point**: C (original Failure
Memory) drops *below* 0.5 at seed 3 in all three conditions (0.4729,
0.4951, 0.4746) — a case where the Phase 2 mechanism actively
anti-correlates with failures for one specific train/test split, regardless
of drift condition. D does not exhibit this at seed 3 (0.7106, 0.7527,
0.6262 — its best-performing seed, if anything). This is reported as an
observation about C's instability across seeds, not something Phase 3.3
was designed to explain further; no seed-specific rescue was attempted, per
the brief's stop condition.

No condition caused D's calibration (ECE) to blow up disproportionately to
B's: ECE(D) tracks ECE(B) closely in every condition (original: 0.075 vs.
0.082; weaker: 0.049 vs. 0.039; stronger: 0.131 vs. 0.150) — both get worse
under stronger drift (as expected: the calibrator itself was never refit
for the drifted conditions, so both scores' calibration degrades together),
neither collapses independently of the other.

Precision at low coverage (5%/10%) — the operating region most relevant to
"only act on the highest-risk flagged fraction" — tracks B within ~0.01–0.02
absolute precision in every condition; recall likewise tracks within
~0.005–0.01. No condition produces a precision/recall collapse specific to
D that spares B.

## 11. Threats to Validity

- Synthetic data throughout — the regime-drift generator's feature/label
  relationship is a controlled, fabricated construction, not a real
  workload.
- No genuine temporal structure (unchanged finding from Phase 3.2:
  `generate_regime_stream` draws each regime via vectorized, non-sequential
  RNG calls; row order carries no elapsed-time semantics).
- No real-workload validation of the candidate, the original Failure
  Memory, or calibrated confidence.
- **Specific to this phase**: the "unseen" conditions vary only the
  label-generating decision boundary (`drift_scale`) while holding the
  input feature distribution `X` fixed — a deliberate, documented,
  generator-supported design choice (section 3), but it means this study
  demonstrates robustness to *concept drift under a fixed covariate
  distribution*, not to *covariate shift* (a genuinely different input
  population). The current generator does not expose a mechanism for
  covariate shift without redesigning it, which this phase explicitly does
  not do (see section 15 of the brief; no benchmark modification was made).
- Only two non-training drift magnitudes were tested (0.5× and 2× the
  training value); this characterizes robustness at those two points, not
  a continuous robustness curve.

## 12. Decision

**🟢 Generalization supported** (within the explicitly synthetic, fixed-
covariate-distribution scope documented above). Across all six
predetermined seeds and both predetermined unseen drift conditions, the
Supervised Failure-Risk candidate: (a) remained clearly above the no-signal
baseline, (b) remained clearly above the original Phase 2 Failure Memory,
and (c) tracked calibrated confidence within a small, stable margin that
never widened meaningfully as drift strength moved away from the training
condition in either direction. Degradation under stronger drift was
essentially the same magnitude for the candidate as for calibrated
confidence itself — the candidate is not more fragile than the strongest
available signal. This is not evidence of real-workload generalization,
production readiness, or that failure prediction is solved — see section
14 of the brief and the "final questions" below for the precise, bounded
claim this evidence supports.

## 13. Final Questions

1. **What exactly counts as an unseen condition in this experiment?**
   Regimes 3+4 generated at a `drift_scale` (0.175 or 0.70) different from
   the training value (0.35) that regimes 0/1/2 always use — verified to
   change only the failure-generating decision boundary, not the input
   feature distribution.
2. **Was that definition fixed before evaluating the results?** Yes. The
   two multiplicative factors (0.5×, 2×) were fixed in
   `benchmarks/phase3_3_generalization.py`'s `CONDITIONS` list before any
   AUROC under either condition was computed; no other drift value was
   tried and discarded.
3. **Did the candidate remain above the no-signal baseline?** Yes, at
   every seed and every condition, with CIs entirely above 0.5.
4. **Did it remain above the original Failure Memory baseline?** Yes, at
   every seed and every condition, with non-overlapping CIs.
5. **How did it compare with calibrated confidence?** Statistically
   indistinguishable, tracking within 0.003–0.005 AUROC in aggregate across
   all three conditions; overlapping CIs throughout.
6. **How stable was it across seeds?** Stable — D beats C and A at every
   one of the 6 seeds × 3 conditions = 18 individual comparisons, and its
   gap to B never widens or reverses direction in a way inconsistent with
   sampling noise.
7. **How much did performance degrade from the original benchmark?**
   ≈0.053 AUROC under 2× drift (comparable to confidence's ≈0.054); *improved*
   by ≈0.044 under 0.5× drift (also comparable to confidence's ≈0.042).
8. **Which conditions caused failure or degradation?** Stronger drift
   (2×) degrades all signals roughly equally; no condition caused the
   candidate specifically (relative to confidence) to fail. The original
   Failure Memory baseline (C) showed an unrelated failure mode — dropping
   below 0.5 at seed 3 in every condition — not shared by the candidate.
9. **Did any unseen condition accidentally influence model fitting or
   selection?** No — verified structurally (AST check that no `.fit()`
   call exists in the condition-evaluation path) and empirically (the
   candidate's logistic-regression coefficients are identical before and
   after scoring all three conditions), in addition to the leakage-hash
   check run inside every seed's evaluation.
10. **Does the evidence support generalization, or only benchmark-specific
    performance?** Within this synthetic benchmark's concept-drift axis,
    it supports generalization — not merely a coincidence of the exact
    training drift value. It does not speak to covariate-shift
    generalization or real-workload generalization, which this benchmark
    cannot test (section 11).
11. **Is the current benchmark sufficient for stronger generalization
    claims?** No. It can vary decision-boundary strength but not the input
    feature distribution, workload semantics, or temporal structure. A
    stronger claim would require a benchmark redesign, which is out of
    scope for this phase.
12. **What is the scientifically justified next step?** Either (a) extend
    the synthetic benchmark to support genuine covariate shift (a new,
    explicitly-scoped benchmark-design effort, not a Phase 3.3 addendum),
    or (b) begin real-workload data collection to test whether any of
    these synthetic findings — including Phase 3.2C's finding that the old
    representation outperforms the new k-NN one — hold outside simulation.
    Per the stop condition below, no such step is begun here.

## Stop Condition

This phase stops here. No integration into autonomous decision-making, no
changes to `src/decision/`, no deployment, no retraining based on these
generalization results, no hyperparameter optimization, no temporal
modeling, no real-workload data, and no automatic continuation into a
"Phase 3.4" were performed. `src/pipeline_builder.py`,
`src/failure_memory/`, `src/evaluation/representations.py`, and
`configs/phase3_1_protocol.json` were not modified.


---

<a id="phase3-4-comparison"></a>
# PHASE3 4 COMPARISON
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_4_COMPARISON.md`  
**Role:** Phase 3.4 comparison of representations/signals (synthetic data).

# Phase 3.4 — Compare Everything Against the Same Baseline

**Status: COMPLETE.** This document is the Phase 3.4 deliverable. Phase 3.4
performs **no new model fitting, training, or tuning**. It consolidates
already-frozen results from Phase 3.1, Phase 3.2, and Phase 3.2C into one
comparison, under the same protocol, evaluated on the same seeds.

Companion artifacts:
- Script: [`benchmarks/phase3_4_compare.py`](../benchmarks/phase3_4_compare.py)
- Machine-readable output: [`experiments/results/phase3_4/comparison.json`](../experiments/results/phase3_4/comparison.json)
- Tests: [`tests/integration/test_phase3_4_compare_pipeline.py`](../tests/integration/test_phase3_4_compare_pipeline.py)

---

## 1. Objective

Given everything evaluated in Phase 3.1–3.3, how do the candidate
failure-risk systems compare when evaluated under the **same frozen
protocol** and the **same evaluation criteria**? This phase does not
develop new models; it answers ten specific questions (section 8 of the
Phase 3.4 brief) about the candidates already on record.

## 2. Frozen protocol reference

`configs/phase3_1_protocol.json` (unmodified). Key values, verified
identical across every source file this comparison reads from (Phase
3.1/3.2/3.2C `per_seed_results.json` and `aggregate_results.json` `meta.protocol_config`
blocks — checked programmatically by `phase3_4_compare.load_sources`,
which raises `ProtocolDiscrepancyError` on any mismatch; none was found):

- Seeds: `[1, 2, 3, 4, 5, 42]`; primary seed `42`
- Coverage operating points: `5%, 10%, 20%, 50%`
- AURC coverage grid: 5%–100% in 5% steps
- Calibration bins: 10
- Bootstrap: 2000 resamples, percentile method, seed 0, 95% CI
- Cross-seed CI: Student-t interval over the six per-seed point estimates
- Failure definition, preprocessing, and train/test separation: unchanged
  from Phase 3.1

Additionally verified: for every seed, `n_test_samples` and
`test_failure_prevalence` are byte-identical across the Phase
3.1/3.2/3.2C result files (`_assert_test_sets_aligned`). This is what
makes per-seed comparisons across those three phases validly **paired** —
same seed + same frozen protocol + deterministic `build_system` produce
the same regime-3/4 stream and the same `y_fail` vector, so the same-seed
row from each phase scores the exact same held-out samples.

## 3. Candidates compared

| ID | Label | Source | Source key |
|---|---|---|---|
| A | No signal | Phase 3.2 | `A_no_signal` |
| B | Calibrated confidence | Phase 3.2 | `B_calibrated_confidence` |
| C | Original Phase 2 Failure Memory | Phase 3.2 | `control_phase2_failure_memory` |
| D | Candidate B — raw structured features | Phase 3.2 | `candidate_raw_features` |
| E | Candidate C — failure-history representation + supervised classifier | Phase 3.2 | `candidate_failure_history` |
| E′ | Phase 3.2C Experiment C (positive control) | Phase 3.2C | `experiment_C_control` |
| F | **Supervised Failure Risk** (Phase 3.2C Experiment B, selected candidate) | Phase 3.2C | `experiment_B_old_repr_supervised` |

**E and E′ are the same implementation, not two independent systems.**
Phase 3.2C documented Experiment C as an unmodified reproduction of Phase
3.2's Candidate C, included as that ablation's positive control. This
comparison verifies that documented claim rather than assuming it: E and
E′ produce **identical per-seed AUROC on all 6 seeds**
(`_assert_duplicate_candidates_match`, `identical: true`, no mismatches).
Wherever this report counts "how many candidates ...", E and E′ are
counted once.

No new candidate was introduced. This is exactly the set named in section
9 of the Phase 3.4 brief.

## 4. Experimental lineage of each candidate

- **A (no signal)** — Phase 3.1 baseline A, unchanged constant score
  equal to empirical failure prevalence on regime 2.
- **B (calibrated confidence)** — Phase 3.1 baseline B,
  `1 - calibrated_confidence`. The strongest established reference prior
  to Phase 3.4.
- **C (original Failure Memory)** — Phase 3.1 baseline C / Phase 3.2
  control. Unmodified Phase 2 KMeans + Gaussian-kernel similarity.
- **D (raw structured features)** — Phase 3.2 Candidate B:
  `RawFeatureFailureRisk`, KMeans directly on raw structured features
  (not a probability — `is_probability=False`).
- **E / E′ (failure-history + supervised)** — Phase 3.2 Candidate C /
  Phase 3.2C Experiment C: `FailureHistoryRiskModel`, rich k-NN
  failure-history features + logistic regression.
- **F (Supervised Failure Risk)** — Phase 3.2C Experiment B:
  `Phase2RepresentationSupervisedRisk`, the **old Phase 2 PCA
  representation** + logistic regression. Phase 3.2C's ablation isolated
  the supervised classifier (not the richer representation) as the
  mechanism that mattered, and Phase 3.3 froze this exact candidate for
  generalization testing.

## 5. Aggregate results (cross-seed, 6 seeds, Student-t 95% CI)

| Candidate | AUROC | AUPRC | AURC (↓ better) | ECE |
|---|---|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.2806 | 0.2699 | 0.0653 |
| C — Original Failure Memory | 0.5141 [0.4914, 0.5368] | 0.2971 | 0.2767 | not meaningful (similarity score) |
| D — Raw structured features | 0.5308 [0.5018, 0.5598] | 0.3088 | 0.2655 | not meaningful (similarity score) |
| E/E′ — Failure-history + supervised | 0.5809 [0.5472, 0.6146] | 0.3376 | 0.2327 | 0.1109 |
| **F — Supervised Failure Risk (selected)** | **0.6548 [0.6159, 0.6938]** | 0.3912 | **0.1972** | 0.0753 |
| B — Calibrated confidence | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 | 0.0823 |

All numbers reproduced exactly (to float precision) from Phase 3.2 /
Phase 3.2C `aggregate_results.json`; `phase3_4_compare.py` independently
recomputes each aggregate from per-seed values with the same `_t_interval`
helper Phase 3.1 defined, and raises on any disagreement with the stored
files. None occurred.

**Ranking by AUROC:** B > F > E ≈ E′ > D > C > A.
**Ranking by AURC (lower = better):** B < F < E ≈ E′ < D < A < C — the same
ordering, with the notable exception that C (original Failure Memory)
falls *below* the no-signal baseline on AURC despite a marginally higher
AUROC mean.

## 6. 95% confidence intervals

Two distinct sources of uncertainty are reported and never combined:

- **Cross-seed variability** (table above): Student-t interval over the
  six per-seed point estimates. This is the uncertainty that matters for
  "would this hold on a different training draw."
- **Within-seed bootstrap uncertainty** (primary seed 42 only): percentile
  bootstrap over resamples of that one seed's held-out rows. Reported
  only for AUROC/AUPRC (the only metrics the Phase 3.1/3.2/3.2C scripts
  bootstrapped). Example, primary seed 42, AUROC:
  - F (Supervised Failure Risk): [0.6031, 0.6452]
  - B (calibrated confidence): [0.6069, 0.6484]
  - C (original Failure Memory): [0.4969, 0.5413]

  These intervals are narrower than the cross-seed intervals and answer a
  different question (sampling noise within one test set, not
  seed-to-seed variability) — they are not interchangeable, and this
  report does not average or otherwise merge them.

## 7. Per-seed paired comparisons

For every candidate, versus each of the three established baselines
(no signal, original Failure Memory, calibrated confidence), computed
per-seed on the exact same 6 held-out test sets:

| Candidate | Beats no-signal | Beats orig. Failure Memory | Beats calibrated confidence |
|---|---|---|---|
| C — Original Failure Memory | 1/6 | — | 0/6 |
| D — Raw structured features | 6/6 | 5/6 | 0/6 |
| E/E′ — Failure-history + supervised | 6/6 | 6/6 | 0/6 |
| **F — Supervised Failure Risk** | **6/6** | **6/6** | 1/6 |
| B — Calibrated confidence | 6/6 | 6/6 | — |

Mean paired AUROC difference (Student-t 95% CI over the 6 paired
per-seed differences; **descriptive interval, not a significance test** —
see caveat below):

- F vs. no signal: **+0.1548** [0.1159, 0.1938] — CI excludes 0.
- F vs. original Failure Memory: **+0.1407** [0.0865, 0.1950] — CI excludes 0.
- F vs. calibrated confidence: **−0.0051** [−0.0096, −0.0006] — CI excludes
  0, on the *negative* side. F is consistently, if narrowly, below
  calibrated confidence — this is not noise in either direction, it is a
  small but consistent gap.
- C (original Failure Memory) vs. no signal: +0.0141 [−0.0368, 0.0086] —
  CI includes 0. **C does not reliably beat no-signal on a per-seed
  basis**, consistent with Phase 3.1/3.2's conclusion that the original
  Failure Memory carries essentially no signal.

**Statistical caveat (explicit, per the Phase 3.4 brief section 11):**
with n=6 predetermined seeds, no formal hypothesis test (t-test, sign
test, Wilcoxon) has meaningful statistical power, and none is computed
here. The Student-t intervals above are reported as descriptive interval
estimates of the paired difference, exactly as the frozen protocol already
specifies for cross-seed aggregation — they are not being used as a
significance test, and "CI excludes 0" is reported as a consistency
signal, not as proof of a population-level effect.

## 8. AUROC comparison

Covered in section 5/7 above. F and B are clearly separated from
everything else (C, D, E/E′, A) by a wide margin (~0.07–0.16 AUROC), and
F and B are close to each other (~0.005 apart) but F is consistently
slightly below B, not above or indistinguishable.

## 9. AUPRC comparison

Same ordering as AUROC: A (0.281) < C (0.297) < D (0.309) < E/E′ (0.338) <
B (0.384) < F (0.391) — note F's AUPRC mean is actually marginally *above*
B's, unlike AUROC, though this was not paired/CI-tested here (AUPRC was
not part of the frozen per-seed paired-comparison scope, which the brief
specified for AUROC). This is worth flagging as a discrepancy in ranking
between the two ranking metrics but should not be over-read given the
absence of a paired CI for AUPRC specifically.

## 10. AURC comparison (risk-coverage)

Lower is better. B (0.1941) and F (0.1972) are the two best (i.e. lowest
average selective risk across the 5%–100% coverage grid), followed by
E/E′ (0.2327), then D (0.2655), then **A (0.2699) beats C (0.2767)** — the
original Failure Memory has *worse* risk-coverage behavior than doing
nothing and flagging a random subset by prevalence. This matches its weak
AUROC/near-1-vs-6-seeds-win record in section 7.

### Low-coverage precision/recall (the region autonomous abstention would use)

| Candidate | Prec@5% | Rec@5% | Prec@10% | Rec@10% | Prec@20% | Rec@20% | Prec@50% | Rec@50% |
|---|---|---|---|---|---|---|---|---|
| A — No signal | 0.262 | 0.048 | 0.257 | 0.094 | 0.263 | 0.190 | 0.271 | 0.488 |
| C — Failure Memory | 0.321 | 0.057 | 0.317 | 0.113 | 0.310 | 0.220 | 0.290 | 0.514 |
| D — Raw features | 0.346 | 0.061 | 0.352 | 0.127 | 0.320 | 0.230 | 0.297 | 0.530 |
| E/E′ — History+supervised | 0.376 | 0.068 | 0.378 | 0.138 | 0.361 | 0.261 | 0.322 | 0.579 |
| **F — Supervised Failure Risk** | **0.438** | **0.081** | **0.427** | **0.157** | **0.416** | **0.303** | 0.377 | 0.682 |
| B — Calibrated confidence | 0.436 | 0.080 | 0.440 | 0.162 | 0.416 | 0.302 | **0.378** | **0.685** |

At every fixed coverage point, the same two-tier structure holds: {B, F}
clearly ahead of {E/E′}, which is clearly ahead of {D, C, A}. F and B are
within ~1 percentage point of each other at every coverage level — an
autonomous system flagging its riskiest 5–20% of workloads would get
essentially the same precision/recall from either.

## 11. Calibration comparison

ECE is reported only for representations that were fit/designed as
probabilities (`is_probability=True` on the underlying representation
class — verified programmatically, not asserted): A, B, E/E′, F. **ECE is
explicitly "not meaningful" and not computed for C (original Failure
Memory) and D (raw structured features)** — both are Gaussian-kernel /
cluster-similarity scores, never calibrated as probabilities. Among the
probability-valued candidates, A (0.065, trivially — a constant score
equals its own empirical rate almost by construction) and F (0.075) have
the lowest ECE; B (0.082) and E/E′ (0.111) are less well calibrated. Lower
ECE is not the same as higher discriminative power — F has both a
reasonably low ECE *and* strong AUROC, which is a more meaningful
combination than A's near-zero ECE (a constant score is trivially
"calibrated" while providing no ranking information at all, AUROC=0.5).

## 12. Comparison with calibrated confidence (section 15 of the brief)

**How close are they?** Very close in aggregate (0.6548 vs. 0.6599 AUROC,
a 0.0051 gap) and close per-seed (F beats B on only 1 of 6 seeds; the mean
paired difference's 95% CI is entirely negative and does not cross zero).

**Does Failure Risk consistently track confidence?** Yes — at every fixed
coverage point (5/10/20/50%) their precision and recall are within ~1
point of each other, and their AUROC/AUPRC/AURC orderings are adjacent
across every metric in this report.

**Does Failure Risk add information beyond confidence, or provide
complementary information?** **Not established by Phase 3.4.** This phase
did not run an experiment designed to answer that question — e.g. it did
not fit a model using calibrated confidence as an input feature alongside
Failure Risk, did not test a combined/ensembled score, and did not measure
residual correlation between the two scores' errors. The consistent
per-seed AUROC gap in F's favor over the *original* Failure Memory (0/6
losses) combined with its consistent shortfall against calibrated
confidence (1/6 wins) is most consistent with an interpretation that
**Candidate F is learning a signal that substantially overlaps with what
calibrated confidence already captures**, rather than an independent
signal — but this is an interpretation of the pattern already visible in
this report's numbers, not a tested claim, and should not be reported as
established.

## 13. Comparison with original Failure Memory

F (and its precursor E/E′) clearly and consistently outperform the
original Phase 2 Failure Memory: 6/6 seeds on AUROC, mean paired AUROC
difference +0.14 with a 95%-CI entirely above zero, and a materially
better AURC (0.197 vs. 0.277 — the original Failure Memory's AURC is
worse than doing nothing). The original Failure Memory itself does not
reliably beat no-signal on a per-seed basis (1/6 seeds), consistent with
Phase 3.1's original finding that it carries essentially no usable
predictive signal on this benchmark.

## 14. Risk-coverage interpretation

At low coverage (5–10%, the region most relevant to an autonomous system
that can only afford to review/abstain on a small fraction of workloads),
F and B both roughly double the precision of the original Failure Memory
and roughly 1.4x the precision of the best non-selected candidate
(E/E′). C (original Failure Memory) is the only candidate whose AURC is
worse than the no-signal baseline across the full 5–100% grid — it would
be actively counterproductive to use for coverage-based triage, not just
unhelpful.

## 15. Limitations

- Six seeds is a small sample for cross-seed inference; the Student-t CIs
  reported here are wide relative to the AUROC gaps being compared for
  the mid-tier candidates (C, D, E/E′), and several pairwise CIs
  (C vs. no-signal, D vs. C) include zero — those comparisons are
  genuinely inconclusive at this seed count, not just "small but real."
- All results are on a single synthetic benchmark
  (`src/data/synthetic.generate_regime_stream`) with a fixed drift
  mechanism; Phase 3.3 tested three drift_scale conditions but Phase 3.4
  compares only the original benchmark condition (`drift_scale=0.35`) —
  it does not re-run this consolidated comparison across Phase 3.3's
  generalization conditions, which was out of this phase's scope.
- AUPRC is reported per-candidate but was not part of the frozen
  per-seed-paired-comparison protocol scope (which specified AUROC for
  win-count/CI purposes); its ranking (F slightly above B) should be
  read as descriptive only.
- ECE for candidate F/E — while "meaningful" by the `is_probability` flag
  — reflects an isotonic/logistic-regression-style calibration that was
  never explicitly re-checked with a dedicated calibration-curve
  diagnostic beyond the 10-bin ECE already computed in Phase 3.2/3.2C.

## 16. Threats to validity

- **Shared feature generator across candidates.** Every candidate in this
  comparison other than B was fit on data derived from the exact same
  `src.pipeline_builder.build_system` call per seed; a systematic property
  of that generator that happens to make calibrated confidence strong
  would propagate identically into every representation-based candidate's
  ceiling.
- **Reused calibrator.** Candidate F, E/E′, and Candidate B's own score
  all depend on the same underlying `ConfidenceCalibrator` — D depends on
  it in the KMeans-similarity mechanism, and F's classifier is trained on
  features that include or derive from calibrated confidence. This is a
  structural reason to expect F and B to be correlated, independent of
  whether F is "actually the same signal" — again, not something Phase
  3.4 tested directly (see section 12).
- **No independent replication benchmark.** All comparisons here are
  within one synthetic benchmark family; nothing in Phase 3.4 speaks to
  real-world transfer.

## 17. What Phase 3.4 establishes

- Under the frozen protocol and all six predetermined seeds, **F
  (Supervised Failure Risk) and B (calibrated confidence) are the two
  strongest candidates on every metric evaluated** (AUROC, AUPRC, AURC,
  precision/recall at every fixed coverage point), clearly separated from
  the original Failure Memory, raw-feature, and failure-history
  candidates.
- **F consistently and substantially outperforms both no-signal (6/6
  seeds) and the original Phase 2 Failure Memory (6/6 seeds)**, with
  cross-seed and paired-difference confidence intervals that exclude
  zero in both cases.
- **F does not consistently outperform calibrated confidence** (1/6
  seeds; paired-difference CI is entirely negative) — the aggregate gap is
  small (~0.005 AUROC) but not in F's favor and not indistinguishable from
  zero in this data.
- **The original Phase 2 Failure Memory does not reliably beat no-signal
  on a per-seed basis** (1/6 seeds) and has the worst AURC of any
  candidate compared, including no-signal — reaffirming Phase 3.1/3.2's
  conclusion, now under a direct multi-candidate comparison rather than
  in isolation.
- **Candidate C (Phase 3.2) and Experiment C (Phase 3.2C) are verified
  byte-identical per-seed**, confirming the ablation's documented claim
  that Experiment C is an exact reproduction, not merely a similar result.

## 18. What Phase 3.4 does NOT establish

- Whether Failure Risk (F) adds information *complementary* to calibrated
  confidence, or is learning a largely overlapping signal — **not
  established**; no experiment here tested combined/ensembled scoring or
  residual correlation (see section 12).
- Whether F would remain competitive with calibrated confidence under
  Phase 3.3's unseen-drift conditions when compared to calibrated
  confidence *in this same consolidated multi-metric format* — Phase 3.3
  already reported per-condition AUROC for both, but Phase 3.4 did not
  re-run the full comparison table (AUPRC/AURC/coverage/ECE/paired
  per-seed) across those conditions.
- Any claim of real-world generalization — this remains a synthetic
  benchmark result.
- Statistical significance in the classical sense for any comparison —
  every interval reported here is a descriptive Student-t or bootstrap
  interval at n=6 or n=1-seed-resampled, explicitly not a hypothesis test.

## 19. Explicit recommendation for Phase 3.5

The evidence here does **not** by itself justify claiming Failure Risk
(F) is ready to replace or augment calibrated confidence in an autonomous
decision path — it tracks confidence closely but has not been shown to
add value beyond it. Before any such use is considered (and before Phase
3.5's attack-generalization work, which this document does not begin):

1. A dedicated complementarity test (does F improve on B when combined,
   e.g. via a simple two-feature model or residual-correlation check) is
   the most direct way to resolve section 12/18's open question, and is
   recommended as a candidate follow-up — **not performed here**, per the
   Phase 3.4 brief's explicit prohibition on new model development inside
   this phase.
2. If Phase 3.5 proceeds with attack/generalization analysis using F, it
   should carry calibrated confidence (B) alongside it as a co-equal
   comparison baseline, not treat B as already-surpassed — this report's
   own numbers do not support that framing.

---

## 20. Formal Phase 3.4 assessment

# 🟡 INCONCLUSIVE

The evidence clearly and consistently supports that the selected
Supervised Failure Risk candidate (F) outperforms the weaker baselines —
no signal and the original Phase 2 Failure Memory — on every metric and
essentially every seed. It does **not** establish that F provides value
beyond the strongest existing reference, calibrated confidence: F tracks
confidence closely but sits slightly and consistently below it on AUROC,
and whether the two carry complementary information was not tested. The
comparison is useful and honest evidence that the supervised-classifier
mechanism (isolated in Phase 3.2C) is real and reproducible relative to
Failure Memory — but it is not evidence that this specific candidate is
"clearly supported" as an improvement over the strongest baseline already
on record.


---

<a id="phase3-5-attack-generalization"></a>
# PHASE3 5 ATTACK GENERALIZATION
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_5_ATTACK_GENERALIZATION.md`  
**Role:** Phase 3.5 attack-generalization evaluation (synthetic data).

# Phase 3.5 — Attack Generalization

**Status: COMPLETE.** This document is the Phase 3.5 deliverable.

Companion artifacts:
- Frozen protocol: [`configs/phase3_5_attack_protocol.json`](../configs/phase3_5_attack_protocol.json)
- Attack transforms: [`src/evaluation/attacks.py`](../src/evaluation/attacks.py)
- Evaluation script: [`benchmarks/phase3_5_attack_generalization.py`](../benchmarks/phase3_5_attack_generalization.py)
- Leakage audit script: [`benchmarks/phase3_5_leakage_audit.py`](../benchmarks/phase3_5_leakage_audit.py)
- Machine-readable results: [`experiments/results/phase3_5/attack_generalization.json`](../experiments/results/phase3_5/attack_generalization.json), [`experiments/results/phase3_5/leakage_audit.json`](../experiments/results/phase3_5/leakage_audit.json)
- Tests: [`tests/integration/test_phase3_5_attack_generalization.py`](../tests/integration/test_phase3_5_attack_generalization.py)

## 1. Objective

Determine whether the predictive behavior of the selected Supervised
Failure Risk candidate (F — Phase 3.2C's Experiment B, frozen unchanged by
Phase 3.3) survives deliberately different failure/attack conditions
**without retraining or test-condition adaptation**, and compare it
fairly against calibrated confidence (B, a co-equal baseline, not an
already-surpassed one) and the original Phase 2 Failure Memory (C).

## 2. Relationship to Phase 3.1–3.4

- Phase 3.1 froze the evaluation protocol and metrics — reused unchanged
  here (seeds, coverage points, bootstrap settings, calibration bins).
- Phase 3.2/3.2C developed and isolated F's mechanism (supervised
  classifier on the old Phase 2 PCA representation).
- Phase 3.3 tested F under **concept drift**: fixed features, rotated
  label-generating boundary (`drift_scale`).
- Phase 3.4 consolidated everything on the clean benchmark and found F
  clearly beats no-signal (A) and original Failure Memory (C), but does
  **not** consistently beat calibrated confidence (B) — status 🟡
  INCONCLUSIVE. **That conclusion is frozen and is not revisited or
  rewritten here.**
- Phase 3.5 tests a **different** axis: **covariate-shift attacks**
  (corrupted/missing input features, label-generating relationship
  untouched) — the opposite structural change from Phase 3.3's concept
  drift, and explicitly not a repeat of it under a new name.

## 3. Frozen evaluation protocol

Inherited unchanged from `configs/phase3_1_protocol.json` (verified by
the evaluation script, which raises if `phase3_5_attack_protocol.json`'s
`seeds`/`primary_seed` disagree with it):

- Seeds `[1, 2, 3, 4, 5, 42]`, primary seed `42`
- Coverage operating points `5%, 10%, 20%, 50%`
- Calibration bins `10`
- Bootstrap: 2000 resamples, percentile method, seed `0`, 95% CI
- Cross-seed CI: Student-t interval over the six per-seed estimates

New for Phase 3.5, frozen in `configs/phase3_5_attack_protocol.json`
**before** this script was run: the attack matrix (section 6), the
robustness metric definition (section 20), and the fitting/no-refit rule
(section 8).

## 4. Attack/generalization threat model

1. **What is being changed?** Only the feature values (`context`) of the
   held-out regime-3/4 samples — after generation, via a deterministic
   post-hoc transform (`src/evaluation/attacks.py`). `src/data/synthetic.py`
   is not modified and its label-generating mechanism is never touched.
2. **Why does it represent an attack/failure perturbation?** It models an
   attacker or environmental fault corrupting the telemetry/inputs a
   deployed system observes (noisy sensors, a dropped/corrupted field) —
   without changing the underlying, true relationship between inputs and
   correctness that the workload model is ultimately judged against.
3. **What remains fixed?** The true label-generating weight vector, the
   workload model, the calibrator, the original Failure Memory, and F —
   all fit once on clean regime-0/1/2 data and never touched again. The
   sample's true `label` and `regime` are also unchanged.
4. **What information is available to the model?** Exactly the corrupted
   context — the same information every candidate (A/B/C/F) would
   observe in a real deployment if its input pipeline were compromised.
5. **What information is unavailable?** The clean, uncorrupted feature
   values — the model has no way to recover them, and no candidate is
   given attack-identity information (which condition is active, or
   attack parameters) at scoring time.
6. **Is the condition seen or unseen?** Unseen. Every candidate is fit
   exclusively on clean regime-0/1/2 data (`build_system`'s own, always
   at the default `drift_scale`, no corruption). No attack transform is
   ever applied before or during fitting.
7. **Is the model allowed to retrain?** No. Verified by a runtime
   leakage check (`no_fit_calls_during_attack_scoring`) confirming no
   `.fit(` call occurs anywhere in the per-condition scoring loop, and by
   the structural pattern reused from Phase 3.3 (fit once, score
   many times).
8. **Why does this constitute generalization rather than ordinary
   train/test variation?** Regimes 3/4 were always held out at the SAME
   (clean) distribution the model was fit on, modulo drift_scale (Phase
   3.1/3.2/3.2C/3.4) or concept drift (Phase 3.3). Here, the held-out data
   is additionally passed through a corruption process the fitting
   pipeline never saw in any form, on any regime, at any seed — this is a
   structurally different distribution shift (covariate shift on inputs),
   not a re-draw of the same generative family.

## 5. Why each attack condition is scientifically justified

The synthetic generator (`src/data/synthetic.generate_regime_stream`)
exposes exactly three knobs: `regime_sizes`, `drift_scale`, `seed`.
`drift_scale` (concept drift) was already Phase 3.3's axis. `seed`
controls both features and the concept jointly and is already the
frozen cross-seed variability axis — treating a new seed as an "attack"
would violate the brief's explicit warning (section 20) that a different
random seed is not automatically a new regime. That leaves **no
generator-native axis for a genuinely different attack** without either
modifying the frozen generator or reimplementing its RNG stream
externally.

Given that, Phase 3.5's attacks are **post-hoc, deterministic
transforms of already-generated held-out samples** — additive feature
noise and feature zeroing — which:
- require no change to `src/data/synthetic.py` or any other frozen file,
- have a clean, standard interpretation (corrupted/missing telemetry) as
  an attack on a deployed system's input pipeline,
- are fully deterministic and reproducible given `(seed, attack_ordinal)`,
  and
- create a genuine, different-in-kind distribution shift (covariate
  shift, not concept drift) from everything tested in Phase 3.1–3.4.

**Explicitly excluded, and why** (frozen in
`configs/phase3_5_attack_protocol.json.excluded_axes`, not silently
dropped):
- *Label-boundary manipulation* — would require modifying the frozen
  generator or reimplementing its weight-vector/RNG construction
  externally; neither was done, to avoid touching frozen code or
  introducing an undocumented, possibly-inconsistent reimplementation.
- *Failure-rate shift* — not independently controllable via the
  generator's exposed parameters without changing the meaning of the
  task.
- *Further concept-drift severities* — already covered by Phase 3.3;
  repeating it under a new name would not test a new axis.

## 6. Attack matrix

Frozen in `configs/phase3_5_attack_protocol.json` before evaluation.

| ID | Mechanism | Parameters | Severity | Seen/unseen |
|---|---|---|---|---|
| `clean` | none (reference) | — | — | — |
| `feature_noise_mild` | additive Gaussian noise on all 5 features | σ=0.5 (half native scale) | mild | unseen |
| `feature_noise_severe` | additive Gaussian noise on all 5 features | σ=1.5 (1.5x native scale) | severe | unseen |
| `feature_dropout` | zero out 2 of 5 features | `f2`, `f4` (fixed a priori) | n/a — binary corruption | unseen |

RNG for the noise attacks is derived deterministically as
`np.random.default_rng((seed, attack_ordinal))` — reproducible, no
uncontrolled randomness (verified by
`check_attack_determinism` in the leakage audit).

## 7. Candidate systems

Per the brief section 5, the primary comparison is exactly **F vs. B vs.
C vs. A** — D/E (Phase 3.2's raw-feature and failure-history candidates)
are not re-evaluated here, to avoid unnecessary scope expansion.

| ID | Candidate | Reused from |
|---|---|---|
| A | No signal | Phase 3.1 baseline, unchanged |
| B | Calibrated confidence | Phase 3.1 baseline, unchanged |
| C | Original Phase 2 Failure Memory | Phase 3.1 baseline, unchanged |
| **F** | **Supervised Failure Risk** | Phase 3.2C Experiment B / Phase 3.3 frozen candidate, unchanged |

`benchmarks/phase3_5_attack_generalization.py` imports
`benchmarks.phase3_3_generalization`'s `_fit_frozen_candidate`,
`_reconstruct_regime2_with_confidences`, `_compute_condition_arrays`,
`_evaluate_one`, `_is_probability`, `_assert_no_regime2_leakage`, and
`BASELINES` **directly, unmodified** — F, B, and C are not reimplemented
for Phase 3.5, only re-scored against new conditions. A test
(`test_f_implementation_matches_phase3_3_frozen_candidate`) confirms F's
score on a held-out sample matches Phase 3.3's own computation exactly.

## 8. Training/fitting boundaries

For every seed: `build_system` fits the workload model (regime 0),
calibrator (regime 1), and original Failure Memory (regime 2) exactly as
every prior phase did. F is fit exactly once, on clean regime-2 data, via
the unmodified `Phase2RepresentationSupervisedRisk.fit()`. All four
candidates are then **frozen** and reused, unmodified, to score the clean
reference condition and all three attack conditions. No `.fit()` call
occurs anywhere in the per-condition scoring loop — checked at runtime,
not just asserted in prose (see section 9).

No hyperparameter, feature, regularization, calibration, PCA dimension,
or KMeans setting was changed from Phase 3.2C/3.3's frozen configuration.

## 9. Leakage audit

`benchmarks/phase3_5_leakage_audit.py`, run against seed 42 — **all 7
checks passed**:

| Check | Result |
|---|---|
| `training_evaluation_disjointness` | PASS |
| `attack_transforms_preserve_ground_truth` | PASS |
| `attack_transforms_actually_corrupt_context` | PASS |
| `attack_determinism` | PASS |
| `no_fit_calls_during_attack_scoring` | PASS |
| `attack_protocol_matches_frozen_file` | PASS |
| `duplicate_samples_across_attack_conditions` | PASS |

`all_passed: true` (`experiments/results/phase3_5/leakage_audit.json`).
No STOP condition was triggered.

## 10. Clean baseline results

Identical (up to the display-label rename `D_supervised_failure_risk` →
`F`) to Phase 3.4's frozen numbers — reused for consistency, not rerun
independently for this table:

| Candidate | AUROC | AUPRC | AURC |
|---|---|---|---|
| A — No signal | 0.5000 [0.5000, 0.5000] | 0.2806 | 0.2699 |
| C — Original Failure Memory | 0.5141 [0.4914, 0.5368] | 0.2971 | 0.2767 |
| **F — Supervised Failure Risk** | **0.6548 [0.6159, 0.6938]** | 0.3912 | 0.1972 |
| B — Calibrated confidence | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 |

## 11. Attack-condition results (cross-seed AUROC, 95% CI)

| Candidate | Clean | Mild noise (σ=0.5) | Severe noise (σ=1.5) | Feature dropout |
|---|---|---|---|---|
| A — No signal | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] | 0.5000 [.5000,.5000] |
| C — Original Failure Memory | 0.5141 [.4914,.5368] | 0.5143 [.4942,.5343] | 0.5152 [.5008,.5296] | 0.4970 [.4677,.5264] |
| **F — Supervised Failure Risk** | **0.6548 [.6159,.6938]** | **0.6297 [.5959,.6635]** | **0.5502 [.5225,.5779]** | **0.5999 [.5483,.6516]** |
| B — Calibrated confidence | 0.6599 [.6185,.7013] | 0.6351 [.5971,.6732] | 0.5565 [.5284,.5845] | 0.6005 [.5472,.6539] |

## 12. Per-seed results

F vs. A / F vs. C / F vs. B win counts (of 6 seeds), AUROC:

| Condition | F beats A | F beats C | F beats B |
|---|---|---|---|
| clean | 6/6 | 6/6 | 1/6 |
| feature_noise_mild | 6/6 | 6/6 | 1/6 |
| feature_noise_severe | 6/6 | **5/6** | 0/6 |
| feature_dropout | 6/6 | 6/6 | **3/6** |

Full per-seed AUROC (F / B / C), every condition:

```
clean:                seed 1: F=0.6325 B=0.6302 C=0.5165   seed 2: F=0.6875 B=0.6917 C=0.5373
                       seed 3: F=0.7106 B=0.7208 C=0.4729   seed 4: F=0.6188 B=0.6251 C=0.5226
                       seed 5: F=0.6547 B=0.6628 C=0.5160   seed 42: F=0.6249 B=0.6289 C=0.5193

feature_noise_mild:    seed 1: F=0.6004 B=0.5976 C=0.5029   seed 2: F=0.6491 B=0.6521 C=0.5241
                       seed 3: F=0.6757 B=0.6867 C=0.4836   seed 4: F=0.6032 B=0.6089 C=0.5113
                       seed 5: F=0.6481 B=0.6602 C=0.5274   seed 42: F=0.6015 B=0.6052 C=0.5362

feature_noise_severe:  seed 1: F=0.5231 B=0.5234 C=0.5306   seed 2: F=0.5492 B=0.5525 C=0.5080
                       seed 3: F=0.5556 B=0.5711 C=0.5332   seed 4: F=0.5227 B=0.5350 C=0.5004
                       seed 5: F=0.5941 B=0.5988 C=0.5049   seed 42: F=0.5565 B=0.5579 C=0.5139

feature_dropout:       seed 1: F=0.5359 B=0.5364 C=0.4927   seed 2: F=0.5732 B=0.5728 C=0.5105
                       seed 3: F=0.6365 B=0.6432 C=0.4561   seed 4: F=0.6292 B=0.6237 C=0.5272
                       seed 5: F=0.6614 B=0.6653 C=0.5215   seed 42: F=0.5635 B=0.5619 C=0.4741
```

Every seed is reported — none hidden or excluded.

## 13. Cross-seed aggregates and CIs

See sections 10–11. As in Phase 3.4, n=6 is too small for a formal
significance test; every interval above is a descriptive Student-t
interval over the six per-seed point estimates, not a hypothesis test.

## 14. Within-seed bootstrap (primary seed 42, AUROC)

| Condition | F | B | C |
|---|---|---|---|
| clean | [0.6031, 0.6452] | [0.6069, 0.6484] | [0.4969, 0.5413] |
| feature_noise_mild | [0.5808, 0.6222] | [0.5843, 0.6260] | [0.5141, 0.5574] |
| feature_noise_severe | [0.5363, 0.5778] | [0.5371, 0.5789] | [0.4919, 0.5363] |
| feature_dropout | [0.5428, 0.5835] | [0.5422, 0.5826] | [0.4526, 0.4944] |

2000 resamples, percentile method, seed 0 — kept entirely separate from
the cross-seed intervals above; not combined.

## 15. AUROC comparison

F and B remain tightly coupled across every condition (within ~0.005–0.03
AUROC of each other), while both remain clearly separated from C and A in
every condition except that C briefly nudges ahead of F on one individual
seed under severe noise (section 23). No candidate's ranking relative to
the others reverses wholesale under any attack.

## 16. AUPRC comparison

**Caveat before reading this section:** unlike AUROC, AUPRC's baseline
depends on failure prevalence, and prevalence itself shifts under the
noise attacks (a noisier input makes the workload model wrong more
often, raising the empirical failure rate) — clean AUPRC and attacked
AUPRC are **not directly comparable** the way clean/attacked AUROC are.
With that caveat: AUPRC rises for every candidate under stronger attacks
(prevalence effect dominates), and F and B remain close to each other at
every condition (e.g. severe noise: F=0.426, B=0.429; dropout: F=0.427,
B=0.415 — F marginally ahead here).

## 17. Risk-coverage comparison (AURC)

| Candidate | Clean | Mild noise | Severe noise | Dropout |
|---|---|---|---|---|
| A | 0.2699 | 0.2961 | 0.3885 | 0.3618 |
| C | 0.2767 | 0.3030 | 0.3815 | 0.3539 |
| **F** | **0.1972** | **0.2330** | **0.3590** | **0.2919** |
| B | 0.1941 | 0.2286 | 0.3526 | 0.2907 |

AURC rises (worse) for every candidate under every attack — expected,
since the workload model itself gets less accurate. F and B remain the
two lowest (best) at every condition; the gap between {F, B} and {A, C}
narrows under severe noise (all four candidates converge toward ~0.35–0.39
as the attack overwhelms the failure signal) but does not close.

## 18. Precision/recall at fixed coverage

At 5% coverage (F vs. B):

| Condition | F precision | B precision | F recall | B recall |
|---|---|---|---|---|
| clean | 0.438 | 0.436 | 0.081 | 0.080 |
| feature_noise_mild | 0.442 | 0.457 | 0.073 | 0.075 |
| feature_noise_severe | 0.418 | 0.460 | 0.053 | 0.059 |
| **feature_dropout** | **0.486** | **0.448** | 0.071 | 0.065 |

At every other fixed coverage point (10/20/50%) F and B stay within ~1–2
points of each other in every condition (full detail in
`attack_generalization.json`). Feature dropout is the one condition where
F's low-coverage precision is *ahead* of B's, consistent with its 3/6
per-seed AUROC win count there — the closest the two candidates come to
diverging in F's favor anywhere in this study, but still not a
consistent or large enough margin to claim F is superior under dropout
(see section 30's comparison rules).

## 19. Calibration

ECE (meaningful only for A/B/F/C's probability-valued outputs; C's
Gaussian-kernel score is never reported — consistent with Phase 3.1's
finding that it is not a probability):

| Candidate | Clean | Mild noise | Severe noise | Dropout |
|---|---|---|---|---|
| F | 0.075 | 0.094 | 0.196 | 0.127 |
| B | 0.082 | 0.117 | 0.229 | 0.123 |

Both degrade (higher ECE = worse) under stronger attacks — expected,
since neither was recalibrated for the attacked distribution. F's ECE is
slightly better than B's at every condition except dropout, where they
are essentially tied (0.127 vs 0.123).

## 20. Robustness/degradation analysis

`excess_auroc_retention_ratio = (attack_auroc - 0.5) / (clean_auroc -
0.5)`, defined in the frozen protocol before evaluation. Undefined
(reported `null`, never fabricated) for A, whose clean AUROC is exactly
0.5.

| Condition | F retention | B retention | C retention |
|---|---|---|---|
| feature_noise_mild | 0.838 | 0.843 | 0.918 |
| feature_noise_severe | 0.325 | 0.352 | 0.315 |
| feature_dropout | 0.658 | 0.632 | 0.444 |

Reading this carefully: C's "high retention" at mild noise (0.918) and
low retention at severe noise (0.315) is a small-number artifact — C's
clean excess-AUROC (0.0141) is tiny, so its retention ratio is highly
sensitive to noise and not informative on its own; the raw AUROC values
(section 11) are the more trustworthy comparison for C. Between F and B
specifically: retention is within ~1–5 percentage points of each other at
every condition, alternating which one retains marginally more (B
retains slightly more under noise, F retains slightly more under
dropout). **Neither candidate collapses disproportionately relative to
the other under any tested attack.**

## 21. F vs calibrated confidence

Consistent with Phase 3.4: F tracks B closely in every attack condition
and does not establish a consistent advantage over it. F beats B on
AUROC in 1/6, 1/6, 0/6, and 3/6 seeds across clean/mild/severe/dropout
respectively — never a majority except nowhere. The gap between them is
small in absolute terms at every condition (typically <0.01–0.03 AUROC)
and both degrade by similar amounts under the same attack. **This
phase does not establish that F is more robust than B, nor that F is
less robust than B in any way that would change Phase 3.4's
conclusion** — the relationship between them (close, F slightly and
inconsistently behind) is stable across the clean condition and all
three attacks tested here.

## 22. F vs original Failure Memory

F clearly and consistently outperforms C at every condition except one
individual seed (section 23): 6/6 wins at clean, mild noise, and
dropout; 5/6 at severe noise. C itself stays close to no-signal (AUROC
0.497–0.515) at every condition, including one aggregate value
(feature_dropout: 0.4970) that is numerically *below* 0.5 — consistent
with Phase 3.1–3.4's finding that the original Failure Memory mechanism
carries little to no reliable signal, a finding that persists rather than
reverses under attack.

## 23. Failure cases

**Explicitly reported, not hidden, per the brief's section 29/31
requirement:**

- **Severe noise, seed 1**: C (0.5306) narrowly exceeds both F (0.5231)
  and B (0.5234) — the only seed/condition combination in this entire
  study where the original Failure Memory beats either supervised/
  calibrated candidate. Given C's aggregate AUROC across all 6 seeds at
  this condition (0.5152 [0.5008, 0.5296]) remains barely above 0.5 and
  its per-seed values elsewhere in this condition are unremarkable
  (0.508, 0.533, 0.500, 0.505, 0.514), this reads as ordinary per-seed
  noise around a near-null signal, not a systematic reversal — but it is
  reported as observed, not smoothed over.
- **Feature dropout is F's/B's weakest relative margin over C and also
  the condition where F comes closest to (and briefly exceeds) B**: F
  beats B on AUROC in 3/6 seeds here (vs. 0–1/6 everywhere else) and
  leads on precision@5%. This is the most "mixed" result in the study —
  reported as mixed, not selected as a headline win for F.
- **Severe noise degrades every candidate toward the no-signal floor**:
  F, B, and C are within 0.06 AUROC of each other and all much closer to
  0.5 than on clean data — the failure-detection task becomes
  substantially harder under strong input corruption for every method
  tested, including calibrated confidence.

No condition was removed or re-parameterized after seeing these results.

## 24. Limitations

- Only two attack mechanisms (additive noise at two severities, and a
  single fixed feature-dropout set) were tested — a small, predetermined
  matrix, not an exhaustive attack taxonomy. A wider corruption space
  (different feature subsets, structured/adversarial noise directions,
  combined noise+dropout) was not explored and is not claimed to be
  covered.
- AUPRC is not directly comparable across conditions due to
  prevalence shift (section 16) — reported for completeness, but not
  used as a primary robustness signal in this report's conclusions.
- The feature-dropout feature set (`f2`, `f4`) was chosen by a stated,
  non-adaptive rule, but it is still a single arbitrary choice among
  `C(5,2)=10` possible pairs; different pairs might show different
  degradation patterns and were not tested.
- Six seeds remain a small sample for cross-seed inference; several
  per-condition CIs (especially for C, whose signal is near-null
  throughout) are wide relative to the effect sizes being compared.

## 25. Threats to validity

- All four candidates share the same underlying calibrator and workload
  model; an attack that degrades the calibrator's input features
  necessarily degrades every downstream candidate that consumes
  calibrated confidence (B, and indirectly F, whose embedding uses it) —
  this is a structural reason F and B move together under attack, not
  necessarily evidence that they carry the same information in general
  (see Phase 3.4 section 12, still unresolved).
- The attacks are purely synthetic transforms of a synthetic benchmark;
  nothing here speaks to how a real telemetry pipeline would actually
  fail or be attacked.
- No adversarial (gradient-based, worst-case-search) attack was
  attempted — only random/structural corruption. A targeted adversarial
  perturbation against the workload model's decision boundary could
  behave very differently and was out of scope here.

## 26. What Phase 3.5 establishes

- F's predictive relationship to the three baselines (A, B, C) — clearly
  above A and C, closely tracking but not exceeding B — **persists
  across all three tested covariate-shift attack conditions**, not just
  the clean benchmark.
- Neither F nor B collapses disproportionately relative to the other
  under any tested attack; their degradation (AUROC delta, retention
  ratio, ECE increase) is of similar magnitude at every severity.
- The original Failure Memory (C) continues to show little to no
  reliable signal under attack, consistent with every prior phase.
- No leakage, refitting, or attack-parameter influence on any fitted
  model was found (7/7 runtime checks passed).
- The feature-dropout condition is the one place F's relative standing
  vs. B improves somewhat (3/6 seed wins, ahead on precision@5%) — a
  genuinely mixed result, reported honestly rather than as a headline.

## 27. What Phase 3.5 does NOT establish

- That F generalizes *better* than B under attack — not shown; the
  evidence is that they degrade similarly and remain close, not that
  either is clearly more attack-robust than the other.
- That F is complementary to B — this phase's core objective was attack
  generalization, not complementarity; the (unperformed) complementarity
  sub-experiment described in `configs/phase3_5_attack_protocol.json`
  remains a required, separate follow-up gate (per the brief section 23),
  not attempted here.
- Anything about real-world attack robustness or security — every
  condition here is a synthetic, deterministic transform of a synthetic
  benchmark.
- Robustness to attack types outside the tested matrix (adversarial
  perturbations, different feature subsets, combined attacks, concept
  -level attacks).
- Statistical significance in the classical sense — every interval here
  is descriptive (n=6 cross-seed, or single-seed bootstrap), not a
  hypothesis test.

## 28. Recommendation

**Formal status:**

# 🟢 GENERALIZATION SUPPORTED

*in the specific, narrow sense defined for this phase*: F demonstrates
consistent robustness under the three predefined, unseen covariate-shift
attack conditions — its clear advantage over no-signal and the original
Failure Memory persists, its degradation under attack is proportionate to
(not worse than) calibrated confidence's own degradation, and it never
collapses to an uninformative signal while other candidates remain
useful. It remains **competitive with, but not superior to**, calibrated
confidence at every tested severity — consistent with, not contradicting,
Phase 3.4's frozen 🟡 INCONCLUSIVE finding on the (different) question of
whether F beats or is complementary to B.

**Whether this justifies moving forward:** The evidence justifies
treating F as a candidate that does not become unreliable or dangerous
relative to the existing baselines under the tested attack conditions —
useful evidence for eventually considering it, but not authorization to
use it. Per the brief's gate (section 33), **before any autonomous
integration of Failure Risk**, the project still needs:

1. The complementarity sub-experiment (B alone vs. F alone vs. a simple,
   pre-specified B+F model) — explicitly deferred from Phase 3.5, not
   performed here.
2. Dedicated calibration/operational-risk analysis beyond the ECE numbers
   already reported.
3. A defined, tested policy for safe decision thresholds and downstream
   recovery consequences — none of which exists yet.

Phase 3.5 is evidence. It is not authorization. **No autonomous
integration, recovery, retraining, or deployment work is performed in
this phase**, and Phase 3.6 is explicitly not begun.


---

<a id="phase3-6-diagnosis-abstention-recovery"></a>
# PHASE3 6 DIAGNOSIS ABSTENTION RECOVERY
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`  
**Role:** Phase 3.6 diagnosis/abstention/recovery study (synthetic data).

# Phase 3.6 — Diagnosis, Abstention & Recovery

**Status: COMPLETE.** This document is the Phase 3.6 deliverable.

Companion artifacts: [`configs/phase3_6_decision_recovery_protocol.json`](../configs/phase3_6_decision_recovery_protocol.json), [`benchmarks/phase3_6_{complementarity,decision_policy,diagnosis,recovery,leakage_audit,export_csv}.py`](../benchmarks/), [`experiments/results/phase3_6/`](../experiments/results/phase3_6/), [`tests/integration/test_phase3_6_*.py`](../tests/integration/).

## 1. Objective

Determine whether the available risk signals (calibrated confidence B,
Supervised Failure Risk F, and their simple combination) can safely
support failure diagnosis, abstention, and recovery decisions — and what
the actual consequences of those decisions are — without assuming the
answer is "yes."

## 2. Relationship to Phase 3.1–3.5

Phase 3.4 found F does not beat B (🟡 INCONCLUSIVE, frozen, not
revisited). Phase 3.5 found F's standing relative to B/C/A persists under
synthetic covariate-shift attacks (🟢 GENERALIZATION SUPPORTED, in the
narrow sense that F doesn't collapse relative to B). Phase 3.6 moves from
**prediction** to **decision, action, and outcome**: given these already
-established scores, does turning them into abstain/review/recover
decisions produce a safe, useful system? It reuses F, B, and Phase 3.5's
attack machinery entirely unmodified.

## 3. Frozen protocol

`configs/phase3_6_decision_recovery_protocol.json`, written before any
Phase 3.6 result was computed. Inherits Phase 3.1's seeds
`[1,2,3,4,5,42]`, primary seed `42`, coverage points, and bootstrap
settings unchanged. Defines: the complementarity model, tier thresholds,
cost model (with disclosed sensitivity ratios), diagnosis taxonomy/rule,
recovery policy, and acceptance criteria — all fixed before evaluation.

## 4. Complementarity experiment (3.6.1)

`CombinedRisk`: a 2-input `LogisticRegression(max_iter=1000,
random_state=seed)` on `[1-confidence, F.risk(...)]`, fit once per seed on
regime-2 data only (verified: fit array length == regime-2 size, zero
row-hash overlap with the test stream).

| Candidate | AUROC | AUPRC | AURC | ECE |
|---|---|---|---|---|
| B alone | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 | 0.0823 |
| F alone | 0.6548 [0.6159, 0.6938] | 0.3912 | 0.1972 | 0.0753 |
| **B+F combined** | **0.6593 [0.6176, 0.7010]** | 0.3962 | 0.1944 | 0.0789 |

Paired per-seed: BF − B AUROC mean = **−0.0006**, 95% CI **[−0.0058,
0.0046]** — includes zero. BF beats B on only **2/6** seeds.

**Interpretation: Case B — B+F ≈ B.** The combined model is
statistically indistinguishable from B alone on every metric. **F does
not add measurable incremental predictive information beyond calibrated
confidence on this benchmark.** This is consistent with, and sharpens,
Phase 3.4's inconclusive finding: it is not just that F fails to beat B,
but that even a simple, well-specified combination of the two collapses
back to B's own performance — the strongest evidence yet in this project
that F's signal substantially overlaps with B's.

## 5. Operational decision policy (3.6.2)

Four risk tiers (LOW/MEDIUM/HIGH/CRITICAL) map onto the existing
`Decision` enum (ANSWER/REVIEW/ABSTAIN/ABSTAIN respectively). Evaluated
policies: `no_risk_policy` (always ANSWER), and one policy each for B, F,
BF_combined.

## 6. Threshold methodology

Per (candidate, seed): `t_50`, `t_80`, `t_95` = the 50th/80th/95th
percentile of that candidate's risk score on **regime-2 data only**
(never test), reusing the already-frozen Phase 3.1 coverage points
(5/20/50%) as the tier cut fractions rather than inventing new
percentiles. A test-time score is tiered by comparison against these
frozen cutoffs. Verified by the leakage audit (section 11) that these
arrays never include a test-stream row.

## 7. Cost model

Explicitly a **synthetic research assumption**, not a real cost
measurement (see disclaimer in the protocol file):

| Outcome | Cost |
|---|---|
| ANSWER, correct | 0.0 |
| ANSWER, incorrect | 5.0 |
| REVIEW, correct | 0.2 |
| REVIEW, incorrect | 5.2 |
| ABSTAIN, would have been correct (false abstention) | 1.0 |
| ABSTAIN, would have been incorrect (correct catch) | 0.3 |

Ordering (`abstain_incorrect < abstain_correct < answer_incorrect`) is
fixed before evaluation. Sensitivity analysis re-runs with
`answer_incorrect` at 2×, 5× (base), 10× the false-abstention cost.

## 8. Abstention methodology (3.6.4)

Reuses `precision_recall_at_coverage` directly at the frozen 5/10/20/50%
coverage points, reframed: precision = 1 − false-abstention-rate at that
abstention level; recall = failure-recall-among-abstained.

## 9. Diagnosis methodology (3.6.3)

**Scope discipline first:** the clean benchmark alone provides no causal
labels — every ordinary failure has the same "cause" (Bayes error near
the decision boundary). What Phase 3.5's attacks provide, that the clean
benchmark does not, is **known ground-truth condition identity** (we
chose which corruption was applied). Phase 3.6's diagnosis task is
therefore **condition attribution** — "which known corruption mechanism
produced this failure" — not deep causal inference, and is described that
way throughout, not oversold.

Because attacks are only ever applied to held-out regimes 3/4 (by Phase
3.5's own design, to avoid leaking attack identity into fitting), there
is no attacked regime-2 data to train a diagnosis *classifier* on without
either fabricating training data or leaking test-condition labels. The
diagnosis method used is therefore a **deterministic, zero-fitting rule**
(`src/evaluation/diagnosis.py`), not a trained model — carrying no
leakage risk by construction:

1. ≥2 exactly-zero features → `feature_dropout`
2. else `mean(x²) > 2.0` → `feature_noise`
3. else → `clean`

The threshold (2.0) is derived from the generator's own algebra (clean
E[x²]=1.0, mild-noise E[x²]=1.25, severe-noise E[x²]=3.25) — fixed before
any result was computed. Evaluated on failure samples pooled across
clean + all 3 attack conditions, per seed.

## 10. Recovery methodology (3.6.5)

Three deterministic actions, eligible only for CRITICAL-tier samples
(top 5%):

- **Retry** (trigger: diagnosed `feature_noise`): re-roll a *new*
  noise realization for the same sample (`attack_ordinal + 100`,
  deterministic), re-score with the same candidate/thresholds.
- **Reconfigure** (trigger: diagnosed `feature_dropout`): re-score using
  **B alone**, ignoring F/BF, against B's own thresholds.
- **Rollback** (trigger: diagnosed `clean`, or retry/reconfigure failed
  to clear HIGH): ABSTAIN — the universal safe fallback.

**Explicit structural non-action:** for diagnosed `clean`, no retry is
attempted at all — the workload model and its input are both
deterministic, so retrying an unattacked, unchanged sample against a
frozen model is provably a no-op. Stated as a finding, not silently
skipped. `max_retries = 1`; no timeout is fabricated (offline synthetic
benchmark, not applicable). Compared against `no_recovery` and
`retry_only` (retry-if-diagnosed-noise, no reconfigure attempted at all)
baselines, for three acting candidates (B, F, BF).

## 11. Leakage audit

`benchmarks/phase3_6_leakage_audit.py` — **all 8 checks passed**:
`threshold_and_complementarity_fit_only_on_regime2`,
`cost_model_matches_frozen_protocol`,
`tier_assignment_does_not_use_ground_truth`,
`diagnosis_is_deterministic_and_unfit`,
`recovery_policy_no_fit_calls`,
`diagnosis_precedes_outcome_check_in_recovery`, `seeds_unchanged`,
`duplicate_samples_regime2_vs_test`. No STOP condition triggered.

## 12. Prediction results

See section 4 (B/F/BF AUROC/AUPRC/AURC/ECE) — no change from Phase 3.4's
frozen clean-benchmark numbers; B remains the strongest single signal.

## 13. Decision results

Cross-seed means at the base cost ratio (5.0):

| Policy | Unsafe action rate | Abstention rate | Expected cost | Utility retention |
|---|---|---|---|---|
| no_risk_policy | 0.2806 | 0.000 | 1.4028 | 1.000 |
| **B** | **0.2258** | 0.297 | **1.0602** | 0.703 |
| F | 0.2481 | 0.195 | 1.1966 | 0.805 |
| BF_combined | 0.2475 | 0.195 | 1.1934 | 0.805 |

**Sensitivity across cost ratios (2×/5×/10×):** at ratio 2.0, *every*
risk-based policy has HIGHER expected cost than doing nothing
(no_risk_policy = 0.561; B = 0.579; F = 0.598; BF = 0.596) — abstention
only pays off once missing a failure is costly enough. At ratios 5.0 and
10.0, B is cheapest of all four policies; F and BF beat no_risk_policy at
both of those ratios too. Per the protocol's pre-registered acceptance
rule (preference must hold at ≥2/3 ratios), **B, F, and BF are all
preferred over no-intervention — but B is the uniformly best-costing
policy at every ratio tested**, trading more abstention (29.7% vs.
19.5%) for a lower unsafe-action rate and lower cost than F/BF at every
tested ratio.

## 14. Abstention results

At 5% coverage (highest-risk 5% abstained): B → 43.6% precision / 8.0%
recall; F → 43.8% / 8.1%; BF → near-identical to F (all three numbers
reproduce Phase 3.4's clean-condition figures exactly, since this reuses
the same scores). No abstention policy is dramatically more effective
than another at catching failures early — consistent with section 4's
complementarity finding.

## 15. Diagnosis results

Pooled across all 6 seeds (32,000 failure samples):

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| clean | 0.393 | 0.928 | 0.552 | 5,050 |
| feature_noise | 0.937 | 0.425 | 0.585 | 12,585 |
| feature_dropout | **1.000** | **1.000** | **1.000** | 6,363 |

Overall accuracy **0.683**, macro F1 **0.712**.

**Reading this honestly:** dropout is perfectly diagnosable (it's a
deterministic, unambiguous corruption). Feature-noise recall is only
42.5% — as predicted a priori (E[x²]=1.25 for mild noise heavily
overlaps clean's E[x²]=1.0), most **mild**-noise failures are
misdiagnosed as `clean`, dragging "clean" precision down to 0.393 (most
things the rule calls "clean" are actually misdiagnosed noise failures).
This is exactly the limitation the frozen protocol predicted before
running any evaluation — not a surprise, and not concealed.

## 16. Recovery results

Recovery-eligible (CRITICAL-tier) population, pooled across seeds and all
4 conditions:

| Acting candidate | Attempt rate | Success rate | Failure rate |
|---|---|---|---|
| B | 14.0% [10.7%, 17.3%] | 54.7% | 45.3% |
| F | 23.4% [17.7%, 29.2%] | 55.7% | 44.3% |
| BF | 24.4% [17.1%, 31.7%] | 55.0% | 45.0% |

**`retry_only` and `diagnosis_gated` produced numerically IDENTICAL
results for all three acting candidates, every seed.** Investigated
directly (not assumed): **zero** feature_dropout-diagnosed CRITICAL
samples were ever recovered by reconfiguration, for any acting candidate,
in any seed checked. Verified structurally: **reconfiguring to B alone
does not help under feature_dropout, because B's calibrated confidence is
computed from the SAME corrupted context and is equally elevated** — B is
not an independent fallback signal here, it shares the corruption's
effect. This is a genuine negative result about the reconfigure action
specifically, not a bug (confirmed: `check_diagnosis_precedes_outcome_
check_in_recovery` passes; the branch is exercised, just never succeeds).

Retry (for feature_noise) recovers 14–24% of the CRITICAL population
depending on acting candidate, but only about **55% of recoveries are
actually correct** — retry is close to a coin flip once it does clear the
risk threshold.

## 17. Safety analysis

- **No recovery action ever converts a would-have-succeeded sample into a
  failure** — recovery only changes ABSTAIN into ANSWER/REVIEW, it never
  changes what the underlying (already frozen) workload model would have
  predicted. The only safety risk recovery introduces is **accepting a
  sample that is still actually wrong** (recovery_failure_rate,
  ~44–45%), i.e. exactly the risk category the frozen protocol requires
  reporting as "unsafe recovery."
- Reconfigure is safe by construction here (it never actually recovers
  anything, so it cannot introduce a new failure) — but that also means
  it provides zero benefit, which is itself worth flagging as wasted
  complexity, not a success.
- Retry's ~45% failure-rate-among-recoveries means **roughly 1 in 2
  "recovered" decisions under this policy is actually still a failure
  that would have been safely caught by rollback instead.** This is the
  single most important safety finding of Phase 3.6: **retry-based
  recovery, as currently defined, is not obviously safer than simply
  abstaining on every CRITICAL case.**

## 18. Utility analysis

Recovery's utility_retention_after_recovery (fraction of the CRITICAL
population it manages to answer instead of abstaining) ranges 14–24%
depending on acting candidate — a real but modest utility gain, bought at
the safety cost in section 17. B's lower recovery-attempt-rate (14.0%
vs. F/BF's ~23–24%) reflects B's smaller CRITICAL population to begin
with (B abstains more broadly per section 13), not a difference in
retry's per-attempt effectiveness (success rates are within 1–2 points of
each other across all three acting candidates).

## 19. Failure cases

- **Reconfigure recovering 0/N samples across every check performed** —
  reported prominently, not smoothed into an aggregate "recovery works"
  number.
- **Retry's ~45% failure rate** — nearly half of "successful" (tier
  -reducing) retries are still wrong. A system trusting retry's tier
  outcome alone, without checking the actual result, would be unsafe
  close to half the time on this subset.
- **Diagnosis misdiagnosing the majority of mild-noise failures as
  `clean`** — meaning under the full recovery policy, most mild-noise
  CRITICAL failures never reach the retry branch at all; they roll back
  via the `clean` branch instead (a safe outcome, but not the intended
  diagnosis-routing behavior).
- **At cost ratio 2.0, every intervention policy costs more than doing
  nothing** — reported, not hidden behind the base-ratio-5.0 headline
  number.

## 20. Limitations

- The cost model is a labeled synthetic assumption; no claim is made
  that its specific numbers reflect any real deployment's costs — only
  the qualitative ranking behavior (do interventions help, and under what
  ratio) is meant to generalize as a methodology.
- Diagnosis is condition-attribution against self-generated ground truth,
  not causal inference in an operational sense; it cannot distinguish
  finer-grained real-world failure causes this benchmark cannot
  represent.
- Recovery's "retry" and "reconfigure" actions are specific to this
  benchmark's mechanics (re-rollable synthetic noise; a second risk
  signal computed from the same corrupted input) and are not directly
  transferable design patterns to a real system without re-justification.
- Six seeds remains a small cross-seed sample; several recovery CIs
  (especially B's, with the smallest eligible population) are wide.

## 21. Threats to validity

- B and F/BF share the same underlying calibrator, which is why
  reconfigure-to-B provides no protection under feature_dropout — this is
  a structural property of this specific architecture, not a general law
  about confidence-based fallbacks.
- The diagnosis rule's threshold was derived from exact knowledge of the
  attack's construction (this project generated it); a real anomaly
  -detection rule would not have this privileged information.
- Recovery evaluation reuses Phase 3.5's synthetic attack conditions
  exclusively; no validation against any other corruption family was
  performed.

## 22. What Phase 3.6 establishes

- **F does not add measurable incremental value beyond calibrated
  confidence**, even under the most permissive test available (a
  simple, dedicated 2-feature combiner) — the clearest, most direct
  evidence in this project's history against F's incremental utility.
- **Risk-based decision policies (B, F, or BF) reduce expected cost and
  unsafe-action rate relative to no intervention**, but only once missing
  a failure is assumed sufficiently more costly than an unnecessary
  abstention (≥5× in this study) — the benefit is not unconditional.
- **B alone is the most cost-efficient decision policy tested** at every
  cost ratio evaluated, consistent with section 4's complementarity
  finding.
- **Diagnosis (condition attribution) is possible but imperfect** on this
  benchmark: dropout is perfectly detectable, feature-noise is
  detectable mostly at severe magnitude, mild-severity corruption is
  frequently indistinguishable from ordinary clean failures.
- **Retry-based recovery is real but risky** (~55% success among
  recoveries); **reconfigure-based recovery, as currently designed,
  provides zero measured benefit** because its fallback signal (B) is
  not independent of the corruption affecting the primary signal.

## 23. What Phase 3.6 does NOT establish

- That F is useless in general — only that it adds no measured value on
  this specific synthetic benchmark, under this specific combination
  method.
- That any specific cost ratio (2×, 5×, or 10×) is the "correct" one for
  any real system — these are labeled research assumptions.
- That the diagnosis taxonomy or recovery actions generalize beyond this
  benchmark's specific, self-generated attack mechanisms.
- That retry or reconfigure, as implemented, are safe or effective
  recovery strategies for a real deployed system — retry's near-50%
  failure-among-recoveries rate argues directly against that.
- Any form of production readiness, deployment safety, or autonomous
  reliability.

## 24. Formal decision

# 🟡 INCONCLUSIVE

Some components work as intended and produce genuinely useful,
honestly-measured evidence (decision policies reduce cost/unsafe-action
rate under a defensible cost assumption; dropout diagnosis is reliable;
retry recovers a meaningful fraction of CRITICAL cases). But the
evidence is **not sufficient for safe autonomous decision authority**:
complementarity is now more clearly negative than before (Case B, not
just inconclusive), reconfigure-based recovery provides zero measured
benefit, and retry-based recovery is wrong on roughly 45% of the cases it
"recovers" — a failure rate too high to trust unsupervised. **Calibrated
confidence (B) alone remains at least as good as, and operationally
cheaper than, every more complex alternative tested in this phase.**

**Is autonomous authority justified?** **No.** Per the frozen gate
(section 33 of the brief), Phase 3.6 being 🟡 does not itself authorize
anything, and even a 🟢 would not have. F/BF are not shown to add
value over B; retry's failure rate is a direct safety concern;
reconfigure does not work. Any authority granted must remain bounded,
reversible, monitored, and auditable — none of that infrastructure exists
yet, and this phase does not build it.

**What must happen next:** (1) given B alone is now the leading candidate
at every measured axis, seriously reconsider whether F/BF-based
components are worth their added complexity; (2) if retry-based recovery
is pursued further, its near-50% failure-among-recoveries rate must be
addressed (e.g. requiring a second confirmation signal after retry)
before any real trust is placed in it; (3) reconfigure needs a genuinely
independent fallback signal, not B, to have any chance of helping under
feature_dropout; (4) no further phase should proceed to deployment,
production infrastructure, or autonomous control on the strength of this
result.


---

<a id="phase3-freeze"></a>
# PHASE3 FREEZE
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_FREEZE.md`  
**Role:** Formal freeze declaration sealing Phase 3.1-3.6 (synthetic-data track) as historical baseline.

# Phase 3 Freeze

**Phase 3 (3.1 through 3.6) is COMPLETE and FROZEN as of this document.**

This freeze is a research-integrity and reproducibility measure. It does
**not** make the repository immutable. Future phases may introduce new
components, new datasets, new failure/recovery mechanisms, improved
representations, or replace existing components entirely — including
discovering that a component Phase 3 found weak becomes useful in a new
setting, or that a component Phase 3 found promising remains unnecessary.
Any such change is **new evidence**, evaluated on its own terms. What the
freeze prohibits is **silently altering the historical Phase 3 record** —
its protocols, results, or conclusions — to make later work look better
by comparison.

> Phase 3 is frozen. Future phases may build upon, replace, or extend its
> components, but Phase 3 protocols, results, and conclusions are
> preserved as the historical experimental baseline.

If a future phase modifies or replaces a component Phase 3 relied on
(e.g. `src/pipeline_builder.py`, `src/failure_memory/`, `src/reliability/`,
`src/evaluation/representations.py`), the **original implementation and
its Phase 3 results must be preserved** (e.g. under a version-tagged copy
or an explicit "superseded by" note), and the relationship between old
and new must be documented — not overwritten in place.

## What is frozen

**Protocols/configs** (do not edit values, thresholds, seeds, coverage
points, cost model, attack matrix, or diagnosis rule in these files):
- `configs/phase3_1_protocol.json`
- `configs/phase3_5_attack_protocol.json`
- `configs/phase3_6_decision_recovery_protocol.json`

**Benchmark/evaluation scripts** (Phase 3.1 → 3.6, do not modify fitting
procedures, seeds, or metric definitions):
- `benchmarks/phase3_1_evaluate.py`, `benchmarks/phase3_1_leakage_audit.py`
- `benchmarks/phase3_2_evaluate.py`
- `benchmarks/phase3_2c_ablation.py`
- `benchmarks/phase3_3_generalization.py`
- `benchmarks/phase3_4_compare.py`
- `benchmarks/phase3_5_attack_generalization.py`, `benchmarks/phase3_5_leakage_audit.py`
- `benchmarks/phase3_6_complementarity.py`, `benchmarks/phase3_6_decision_policy.py`, `benchmarks/phase3_6_diagnosis.py`, `benchmarks/phase3_6_recovery.py`, `benchmarks/phase3_6_leakage_audit.py`, `benchmarks/phase3_6_export_csv.py`
- `benchmarks/risk_coverage.py` (Phase 2 harness, reused unmodified by every Phase 3 script)

**Evaluation/source modules explicitly frozen during Phase 3** (each
phase's own docstrings/reports name these as unmodified — see each
`docs/PHASE3_*.md` for the specific "does not modify" list of that
phase):
- `src/evaluation/protocol.py`, `bootstrap.py`, `metrics.py`, `representations.py`
- `src/evaluation/attacks.py`, `complementarity.py`, `decision_policy.py`, `diagnosis.py`, `recovery.py`
- `src/pipeline_builder.py`
- `src/failure_memory/` (`memory.py`, `embedding.py`, `anticipatory.py`)
- `src/reliability/` (`workload_model.py`, `calibrator.py`)
- `src/data/synthetic.py`
- `src/decision/policy.py`
- `src/schema/events.py`

**Result artifacts** (never regenerate/overwrite to change a historical
number — a genuine reproducibility bug is grounds to STOP and document,
per every phase's own protocol, not to silently re-run):
- `experiments/results/phase3_1/`, `phase3_2/`, `phase3_2c/`, `phase3_3/`, `phase3_4/`, `phase3_5/`, `phase3_6/` (all files)

**Reports/documentation:**
- `docs/PHASE3_1_EVALUATION_PROTOCOL.md`
- `docs/PHASE3_2_REPRESENTATION_EXPERIMENTS.md`
- `docs/PHASE3_2C_CANDIDATE_ABLATION.md`
- `docs/PHASE3_3_GENERALIZATION.md`
- `docs/PHASE3_4_COMPARISON.md`
- `docs/PHASE3_5_ATTACK_GENERALIZATION.md`
- `docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`

**Tests and leakage audits** (all Phase 3.x tests under `tests/unit/` and
`tests/integration/` matching `test_phase3_*.py`, plus the leakage-audit
scripts listed above) — do not weaken or delete these to make a future
change pass more easily.

## Frozen conclusions (the historical record)

- **Phase 3.1** established the frozen evaluation protocol and the three
  original baselines (no signal, calibrated confidence, original Failure
  Memory).
- **Phase 3.2 / 3.2C** established that the original Failure Memory
  mechanism was weak (AUROC ≈ 0.514, barely above no-signal), while a
  supervised classifier extracted a real but modest signal — and that the
  supervised *classifier*, not the richer hand-designed representation,
  was the mechanism responsible.
- **Phase 3.3** supported generalization within the documented synthetic
  concept-drift scope (fixed features, rotated label boundary).
- **Phase 3.4** established that Supervised Failure Risk (F) did not
  consistently outperform calibrated confidence (B) — 🟡 INCONCLUSIVE.
- **Phase 3.5** supported robustness/generalization under the
  specifically tested synthetic covariate-shift attacks (feature noise,
  feature dropout), but did not establish superiority over B — 🟢
  GENERALIZATION SUPPORTED, narrowly (relative standing preserved, not
  superiority).
- **Phase 3.6** established that B+F provided no measurable incremental
  value over B alone (paired AUROC diff CI included zero); that
  calibrated confidence was the strongest and most cost-efficient signal
  under the tested synthetic cost assumptions; that failure-cause
  diagnosis was only partially successful (perfect on structurally
  unambiguous corruption, unreliable on mild perturbations); that
  retry-based recovery was real but unsafe (~45% failure rate among
  attempted recoveries); and that reconfiguration-based recovery provided
  zero measured benefit in the tested setting (its fallback signal shared
  the same corruption as the signal it was replacing) — 🟡 INCONCLUSIVE.
- **Autonomous decision authority is NOT justified** by any Phase 3
  result. This conclusion stands until a later phase produces new,
  independently evaluated evidence addressing complementarity,
  operational risk, calibration, and recovery safety at a level Phase 3
  did not reach.

## Verification performed at freeze time

- All expected result files exist under `experiments/results/phase3_{1,2,2c,3,4,5,6}/` (verified by directory listing).
- Spot-checked key numbers (Phase 3.1 `C_failure_memory` AUROC, Phase 3.2C Experiment B AUROC, Phase 3.4 F AUROC, Phase 3.5 clean-condition F AUROC, Phase 3.6 BF-vs-B paired diff, Phase 3.6 retry failure rate) against their source JSON files and confirmed they match the corresponding `docs/PHASE3_*.md` reports exactly.
- Confirmed `.gitignore` does not exclude `experiments/results/`, `configs/`, or `docs/` — no Phase 3 result artifact is silently untracked.
- Confirmed no Phase 4 files, directories, or references exist anywhere in the repository.
- Full test suite: **231 passed, 0 failed** (`python -m pytest -q`).


---

<a id="phase4-0-episodic-data"></a>
# PHASE4 0 EPISODIC DATA
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE4_0_EPISODIC_DATA.md`  
**Role:** Old Phase 4.0: synthetic episodic incident-stream generator.

# Phase 4.0 — Episodic Incident Data Generator

**Status: COMPLETE.** This document is the Phase 4.0 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md) section 1.

Companion artifacts: [`configs/phase4_0_episodic_protocol.json`](../configs/phase4_0_episodic_protocol.json),
[`src/data/episodic.py`](../src/data/episodic.py),
[`benchmarks/phase4_0_generate_episodes.py`](../benchmarks/phase4_0_generate_episodes.py),
[`benchmarks/phase4_0_leakage_audit.py`](../benchmarks/phase4_0_leakage_audit.py),
[`experiments/results/phase4_0/`](../experiments/results/phase4_0/),
[`tests/integration/test_phase4_0_episodic.py`](../tests/integration/test_phase4_0_episodic.py).

## 1. Objective

Phase 3's benchmark (`src/data/synthetic.py`) generates i.i.d. classification
samples under a single regime-drift condition — no recurring workload
identity, no incident recurrence over simulated time, no known/novel
ground truth. Phase 4.1 (failure memory), 4.2 (pattern learning), 4.3
(recovery strategy learning), 4.6 (continual learning), and 4.7
(generalization) all require exactly that structure. Phase 4.0 builds it,
without touching anything Phase 3 froze.

## 2. What is reused, unmodified, read-only

Per `docs/PHASE3_FREEZE.md` and the approved integration boundary
(`docs/PHASE4_PLAN.md` review decisions): `src.pipeline_builder.build_system`
(one call per workload seed), `src.data.synthetic.generate_regime_stream`
(regime-2 reconstruction for threshold derivation, exactly as
`benchmarks/phase3_3_generalization.py`'s `_reconstruct_regime2_with_confidences`
does), `src.evaluation.attacks.{apply_feature_noise,apply_feature_dropout}`,
`src.evaluation.decision_policy.{TierThresholds,assign_tier,RiskTier,
TIER_ACTION}`, `src.evaluation.diagnosis.diagnose`, and
`src.evaluation.recovery.attempt_recovery`. No new module wraps or edits
any of these in place; `src/data/episodic.py` is new, additive code that
calls them.

**Acting candidate: B (calibrated confidence) alone.** Phase 3.6 (frozen)
established B is the strongest, cheapest signal at every tested axis; F/BF
add no measured value. Driving the episodic stream's tiering/decision/
recovery off B alone is therefore the research-justified minimal choice,
not an arbitrary simplification — see
`configs/phase4_0_episodic_protocol.json.acting_candidate`. F/BF-driven
episode variants are explicitly deferred to a later subphase if a
`src/experience/` component needs them, not silently dropped.

## 3. What is genuinely new

- **4 independent "workloads"** (`workload_1..4`, seeds 101–104, disjoint
  from Phase 3's frozen seed list `[1,2,3,4,5,42]`) — each a distinct
  `build_system` call, i.e. a structurally different decision boundary
  (`base_w`), not a relabeling of one shared model.
- **A fixed condition vocabulary** (`clean`, `feature_noise_mild`,
  `feature_noise_severe`, `feature_dropout`) reusing Phase 3.5's frozen
  attack parameters verbatim (`configs/phase3_5_attack_protocol.json`),
  applied to each workload's own held-out `test_stream` (regimes 3+4,
  never used in that workload's own training).
- **Recurrence**: each known (workload, condition) combo occurs 5 times,
  each occurrence drawing a distinct 15-row chunk of that workload's
  `test_stream` and (for noise conditions) an independently-drawn
  corruption realization per occurrence (`attack_ordinal + occurrence_ordinal
  * 1000` — a genuinely new realization per recurrence, not a byte-identical
  repeat), so retry-recovery's re-roll is also unique per occurrence.
- **Known/novel combo split, fixed before generation**: 12 known combos
  recur across train/validation/test; 4 combos (`workload_4 ×
  {feature_noise_mild, feature_noise_severe, feature_dropout}` and
  `workload_1 × feature_dropout`) are entirely novel — zero occurrences
  before their single, frozen-test-only appearance. This gives two
  distinct, labeled generalization axes for Phase 4.7: a wholly unseen
  workload facing known condition families, and a well-known workload
  facing a condition it has never encountered.
- **Deterministic round-robin scheduling** across a global `step` index,
  so occurrences interleave through simulated time instead of bunching by
  combo, with novel combos scheduled strictly after every known-combo
  occurrence.
- **Per-combo chronological train/validation/test split**: occurrences
  0–2 → train, occurrence 3 → validation, occurrence 4 (chronologically
  last) → test — no combo's test occurrence ever precedes its own
  train/validation occurrences in `step` order.

## 4. Output schema (`EpisodeStep`)

One record per scored sample: `step`, `occurrence_ordinal`,
`sample_index_in_occurrence`, `workload_id`, `condition_id`,
`is_novel_combo`, `split`, `occurrence_count_for_combo`, `context`,
`true_label`, `predicted_label`, `confidence`, `b_risk_score`, `tier`,
`decision`, `is_failure`, `outcome`, and (CRITICAL-tier rows only)
`diagnosed_cause`, `recovery_attempted`, `recovery_action`,
`recovery_outcome`, `recovery_correct`. This is the full episode tuple
`docs/PHASE4_PLAN.md` section 1 specified, generated by scoring the new
incident structure through Phase 3.6's frozen decision/diagnosis/recovery
machinery — not a duplicate schema.

Information available at decision time vs. only after outcome: `context`,
`confidence`, `b_risk_score`, `tier`, `decision`, `diagnosed_cause`,
`recovery_action` are all knowable before the true label is checked;
`true_label`, `predicted_label` correctness, `outcome`, `is_failure`, and
`recovery_correct` are only knowable after — this distinction matters for
Phase 4.1's memory (which may only condition retrieval on pre-outcome
fields when simulating a live decision) and is preserved by keeping both
groups as separate, clearly-named fields rather than collapsing them.

## 5. Generated dataset (primary run, `configs/phase4_0_episodic_protocol.json` as committed)

| Metric | Value |
|---|---|
| Total steps | 960 |
| Workloads | 4 |
| Known combos | 12 |
| Novel combos | 4 |
| Train / Validation / Test rows | 540 / 180 / 240 |
| CRITICAL-tier rows | 109 |
| Recovery attempts | 109 |
| Recovered (RECOVERED outcome) | 9 |
| Content hash (SHA-256) | `c69a87ee877ed6090ed7e8d648d9da24fb8090fbb667b070724fe5d983f2057a` |

Regenerating with the same protocol reproduces this hash exactly (verified
by the leakage audit's `generation_is_deterministic` check and by manual
re-run during development). Full per-step records:
`experiments/results/phase4_0/episodes.json`; summary + environment
provenance: `experiments/results/phase4_0/manifest.json`.

The low recovered count (9/109 CRITICAL rows) is consistent with, not a
regression from, Phase 3.6's frozen finding that recovery only clears the
risk threshold for a modest minority of CRITICAL samples, and that
reconfigure recovers ~0% under `feature_dropout` — nothing here overrides
or is compared against that frozen result; the same recovery mechanics are
simply reused on a new incident stream.

## 6. Leakage/integrity audit — all 7 checks passed

`benchmarks/phase4_0_leakage_audit.py`:
`generation_is_deterministic`, `no_duplicate_rows_within_or_across_combos`,
`novel_combos_absent_from_train_and_validation`,
`novel_and_known_combo_sets_are_disjoint`,
`split_boundary_matches_protocol_rule`,
`chronological_no_future_leakage_within_combo`,
`no_regime_0_1_2_row_ever_emitted`. Result:
`experiments/results/phase4_0/leakage_audit.json`, `all_passed: true`. No
STOP condition triggered.

## 7. Tests

`tests/integration/test_phase4_0_episodic.py` — 13 tests, all passing:
the 7 leakage-audit checks run directly (not re-described), plus
structural assertions (expected combo/split row counts derived
arithmetically from the protocol, every context has exactly the 5 expected
feature keys, `decision` always matches `tier` via the frozen
`TIER_ACTION` mapping, recovery is attempted if and only if `tier ==
CRITICAL`, and `outcome`/`is_failure` are consistent with
`predicted_label` vs. `true_label`).

## 8. Limitations

- Only the B-alone acting candidate is used to drive tiering/decision/
  recovery in this generator; an F- or BF-driven episodic variant is not
  produced and would need its own protocol addendum if a later subphase
  needs it (unlikely, given Phase 3.6's finding that B alone is sufficient
  and cheapest).
- The condition vocabulary is exactly Phase 3.5's 3 attacks + clean — no
  new corruption mechanism is introduced; "novel condition" in this
  dataset always means a known mechanism applied to an unfamiliar
  workload/combo, not a mechanism the system has literally never seen in
  any form. This is a real scope limit for Phase 4.7's generalization
  claims and must be stated there, not overclaimed.
- Recurrence count (5 known-combo occurrences) and batch size (15) are
  small by design (fast, deterministic, inspectable smallest-valid-version
  choices per the Implementation Rule) — if Phase 4.6's continual-learning
  experiments need finer-grained checkpoints or more statistical power,
  this protocol's `recurrence` block would need a documented, pre-frozen
  revision (a new protocol version, not a silent edit of this one) before
  that experiment runs.
- Workload identity here is entirely synthetic (a different `base_w`
  decision boundary per seed) — it stands in for "a different deployed
  model/workload" structurally, not for any claim about real-world
  workload diversity.

## 9. What Phase 4.0 establishes

- A deterministic, reproducible, leakage-audited episodic incident
  generator exists and is tested — the structural prerequisite Phase 4.1
  through 4.7 needed and Phase 3's benchmark did not provide.
- Known-history and entirely-novel (workload, condition) combos are both
  represented in the frozen test split, with machine-checked disjointness
  from train/validation — Phase 4.7's generalization evaluation has real,
  labeled novel cases to test against, not an assumed novelty.
- All of this was built without editing any file `docs/PHASE3_FREEZE.md`
  lists as frozen, verified structurally (the `no_regime_0_1_2_row_ever_
  emitted` and `generation_is_deterministic` checks) rather than only by
  code inspection.

## 10. Next step

Per the frozen Phase 4 sequence, Phase 4.1 (Failure Memory & Experience
Learning) may now begin, using this episodic dataset's `train` split for
memory population and `validation`/`test` splits reserved per
`docs/PHASE4_PLAN.md` section 3's isolation protocol.


---

<a id="phase4-1-failure-memory"></a>
# PHASE4 1 FAILURE MEMORY
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE4_1_FAILURE_MEMORY.md`  
**Role:** OLD Phase 4.1: synthetic-only failure memory / experience retrieval (H1 PARTIALLY SUPPORTED). Superseded in role, not in content, by the ACTIVE Phase 4.1 later in this document -- see the Active Phase 4 Reassessment section for the relationship.

# Phase 4.1 — Failure Memory & Experience Learning

**Status: COMPLETE.** This document is the Phase 4.1 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md).

Companion artifacts: [`configs/phase4_1_experience_protocol.json`](../configs/phase4_1_experience_protocol.json),
[`src/experience/`](../src/experience/),
[`benchmarks/phase4_1_retrieval_evaluate.py`](../benchmarks/phase4_1_retrieval_evaluate.py),
[`benchmarks/phase4_1_leakage_audit.py`](../benchmarks/phase4_1_leakage_audit.py),
[`experiments/results/phase4_1/`](../experiments/results/phase4_1/),
[`tests/unit/test_experience_schema.py`](../tests/unit/test_experience_schema.py),
[`tests/integration/test_phase4_1_retrieval.py`](../tests/integration/test_phase4_1_retrieval.py).

## 1. Objective and hypothesis

**H1** (fixed before evaluation, `configs/phase4_1_experience_protocol.json`):
a structured, indexed experience store built on `ReliabilityEvent` +
episode outcome data can retrieve relevant past incidents for a new
failure with better-than-chance similarity ranking, without becoming an
unstructured log.

## 2. What was reused (inspected first, per 4.1.1)

- `src.schema.events.ReliabilityEvent` — the experience representation is
  built ON this, not a parallel schema. `workload_id`, `context`,
  `confidence`, `failure_risk`, `decision`, `abstained`, `is_failure`,
  `outcome`, `metadata` are used directly; nothing was duplicated.
- `src.storage.repository.EventRepository` / `src.storage.db` — reused
  unmodified for optional persistence (`ExperienceStore.persist`).
- `src.failure_memory.embedding.FailureEmbedder` — reused unmodified for
  the proposed method's similarity computation (identical embedding
  formula to `src.failure_memory.memory.FailureMemory.retrieve`, not
  reimplemented).
- `src.evaluation.diagnosis.diagnose` (indirectly, via Phase 4.0's
  `diagnosed_cause` field) — the decision-time proxy for condition
  identity.
- Phase 4.0's `experiments/results/phase4_0/episodes.json` — the sole
  data source; not regenerated, not modified.
- `docs/PHASE3_FREEZE.md` and `docs/PHASE4_PLAN.md` section 3 (isolation
  protocol) — governed every split-usage decision below.

No frozen Phase 3 file was edited. `src/failure_memory/` is unchanged;
`src/experience/` is new, additive code that calls into it read-only.

## 3. What was newly implemented

`src/experience/`:
- `schema.py` — `EpisodeProvenance` (episodic metadata `ReliabilityEvent`
  has no field for: `condition_id` ground truth, occurrence/step/split,
  diagnosis, recovery trace, protocol/dataset version), `DecisionTimeQuery`
  (the only type retrieval functions accept — structurally excludes
  `condition_id`/outcome/recovery fields, not just by convention; see
  §5), `Experience` (event + provenance), `experience_from_episode_record`
  (builder), `deterministic_event_id` (reproducible, not `uuid4`-random,
  so store content-hashing is meaningful).
- `store.py` — `ExperienceStore` (in-memory; `add`/`add_many`,
  `fit_embedder`, `retrieve_random`/`retrieve_recency`/`retrieve_similarity`,
  `persist`, `content_hash`), `build_store_from_episode_records`
  (split/failure-filtered builder).
- `metrics.py` — `precision_at_k`, `recall_at_k`,
  `same_workload_and_condition_rate` (secondary diagnostic),
  `count_relevant_in_store`.

`configs/phase4_1_experience_protocol.json` — frozen before evaluation:
data source and split rules, relevance definition, the 3 retrieval
methods, `k ∈ {1,3,5}`, the decay ablation (validation-only), and
pre-registered H1 acceptance criteria.

## 4. Data used / excluded

**Store population**: `split == "train"` AND `is_failure == true` rows
only (178 of Phase 4.0's 960 rows). Restricting to failures matches
`FailureMemory`'s existing store-only-failures convention (not a new
scope decision).

**Query sets**: `is_failure == true` rows from `split == "validation"`
(decay ablation only) and `split == "test"` (primary reported evaluation),
further split into `known_combo_test` (n=51) and `novel_combo_test`
(n=28), `all_test` = both pooled (n=79).

**Excluded**: every `validation`/`test` row, and every `is_failure ==
false` row, is never added to the store — enforced by
`build_store_from_episode_records`'s filter and verified by the leakage
audit (§6).

## 5. Decision-time vs. outcome vs. evaluation-only information

Enforced structurally, not by convention: `DecisionTimeQuery`
(`context`, `confidence`, `workload_id`, `tier`, `diagnosed_cause`,
`step`) has no field for `condition_id`, `true_label`, `outcome`,
`is_failure`, or any `recovery_*` value —
`tests/unit/test_experience_schema.py::
test_decision_time_query_has_no_outcome_or_ground_truth_fields` asserts
this directly against the dataclass's field set, so it fails loudly if
the type is ever extended carelessly. `condition_id` (Phase 4.0's
generator ground truth) is passed to `precision_at_k`/`recall_at_k`
directly by the benchmark script — never through a query object — and is
documented in `metrics.py`'s module docstring as evaluation-only.

## 6. Leakage/integrity audit — all 6 checks passed

`benchmarks/phase4_1_leakage_audit.py`: `store_contains_only_train_split`,
`store_contains_only_is_failure_true_rows`,
`decision_time_query_excludes_ground_truth_and_outcome_fields`,
`store_content_hash_is_deterministic`,
`no_validation_or_test_event_id_present_in_store`,
`retrieval_on_empty_store_returns_empty_not_error`. Result:
`experiments/results/phase4_1/leakage_audit.json`, `all_passed: true`.

## 7. Baselines and proposed method (4.1.6)

- **A — no-memory/uniform-random**: `retrieve_random(query, k, seed=42)`,
  ignores query content entirely.
- **B — recency-only**: `retrieve_recency(query, k)`, k most recent
  stored experiences by `step`, ignores content.
- **C — similarity (proposed)**: `retrieve_similarity(query, k,
  decay_lambda=0.0)`, k-nearest by `FailureEmbedder` embedding distance
  over context + confidence — the smallest research-valid mechanism
  (4.1.9), no recency weighting in the primary result.

No baseline was added or removed after seeing a result.

## 8. Metrics (4.1.7)

**Precision@k** = (# retrieved among top-k sharing `condition_id` with
the query) / (# actually retrieved, ≤ k). **Recall@k** = (# retrieved
among top-k sharing `condition_id`) / (total # train-split failures in
the store sharing that `condition_id`). Both `None` (not fabricated 0.0)
when undefined (empty retrieval / zero relevant population). 95%
percentile bootstrap CIs (1000 resamples, seed 0) over per-query values —
a small new utility (`_bootstrap_mean_ci`), documented as not reusing
`src.evaluation.bootstrap.bootstrap_ci` because that function's
`metric_fn(y_true, y_score)` signature doesn't fit a per-query-array use
case.

## 9. Results

Store size: 178 (train-split failures). Query groups: `all_test` n=79,
`known_combo_test` n=51, `novel_combo_test` n=28.

**Precision@k, mean [95% CI]:**

| Group | Method | k=1 | k=3 | k=5 |
|---|---|---|---|---|
| all_test | A random | 0.278 [0.190, 0.367] | 0.253 [0.224, 0.283] | 0.218 [0.180, 0.261] |
| all_test | B recency | 0.165 [0.089, 0.253] | 0.165 [0.089, 0.253] | 0.165 [0.089, 0.253] |
| all_test | **C similarity** | 0.241 [0.152, 0.342] | **0.283 [0.215, 0.354]** | 0.256 [0.208, 0.309] |
| known_combo_test | A random | 0.314 [0.176, 0.451] | 0.255 [0.216, 0.288] | 0.255 [0.192, 0.314] |
| known_combo_test | B recency | 0.255 [0.137, 0.373] | 0.255 [0.137, 0.373] | 0.255 [0.137, 0.373] |
| known_combo_test | **C similarity** | 0.314 [0.196, 0.431] | **0.346 [0.268, 0.418]** | 0.298 [0.239, 0.361] |
| novel_combo_test | A random | 0.214 [0.071, 0.358] | 0.250 [0.190, 0.298] | **0.150 [0.114, 0.179]** |
| novel_combo_test | B recency | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| novel_combo_test | C similarity | 0.107 [0.000, 0.250] | 0.167 [0.071, 0.274] | 0.179 [0.107, 0.264] |

Full precision/recall (all k, both metrics, all groups) + the decay
ablation: `experiments/results/phase4_1/retrieval_results.json`.

**Decay ablation (validation split only, precision@k, method C):**
`decay_lambda ∈ {0.0, 0.01, 0.05, 0.1}` produced precision@1/3/5 of
`{0.40, 0.35, 0.33}`, `{0.44, 0.34, 0.30}`, `{0.36, 0.37, 0.30}`, `{0.36,
0.34, 0.32}` respectively — no `decay_lambda` value shows a consistent
improvement over `0.0` across k; differences are within what 25-query
validation noise would produce. **Conclusion: no recency weighting is
adopted.** The primary reported method C result (`decay_lambda=0.0`)
stands as the frozen default per the protocol — this ablation was
evaluated, found not to help, and reported as a negative finding, not
silently dropped.

## 10. Is H1 supported? — Per the pre-registered acceptance criteria

Applying `configs/phase4_1_experience_protocol.json`'s
`acceptance_criteria` exactly as written (CI *lower bound* of C must
exceed *both* baselines' point estimates, same group/k):

- **`known_combo_test`, k=3**: C = 0.346, CI = [0.268, 0.418] — CI lower
  bound (0.268) exceeds both A's (0.255) and B's (0.255) point estimates.
  **Criterion met.**
- **`all_test`**, every k, and **`known_combo_test`** at k=1/k=5: C's CI
  lower bound does NOT clear both baselines (closest miss:
  `all_test` k=5, CI low 0.208 vs. A's 0.218). **Criterion not met.**
- **`novel_combo_test`**: C never clears baseline A at any k, and at k=1
  C (0.107) is numerically *below* A (0.214) — random guessing
  outperforms similarity retrieval on this group at k=1. **Criterion not
  met; directionally unfavorable to C.**

Per the protocol's `H1_partially_supported` definition ("Method C beats
both baselines by the criterion above on SOME but not all k values, or
on known_combo_test but not novel_combo_test"), this is exactly that
case.

## 11. Formal decision

# 🟡 H1: PARTIALLY SUPPORTED

Structured similarity retrieval clears the pre-registered bar against
both no-memory-random and recency-only baselines in exactly one tested
condition (`known_combo_test`, k=3), and is directionally favorable
(though not statistically clearing the bar) at most other known-combo
k's. It reliably, consistently beats the recency-only baseline (B) across
every group and k — recency alone carries no useful signal here, which
is itself a finding (B's precision is flat across k because it always
retrieves the same fixed most-recent-k set for every query, evidently a
population whose condition mix does not track any individual query's
condition). It does **not** reliably beat pure random retrieval (A) on
pooled `all_test`, and on `novel_combo_test` it is sometimes *worse* than
random at k=1.

## 12. Failure-case analysis

- **Why C underperforms A on `novel_combo_test` at k=1**: novel-combo
  queries come from a workload/condition pair the store has zero
  matching examples of; the nearest store neighbor by raw embedding
  distance is then whatever failure (any workload, any condition)
  happens to sit closest in the 2-PCA-component + confidence-derived
  embedding space — which is not guaranteed to share the query's
  condition, and single-nearest-neighbor (k=1) has no averaging effect to
  dampen an unlucky closest match. Random retrieval, by chance, sometimes
  does better simply because the store's overall composition happens to
  favor conditions common across workloads.
- **Why recency-only (B) is flat and weak**: `retrieve_recency` returns
  the same fixed set of the most-recent-`step` stored experiences for
  every query, regardless of content — precision@k is therefore just that
  fixed set's own condition-match rate against whichever query is asked,
  which cannot adapt to different queries; it collapses to near-zero on
  `novel_combo_test` because that fixed recent set essentially never
  happens to share a novel query's specific condition.
- **Sample-size caution**: `novel_combo_test` (n=28) and even
  `known_combo_test` (n=51) are small; several CIs are wide and
  overlapping between methods (e.g. `all_test` k=1 and k=3 for A vs. C).
  The one criterion-clearing result (`known_combo_test`, k=3) should be
  read as suggestive, not decisive, given six query-group/k combinations
  were checked and only one cleared the bar — some chance this reflects
  multiple-comparisons noise rather than a robust effect; this is stated
  as a limitation, not adjusted away post hoc (no correction was
  pre-registered, so none is applied retroactively either).

## 13. Limitations

- Relevance is defined at the `condition_id` (corruption-mechanism)
  level, not workload-specific — a deliberate, documented scope choice
  (§8), not an oversight; `same_workload_and_condition_rate` exists as a
  secondary diagnostic but was not the primary metric.
- The embedding (`FailureEmbedder`: 2-component PCA + 2
  confidence-derived scalars) is the exact, unmodified Phase 2/3
  representation — no new representation was developed for Phase 4.1;
  if H1's partial support is representation-limited rather than
  retrieval-mechanism-limited, this evaluation cannot distinguish the two
  (a Phase 4.2 concern, not addressed here).
- `novel_combo_test`'s "novelty" is exactly Phase 4.0's documented scope
  (workload/condition combination novelty, not novel corruption
  mechanisms) — carried forward from `docs/PHASE4_0_EPISODIC_DATA.md`
  section 8 verbatim, per the review requirement that this limitation
  remain part of the record.
- No persistence-layer evaluation was performed at scale (the `persist`/
  reload round trip is tested for correctness on 5 rows, not benchmarked
  for retrieval performance from a reloaded store — out of scope, no
  Phase 4.1 experiment needed it).

## 14. Progression note (per the review's research-integrity clarification)

Phase 3.6 (frozen) found F/BF add no measured value over calibrated
confidence B for *prediction*. Phase 4.1 asks a structurally different
question — can *retrieval over stored failure history* (not a fitted
risk score) find relevant past incidents — and finds partial,
condition-dependent support. These are independent findings about
different mechanisms; Phase 3.6's result is not touched, revisited, or
implied to be resolved by this one. If a later Phase 4 subphase (e.g.
4.2's pattern learning, which may use a different or enriched
representation) produces evidence that further resolves whether
retrieval-based memory is useful, that will be recorded as: **Phase 4.1
→ PARTIALLY SUPPORTED (this document) → new Phase 4.X evidence →
combined conclusion**, in a new document — not by editing this one.

## 15. Deliverables checklist

1. `src/experience/` implementation — done (`schema.py`, `store.py`, `metrics.py`).
2. Phase 4.1 tests — done (6 unit + 12 integration = 18, all passing).
3. Retrieval/evaluation benchmark — done (`benchmarks/phase4_1_retrieval_evaluate.py`).
4. Baseline implementations — done (A, B in `ExperienceStore`).
5. Reproducible configuration — done (`configs/phase4_1_experience_protocol.json`).
6. Learned-state/provenance artifact — done (`ExperienceStore.content_hash()`, recorded in `retrieval_results.json`).
7. Phase 4.1 experiment results — done (`experiments/results/phase4_1/retrieval_results.json`).
8. Failure-case analysis — done (§12).
9. Metric definitions — done (§8, `src/experience/metrics.py` docstrings).
10. `docs/PHASE4_1_FAILURE_MEMORY.md` — this document.
11. Full test-suite results — 244/244 pre-existing + 18 new = 262/262 (see completion report).
12. Phase 4.1 verification/completion record — §11 (formal decision) + this checklist.

## 16. Final status

# 🟡 PASS WITH ISSUES

Implementation, evaluation, documentation, and research-integrity checks
are complete. H1 is **partially supported**: the proposed mechanism is
implemented correctly, is measurably better than the recency baseline
everywhere and better than random in the one condition it was
pre-registered to be judged strongest in (`known_combo_test`), but does
not clear the pre-registered bar against random retrieval when pooled,
and is directionally unfavorable on the hardest (`novel_combo_test`)
group at low k. This is reported as-is — a mixed, not uniformly positive,
result — consistent with the research-integrity requirement not to treat
implementation success as hypothesis support.


---

<a id="phase4-2-failure-patterns"></a>
# PHASE4 2 FAILURE PATTERNS
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE4_2_FAILURE_PATTERNS.md`  
**Role:** OLD Phase 4.2: synthetic-only failure pattern learning (H2 INCONCLUSIVE). This verdict is NOT changed anywhere in this document.

# Phase 4.2 — Failure Pattern Learning

**Status: COMPLETE.** This document is the Phase 4.2 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md) and the Phase 4.2 authorization.

Companion artifacts: [`configs/phase4_2_pattern_protocol.json`](../configs/phase4_2_pattern_protocol.json),
[`src/patterns/`](../src/patterns/),
[`benchmarks/phase4_2_pattern_evaluate.py`](../benchmarks/phase4_2_pattern_evaluate.py),
[`benchmarks/phase4_2_leakage_audit.py`](../benchmarks/phase4_2_leakage_audit.py),
[`experiments/results/phase4_2/`](../experiments/results/phase4_2/),
[`tests/unit/test_pattern_discovery.py`](../tests/unit/test_pattern_discovery.py),
[`tests/integration/test_phase4_2_patterns.py`](../tests/integration/test_phase4_2_patterns.py).

## 1. Hypothesis

**H2** (fixed before final evaluation, `configs/phase4_2_pattern_protocol.json`):
recurring failure patterns (condition recurrence, temporal clustering,
symptom→cause→outcome relationships) are detectable above chance in the
episode stream, and the system can correctly separate observed evidence
from inferred pattern from confirmed relationship from uncertain
hypothesis using four explicit confidence tiers.

Phase 4.2 is a distinct question from Phase 4.1: 4.1 asked whether a
*single* relevant prior incident can be retrieved; 4.2 asks whether a
*recurring relationship across multiple* incidents can be identified and
its strength graded.

## 2. Inspection performed before implementation (per the authorization's section 5)

Phase 4.0's generator (`src/data/episodic.py`) and dataset
(`experiments/results/phase4_0/episodes.json`), Phase 4.1's `src/experience/`
(schema/store/metrics/protocol/results), `src.failure_memory.embedding`,
the frozen Phase 3.6 diagnosis taxonomy (`src/evaluation/diagnosis.py`),
`docs/PHASE3_FREEZE.md`, `docs/PHASE4_PLAN.md`, and the Phase 4.1
completion report were all read before writing any Phase 4.2 code.

**Reuse decisions:**
- `diagnosed_cause` (Phase 4.0's per-row field, itself computed via the
  frozen, unmodified `src.evaluation.diagnosis.diagnose`) is used as the
  decision-time-observable "symptom" side of the pattern claim — not
  recomputed, not reimplemented.
- `condition_id` (Phase 4.0 ground truth) is reused as the discovery/
  evaluation-only ground truth, exactly as Phase 4.1 used it — never
  exposed through a live-query type.
- `src.failure_memory.embedding.FailureEmbedder`'s KMeans-style clustering
  (identified in `docs/PHASE4_PLAN.md` section 4.2 as a *candidate*
  pattern-detection primitive) was inspected and **not used**: with only
  28 train-split CRITICAL-failure rows total (§4), fitting any clustering
  model would be operating far below a sample size where cluster
  assignments could be trusted, and — more importantly — the actual
  pattern claim under test here (does a `diagnosed_cause` reliably map to
  one `condition_id`) is already a direct, interpretable frequency/purity
  question that clustering would not answer more directly. This is a
  documented "reuse is not automatically adequate" decision, not an
  oversight.
- Phase 4.1's structural pattern (a type — `PatternQuery` here, mirroring
  `DecisionTimeQuery` — that syntactically cannot carry ground truth) is
  reused as the design template for leakage prevention, applied fresh to
  the pattern-learning problem (`src/patterns/schema.py`), not copied
  code.
- No frozen Phase 3 file, Phase 4.0 dataset file, or Phase 4.1 result file
  was modified.

## 3. What is a "pattern"? (fixed before evaluation)

A pattern **candidate** is keyed by `(workload_id, diagnosed_cause)`. The
claim under test is a **symptom→cause relationship**: does this
`diagnosed_cause`, for this workload, reliably correspond to one
particular true `condition_id`? A key is a candidate at all only if it
recurs in the train split (`n_train >= 2`) — a singleton is not
recurrence by definition and is excluded entirely, not folded into the
lowest tier.

This is a narrower pattern definition than the full space section 8 of
the authorization lists (condition recurrence, temporal clustering,
symptom→cause, cause→outcome, combined chains). The primary
precision/recall-evaluated mechanism covers **condition recurrence +
symptom→cause** (A and C in that list). **Temporal clustering** (B) and
**cause→outcome** (D) are implemented as separate, descriptive-only
secondary analyses (§8), not folded into the same tiered
precision/recall machinery — combining five different pattern types into
one scored mechanism was judged to overreach the smallest-research-valid
version this dataset's size (§4) could actually support; the scope
narrowing is stated here, not silently absorbed.

## 4. Data used, and a real scope constraint

`diagnosed_cause` only exists on CRITICAL-tier rows (diagnosis, per the
frozen Phase 3.6 policy Phase 4.0 reuses unmodified, is only computed for
CRITICAL-tier samples). This shrinks the usable population sharply:

| Split | is_failure & diagnosed_cause-not-null rows |
|---|---|
| train | 28 |
| validation | 4 |
| test | 14 |

This is a real, load-bearing limitation, not a bug: Phase 4.0's dataset
was sized for its own Phase 4.0 purpose, and CRITICAL-tier diagnosis
availability was not specifically tuned for Phase 4.2's needs. It is
carried into every result below.

**Split usage**: train → candidate discovery (recurrence counts, mode
condition, train-purity). Validation → CONFIRMED-tier replication check
only (permitted per `docs/PHASE4_PLAN.md` section 3: "confidence-tier
calibration"). Test → final, one-time row-level evaluation only —
verified never to influence discovery (§7).

## 5. Methodological integrity disclosure

During protocol design, candidate feasibility was checked against
train/validation counts to confirm the chosen thresholds would produce a
non-degenerate tier distribution (permitted). While doing this, a small
number of test-split row values were also inadvertently reviewed during
interactive design-phase scoping, **before** `configs/phase4_2_pattern_protocol.json`
was frozen. No threshold, baseline, or acceptance criterion in that file
was chosen or adjusted based on that inadvertent observation — the tier
thresholds were fixed from train/validation reasoning alone, and the
`minimum_evaluable_n = 10` acceptance bar was set from a generic,
dataset-independent small-sample convention, not reverse-engineered from
the realized test count (which turned out to be 7, i.e. below that bar —
see §10). This is disclosed here rather than concealed, per the
research-integrity requirement to report irregularities honestly. No
result below was altered because of this; the concern is about the
*process*, and it is recorded so the reader can judge it independently.

## 6. The four evidence tiers

`src/patterns/schema.py`'s `EvidenceTier` (`OBSERVED`, `INFERRED`,
`CONFIRMED`, `UNCERTAIN`) and `src/patterns/discovery.py::assign_tier`,
applied in this precedence (from the frozen protocol):

1. `n_train < 2` → not a candidate (excluded).
2. `n_train ≥ 6` AND `purity_train ≥ 0.8` AND validation replicates
   (`n_validation ≥ 1` and `purity_validation ≥ 0.5`) → **CONFIRMED**.
3. `purity_train ≥ 0.6` → **INFERRED**.
4. `n_train < 3` → **UNCERTAIN**.
5. else → **OBSERVED** (recurs with trustworthy n, but purity below the
   INFERRED bar — recurrence without an established relationship).

## 7. Leakage/integrity audit — all 5 checks passed

`benchmarks/phase4_2_leakage_audit.py`:
`pattern_query_excludes_ground_truth_and_outcome_fields`,
`no_candidate_derived_only_from_test_split`,
`candidacy_rule_excludes_n_train_below_2`, `discovery_is_deterministic`,
`empty_candidate_or_row_set_handled_gracefully`. Result:
`experiments/results/phase4_2/leakage_audit.json`, `all_passed: true`.
An additional integration test
(`test_no_test_split_row_influences_candidate_discovery`) confirms the
check is not vacuous: deliberately contaminating train with test rows
*does* change the discovered candidates, proving the real (uncontaminated)
build is meaningfully test-blind, not just untested for it.

## 8. Discovered candidates (train + validation)

| Workload | Diagnosed cause | n_train | Mode condition (train) | Purity (train) | n_validation | Purity (validation) | Tier |
|---|---|---|---|---|---|---|---|
| workload_1 | clean | 2 | clean | 1.00 | 0 | — | INFERRED |
| workload_2 | clean | 4 | clean | 0.75 | 1 | — | INFERRED |
| workload_2 | feature_noise | 2 | feature_noise_severe | 1.00 | 0 | — | INFERRED |
| workload_3 | clean | 5 | clean | 0.60 | 0 | — | INFERRED |
| workload_3 | feature_dropout | 7 | feature_dropout | 1.00 | 1 | 1.00 | **CONFIRMED** |
| workload_4 | clean | 4 | clean | 1.00 | 1 | 1.00 | INFERRED |

6 candidates discovered; **0 landed in OBSERVED or UNCERTAIN** in this
run — every recurring key that met the candidacy floor (n≥2) happened to
also clear the 0.6 purity bar for INFERRED. This is a real, honest
property of this particular realization (not a design flaw): the
OBSERVED/UNCERTAIN tiers exist and are exercised by the unit tests
(`tests/unit/test_pattern_discovery.py`), but this specific dataset
happened not to produce any candidate landing there.

## 9. Row-level evaluation (test split, n=14 total, 7 covered)

Coverage: 7/14 (50%) — test rows whose exact `(workload_id,
diagnosed_cause)` key exists among the 6 discovered candidates.
7 test rows fall under 3 of the 6 candidates
(`workload_2/feature_noise` n=1, `workload_3/clean` n=2,
`workload_4/clean` n=4); the other 3 candidates (including the one
CONFIRMED candidate, `workload_3/feature_dropout`) have **zero** test
occurrences of their exact key, so nothing about them could be verified
against held-out data in this run.

| Method | n_flagged | Precision | Recall |
|---|---|---|---|
| A — no pattern learning | 0 | undefined (0 flagged) | 0.0 |
| B — naive frequency (n_train≥3) | 6 | **0.333** | 1.0 |
| **C1 — tiered (proposed)** | 7 | 0.286 | 1.0 |
| C2 — ablation, no tiering (purity≥0.6, any n) | 7 | 0.286 | 1.0 |

Full detail: `experiments/results/phase4_2/pattern_results.json`.

**Tier calibration** (true-structure rate by tier, test split): only
`INFERRED` has any covered rows in this run (n=7, true-structure rate
0.286); `CONFIRMED`, `OBSERVED`, `UNCERTAIN` all have n=0 covered test
rows. **The CONFIRMED > INFERRED > OBSERVED/UNCERTAIN ordering cannot be
checked at all in this run** — the one CONFIRMED candidate had no test
occurrences to verify against.

## 10. Is H2 supported? — Per the pre-registered acceptance criteria

`n_covered_test_rows = 7 < minimum_evaluable_n = 10`. Per
`configs/phase4_2_pattern_protocol.json`'s `acceptance_criteria`, this
alone determines the verdict:

# 🟡 H2: INCONCLUSIVE (evidence volume insufficient)

This is the pre-registered outcome for `n_covered < 10`, decided by the
rule fixed before evaluation (§5's disclosure notwithstanding — the rule
itself does not depend on the specific realized count). It would be
mandated regardless of which way the point estimates leaned.

**For the record, since the numbers exist and are not being suppressed**:
the point estimates in this run are directionally **unfavorable** to the
proposed tiered method — baseline B (naive frequency-count flagging)
achieved *higher* precision (0.333 vs. 0.286) than both the proposed C1
and its C2 ablation, at equal recall (1.0 for all three non-trivial
methods). The reason is specific and traceable (§12): C1's INFERRED tier
admitted a `workload_2/feature_noise` candidate with only `n_train=2`
(purity 1.0, but on just 2 observations), which turned out wrong on its
single test occurrence; baseline B's simpler `n_train ≥ 3` floor happened
to exclude that exact candidate. This is reported as a genuine
observation from an underpowered run, not evidence that tiering is
generally worse than frequency-flagging — 7 covered rows is nowhere near
enough to draw that conclusion either way.

## 11. Ablation: C1 (tiered) vs. C2 (no tiering)

**C1 and C2 produced numerically identical results in this run**
(precision 0.286, recall 1.0, n_flagged 7): every discovered candidate's
train-purity happened to be ≥ 0.6, so C2's flat-threshold rule and C1's
tiered rule agreed on every single candidate's flag/no-flag decision.
**The ablation is uninformative in this specific run** — it cannot show
whether the tier system's small-sample humility (the `UNCERTAIN`
n<3 carve-out) or its validation-replication requirement (the
`CONFIRMED` gate) contribute anything, because no candidate in this
realization was close enough to those boundaries to produce a different
decision between C1 and C2. This is reported as a limitation of this
run's specific candidate set, not evidence that the ablation factors are
inert in general.

## 12. Failure-case analysis

- **Why C1 loses precision to B specifically**: `workload_2/feature_noise`
  (n_train=2, purity_train=1.0) is admitted by C1's INFERRED tier
  (purity ≥ 0.6 is checked before any n-floor in the frozen precedence —
  see §6 step 3 vs. step 4) but excluded by B's `n_train ≥ 3` floor. Its
  single test occurrence (`condition_id = feature_noise_mild`) did not
  match its train-derived mode (`feature_noise_severe`), so it
  contributed one false positive to C1/C2 that B never risked. This is
  exactly the kind of small-n instability the `UNCERTAIN` tier concept
  was designed to guard against — but the frozen precedence (purity check
  before the n-floor check, per the protocol as written) lets a high
  train-purity override the n-floor, so it didn't guard against it here.
  This is reported as a real, traceable finding about this specific
  tier-precedence design choice, not smoothed over.
- **Why CONFIRMED's tier-calibration claim can't be checked**: the one
  CONFIRMED candidate (`workload_3/feature_dropout`) simply has no test
  occurrence of that exact key — its test-split occurrence (§9's known
  combo, per Phase 4.0) either produced no CRITICAL-tier failure at all
  or one diagnosed as something else. Nothing about "does CONFIRMED
  actually mean higher precision" could be tested this round.
- **Sample size is the dominant explanation for all of the above** — not
  weak representation, not noisy diagnosis, not workload-specific
  effects. With 28 train / 4 validation / 14 test usable rows spread over
  potentially 16 (workload × diagnosed_cause) combinations, most cells
  are populated by 1-7 observations. This is consistent with, and does
  not contradict, Phase 4.1's own small-sample caution (`docs/PHASE4_1_FAILURE_MEMORY.md`
  section 12) — both subphases are bottlenecked by the same underlying
  Phase 4.0 dataset scale at the CRITICAL-tier population specifically.

## 13. Secondary analyses (descriptive, not part of H2's formal criteria)

**Temporal clustering (pattern type B)**: for all 12 known combos, the
inter-occurrence step gaps are **exactly constant** (gap variance = 0.0
in every case — e.g. `workload_1|clean`: gaps `[180, 180, 180, 180]`).
This is a direct, expected consequence of Phase 4.0's deterministic
round-robin scheduler (`src/data/episodic.py`), which spaces every
combo's occurrences evenly by construction. **No temporal clustering
(bursty recurrence) exists in this dataset, and none was expected** —
this is a property of the generator, not a finding about real-world
failure timing, and is reported as an honest null result rather than
omitted. `experiments/results/phase4_2/pattern_results.json`'s
`temporal_clustering` block has full detail for all 12 combos.

**Cause→outcome (pattern type D)**, train-split CRITICAL-tier recovery
attempts, grouped by `diagnosed_cause` (descriptive only — **not** used
to make or evaluate any recovery decision; that is Phase 4.3's separate
objective, per the authorization's closing instruction):

| Diagnosed cause | Attempts | Recovered | Rolled back | Recovered correct | Recovered incorrect |
|---|---|---|---|---|---|
| clean | 29 | 0 | 29 | 0 | 0 |
| feature_dropout | 11 | 0 | 11 | 0 | 0 |
| feature_noise | 10 | 3 | 7 | 2 | 1 |

This closely **replicates Phase 3.6's frozen findings** (`docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`
§16-17) on independently-generated Phase 4.0 data: `clean`-diagnosed
CRITICAL samples never attempt retry (matches Phase 3.6's structural
non-action finding exactly), `feature_dropout`-diagnosed samples recover
**0/11** via reconfigure (matches Phase 3.6's "reconfigure provides zero
measured benefit" finding), and `feature_noise`-diagnosed samples recover
a modest, imperfect fraction (3/10, of which 1/3 was actually incorrect).
This is stated as corroborating evidence on new data, not as a new
finding, and Phase 3.6's own frozen conclusion is not reopened or
restated as improved by it.

## 14. Limitations

- Pattern population is small (§4): 28/4/14 train/validation/test usable
  rows, a direct consequence of `diagnosed_cause` only existing on
  CRITICAL-tier rows. If more statistical power is needed for a future
  subphase, Phase 4.0's protocol would need a documented, pre-frozen
  revision (larger recurrence/batch parameters) — not attempted here,
  per the instruction not to modify Phase 4.0's frozen dataset.
- The pattern vocabulary evaluated with full precision/recall/tiering is
  narrower than the authorization's full list (§3) — temporal clustering
  and cause→outcome are descriptive-only secondary analyses, not scored.
- The tier precedence (purity check before the n-floor check) allows a
  high-purity, low-n candidate to reach INFERRED without ever passing
  through the n-floor gate that baseline B uses — this is exactly what
  the frozen protocol specifies, but §12 shows it has a real, traceable
  cost in this run; a future protocol revision could reorder this
  precedence, but that is a new experimental factor for a later
  subphase, not a change made here.
- The ablation (§11) is uninformative in this specific run because no
  discovered candidate sat near a tier boundary — this reflects the small
  candidate set, not a property of the tiering mechanism established one
  way or the other.
- "Novel" combinations (Phase 4.0's own documented scope) are not
  separately analyzed in Phase 4.2's row-level evaluation — with only 14
  test rows total and most falling in known combos by chance, splitting
  further by novelty would leave cells too small to report meaningfully;
  novelty-stratified pattern generalization remains primarily a Phase
  4.7 question, consistent with the authorization's section 14.
- §5's methodological disclosure: strict test-blindness during protocol
  design was not perfectly maintained; documented rather than concealed.

## 15. Progression note

Phase 4.1 (frozen): H1 **PARTIALLY SUPPORTED** — similarity retrieval
clears baselines only in the `known_combo_test, k=3` condition. Phase
4.2 (this document): H2 **INCONCLUSIVE**, evidence volume insufficient
(7 < 10 covered test rows), with directionally unfavorable-to-tiering
point estimates reported transparently. These are independent findings
about different mechanisms (single-incident retrieval vs.
multi-incident pattern/tier assignment) evaluated on overlapping but not
identical row populations. Neither result is rewritten by the other.
**Combined interpretation**: both Phase 4.1 and Phase 4.2, independently,
found that the smallest-valid mechanisms tested here provide at most
modest, inconsistent, sample-size-limited evidence of value on this
particular Phase 4.0 dataset scale — a pattern worth carrying into Phase
4.3's design (favor mechanisms and evaluations that are robust to, or
explicitly account for, this dataset's small CRITICAL-tier/failure
population), not a reason to abandon the overall Phase 4 research
program.

## 16. Deliverables checklist

1. Phase 4.2 implementation — done (`src/patterns/`).
2. Pattern representation/schema — done (`schema.py`: `EvidenceTier`, `PatternCandidate`, `PatternQuery`).
3. Pattern detection mechanism — done (`discovery.py::discover_candidates`, `assign_tier`).
4. Four-tier evidence mechanism — done (§6, exercised by unit tests for all 4 tiers).
5. Required baselines — done (A, B in `benchmarks/phase4_2_pattern_evaluate.py`).
6. Evaluation benchmark — done (`benchmarks/phase4_2_pattern_evaluate.py`).
7. Reproducible configuration — done (`configs/phase4_2_pattern_protocol.json`).
8. Leakage/integrity audit — done, 5/5 passed (§7).
9. Phase 4.2 tests — done, 14 unit + 9 integration = 23, all passing.
10. Full-suite test results — 285/285 (see completion report).
11. Pattern precision/recall results — done (§9).
12. Tier-level calibration results — done (§9, reported as unverifiable in this run — not fabricated).
13. Required ablation — done, reported as uninformative in this run (§11).
14. Failure-case analysis — done (§12).
15. Limitations — done (§14).
16. This document.
17. Formal completion record — §17 below.

## 17. Final status

# 🟡 INCONCLUSIVE

Implementation, evaluation, documentation, leakage audit, and
research-integrity checks are all complete, and every required mechanism
(4 evidence tiers, both baselines, the proposed method, the ablation, two
secondary pattern analyses) was built, tested, and evaluated. **H2 is
INCONCLUSIVE** — not because the mechanism failed to run, but because the
pre-registered minimum-evidence bar (10 covered test rows) was not met
(7 achieved), a direct consequence of Phase 4.0's CRITICAL-tier
population being small. The point estimates that do exist lean
unfavorably for the proposed tiered method relative to a naive
frequency-count baseline, for a specific, traced reason (§12) — reported
plainly rather than minimized. The cause→outcome secondary analysis did
independently replicate Phase 3.6's frozen recovery findings on new data,
which is a positive, if secondary, result. Per the completion rule,
"implementation success" and "hypothesis support" are reported as the
separate outcomes they are: implementation is a clean PASS; H2 support is
INCONCLUSIVE; the overall Phase 4.2 status is recorded as INCONCLUSIVE to
reflect the hypothesis-level result, not the implementation-level one.


---

<a id="phase3-real-data-feasibility-audit"></a>
# PHASE3 REAL DATA FEASIBILITY AUDIT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md`  
**Role:** Feasibility audit for expanding into real datasets (AgentRx, AIOps 2020, Alibaba GPU 2020).

# Phase 3 Real-Data Replication — Dataset Feasibility Audit

**Status: IN PROGRESS — preliminary audit complete for all 3 currently
acquired datasets.** This pass audits the three datasets fully staged
under `data/raw/`: **AgentRx**, **AIOps KPI**, and **Alibaba GPU2020**
(now including `pai_sensor_table.tar.gz`, whose download completed
during this pass — audited below, all 7 of 7 known GPU2020 archives
are now present and covered). Alibaba 2017 and Google Cluster Data
were never acquired — their `data/raw/` subdirectories were removed
(see prior cleanup) and they are absent from this audit entirely, not
marked PENDING.

This pass is **read-only inspection**. No raw file was modified,
moved, renamed, or extracted-in-place. Where archive contents needed
inspection (CSV rows inside `.tar.gz`, files inside the AIOps `.zip`),
they were streamed/read in memory (`tarfile`/`zipfile` Python
modules, `tar -xOzf ... | ...`) without writing extracted output to
disk. No cleaning, imputation, deduplication, splitting, or feature
selection has been performed. Nothing here modifies Phase 3's frozen
surface (`PHASE3_FREEZE.md`) or touches Phase 4.

Every finding below is either directly observed from the files
(marked with counts/values) or explicitly marked **PENDING** where it
requires information not present in the files themselves (e.g.
official schema docs not fetched this pass, or archives — like the
AIOps per-day zips and Alibaba sensor table — not yet opened).
Nothing is guessed or filled in to make a dataset look more complete
than it is.

---

## Dataset D — Microsoft AgentRx

**Classification: REAL SYSTEM, EVALUATION-HARNESS ENVIRONMENT — not
organic production traffic, but not fault-injected either.** Doesn't
cleanly fit the audit's four buckets (NATURAL REAL-WORLD / REAL
SYSTEM-EXPERIMENTALLY INJECTED / SYNTHETIC / MIXED): trajectories are
genuine LLM-agent executions against real tools/environments
(Magentic-One benchmark tasks; tau-bench retail environment), so
failures are real agent behavior, not synthetic text — but they were
produced by running a benchmark harness, not captured from live user
traffic. Treat as **REAL SYSTEM (non-production, benchmark-harness
origin)** and do not present it as organic production evidence.

### 1–3. Existence, integrity, acquisition record

| File | Bytes | SHA-256 | Records |
|---|---|---|---|
| `magentic_dataset.jsonl` | 4,203,050 | `e2c697a9...c2179` | 58 |
| `magentic_one.jsonl` | 152,350 | `9bfa5629...c3518` | 44 |
| `tau_retail.jsonl` | 36,169 | `95729a0f...49d1a` | 29 |
| `tau_retail_dataset.jsonl` | 831,593 | `21852996...969bf` | 29 |

(Full checksums in `data/provenance/agentrx_download_provenance.md`.)
Source: `huggingface.co/datasets/microsoft/AgentRx` (main branch,
gated — access granted by user). Acquired 2026-08-13. All 4 files
parse as valid line-delimited JSON, 0 malformed lines in any file. No
official checksum manifest was found published alongside the dataset;
the SHA-256s above are our own acquisition-time record, not verified
against a publisher-supplied hash.

### 4. Archive/file structure

Two independent pairs, not a single unified schema:
- **Magentic pair**: `magentic_dataset.jsonl` (raw agent trajectories) +
  `magentic_one.jsonl` (failure/diagnosis annotations for a subset of
  those trajectories).
- **Tau-retail pair**: `tau_retail_dataset.jsonl` (raw trajectories) +
  `tau_retail.jsonl` (failure/diagnosis annotations).

### 5. Schema / field types

**Trajectory files** (`magentic_dataset.jsonl`, `tau_retail_dataset.jsonl`):
`trajectory_id` (str), `instruction` (str), `steps` (list of `{index,
substeps: [{sub_index, role, content}]}`). No timestamps anywhere.

**Annotation files** (`magentic_one.jsonl`, `tau_retail.jsonl`):
`trajectory_id` (str), `failure_summary` (str), `failures` (list of
`{failure_id, step_number, step_reason, failure_category,
category_reason, failed_agent}`), `num_failures` (int), `root_cause`
(dict: `{failure_id, reason_for_root_cause}`), `root_cause_failure_id`
(str), `root_cause_reason` (str). All 7 keys present in 100% of records
in both annotation files (no missing top-level keys).

Observed `failure_category` values (from samples, not a full-enum
scan): "Instruction/Plan Adherence Failure", "Invention of new
information" — full taxonomy not yet extracted.

### 6. Record counts

58 / 44 / 29 / 29 as above. (Earlier `wc -l` on `tau_retail_dataset.jsonl`
reported 28 due to a missing trailing newline on the last line; the
JSON-parse-based count of 29 is authoritative.)

### 7. Timestamps / temporal coverage

**None.** Only ordinal `index`/`sub_index` fields establish order
within a trajectory. **NOT EVALUABLE** for any wall-clock temporal
split, calendar-based drift analysis, or "unseen time period"
generalization test (Section 6/13 of the protocol). Only
trajectory-level entity-disjoint splits are meaningful here.

### 8. Identifiers / persistent entities

- Magentic pair joins directly on `trajectory_id`: **44/44 annotated
  IDs are a strict subset of the 58 trajectory IDs** (14 trajectories
  have no failure annotation — presumably unannotated or successful
  runs, not confirmed which). Zero duplicate IDs in either file.
- Tau-retail pair does **not** join directly: `tau_retail_dataset.jsonl`
  uses IDs like `"tau_retail_2"`, `tau_retail.jsonl` uses bare `"2"`.
  Verified: stripping the `tau_retail_` prefix gives a **full 29/29
  bijection**, zero orphans either direction. This mapping must be
  applied explicitly in any future join — it is not automatic.
- Each trajectory is its own entity; there's no shared cross-trajectory
  ID (e.g. no "agent" or "user" field), so entity-disjoint splitting
  reduces to trajectory-disjoint splitting.

### 9. Missingness

All declared top-level keys present in 100% of records, both
annotation files. Deeper value-level missingness (e.g. empty strings
nested inside `failures[]`) has not been scanned — flagged as a
follow-up before any cleaning rule is written.

### 10. Duplicates

Zero duplicate `trajectory_id` confirmed within each of the 4 files
individually (verified for magentic pair explicitly; tau-retail pair's
1:1 bijection after prefix-stripping implies the same).

### 11. Failure/anomaly labels

`failures[].failure_category` + `num_failures` is the label source.
Small taxonomy, not yet fully enumerated across all 73 annotated
trajectories.

### 12. Diagnosis / root-cause info

**Present** — uniquely among the three audited datasets, AgentRx has
an explicit `root_cause_failure_id` + `root_cause_reason` (free text)
pointing into the `failures[]` list. This is the strongest current
candidate for Phase 3.6 / H6 (diagnosis) evaluation.

### 13. Recovery / action / outcome info

**Not present as a field.** No "recovery attempted"/"recovery
succeeded" label. **NOT EVALUABLE for H7** (recovery safety) without
inferring recovery from raw trajectory steps (e.g. detecting a retried
action after a failure) — and if that inference is ever built, it must
be labeled explicitly as *inferred*, not treated as ground truth.

### 14. Post-outcome leakage fields

`failure_summary`, `failures`, `num_failures`, and all `root_cause*`
fields are demonstrably produced **after** observing the complete
trajectory (they reference step numbers throughout the entire run and
explain why the trajectory ultimately failed). **AVAILABLE ONLY AFTER
OUTCOME** — must never be used as decision-time input for a real-time
failure-prediction evaluation. They are only valid as (a) ground truth
for an after-the-fact diagnosis task, or (b) training targets for
offline classification restricted to trajectory content strictly
before the labeled failure step.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Possible | using pre-failure trajectory content as features |
| H2 drift | **NOT EVALUABLE** | no timestamps |
| H3 F-vs-B | Weakly possible | needs a real decision-time feature/label split |
| H4 attack-generalization | Weakly possible | same caveat |
| H5 complementarity | Weakly possible | same caveat |
| H6 diagnosis | **Best candidate of all 3 datasets** | explicit root_cause field |
| H7 recovery | **NOT EVALUABLE** | no recovery field |
| H8 authority | General | qualitative only |

### 16. Limitations

Extremely small n (87 trajectories total, 73 annotated, single root
cause each); two unrelated task domains (open-ended web/file agent
tasks vs. retail tool-use tasks) that should **not** be pooled without
justification; no timestamps; benchmark-harness origin, not production
traffic — must not be presented as organic real-world production
evidence in the final writeup.

---

## Dataset A1 — Alibaba GPU2020 (PAI trace) — all 7 archives

**Classification: NATURAL REAL-WORLD** (production PAI cluster, July–
~2 month window 2020, per Alibaba's public documentation). **7 of 7**
known archives now present and audited, including
`pai_sensor_table.tar.gz` (download completed this pass).

### 1–3. Existence, integrity, acquisition record

All 6 present archives pass `gzip -t` integrity checks. Internal
timestamps (from `tar -tzvf`) all read `2021-04-15 07:25`, consistent
across all 6 files — a plausible single-batch repackaging date, not
necessarily the collection date.

| Archive | Bytes (compressed) | SHA-256 | Inner CSV rows |
|---|---|---|---|
| `pai_group_tag_table.tar.gz` | 55,064,781 | `722fef30...23a14` | 1,055,032 |
| `pai_job_table.tar.gz` | 62,065,432 | `5aad7f7c...0a6cb0` | 1,055,501 |
| `pai_task_table.tar.gz` | 35,514,117 | `cd1d6dc3...499ac40e5` | 1,261,050 |
| `pai_instance_table.tar.gz` | 694,839,139 | `1bf1e423...97995ca06` | 7,522,002 |
| `pai_machine_metric.tar.gz` | 206,596,175 | `53ad9171...875892eef5` | 2,009,423 |
| `pai_machine_spec.tar.gz` | 30,449 | `cc0d38a4...1276c2d` | 1,897 |
| `pai_sensor_table.tar.gz` | 406,119,947 | `9a0b82e8...a69c7a0` | 3,033,232 |

No official checksum manifest was fetched/checked against this pass
(the 2017/2018 Alibaba traces are known to ship an MD5 manifest in
some releases; whether GPU2020 does was not verified this session) —
the SHA-256s above are our own acquisition-time record.

### 4. Archive/file structure

Each `.tar.gz` contains exactly one flat `.csv` of the matching name.
No nested directories, no embedded header row in any file.

### 5. Schema / field types

**No CSV in this trace ships a header row.** Alibaba documents column
names separately (repo README/schema doc), which was **not fetched
this session** — everything below is inferred from column position,
value patterns, and general familiarity with this trace family, and
must be cross-checked against the official schema before being relied
on for feature engineering:

- `pai_job_table.csv` (6 cols): `job_name` (confirmed unique key, see
  §8), 2 further hex-token columns of uncertain semantics (PENDING),
  `status` ∈ {Terminated, Failed, Running, Waiting}, `start_time`,
  `end_time`.
- `pai_task_table.csv` (10 cols): `job_name`, `task_name` (values like
  `tensorflow`, `worker`, `ps`, `PyTorchWorker`, `xComputeWorker` —
  high-confidence framework/role labels), `inst_num`, `status` (same 4
  values), `start_time`, `end_time`, `plan_cpu`, `plan_mem`,
  `plan_gpu`, `gpu_type` (values: MISC, T4, P100, V100, V100M32, or
  empty).
- `pai_instance_table.csv` (9 cols): `job_name`, `task_name`, then 3
  further hex-token columns (inst_name/worker_name/machine — exact
  order PENDING), `status`, `start_time`, `end_time`, a trailing hex
  token (PENDING).
- `pai_group_tag_table.csv` (5 cols, one column empty in every sampled
  row): low confidence overall — PENDING.
- `pai_machine_spec.csv` (5 cols): `machine_id`, a type label (`CPU`
  seen; other values not sampled), `cpu_num` (96 in sample), `mem_gb`
  (512 in sample), `gpu_num` (0 in CPU-only sample rows).
- `pai_machine_metric.csv` (12 cols): `worker_name`, `machine`,
  `start_time`, `end_time`, then ~8 numeric telemetry columns with
  partial nulls even on populated rows — column-level semantics
  PENDING.
- `pai_sensor_table.csv` (16 cols): `job_name`, `task_name` (values
  match task_table's role labels — `worker`, `tensorflow`,
  `PyTorchWorker`, `xComputeWorker`, `evaluator`,
  `OssToVolumeWorker`, `ps`, `OpenmpiWorker`, `TVMTuneMain`,
  `LeadingWorker`, confirming this table joins to task/instance level),
  `inst_name` (hex), `worker_name` (hex), `machine` (hex), `gpu_name`
  (`/dev/nvidiaN`, N∈0–7 observed), then **10 numeric GPU sensor
  metrics** — column-level semantics PENDING (values consistent with
  utilization/memory/power/temperature-style GPU telemetry, but exact
  field-to-name mapping not confirmed against official docs). **No
  `start_time`/`end_time` columns** — unlike `machine_metric`, this
  table appears to be one aggregate row per (job, instance, GPU
  device) rather than a time-windowed series.

### 6. Record counts

As in the table above (streamed line counts, robust since there's no
header row to account for).

### 7. Timestamps / temporal coverage

All `start_time`/`end_time` values are small numeric values (e.g.
`1053513.0`) — **relative seconds from an undocumented zero-point**,
not Unix epoch (values are far too small). Consistent with Alibaba's
documented convention for this trace family. **No absolute calendar
timestamp is recoverable from the files themselves** — only relative
ordering and elapsed duration. This means any "unseen time period"
split must use relative-time bucketing (e.g. first N% vs. last
(100−N)% of the trace by `start_time`), not calendar dates. `pai_sensor_table.csv` has **no timestamp columns at
all** — it cannot support any temporal split or drift analysis on its
own; it can only be joined to job/task/instance records (which do
carry `start_time`/`end_time`) to inherit a time context.

### 8. Identifiers / persistent entities

`job_name` confirmed as a **clean unique key** in `pai_job_table.csv`:
1,055,501 rows, 1,055,501 unique `job_name` values, 0 duplicates.
`task_table`/`instance_table` reference `job_name` as an expected
foreign key (many tasks per job, many instances per task) — not yet
cross-validated for referential completeness (whether every
`job_name` in task/instance tables exists in job_table). Machine IDs
appear across `machine_spec`/`machine_metric`/`instance_table` but
cross-table referential integrity is **not yet checked** — flagged as
required before any entity-disjoint (machine-level) split is frozen.
`pai_sensor_table.csv` additionally confirms **1,737 distinct
machines** and its `(job_name, inst_name)` pair is a **clean unique
key** (3,033,232 rows, 3,033,232 distinct pairs, 0 duplicates) — i.e.
one sensor row per (job, instance, GPU device) combination, not a
repeated time series.

### 9. Missingness

- `pai_job_table.csv`: **28.08%** of rows have empty `end_time`,
  corresponding exactly to `status` ∈ {Running, Waiting} (i.e. jobs
  still unresolved when the trace was cut off). This is **right-
  censoring**, not random missingness — per the audit rules these rows
  must be excluded from any binary failure/success label, not imputed
  and not treated as negative (success) examples.
- `pai_task_table.csv`: analogous censoring pattern (Running 9.16% +
  Waiting 0.29%).
- `pai_machine_metric.csv`: partial per-row nulls observed even among
  populated rows — needs a dedicated per-column missingness scan
  before cleaning; not done this pass.
- `pai_sensor_table.csv`: 14 of 16 columns 100% populated. Two numeric
  columns have small missingness (5,829 and 1,217 empty values out of
  3,033,232 rows respectively), and exactly **3 rows** have 6 of their
  10 metric columns empty simultaneously (verified — all
  `worker`/`OssToVolumeWorker` tasks) — consistent with a GPU device
  that reported no usable telemetry, not a random gap. Negligible in
  count (3/3,033,232) but still meaningful (sensor-unavailable)
  missingness, not to be imputed.

### 10. Duplicates

`job_name` uniqueness confirmed (0/1,055,501). Duplicate-key checks
for `(job_name, task_name)` in task_table and
`(job_name, task_name, inst_name)` in instance_table **not yet run** —
flagged PENDING (both are large files; a streaming check is feasible
but wasn't prioritized this pass). `pai_sensor_table.csv`'s
`(job_name, inst_name)` key is confirmed duplicate-free (see §8).

### 11. Failure/anomaly labels

`status` field. Raw distribution (all rows):

| Table | Terminated | Failed | Running | Waiting |
|---|---|---|---|---|
| job_table (n=1,055,501) | 69.38% | 24.31% | 5.96% | 0.35% |
| task_table (n=1,261,050) | 70.19% | 20.36% | 9.16% | 0.29% |

**Terminal-outcome-only failure rate** (excluding censored
Running/Waiting rows, which is the methodologically correct
denominator): job level = 256,555 / 988,910 = **25.94%**; task level =
256,762 / 1,141,835 = **22.49%**.

### 12. Diagnosis / root-cause info

**Not present.** `status=Failed` is a terminal outcome only — no error
code, no failure-reason string in any of the 6 audited tables.
**NOT EVALUABLE for H6** on this dataset (consistent with the
provisional call in the earlier audit draft).

### 13. Recovery / action / outcome info

**Not present as an explicit field.** No resubmission-linkage between
a Failed job and a later retry job. Any recovery signal here would
require heuristic entity matching (same user/similar resource request
shortly after a failure) — that would be an **inferred**, not
ground-truth, recovery label and must be documented as such if ever
attempted. **NOT EVALUABLE for H7** as currently understood.

### 14. Post-outcome leakage fields

`end_time` (and anything derived from it, e.g. duration =
`end_time - start_time`) is only knowable once a job/task has
terminated — **available only after outcome**, must be excluded from
decision-time input for any "predict failure before it happens" task.
`status` is the label itself. `pai_machine_metric.csv` rows are keyed
by a `(worker_name, start_time, end_time)` **reporting interval** —
whether a given metric row's interval precedes, overlaps, or follows
its task's failure point has **not yet been checked**, and must be
before any metric-derived feature is treated as decision-time-safe.
`pai_sensor_table.csv` carries no timestamp of its own (see §7) —
whether a given sensor row reflects the instance's full lifetime or
only a post-hoc summary computed after the instance terminated is
**undetermined** and must be resolved (via the official schema doc,
not guessed) before treating sensor features as decision-time-safe;
until resolved, sensor-table features should be treated as
**potentially leaking** rather than assumed safe.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Likely | task/instance/machine_metric/sensor features |
| H2 drift | Possible | only via relative-time splits, not calendar; sensor table has no time axis of its own |
| H3 F-vs-B | Likely | |
| H4 attack-generalization | Possible | synthetic perturbations applied on top of real features, same structural pattern as original Phase 3.5 |
| H5 complementarity | Likely | if a comparable failure-memory representation can be built; sensor table adds a richer per-GPU-device feature set for this |
| H6 diagnosis | **NOT EVALUABLE** | no cause field anywhere, including sensor table |
| H7 recovery | **NOT EVALUABLE** | no recovery field (or inferred-only, must be flagged) |
| H8 authority | General | qualitative |

### 16. Limitations

Single organization, single ~2-month window, one cluster's own
scheduling policy — external validity is bounded by that regime; no
absolute calendar time recoverable; no diagnosis/recovery fields;
sensor-table leakage status is unresolved (see §14) — must not be used
as a decision-time feature until that's settled;
several column semantics are position-inferred, not yet confirmed
against Alibaba's official schema doc (not fetched this session);
`machine_metric` needs a dedicated missingness pass; cross-table
referential integrity for machine/job IDs not yet verified;
`pai_sensor_table.tar.gz` still pending and **excluded** — do not
assume its content ahead of time.

---

## Dataset C — AIOps KPI (identified: CCF AIOps Challenge 2020, preliminary round)

**Classification: REAL SYSTEM / EXPERIMENTALLY INJECTED — not
NATURAL REAL-WORLD.** The fault log's own contents make this
unambiguous: faults (`CPU fault`, `network delay`, `network loss`,
`db connection limit`, `db close`) were deliberately injected into a
docker/db/os testbed for a competition, with organizers recording
exactly what they injected and when. This must not be presented as
organic production-failure evidence — it answers a different, still
valuable question ("can a system recover known-injected fault type
from telemetry"), not "does this system handle real unplanned
production failures."

### 1–3. Existence, integrity, acquisition record

Outer container: `AIOps挑战赛2020预赛数据.zip`, 3,084,639,115 bytes,
SHA-256 `0b50d8a6...5162dce`. `zipfile.testzip()` returned `None`
(CRC-OK for all central-directory entries) — container-level integrity
confirmed. The dataset was already staged by the user before this
audit began; the exact original download URL/date were not
independently re-verified this pass — recording what the archive
itself asserts (internal filenames identify it clearly as the CCF
AIOps Challenge 2020 preliminary-round release).

Uniquely among the 3 audited datasets, this one ships its **own
official checksum manifest** (`sha256sum.txt`, 10 entries, one per
`_lock.zip` daily archive) — not yet cross-verified against the actual
`_lock.zip` contents, since that requires extracting them from the
outer container first (deferred, per "do not extract yet").

### 4. Archive/file structure

31 entries in the outer zip:
- 20 per-day telemetry zips, `2020_04_11.zip` … `2020_05_31.zip` —
  some plain, some `_lock.zip` (password-protected; the 10 filenames
  in `sha256sum.txt` are all `_lock.zip` variants, implying at least
  those 10 dates are password-gated — which specific dates are locked
  vs. plain has not been fully reconciled).
- `data_release_v3.5/` — 9 metadata files: field manifest
  (`1数据字段清单.xlsx`), deployment architecture
  (`1应用部署架构清单.xlsx`), fault description
  (`0故障说明.xlsx`, plus a `~$0故障说明.xlsx` Excel lock/temp file —
  itself a small provenance clue that the source `.xlsx` was open in
  Excel when packaged), and per-layer metric dictionaries (DB, OS,
  DCOS, middleware, business — `.xlsx` except business, which is plain
  text).
- `故障整理（预赛）.csv` at the **top level**, not inside any per-day
  zip — the fault/failure ground-truth log, directly readable without
  a password.
- `passwd.txt` — the zip password for `_lock.zip` files, base64 + a
  `%uXXXX`-escaped Chinese string; decoded (for documentation only,
  **not applied to extract anything**) to `这是挑战赛初赛答案密码`
  ("this is the challenge preliminary-round answer password").
- `sha256sum.txt`, `unzip_all.sh` — the publisher's own verification
  and extraction scripts, confirming which files need the password.

### 5. Schema / field types

`故障整理（预赛）.csv` header (English, source's own typos preserved):
`index, object, fault_desrcibtion, kpi, name, container, log_time,
log_block, block, start_time, duration`.

- `object` ∈ {docker, db, os}
- `fault_desrcibtion` (fault category, free-text-ish but low
  cardinality — see §11)
- `kpi` — semicolon-delimited affected-metric names, present only for
  some fault types (structural, see §9)
- `name` — component instance id (`docker_003`, `db_007`, `os_018`)
- `container` — parent container id, present only for docker faults
- `log_time` — `YYYY/M/D H:MM`, no explicit timezone recorded
- `log_block` / `block` — integer bookkeeping fields, semantics
  **PENDING** (likely trace-round/window indices — not confirmed)
- `start_time` — a **second**, later timestamp distinct from
  `log_time` (see §7 — semantics unclear, PENDING)
- `duration` — constant `"5min"` for every row observed

One metric family's schema is directly documented in
`data_release_v3.5/2业务指标说明` (plain text): `serviceName,
startTime, avg_time, num, succee_num, succee_rate` — business/service
call metrics, 2-minute sampling interval. The other metric families
(OS, docker/DCOS, DB, middleware) have their own `.xlsx` dictionaries,
**not parsed this pass** (would require extraction + spreadsheet
parsing, deferred).

### 6. Record counts

`故障整理（预赛）.csv`: **81 data rows** (82 lines incl. header),
`index` values non-contiguous across 1–169 — **88 index values in
that range are genuinely absent from the file** (verified by full
parse, not a display artifact), e.g. 12–99 entirely missing. Reason
unconfirmed — plausibly reserved for a different data-release phase or
excluded from the preliminary round; not fabricated or filled in.
Zero duplicate `index` values among the 81 present. Per-day telemetry
row counts are **not available without extraction** — deferred.

### 7. Timestamps / temporal coverage

Fault log spans **2020-04-11 through 2020-05-31** (~7 weeks),
corroborated independently by the per-day zip filenames covering the
same range — **this is the only one of the 3 audited datasets with
recoverable absolute calendar time**, making it the only current
candidate for a genuine calendar-based temporal split. Timezone is
unstated — must be confirmed, not assumed, before use.

`start_time` values reuse dates that look like a **later occurrence**
of the same fault pattern (e.g. row index 100: `log_time`
2020-05-15, `start_time` 2020-05-22 — a 7-day offset) — this pattern
recurs across multiple rows and looks systematic, not random, but its
actual meaning (replay window? re-scoring date? a second injection of
the same fault?) is **not determinable from this file alone** and is
flagged as an open question likely answered by the unparsed `.xlsx`
fault-description file.

### 8. Identifiers / persistent entities

`name` (`docker_NNN`/`db_NNN`/`os_NNN`) recurs across multiple fault
rows — a persistent entity. `container` links docker faults to a
parent (`container_001`/`container_002`) — a second entity level. Any
entity-disjoint split must keep all rows for a given `name` together.

### 9. Missingness

`kpi` is empty for all `network delay`/`network loss`/`db close` rows
and populated only for `CPU fault`/`db connection limit` rows (30/81
missing overall) — **structural** (not every fault type maps to a
single KPI column), not random. `container` is empty for all
`db`/`os` rows, populated only for `docker` rows (32/81 missing) —
also structural (only docker faults are nested inside a container).
Both must be treated as meaningful missingness, not imputed, per the
audit rules.

### 10. Duplicates

Zero duplicate `index` values (verified, full parse, n=81). No other
duplicate-row check performed yet (e.g. exact-duplicate fault entries
by `name`+`log_time`) — not run this pass.

### 11. Failure/anomaly labels

The fault log itself is the label source. `fault_desrcibtion`
distribution (n=81): network delay 31, CPU fault 19, network loss 19,
db connection limit 7, db close 5. `object` distribution: docker 49,
os 20, db 12.

### 12. Diagnosis / root-cause info

`object` + `fault_desrcibtion` + `kpi` functions as ground-truth
diagnosis (what failed, how, which metric reflects it) — but this is
**fault-injection ground truth** (organizers control and log exactly
what was injected), not diagnosis inferred from symptoms by any
system. Evaluable as "recover the injected fault type/category from
telemetry," must be labeled as such, not presented as organic root-
cause diagnosis.

### 13. Recovery / action / outcome info

**Not present.** No field records mitigation or a return-to-normal
event beyond the fixed `duration=5min` injection window (which
describes the fault's own timing, not any recovery outcome).
**NOT EVALUABLE for H7.**

### 14. Post-outcome leakage

The fault log is ground truth by construction and must be used only
as `y`, never as a decision-time input feature. Any telemetry
timestamp at or after a given entity's `log_time`/`start_time`
potentially reflects the fault's *consequence* rather than a pre-fault
predictor — this constraint is not yet enforced in any pipeline
(there is no pipeline yet), but must be built into feature
construction once telemetry is extracted.

### 15. Phase 3 hypotheses this dataset can support

| Hypothesis | Evaluable? | Note |
|---|---|---|
| H1 representation | Likely | pending telemetry extraction |
| H2 drift | **Likely — best candidate of the 3** | only dataset with real absolute calendar span |
| H3 F-vs-B | Likely | |
| H4 attack-generalization | Likely | |
| H5 complementarity | Likely | |
| H6 diagnosis | Likely | injected-fault-category classification, not organic diagnosis — must be labeled as such |
| H7 recovery | **NOT EVALUABLE** | no recovery field |
| H8 authority | General | qualitative |

### 16. Limitations

This is injected-fault data on an apparent controlled/testbed
multi-tier application (docker/db/os/middleware), **not** organic
production failures — must never be presented as NATURAL REAL-WORLD
evidence. Most per-day telemetry (10+ of 20 daily zips) is password-
locked and unextracted; extraction is deferred pending explicit
authorization to proceed past the audit stage. Two `.xlsx` metadata
files likely resolve the `start_time`/`log_time` and `log_block`/
`block` ambiguities noted above but have not been parsed. Original
acquisition URL/date not independently re-verified (file was
pre-staged).

---

## Effective independent sample units (item 16 of this pass)

This is a preliminary read, not the formal power analysis the
authorizing brief requires before any Phase 3.1 real-data protocol
lock (Section 7 of that brief) — that still needs to happen as its own
step. But even at this audit stage, the *unit of independence* for
each dataset is already visible and worth recording now, since it
constrains what any later split/comparison can claim.

**AgentRx.** The independent unit is the **trajectory** — each is one
self-contained agent run, no shared entity across trajectories. Total
n=87 (58 magentic + 29 tau-retail), of which n=73 have failure
annotations (44 + 29). The two task domains are structurally different
(open-ended web/file-agent tasks vs. retail tool-use) and should be
treated as **two separate small samples** (n=44, n=29), not pooled to
n=73, unless a specific justification for pooling is made explicit in
the real-data protocol. Both are far below any conventional threshold
for a stable AUROC/AUPRC estimate — any comparison here should expect,
and report, wide confidence intervals, not treat a point estimate as
decisive.

**Alibaba GPU2020.** Multiple candidate units exist at different
granularities, and they are **not interchangeable**:
- Job-level: 1,055,501 jobs total; 988,910 with a decided terminal
  outcome (Terminated/Failed) — this is the right denominator for a
  job-level failure-prediction task; 256,555 positive (Failed) /
  732,355 negative (Terminated).
- Task-level: 1,141,835 terminal tasks; 256,762 positive / 885,073
  negative — **not independent of job-level units**, since many tasks
  share a job; any split must keep all tasks of a job on one side.
- Instance-level (7,522,002 rows) and sensor-level (3,033,232 rows)
  are nested even further inside task/job and are not independent
  sampling units for a job- or task-level claim — they're additional
  features/observations *about* a job or task, not additional
  independent examples of "did a job fail."
- Machine-level: 1,737 distinct machines (from sensor table) — far
  smaller than the job/task counts; any machine-level generalization
  claim (e.g. "unseen machine") is bounded by this much smaller n, not
  by the million-plus job/task counts.

**AIOps KPI.** The fault log gives **n=81 independent fault-injection
events** — the clear independent unit for any diagnosis/anomaly-
category claim on this dataset, and a small-sample regime by any
standard. A finer unit (entity × time-window, once telemetry is
extracted) would raise the nominal n but each window's label is still
derived from the same 81 events, so the *effectively independent*
count for any fault-category-level claim remains bounded near 81, not
the row count of the extracted telemetry. Per-fault-category counts
are smaller still (7–31 per category, see §11 of the AIOps section) —
several categories (`db close`: 5, `db connection limit`: 7) are too
small for a reliable per-class estimate on their own.

---

## Dataset-to-hypothesis matrix

Mapped to the original Phase 3 subphases (3.1 protocol lock / 3.2
representation matrix / 3.3 generalization / 3.4 baseline comparison /
3.5 attack-generalization / 3.6 diagnosis+recovery+decision), per your
requested format. "Evaluable" here means *the dataset contains the
information needed*, not that the comparison would be adequately
powered — see the sample-size notes above and the full Section 7
power analysis still to come.

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Evidence available | Limitations |
|---|---|---|---|---|---|---|---|---|
| AgentRx | Yes | Partial | No | Partial | Partial | **Diagnosis: Yes** (best of the 3); Recovery: No | Explicit `root_cause`/`failure_category` fields; trajectory content as features | n≤73 (two domains, n=44/n=29); no timestamps → no drift/temporal-split claims; benchmark-harness origin, not production; no recovery field |
| AIOps KPI | Yes | Yes | **Yes** (best of the 3 — only real calendar span) | Yes | Yes | Diagnosis: Yes (**injected**-fault category, not organic); Recovery: No | Real ~7-week calendar span; 81 labeled fault-injection events across docker/db/os; two-tier entity structure (name→container) | Classification is REAL SYSTEM/EXPERIMENTALLY INJECTED, not natural — must not be presented as organic production evidence; n=81 events, several fault categories n<10; bulk telemetry (20 daily zips) still unextracted; `start_time`/`log_time` semantics unresolved |
| Alibaba GPU2020 | Yes | Yes | Partial (relative-time only) | Yes | Yes | Diagnosis: No; Recovery: No | ~1M jobs / ~1.14M terminal tasks / 7.5M instances / 3M sensor rows, real production cluster, clean unique keys confirmed at job and (job,inst) level | No absolute calendar time (relative seconds only); no diagnosis/recovery field anywhere across all 7 tables; several column semantics still position-inferred, not confirmed against official schema; sensor-table leakage timing unresolved; single org/cluster/window |

No cell above was filled in by assuming a dataset supports a claim
just because it's plausible — every "Yes"/"Partial"/"No" traces back
to a specific field (or specific absence of one) documented in the
per-dataset sections above.

---

## Updated open items

1. **Alibaba GPU2020 official schema doc** — not fetched this
   session; several column-position inferences above (job_table cols
   1–2, instance_table cols 2–4/8, group_tag_table, sensor_table's 10
   metric columns) need confirmation before they're used in any
   feature definition.
2. **`pai_sensor_table.tar.gz`** — now downloaded and audited (see
   Dataset A1 above). Its leakage timing (§14) is still unresolved and
   needs the official schema doc to settle.
3. **AIOps per-day telemetry** — 20 daily zips (some password-locked,
   password identified but not applied) remain unopened; the actual
   KPI time series (the bulk of this dataset's evidentiary value) is
   still unaudited. Needs explicit go-ahead to extract before I do,
   since extraction is a bigger step than the read-only peeking done
   so far.
4. **AIOps `.xlsx` metric/field dictionaries** — unparsed; would
   resolve several PENDING schema questions, including the
   `start_time` vs `log_time` ambiguity.
5. **Formal sample-size/power analysis** (Section 7 of the authorizing
   brief) — the "effective independent sample units" above is a
   preliminary read for this audit, not that formal analysis; it still
   needs to be done as its own step before the Phase 3.1 real-data
   protocol is frozen.
6. No further AgentRx-side open items beyond the small-n/domain-
   pooling caveat already noted.

Per your instruction, **stopping here** — no cleaning, splitting,
feature selection, model tuning, imputation, deduplication, outlier
removal, normalization, feature engineering, merging, or Phase 3.1–3.6
evaluation has been run. Phase 3 frozen docs are untouched, Phase 4
was not touched, and Alibaba 2017 / Google Cluster remain excluded
(not acquired). Waiting for explicit authorization before proceeding
to final cleaning or evaluation.


---

<a id="phase3-real-data-alibaba-sensor-leakage-gate"></a>
# PHASE3 REAL DATA ALIBABA SENSOR LEAKAGE GATE
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`  
**Role:** Leakage gate specifically for Alibaba sensor-derived features.

# Alibaba GPU2020 — Sensor/Machine-Metric Leakage Gate Decision

**Status: RESOLVED (not "potentially leaking" — confirmed, from
official documentation, not inferred).**

## Question posed

Do `pai_sensor_table` and `pai_machine_metric` represent (A)
measurements available during execution / before the outcome, or (B)
full-lifetime/post-hoc aggregates that may be unavailable at
prediction time?

## Answer: (B), for both tables, confirmed by the publisher's own documentation

Source: `data/provenance/alibaba_gpu2020/official_README.md` (official
Alibaba clusterdata repo, fetched 2026-08-13).

- **`pai_sensor_table`**, quoted verbatim: *"all the sensor metrics
  (CPU, GPU, Memory, I/O) in this table are collected for each
  instance (indexed by `worker_name`) but not task, taking the
  average of all data in the instance's lifetime (except for `max_mem`
  and `max_gpu_wrk_mem` being the maximum)."*
- **`pai_machine_metric`**, quoted verbatim: *"these metrics are
  machine-level metrics, taking average of the sensor data during the
  instance's (indexed by `worker_name`) lifetime."* Its `start_time`/
  `end_time` columns are not an independent reporting window — they
  are literally copies of the parent instance's own launch/completion
  timestamps (per `pai_instance_table`'s documented fields).

An instance's "lifetime" runs from its `start_time` to its
`end_time` — and `end_time` is only known once the instance has
**already terminated** (successfully or via failure; see
`pai_instance_table.status`). A full-lifetime average by construction
incorporates information from the entire run, including its final
moments and its manner of ending — it cannot be computed at any point
strictly before the instance's outcome is already determined.

## Decision

Both tables are classified **CONFIRMED LEAKING** (not merely
"potentially leaking") for any task framed as *"predict failure before
it happens"* — i.e., any decision-time / pre-outcome evaluation.

**Exclusions:**
- No field from `pai_sensor_table` or `pai_machine_metric` may be used
  as a decision-time input feature in any Phase 3.1–3.6 real-data
  predictive evaluation (H1 representation, H3 F-vs-B, H4
  attack-generalization, H5 complementarity).
- `max_mem` and `max_gpu_wrk_mem` are lifetime *maxima*, not averages
  — same exclusion applies; a maximum over the full lifetime is at
  least as leaky as an average.

**Retained uses (must be clearly labeled as post-hoc, not predictive):**
- Descriptive/exploratory analysis: e.g., "did Failed instances show
  different average GPU utilization than Terminated instances?" is a
  valid post-hoc question and these tables are the right evidence for
  it.
- Diagnosis-adjacent analysis, if ever attempted: a *diagnosis* task
  (explaining why something already failed) may legitimately consume
  post-outcome information, unlike a *prediction* task — but this
  still needs to be evaluated separately from any pre-outcome claim
  and explicitly labeled as diagnosis-only, given neither table
  carries an actual failure-cause field (see the feasibility audit —
  H6 remains NOT EVALUABLE on Alibaba regardless of this gate, since
  there is no cause label to diagnose, only a terminal status).

## What this changes vs. the prior feasibility audit

The prior audit (before official docs were available) had:
- `pai_sensor_table`: flagged "leakage status unresolved," provisional
  "potentially leaking."
- `pai_machine_metric`: speculated its `start_time`/`end_time` might
  be an independent, possibly pre-outcome, reporting window —
  incorrect. It is the same full-instance-lifetime window as the
  sensor table, with the same leakage profile.

Both are now **definitively excluded** from decision-time feature
sets, not provisionally flagged. This is a stricter conclusion than
the audit's provisional stance, arrived at by consulting the official
schema rather than guessing — consistent with the "if timing cannot be
established with confidence, classify as leaking" instruction, except
here timing *was* established with confidence, and it confirms
leakage rather than merely failing to rule it out.

## Downstream consequence for representation experiments (H1/H5)

Any "richer representation" candidate built from Alibaba data for
Phase 3.2-equivalent real-data representation experiments must be
restricted to genuinely pre-outcome fields:
- `pai_job_table`: `user`, `start_time` (submission time only)
- `pai_task_table`: `task_name`, `inst_num`, `plan_cpu`, `plan_mem`,
  `plan_gpu`, `gpu_type`, task `start_time`
- `pai_instance_table`: `machine` (once scheduled), instance
  `start_time`
- `pai_group_tag_table`: `gpu_type_spec`, `group`, `workload` (sparse)
- `pai_machine_spec`: all fields (static machine properties, never
  leaking)

This is a **request/scheduling-time feature set**, not a
runtime-telemetry feature set — a materially weaker representation
than what the sensor/machine_metric tables would have offered, and
this constraint should be stated plainly in the eventual Phase 3.2
real-data results rather than worked around.


---

<a id="phase3-real-data-cleaning-report"></a>
# PHASE3 REAL DATA CLEANING REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`  
**Role:** Real-data cleaning report (Alibaba/AIOps/AgentRx).

# Phase 3 Real-Data Replication — Cleaning, Sampling & Preparation Report

**Status: preprocessing stage complete for what was authorized this
pass. No Phase 3.1–3.6 evaluation has been run. Phase 3's frozen
results (`docs/PHASE3_FREEZE.md`) and Phase 4 are untouched.** This
report is a new, separate artifact — "Phase 3 Real-Data Replication,"
not "corrected Phase 3."

All raw files under `data/raw/` were re-verified byte-identical
(SHA-256) to their originally recorded checksums before and after this
pass — nothing under `data/raw/` was modified, moved, renamed, or
extracted in place. All derived artifacts live under
`data/intermediate/`, `data/processed/`, `data/audit/`,
`data/metadata/`, `data/provenance/`.

---

## 1. Raw dataset inventory

| Dataset | Files | Total size |
|---|---|---|
| AgentRx | 4 `.jsonl` | 5.2 MB |
| AIOps KPI | 1 `.zip` (31 nested entries) | 2.9 GB |
| Alibaba GPU2020 | 7 `.tar.gz` | ~1.5 GB compressed |

## 2. Provenance

- AgentRx: `data/provenance/agentrx_download_provenance.md` (source
  URLs, SHA-256, acquisition date).
- Alibaba GPU2020: `data/provenance/alibaba_gpu2020/official_README.md`
  — the **official** schema doc, fetched this pass from
  `raw.githubusercontent.com/alibaba/clusterdata`. Its published
  checksum block was cross-checked against our own acquisition-time
  SHA-256 values for all 7 archives — **exact match**, confirming file
  integrity against the publisher's own record, not just our re-hash.
- AIOps KPI: acquired pre-staged; internal file structure (own
  `sha256sum.txt`, `passwd.txt`, `unzip_all.sh`) identifies it as the
  CCF AIOps Challenge 2020 preliminary-round release; no independent
  external re-verification of the acquisition URL was performed this
  pass (unchanged from the earlier audit).

## 3. Official schema references

- `data/metadata/alibaba_gpu2020/schema_dictionary.md` — full field
  dictionary for all 7 tables, sourced from the official README, not
  inferred from column names. Every job_table/task_table/
  instance_table column name in the earlier audit's position-inferred
  guesses is now confirmed correct against the official doc except
  job_table's `inst_id` (previously unlabeled, now resolved: ≈
  job_id).
- `data/metadata/aiops_kpi/schema_and_telemetry_findings.md` — full
  telemetry schema (tall/long `itemid,name,bomc_id,timestamp,value,
  cmdb_id` format), per-metric sampling rates, and trace-call schema
  (including the `success` field), all sourced from the dataset's own
  shipped `.xlsx`/text dictionaries and cross-validated against one
  fully-extracted real day (`2020_04_11`).
- AgentRx: no separate schema doc needed — its JSON field names are
  already self-descriptive and were fully characterized in the
  feasibility audit.

## 4. Raw record counts

Unchanged from the feasibility audit; see
`docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md` for the full per-table
breakdown (job_table 1,055,501; task_table 1,261,050; instance_table
7,522,002; sensor_table 3,033,232; machine_metric 2,009,423;
machine_spec 1,897; group_tag_table 1,055,032; AgentRx 87 trajectories
across 4 files; AIOps fault log 81 rows).

## 5–6. Cleaning rules and records removed

**Alibaba `job_table`/`task_table`** — the only tables cleaned at full
scale this pass (`scripts/real_data/clean_alibaba_job_task.py`). A row
is removed only if genuinely malformed: wrong field count, an
unparseable required numeric field, a `status` outside the documented
enum, or `end_time < start_time`.

**Important self-correction during this pass:** the first version of
this script treated an empty `start_time` as malformed for *every*
row and removed 3,663 job rows / 3,714 task rows. Investigation showed
every single removed row had `status=Waiting` — i.e. these are jobs/
tasks that legitimately have not launched yet, per the official
schema, not corrupted records. The rule was corrected to require
`start_time` only for non-`Waiting` rows. Re-run result: **0 rows
removed from either table** — both are fully well-formed at the raw
level; all apparent "missingness" is the documented right-censoring
pattern (Running/Waiting jobs with no `end_time`, Waiting jobs with no
`start_time`), not corruption. This is itself a real, reportable
finding: Alibaba's job/task tables need no repair, only correct
handling of meaningful missingness. The incorrect first pass and its
removed-record log were overwritten by the corrected re-run; the
`removed_records.csv` audit files are consequently empty for both
tables, reflecting the final, correct run.

**Alibaba `instance_table`/`sensor_table`/`machine_metric`** — not
cleaned at full scale (7.5M/3M/2M rows). Per the brief's own Step 6
guidance (sample jobs first, then retain only linked child records),
full-table cleaning was deferred in favor of extracting and validating
only the records linked to the sampled job population (§8 below).
Malformed-row detection (field-count check) *was* run inline during
that extraction (`scripts/real_data/alibaba_extract_linked_records.py`)
and found 0 malformed rows in the extracted subset.

**AIOps KPI** — no destructive cleaning performed this pass. The fault
log (81 rows) was fully parsed and validated in the feasibility audit
(0 duplicates, all 81 rows well-formed). Full-scale telemetry cleaning
across all 20 daily archives was **not performed** — see the scope
decision in `data/metadata/aiops_kpi/schema_and_telemetry_findings.md`
(tens of GB of trace data; deferred until the real-data protocol
defines what window/entity subset is actually needed, to avoid
extracting data before the criteria for using it are frozen).

**AgentRx** — no records removed (0 malformed lines across all 4
files, confirmed in the feasibility audit and re-confirmed by the join
script this pass). The canonical trajectory-level join
(`scripts/real_data/agentrx_build_joined_tables.py`) found 0 orphan
annotations (every annotation matches a real trajectory) in both
domains.

## 7. Records retained

- Alibaba job_table: 1,055,501 / 1,055,501 (100%)
- Alibaba task_table: 1,261,050 / 1,261,050 (100%)
- Alibaba instance/sensor/machine_metric: only the subset linked to
  the "main" sampled 10,000 jobs was materialized (60,005 / 26,350 /
  19,841 rows respectively) — not a cleaning removal, a deliberate
  hierarchy-respecting extraction (§8).
- AgentRx: 87/87 trajectories retained (73 with annotations, 14
  without — none dropped).
- AIOps fault log: 81/81 rows retained.

## 8. Missingness before/after

No change from the feasibility audit's findings (no imputation was
performed, per the brief's explicit prohibition): Alibaba job_table
28.08% censored `end_time` (Running/Waiting); task_table analogous;
AIOps `kpi`/`container` fields structurally empty depending on fault
type; AgentRx 100% key presence in all 4 files. All preserved as-is.

## 9. Duplicate analysis

Alibaba `job_name`: 0 duplicates (1,055,501 unique, re-confirmed).
Alibaba `(job_name, inst_name)` in sensor_table: 0 duplicates
(re-confirmed in the audit, not re-run at full scale this pass).
AgentRx: 0 duplicate `trajectory_id` within any file. AIOps fault log:
0 duplicate `index` (81/81 unique).

## 10–11. Integrity / referential-integrity results

**New this pass:** `task_table.job_name` was checked against the
cleaned `job_table.job_name` set — **0 of 1,261,050 task rows** have a
`job_name` absent from job_table. Referential integrity between job
and task tables is **perfect**, resolving a PENDING item from the
feasibility audit.

Instance/sensor/machine_metric referential integrity against
job_table/task_table was checked only for the extracted "main"-tier
subset (by construction — every extracted row's `job_name` is drawn
from the sampled job set, so integrity is guaranteed for that subset
by the extraction method itself, not separately verified against the
full raw tables).

## 12. Timestamp validation

Alibaba: confirmed via official docs to be relative seconds with an
undocumented per-trace offset, **not** epoch — but day-of-week/
time-of-day *are* preserved under a UTC+8 interpretation (new
information from the official README, not available in the earlier
audit). AIOps: confirmed via real extracted data to be genuine Unix
epoch milliseconds (`1586534693000` → 2020-04-11 00:04:53 UTC+8,
exactly matching the file's own date label) — the only dataset with
fully recoverable absolute calendar time. AgentRx: confirmed, no
timestamps exist anywhere in the schema.

## 13. Leakage analysis

**Mandatory gate resolved** (Step 2): both `pai_sensor_table` and
`pai_machine_metric` are **CONFIRMED LEAKING** for any decision-time
prediction task — both are explicitly documented by Alibaba as
full-instance-lifetime averages/maxima, not pre-outcome windowed
measurements. Full decision and rationale:
`docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`. This is a
stricter, evidence-based conclusion than the earlier audit's
provisional "unresolved" status — in particular it corrects an
earlier speculation that `machine_metric` might have an independent,
possibly-safe reporting window; it does not.

AIOps: fault-log fields (`object`, `fault_desrcibtion`, `kpi`, `name`,
`container`) are ground truth by construction, usable only as `y`.
Trace `success`/`elapsedTime` are that call's own outcome, not an
input feature for predicting the same call. See the full table in
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`.

AgentRx: `failure_summary`, `failures`, `num_failures`, `root_cause*`
are demonstrably post-hoc (reference the trajectory's full, final
step) — confirmed unchanged from the audit.

## 14. Sampling protocol (Alibaba)

Sampling unit: **job** (`job_name`). Population: 988,910 eligible
terminal jobs (`Terminated`+`Failed`; `Running`/`Waiting` excluded as
censored). Strata: `(outcome_status × dominant_gpu_type ×
relative_time_quartile)`. Allocation: proportional to each stratum's
population share (not equalized — equalizing would misrepresent real
prevalence). Selection: deterministic (`SEED=42`, lexicographic sort +
`random.Random.sample`). Full protocol, strata sizes, and exact
selected IDs:
`data/audit/alibaba_gpu2020/{sampling_frame,sampling_report}.json`
and `sample_job_ids_{pilot,main,robustness}.txt`.

Sanity check: sampled Failed-rate matches the population rate almost
exactly at every tier (pilot 26.00%, main 25.94%, robustness 25.94%,
vs. population 25.94%) — confirms the stratified procedure preserves
real-world class balance rather than distorting it.

Linked child records for the **main** tier (10,000 jobs) were
extracted respecting the entity hierarchy — never sampling
instance/sensor/machine_metric rows independently of their parent job
(`scripts/real_data/alibaba_extract_linked_records.py`): 11,750 tasks,
60,005 instances, 26,350 sensor rows, 19,841 machine_metric rows.
Pilot and robustness tiers' linked records were **not** extracted this
pass (deferred until those tiers are actually put to use, to avoid
unnecessary large-file processing ahead of an authorized next step).

## 15. Power analysis

Full results: `data/audit/alibaba_gpu2020/power_analysis.json`
(`scripts/real_data/alibaba_power_analysis.py`, run and frozen
**before** any sampling). Method: Hanley-McNeil (1982) approximate
AUROC variance, at the real observed class balance (25.94% Failed).
Sensitivity swept across AUROC ∈ {0.55, …, 0.80} rather than a single
favorable assumption.

- To estimate a single AUROC to ±0.02 (95% CI half-width): **n ≈
  3,500–4,300** jobs, depending on assumed AUROC.
- To detect a **0.03 AUROC difference** between two candidates (power
  0.80, α=0.05, conservative independent-samples bound — a paired/
  DeLong test on the same test set would need fewer): **n ≈
  7,700–8,100** jobs.

These numbers directly set the tier sizes: pilot (2,000, pipeline
verification only, not powered for a difference claim), main (10,000,
exceeds the ~8,100 needed for a 0.03 difference with margin for
attrition), robustness (50,000, generous margin for subgroup/attack
analyses). **No tier size was chosen after, or influenced by, any
evaluation result** — this script and the sampling script were run in
that order, before any model was ever fit.

## 16. Split protocol

Two split protocols built on the **main** tier (10,000 jobs),
answering two different generalization questions — not one split
forced to serve both. Full construction and per-split class balance:
`data/audit/alibaba_gpu2020/{splits_random_stratified,splits_temporal,
splits_report}.json`.

1. **Random-stratified** (70/15/15, stratified on outcome×gpu_type):
   class balance preserved almost exactly across train/val/test
   (25.95% / 25.97% / 25.88% Failed).
2. **Temporal** (train/val = relative-time Q1–Q3, test = strict future
   holdout Q4): **class balance is NOT preserved** — Failed rate is
   ~20.1% in train/val but **43.4% in the Q4 test holdout**. This is a
   genuine, unforced finding — real temporal drift in the failure rate
   exists in this trace, discovered by the split construction itself,
   before any model was evaluated. This is directly relevant to the
   real-data H2 (drift/generalization) hypothesis and should be
   reported prominently regardless of how any future model performs
   under it — a model evaluated on this temporal split faces a
   materially different base rate than it trained on, which is exactly
   the kind of distribution shift Phase 3.3/3.5-equivalent real-data
   experiments should be measuring.

**Not built this pass:** a machine-disjoint split. Alibaba's job↔
machine relationship is many-to-many; a clean job-disjoint split does
not automatically avoid machine overlap across splits, and building
one without dropping a nontrivial share of jobs is a real
graph-partitioning problem. Documented as a limitation, not silently
skipped.

## 17. Final effective sample sizes

| Dataset | Independent unit | Effective N |
|---|---|---|
| AgentRx — magentic | trajectory | 44 annotated / 58 total |
| AgentRx — tau-retail | trajectory | 29 annotated / 29 total |
| AIOps KPI | fault-injection event | 81 (or 70, pending the IDs-1–11-vs-100–169 reconciliation, see AIOps findings doc) |
| Alibaba GPU2020 (job-level) | job | 988,910 eligible; sampled tiers 2,000 / 10,000 / 50,000 |
| Alibaba GPU2020 (machine-level) | machine | 1,737 total — no machine-disjoint sample constructed this pass |

## 18. Dataset-to-hypothesis matrix (updated, post-cleaning)

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Independent unit | Effective N | Evidence available | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| AgentRx (magentic) | Yes | Partial | Insufficient evidence | Partial | Partial | Diagnosis: **Yes**; Recovery: No | trajectory | 44 | explicit `root_cause`/`failure_category`, joined & verified 0 orphans | n=44, no timestamps, benchmark-harness origin |
| AgentRx (tau-retail) | Yes | Partial | Insufficient evidence | Partial | Partial | Diagnosis: **Yes**; Recovery: No | trajectory | 29 | same as above, ID-mapping resolved & verified | n=29, different domain — not pooled with magentic |
| AIOps KPI | Yes | Yes | **Yes** | Yes | Yes | Diagnosis: Yes (injected-fault category); Recovery: No | fault-injection event | 81 (or 70) | real absolute timestamps confirmed on real data; tall-format telemetry schema resolved; per-call `success` field found (organic outcome signal, new this pass) | injected, not organic; full 20-day telemetry not yet extracted; fault-log start_time/log_time semantics only partially reconciled |
| Alibaba GPU2020 | Yes | Yes | Partial (relative-time only, but **real drift confirmed** this pass) | Yes | Yes | Diagnosis: No; Recovery: No | job (988,910 eligible) | 2,000 / 10,000 / 50,000 sampled tiers, power-justified | sensor/machine_metric CONFIRMED leaking (not just unresolved); referential integrity between job/task confirmed perfect; no machine-disjoint split yet |

Changes from the pre-cleaning matrix: Alibaba's 3.3 cell strengthened
from "Partial (relative-time only)" to "Partial, but real drift now
empirically confirmed" — this is new evidence, not a re-interpretation
of anything frozen. AIOps gained a new organic outcome signal (trace
`success`) not visible before extraction. AgentRx's two domains are
now split into separate matrix rows rather than one combined row, per
the "do not pool" instruction.

## 19. Known limitations (consolidated)

- Alibaba: no machine-disjoint split; instance/sensor/machine_metric
  cleaned only for the sampled subset, not the full raw tables; AIOps
  full-telemetry extraction deferred (tens of GB, scope decision
  documented); AgentRx small-n and cross-domain non-poolability stand
  as before. AIOps fault-log ID-gap (1–11 vs 100–169) reconciliation
  remains partial.
- This preprocessing pass covered the **main** sampling tier
  end-to-end; **pilot** and **robustness** tiers have their job IDs
  selected and frozen but not yet had linked child records extracted.

## 20. Reproducibility instructions

All scripts are under `scripts/real_data/`, deterministic (fixed
`SEED=42` where randomness is used), and read only from `data/raw/`
or from another script's own output — never from anything hand-edited.
Run order:
```
python scripts/real_data/clean_alibaba_job_task.py
python scripts/real_data/alibaba_power_analysis.py
python scripts/real_data/alibaba_stratified_sampling.py
python scripts/real_data/alibaba_extract_linked_records.py main
python scripts/real_data/alibaba_build_splits.py
python scripts/real_data/agentrx_build_joined_tables.py
```
Each script's outputs are content-addressed by the deterministic
inputs above — re-running with unchanged raw files and unchanged
script code reproduces byte-identical `data/audit/`/`data/processed/`
outputs.

---

## Is the data ready for a new frozen Phase 3.1 real-data protocol?

**Partially — main-tier Alibaba and AgentRx are ready; AIOps needs one
more decision before it is.**

- **Alibaba (main tier):** cleaning validated (0 malformed rows once
  the Waiting-status bug was caught and fixed), referential integrity
  confirmed, leakage gate resolved definitively, power-justified
  sample drawn, two split protocols built and frozen. Ready to inform
  a Phase 3.1 protocol draft for job-level failure prediction using
  the request/scheduling-time feature set only (per the leakage gate).
- **AgentRx:** joins verified, domains correctly kept separate,
  leakage fields identified. Ready, with the caveat that n≈44/29 means
  any Phase 3.1 protocol must plan for wide confidence intervals and
  should not set acceptance criteria that assume more statistical
  power than these sample sizes can deliver.
- **AIOps KPI:** schema and leakage semantics are now resolved with
  high confidence, and the one representative day validated
  end-to-end — but the full telemetry corpus is not yet extracted, and
  the fault-log's `start_time`/`log_time`/`log_block` semantics are
  only partially reconciled. A Phase 3.1 protocol could be drafted for
  this dataset now, but the decision of *what time window / how much
  telemetry* to extract should itself be written into that protocol
  **before** doing the extraction — extracting everything now, ahead
  of that decision, risks exactly the kind of "shape the data toward a
  convenient analysis" pattern the brief prohibits.

No cleaning, sampling, or split decision in this report was made after
looking at, or was influenced by, any evaluation metric — none has
been computed. Per your instruction, **stopping here** and waiting for
explicit authorization before Phase 3.1.


---

<a id="phase3-real-data-aiops-protocol"></a>
# PHASE3 REAL DATA AIOPS PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`  
**Role:** AIOps 2020 real-data extraction/evaluation protocol.

# AIOps KPI (CCF AIOps Challenge 2020) — Extraction Protocol & Temporal Model

**Status: protocol-design document. No Phase 3.1–3.6 evaluation run.
No full 20-day telemetry extraction performed. This document
supplements — and does not overwrite or contradict —
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`,
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`, and
`docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md`. Where this document
resolves something the prior docs left open, it says so explicitly and
points back to the prior text rather than deleting it.**

Machine-readable protocol: `configs/aiops_extraction_protocol_v1.json`
(frozen alongside this document, same version/date).

---

## Step 1 — What was already established (review, not re-derived)

Confirming against `data/metadata/aiops_kpi/schema_and_telemetry_findings.md`:

| Item | Status per prior doc | Confirmed here? |
|---|---|---|
| 81 fault-log events, 0 duplicates, 0 malformed | CONFIRMED | Unchanged |
| Tall/long telemetry format (`itemid,name,bomc_id,timestamp,value,cmdb_id`) | CONFIRMED (real data) | Unchanged |
| Metric sampling rates (60s dominant, 120/300/3600s subset) | CONFIRMED (official docs) | Unchanged |
| Timestamps = Unix epoch ms, real absolute calendar time | CONFIRMED (real data, day-label match) | Unchanged |
| `cmdb_id` = entity ID, matches fault log's `name` | CONFIRMED | Unchanged |
| Business metrics (`esb.csv`), 2-min window | CONFIRMED | Unchanged |
| Distributed traces, 6 files, `success`/`elapsedTime` fields | CONFIRMED (real data) | Unchanged |
| `success=False` real, non-trivial rate (0.37% on sampled day) | CONFIRMED (real data) | Unchanged |
| Fault-log fields = ground truth by construction | CONFIRMED | Unchanged |
| `log_time`/`start_time`/`log_block`/`block` relationship | **UNRESOLVED** (partial) | **RESOLVED this pass — see Step 2** |

Nothing above is repeated in redundant detail below; see the source
doc for full context.

---

## Step 2 — Fault-log timestamp reconciliation

### Confirmed (not assumed): the block↔calendar-date correspondence

All 70 events with `index ≥ 100` were re-parsed and cross-tabulated.
**Result:** `block` corresponds almost exactly to the actual calendar
date carried in `start_time`:

| block | start_time date |
|---|---|
| 1 | 2020-05-22 |
| 2 | 2020-05-23 |
| 3 | 2020-05-24 |
| 4 | 2020-05-25 |
| 5 | 2020-05-26 |
| 6 | 2020-05-27 |
| 7 | 2020-05-28 |
| 8 | 2020-05-29 **and** 2020-05-30 (see exception below) |
| 10 | 2020-05-31 |

These 9 dates (block values 1–8, 10 — **no `block=9` value appears
anywhere in the 81-row fault log**) are **exactly** the 10 dates whose
telemetry ships as password-protected `_lock.zip` archives (per
`sha256sum.txt`, cross-referenced against the feasibility audit) —
i.e. the scored preliminary-round evaluation days.

**Exception, reported honestly, not smoothed over:** `block=8` covers
*two* different `start_time` calendar dates (2020-05-29, tied to
`log_block=8`; 2020-05-30, tied to `log_block=6`). This is inconsistent
with a clean 1:1 block→date mapping and was **not** resolved further —
most plausibly a labeling inconsistency in the organizer's own
(manually-edited — see the `~$0故障说明.xlsx` Excel lock file found in
the archive, itself evidence of manual editing) spreadsheet, but this
is speculation, not a documented fact, and is flagged as such.
`start_time` itself (not `block`) is used as the authoritative
timestamp in this protocol, so this exception does not block using
these events — it only means `block`/`log_block` cannot be trusted as
a clean grouping key on their own.

### Confirmed: time-of-day is preserved from `log_time` to `start_time`

59 of 70 (`index ≥ 100`) rows have **identical** hour:minute between
`log_time` and `start_time` (only the calendar date differs). The
remaining 11 rows (all sharing `log_block ∈ {4, 5}`) show a
**consistent, uniform +6:00 shift** (e.g. `log_time` 2020-04-23 18:17
→ `start_time` 2020-05-24 00:17), not random drift. The existence of a
clean, deterministic shift (rather than scattered noise) supports
`log_time`/`start_time` being genuinely related by a systematic
transformation for this subset — but *why* it's 6 hours specifically
(rather than 0, consistent with everything else) was **not**
determined and is not asserted as understood; documented as an
observed, reproducible pattern, not a fully explained one.

### Confirmed (well-supported, not certain): interpretation of `log_time` vs. `start_time`

Putting the evidence together:
- `index 100–169`: `start_time` (May 22–31) lands exactly on the 10
  scored/locked telemetry days; `log_time` (spanning April 11 – May
  15) does not. The natural reading: **`start_time` is the actual
  fault-injection timestamp in the scored telemetry corpus**; `log_time`
  is a reference to when the *same fault pattern* was originally
  logged/templated, on an earlier occasion, and is not itself a
  telemetry-alignment timestamp for these rows.
- `index 1–11`: no `start_time` at all; `log_time` dates are all
  2020-04-11 — which is **exactly the one unlocked day already
  extracted and confirmed to contain real telemetry**
  (`data/intermediate/aiops_kpi/2020_04_11.zip`, per the cleaning
  report). The natural reading: **for these 11 rows, `log_time` *is*
  the actual fault-injection timestamp**, since April 11 is itself a
  real (unlocked, directly usable) telemetry day, with no separate
  "replay" step needed.

**Confidence level: well-supported by three independent, mutually
consistent lines of evidence (block↔locked-day correspondence,
preserved time-of-day, and index-1–11-dates↔unlocked-day match) — but
not verified by, e.g., organizer confirmation or a written spec
statement of this exact mechanism. Treated as CONFIRMED for protocol
purposes given the strength and consistency of the internal evidence,
with the residual uncertainties (block=8 split, the +6h shift's cause,
whether index 1–11 were truly scored) stated plainly above rather than
hidden.**

### Resolved onset timestamp rule (frozen)

```
fault_onset(event) = start_time  if start_time is non-empty
                    = log_time   otherwise (index 1-11 only)
```

This gives all 81 events a single, fully-parsed, real calendar
datetime, ranging 2020-04-11 00:05 to 2020-05-31 05:48.

---

## Step 3 — AIOps prediction/diagnosis temporal model

```
        PRE-FAILURE              DURING-FAILURE        POST-FAILURE
  |------------------------|--------------------|----------------------|
  T0                  fault_onset          fault_onset+5min      (unbounded)
  (onset - WINDOW)                         (documented duration
                                             is a fixed 5min for
                                             every one of the 81
                                             events)
```

- **T_failure** = `fault_onset` as resolved above.
- **PRE-FAILURE** = `[fault_onset − WINDOW, fault_onset)` — the only
  region legitimately usable as **predictive** input. `WINDOW` is
  fixed in Step 4 below.
- **DURING-FAILURE** = `[fault_onset, fault_onset + 5min)` — the
  documented injection duration. Telemetry in this window reflects the
  fault already happening; usable only for **diagnosis**, never
  prediction.
- **POST-FAILURE** = everything after `fault_onset + 5min`. Usable
  only for **diagnosis** (e.g. "how did the system recover," if
  recovery telemetry is later extracted) — never as a predictive input
  for the same event.

**Rule enforced by this protocol:** any predictive (failure-before-it-
happens) experiment may draw features **only** from PRE-FAILURE.
DURING/POST-FAILURE telemetry may be used **only** in an explicitly
labeled diagnosis experiment, never mixed into the same feature set as
a prediction experiment. This mirrors, at the AIOps level, the same
rule already frozen for Alibaba in
`docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`.

---

## Step 4 — Extraction window (frozen, chosen from timing structure, not performance)

All decisions below come from the **observed fault-event timing
structure**, computed once, before any model or metric existed to
optimize against:

- Global minimum gap between any two consecutive fault onsets (sorted
  across all 81 events): **25.0 minutes**. 0/80 consecutive gaps are
  below 25 minutes; the next-smallest gaps are a large cluster at
  exactly 30.0 minutes.
- Minimum per-entity (same `name`) consecutive gap: **30.0 minutes**.
- 50/80 (62.5%) of consecutive gaps are under 45 minutes — a window
  that large would risk absorbing a neighboring fault's effect for a
  majority of events.

**Frozen primary window: 20 minutes pre-failure.**
`T0 = fault_onset − 20min`. This is **strictly inside** the observed
25-minute global minimum gap (5-minute safety margin), so it is
contamination-free for essentially the entire event population — no
event's 20-minute PRE-FAILURE window can include another event's
DURING/POST-FAILURE period. At the dominant 60-second metric sampling
rate this yields **up to 20 observations per metric per entity**;
slower-cadence metrics (300s/600s/3600s — see the metric dictionary)
yield proportionally fewer (down to 0–1 observations for hourly
metrics in a 20-minute window) — this is a real, stated limitation,
not smoothed over by extending the window.

**Frozen DURING window:** `[fault_onset, fault_onset+5min)` — fixed by
the dataset itself (every event's documented `duration` is `5min`),
no design choice involved.

**Explicitly NOT frozen as a default: an extended (e.g. 60-minute)
pre-failure context window.** A 60-minute window would only be
contamination-free for ~51/81 events (62%); for the rest it would
silently blend in a neighboring fault's telemetry. If a longer-context
experiment is wanted later, it must (a) be restricted to the subset of
events with a ≥60-minute preceding gap, explicitly computed and
listed, or (b) individually truncate each event's window to its actual
preceding gap. **Neither is decided or built here** — flagging the
option without picking it, per the "do not create multiple windows and
keep whichever performs best" instruction; if pursued, the exact rule
must be frozen before it's used, same as the primary window was.

**No window was chosen, adjusted, or discarded based on any
preliminary evaluation — no evaluation of any kind has been run
against AIOps telemetry.**

---

## Step 5 — Entity/metric/trace scope (inclusion/exclusion table)

| Data type | Entity level | Pre-failure usable? | Prediction | Diagnosis | Reason |
|---|---|---|---|---|---|
| Platform/infra metrics (`os_linux`, `db_oracle_11g`, `mw_redis`, `dcos_container`, `dcos_docker`) | host/db/middleware/container (`cmdb_id`) | Yes, within the frozen 20-min pre-window | **Yes** | Yes | Genuine pre-outcome telemetry; timestamped, entity-indexed, sampling rate known |
| Business metrics (`esb.csv`) | service (`serviceName`) | Yes, within pre-window (2-min native granularity) | **Yes** | Yes | Same reasoning; coarser granularity (2-min windows, not point samples) |
| Call-trace fields EXCEPT `success`/`elapsedTime` (`callType`, `traceId`, `cmdb_id`, timestamps, entity/service identifiers) | call | Yes, within pre-window | **Yes** | Yes | Structural/identifying fields, not an outcome |
| Call-trace `success`, `elapsedTime` | call | **No**, for predicting that same call's own outcome | **No** (as same-call input) / **Yes** (as an aggregated PRE-window feature, e.g. "% failed calls in the preceding 20 min," which does not use any individual call's own future-relative outcome) | **Yes** | A call's own outcome is what would be predicted — using it as that call's input is circular; using PAST calls' aggregated outcome rate as a feature for a LATER prediction target is legitimate and does not leak |
| Fault log: `object`, `fault_desrcibtion`, `kpi`, `name`, `container` | fault event | No | No | **Yes / label** | Ground truth by construction (organizer-injected) |
| Fault log: `log_time`, `start_time`, `log_block`, `block` | fault event | No (as features) | No | Used only to draw the T0 cutoff | Define the label's timing, not an observable signal |
| Deployment architecture (`1应用部署架构清单.xlsx`: entity→container mapping) | entity | Yes (static) | Yes | Yes | Static topology, never leaking |
| Metric/field dictionaries (units, sampling rate, `bomc_id`) | n/a | Yes (static, defines schema) | Yes (as metadata, not a feature itself) | Yes | Reference data, not an observation |

**Excluded entirely from this protocol's initial scope:** the 5
`.xlsx` per-tech-stack metric catalogs' full contents beyond what's
already extracted into the schema-findings doc (already sufficient for
the field dictionary; no further xlsx parsing planned). The 20-day
telemetry corpus beyond `2020_04_11` (already-validated sample day) —
not extracted until this protocol is explicitly authorized to run.

---

## Step 6 — Event-level independence / effective N

- **81 raw fault-log rows**, but these are **not 81 independent
  samples** in the sense of arising from 81 independent underlying
  systems or conditions:
  - Only **16 distinct entities** (`name`) are targeted across all 81
    events (`docker_001` alone accounts for 10; `db_003`/`docker_006`
    7 each; full distribution in
    `configs/aiops_extraction_protocol_v1.json`). 15/16 entities have
    ≥2 fault events.
  - Object-type split: `docker` 49, `os` 20, `db` 12 — the 5
    fault-category labels are unevenly distributed (`network delay`
    31, `CPU fault` 19, `network loss` 19, `db connection limit` 7,
    `db close` 5).
  - No two events overlap in time (minimum gap 25 min, fixed 5-min
    duration) — so events are **temporally** independent (no double-
    counting the same incident), but repeated faults on the same
    entity are **not statistically independent draws** from a
    population of entities — an entity's baseline behavior, hardware,
    or configuration is a shared confound across its own repeated
    events.
- **Recommended clustering structure for any variance/power
  estimate:** cluster by `name` (16 clusters), not treat n=81 as 81
  i.i.d. observations. A naive n=81 analysis would understate
  uncertainty.
- **Effective N is honestly smaller than 81** — bounded below by 16
  (entity clusters) and above by 81 (raw events), with the true
  effective value somewhere between depending on how much between-
  entity vs. within-entity variance the eventual model captures. This
  protocol does not pick a single number to paper over that — it
  requires any future AIOps power/CI computation to report results
  **both** ways (naive n=81 and entity-clustered) rather than picking
  the more favorable one.

---

## Step 7 — What can realistically be powered

Applying the same class of Hanley-McNeil AUROC-precision reasoning
used for Alibaba (`scripts/real_data/alibaba_power_analysis.py`), but
honestly reporting what n=81 (or effective n≈16–81) can support:

| Planned experiment | Effective N | Verdict |
|---|---|---|
| Binary "any fault vs. no fault" detection, entity×window level | Requires defining a negative (non-fault) window population — **not yet constructed**; even optimistically pairing each of 81 positive windows with matched negatives gives n≈162 raw / ≈32 entity-clustered | **UNDERPOWERED / EXPLORATORY** — even at the generous end this is far below the ~3,500+ Alibaba needed for ±0.02 AUROC precision |
| 5-class fault-category classification | Per-class n = 5 (`db close`) to 31 (`network delay`) | **UNDERPOWERED / INCONCLUSIVE-PRONE** for the rare classes (`db close` n=5, `db connection limit` n=7) — any per-class metric on these will have enormous confidence intervals; only the two largest classes (`network delay` n=31, `CPU fault`/`network loss` n=19 each) could support even exploratory per-class estimates |
| Object-type (docker/os/db) classification | n = 49/20/12 | **EXPLORATORY** — 3-way, moderate imbalance, still well below any AUROC-precision target computed for Alibaba |
| Entity-level generalization ("unseen entity") | 16 entities total, ≤15 with multiple events to split from | **UNDERPOWERED** — leave-some-entities-out at this scale cannot support a confident generalization claim, only a directional/qualitative one |
| Cross-dataset comparison of AIOps vs. Alibaba findings | n/a (different populations) | Valid only as a **qualitative** consistency check ("did the same broad pattern appear"), never a joint statistical test |

**No AIOps hypothesis in this dataset should be framed as
confirmatory.** Every AIOps-based Phase 3.1-equivalent experiment
should be pre-labeled **EXPLORATORY**, and any negative/null/
inconclusive result must be reported as such, not as evidence of
absence.

---

## Step 8 — Frozen extraction protocol

See `configs/aiops_extraction_protocol_v1.json` for the exact,
versioned, machine-readable rules. Summary:

- **Fault events included:** all 81 (no cherry-picking); each tagged
  with its resolved `fault_onset`, `resolution_confidence` (see Step
  2), and cluster id (`name`).
- **Eligibility for a PREDICTION-framed experiment:** an event is
  eligible only if its full 20-minute PRE-FAILURE window falls within
  an extracted, available telemetry day. Since only `2020-04-11` is
  extracted so far, **only events whose PRE-FAILURE window is fully
  contained in `2020-04-11` are currently eligible** — from the fault
  log, that's `index 1–11` only (11 events, all with `log_time` on
  2020-04-11). This is a real, current constraint, not a future one —
  stated plainly so nobody assumes 81 events are already usable.
- **Telemetry dates/files:** for a full-scope future extraction (not
  authorized yet): all 20 daily archives, all 3 telemetry families
  (platform, business, trace) at their native schema — no metric or
  trace file excluded a priori (per the Step 5 inclusion table, only
  the fault-log's own ground-truth fields and same-call outcome
  fields are excluded as features).
- **Entity filtering:** none — extract all `cmdb_id`s present in a
  given day's files (not restricted to only the 16 fault-targeted
  entities), so that non-faulted entities are available as a
  comparison/negative population if a future step needs one.
- **Timestamp conversion:** platform/business/trace timestamps are
  already Unix epoch ms — convert to UTC+8 (`Asia/Shanghai`) for
  human-readable alignment against the fault log's local-time
  `log_time`/`start_time`; **preserve the original epoch-ms value
  alongside** the converted one, never overwrite it.
- **Event-to-telemetry alignment:** join on `cmdb_id == fault_log.name`
  and `telemetry.timestamp ∈ [fault_onset − 20min, fault_onset)` for
  PRE-FAILURE, `[fault_onset, fault_onset+5min)` for DURING.
- **Missing telemetry handling:** if an entity/metric has zero
  observations in a window (e.g. an hourly metric in a 20-min window),
  record explicit `MISSING`/count=0 — never impute a value.
- **Overlapping events:** none exist under the frozen 20-minute window
  (by construction, see Step 4) — no overlap-resolution rule is
  needed at this window size; if a future longer window is pursued,
  an explicit overlap rule must be frozen first (not decided here).
- **Independent unit:** fault event (`index`), with entity (`name`) as
  the required clustering variable for any variance estimate (Step 6).
- **Provenance:** every extracted telemetry row keeps `source_file`
  (the daily zip + inner CSV path), `source_dataset="AIOps KPI"`,
  original epoch-ms timestamp, and the `fault_log.index` it was
  extracted for (if any) — no row is stripped of its origin.
- **Determinism:** extraction is a pure filter (entity + time-window
  membership) with no randomness — fully reproducible from the frozen
  rules above and the raw zip's own checksum.

**This protocol is frozen but NOT yet executed against the remaining
19 daily archives.** Execution requires separate authorization per
Step 9's explicit instruction.

---

## Step 9 — Not extracted

Confirmed: no additional telemetry beyond the already-extracted
`2020_04_11` day was pulled in this pass. The remaining 19 days
(several password-locked) remain unextracted, pending authorization.

---

## Step 10 — Unified benchmark preservation (forward-looking only, not built)

For any future extraction, each output record will carry:
`source_dataset="AIOps KPI (CCF AIOps Challenge 2020)"`,
`source_file`, `cmdb_id` (native entity id, not remapped to Alibaba's
`job_name`/`machine` conventions), native epoch-ms timestamp (plus a
converted UTC+8 field), `fault_log_index` (native event id, when
applicable), and explicit `MISSING` markers for any Alibaba-style
field (e.g. `recovery_action`) that AIOps does not itself provide. No
common schema is forced across AIOps and Alibaba/AgentRx at this
stage.

---

## Deliverables produced this pass

1. Timestamp reconciliation — this document, Step 2.
2. Temporal model — Step 3.
3. Inclusion/exclusion table — Step 5.
4. Independence/effective-N analysis — Step 6.
5. Power/feasibility assessment — Step 7.
6. Frozen extraction protocol — Step 8 + `configs/aiops_extraction_protocol_v1.json`.
7. Updated hypothesis assessment — see table below.
8. Unresolved issues — see below.

### Updated AIOps row for the dataset-to-hypothesis matrix

Supersedes (adds detail to, does not contradict) the AIOps row in
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §18:

| Dataset | 3.1 | 3.2 | 3.3 | 3.4 | 3.5 | 3.6 | Independent unit | Effective N | Notes |
|---|---|---|---|---|---|---|---|---|---|
| AIOps KPI | Yes, protocol now frozen | Yes, but EXPLORATORY (Step 7) | Yes — real absolute time confirmed | Yes, EXPLORATORY | Yes, EXPLORATORY | Diagnosis: Yes (injected-category); Recovery: No | fault event, entity-clustered (16 clusters) | 81 raw / effectively 16–81 depending on clustering; currently only 11 events (index 1–11) have their PRE-FAILURE window inside already-extracted telemetry | Timestamp semantics now resolved with high confidence; extraction scope frozen but not executed beyond 1 day |

### Unresolved issues (explicit, not hidden)

1. `block=8`'s split across two calendar dates (2020-05-29/30) — not
   explained, only documented.
2. The +6-hour `log_time`→`start_time` shift for `log_block ∈ {4,5}`
   — pattern confirmed, cause not determined.
3. Whether `index 1–11` were genuinely part of the *scored* evaluation
   or an unscored preview/template batch — plausible but not certain.
4. No negative (non-fault) window population has been defined yet —
   required before any binary detection framing can move past
   "EXPLORATORY."
5. 19 of 20 daily telemetry archives remain unextracted.
6. The 5 per-tech-stack `.xlsx` metric dictionaries' full row-by-row
   catalogs (beyond what's already summarized) were not exhaustively
   parsed (merged-cell issues noted previously stand).

---

## Is AIOps now ready for inclusion in the frozen Phase 3.1 real-data protocol?

**The AIOps-specific questions this task was scoped to answer are
resolved**: timestamp semantics (high confidence), temporal model
(frozen), extraction window (frozen, evidence-derived), inclusion/
exclusion rules (frozen), independence structure (documented, honestly
smaller than the raw row count suggests), and power expectations
(every AIOps hypothesis pre-labeled EXPLORATORY, not confirmatory).

**Not yet ready for an evaluation-scale protocol**, because: (a) only
one telemetry day is extracted, giving only 11 currently-eligible
predictive events; (b) no negative-window population is defined; (c)
several minor semantic gaps remain (block=8, the 6h shift). These are
exactly the kind of items a Phase 3.1 protocol document itself should
enumerate as open before evaluation, rather than silently resolving by
extracting everything now.

Per your instruction, **stopping here** — no Phase 3.1 run, no further
telemetry extraction, Phase 3 frozen docs and Phase 4 untouched, raw
files unmodified. Waiting for explicit authorization before extracting
the remaining 19 days or beginning Phase 3.1.


---

<a id="phase3-real-data-aiops-negative-window-protocol"></a>
# PHASE3 REAL DATA AIOPS NEGATIVE WINDOW PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`  
**Role:** AIOps negative-window (non-fault) sampling protocol.

# AIOps KPI — Negative/Control Window Protocol (frozen before extraction)

**Status: FROZEN, version 1.0.0, 2026-08-13. Written and frozen BEFORE
any telemetry beyond the single already-validated day (`2020_04_11`)
was extracted, and before any window's actual telemetry values were
inspected.** This is a pure temporal/entity-membership rule — nothing
here depends on what any window's data looks like.

Companion to `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` (the extraction
scope/timestamp/window protocol this builds on) and
`configs/aiops_extraction_protocol_v1.json`. Does not modify either.

## Why a fault-free-day discovery matters here

Applying the already-resolved `fault_onset` rule
(`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` Step 2) to all 81 events
shows every event's onset falls on exactly one of 11 calendar dates:
`2020-04-11` (11 events) or one of the ten `2020-05-22`…`2020-05-31`
dates (70 events). The dataset's other 4 extractable telemetry days —
**`2020-04-20`, `2020-04-21`, `2020-04-22`, `2020-04-23`** — have **zero**
resolved fault onsets. This was determined by pure date arithmetic on
already-frozen onset timestamps, not by inspecting any telemetry
value, and is recorded here before extraction, not discovered by
looking for "convenient" negative examples after the fact.

## Eligible entities

The same **43 fault-eligible entities** used throughout this protocol
family: 8 `docker_*`, 13 `db_*`, 22 `os_*` (per
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`'s entity
roster). `csf_*`/`redis_*`/`osb_*` entities are **excluded** — they
were never fault-injection targets in this preliminary round (per the
fault log's `object` field, only ever `docker`/`db`/`os`), so using
them as "negative" examples would compare across entity *types*, not
just fault/no-fault states — a confound this protocol avoids by
construction, not by post-hoc filtering.

**Known limitation, stated not hidden:** 27 of the 43 fault-eligible
entities never appear in the actual 81-row fault log at all. It is
possible (not confirmed, not ruled out) that these entities were
excluded from injection for some operational reason unrelated to their
"normalcy" — this protocol cannot distinguish "never targeted because
representative of normal operation" from "never targeted for an
unrelated reason." Both fault-log entities (in their fault-free
periods) and never-targeted entities are included as candidate
negative sources; this limitation applies to the latter group.

## Window definition

- **Length: 20 minutes** — identical to the frozen positive
  (PRE-FAILURE) window, for direct comparability.
- **Grid construction:** each extractable telemetry day is partitioned
  into 72 fixed, sequential, non-overlapping 20-minute blocks aligned
  to day boundaries (`00:00–00:20`, `00:20–00:40`, …, `23:40–00:00`).
  Non-overlap is guaranteed by construction, not checked after the
  fact.

## Exclusion rule (per entity, per candidate block)

A candidate block `[w_start, w_start+20min)` for entity `E` is
**ineligible** if `E`'s own resolved fault onset falls within
**60 minutes before or after** `w_start` (i.e., excluded interval
`[w_start − 60min, w_start + 20min + 60min]`). Rationale for 60
minutes: comfortably exceeds the 20-minute PRE-FAILURE window plus the
5-minute DURING-FAILURE duration, with an added ~35-minute margin for
unmodeled recovery/aftereffects — a round, conservative number chosen
without reference to any observed recovery duration (none has been
measured; if one is measured later, this number is not silently
revised to fit it).

This rule is entity-specific: a block excluded for `docker_001` (near
one of its own faults) may still be eligible for `docker_002` on the
same day/time, since faults target one entity at a time.

Blocks on the 4 confirmed fault-free days require no exclusion check
per this rule (no fault onset exists to exclude against) but are still
subject to the eligible-entity restriction above.

## Overlap with positive windows

By construction, no candidate negative block can overlap a positive
window for the *same* entity (the exclusion rule above already removes
anything within 60 minutes of that entity's own fault onset, a strict
superset of the 20-minute positive window). No additional check is
needed, but the validation pass (separate document) verifies this
holds rather than assuming it.

## Natural population vs. sampled pool (two separate, both documented)

Per the "avoid artificial balance" instruction: this protocol reports
**both** a natural population size (the full eligible-grid count,
computed by date/entity/exclusion arithmetic alone, no telemetry
extraction required) and a separate, smaller, **sampled** pool that is
actually extracted and materialized — extracting telemetry for the
full natural population (tens of thousands of candidate blocks) before
any decision exists to use them would be unjustified extraction, not
a reproducibility improvement.

- **Natural population:** computed and reported in
  `data/audit/aiops_kpi/negative_window_natural_population.json`
  before any sampling.
- **Sampled pool** (frozen rule, decided here, not after inspecting
  the natural population's size):
  - Per-entity cap: **20 negative windows per entity** (round number,
    chosen for tractability, not tuned to any target ratio).
  - Selection: within each eligible entity, sort all its eligible
    candidate blocks lexicographically by `(date, block_start)`, then
    draw up to 20 via `random.Random(SEED=42).sample(...)` — same
    deterministic pattern as the Alibaba sampling scripts.
  - If an entity has fewer than 20 eligible blocks, all of its
    eligible blocks are taken (no shortfall padding from another
    entity).
  - **No selection may be based on inspecting that block's own
    telemetry values** — the grid, exclusion rule, and per-entity
    sample are fixed entirely from timestamps and entity IDs.

This yields an expected sampled-pool ceiling of `43 entities × 20 =
860` negative windows (fewer in practice wherever an entity has fewer
than 20 eligible blocks) against 81 positive windows — an
**imbalanced, not artificially 50/50**, pool (~10.6:1 at the ceiling),
which is reported alongside the natural population's true (much
larger) imbalance, not presented as "the" real-world prevalence.

## What negative windows must NOT be

Enforced by the rules above, restated explicitly per the brief's
checklist:
- Must not overlap a positive window (guaranteed by the 60-min
  exclusion, a strict superset of the 20-min positive window).
- Must not contain a known impending fault within the prediction
  horizon (guaranteed — a block within 60 min *before* a fault onset
  is excluded).
- Must not be a post-failure recovery window (guaranteed — a block
  within 60 min *after* a fault onset is excluded).
- Must not use information from after its own prediction cutoff (the
  block's own end time *is* its cutoff — nothing beyond it is used to
  select it).
- Must not be selected because telemetry "looks normal" (guaranteed —
  selection is timestamp/entity arithmetic only, performed before any
  telemetry for these days beyond `2020-04-11` was extracted).


---

<a id="phase3-real-data-aiops-preparation-complete"></a>
# PHASE3 REAL DATA AIOPS PREPARATION COMPLETE
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md`  
**Role:** AIOps real-data preparation completion record.

# AIOps KPI — Final Data Preparation Report

**Status: data preparation complete for the frozen 20-minute-window
scope. No Phase 3.1–3.6 evaluation run. Raw files unmodified (verified
by checksum, see below). Supplements — does not overwrite —
`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`,
`docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`,
`data/metadata/aiops_kpi/schema_and_telemetry_findings.md`.**

---

## 1. Telemetry extraction

All 15 extractable daily archives (per
`configs/aiops_extraction_protocol_v1.json`) were processed:
`2020-04-11, 04-20, 04-21, 04-22, 04-23, 05-22…05-31`. No date was
added or dropped from the frozen list; no password/lock mechanism was
actually needed for this copy of the archive (the outer per-day zips
in `data/raw/aiops_kpi/`'s copy are directly readable — see below).

- **Platform metrics** (5 files/day) + **business metrics**
  (`esb.csv`) extracted **in full**, all 15 days — not filtered, per
  the frozen scope. Written to
  `data/processed/aiops_kpi/{platform,business}/`.
- **Call-traces** (6 files/day) stream-filtered to rows whose
  `cmdb_id` is one of the 43 fault-eligible entities AND whose
  timestamp falls inside a pre-registered window (positive or
  sampled-negative) — the window set was frozen from fault-log timing
  alone, *before* any trace content was read, so this is a
  computational-feasibility filter, not a results-driven one. Written
  to `data/processed/aiops_kpi/trace_windows/`. Verified by an
  independent re-check: **0 kept rows fall outside their scheduled
  window** (spot-checked in full on `2020-04-22`).
- Full per-day, per-file counts: `data/audit/aiops_kpi/extraction_report.json`.
- **Raw archive integrity:** `sha256sum` of
  `data/raw/aiops_kpi/AIOps挑战赛2020预赛数据.zip` re-verified
  unchanged (`0b50d8a6...5162dce`) after extraction.

### Correction to a prior assumption: no password layer needed

`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` and
`configs/aiops_extraction_protocol_v1.json` both stated the 10
`2020-05-22`…`2020-05-31` dates were "password-locked" per the
dataset's own `passwd.txt`/`unzip_all.sh`/`sha256sum.txt`. On actual
extraction, **this copy of the archive does not have that lock layer**
— each day's outer zip (e.g. `AIOps挑战赛数据/2020_05_22.zip`) opens
directly with no inner `_lock.zip` and no password prompt. Whoever
originally staged this raw file for the project evidently already
merged/unlocked it before packaging. This is a factual correction, not
a silent one — the original documents' statements are left as written
(they were correct **about the dataset's own distribution
mechanism**, just not applicable to this particular staged copy).

### New finding: every daily archive covers only 00:00–05:59:59 local time

**Confirmed across all 15 days independently** (not a single-day
artifact): every extracted platform-metric file's timestamp range is
exactly `00:00:00`–`05:59:59` local (UTC+8), regardless of date. This
was not known or assumed in either prior protocol document — both
implicitly modeled a full 24-hour day (the negative-window grid used
72 20-minute blocks/day). It was discovered here, empirically, by
extraction — not guessed, not assumed, and it directly explains why
the majority of randomly-sampled negative-window candidates failed
telemetry-coverage validation (Section 3 below), and *why all 81 fault
events happen to fall inside this window* (organizers evidently only
ran/collected telemetry during a fixed daily 6-hour window, and only
injected faults inside it).

**This finding does not retroactively change the frozen 20-minute
window or the frozen negative-window construction rule** — per the
brief's explicit instruction not to alter a frozen protocol to obtain
more convenient data. It does mean the actual usable negative-window
population is smaller than the naive 45,911-candidate "natural
population" figure computed in
`docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md` implied (that
figure assumed all 72 blocks/day were viable; only ~18/72 are, given
the true 6-hour coverage). A coverage-adjusted natural-population
estimate: `43 entities × ~15 usable days × 18 blocks × (fraction not
excluded)` ≈ roughly a quarter of the original 45,911 figure — i.e.
still in the low thousands, still far larger than what was sampled,
so this does not change the qualitative conclusion that positives are
rare relative to the natural population. The original 45,911 number is
left in its source document unedited, with this correction pointing to
it rather than replacing it.

---

## 2. Timestamp anomaly resolution (data-driven, not guessed)

Per your instruction to resolve conservatively using actual data:

| Issue | Prior status | New status | Evidence |
|---|---|---|---|
| Were `index 1–11` events actually injected into real telemetry? | UNRESOLVED (plausible from date-matching only) | **CONFIRMED** | `docker_003`'s `container_cpu_used` metric on `2020-04-11` shows a clean baseline (~1–2%) jumping to **98–100%** for ~5 minutes starting ~3 minutes after event `index=1`'s resolved onset (`2020-04-11 00:05`) — a textbook CPU-fault signature at the exact right entity, metric, and time. |
| Is `start_time` (not `log_time`) the real injection timestamp for `index ≥ 100`? | PROBABLE (date/structural evidence only) | **PROBABLE, now with direct signal support** | `docker_001`'s `container_cpu_used` on `2020-05-22` shows elevated values (up to 107%, vs. a noisier ~30-80% baseline) concentrated in the minutes following event `index=101`'s resolved onset (`2020-05-22 00:48`) — noisier than the April example (this entity/day has a higher baseline load) but directionally consistent. **Not independently checked for every fault category** — only `CPU fault`-type events were spot-checked, since `container_cpu_used` gives the cleanest single-metric signature; `network delay`/`network loss`/`db connection limit`/`db close` events were not signal-verified this pass. |
| `block=8` spans two different `start_time` calendar dates | UNRESOLVED | **Still UNRESOLVED** | No new evidence found; most plausibly a labeling inconsistency in the organizer's (manually-edited) spreadsheet. **Does not affect this protocol's correctness** — `block`/`log_block` are never used as the authoritative timestamp source, only `start_time`/`log_time` (per-row) are, and those remain valid and internally consistent regardless of the `block` grouping label's own inconsistency. |
| +6h `log_time`→`start_time` shift for `log_block∈{4,5}` | UNRESOLVED (pattern confirmed, cause unknown) | **Still UNRESOLVED** | No new evidence found. Same non-impact rationale as above — `start_time` itself (not the shift's explanation) is what this protocol relies on. |

**Conservative handling adopted:** all 81 events are retained and used
via the already-frozen `fault_onset` rule (`start_time` if present,
else `log_time`) exactly as documented previously — no event was
discarded, reinterpreted, or given a fabricated timestamp because of
the two still-unresolved items above.

---

## 3. Positive window validation

Script: `scripts/real_data/aiops_validate_positive_windows.py`.
Full results: `data/audit/aiops_kpi/positive_window_validation.json`.

**Result: 81/81 VALID.** Every positive window independently
re-derived from the raw fault log (catching any transcription bug —
none found), has exactly a 20-minute span, has ≥1 telemetry
observation from the object-appropriate metric family within the
window, has zero observations at or after the fault's own onset
inside that window (no post-failure contamination), and does not
overlap another event's onset for the same entity.

One implementation bug was caught and fixed during this step: an
early version of the validation script's "no post-onset
contamination" check scanned an entity's *entire day* of telemetry
rather than only the rows already confirmed to be inside the window,
which spuriously flagged all 81 windows as contaminated (since of
course telemetry exists somewhere later in the day). Corrected before
trusting the result — documented here rather than silently fixed.

---

## 4. Negative window validation

Script: `scripts/real_data/aiops_validate_negative_windows.py`.
Full results: `data/audit/aiops_kpi/negative_window_validation.json`
(includes a full rejection report for all 715 rejected candidates).

**Result: 145/860 VALID, 715 rejected.** Rejection breakdown: **all
715** rejections were `has_telemetry_coverage=False` (Section 1's
6-hour-coverage finding) — **zero** rejections were due to the
fault-exclusion or positive-overlap checks failing, confirming the
frozen exclusion-window construction logic (§Step 4 of the negative
protocol) was itself correctly built; the shortfall is purely a data-
availability constraint discovered only once extraction ran, not a
flaw in the sampling rule.

**No negative window was added, swapped, or re-sampled to compensate
for the low yield.** The 145 that passed are the final, honest
negative pool.

---

## 5. Final effective sample size

| Quantity | Count |
|---|---|
| Raw fault-log events | 81 |
| Qualifying positive windows (validated) | **81** (100%) |
| Unique positive-window entities | 16 |
| Candidate negative windows (frozen sampled pool) | 860 |
| Final valid negative windows | **145** (16.9%) |
| Unique negative-window entities | 43 |
| Entities appearing in both positive and negative pools | 16 |
| Entities only in the negative pool | 27 |
| **Total unique entities across both pools** | **43** |
| Positive events per entity | min 1 (`os_001`), median 5, max 10 (`docker_001`) |
| Negative windows per entity | min 2, median 3, max 7 (`docker_003`) |

**Independent unit:** entity (43 clusters), not window (226 total
positive+negative windows). A naive analysis treating 226 as i.i.d.
would overstate precision — any real evaluation must use
entity-clustered variance/bootstrap, or an entity-disjoint split for
any entity-generalization claim (`docker_001`'s 10 positives + 3
negatives cannot be split across train/test without leaking that
specific entity's baseline behavior across the split).

---

## 6. Updated power / feasibility assessment

Using the actual final population (n_pos=81, n_neg=145, total=226),
Hanley-McNeil AUROC-precision analysis (same method as
`scripts/real_data/alibaba_power_analysis.py`):

| Assumed AUROC | 95% CI half-width at n=226 |
|---|---|
| 0.55 | ±0.079 |
| 0.60 | ±0.078 |
| 0.65 | ±0.076 |
| 0.70 | ±0.074 |
| 0.75 | ±0.069 |
| 0.80 | ±0.064 |

Compare to Alibaba's main tier (n=10,000), which achieves ≈±0.02–0.03.
**AIOps remains EXPLORATORY, not confirmatory** — a ±0.07-ish AUROC CI
supports a directional read ("is there any detectable signal at all")
but not a precise estimate or a confident comparison against a
baseline.

| Planned experiment | Effective N | Updated verdict |
|---|---|---|
| Binary 20-min-window fault-vs-no-fault detection | 81 pos / 145 neg, 43 entity clusters | **EXPLORATORY** — now has an actual, real, non-hypothetical population (previous assessment could only note this required an undefined negative population); ±0.07 CI at best |
| 5-class fault-category classification | same per-class counts as before (5–31) | **UNDERPOWERED / INCONCLUSIVE-PRONE**, unchanged |
| Object-type (docker/os/db) classification | 49/20/12 positive events | **EXPLORATORY**, unchanged |
| Entity-level generalization | 43 entities, 16 with positives | **UNDERPOWERED**, unchanged, now with confirmed real per-entity window counts (median 3-5) reinforcing this |

No change was made to any window, entity list, or sampling rule after
seeing these numbers — this table reports what the already-frozen
protocol yielded.

---

## 7. Files created this pass

- `scripts/real_data/aiops_build_windows.py` (positive/negative window
  definitions — pure logic, run before any telemetry beyond
  `2020-04-11` existed)
- `scripts/real_data/aiops_extract_telemetry.py` (the extraction
  itself)
- `scripts/real_data/aiops_validate_positive_windows.py`
- `scripts/real_data/aiops_validate_negative_windows.py`
- `data/audit/aiops_kpi/{positive_windows,negative_window_natural_population,negative_windows_sampled,extraction_report,positive_window_validation,negative_window_validation}.json`
- `data/processed/aiops_kpi/{platform,business,trace_windows}/*.csv`
  (all provenance-tagged: `source_dataset`, `source_file`,
  `extraction_day`)
- `docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md` (written
  in the prior turn, referenced not modified)
- This document.

---

## 8. Remaining unresolved issues

1. `block=8`'s two-date split — unexplained (no operational impact,
   §2).
2. The +6h `log_time` shift for `log_block∈{4,5}` — unexplained (no
   operational impact, §2).
3. Only `CPU fault`-category events were signal-verified against real
   telemetry; `network delay`/`network loss`/`db connection limit`/
   `db close` were not independently checked for a detectable
   signature.
4. The coverage-adjusted natural-population count (§1) is an estimate,
   not a re-run of the exact grid computation — if a future step needs
   the precise adjusted figure, `aiops_build_windows.py`'s grid
   construction would need a documented new version restricted to
   `00:00–06:00`, which was **not done here** (would count as altering
   the frozen protocol after seeing data, exactly what's prohibited).
5. 27 of the 43 fault-eligible entities never appear in the fault log
   at all — still an open question (noted originally in the negative-
   window protocol) whether this reflects genuine normalcy or an
   unrelated exclusion reason.

---

## Is AIOps now ready for the frozen Phase 3.1 real-data protocol?

**Yes, with its limitations stated plainly, not hidden:** a real,
validated, entity-clustered positive/negative population now exists
(81/145), every window has confirmed telemetry coverage, provenance is
preserved throughout, and the power ceiling is known and modest
(±0.07 AUROC CI). This is sufficient to support an **EXPLORATORY**
Phase 3.1 real-data evaluation on AIOps — not a confirmatory one, and
any Phase 3.1 protocol document should say so explicitly rather than
implying AIOps carries the same evidentiary weight as Alibaba's
much larger sample.

Per your instruction, **stopping here** — no Phase 3.1 run. Raw files
unmodified (checksum re-verified). Phase 3 frozen docs and Phase 4
untouched. Waiting for explicit authorization before Phase 3.1.


---

<a id="phase3-real-data-protocol"></a>
# PHASE3 REAL DATA PROTOCOL
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_PROTOCOL.md`  
**Role:** The overall frozen real-data Phase 3 protocol (all three datasets).

# Phase 3 Real-Data Replication — Frozen Evaluation Protocol

**Status: FROZEN (protocol design only — no evaluation has been run under this document).**
**Version: 1.0**
**Date frozen: 2026-08-13**

---

## 0. Relationship to the original Phase 3

This document defines **"Phase 3 Real-Data Replication"** (internally: **Phase 3.1-RD**, to avoid collision
with the original synthetic `docs/PHASE3_1_EVALUATION_PROTOCOL.md`). It is a **separate, additional** research
track, not a continuation, correction, or replacement of the original Phase 3.

- The original Phase 3 (`docs/PHASE3_1_EVALUATION_PROTOCOL.md` through `docs/PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`,
  frozen by `docs/PHASE3_FREEZE.md`) evaluated the failure-risk pipeline on a fully synthetic, controlled generator
  (`src/data/synthetic.py::generate_regime_stream`). Its results, configs, scripts, and reports are **frozen and
  will not be edited, rerun, or reinterpreted** by this document or by anything downstream of it.
- This document instead asks: **do the original Phase 3 findings hold up when the same class of questions is
  asked of real-world data?** The answer may be "yes," "no," "partially," or "not evaluable" per hypothesis
  per dataset — all four outcomes are acceptable and none is preferred a priori (see §21, Research Integrity).
- No file under `experiments/results/phase3_1/` … `phase3_6/`, no file listed in `docs/PHASE3_FREEZE.md`'s
  frozen-artifact list, and no synthetic-data config (`configs/phase3_1_protocol.json`,
  `configs/phase3_5_attack_protocol.json`, `configs/phase3_6_decision_recovery_protocol.json`) is modified by
  this protocol or by any phase run under it.
- All real-data results are written to a **new, separate** results tree: `experiments/results/phase3_real_data/`.
  This tree does not exist yet and is not created by this document — it is created only when Phase 3.1-RD is
  actually run, which requires separate authorization (see §26).

---

## 1. Research objective

Determine whether the six hypotheses established in the original (synthetic) Phase 3 —

- **H1** — a supervised failure-risk signal exists beyond calibrated confidence (Phase 3.1/3.2)
- **H2** — that signal's source is supervised learning, not representation richness (Phase 3.2C)
- **H3** — the signal generalizes across concept drift (Phase 3.3)
- **H4** — the signal generalizes across covariate-shift attacks (Phase 3.5)
- **H5** — the signal is complementary to calibrated confidence (Phase 3.6.1) and changes decision-cost
  outcomes (Phase 3.6.2)
- **H6** — the pipeline can diagnose the cause of a failure/anomaly (Phase 3.6.3)
- **H7** — the pipeline can recover from a diagnosed failure (Phase 3.6.4–3.6.5)

remain supported, are contradicted, are only partially supported, or cannot be adjudicated, when the same
class of question is posed against real-world operational data: Alibaba GPU Cluster Trace 2020, AIOps
Challenge 2020, and Microsoft AgentRx (Magentic-One, τ-Retail).

This is explicitly **not** an attempt to reproduce or exceed the original AUROC/AUPRC numbers, and the
protocol below is not tuned to make any result "work." See §21.

---

## 2. Dataset inventory

| Dataset | Domain | Raw record scale | Real-data-eligible sample | Independent unit | Effective N |
|---|---|---|---|---|---|
| Alibaba GPU Cluster Trace 2020 | ML training job scheduling/failure | 1,055,501 jobs / 7,522,002 instances | 988,910 eligible terminal jobs; sampled tiers 2,000 / 10,000 / 50,000 | job | 10,000 (main tier, used for all confirmatory-capable analysis) |
| AIOps Challenge 2020 (CCF) | Microservice fault detection | 81 fault-log events across 15 telemetry days | 81 positive windows + 145 negative windows | fault entity | 226 windows / 43 entities (16 positive, 27 negative-only) |
| Microsoft AgentRx — Magentic-One | LLM agent trajectory failure/diagnosis | 58 trajectories | 44 annotated trajectories | trajectory | 44 |
| Microsoft AgentRx — τ-Retail | LLM agent trajectory failure/diagnosis | 29 trajectories | 29 annotated trajectories | trajectory | 29 |

These four datasets are evaluated **separately**. They are never pooled into one experiment (see §4, §12, §21).
Provenance for each is documented in `docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md` and
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`.

---

## 3. Dataset-to-hypothesis mapping

`✅ EVALUABLE (confirmatory-capable)` · `🟡 EVALUABLE (exploratory only)` · `⚪ NOT EVALUABLE`

| Hypothesis | Alibaba GPU2020 | AIOps 2020 | AgentRx Magentic | AgentRx τ-Retail |
|---|---|---|---|---|
| H1 — supervised risk signal exists | ✅ (n=10,000 job main tier) | 🟡 (n=226 windows, 43 entities) | 🟡 (n=44) | 🟡 (n=29) |
| H2 — mechanism is supervision, not representation | ✅ | 🟡 | ⚪ (no representation-ablation axis in the data — no engineered feature families to compare) | ⚪ |
| H3 — concept-drift generalization | 🟡 (relative-time only; real distribution shift confirmed, see §9) | 🟡 (real absolute calendar time across 15 days) | ⚪ (no timestamps in AgentRx at all — see §13) | ⚪ |
| H4 — covariate-shift / attack generalization | 🟡 (only naturally occurring covariate variation available; no synthetic attack matrix applies to real data) | 🟡 (naturally occurring telemetry noise/outage conditions, not a controlled attack matrix) | ⚪ | ⚪ |
| H5a — complementarity (risk signal adds to confidence) | ✅ | 🟡 | ⚪ (no confidence/calibration signal exists in AgentRx transcripts) | ⚪ |
| H5b — decision-cost policy | 🟡 (no real operational cost model exists for Alibaba; any cost model would be assumed, not measured — see §21) | 🟡 (same caveat) | ⚪ | ⚪ |
| H6 — diagnosis | ⚪ (no cause-of-failure field in Alibaba trace; `status` is the outcome, not a diagnosis) | 🟡 (fault category is the injected ground truth — diagnosis task is real but injected-fault, not organic) | ✅ (organic `root_cause_failure_id` + `root_cause_reason` fields — strongest diagnosis dataset available; still small-N, see §17) | ✅ (same fields, n=29) |
| H7 — recovery | ⚪ (no recovery action recorded) | ⚪ (no recovery action recorded) | ⚪ (no recovery field) | ⚪ (no recovery field) |

**H7 (recovery) is NOT EVALUABLE on any real dataset currently held.** This is reported as a limitation
(§24), not worked around by inferring or fabricating recovery outcomes (prohibited, §21).

Where a cell is marked `⚪ NOT EVALUABLE`, no experiment is designed for it in this protocol, and none may be
added later by adapting the hypothesis to fit the data (§21).

---

## 4. Independent units (do not inflate N)

| Dataset | Independent unit | What is NOT an independent unit |
|---|---|---|
| Alibaba GPU2020 | **job** (`job_name`) | task rows (child of job), instance rows (child of task), sensor rows (child of instance), machine_metric rows — these are correlated children of a sampled job and must not be counted as separate observations. Machine-level generalization claims are bounded by **1,737 distinct machines**, not by job or row count. |
| AIOps 2020 | **fault entity** (`cmdb_id`), with fault events nested inside entities | the 226 windows are not 226 independent observations — 81 positives cluster into 16 entities (median 5 events/entity, max 10) and 145 negatives cluster into 43 entities (median 3, max 7). Any statistical test must either block/cluster on entity or explicitly report the window count as an upper bound on the effective N with entity count as the conservative lower bound. |
| AgentRx (each domain) | **trajectory** (`trajectory_id`) | steps/substeps within a trajectory are not independent units; failure records within one trajectory's `failures` list are not independent units for a per-trajectory-outcome test. |

No experiment in this protocol treats a correlated child record as an additional independent observation.
Where an analysis is entity-clustered (AIOps) or trajectory-level (AgentRx), the reported N is the unit count,
and any variance/CI estimate accounts for clustering (e.g., cluster bootstrap over entities, not over windows).

---

## 5. Effective sample sizes (frozen, pre-registered)

| Dataset | Nominal N | Effective independent N | Confirmatory-capable? |
|---|---|---|---|
| Alibaba, random-stratified split | 10,000 jobs (7,000/1,500/1,500 train/val/test) | 10,000 jobs | Yes — power analysis (§18) supports ±0.02–0.03 AUROC precision and detection of a 0.03 AUROC difference at power 0.80 |
| Alibaba, temporal split | 10,000 jobs (Q1–Q3 train/val, Q4 test) | 10,000 jobs, but Q4 test carries a confirmed base-rate shift (§9) | Yes for descriptive/shift reporting; treat point estimates on the shifted test set with caution |
| AIOps | 226 windows | 43 entities (16 positive-bearing, 27 negative-only) | No — exploratory only (±0.064–0.079 AUROC CI half-width at assumed AUROC 0.55–0.80, n=226; entity-level N is smaller still) |
| AgentRx Magentic | 44 trajectories | 44 trajectories | No — exploratory only, wide CIs expected |
| AgentRx τ-Retail | 29 trajectories | 29 trajectories | No — exploratory only, wide CIs expected |

---

## 6. Alibaba sampling protocol (already frozen upstream — reused verbatim)

This protocol does not re-sample. It reuses the sample already frozen in
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §14 and `data/audit/alibaba_gpu2020/`:

- **Sampling unit**: job (`job_name`).
- **Population**: 988,910 eligible terminal jobs (status ∈ {Terminated, Failed}; Running/Waiting excluded as
  right-censored, not imputed).
- **Strata**: `outcome_status × dominant_gpu_type × relative_time_quartile`.
- **Allocation**: proportional to each stratum's population share.
- **Selection**: deterministic, `seed=42`, lexicographic sort of `job_name` then `random.Random.sample`.
- **Tiers**: pilot (2,000), **main (10,000, used for this protocol)**, robustness (50,000, not used here —
  reserved for a future robustness check, not part of Phase 3.1-RD).
- **Verification already performed**: sampled Failed-rate for the main tier is 25.94%, matching the population
  rate of 25.94% to four significant figures.
- **This protocol will not draw a new sample, change the seed, or change the tier.** If the main tier proves
  insufficient for some sub-analysis discovered during execution, that is reported as a limitation; the
  robustness tier is not silently substituted mid-protocol.

---

## 7. Alibaba feature eligibility / leakage exclusions (frozen upstream — reused verbatim)

Per `docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`, the following are **excluded from every
decision-time predictive feature set** in this protocol, for every Alibaba experiment under every hypothesis:

- `pai_sensor_table` in its entirety — official documentation confirms these are per-instance-lifetime
  averages (and, for `max_mem`/`max_gpu_wrk_mem`, per-instance-lifetime maxima), i.e. computed over the full
  span of the very instance whose outcome is being predicted.
- `pai_machine_metric` in its entirety — same lifetime-average construction, machine-level.
- `max_mem`, `max_gpu_wrk_mem` specifically (redundant with the table-level exclusion above, restated because
  these two fields are the most likely to be reintroduced by accident as "just a summary statistic").

**Allowed (pre-outcome, request/scheduling-time) predictive fields:**

| Table | Allowed fields |
|---|---|
| `pai_job_table` | `user`, `start_time` (submission time only) |
| `pai_task_table` | `task_name`, `inst_num`, `plan_cpu`, `plan_mem`, `plan_gpu`, `gpu_type`, task `start_time` |
| `pai_instance_table` | `machine` (once scheduled), instance `start_time` |
| `pai_group_tag_table` | `gpu_type_spec`, `group`, `workload` (sparse) |
| `pai_machine_spec` | all fields (static machine specs — never leak, since they don't depend on job outcome) |

**Consequence, stated explicitly (per instruction and per the leakage-gate doc):** the Alibaba real-data
representation/failure-prediction experiment is necessarily based primarily on **request- and
scheduling-time information**, not runtime telemetry. This is a real constraint on what the Alibaba real-data
experiment can show about H1/H2 — it cannot be interpreted as testing the same "richer runtime representation"
question that Phase 3.2 tested on synthetic features, only the narrower "does pre-outcome
scheduling/spec information carry a supervised failure-risk signal" question. This distinction is carried into
the H1/H2 result write-up, not glossed over.

No lifetime telemetry field is reintroduced into any predictive experiment under this protocol, including
indirectly (e.g., no engineered feature is a function of an excluded field). Sensor/machine-metric tables
remain usable **only** for post-hoc descriptive/exploratory analysis, explicitly labeled as such and never fed
to a predictive model.

---

## 8. Alibaba random split (frozen upstream — reused verbatim)

- 70/15/15 train/validation/test.
- Stratified on `outcome_status × dominant_gpu_type`.
- Source: `data/audit/alibaba_gpu2020/splits_random_stratified.json`.
- Observed class balance: 25.95% / 25.97% / 25.88% Failed across train/val/test — closely matched, as
  intended by stratification.
- Test set is frozen at the point this protocol is authorized to run and is used only for final evaluation
  (§19).

---

## 9. Alibaba temporal split (frozen upstream — reused verbatim; distribution shift disclosed up front)

- Train/validation = relative-time **Q1–Q3**.
- Test = strict future holdout **Q4**.
- Source: `data/audit/alibaba_gpu2020/splits_temporal.json`.
- **Base-rate shift, discovered during data preparation, before any model evaluation, and disclosed here in
  full:**
  - Failed rate in Q1–Q3 (train/val): **≈20.1%**
  - Failed rate in Q4 (test): **≈43.4%**
- This is a genuine, already-observed distribution shift in the real data, not an artifact of sampling. It is
  treated as a **finding to report**, not a problem to correct by rebalancing, resampling, or reweighting the
  temporal test set. Any H3 (generalization) result on the Alibaba temporal split is interpreted with this
  shift explicitly stated alongside the metric, and raw AUROC/AUPRC under a 2.2x base-rate change between
  train and test is not compared directly to the random-split numbers without that caveat.
- No machine-disjoint split exists for Alibaba (job↔machine is many-to-many; not solved by this protocol) —
  documented as a limitation (§24), not silently skipped.

---

## 10. AIOps temporal/window protocol (frozen upstream — reused verbatim)

Per `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`:

- **PRE-FAILURE window**: `[fault_onset − 20min, fault_onset)` — the only region usable as predictive input.
- **DURING-FAILURE window**: `[fault_onset, fault_onset + 5min)` — usable only for diagnosis, never prediction.
- **POST-FAILURE**: everything after `fault_onset + 5min` — usable only for diagnosis, never prediction.
- Rationale for 20 minutes: global minimum gap between consecutive fault onsets is 25.0 minutes (min per-entity
  gap 30.0 minutes); a 20-minute window leaves a 5-minute safety margin against cross-event contamination for
  effectively the whole population. A 60-minute window was considered and rejected because it is
  contamination-free for only ~62% of events (51/81).
- `fault_onset(event) = start_time` if non-empty, else `log_time`.
- Telemetry inclusion/exclusion (verbatim from the frozen table): platform metrics, business metrics
  (`esb.csv`), and call-trace fields other than same-call `success`/`elapsedTime` are usable as PRE-FAILURE
  predictive features; `success`/`elapsedTime` are usable only as aggregated PRE-window features (e.g. "%
  failed calls in preceding 20 min"), never as same-call input; fault-log descriptive fields are diagnosis/label
  only; fault-log timing fields are used only to draw the T0 cutoff, never as a feature value.
- These rules are **not** revisited after seeing any evaluation result.

---

## 11. AIOps positive/negative population (frozen upstream — reused verbatim)

- **Positive windows**: 81/81 fault-log events validated (exact 20-min span, ≥1 telemetry observation, zero
  observations at/after onset, no cross-event overlap for the same entity). Source:
  `scripts/real_data/aiops_validate_positive_windows.py`.
- **Negative windows**: 145 valid, drawn from a frozen candidate pool of 860 (43 eligible entities × 20
  candidates/entity, `seed=42`), rejected only for lack of telemetry coverage (715/715 rejections were
  `has_telemetry_coverage=False`; zero rejections were due to the fault-exclusion/overlap logic failing).
  Exclusion window around each entity's own fault onset: `[w_start − 60min, w_start + 20min + 60min]`.
  Negative-eligible entities are the same 43 fault-eligible entities as the positive pool (8 docker_*, 13
  db_*, 22 os_*); `csf_*`/`redis_*`/`osb_*` are excluded as never fault-injection targets.
- **Total**: 226 windows (81 positive + 145 negative).
- This population is not re-sampled, re-balanced, or filtered further by this protocol.

---

## 12. AIOps entity-level dependence (must be reported alongside every AIOps result)

- 43 total entities in the final positive/negative window population.
- 16 entities have at least one positive (fault) window; 27 entities appear only in the negative pool.
- Positive events per entity: min 1, median 5, max 10.
- Negative windows per entity: min 2, median 3, max 7.
- Every AIOps statistical result in Phase 3.1-RD reports **both** the window count (226) and the entity count
  (43, with the 16/27 positive/negative-only split), and any variance estimate accounts for entity clustering.
  A result that only reports "n=226" without the entity breakdown is not a valid Phase 3.1-RD deliverable.
- **AIOps is classified EXPLORATORY for every hypothesis in §3.** No AIOps result is described as confirmatory,
  regardless of p-value or point estimate.
- Two known, unresolved timestamp irregularities remain documented and are **not silently fixed**:
  1. `block=8` spans two calendar dates (2020-05-29 and 2020-05-30) with no operational explanation found.
  2. An unexplained **+6-hour** shift between `log_time` and `start_time` for `log_block ∈ {4,5}` (11 of 70
     index≥100 rows).
  Neither irregularity is corrected, imputed around, or excluded without being reported as a limitation (§24).

---

## 13. AgentRx domain separation

- **Magentic-One**: 44 annotated trajectories.
- **τ-Retail**: 29 annotated trajectories.
- These are evaluated as **two separate small-sample datasets**, never pooled to reach a combined N=73. Any
  aggregate statement about "AgentRx" as a whole reports both numbers separately; it never reports a single
  merged AUROC/accuracy figure across domains.
- Explicit constraints carried into every AgentRx analysis:
  - No timestamps exist anywhere in either dataset (only ordinal step/substep indices) — H3 (drift) and any
    wall-clock temporal analysis are **NOT EVALUABLE** on AgentRx.
  - Origin is a benchmark-harness evaluation environment: genuine LLM-agent executions against real tools, but
    not organic production traffic and not a controlled fault-injection design either. Results are never
    described as "production evidence."
  - `failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`, `root_cause_reason` are all
    post-hoc fields, available only after the trajectory concluded — never used as decision-time predictive
    input, only as diagnosis-task labels/targets.
  - n=44 and n=29 are both far below any conventional threshold for a stable AUROC/AUPRC estimate. Every
    AgentRx result is reported with a confidence interval, and no AgentRx point estimate is treated as
    decisive on its own.

---

## 14. Statistical tests

| Context | Test / estimator |
|---|---|
| AUROC/AUPRC point estimate, any dataset | Empirical estimator on the frozen test split |
| Alibaba random split (confirmatory-capable) | Cross-seed Student-t interval is not applicable (single real split, not multi-seed synthetic regeneration) — instead: nonparametric bootstrap over jobs (test-set rows), matching the within-seed bootstrap method already used in the original Phase 3 (`n_resamples=2000`, `seed=0`, 95% percentile CI) |
| Alibaba random vs temporal split comparison | Report both metrics side by side with CIs; do not compute a single paired difference test across splits with different base rates — report the base-rate shift (§9) as the primary explanatory factor before any performance delta is interpreted |
| AIOps (any hypothesis) | Cluster bootstrap over the 43 entities (resample entities with replacement, not windows), 2000 resamples, seed 0, 95% percentile CI — window-level bootstrap is not used as the primary estimator because it treats correlated within-entity windows as independent |
| AgentRx (either domain) | Nonparametric bootstrap over trajectories, 2000 resamples, seed 0, 95% percentile CI; given n=29–44, CIs are expected to be wide and are reported as-is, not narrowed by any post-hoc adjustment |
| Any cross-dataset comparison (e.g. AIOps vs Alibaba on H3) | Qualitative consistency check only (same-direction / different-direction, overlapping / non-overlapping CIs) — never a single pooled statistical test across datasets with different units, domains, and sample sizes |

P-values, where computed at all, are reported alongside effect sizes and confidence intervals, never alone.

---

## 15. Effect-size reporting

Every quantitative result reports, at minimum:
- Point estimate (AUROC, AUPRC, accuracy, or the task-appropriate metric) with its 95% CI.
- A paired or unpaired effect-size measure against the relevant baseline (e.g., ΔAUROC vs. no-signal baseline,
  vs. calibrated-confidence baseline, matching the baseline structure used in the original Phase 3 where an
  analogous baseline exists on the real dataset).
- The independent-unit N used for the CI (job count, entity count, or trajectory count — never raw row count).
- Where a baseline used in the original Phase 3 (no-signal, calibrated confidence) has a real-data analogue,
  it is computed and reported alongside the candidate signal, exactly as Phase 3.1/3.4 did on synthetic data —
  so real-data H1/H5a results are directly comparable in structure (not necessarily magnitude) to the original.

---

## 16. Confidence-interval methodology

- **Bootstrap CIs**: nonparametric percentile bootstrap, `n_resamples=2000`, `seed=0`, 95% confidence level —
  identical methodology to the original Phase 3 (`configs/phase3_1_protocol.json`), applied at the
  independent-unit level appropriate to each dataset (job for Alibaba, entity for AIOps, trajectory for
  AgentRx).
- No cross-seed Student-t interval is used for real data, because real data is not regenerated across
  synthetic seeds; there is exactly one real sample per split. Where multiple random splits or resampling
  schemes are legitimately available (e.g., repeated stratified resampling of the Alibaba main tier for a
  robustness check), that is treated as a distinct, explicitly labeled sub-analysis, not substituted silently
  for the frozen primary split.

---

## 17. Power / feasibility limitations (frozen upstream — reused verbatim, restated here for the record)

| Dataset | Power analysis result | Conclusion |
|---|---|---|
| Alibaba main tier (n=10,000) | Hanley-McNeil approximation at observed 25.94% base rate: n≈3,500–4,300 for ±0.02 AUROC precision; n≈7,700–8,100 for 80% power to detect a 0.03 AUROC difference at α=0.05 | Main tier exceeds both thresholds — confirmatory-capable |
| AIOps (n=226 windows) | 95% CI half-width at n=226 ranges ±0.064 (AUROC≈0.80) to ±0.079 (AUROC≈0.55) | Explicitly exploratory, not confirmatory, for every hypothesis |
| AIOps fault-category classification (5 classes) | Per-class n ranges 5–31 | Underpowered / inconclusive-prone by design; any per-class metric reported with this caveat attached |
| AIOps entity-level generalization | 16 entities with positives, 15 with ≥2 events | Underpowered for a leave-entities-out generalization claim; any such analysis is reported as a directional/qualitative observation only |
| AgentRx (n=44, n=29) | No stable-AUROC threshold met at either sample size | Exploratory only; wide CIs expected and reported as such, never treated as decisive |

The power analysis was performed **before** sampling (Alibaba) and before window extraction (AIOps), per
`docs/PHASE3_REAL_DATA_CLEANING_REPORT.md` §15 and `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md` §6.
No tier or window count is chosen or changed after seeing any evaluation result under this protocol.

---

## 18. Confirmatory vs. exploratory status (explicit, per dataset)

| Dataset | Status | Basis |
|---|---|---|
| Alibaba, random-stratified split, request/scheduling-time features | **Confirmatory-capable** | Power analysis (§17) supports the target precision; leakage gate (§7) ensures features are genuinely pre-outcome |
| Alibaba, temporal split | **Confirmatory-capable for the metric itself; interpretation constrained** by the disclosed base-rate shift (§9) | Same power basis, but cross-split comparison is not a clean apples-to-apples confirmatory test given the shift |
| AIOps (all hypotheses) | **Exploratory** | §17 — CI half-widths of 0.06–0.08 at n=226 windows / entity-clustered N as low as 16 |
| AgentRx, Magentic and τ-Retail (all hypotheses) | **Exploratory** | §17 — n=44 and n=29, no stable-estimate threshold met |

No exploratory-status result is later relabeled confirmatory based on how the numbers turn out.

---

## 19. Train/validation/test rules

- **Alibaba random split**: train (70%) used for model fitting; validation (15%) used for any legitimate
  model-selection/hyperparameter decision (e.g., regularization strength for a supervised risk model, mirroring
  the frozen-candidate-F structure from the original Phase 3); test (15%) is touched exactly once, for final
  evaluation, after all modeling decisions are frozen.
- **Alibaba temporal split**: Q1–Q3 (train+validation, further split internally if a validation set is needed)
  used for fitting/selection; Q4 test is touched exactly once, for final evaluation.
- **AIOps**: given the small entity-clustered N, no separate validation split is carved out of the 226-window
  population for AIOps; any model-selection decision needed for an AIOps experiment is made using the
  Alibaba validation set's selected configuration where the same model family applies, or is fixed a priori
  from the original Phase 3's frozen candidate definitions (`src/evaluation/representations.py`) — not tuned
  on AIOps data itself. This constraint is stated explicitly in any AIOps sub-report.
- **AgentRx**: same rule as AIOps — no held-out validation carved from 44 or 29 trajectories; any modeling
  choice reuses a configuration fixed elsewhere, never tuned on AgentRx test data.
- **Test sets, once designated, are frozen for the remainder of Phase 3.1-RD.** They are read exactly once
  per experiment, for final evaluation. No metric computed on a test set is used to revise sampling,
  preprocessing, features, representation, hyperparameters, thresholds, model selection, extraction windows,
  or negative-window selection (see §21 for the full prohibited-actions list).

---

## 20. Leakage prevention

- Alibaba: §7's exclusion list (`pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem`) is
  enforced for every predictive experiment, including any derived/engineered feature that is a function of an
  excluded field.
- AIOps: §10's PRE/DURING/POST partition is enforced for every predictive experiment; fault-log descriptive
  and timing fields are never predictive features.
- AgentRx: post-hoc annotation fields (`failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`,
  `root_cause_reason`) are never predictive input for any prediction-task experiment; they are the label/target
  for diagnosis-task experiments only (H6), which is the one task class where AgentRx is evaluable (§3).
- Entity leakage (AIOps) and machine leakage (Alibaba, where feasible): no entity/machine that contributes to
  a test window/job may also contribute a window/job used for fitting or model selection on the same
  experiment, wherever the split design makes this checkable. Where it is not fully checkable (Alibaba's
  job↔machine many-to-many relationship, §9), this is documented as a limitation, not silently ignored.
- Temporal leakage: for the Alibaba temporal split and for any AIOps analysis that uses absolute calendar time,
  no feature computed using information from after the prediction cutoff (`T0` for AIOps, job `start_time` for
  Alibaset scheduling-time features) enters training or evaluation for that unit.

---

## 21. Research integrity — explicit prohibited actions

The following are prohibited for the duration of Phase 3.1-RD, without exception:

- Tuning on the test set, in any dataset.
- Selecting or dropping a dataset after seeing its evaluation result.
- Removing difficult test cases.
- Rebalancing a test set after evaluation (including the Alibaba Q4 base-rate shift, §9 — reported as-is).
- Changing sampling seeds after evaluation.
- Altering AIOps window definitions after evaluation.
- Selecting a representation or candidate model based on test-set performance.
- Cherry-picking datasets or metrics for the write-up.
- Fabricating labels.
- Inferring unavailable recovery outcomes for H7 (AgentRx, AIOps, Alibaba all lack a recovery field — H7 is
  reported NOT EVALUABLE, not approximated).
- Treating missing information as negative evidence (e.g., an AIOps entity never appearing in the fault log is
  not treated as evidence that entity cannot fail — it is an open question, per §24).
- Inflating sample size by treating correlated child rows/windows as independent observations (§4).
- Hiding inconclusive or negative findings.
- Modifying any original (synthetic) Phase 3 frozen result, config, script, or report.

If a hypothesis is inconclusive after evaluation, the protocol requires it to be **reported as inconclusive**,
using the same INCONCLUSIVE label the original Phase 3 already used for its own H1/H5/H7-equivalent findings
(Phase 3.2, 3.4, 3.6) — inconclusive is a legitimate, expected outcome class in this research program, not a
failure of the protocol.

---

## 22. Reproducibility requirements

- Every script under `scripts/real_data/` used to build a Phase 3.1-RD input is deterministic, with
  `seed=42` wherever randomness is involved, matching the seed already used for sampling and negative-window
  construction upstream.
- Every Phase 3.1-RD result artifact records: protocol version (this document's version, §above), full
  resolved config (this document's companion `configs/phase3_real_data_protocol.json`), dataset source file(s)
  and their provenance (source dataset name, source file path/day, extraction script and version), split
  membership, seed(s) used, and a UTC timestamp — mirroring the `meta` block convention already used by
  `benchmarks/phase3_1_evaluate.py`.
- No raw file under `data/raw/` is modified by any Phase 3.1-RD script. All derived artifacts are written under
  `data/processed/`, `data/audit/`, or the new `experiments/results/phase3_real_data/` tree.

---

## 23. Comparison with original Phase 3

A comparison structure — not a rewrite — is produced once real-data evaluation actually runs. It is designed
now so the comparison is specified before any result exists:

For every hypothesis (H1–H7), the eventual comparison report records:

| Field | Content |
|---|---|
| Hypothesis | H1–H7, as defined in §1 |
| Original Phase 3 result | Verbatim from the frozen synthetic-data reports (`docs/PHASE3_1_EVALUATION_PROTOCOL.md` … `PHASE3_6_...md`) — not restated with new interpretation |
| Real-data result(s) | Per dataset, per §3's mapping; `NOT EVALUABLE` where applicable |
| Direction of agreement/disagreement | Supports / contradicts / partially supports / cannot adjudicate |
| Confidence/uncertainty | CI width and independent-unit N carried through from §14–17 |
| Dataset limitations | Restated from §17/§24 relevant to that hypothesis/dataset pairing |
| Interpretation | Whether the real-data result strengthens, weakens, contradicts, or cannot adjudicate the original finding — **disagreement is not automatically treated as evidence the original result was wrong**; both results are reported and the reasons a real-data result might diverge (different feature availability, different domain, different N, different leakage constraints) are stated alongside any interpretation |

This comparison structure is stored as its own document (e.g. `docs/PHASE3_REAL_DATA_COMPARISON.md`) when
produced — it does not overwrite `docs/PHASE3_4_COMPARISON.md` or any other original Phase 3 file.

---

## 24. Known limitations (carried forward, not resolved by this protocol)

- Alibaba: no machine-disjoint split exists (job↔machine many-to-many). Alibaba real-data H1/H2 experiments
  are necessarily scheduling/request-time-feature-only, not runtime-telemetry-based, per §7. Temporal split
  carries a confirmed ~2.2x base-rate shift (§9), which confounds any raw performance-delta interpretation
  between random and temporal splits.
- AIOps: `block=8` two-date irregularity and the +6-hour `log_time`/`start_time` shift for `log_block∈{4,5}`
  remain unexplained (§12). Whether fault-log index 1–11 were part of the scored evaluation or an unscored
  preview batch is uncertain. 27 of 43 fault-eligible entities never appear in the fault log — genuinely
  fault-free, or excluded for an unrelated reason, is an open question, and is not resolved by assumption.
  AIOps fault categories are injected (via the CCF challenge design), not organic — diagnosis results on AIOps
  are not claimed to generalize to organic fault taxonomies.
- AgentRx: benchmark-harness origin means results are not organic production evidence (§13). No timestamps
  exist, so H3/H4 are not evaluable. n=44/n=29 mean every AgentRx result carries wide, sometimes uninformative
  confidence intervals — a null or inconclusive AgentRx result is not strong evidence against a hypothesis; it
  may simply reflect insufficient power, and is reported with that caveat.
- No dataset supports H7 (recovery). This is a structural gap in the currently held real data, not a design
  choice of this protocol.
- No unified cross-dataset schema is imposed (§25) — this preserves each dataset's real structure but means no
  single combined statistical claim can be made across all three data sources; only qualitative
  consistency-checking is possible (§14).

---

## 25. Future unified benchmark/dataset implications

This protocol intentionally does not force Alibaba, AIOps, and AgentRx into a common schema — each dataset's
native structure, units, and limitations are preserved as-is (per the design intent already stated in
`docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md` §10 for AIOps). For a future unified benchmark to be buildable from
this work, every Phase 3.1-RD extraction/processing artifact preserves, where the field genuinely exists in
the source data (never fabricated where it doesn't):

- `source_dataset` (e.g. `"Alibaba_GPU2020"`, `"AIOps_2020"`, `"AgentRx_Magentic"`, `"AgentRx_TauRetail"`)
- `source_record_id` / `source_event_id` (native ID: `job_name`, fault-log `index`, `trajectory_id`)
- `entity_id` (native: `machine`/`cmdb_id`/N/A for AgentRx — no forced remapping between datasets' conventions)
- `workload_id` (native: `task_name`/`domain` where applicable)
- `timestamp` (native format preserved alongside any converted UTC value; explicit `MISSING` marker, never
  imputed, where a dataset has none — e.g. AgentRx)
- `label_provenance` (how the label was derived: observed terminal status, injected fault, organic annotation)
- `processing_version` (script + version that produced the derived record)
- `split_membership` (random/temporal, train/val/test, as applicable)
- `data_quality_flags` (e.g. AIOps's `has_telemetry_coverage`, Alibaba's `_source_row_index` provenance
  column, the leakage-status flag for excluded fields)

No field is forced onto a dataset that does not naturally have it; a future benchmark record for AgentRx, for
example, carries an explicit missing-timestamp flag rather than a synthesized timestamp.

---

## 26. Stopping/decision rules — DO NOT RUN PHASE 3.1-RD YET

This document is a **protocol design and freeze deliverable only**. Per explicit instruction:

- No model training, evaluation, or representation comparison is performed under this document.
- Phase 3.1-RD (and any subsequent 3.2-RD…3.6-RD or Phase 4 real-data work) requires **separate, explicit
  authorization** before execution begins.
- Once authorized, execution follows this document and its companion config
  (`configs/phase3_real_data_protocol.json`) exactly; any deviation discovered to be necessary during
  execution is documented as an amendment with a rationale and timestamp, not applied silently.

---

## Appendix: file inventory referenced by this protocol

**Authoritative real-data sources (read, not modified):**
- `docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md`
- `docs/PHASE3_REAL_DATA_CLEANING_REPORT.md`
- `docs/PHASE3_REAL_DATA_AIOPS_PREPARATION_COMPLETE.md`
- `docs/PHASE3_REAL_DATA_AIOPS_PROTOCOL.md`
- `docs/PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`
- `docs/PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md`

**Original (synthetic) Phase 3 — frozen, read-only:**
- `docs/PHASE3_1_EVALUATION_PROTOCOL.md`, `PHASE3_2_REPRESENTATION_EXPERIMENTS.md`,
  `PHASE3_2C_CANDIDATE_ABLATION.md`, `PHASE3_3_GENERALIZATION.md`, `PHASE3_4_COMPARISON.md`,
  `PHASE3_5_ATTACK_GENERALIZATION.md`, `PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`, `PHASE3_FREEZE.md`
- `configs/phase3_1_protocol.json`, `phase3_5_attack_protocol.json`, `phase3_6_decision_recovery_protocol.json`
- `experiments/results/phase3_1/` … `phase3_6/` (all frozen, unmodified)

**Data (read-only for this protocol):**
- `data/raw/{alibaba_gpu2020,aiops_kpi,agentrx}/`
- `data/processed/{alibaba_gpu2020,aiops_kpi,agentrx}/`
- `data/audit/alibaba_gpu2020/{sampling_frame,sampling_report,splits_random_stratified,splits_temporal,splits_report}.json`

**New deliverables of this task:**
- `docs/PHASE3_REAL_DATA_PROTOCOL.md` (this document)
- `configs/phase3_real_data_protocol.json`


---

<a id="phase3-real-data-3-1-report"></a>
# PHASE3 REAL DATA 3 1 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_1_REPORT.md`  
**Role:** Real-data Phase 3.1 (detection) report.

# Phase 3.1-RD — Real-Data Baseline/Signal Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.1-RD
execution only (Phase 3.2-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Protocol version

`1.0`, matching `docs/PHASE3_REAL_DATA_PROTOCOL.md` and `configs/phase3_real_data_protocol.json`
(both frozen 2026-08-13, unmodified during this execution).

## 2. Execution date

2026-08-13.

## 3. Environment information

- Python 3.11.3
- numpy 2.4.6, pandas 3.0.5, scikit-learn 1.9.0, scipy 1.17.1
- Platform: Windows (win32), working directory `C:\Autonomous AI infrastructure`
- No GPU/accelerator used (CPU-only `LogisticRegression`, `sklearn.linear_model`)

## 4. Dataset versions/identifiers

| Dataset | Source | Files read |
|---|---|---|
| Alibaba GPU2020 | `data/processed/alibaba_gpu2020/{job_table.clean,task_table.main_sample,instance_table.main_sample}.csv`; splits from `data/audit/alibaba_gpu2020/{splits_random_stratified,splits_temporal}.json`; sample IDs from `data/audit/alibaba_gpu2020/sample_job_ids_main.txt` | main tier, 10,000 jobs |
| AIOps 2020 | `data/processed/aiops_kpi/platform/*.csv`; window manifests `data/audit/aiops_kpi/{positive_window_validation,negative_window_validation}.json` | 226 windows (81 positive, 145 negative) |
| AgentRx | `data/processed/agentrx/{magentic_joined,tau_retail_joined}.jsonl` | 44 (Magentic) + 29 (τ-Retail) annotated trajectories |

No file under `data/raw/` was opened or modified by any Phase 3.1-RD script — only `data/processed/` and
`data/audit/` artifacts were read.

## 5. Integrity checks (pre-execution, per §26 of the protocol)

| Check | Result |
|---|---|
| Execution gate authorized | `configs/phase3_real_data_protocol.json`'s static `execution_gate.authorized_to_run` field reads `false` — this field was never edited (editing the frozen config would itself be a prohibited protocol modification). Authorization for Phase 3.1-RD was instead granted explicitly via chat on 2026-08-13, which is the valid instruction channel the protocol's §26 anticipates ("requires separate, explicit authorization"). This is recorded here as the authorization-of-record; the static file field is left as-is. |
| Protocol version = 1.0 | Confirmed in both `docs/PHASE3_REAL_DATA_PROTOCOL.md` header and `configs/phase3_real_data_protocol.json.protocol_version` |
| Referenced datasets/splits/configs exist | All referenced files (§4 above) confirmed present before use; scripts fail fast (`FileNotFoundError`/`assert`) if a referenced file were missing — none were |
| Raw files unchanged | Not opened by any Phase 3.1-RD script this session; no write operation targeted `data/raw/` |
| Original Phase 3 frozen files untouched | No `docs/PHASE3_1_EVALUATION_PROTOCOL.md`…`PHASE3_6_...md`, no `configs/phase3_{1,5,6}_*.json`, no `experiments/results/phase3_1/`…`phase3_6/` file was opened for writing this session |
| Phase 4 untouched | No `docs/PHASE4_*`, `configs/phase4_*`, or `experiments/results/phase4_*` file was opened for writing this session |
| Execution environment matches frozen protocol | seed=42 (sampling/negative-window reuse), bootstrap seed=0/n=2000/95% CI as specified in `configs/phase3_real_data_protocol.json.statistics` — confirmed applied (§9, §17 below) |

No integrity check failed. Execution proceeded.

## 6. Exact sample sizes

| Dataset | N | Breakdown |
|---|---|---|
| Alibaba, random split | 10,000 jobs | train 6,999 / val 1,498 / test 1,503 |
| Alibaba, temporal split | 10,000 jobs | train 6,177 / val 1,324 / test 2,499 |
| AIOps | 226 windows | 81 positive / 145 negative; 0 dropped for missing telemetry |
| AgentRx Magentic | 44 annotated trajectories (of 58 total in source file) | — |
| AgentRx τ-Retail | 29 annotated trajectories (of 29 total in source file) | — |

## 7. Independent units

- Alibaba: **job** (bootstrap resamples test-set job rows).
- AIOps: **entity** (`cmdb_id`) — cluster bootstrap resamples the 43 entities, not the 226 windows; cross-validation is leave-one-entity-out (see §16).
- AgentRx: **trajectory**, per domain (Magentic and τ-Retail kept separate).

No correlated child row (Alibaba task/instance rows, AIOps within-entity windows) was counted as an
independent observation in any statistical estimator.

## 8. Feature set used

**Alibaba** (pre-outcome, request/scheduling-time only): `job_start_time`, `n_tasks`,
`n_distinct_task_names`, `sum_inst_num`, `mean_plan_cpu`, `max_plan_cpu`, `mean_plan_mem`, `max_plan_mem`,
`mean_plan_gpu`, `max_plan_gpu`, `n_distinct_gpu_types`, `dominant_gpu_type` (one-hot), `n_instances`,
`n_distinct_machines`, `mean_instance_start_time`.

**Feature-availability limitation, discovered during implementation**: the protocol's allowed-field list
(§7 of `docs/PHASE3_REAL_DATA_PROTOCOL.md`) includes `pai_group_tag_table` (`gpu_type_spec`, `group`,
`workload`) and `pai_machine_spec` (all fields). Neither table was ever materialized in processed/sampled
form during the earlier extraction work — only raw `.tar.gz` archives exist for them
(`data/raw/alibaba_gpu2020/pai_group_tag_table.tar.gz`, `pai_machine_spec.tar.gz`). This evaluation does
**not** extract them (doing so would require new extraction/decompression code, a change to the data
pipeline beyond a minimal baseline evaluation). Their absence narrows feature completeness; it does not
violate the leakage ceiling, since omitting an allowed field is always leakage-safe. `job_table.user` was
also deliberately excluded — it is allowed by the protocol but is a very high-cardinality identifier that
would require its own leakage-safe target-encoding design (fit on train only) to use responsibly; that is
out of scope for a minimal Phase 3.1-RD baseline and was not built.

**AIOps** (PRE-FAILURE window only, platform telemetry): `n_observations`, `n_distinct_metrics`, `mean_value`,
`std_value`, `min_value`, `max_value` (aggregated over all platform metric readings within
`[fault_onset−20min, fault_onset)` or the equivalent negative-window bounds), plus `object` (docker/db/os)
as a categorical feature. Source families: `dcos_docker.csv`, `dcos_container.csv` (docker entities),
`db_oracle_11g.csv` (db entities), `os_linux.csv` (os entities).

**Feature-availability limitation**: business telemetry (`esb.csv`) and call-trace windows were **not**
included in this minimal baseline. They are allowed by the protocol but are not cleanly attributable to a
single fault entity without additional join logic (service-name-to-entity mapping) that was not built here.
Documented, not a leakage issue.

**AgentRx**: no predictive feature set was built — see §16 (H1 not executable).

## 9. Leakage exclusions (enforced, verified)

- `pai_sensor_table`, `pai_machine_metric` — not read by the Alibaba script at all (not in any `usecols=`
  list, not merged).
- `max_mem`, `max_gpu_wrk_mem` — not read (these live only in `sensor_table.main_sample.csv`, which is never
  opened by `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`).
- An `assert_no_excluded_columns` check runs against the final Alibaba feature frame before model fitting,
  as a defense-in-depth check (redundant with the above, since the excluded fields are never loaded, but
  verifies no column named `max_mem`/`max_gpu_wrk_mem` slipped in through any future edit).
- AIOps: only the PRE-FAILURE window `[fault_onset−20min, fault_onset)` (or the equivalent frozen negative
  window bounds) is queried for telemetry; DURING/POST-window data and fault-log descriptive/timing fields
  are never read as features.
- AgentRx: `failure_summary`, `failures`, `num_failures`, `root_cause_failure_id`, `root_cause_reason` were
  read only for descriptive reporting (§16), never as predictive input — moot in any case, since no
  predictive model was built for AgentRx.
- **No excluded-field usage was encountered or attempted during execution.**

## 10. Alibaba random-split results

| | Baseline A (no-signal) | Candidate F (supervised risk) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.735** [0.703, 0.766] |
| AUPRC | 0.259 [0.237, 0.281] | **0.540** [0.487, 0.596] |

train n=6,999 (25.95% Failed), test n=1,503 (25.88% Failed). Bootstrap: 2,000 resamples, seed 0, job-level,
95% CI.

## 11. Alibaba temporal-split results

| | Baseline A (no-signal) | Candidate F (supervised risk) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.793** [0.774, 0.812] |
| AUPRC | 0.434 [0.415, 0.454] | **0.636** [0.608, 0.667] |

train/val n=6,177 (Q1–Q3, 20.11% Failed), test n=2,499 (Q4, **43.42% Failed** — the disclosed base-rate
shift, reproduced here to 3 significant figures against the frozen `splits_report.json` values of
20.1%/43.4%). Bootstrap: 2,000 resamples, seed 0, job-level, 95% CI.

**Diagnostic check (not a new experiment — inspection of the already-fitted model's standardized
coefficients)**: because the Q4 test set differs from train partly *by definition* of being later in time,
a natural concern is that the model's apparent temporal-split lift is just memorizing "later `start_time` ⇒
higher risk" rather than learning anything about workload characteristics. The fitted logistic regression's
standardized coefficients do not support that concern: `job_start_time` (coefficient ≈ −0.022) and
`mean_instance_start_time` (≈ +0.032) are both near-zero, far below the dominant coefficients
(`sum_inst_num` ≈ −1.61, `n_instances` ≈ +1.61, `dominant_gpu_type` categories ≈ 0.5–0.6,
`max_plan_mem`/`max_plan_cpu` ≈ 0.4–0.5). The model's signal is driven by workload shape and resource-request
features, not by trivially encoding submission time. This is reported as a transparency check, not as
proof the model captures a deep causal mechanism.

## 12. AIOps exploratory results

Method: leave-one-entity-out (LOEO) cross-validation over the 43 entities (no hyperparameter tuning), then
entity-level cluster bootstrap (2,000 resamples, seed 0, 95% CI) on the pooled out-of-sample predictions.

| | Baseline A (no-signal, global prevalence) | Candidate F (supervised risk, LOEO) |
|---|---|---|
| AUROC | 0.500 [0.500, 0.500] | **0.646** [0.536, 0.760] |
| AUPRC | 0.353 [0.254, 0.438] | **0.575** [0.447, 0.666] |

226 windows (81 positive, 145 negative), 43 entities (16 positive-bearing, 27 negative-only), 0 windows
dropped for missing telemetry. **This result is EXPLORATORY, not confirmatory**, per protocol §12/§17/§18 —
the CI is wide (width 0.224 on AUROC) and reflects the small entity-clustered N, not high-precision
evidence.

**Implementation correction made during execution (documented per protocol §21's transparency requirement,
made before inspecting the candidate result)**: the first version of Baseline A used, for each held-out
entity's fold, the training-fold's own prevalence (i.e., the pool's prevalence with that entity excluded) as
the "no-signal" score. This produced AUROC 0.171 — far from the 0.5 a true no-signal baseline should
produce by construction. Diagnosis: entities vary sharply in how many positive windows they contribute
(median 5, max 10 per positive-bearing entity), so excluding a heavily-positive entity measurably lowers the
remaining pool's prevalence, which spuriously *anti-correlates* that per-fold constant with the excluded
entity's true label. This is an artifact of the per-fold-varying-constant design, not a property of the
data. It was corrected to a single fixed constant (the overall 226-window pool prevalence, 35.8%, applied
identically to every window regardless of fold) — matching Alibaba's Baseline A design (a fixed pre-computed
constant) — which produces AUROC exactly 0.500 as expected. **This correction changed only the reference
baseline's computation; the candidate model's LOEO predictions and resulting AUROC (0.646) were not
recomputed or altered by this fix.**

## 13. AgentRx Magentic results

**H1 (binary failure-risk signal) is NOT EXECUTABLE within the frozen 44-trajectory sample.** See §16.

Descriptive statistics only (44 annotated trajectories, of 58 total in the source file):
- `num_failures`: min 1, max 55, mean 6.70 — **zero trajectories have `num_failures = 0`**.
- `num_steps`: min 5, max 130, mean 50.0.
- `failure_categories` (multi-label, counts across 44 trajectories): Instruction/Plan Adherence Failure 25,
  Guardrails Triggered 23, Misinterpretation of Tool Output 17, Intent Plan Misalignment 7, Intent not
  supported 5, Invention of new information 5, Invalid Invocation 1, System Failure 1.

## 14. AgentRx τ-Retail results

**H1 is NOT EXECUTABLE**, same reason. Descriptive statistics only (29 annotated trajectories, all 29
trajectories in the source file are annotated):
- `num_failures`: min 1, max 4, mean 1.34 — again, zero trajectories with `num_failures = 0`.
- `num_steps`: min 20, max 62, mean 36.7.
- `failure_categories`: Underspecified User Intent 10, Intent Plan Misalignment 8, Misinterpretation of Tool
  Output 7, Instruction Adherence Failure 6, Invalid Invocation 2, Intent Not Supported 2, System Failure 1.

## 15. Baseline results

Summarized in §10–12 above (Baseline A, no-signal, per dataset/split). No calibrated-confidence baseline
(the original Phase 3's "Baseline B") was computed for any real dataset: none of the three real-data sources
has a pre-existing upstream classifier whose confidence output could be measured — this baseline has no
real-data analogue and was not fabricated. This was anticipated by protocol §15 ("Where a baseline… has a
real-data analogue, it is computed… ") and is reported here as a structural absence, not an omission.

## 16. Proposed/evaluated method results

"Candidate F" (supervised-risk analogue): a single `LogisticRegression` (scikit-learn defaults, no
hyperparameter search, `max_iter=2000`, `random_state=42`) fit on standardized numeric features plus
one-hot categoricals, using only the allowed/available pre-outcome feature set per dataset (§8). This
mirrors the original Phase 3's finding that supervised learning — not representation richness — is the
operative mechanism (Phase 3.2C), by using the simplest possible supervised model rather than any
hand-engineered representation. No second candidate, no representation ablation, and no ensemble was run —
that scope belongs to Phase 3.2-RD onward, not authorized in this execution.

**AgentRx H1, not executable — full explanation**: within the frozen sample (44 Magentic, 29 τ-Retail
annotated trajectories), every single trajectory has `num_failures ≥ 1`. There is no trajectory with zero
recorded failures in either frozen sample. A binary "will this trajectory fail" classifier requires both a
positive and a negative class; none exists here. The `has_failure_annotation` field distinguishes annotated
(44/58 Magentic, 29/29 τ-Retail) from non-annotated trajectories, but building a binary label from
"annotated vs. not annotated" would mean **adding the 14 non-annotated Magentic trajectories to the sample**,
which is explicitly prohibited by this authorization ("Do NOT… add/remove records… change the splits").
This was discovered during implementation and is reported here, per the instruction to stop and document
rather than improvise a workaround, as a genuine data-composition finding: **the currently held, frozen
AgentRx sample does not support a binary failure-occurrence prediction task.** A severity-regression
reframing (predicting `num_failures` as a count, or `failure_categories` as a multi-label target) might be
viable, but that is a different task definition than H1's "does a supervised failure-risk signal exist"
framing and was not specified by the frozen protocol — introducing it would be a protocol design decision,
which is outside Phase 3.1-RD's execution authorization and is left for the user's review.

## 17. Effect sizes

| Comparison | ΔAUROC (candidate − baseline A) |
|---|---|
| Alibaba random split | +0.235 |
| Alibaba temporal split | +0.293 |
| AIOps (LOEO, exploratory) | +0.146 |

All three are directionally consistent with the original Phase 3's core finding (a supervised signal exists
above no-signal), though the *magnitude* is not directly comparable — see §24/§25 for why.

## 18. 95% confidence intervals

All reported inline in §10–12; computed via nonparametric percentile bootstrap, 2,000 resamples, seed 0,
at the correct independent-unit level (job for Alibaba, entity for AIOps) per protocol §14/§16.

## 19. Statistical results

- Alibaba random split: Candidate F AUROC 95% CI [0.703, 0.766] excludes 0.5 entirely — signal is clearly
  present at confirmatory-capable precision.
- Alibaba temporal split: Candidate F AUROC 95% CI [0.774, 0.812] excludes 0.5 entirely — signal is present,
  but interpreted alongside the base-rate shift (§11) and the temporal-generalization caveat (§24).
- AIOps: Candidate F AUROC 95% CI [0.536, 0.760] — excludes 0.5, but only barely at the lower bound, and the
  interval is wide (width 0.224). This is exploratory evidence of a signal, not confirmatory evidence.
- No p-values were computed in isolation; every quantitative claim above is paired with its CI and effect
  size (§17), per protocol §14.

## 20. Failure cases

- AIOps Baseline A initial implementation was a genuine failure case (AUROC 0.171 instead of ~0.5) — caught,
  diagnosed, and corrected before finalizing results; full account in §12.
- No Alibaba job/window/trajectory failed to process (0 dropped in Alibaba feature build; 0 AIOps windows
  dropped for missing telemetry; all 226 windows had at least one telemetry observation in their PRE window
  or equivalent negative window).

## 21. Negative findings

- No calibrated-confidence baseline exists for any real dataset (§15) — a structural gap versus the original
  Phase 3, not a result of this execution.
- AgentRx H1 could not be executed at all (§13/§14/§16) — the most significant negative finding of this
  report: two of the four real datasets authorized for Phase 3.1-RD produced no H1 result whatsoever.
- Feature completeness for both Alibaba (`pai_group_tag_table`, `pai_machine_spec` unavailable) and AIOps
  (business/trace telemetry not included) is narrower than the protocol's full allowed set (§8) — the
  reported signal is a lower bound on what a more complete feature set might show, not an upper bound.

## 22. Inconclusive findings

- AIOps's AUROC 95% CI [0.536, 0.760] is exploratory-only and, while it excludes 0.5, the lower bound is
  close enough to 0.5 that this should not be treated as strong evidence — it is consistent with either a
  genuine modest signal or a somewhat optimistic point estimate from a small, entity-clustered sample. Per
  protocol §18, this remains classified EXPLORATORY regardless of the direction of the point estimate.

## 23. Dataset-specific limitations

- **Alibaba**: feature set restricted to a subset of the allowed fields (no `group_tag`/`machine_spec`, no
  `user`) — see §8. Machine-disjoint split was never built (documented upstream, §9 of the protocol doc,
  restated here). Temporal-split base-rate shift (20.1%→43.4%) confounds any raw performance comparison
  between random and temporal splits.
- **AIOps**: exploratory only; feature set restricted to platform telemetry only (no business/trace); the
  two unresolved timestamp irregularities (`block=8` two-date split, +6h `log_time` shift) remain
  undocumented in cause and were not investigated further in this execution (out of scope — they affect the
  frozen window manifests upstream, not this evaluation's logic).
- **AgentRx**: H1 structurally not evaluable given the frozen sample's 100%-failure composition (§16); no
  timestamps exist for either domain; benchmark-harness origin (not organic production traffic).

## 24. Interpretation

The real-data evidence for **H1 ("a supervised failure-risk signal exists beyond calibrated confidence")**
is:

- **Alibaba (both splits)**: a clear, confirmatory-capable-precision signal exists (AUROC 0.735–0.793,
  CIs excluding 0.5 by a wide margin). This is a *stronger* real-data result, in raw AUROC terms, than the
  original synthetic Phase 3.1's Candidate-F-equivalent result (AUROC 0.6548 [0.6159, 0.6938]). **This
  magnitude comparison should not be over-read**: the two tasks are not the same task. The original Phase
  3.1 predicted whether an upstream classifier's own prediction would be *wrong* (a meta-level, deliberately
  hard task calibrated to produce only a modest synthetic signal), whereas this Alibaba evaluation predicts
  whether a scheduled job will *fail outright* — a direct-outcome prediction task with no analogous upstream
  classifier in the loop. A higher AUROC here is not evidence that the original Phase 3 candidate was
  under-performing; it reflects a genuinely different, and arguably easier, prediction target. The
  qualitative finding — "a supervised model beats no-signal by a wide, statistically clear margin" — agrees
  directionally with H1's original conclusion. The magnitude does not transfer and is not claimed to.
- **AIOps**: weak, exploratory-only support for H1 (AUROC 0.646, CI barely excluding 0.5). Consistent in
  direction with H1 but far from confirmatory, exactly as the power analysis anticipated (§17 of the
  protocol document).
- **AgentRx**: cannot adjudicate H1 at all — no experiment could be run.

No claim of causality is made anywhere in this report — all results are associational (a fitted classifier's
discriminative performance), not a causal analysis. No claim of generalization beyond the evaluated domains,
splits, or feature sets is made. No claim of statistical significance is made without an accompanying CI and
effect size. No claim of recovery capability is made — H7 was not evaluated (not authorized, and no dataset
supports it regardless, per the frozen protocol's mapping).

## 25. Comparison implications for the original Phase 3

See the companion document `docs/PHASE3_REAL_DATA_COMPARISON.md`, created alongside this report and scoped
strictly to the H1 result actually produced here. The original Phase 3's frozen files
(`docs/PHASE3_1_EVALUATION_PROTOCOL.md`, `experiments/results/phase3_1/`, etc.) were not modified, read
for reference only.

## 26. Reproducibility information

- Scripts: `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`, `scripts/real_data/phase3_1_rd_aiops_evaluate.py`
  (both deterministic: sampling/window reuse at `seed=42` upstream, model fit `random_state=42`, bootstrap
  `seed=0`); AgentRx descriptive statistics computed inline (no randomness involved).
- Result artifacts: `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json,agentrx_descriptive.json}`,
  each embedding protocol version, dataset identifiers, feature set, exclusions, and bootstrap configuration.
- Re-running either script against the unmodified `data/processed/`/`data/audit/` artifacts reproduces the
  same numbers bit-for-bit (no non-seeded randomness is used anywhere in either script).

---

## Files created by this execution

- `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_1_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_1/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_1/aiops_results.json`
- `experiments/results/phase3_real_data/phase3_1/agentrx_descriptive.json`
- `docs/PHASE3_REAL_DATA_3_1_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (companion comparison artifact)

No file outside `scripts/real_data/`, `experiments/results/phase3_real_data/`, and this pair of new `docs/`
files was modified.

---

## STOP — Phase 3.1-RD complete

No later phase (3.2-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.


---

<a id="phase3-real-data-3-2-report"></a>
# PHASE3 REAL DATA 3 2 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_2_REPORT.md`  
**Role:** Real-data Phase 3.2 (representation) report.

# Phase 3.2-RD — Representation-Robustness Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.2-RD
execution only (Phase 3.3-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Phase 3.2-RD objective

Determine whether the real-data failure-risk signal established in Phase 3.1-RD is **robust to a small,
pre-registered representation matrix**, holding dataset, splits, test sets, leakage rules, and the supervised
classifier itself fixed — varying only the feature representation. This is a robustness check, not a search
for the best-performing representation; all pre-registered candidates are reported regardless of outcome.

## 2. Protocol version

`1.0` (`configs/phase3_real_data_protocol.json`, `docs/PHASE3_REAL_DATA_PROTOCOL.md`) — unchanged.
Representation matrix pre-registered separately in `configs/phase3_2_rd_representation_matrix.json`,
written and committed **before** any Phase 3.2-RD result was produced or inspected.

## 3. Phase 3.1 reference results (frozen, unmodified, re-quoted here for comparison only)

| | Alibaba random | Alibaba temporal | AIOps (LOEO, exploratory) |
|---|---|---|---|
| Baseline A (no-signal) AUROC | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Candidate F AUROC | 0.735 [0.703, 0.766] | 0.793 [0.774, 0.812] | 0.646 [0.536, 0.760] |

Source: `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json}` — verified
byte-identical to Phase 3.1-RD's original values before this execution began (§5 below). Not rerun, not
recomputed, not altered.

## 4. Representation definitions (pre-registered, see `configs/phase3_2_rd_representation_matrix.json`)

Classifier held fixed across all three: `LogisticRegression(max_iter=2000, random_state=42)` — identical to
Phase 3.1-RD's Candidate F.

- **R0_raw_scaled** — reference/anchor. Identical to Phase 3.1-RD's Candidate F: numeric columns
  median-imputed + `StandardScaler`; categorical columns constant-imputed + one-hot.
- **R1_log_transformed** — same feature columns as R0, but non-negative, heavy-tailed count/resource fields
  are `log1p`-transformed before standardization (Alibaba: task/instance counts, `plan_cpu`/`plan_mem`/
  `plan_gpu` statistics; AIOps: `n_observations`, `n_distinct_metrics`). Time-coordinate fields (Alibaba
  `job_start_time`, `mean_instance_start_time`) and AIOps value statistics (`mean_value`, `std_value`,
  `min_value`, `max_value`, which can be negative) are excluded from the log transform and remain on the R0
  path — documented in the pre-registration, not a post-hoc carve-out.
- **R2_pca_reduced** — the standardized numeric feature block is reduced to its first 2 principal components
  via `PCA(n_components=2)`, fit on the training data only (Alibaba: train split; AIOps: each LOEO training
  fold) and applied unchanged to held-out data. `n_components=2` matches the PCA(2) representation used
  throughout the original synthetic-data Phase 2/3 methodology (`src/failure_memory`), not tuned for
  real-data performance. Categorical one-hot columns are unchanged and concatenated alongside the 2 PCA
  components.

No fourth representation was added. No representation was dropped after seeing results (see §17 for the
weak/negative R2 finding, reported in full).

## 5. Pre-execution verification (per the authorization's explicit checklist)

| Check | Result |
|---|---|
| Frozen Real-Data Phase 3 protocol read | `docs/PHASE3_REAL_DATA_PROTOCOL.md`, `configs/phase3_real_data_protocol.json` — version confirmed `1.0` |
| Phase 3.1-RD completion report read | `docs/PHASE3_REAL_DATA_3_1_REPORT.md` |
| Phase 3.1-RD result artifacts read | `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json,agentrx_descriptive.json}` |
| Phase 3.1 test sets/splits unchanged | `data/audit/alibaba_gpu2020/splits_random_stratified.json` and `splits_temporal.json` re-loaded; counts re-confirmed identical to Phase 3.1-RD's reported 6,999/1,498/1,503 (random) and 6,177/1,324/2,499 (temporal) |
| No Phase 3.1 results altered | Alibaba random-split Candidate F AUROC re-read from the untouched Phase 3.1-RD JSON immediately before and after this execution: `0.7348398689698409` both times — file not modified |
| Phase 4 untouched | No file under `experiments/results/phase4_0/`, `phase4_1/`, `phase4_2/`, `docs/PHASE4_*`, or `configs/phase4_*` was opened for writing |
| Original Phase 3 results untouched | `experiments/results/phase3_1/aggregate_results.json` mtime unchanged, not opened for writing |

No integrity check failed. Execution proceeded.

## 6. Exact datasets evaluated

Alibaba GPU2020 main tier (same 10,000-job sample, same random and temporal splits as Phase 3.1-RD), AIOps
2020 (same 226 windows / 43 entities), AgentRx (NOT_EVALUABLE — see §12).

## 7. Exact independent units

Identical to Phase 3.1-RD: job (Alibaba), entity via LOEO (AIOps), trajectory (AgentRx, N/A here).

## 8. Exact sample sizes

Identical to Phase 3.1-RD, reused unchanged: Alibaba random 6,999/1,503 (train/test); temporal 6,177/2,499;
AIOps 226 windows (81 positive/145 negative), 43 entities, 0 dropped for missing telemetry. No resampling,
no record additions/removals.

## 9. Leakage exclusions

Identical to Phase 3.1-RD: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded
(never read by either Phase 3.2-RD script — verified via `assert_no_excluded_columns` on the Alibaba feature
frame, reused unmodified from the Phase 3.1-RD module). `pai_group_tag_table`/`pai_machine_spec` remain
unavailable in processed form and are not used by any of R0/R1/R2. AIOps PRE-FAILURE-window-only telemetry
scope is unchanged; business/trace telemetry was not added to any representation.

## 10. Alibaba random-split results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.735 | [0.703, 0.766] | 0.540 | [0.487, 0.596] |
| R1 (log1p-transformed) | 0.736 | [0.705, 0.767] | 0.511 | [0.461, 0.567] |
| R2 (PCA(2)-reduced) | 0.720 | [0.688, 0.751] | 0.495 | [0.445, 0.547] |

All three representations produce statistically indistinguishable AUROC on the random split (overlapping
CIs, point estimates within 0.016 of each other). **Robust to representation on this split.**

## 11. Alibaba temporal-split results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.793 | [0.774, 0.812] | 0.636 | [0.608, 0.667] |
| R1 (log1p-transformed) | **0.843** | [0.826, 0.861] | 0.736 | [0.705, 0.769] |
| R2 (PCA(2)-reduced) | **0.395** | [0.371, 0.418] | 0.356 | [0.337, 0.377] |

**Not robust to representation on this split.** R1 is materially higher than R0 (ΔAUROC +0.050, non-
overlapping CIs). R2 collapses to **below the no-signal baseline** (0.395 < 0.500) — worse than doing
nothing, with a tight CI ([0.371, 0.418]) that clearly excludes both 0.5 and R0/R1's range. See §17 for
interpretation; this is reported in full, not smoothed over.

As instructed: the 0.793 (R0, temporal) and 0.735 (R0, random) results are **not** interpreted as directly
comparable without acknowledging the Q4 distribution shift (20.1% train/val vs. 43.4% test failure rate,
established in Phase 3.1-RD) — restated here because it is the most plausible explanation for why
representation choice interacts so much more strongly with the temporal split than the random split (§17).

## 12. AIOps exploratory results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | [0.500, 0.500] | 0.353 | [0.254, 0.438] |
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.646 | [0.536, 0.760] | 0.575 | [0.447, 0.666] |
| R1 (log1p-transformed) | 0.630 | [0.506, 0.749] | 0.574 | [0.443, 0.667] |
| R2 (PCA(2)-reduced) | 0.605 | [0.477, 0.728] | 0.525 | [0.406, 0.610] |

226 windows, 43 entities, LOEO cross-validation, entity-level cluster bootstrap — identical structure to
Phase 3.1-RD. **AIOps remains EXPLORATORY** — none of these results is treated as confirmatory regardless of
point estimate. R0 and R1's CIs barely exclude 0.5 at the lower bound; **R2's CI ([0.477, 0.728]) includes
0.5** — R2 is not distinguishable from no-signal on AIOps, an inconclusive/negative finding for that
representation reported here in full.

## 13. AgentRx status

**NOT EVALUABLE.** No representation-robustness experiment was run. The frozen protocol's hypothesis-dataset
mapping (`configs/phase3_real_data_protocol.json`,
`hypothesis_dataset_mapping.H2_mechanism_is_supervision_not_representation`) already marks both
`agentrx_magentic` and `agentrx_tau_retail` as `NOT_EVALUABLE`, decided before Phase 3.1-RD ran and unchanged
here. Independently, Phase 3.1-RD's H1 blocker (every trajectory in both frozen samples — 44 Magentic, 29
τ-Retail — has ≥1 recorded failure, no negative class exists) means there is no supervised classifier at all
whose representation-robustness could even be tested. No unannotated trajectories were added to manufacture
a negative class. AgentRx is left unevaluated for Phase 3.2-RD, consistent with both the frozen protocol's
prior decision and Phase 3.1-RD's finding.

## 14. Representation comparison table (all datasets/splits)

| Dataset / split | R0 AUROC | R1 AUROC | R2 AUROC | Max spread (R_max − R_min) | Robust? |
|---|---|---|---|---|---|
| Alibaba random | 0.735 | 0.736 | 0.720 | 0.016 | Yes |
| Alibaba temporal | 0.793 | 0.843 | 0.395 | 0.448 | **No** |
| AIOps (exploratory) | 0.646 | 0.630 | 0.605 | 0.041 (within wide, overlapping CIs) | Yes, within exploratory uncertainty |

## 15. Effect sizes (relative to Phase 3.1-RD's R0/Candidate F reference)

| Dataset / split | Representation | ΔAUROC vs. R0 | Practically meaningful? |
|---|---|---|---|
| Alibaba random | R1 | +0.001 | No — within bootstrap noise |
| Alibaba random | R2 | −0.015 | No — within bootstrap noise (overlapping CIs) |
| Alibaba temporal | R1 | +0.050 | **Yes** — non-overlapping 95% CIs ([0.774,0.812] vs. [0.826,0.861]) |
| Alibaba temporal | R2 | −0.398 | **Yes, and adverse** — R2 falls below no-signal; not a subtle effect |
| AIOps | R1 | −0.016 | No — CIs overlap heavily, both wide |
| AIOps | R2 | −0.041 | Ambiguous — R2's CI includes 0.5 while R0/R1's barely exclude it; suggestive but not statistically decisive given AIOps's exploratory-only power |

## 16. Confidence intervals

All reported inline in §10–12; nonparametric percentile bootstrap, 2,000 resamples, seed 0, 95% CI, at the
correct independent-unit level (job for Alibaba, entity for AIOps) — identical methodology and configuration
to Phase 3.1-RD.

## 17. Robustness analysis

**Alibaba random split**: the signal is robust to all three representations. R0/R1/R2 AUROC all fall within
a 0.016 band with heavily overlapping CIs. This is the expected, unremarkable outcome for a well-behaved
i.i.d.-like split.

**Alibaba temporal split**: the signal is **not robust to representation**. Two distinct, opposite-direction
effects appear:
- R1 (log-transform) **improves** performance materially (+0.050 AUROC, non-overlapping CI) relative to R0.
  A plausible explanation: several of the log-transformed fields (`sum_inst_num`, `plan_cpu`/`plan_mem`/
  `plan_gpu`, instance/task counts) are heavy-tailed, and the Q4 test period's failure-heavy regime may
  involve workloads at more extreme values of these fields than the training period saw — a linear model on
  raw (non-log) heavy-tailed features can be disproportionately influenced by the tail under distribution
  shift, while the log-compressed version generalizes more evenly. This is a plausible mechanism, not a
  proven one; no causal claim is made.
- R2 (PCA(2)) **collapses below no-signal** (AUROC 0.395, tight CI excluding 0.5). The principal components
  are fit on the Q1–Q3 training distribution; under the confirmed real distribution shift to Q4 (20.1%→43.4%
  failure rate), the dominant axes of variance captured by PCA(2) on the training data do not preserve the
  same relationship to the label in the test period — plausibly, the direction the logistic regression
  learned as "risk-increasing" on the training-fit components corresponds to a different, or even reversed,
  real-world pattern in the shifted test distribution. This is a genuine representation-robustness failure,
  not a bug: the same PCA/LogisticRegression code produces a normal-looking result (0.720) on the random
  split, where no comparable distribution shift exists. **This is exactly the kind of finding Phase 3.2-RD
  was designed to surface, and is reported as a real negative result for R2 under temporal shift, not
  hidden or minimized.**

**AIOps**: R0/R1/R2 are statistically indistinguishable from each other given the wide, overlapping CIs
inherent to n=226/43 entities. R2's CI additionally fails to exclude the no-signal baseline. Given AIOps's
exploratory-only power (established in Phase 3.1-RD and the frozen protocol), this is reported as
inconclusive rather than as evidence that PCA "does not work" on AIOps — the sample size cannot support that
strong a claim either way.

**Overall determination**: the real-data failure-risk signal is **robust to representation on Alibaba's
random split and, with caveats, on AIOps**, but is **NOT robust to representation on Alibaba's temporal
(distribution-shifted) split** — representation choice interacts materially with the presence of covariate/
concept drift. This is itself a substantive, honestly-reported finding, not an experimental failure.

## 18. Negative findings

- R2 (PCA(2)) performs **worse than no-signal** on the Alibaba temporal split (AUROC 0.395) — the most
  significant negative finding of this report.
- R2 is statistically indistinguishable from no-signal on AIOps (CI includes 0.5).
- AgentRx again produced no result at all for this hypothesis (H2), for the same reason as H1 in Phase
  3.1-RD, plus the frozen protocol's prior NOT_EVALUABLE designation.

## 19. Inconclusive findings

- AIOps representation comparisons (R0 vs. R1 vs. R2) are inconclusive — all CIs overlap substantially, and
  the sample is too small/entity-clustered to distinguish representation effects with confidence, even though
  R2's point estimate is numerically lowest.

## 20. Failure cases

- No implementation failure occurred in this execution (unlike Phase 3.1-RD's AIOps baseline bug). R2's poor
  temporal-split performance is a genuine data/method finding, not a bug — confirmed by R2 performing
  normally (0.720, consistent with R0/R1) on the random split using identical code, which rules out a
  coding defect as the explanation for the temporal-split collapse.

## 21. Dataset-specific limitations

Carried forward unchanged from Phase 3.1-RD (§23 of that report): Alibaba's feature set remains restricted
(no `group_tag`/`machine_spec`/`user`); AIOps remains platform-telemetry-only and exploratory; AgentRx
remains structurally blocked. Additionally: PCA(2)'s specific behavior under the Alibaba temporal shift
(§17) should be treated as a property of this particular representation/distribution-shift combination, not
generalized to claim "PCA is unreliable" broadly — only 2 components were tested (chosen to match the
original methodology, not tuned), and no attempt was made to determine whether a different number of
components would behave differently (that would be a new, non-pre-registered experiment, out of scope here).

## 22. Comparison with original Phase 3

The original Phase 3.2/3.2C found that **supervision, not representation, was the operative mechanism**
(Candidate C's richer k-NN representation improved over control only modestly and inconsistently; Candidate
F's supervised learning on the *old, unmodified* PCA representation matched Candidate C's performance,
isolating supervision as the cause — `docs/PHASE3_2C_CANDIDATE_ABLATION.md`).

This real-data Phase 3.2-RD asked a related but distinct question — not "does supervision or representation
explain an existing weak signal" (the original's framing, motivated by a weak original result), but "is an
already-strong real-data signal robust across representation choices." The findings:

- **Alibaba random split**: **supports** the spirit of the original conclusion — representation makes
  little difference (R0≈R1≈R2), consistent with "supervision is what matters, representation is
  interchangeable" as a description of what's happening here too.
- **Alibaba temporal split**: **partially contradicts** that generalization — representation choice matters
  a great deal under distribution shift, to the point of flipping a signal from strongly positive to
  below-no-signal. The original Phase 3 never tested a distribution-shift condition in its 3.2/3.2C work
  (concept drift was tested later, in Phase 3.3, using the frozen Candidate-F representation only, not a
  representation comparison) — so this finding does not contradict a specific original claim, but it does
  show that the original's "representation doesn't matter much" conclusion should not be assumed to extend
  to a distribution-shift setting, which the original methodology did not examine in that combination.
- **AIOps**: **cannot adjudicate** — underpowered to distinguish representations at all.
- **AgentRx**: **cannot adjudicate** — no experiment possible.

The original conclusion is not rewritten, not forced into agreement, and not treated as contradicted where
the two experiments simply asked different questions.

## 23. Comparison with Phase 3.1-RD

| Metric | Phase 3.1-RD (R0/Candidate F only) | Phase 3.2-RD (R0/R1/R2) |
|---|---|---|
| Alibaba random AUROC | 0.735 [0.703,0.766] | R0 0.735 (identical, reused), R1 0.736, R2 0.720 — all consistent |
| Alibaba temporal AUROC | 0.793 [0.774,0.812] | R0 0.793 (identical, reused), R1 **0.843** (higher), R2 **0.395** (far lower) |
| AIOps AUROC | 0.646 [0.536,0.760] | R0 0.646 (identical, reused), R1 0.630, R2 0.605 — overlapping, inconclusive spread |

R0 in every case is a re-report of the exact Phase 3.1-RD Candidate F number (same code path, same data,
same split) — included here for side-by-side comparison, not recomputed. The main addition Phase 3.2-RD
contributes beyond Phase 3.1-RD is exposing that the Alibaba temporal-split result is **representation-
sensitive**, which Phase 3.1-RD (testing only one representation) could not have shown.

## 24. Reproducibility information

- Scripts: `scripts/real_data/phase3_2_rd_alibaba_evaluate.py`,
  `scripts/real_data/phase3_2_rd_aiops_evaluate.py` — both import and reuse the Phase 3.1-RD modules'
  feature-extraction functions unmodified (`build_feature_matrix`, `load_windows`,
  `extract_window_features`, leakage-exclusion constants) rather than re-implementing them, to guarantee
  identical underlying data/preprocessing.
- Representation matrix: `configs/phase3_2_rd_representation_matrix.json`, pre-registered before any result
  was produced.
- Result artifacts: `experiments/results/phase3_real_data/phase3_2/{alibaba_results.json,aiops_results.json}`,
  each embedding phase, protocol version, representation-matrix source, dataset identifiers, and bootstrap
  configuration.
- Determinism: sampling/window reuse at `seed=42` (upstream, unchanged), classifier `random_state=42`, PCA
  `random_state=42`, bootstrap `seed=0`. Re-running either script against the unmodified
  `data/processed/`/`data/audit/` artifacts and the unmodified representation-matrix config reproduces the
  same numbers bit-for-bit.
- Provenance preserved per the unified-benchmark requirement: `source_dataset`, entity/job identifiers,
  split membership, and processing version are carried through in the same manner as Phase 3.1-RD (feature
  frames are built from the same provenance-carrying processed CSVs; no new field was stripped).

---

## Files created by this execution

- `configs/phase3_2_rd_representation_matrix.json`
- `scripts/real_data/phase3_2_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_2_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_2/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_2/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_2_REPORT.md` (this document)

No file outside `configs/`, `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_2/`, and this
new `docs/` file was modified. Phase 3.1-RD's artifacts, the frozen Real-Data Phase 3 protocol, the original
Phase 3 results, and Phase 4 were all re-verified unchanged (§5).

---

## STOP — Phase 3.2-RD complete

No later phase (3.3-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.


---

<a id="phase3-real-data-3-3-report"></a>
# PHASE3 REAL DATA 3 3 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_3_REPORT.md`  
**Role:** Real-data Phase 3.3 (generalization/distribution-shift) report.

# Phase 3.3-RD — Real-Data Generalization / Distribution-Shift Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.3-RD
execution only (Phase 3.4-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Objective

Determine how well the real-data failure-risk signal generalizes when the evaluation distribution differs
from the training distribution — specifically, whether the representation behavior already observed on
Alibaba's frozen temporal split in Phase 3.2-RD (R0 ≈ 0.79, R1 ≈ 0.84, R2 collapsing to ≈ 0.40) reflects a
genuine generalization phenomenon, characterized here (not re-optimized, not repaired). This phase does
**not** search for a better representation, does not tune PCA, and does not attempt to make the temporal
result "look better."

## 2. Protocol version

`1.0` (`configs/phase3_real_data_protocol.json`, `docs/PHASE3_REAL_DATA_PROTOCOL.md`) — unchanged.
Representation matrix (`configs/phase3_2_rd_representation_matrix.json`) — unchanged, reused as-is; no
fourth representation added, none removed.

## 3. Authorization scope

Authorized: Phase 3.3-RD only. Not authorized: Phase 3.4-RD, 3.5-RD, 3.6-RD, Phase 4, any modification to
the frozen Real-Data Phase 3 protocol, any modification to original Phase 3 results. Confirmed respected
throughout (§21, §Files-created).

## 4. Integrity checks (pre-execution, per the authorization's explicit 10-point checklist)

| # | Check | Result |
|---|---|---|
| 1 | Phase 3.1-RD results unchanged | Alibaba random AUROC re-read: `0.7348398689698409` (identical to original); Alibaba temporal AUROC: `0.7931707840566771` (identical); AIOps AUROC: `0.6455824250651649` (identical) |
| 2 | Phase 3.2-RD results unchanged | Temporal R0/R1/R2 re-read: `0.7931707840566771 / 0.8433965882788796 / 0.39450623763274134` (identical to the frozen Phase 3.2-RD report); random R0/R1/R2 and AIOps R0/R1/R2 also re-confirmed identical |
| 3 | Frozen protocol version still 1.0 | Confirmed |
| 4 | Alibaba random split unchanged | 6,999 / 1,498 / 1,503 (train/val/test) — identical to Phase 3.1-RD/3.2-RD |
| 5 | Alibaba temporal split unchanged | 6,177 / 1,324 / 2,499 — identical |
| 6 | AIOps population unchanged | 81 valid positive windows, 145 valid negative windows — identical |
| 7 | AgentRx composition unchanged | Magentic 58 total / 44 annotated / 0 with zero failures; τ-Retail 29 total / 29 annotated / 0 with zero failures — identical to Phase 3.1-RD's finding |
| 8 | No excluded leakage features entered the pipeline | This phase's only new script (`phase3_3_rd_alibaba_distribution_shift.py`) reuses `build_feature_matrix()` and `assert_no_excluded_columns()` unmodified from Phase 3.1-RD's module; no new field was read; `pai_sensor_table`/`pai_machine_metric`/`max_mem`/`max_gpu_wrk_mem` remain unread |
| 9 | Phase 4 untouched | No file under `experiments/results/phase4_*`, `docs/PHASE4_*`, `configs/phase4_*` opened for writing |
| 10 | Original Phase 3 untouched | `experiments/results/phase3_1/aggregate_results.json` mtime unchanged, not opened for writing |

No integrity check failed. Execution proceeded.

## 5. Exact datasets

Alibaba GPU2020 main tier (identical 10,000-job sample, identical splits). AIOps 2020: **NOT EVALUABLE FOR
THIS GENERALIZATION ANALYSIS** (§9). AgentRx: **NOT EVALUABLE** (§10).

## 6. Independent units

Job (Alibaba) — unchanged from Phase 3.1-RD/3.2-RD. No unit-level change in this phase.

## 7. Exact splits

Alibaba temporal split, reused verbatim and unmodified: train/validation = relative-time Q1–Q3 (n=6,177/
1,324), test = strict future holdout Q4 (n=2,499). This **is** the frozen generalization/distribution-shift
condition specified by the protocol (`docs/PHASE3_REAL_DATA_PROTOCOL.md` §9) — Phase 3.3-RD does not define a
new split, does not rebalance Q4, and does not use Q4 labels to alter the model in any way.

## 8. Representation definitions

Identical to Phase 3.2-RD, reused unmodified from `configs/phase3_2_rd_representation_matrix.json`: R0
(raw/scaled), R1 (log1p-transformed heavy-tailed fields), R2 (PCA(2)-reduced numeric block). No fourth
representation was added. No representation was dropped. PCA dimensionality was **not** changed (no PCA(3),
PCA(5), PCA(10) or any variant was tested — that would be a new experiment, explicitly out of scope per the
authorization, and is instead listed as a possible future experiment in §22).

## 9. Distribution-shift characterization (new analysis performed in this phase, label-free except for the
already-disclosed base-rate figure)

A purely descriptive comparison of each feature's train (Q1–Q3) vs. test (Q4) distribution was computed —
**no model was fit, no test label was used to select or transform any feature**, and the previously-disclosed
failure-rate shift is restated, not recomputed differently. Source:
`experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`
(`scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py`).

**Already-established label shift** (identical figure to Phase 3.1-RD/3.2-RD, restated for context): train
20.11% Failed, test 43.42% Failed.

**Newly characterized covariate shift** (this phase's contribution):

| Feature | Train mean | Test mean | Train median | Test median | Note |
|---|---|---|---|---|---|
| `mean_plan_cpu` | 691.8 | 465.9 | 600 | 600 | test jobs request ~33% less CPU on average |
| `max_plan_cpu` | 708.6 | 478.6 | 600 | 600 | same pattern |
| `mean_plan_gpu` | 70.5 | 56.4 | **50** | **25** | test median GPU allocation halves |
| `max_plan_gpu` | 70.6 | 56.4 | 50 | 25 | same pattern |
| `sum_inst_num` | 6.29 | 4.33 | 1 | 1 | test jobs request fewer total instances on average |
| `n_instances` | 6.57 | 4.64 | 1 | 1 | same pattern |
| `n_distinct_machines` | 4.71 | 3.41 | 1 | 1 | same pattern |
| `job_start_time` (std) | 1,279,722 | 262,293 | — | — | test period (Q4) spans a much narrower absolute time window than the pooled Q1–Q3 train period, as expected from quartile construction |

| `dominant_gpu_type` | Train proportion | Test proportion |
|---|---|---|
| MISC | 62.1% | **80.9%** |
| T4 | 23.6% | 12.1% |
| P100 | 7.2% | 4.0% |
| V100 | 3.1% | 1.2% |
| V100M32 | 2.0% | 0.5% |
| UNKNOWN | 2.1% | 1.2% |

**Observation**: this is a genuine covariate shift, not merely a label-rate shift — the Q4 test period has
systematically smaller resource requests (CPU, GPU, instance counts) and a substantially different GPU-type
mix (MISC share rising ~19 points) than the Q1–Q3 training period. Both the label distribution and the
feature distributions differ between train and test. This is reported as a factual characterization of the
evaluation environment; no causal claim about *why* the platform's workload composition changed over time is
made — that is outside what this data can determine.

## 10. Alibaba generalization results

**These are the exact, unmodified R0/R1/R2 temporal-split results already produced and frozen in Phase
3.2-RD** (`experiments/results/phase3_real_data/phase3_2/alibaba_results.json`,
`results.temporal.representations`). They are reused here, not rerun, not recomputed, and not altered in
any way — re-running the identical deterministic script (fixed seeds throughout) against unmodified data
would reproduce them bit-for-bit, so no new computation was performed. This is precisely the frozen temporal
generalization experiment the objective (§1) calls for; Phase 3.3-RD's contribution is characterizing (§9)
and interpreting (§17) that already-frozen result, not re-deriving it.

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled) | 0.793 | [0.774, 0.812] | 0.636 | [0.608, 0.667] |
| R1 (log1p-transformed) | **0.843** | [0.826, 0.861] | 0.736 | [0.705, 0.769] |
| R2 (PCA(2)-reduced) | **0.395** | [0.371, 0.418] | 0.356 | [0.337, 0.377] |

Baseline A (no-signal), for reference: AUROC 0.500 [0.500, 0.500], AUPRC 0.434 [0.415, 0.454] (AUPRC above
0.5-baseline-AUROC because AUPRC's uninformative floor equals the positive prevalence, 43.42% at Q4, not
0.5 — see §11 for why raw AUROC/AUPRC must be read against this prevalence, not in isolation).

## 11. AUPRC and AUROC, interpreted against Q4 prevalence

Q4's positive (Failed) prevalence is 43.42% — over double the 20.11% train-period rate. A few consequences,
stated explicitly per the authorization's instruction not to interpret AUPRC without this context:

- AUPRC's uninformative baseline is the positive prevalence itself (here, 0.434), not 0.5. R0's AUPRC (0.636)
  and R1's (0.736) both clear that elevated floor by a wide margin; R2's AUPRC (0.356) falls **below** the
  0.434 floor — i.e., R2 is worse than a random-ranking classifier would be expected to score on this
  prevalence, consistent with (and reinforcing) its sub-0.5 AUROC.
- A higher raw AUROC on the Q4 test set is **not**, by itself, evidence of better real-world deployment
  performance: Q4's substantially higher base rate changes the cost/benefit profile of any fixed decision
  threshold, and the covariate shift documented in §9 means the *feature values* a deployed model would see
  in a Q4-like future period differ systematically from what it was trained on. AUROC/AUPRC quantify ranking
  quality on this specific, already-shifted test set — they do not by themselves certify that a threshold
  calibrated on Q1–Q3 would behave sensibly on Q4, a question this phase does not attempt to answer (no
  threshold/calibration analysis was in scope or run).

## 12. Effect sizes

| Comparison | ΔAUROC | Interpretation |
|---|---|---|
| R1 vs. R0 (temporal) | +0.050 | Non-overlapping 95% CIs — a real, reproducible difference under this specific train/test pair, not noise |
| R2 vs. R0 (temporal) | −0.398 | Large, adverse, tightly-bounded (CI width 0.047) — R2 is not merely weaker, it is anti-informative on this split |
| R0 (temporal) vs. R0 (random, Phase 3.2-RD reference 0.735) | +0.058 | Not comparable at face value — different test populations with different prevalence (§11); not interpreted as "temporal generalizes better than random" |

## 13. Comparison with Phase 3.1-RD

Phase 3.1-RD evaluated only R0 (called "Candidate F" there) on the temporal split: AUROC 0.793 [0.774,0.812].
That number is exactly R0's value here (same computation, same data, same code path) — **no change**. Phase
3.1-RD did not test whether this behavior was representation-dependent; that question was first answered in
Phase 3.2-RD (§14) and is now characterized further (not re-answered) in this phase.

## 14. Comparison with Phase 3.2-RD

Phase 3.2-RD is where R0/R1/R2's temporal-split behavior was first measured (§10 of that report) — this
phase reuses those exact numbers unchanged (§10 above) and adds the covariate-distribution characterization
(§9) that Phase 3.2-RD's scope (representation robustness) did not include. No representation's result
changed between Phase 3.2-RD and this phase, because none was re-run with any different configuration — this
persistence is itself the finding requested by the objective (§1): the previously observed R1>R0≫R2 ordering
is not an artifact of a single run; it is the frozen, reproducible state of the evaluation, now placed in the
context of a characterized (not just observed) real covariate shift.

## 15. Comparison with original Phase 3

The original (synthetic) Phase 3.3 (`docs/PHASE3_3_GENERALIZATION.md`) tested **concept drift** — varying
`drift_scale` at test time only, under a **fixed covariate distribution** — and found the frozen Candidate F
representation generalized: AUROC stayed well above no-signal across weaker (0.698), original (0.655), and
stronger (0.602) drift conditions, without needing to vary representation (only one representation, the
frozen Candidate F, was ever tested in the original Phase 3.3).

This real-data Phase 3.3-RD result is **not a replication of that finding** — it is a different, complementary
condition:
- The original Phase 3.3 explicitly excluded covariate shift (fixed feature distribution) and tested only
  concept drift (label-generating relationship changing).
- Alibaba's Q1–Q3→Q4 split, as characterized in §9, is **both** a label-rate shift **and** a genuine covariate
  shift (resource-request sizes and GPU-type mix both shift), and Phase 3.2-RD showed representation choice
  interacts strongly with it (R1 improves, R2 collapses).
- The two experiments therefore **cannot be directly compared** as confirming or contradicting one another —
  they probe different shift types (concept-only vs. concept+covariate) and, unlike the original, this one
  varies representation rather than holding a single representation fixed. This is reported as **NOT
  DIRECTLY COMPARABLE**, not forced into a replicated/contradicted classification.
- The qualitative lesson that *does* carry over loosely: the original Phase 3.3 found the frozen candidate
  representation (their only one) generalized under concept drift; this real-data result shows that whether
  a real-data representation generalizes under a real (concept+covariate) shift **depends on which
  representation** — a nuance the original single-representation design could not have surfaced, since it
  never had a second representation to compare against under drift.

## 16. Distribution-shift findings

Summarized from §9: Q1–Q3→Q4 is a compound shift — failure-rate increase (20.1%→43.4%), reduced average
resource requests (CPU/GPU/instance counts all lower in Q4), and a substantial GPU-type composition shift
(MISC share 62.1%→80.9%). This is presented as a factual characterization; §17 discusses (as hypotheses, not
proven mechanisms) how this might relate to R1/R2's divergent behavior.

## 17. Alternative explanations (explicitly hypotheses, not demonstrated causes)

Per the authorization's instruction, the following are offered as **candidate hypotheses only** — none is
claimed as demonstrated:

- **Heavy-tailed feature behavior under shift (favors R1's improvement)**: `sum_inst_num`, `plan_cpu`,
  `plan_gpu`, and instance/machine counts are right-skewed (train means far exceed medians in every case,
  e.g. `mean_plan_cpu` mean 691.8 vs. median 600). A linear model on raw values can be disproportionately
  sensitive to the tail; log-compression may make the learned relationship more stable across a shift in the
  tail's shape. This is a plausible mechanism for R1 > R0, not a proven one.
- **PCA projection instability under covariate shift (favors R2's collapse)**: PCA(2) is fit only on Q1–Q3
  training data. If the dominant axes of variance in Q1–Q3 (the directions PCA(2) captures) do not align the
  same way with the failure label once the covariate distribution shifts (§9's GPU-type and resource-size
  changes), a linear classifier trained on those axes could see its learned "risk-increasing" direction
  become partially or wholly inverted on the shifted test data — a known failure mode of unsupervised
  dimensionality reduction under covariate shift. Also plausible, not demonstrated: no experiment
  decomposing the PCA components' loadings pre/post shift was run in this phase (that would be a new
  analysis — see §22).
- **Changed workload composition changing the feature-label relationship (concept drift, not just covariate
  shift)**: it is possible that the *relationship* between a given resource-request pattern and failure
  probability itself changed between Q1–Q3 and Q4 (true concept drift), independent of or in addition to the
  covariate shift documented in §9. This phase's design (fixed model, fixed train/test split) cannot
  distinguish covariate shift from concept drift as the dominant driver — doing so would require a dedicated
  experiment (e.g., holding covariates fixed and varying only time, which the real data does not allow to be
  cleanly separated) and is not attempted here.

No claim of causality is made for any of the above. They are offered as candidate explanations consistent
with the observed pattern, explicitly to satisfy the requirement not to assert an unproven mechanism as fact.

## 18. AIOps

**NOT EVALUABLE FOR THIS GENERALIZATION ANALYSIS.** The frozen AIOps protocol provides no legitimate
independent distribution-shift/generalization condition: the 226-window population has no frozen train/test
temporal partition (unlike Alibaba's Q1–Q3/Q4 split), and constructing one now (e.g., an April-vs-May split)
would be inventing a new split after the fact — explicitly prohibited by this authorization ("Do NOT
manufacture temporal splits from the data simply to obtain a generalization experiment"). The existing LOEO
structure tests entity-level generalization, not distribution shift, and was already exercised in Phase
3.1-RD/3.2-RD; it is not re-run here since nothing about it would test a *shift* condition. AIOps remains
EXPLORATORY ONLY per the frozen protocol and this phase adds no AIOps result.

## 19. AgentRx

**NOT EVALUABLE**, for the same reason established in Phase 3.1-RD and reconfirmed in Phase 3.2-RD: both
frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain no negative class (every trajectory
has ≥1 recorded failure), so no supervised classifier exists whose generalization could be tested. No
unannotated trajectories were added; the two domains were not pooled; no workaround was attempted.

## 20. Positive findings

- R1 (log1p-transformed) not only survives but *improves* under the temporal distribution shift relative to
  R0 (+0.050 AUROC, non-overlapping CI) — a genuinely positive, reproducible result for that representation
  under this specific shift.
- The distribution-shift characterization (§9) is itself a positive contribution: it establishes, using only
  pre-outcome covariates and without any test-label tuning, that Q1–Q3→Q4 is a real, multi-faceted shift
  (label rate, resource-request sizes, GPU-type mix) — not a sampling artifact.

## 21. Negative findings

- **R2 (PCA(2)) remains below the no-signal baseline under the temporal shift** (AUROC 0.395, tight CI
  [0.371, 0.418]) — reported prominently, exactly as instructed, not minimized. This is the same result
  already reported in Phase 3.2-RD, reconfirmed here as the frozen, unmodified state (§4, checks 1–2), not a
  new negative finding but a persistent one.

## 22. Inconclusive findings / limitations

- The mechanism behind R1's improvement and R2's collapse (§17) remains **undetermined** — three plausible
  hypotheses are offered, none confirmed. This is intentionally left inconclusive rather than resolved by a
  new, unauthorized experiment.
- AIOps and AgentRx contribute no generalization evidence in this phase (§18, §19) — the real-data
  generalization question is answered by Alibaba alone in this execution.
- The Alibaba temporal result reflects one single train/test partition (Q1–Q3 vs. Q4); no repeated or
  cross-validated temporal generalization estimate exists (the frozen protocol defines only this one
  temporal split), so the precision of "how well does this generalize" is bounded by having exactly one
  such comparison, not several.

## Future experiments (explicitly NOT run in this phase — separated from current findings)

The following are documented as candidate follow-up work only. **None of them was performed, and none
influenced any result reported above**:

- Testing PCA at other dimensionalities (PCA(3), PCA(5), PCA(10), …) to see whether R2's collapse is
  specific to 2 components — would require a new, separately pre-registered representation matrix under a
  future authorized phase, not this one.
- Decomposing PCA(2)'s component loadings before vs. after the shift to directly test the "projection
  instability" hypothesis in §17, rather than leaving it as an untested hypothesis.
- A dedicated experiment isolating covariate shift from concept drift (e.g., reweighting or matching on
  covariates) to determine which dominates the Q1–Q3→Q4 shift's effect on representation robustness.
- Threshold/calibration analysis under the shifted Q4 prevalence, since §11 notes that ranking-quality
  metrics (AUROC/AUPRC) alone do not certify deployment-time decision quality under a shifted base rate.

## 23. Reproducibility information

- New script: `scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py` — deterministic, no randomness
  involved (purely descriptive statistics), reuses `build_feature_matrix()` from the unmodified Phase 3.1-RD
  module.
- No model-fitting script was created or run in this phase; §10's results are citations of
  `experiments/results/phase3_real_data/phase3_2/alibaba_results.json`, not new computations.
- Result artifact: `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`, embedding
  phase, protocol version, dataset identifier, and the exact train/test sample sizes.
- Provenance preserved: the distribution-shift script operates on the same provenance-carrying processed CSVs
  and the same frozen split-membership file as all prior phases; no field was stripped or renamed.

---

## Files created by this execution

- `scripts/real_data/phase3_3_rd_alibaba_distribution_shift.py`
- `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json`
- `docs/PHASE3_REAL_DATA_3_3_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — see that file's new H3 section)

No file outside `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_3/`, and these two `docs/`
files was modified. Phase 3.1-RD's and Phase 3.2-RD's artifacts, the frozen Real-Data Phase 3 protocol, the
original Phase 3 results, and Phase 4 were all re-verified unchanged (§4).

---

## STOP — Phase 3.3-RD complete

No later phase (3.4-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.


---

<a id="phase3-real-data-3-4-report"></a>
# PHASE3 REAL DATA 3 4 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_4_REPORT.md`  
**Role:** Real-data Phase 3.4 (comparison) report.

# Phase 3.4-RD — Consolidated Baseline-vs-Candidate Comparison — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.4-RD
execution only (Phase 3.5-RD, 3.6-RD, and Phase 4 explicitly not authorized).

---

## 1. Objective

Following the original (synthetic) Phase 3.4's design (`docs/PHASE3_4_COMPARISON.md`): consolidate everything
evaluated so far into one comparison, under the same frozen protocol, with **no new model fitting, training,
or tuning**. Answer: do the candidate representations (R0/R1/R2) actually improve over the frozen baseline
(no-signal) when compared under identical data/splits/metrics/statistics, with a properly *paired* statistical
test where the same test-set examples support pairing?

## 2. Protocol version

`1.0` — unchanged. Representation matrix (`configs/phase3_2_rd_representation_matrix.json`) — unchanged,
reused as-is.

## 3. Exact baseline definition

**Baseline A (no-signal)**, frozen in Phase 3.1-RD: a fixed constant score (Alibaba: train-split empirical
failure prevalence; AIOps: overall 226-window pool prevalence). This is the **only** baseline that exists
uniformly across the real-data track.

**Documented departure from the original Phase 3.4's baseline choice**: the original synthetic Phase 3.4
treated *calibrated confidence* (Baseline B) as the strongest existing reference and asked whether the
selected candidate beat *that*. No analogue of calibrated confidence exists anywhere in the real-data track
— established in `docs/PHASE3_REAL_DATA_3_1_REPORT.md` §15 ("no dataset has a pre-existing upstream classifier
whose confidence output could be measured") and unchanged since. Baseline A is therefore the necessary and
only frozen baseline Phase 3.4-RD can compare against; this is a structural fact about the available real
data, not a choice made for convenience. Full pre-registration:
`configs/phase3_4_rd_comparison_matrix.json`.

## 4. Exact candidate definitions

R0 (raw/scaled), R1 (log1p-transformed), R2 (PCA(2)-reduced) — identical, unmodified, frozen in Phase
3.2-RD (`configs/phase3_2_rd_representation_matrix.json`). No fourth candidate was added; none was dropped.

## 5. Pre-registered comparison matrix

Written to `configs/phase3_4_rd_comparison_matrix.json` before any Phase 3.4-RD computation was run. Fixes:
exact baseline (§3), exact candidates (§4), exact datasets/splits (Alibaba random + temporal, AIOps LOEO;
AgentRx `NOT_EVALUABLE`), and the statistical unit for each (job / entity / not applicable).

## 6. Integrity checks

| Check | Result |
|---|---|
| Protocol unchanged | `protocol_version` re-read as `1.0` |
| Phase 3.1-RD results unchanged | Alibaba random Candidate F AUROC re-read: `0.7348398689698409` (matches); AIOps Candidate F AUROC: `0.6455824250651649` (matches) |
| Phase 3.2-RD results unchanged | Alibaba temporal R2 AUROC: `0.39450623763274134` (matches); AIOps R0 AUROC: `0.6455824250651649` (matches) |
| Phase 3.3-RD results unchanged | Distribution-shift artifact `n_train`/`n_test`: `6177`/`2499` (matches) |
| Original Phase 3 unchanged | `experiments/results/phase3_1/aggregate_results.json` mtime/content unchanged from before this phase |
| Phase 4 unchanged | `experiments/results/phase4_0/episodes.json` mtime/content unchanged |
| Raw data unchanged | No `data/raw/` file opened by any Phase 3.4-RD script |
| Splits unchanged | Random 6,999/1,498/1,503; temporal 6,177/1,324/2,499 — identical |
| Sample populations unchanged | AIOps 81 positive / 145 negative / 43 entities; AgentRx 44/29 annotated, 0 with zero failures — identical |
| All matrix candidates evaluated/reported | R0, R1, R2, and Baseline A all reported for every applicable dataset/split (§10–12) |
| No test-set tuning | No hyperparameter, threshold, or candidate selection decision was made using any Phase 3.4-RD test result |
| Correct independent-unit inference | Job-level paired bootstrap (Alibaba); entity-level paired cluster bootstrap (AIOps) |

**One process error occurred and is disclosed in full, not minimized**: while investigating a score-verification
discrepancy (§Implementation issues), the standalone script `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`
was re-run directly, which overwrote `experiments/results/phase3_real_data/phase3_1/alibaba_results.json` —
a file this authorization explicitly required to remain unmodified. **The rewritten file's content was
verified field-by-field against the values already on record in this conversation and in
`docs/PHASE3_REAL_DATA_3_1_REPORT.md`, and matched bit-for-bit in every field.** No actual change occurred to
the frozen Phase 3.1-RD result; only the file's modification timestamp changed. This should not have happened
regardless of the outcome being harmless, and is reported here rather than silently passed over.

No other integrity check failed.

## 7. Dataset/sample information

Identical to Phase 3.1-RD/3.2-RD/3.3-RD throughout: Alibaba main tier 10,000 jobs (random split
6,999/1,498/1,503; temporal split 6,177/1,324/2,499); AIOps 226 windows / 43 entities; AgentRx 44 (Magentic)
+ 29 (τ-Retail) annotated trajectories, `NOT_EVALUABLE`.

## 8. Independent units

Job (Alibaba, paired bootstrap over test-set rows), entity (AIOps, paired cluster bootstrap over the 43
entities), not applicable (AgentRx).

## 9. Leakage exclusions

Unchanged: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded; `pai_group_tag_table`/
`pai_machine_spec` remain unavailable in processed form and are not used; feature availability is identical
between baseline and every candidate (all four share the exact same input feature columns, differing only in
representation transform) — no "STOP" condition (feature availability differing between baseline and
candidate) was triggered, because it never arose.

## 10. Alibaba random-split results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.735 | 0.537 | +0.235 | [0.203, 0.266] |
| R1 (log1p) | 0.736 | 0.508 | +0.236 | [0.205, 0.267] |
| R2 (PCA(2)) | 0.720 | 0.491 | +0.220 | [0.188, 0.251] |

All three candidates clearly and significantly beat Baseline A (every paired-difference CI excludes 0, all
positive). R0/R1/R2 are close to each other; no candidate's CI over the other two's point estimates suggests
a clearly superior choice on this split — consistent with Phase 3.2-RD's original "robust to representation on
the random split" finding, now confirmed with a proper paired test rather than an overlapping-CI heuristic.

## 11. Alibaba temporal-split results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.793 | 0.635 | +0.293 | [0.274, 0.312] |
| R1 (log1p) | 0.843 | 0.735 | +0.343 | [0.326, 0.361] |
| R2 (PCA(2)) | 0.395 | 0.355 | **−0.105** | **[−0.129, −0.082]** |

R0 and R1 both clearly and significantly beat Baseline A. **R2 is significantly WORSE than doing nothing** —
its paired-difference CI is entirely negative and excludes 0, which is a materially stronger and more
rigorous statement than the earlier, unpaired observation that R2's point estimate merely fell below 0.5:
this paired test directly establishes that R2 costs, not just fails to help, relative to the no-signal
baseline on this exact test set. Reported prominently, exactly as required.

## 12. AIOps results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.647 | 0.573 | +0.146 | [0.036, 0.260] |
| R1 (log1p) | 0.631 | 0.573 | +0.130 | [0.006, 0.249] |
| R2 (PCA(2)) | 0.604 | 0.516 | +0.105 | **[−0.023, 0.228]** |

**EXPLORATORY, unchanged classification.** R0 and R1's paired-difference CIs exclude 0 (R1 only barely, lower
bound 0.006), providing some evidence both beat no-signal. **R2's paired-difference CI includes 0**
([−0.023, 0.228]) — under this more rigorous paired entity-cluster test, R2's apparent improvement over
Baseline A on AIOps is **not statistically distinguishable from no effect**. This is a materially more
cautious conclusion than the unpaired Phase 3.2-RD framing ("all similar, wide overlapping CIs") — the paired
design sharpens the AIOps R2 finding specifically into an explicit non-result, reported as such.

## 13. AgentRx status

**NOT EVALUABLE.** Both frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain zero
trajectories with `num_failures = 0` — reconfirmed unchanged this phase. No unannotated trajectory was added;
the two domains were not pooled; no comparison was attempted.

## 14. Baseline-vs-candidate comparison (consolidated table)

| Dataset | Split | Baseline | Candidate | AUROC | 95% CI (paired Δ) | Interpretation |
|---|---|---|---|---|---|---|
| Alibaba | random | A (0.500) | R0 | 0.735 | +0.235 [0.203,0.266] | Clear, significant improvement |
| Alibaba | random | A (0.500) | R1 | 0.736 | +0.236 [0.205,0.267] | Clear, significant improvement |
| Alibaba | random | A (0.500) | R2 | 0.720 | +0.220 [0.188,0.251] | Clear, significant improvement |
| Alibaba | temporal | A (0.500) | R0 | 0.793 | +0.293 [0.274,0.312] | Clear, significant improvement |
| Alibaba | temporal | A (0.500) | R1 | 0.843 | +0.343 [0.326,0.361] | Clear, significant improvement (largest of any row) |
| Alibaba | temporal | A (0.500) | R2 | 0.395 | **−0.105 [−0.129,−0.082]** | **Clear, significant HARM** — worse than doing nothing |
| AIOps | LOEO (exploratory) | A (0.500) | R0 | 0.647 | +0.146 [0.036,0.260] | Improvement, exploratory precision |
| AIOps | LOEO (exploratory) | A (0.500) | R1 | 0.631 | +0.130 [0.006,0.249] | Improvement, exploratory precision (borderline) |
| AIOps | LOEO (exploratory) | A (0.500) | R2 | 0.604 | +0.105 [−0.023,0.228] | **Inconclusive** — CI includes 0 |
| AgentRx | — | — | — | — | — | NOT EVALUABLE |

No candidate was hidden; no row omitted regardless of outcome.

## 15. AUROC/AUPRC

Reported inline in §10–12. AUPRC point estimates track the same ordering as AUROC within each split/dataset,
with one exception already known from Phase 3.1-RD/3.2-RD: because Q4's positive prevalence (43.4%) sets
AUPRC's uninformative floor much higher than 0.5, R2's temporal AUPRC (0.355) sits **below** that floor
(0.434 disclosed in Phase 3.3-RD §11) — reconfirmed here, consistent with its negative paired AUROC effect.

## 16. Effect sizes

Reported as the paired mean difference in §10–12/§14 (not merely the difference of independently-computed
point estimates) — this is the methodologically stronger choice given the same test-set rows/entities
support every candidate.

## 17. 95% CIs

All from paired bootstrap (job-level for Alibaba, entity-cluster-level for AIOps), 2,000 resamples, seed 0,
95% percentile CI — reported alongside every effect size, never in isolation.

## 18. Statistical comparisons

The paired design (resampling the same test rows/entities jointly across baseline and candidate) is the
"appropriate paired comparison" called for when comparing correlated predictions on the same test examples —
it directly answers whether a *specific* candidate's improvement (or harm) over the baseline is distinguishable
from zero on *this* test set, which an unpaired CI-overlap heuristic (used in Phase 3.1-RD/3.2-RD/3.3-RD)
only approximates. No new statistical test was invented after seeing any result — the paired-bootstrap
design was fixed in §5's pre-registration, before any Phase 3.4-RD number was computed.

## 19. Positive findings

- On both Alibaba splits, R0 and R1 significantly and substantially beat the no-signal baseline, with tight,
  clearly-positive CIs.
- R1 achieves the single largest paired improvement of any row in this report (+0.343 AUROC on the temporal
  split) — reported factually, not as a general endorsement (see §"What this does NOT establish").
- AIOps R0 and R1 show paired evidence of improvement over no-signal even under the stricter entity-cluster
  paired test, though at exploratory precision.

## 20. Negative findings

- **R2 (PCA(2)) is significantly WORSE than the no-signal baseline on the Alibaba temporal split** — the
  paired test makes this a stronger, more direct statement than the earlier phases' framing. Reported
  prominently, as required.
- AIOps R2's apparent improvement over no-signal does not survive the paired entity-cluster test (CI includes
  0) — a genuine negative/non-finding for that specific candidate on that specific dataset, not hidden.

## 21. Inconclusive findings

- AIOps R1's paired CI [0.006, 0.249] barely excludes 0 — treated as weak, not strong, evidence; not upgraded
  to a confident claim merely because the interval technically excludes zero.
- Whether R1's temporal-split advantage over R0 (+0.050 AUROC, established in Phase 3.2-RD/3.3-RD) reflects a
  generally superior representation or a shift-specific artifact remains open — this phase adds a paired
  confirmation that the *baseline* comparison holds, but does not add a new R1-vs-R0 head-to-head paired test
  (that would be a different, new statistical comparison not specified in the pre-registered matrix, and is
  not performed here).

## 22. Distribution-shift interpretation

Per the authorization's explicit instruction: the Alibaba temporal test set carries ~43.4% failure prevalence
and the covariate shift already characterized in Phase 3.3-RD (reduced resource requests, GPU-type composition
shift toward MISC). Every temporal-split number in this report is a description of performance **on that
specific shifted population**, not a general statement about "temporal generalization ability" independent of
what that population looks like. R2's negative paired effect is interpreted in this light: it is a
demonstrated harm on this specific real, shifted evaluation population, not a claim about PCA(2)'s behavior
under distribution shift in general.

## 23. Comparison with Phase 3.1-RD

Phase 3.1-RD established Baseline A and Candidate F (=R0) with a single-representation, unpaired-CI
methodology. This phase reuses that baseline unmodified and adds a paired comparison that the original
Phase 3.1-RD design did not attempt (it had only one candidate to compare, so a baseline-vs-candidate pairing
was implicit in its bootstrap CI, not an explicit paired-difference statistic). No Phase 3.1-RD number changed.

## 24. Comparison with Phase 3.2-RD

Phase 3.2-RD established R0/R1/R2 and interpreted their relationship to Baseline A using independently-computed,
overlapping-CI comparisons (not paired). This phase's paired-difference results are consistent in direction
with every Phase 3.2-RD conclusion but are **more decisive** in two places: (a) Alibaba temporal R2's harm
relative to Baseline A is now a directly-tested, CI-excludes-zero finding rather than an inference from "R2's
point estimate is below 0.5"; (b) AIOps R2's improvement over Baseline A is now shown to be statistically
indistinguishable from zero under a paired test, sharpening Phase 3.2-RD's vaguer "overlapping CIs, inconclusive"
language into an explicit non-finding.

## 25. Comparison with Phase 3.3-RD

Phase 3.3-RD characterized the covariate shift underlying the Alibaba temporal split and offered hypotheses
for R1's improvement / R2's collapse, without re-testing the baseline comparison. This phase supplies that
missing baseline-paired test, confirming (not re-deriving differently) that R0 and R1 both significantly
beat no-signal under the shift while R2 does not merely underperform but actively harms relative to no-signal.

## 26. Comparison with original Phase 3.4

| Field | Content |
|---|---|
| **Original Phase 3.4 result** | Consolidated ranking B > F > E/E′ > D > C > A; F "does not consistently outperform calibrated confidence" (1/6 seeds, paired CI entirely negative); complementarity with B explicitly **not established**; overall verdict **🟡 INCONCLUSIVE**. |
| **Real-data result** | No calibrated-confidence baseline exists to test against (§3) — the real-data track cannot ask "does the candidate beat the strongest reference" in the original's sense, only "does it beat no-signal," which every candidate except AIOps-R2 answers affirmatively, and Alibaba-temporal-R2 answers with a significant **negative** result. |
| **Direction of agreement/disagreement** | **Not directly comparable** for the "beats the strongest baseline" question (no real-data analogue of B exists). Where a comparison IS possible (beats no-signal), the real-data finding is **stronger** than the original's: the original's candidate F beat no-signal 6/6 seeds with CI excluding 0; the real-data candidates mostly replicate that "clearly beats no-signal" pattern, but ALSO surface a failure mode (R2's significant harm) that the original single-representation design never had occasion to discover, since it only ever tested one representation per candidate mechanism. |
| **Confidence/uncertainty** | Alibaba: tight paired CIs, confirmatory-capable. AIOps: wider paired CIs, exploratory, and this phase specifically demonstrates R2's AIOps improvement does not survive the stricter paired test. |
| **Dataset limitations** | Same as prior phases — narrower Alibaba feature set, platform-telemetry-only AIOps features, no AgentRx comparison possible. |
| **Interpretation** | This phase **extends** rather than replicates or contradicts the original Phase 3.4: it answers the "beats baseline" half of the original's question (which real data supports strongly, with one significant exception) while being structurally unable to answer the "beats the strongest reference" half (no such reference exists in real data). The original's caution — that a candidate beating no-signal is not the same as a candidate being ready for deployment — is echoed here even more starkly by R2's Alibaba-temporal result: a candidate can beat no-signal on one population (random split) and be significantly *worse* than no-signal on another (temporal split), a distinction the original synthetic Phase 3.4, evaluated on one fixed benchmark condition, could not have surfaced. |

## 27. Limitations

- No calibrated-confidence-equivalent baseline exists for any real dataset, so the "strongest reference"
  question the original Phase 3.4 answered cannot be asked here at all (§26).
- The paired bootstrap tests one candidate against Baseline A at a time; no paired R0-vs-R1 or R0-vs-R2
  head-to-head test was run (not part of the pre-registered comparison matrix — see §21).
- AIOps's paired test, while more rigorous than Phase 3.2-RD's unpaired framing, still operates on only 43
  independent entities — the R1 result in particular sits close to the CI boundary and should not be treated
  as strong evidence in either direction.
- AgentRx contributes nothing to this phase.

## 28. Implementation issues

- **Solver-level floating-point non-determinism, discovered and characterized in this phase**: re-fitting the
  identical `LogisticRegression` (fixed `random_state=42`, identical input data) in a different process/
  invocation context reproduces the frozen AUROC to within a small but non-zero tolerance, not bit-for-bit.
  Isolated and confirmed **not a logic bug**: the relevant pipeline-construction functions across
  `phase3_1_rd_alibaba_evaluate.py`/`phase3_2_rd_alibaba_evaluate.py` (and the AIOps equivalents) were
  verified to produce byte-identical scores and coefficients (max absolute difference `0.0`) when fit on the
  same data within a single process. The remaining cross-invocation drift (~7e-5 AUROC for Alibaba's single
  fit per split; ~1.1e-3 for AIOps's 43-fit LOEO, where small per-fit drift has more opportunities to
  accumulate) is consistent with floating-point non-associativity in the BLAS/LAPACK routines the `lbfgs`
  solver calls, sensitive to how much other computation ran earlier in the same process. This revises, without
  rewriting, a claim made in the Phase 3.1-RD/3.2-RD reports that results "reproduce bit-for-bit" — that claim
  should be read as "reproduce to within ~1e-3 solver tolerance," which is what was actually verified here.
  The magnitude in every case is one to three orders of magnitude smaller than any effect size this research
  program reports (≥0.02) and changes no qualitative conclusion in any prior phase.
- **A process error**: `scripts/real_data/phase3_1_rd_alibaba_evaluate.py` was run directly during the
  investigation of the above, overwriting the Phase 3.1-RD Alibaba result file. Content was verified
  unchanged (§6). Going forward, no Phase 3.1-RD/3.2-RD/3.3-RD script is re-run directly under this or any
  future phase; verification against frozen results is performed by loading their JSON output only or, where
  score-level recomputation is genuinely needed (as here), by writing to a new phase-specific output path.

## 29. Reproducibility information

- New scripts: `scripts/real_data/phase3_4_rd_alibaba_compare.py`, `scripts/real_data/phase3_4_rd_aiops_compare.py`.
  Both re-derive scores deterministically (fixed seeds throughout) and verify against the frozen Phase
  3.1-RD/3.2-RD result files within the disclosed, justified tolerances (§28) before computing any new
  statistic; both raise `ProtocolDiscrepancyError` and halt on any mismatch beyond tolerance.
- Result artifacts: `experiments/results/phase3_real_data/phase3_4/{alibaba_results.json,aiops_results.json}`,
  each recording the comparison-matrix source, verification mismatches (if any, within tolerance), and full
  bootstrap configuration.
- Provenance preserved: identical processed-data sources, split-membership files, and representation
  definitions as every prior phase; no field stripped or renamed.

---

## What this report does NOT establish

- That R1 is "the best" representation in any general sense — it shows the largest improvement on the
  Alibaba temporal split specifically, under that split's specific distribution shift; no claim is made about
  its performance under any other, untested shift.
- That R2 is unusable in general — it performs comparably to R0/R1 on the Alibaba random split; its failure
  is specific to the temporal (shifted) evaluation.
- Any complementarity or ensembling result — not tested, exactly as the original Phase 3.4 also declined to
  test this (docs/PHASE3_4_COMPARISON.md §12/§18).
- Real-world deployment readiness for any candidate — ranking-quality metrics under a paired statistical test
  are not a substitute for a deployment-context cost/threshold analysis (not run in this phase).

## Files created by this execution

- `configs/phase3_4_rd_comparison_matrix.json`
- `scripts/real_data/phase3_4_rd_alibaba_compare.py`
- `scripts/real_data/phase3_4_rd_aiops_compare.py`
- `experiments/results/phase3_real_data/phase3_4/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_4/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_4_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — new H2-extension/H1-consolidation notes; see that file's Phase 3.4-RD section)

No file outside `configs/`, `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_4/`, and these
two `docs/` files was modified, with the single disclosed exception in §6/§28 (content-verified unchanged).

---

## STOP — Phase 3.4-RD complete

No later phase (3.5-RD, 3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.


---

<a id="phase3-real-data-3-5-report"></a>
# PHASE3 REAL DATA 3 5 REPORT
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_5_REPORT.md`  
**Role:** Real-data Phase 3.5 (attack/generalization) report.

# Phase 3.5-RD — Unseen-Workload Generalization — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.5-RD
execution only (Phase 3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Objective

Determine whether the observed real-data failure-risk signal remains useful when evaluated on
workloads/conditions **entirely absent from the corresponding training population** — a distinct axis from
Phase 3.3-RD's temporal distribution-shift characterization, and from Phase 3.1-RD/3.2-RD/3.4-RD's
entity-level (AIOps LOEO) or split-level (Alibaba random/temporal) evaluations.

## 2. Protocol version

`1.0` — unchanged. New companion config: `configs/phase3_5_rd_generalization_protocol.json`, written and
frozen before any Phase 3.5-RD result was produced.

## 3. Exact definition of generalization used here

"Unseen workload/condition" = a categorical partition, already present in the frozen processed data (not
invented for this phase), along which the train and test populations share **zero** overlap in category
membership. This is the pre-existing-categorical-structure axis the authorization explicitly permitted
("GPU/workload categories; predefined workload groups... other already-existing categorical workload
structure"), used in place of the original Phase 3.5's synthetic attack-perturbation mechanism, which has no
legitimate real-data analogue (§26).

## 4. Pre-registered generalization matrix

Frozen in `configs/phase3_5_rd_generalization_protocol.json` before any evaluation:

- **Alibaba**: hold out `dominant_gpu_type == "T4"` entirely from training.
- **AIOps**: hold out the `db` object-family entirely from training.
- **AgentRx**: `NOT_EVALUABLE` (unchanged blocker, restated §14).

**Category-selection rule, applied identically to both eligible datasets, fixed before evaluation**: hold out
the *largest non-dominant* category — large enough for a statistically usable test population, but not the
dominant category (which would leave too little data to train on). This is a mechanical, symmetric rule, not
a choice made after observing which holdout produces a larger or more interesting effect.

## 5. Dataset eligibility

| Dataset | Eligible categorical field | Eligible? |
|---|---|---|
| Alibaba | `dominant_gpu_type` (6 categories: MISC, T4, P100, V100, V100M32, UNKNOWN) | Yes |
| AIOps | entity object-family (docker/db/os, derived from `cmdb_id` prefix) | Yes |
| AgentRx | none — no categorical workload field exists whose holdout would leave a usable population, and the underlying binary-classification blocker (no negative class) makes the question moot regardless | No — `NOT_EVALUABLE` |

## 6. Independent units

Job (Alibaba). Entity (AIOps, cluster bootstrap over the 13 held-out `db` entities). Not applicable (AgentRx).

## 7. Training populations

- **Alibaba**: all main-tier jobs with `dominant_gpu_type != "T4"` — n=7,938 (of the same, unmodified,
  frozen 10,000-job main-tier sample; no resampling, no new jobs).
- **AIOps**: all `docker`+`os` entities' windows — 30 entities, 170 windows (69 positive, 101 negative) (of
  the same, unmodified, frozen 226-window population; no resampling, no new windows).
- **AgentRx**: not applicable.

## 8. Generalization/test populations

- **Alibaba**: all main-tier jobs with `dominant_gpu_type == "T4"` — n=2,062. Verified programmatically
  (`held_out_category_present_in_train: false`) that T4 does not appear anywhere in the training population.
- **AIOps**: all `db` entities' windows — 13 entities (2 positive-bearing, 11 negative-only), 56 windows (12
  positive, 44 negative). Verified programmatically (`held_out_family_present_in_train: false`).
- **AgentRx**: not applicable.

## 9. Representation definitions

R0 (raw/scaled), R1 (log1p-transformed), R2 (PCA(2)-reduced) — identical, unmodified, frozen in Phase
3.2-RD. No new representation was added; none was dropped.

## 10. Baseline definition

Baseline A (no-signal) — a fixed constant equal to the **training population's** empirical positive
prevalence for this specific generalization condition (Alibaba: 29.9% among non-T4 jobs; AIOps: 40.6% among
docker+os windows), applied unchanged to the held-out test population. No new baseline was introduced; no
calibrated-confidence baseline was substituted (none exists in the real-data track, unchanged since Phase
3.1-RD §15).

## 11. Leakage exclusions

Unchanged: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded from Alibaba;
`pai_group_tag_table`/`pai_machine_spec` remain unavailable and unused; AIOps restricted to platform
telemetry within the frozen PRE-FAILURE window. **New note specific to this phase**: both `dominant_gpu_type`
(Alibaba) and `object` (AIOps) are themselves model input features. Because the held-out category never
appears in training, the fitted `OneHotEncoder` has no learned column for it — held-out test rows receive an
all-zero encoding for that block (`handle_unknown="ignore"`), which is the correct and intended behavior for
a genuine unseen-category test, not a bug: the model has no category-specific learned weight to fall back on
and must generalize from the remaining features alone.

## 12. Alibaba results

| | n | Positive rate | Baseline A AUROC | R0 AUROC | R1 AUROC | R2 AUROC |
|---|---|---|---|---|---|---|
| Train (non-T4) | 7,938 | 29.9% | — | — | — | — |
| Test (T4, unseen) | 2,062 | **10.8%** | 0.500 [0.500,0.500] | 0.571 [0.532,0.609] | 0.550 [0.512,0.587] | 0.509 [0.469,0.550] |

**A striking, unplanned finding surfaced by this condition** (not the generalization question itself, but
directly relevant context for interpreting it): T4-dominant jobs fail at 10.8%, roughly a third the rate of
non-T4 jobs (29.9%). GPU type carries a strong, direct association with the base failure rate — a fact this
phase's design surfaces as a byproduct of partitioning on it, not something searched for.

| Candidate | Paired ΔAUROC vs. Baseline A | 95% CI | Verdict |
|---|---|---|---|
| R0 | +0.071 | [0.032, 0.109] | Significant, but small |
| R1 | +0.050 | [0.012, 0.087] | Significant, but small — CI barely excludes 0 |
| R2 | +0.009 | [−0.031, 0.050] | **Not significant** — CI includes 0 |

## 13. AIOps results

| | n windows | n entities | Positive rate | Baseline A AUROC | R0 AUROC | R1 AUROC | R2 AUROC |
|---|---|---|---|---|---|---|---|
| Train (docker+os) | 170 | 30 | 40.6% | — | — | — | — |
| Test (db, unseen) | 56 | 13 | 21.4% | 0.500 [0.500,0.500] | 0.748 [0.596,0.933] | 0.725 [0.565,0.910] | 0.446 [0.190,0.634] |

**EXPLORATORY** — the held-out population is very small (13 entities, only 2 positive-bearing), and the
bootstrap itself reflects this: only 1,765 of 2,000 resamples produced both classes (235 resamples drew zero
positive entities from the pool of just 2), which is reported transparently, not hidden.

| Candidate | Paired ΔAUROC vs. Baseline A | 95% CI | Verdict |
|---|---|---|---|
| R0 | +0.248 | [0.096, 0.433] | Significant, and a **large** point estimate — but from a tiny, wide-CI test population |
| R1 | +0.225 | [0.065, 0.410] | Significant, similarly wide |
| R2 | −0.054 | [−0.310, 0.134] | **Not significant** — CI includes 0, and the point estimate is negative |

## 14. AgentRx results

**NOT EVALUABLE.** Both frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain zero
trajectories with `num_failures = 0` — the same H1 blocker established in Phase 3.1-RD and reconfirmed every
phase since. No categorical workload field exists whose unseen-holdout could be tested even in principle
without first resolving that structural absence of a negative class. No unannotated trajectory was added; no
substitute task was invented; the two domains remain unpooled.

## 15. AUROC

Reported in full in §12–13. Summary: on Alibaba, R0/R1 show small but statistically real improvements over
no-signal on the unseen-GPU-type population; R2 does not. On AIOps, R0/R1 show large point estimates but with
very wide CIs from a tiny test population; R2 does not improve over no-signal (and its point estimate is
below 0.5).

## 16. AUPRC

Interpreted against each population's own positive prevalence, per the authorization's explicit instruction —
**never compared across the two datasets or across conditions without restating prevalence**:
- Alibaba T4 test: prevalence 10.8%. Baseline A AUPRC 0.108 [0.095,0.121] (as expected, tracks prevalence for
  a constant predictor). R0's AUPRC 0.146 clears this floor modestly; R1 (0.118) and R2 (0.119) barely clear
  it or sit within its CI.
- AIOps db test: prevalence 21.4%. Baseline A AUPRC 0.218 [0.106,0.378] (wide, small-N). R0's AUPRC (0.518)
  and R1's (0.490) clear this floor substantially; R2's (0.331) sits within the baseline's own wide CI —
  consistent with its non-significant AUROC finding.

## 17. Effect sizes

Paired mean differences reported throughout §12–13, computed identically (paired job-level bootstrap for
Alibaba, paired entity-cluster bootstrap for AIOps) to the methodology introduced in Phase 3.4-RD.

## 18. 95% CIs

All reported inline; 2,000 resamples, seed 0, percentile method, at the correct independent-unit level.
AIOps's `n_valid_resamples: 1765` (not 2000) is reported explicitly rather than silently treating it as 2000
— a direct consequence of the tiny (2-entity) positive pool in the held-out population, not a computation
error.

## 19. Distribution-shift context

This is **not** a repeat of Phase 3.3-RD. Phase 3.3-RD characterized the Alibaba **temporal** (Q1–Q3→Q4)
shift — a compound change in label rate, resource-request sizes, and GPU-type mix, with train and test
populations still sharing every GPU-type category, just in different proportions. This phase's Alibaba
condition is structurally different: the T4 category is **completely absent** from training, not merely
underrepresented — a categorical, not proportional, shift. The two are complementary, not duplicative:
Phase 3.3-RD asked "how does performance change when the *mix* of conditions shifts over time," this phase
asks "how does performance hold up on a condition the model never saw at all."

## 20. Positive findings

- On both eligible datasets, R0 and (with a smaller margin) R1 show a statistically real improvement over
  no-signal on an entirely unseen workload category — the failure-risk signal is not purely an artifact of
  having seen every category during training.
- The AIOps db-holdout point estimates (R0 0.748, R1 0.725) are numerically the strongest in this report,
  though this must be read alongside the small-N caveat (§13, §21).

## 21. Negative findings

- **R2 (PCA(2)) shows no statistically distinguishable improvement over no-signal on either dataset's
  unseen-workload test** — CI includes 0 on both Alibaba (T4) and AIOps (db). This is a third, independent
  piece of evidence (alongside Phase 3.2-RD/3.3-RD/3.4-RD's temporal-shift finding) that R2 is the least
  robust of the three representations, now specifically under a categorical-holdout generalization condition
  rather than a temporal one.
- The magnitude of improvement on Alibaba's unseen-GPU-type test (R0 AUROC 0.571) is **substantially smaller**
  than on the random split (0.735) or temporal split (0.793) — the signal generalizes far less completely to
  a truly unseen workload category than it does within a population that shares the same categories, just
  different individual jobs or a different time window.

## 22. Inconclusive findings

- AIOps's large point estimates (R0/R1 ≈ 0.73–0.75) come with CIs wide enough (up to ±0.17 half-width) that
  they should not be read as a confident claim of strong cross-family generalization — the underlying test
  population (13 entities, 2 positive-bearing) is simply too small to support a precise estimate in either
  direction.
- R1's Alibaba paired CI [0.012, 0.087] barely excludes 0 — treated as weak, not strong, evidence.

## 23. NOT_EVALUABLE components

AgentRx (both domains) — §14. The original attack-matrix mechanism itself — §26 (not reproducible on real
data without fabrication, and therefore not attempted in any form, including a diluted or partial version).

## 24. Comparison with Phase 3.1-RD

Phase 3.1-RD established that a supervised signal exists at all (AUROC 0.735 random, 0.793 temporal, 0.646
AIOps LOEO). This phase shows that signal's magnitude is **not uniform across generalization axes** — it
degrades substantially (to 0.51–0.75 depending on dataset and representation) when the test population shares
no categories with training, versus holding up much better (0.72–0.84) when train and test differ only in
time or random assignment but share the same category mix.

## 25. Comparison with Phase 3.2-RD

Phase 3.2-RD established R0≈R1≈R2 on the random split and R1>R0≫R2 on the temporal split. This phase adds a
third data point: on unseen-category generalization, R0 and R1 both show small-to-moderate significant
effects while **R2 shows none** on either dataset — consistent with, and extending, Phase 3.2-RD's finding
that R2 is the least representation-robust choice, now under a condition Phase 3.2-RD never tested.

## 26. Comparison with Phase 3.3-RD

Distinct, complementary axis — see §19. Phase 3.3-RD's compound covariate+label shift and this phase's
categorical holdout are both "distribution shift" in a loose sense but are structurally different
conditions and are not merged or compared numerically against each other in this report.

## 27. Comparison with Phase 3.4-RD

Phase 3.4-RD established, via a paired test, that R2 significantly *harms* relative to no-signal specifically
on the Alibaba temporal split, while R0/R1 significantly help on every condition tested there. This phase's
paired tests show a related but distinct pattern: R2 does not significantly harm on either unseen-workload
condition (both CIs straddle 0, not entirely negative) — R2's failure mode here is "no reliable benefit,"
not "reliable harm," a real and reportable distinction from the temporal-shift finding, not the same result
restated.

## 28. Comparison with original Phase 3.5

| Field | Content |
|---|---|
| **Original Phase 3.5 result** | F (Supervised Failure Risk) survives synthetic covariate-shift attacks (additive noise, feature dropout) on held-out synthetic data without retraining, remaining competitive with (not superior to) calibrated confidence at every severity level; 🟢 GENERALIZATION SUPPORTED, narrowly scoped. |
| **Real-data result** | The original's literal mechanism (synthetic feature perturbation) is **NOT EVALUABLE** on real data — no already-existing real-data analogue of injected noise/dropout exists, and fabricating one is explicitly prohibited. Using the reframed, real, non-synthetic axis this authorization permitted instead (unseen categorical workload), R0/R1 show a real but much smaller generalization margin than on in-distribution splits; R2 shows none. |
| **Direction of agreement/disagreement** | **Not directly comparable** — different mechanism entirely (synthetic post-hoc perturbation vs. real categorical exclusion), explicitly acknowledged rather than forced into a false replication. |
| **Interpretation** | Where a loose qualitative comparison is possible: the original found the frozen candidate "remains competitive... under attack," a relatively strong claim. This phase's real-data finding is more modest — the signal generalizes to an unseen category, but with a visibly smaller effect than in-distribution, and for one representation (R2) with no reliable effect at all. This is reported as a **distinct real-data finding**, not a stronger or weaker version of the original's synthetic-attack result — the two experiments do not test the same thing closely enough to be ranked against each other. |

## 29. Limitations

- Exactly one held-out category per dataset was tested (T4 for Alibaba, `db` for AIOps) — a single
  generalization condition, not a distribution over possible unseen categories. No claim is made about
  whether other categories (e.g., P100, `os`) would generalize similarly; this is explicitly listed as a
  candidate future analysis (§32), not run here to avoid multiplying comparisons.
- The AIOps held-out population is very small (13 entities, 2 positive) — the resulting CIs are wide and the
  bootstrap itself loses ~12% of resamples to single-class draws.
- Both held-out categories were chosen by the same fixed rule (largest non-dominant category) — a defensible,
  pre-registered, symmetric choice, but not necessarily the "hardest" or most representative unseen condition;
  a different rule could plausibly produce a different-magnitude result, and this report does not claim T4/`db`
  are representative of all possible unseen workloads.
- AgentRx contributes nothing to this phase, for the same structural reason as every prior phase.

## 30. Alternative explanations (hypotheses only, per this phase's own findings)

- The large gap between Alibaba's in-distribution performance (AUROC 0.72–0.84) and unseen-category
  performance (0.51–0.57) is consistent with the model relying substantially on GPU-type-correlated signal
  (directly, via the one-hot feature, or indirectly, via other features correlated with GPU-type choice) that
  simply isn't available when the category itself is novel — a plausible, not proven, explanation given the
  striking prevalence difference noted in §12 (10.8% vs. 29.9%).
- R2's consistent lack of a reliable effect across both this phase's conditions and Phase 3.2-RD/3.3-RD/
  3.4-RD's temporal condition may reflect a general fragility of the PCA(2) representation to any distribution
  change (temporal or categorical) rather than a temporal-shift-specific issue — plausible given the breadth
  of conditions under which it now underperforms, but not directly tested by decomposing why (that would be a
  new experiment, listed in §32, not run here).

## 31. Reproducibility information

- New scripts: `scripts/real_data/phase3_5_rd_alibaba_evaluate.py`, `scripts/real_data/phase3_5_rd_aiops_evaluate.py`.
  Both import only the pipeline-construction helpers from the frozen Phase 3.1-RD/3.2-RD modules (never
  executing those modules' own `__main__` blocks, and never writing to their output paths) — per the
  authorization's explicit process-safety rule. Both write exclusively to
  `experiments/results/phase3_real_data/phase3_5/`.
- No historical result file was opened for writing at any point in this phase (unlike Phase 3.4-RD's disclosed
  incident) — verified before finalizing (§Integrity checks).
- Provenance preserved: `dominant_gpu_type`/`object` category membership, train/test population assignment,
  and representation identity are all embedded in the output JSON, sufficient to reconstruct exactly why any
  given job/window was assigned to the seen or unseen population.

## 32. Future experiments (explicitly NOT run — separated from current evidence)

- Repeating the unseen-category test for other categories (Alibaba: P100, V100, V100M32, UNKNOWN; AIOps:
  `os`) to determine whether the T4/`db` results generalize across held-out choices or are specific to those
  two categories.
- A dedicated experiment decomposing *why* R2 fails to generalize reliably across every non-random condition
  tested so far (temporal, unseen-GPU-type, unseen-object-family) — e.g., examining its component loadings
  under each condition.
- A larger AIOps held-out population (if more entities/telemetry become available) to narrow the wide CIs
  observed in §13.
- None of the above informed, or was used to select, any result reported above.

---

## Files created by this execution

- `configs/phase3_5_rd_generalization_protocol.json`
- `scripts/real_data/phase3_5_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_5_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_5/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_5/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_5_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only)

No historical file (Phase 3.1-RD–3.4-RD artifacts, original Phase 3, Phase 4) was opened for writing at any
point in this phase.

---

## STOP — Phase 3.5-RD complete

No later phase (3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.


---

<a id="phase3-real-data-3-6-decision"></a>
# PHASE3 REAL DATA 3 6 DECISION
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_6_DECISION.md`  
**Role:** Real-data Phase 3.6 final decision synthesis -- the document that triggered the Phase 4 pause/reassessment.

# Phase 3.6-RD — Final Decision and Synthesis — Real-Data Phase 3 Replication

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.6-RD
execution only (Phase 4 explicitly not authorized — planning, design, or implementation).

**This is a synthesis phase. No model was trained, no representation was tested, no split was created, and
no dataset was added in the production of this document. Every number below is quoted from a Phase
3.1-RD–3.5-RD result artifact, loaded and verified against the frozen files, not recomputed.**

---

## 1. Objective

Synthesize the complete Phase 3.1-RD–3.5-RD evidence into explicit, mechanically defensible hypothesis
decisions: what does the real-data replication actually allow us to conclude, and what does it not allow us
to conclude?

## 2. Scope

In scope: reading and synthesizing frozen evidence, hypothesis-by-hypothesis decisions, cross-phase and
original-vs-real-data comparison, Phase 4 *recommendations* (not implementation), unified-benchmark
documentation (not publication). Out of scope, and not performed: any new evaluation, model, representation,
split, dataset, or Phase 4 work of any kind.

## 3. Protocol version

`1.0` throughout — `configs/phase3_real_data_protocol.json`, unchanged.

## 4. Frozen evidence inventory

| Phase | Artifact(s) | What it established |
|---|---|---|
| 3.1-RD | `experiments/results/phase3_real_data/phase3_1/{alibaba_results,aiops_results,agentrx_descriptive}.json` | H1: a supervised signal exists (Alibaba, AIOps); AgentRx H1 not executable |
| 3.2-RD | `experiments/results/phase3_real_data/phase3_2/{alibaba_results,aiops_results}.json` | H2: representation robustness on random split, fragility under temporal shift |
| 3.3-RD | `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json` | Characterized the Q1–Q3→Q4 compound covariate+label shift |
| 3.4-RD | `experiments/results/phase3_real_data/phase3_4/{alibaba_results,aiops_results}.json` | Paired baseline comparison; R2's temporal harm confirmed statistically |
| 3.5-RD | `experiments/results/phase3_real_data/phase3_5/{alibaba_results,aiops_results}.json` | Unseen-workload-category generalization; signal weakens substantially, R2 shows no reliable effect |

## 5. Integrity checks

| Check | Result |
|---|---|
| Phase 3.1-RD unchanged | Alibaba random AUROC re-read: `0.7348398689698409` (matches every prior citation) |
| Phase 3.2-RD unchanged | Alibaba temporal R2: `0.39450623763274134` (matches) |
| Phase 3.3-RD unchanged | Label shift figures re-read: `0.20106847984458476` / `0.4341736694677871` (matches) |
| Phase 3.4-RD unchanged | Temporal R2 paired diff: `-0.10549376236725871` (matches) |
| Phase 3.5-RD unchanged | Alibaba T4-holdout n_test: `2062` (matches) |
| Original Phase 3 unchanged | `experiments/results/phase3_1/aggregate_results.json` mtime/content unchanged |
| Phase 4 unchanged | `experiments/results/phase4_0/episodes.json`, `phase4_1/`, `phase4_2/` unchanged |
| Raw data unchanged | No `data/raw/` file accessed this phase (no evaluation script was run) |
| No new evaluation occurred | No script in this phase calls `.fit(`, `predict_proba(`, or any bootstrap resampling loop — verified by inspection of every file created (§Files created) |
| No historical result overwritten | Every historical artifact was opened read-only (`json.load`), never `json.dump`-ed back to its own path |
| All hypotheses represented | H1–H7 all appear in §10 and `configs/phase3_6_rd_decision.json`, including the four marked NOT EVALUABLE |
| All negative/inconclusive/NOT_EVALUABLE findings represented | §14–16 |

No integrity check failed.

## 6. Dataset summary

| Dataset | Domain | Nominal scale | Real evaluated N |
|---|---|---|---|
| Alibaba GPU2020 | Job scheduling/failure | 988,910 eligible jobs | 10,000-job main tier (random split, temporal split, T4-holdout) |
| AIOps 2020 | Microservice fault detection | 81 fault events, 15 telemetry days | 226 windows / 43 entities (LOEO, db-holdout) |
| AgentRx Magentic | LLM agent trajectory diagnosis | 58 trajectories | 44 annotated — NOT_EVALUABLE for binary risk |
| AgentRx τ-Retail | LLM agent trajectory diagnosis | 29 trajectories | 29 annotated — NOT_EVALUABLE for binary risk |

## 7. Independent-unit summary

| Dataset | Unit | Nominal count | Effective count used in inference |
|---|---|---|---|
| Alibaba | job | up to 10,000 | 1,503–2,499 per test population (never job rows counted as anything but 1 unit each) |
| AIOps | entity (`cmdb_id`) | 226 windows | **43 entities** (16 positive-bearing, 27 negative-only) — every bootstrap in every phase resampled at the entity level, never the window level |
| AgentRx | trajectory | 87 total in source files | 44 (Magentic) / 29 (τ-Retail) — never treated as interchangeable, never pooled |

226 AIOps windows were never treated as 226 independent observations at any point in this research program.

## 8. Power/evidence-strength summary

| Condition | Effective N | CI half-width (AUROC) | Confirmatory-capable? |
|---|---|---|---|
| Alibaba random split | 1,503 jobs | ±0.03 | Yes |
| Alibaba temporal split | 2,499 jobs | ±0.02 | Yes (for the metric itself; interpretation constrained by the shift, §H3) |
| Alibaba T4-holdout | 2,062 jobs | ±0.04 | Yes for the paired test, though effect sizes are small |
| AIOps LOEO | 43 entities | ±0.11 | No — exploratory |
| AIOps db-holdout | 13 entities (2 positive) | ±0.17–0.19 | No — exploratory, and `n_valid_resamples` dropped to 1,765/2,000 because some bootstrap draws contained zero positive entities |
| AgentRx | 44 / 29 trajectories | N/A — no classifier exists | Not evaluable |

## 9. Consolidated results table

| Dataset | Condition | Candidate | AUROC | AUPRC | 95% CI (AUROC) | Paired Δ vs. baseline | Type |
|---|---|---|---|---|---|---|---|
| Alibaba | random | Baseline A | 0.500 | 0.259 | [0.500,0.500] | — | Confirmatory |
| Alibaba | random | R0 | 0.735 | 0.537 | [0.703,0.766]* | +0.235 [0.203,0.266] | Confirmatory |
| Alibaba | random | R1 | 0.736 | 0.508 | [0.705,0.767]* | +0.236 [0.205,0.267] | Confirmatory |
| Alibaba | random | R2 | 0.720 | 0.491 | [0.688,0.751]* | +0.220 [0.188,0.251] | Confirmatory |
| Alibaba | temporal | Baseline A | 0.500 | 0.434 | [0.500,0.500] | — | Confirmatory |
| Alibaba | temporal | R0 | 0.793 | 0.635 | [0.774,0.812] | +0.293 [0.274,0.312] | Confirmatory |
| Alibaba | temporal | R1 | 0.843 | 0.735 | [0.826,0.861] | +0.343 [0.326,0.361] | Confirmatory |
| Alibaba | temporal | **R2** | **0.395** | 0.355 | [0.371,0.418] | **−0.105 [−0.129,−0.082]** | Confirmatory — **significant harm** |
| Alibaba | T4-holdout (unseen) | Baseline A | 0.500 | 0.108 | [0.500,0.500] | — | Confirmatory-capable |
| Alibaba | T4-holdout (unseen) | R0 | 0.571 | 0.146 | [0.532,0.609] | +0.071 [0.032,0.109] | Confirmatory-capable |
| Alibaba | T4-holdout (unseen) | R1 | 0.550 | 0.118 | [0.512,0.587] | +0.050 [0.012,0.087] | Confirmatory-capable, small |
| Alibaba | T4-holdout (unseen) | R2 | 0.509 | 0.119 | [0.469,0.550] | +0.009 [−0.031,0.050] | **Not significant** |
| AIOps | LOEO | Baseline A | 0.500 | 0.353 | [0.500,0.500] | — | Exploratory |
| AIOps | LOEO | R0 | 0.647 | 0.573 | [0.536,0.760] | +0.146 [0.036,0.260] | Exploratory |
| AIOps | LOEO | R1 | 0.630 | 0.574 | [0.506,0.749] | +0.130 [0.006,0.249] | Exploratory, borderline |
| AIOps | LOEO | R2 | 0.605 | 0.525 | [0.477,0.728] | +0.105 [−0.023,0.228] | Exploratory — **not significant** |
| AIOps | db-holdout (unseen) | Baseline A | 0.500 | 0.218 | [0.500,0.500] | — | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R0 | 0.748 | 0.518 | [0.596,0.933] | +0.248 [0.096,0.433] | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R1 | 0.725 | 0.490 | [0.565,0.910] | +0.225 [0.065,0.410] | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R2 | 0.446 | 0.331 | [0.190,0.634] | −0.054 [−0.310,0.134] | Exploratory — **not significant** |
| AgentRx | Magentic/τ-Retail | — | — | — | — | — | **NOT EVALUABLE** |

*Alibaba random-split candidate CIs shown are from Phase 3.2-RD's independently-computed (unpaired) bootstrap; the Phase 3.4-RD paired-difference CI is the methodologically stronger figure and is what's reported in the "Paired Δ" column throughout.

No cell was omitted regardless of outcome; R2's negative/non-significant results appear exactly as often as R0/R1's positive ones.

## 10. Hypothesis-by-hypothesis decisions

### H1 — a supervised failure-risk signal exists

1. **Original hypothesis**: a supervised failure-risk signal exists beyond calibrated confidence.
2. **Evidence**: Alibaba random AUROC 0.735 [0.703,0.766]; temporal 0.793 [0.774,0.812]; AIOps LOEO 0.646
   [0.536,0.760]; AgentRx not executable (§14).
3. **Datasets providing evidence**: Alibaba (both splits), AIOps.
4. **Independent N**: 1,503–2,499 jobs (Alibaba); 43 entities (AIOps).
5. **Confirmatory/exploratory**: Alibaba confirmatory-capable; AIOps exploratory.
6. **Effect sizes/CIs**: reported above; all exclude 0.5.
7. **Limitations**: no calibrated-confidence baseline exists in real data — this answers "beats no-signal,"
   a narrower claim than the original's "beats calibrated confidence."
8. **Final status**: **SUPPORTED** (Alibaba, confirmatory precision) / **PARTIALLY SUPPORTED** (AIOps,
   exploratory-only — directionally consistent, not confirmatory) / **NOT EVALUABLE** (AgentRx).

### H2 — mechanism is supervision, not representation

1. **Original hypothesis**: supervised learning, not richer representation, drives the effect.
2. **Evidence**: Alibaba random R0≈R1≈R2 (0.735/0.736/0.720, all overlapping); Alibaba temporal R0=0.793,
   R1=0.843, R2=**0.395** (R2 significantly below baseline, Phase 3.4-RD paired CI [−0.129,−0.082]); AIOps
   R0/R1/R2 overlapping, wide CIs.
3. **Datasets**: Alibaba (both splits), AIOps.
4. **Independent N**: as H1.
5. **Confirmatory/exploratory**: Alibaba confirmatory-capable for both splits; AIOps exploratory.
6. **Effect sizes/CIs**: reported above.
7. **Limitations**: only 3 representations tested; PCA at one dimensionality only.
8. **Final status**: **PARTIALLY SUPPORTED** — holds under i.i.d.-like conditions (random split) but does
   **NOT** hold under real distribution shift (temporal split), where representation choice dominates and
   can actively harm. **INCONCLUSIVE** (AIOps). **NOT EVALUABLE** (AgentRx).

### H3 — concept-drift generalization

1. **Original hypothesis**: the frozen candidate generalizes across concept drift with covariates held fixed.
2. **Evidence**: Alibaba's only real temporal partition (Q1–Q3→Q4) is a **compound** shift — label rate
   20.1%→43.4%, `mean_plan_gpu` 70.5→56.4, `dominant_gpu_type` MISC share 62.1%→80.9% — not a concept-only
   shift like the original's `drift_scale` mechanism.
3. **Datasets**: Alibaba only (descriptive characterization); AIOps/AgentRx not evaluable for this specific
   axis (no frozen temporal partition for AIOps; no timestamps for AgentRx).
4. **Independent N**: 6,177 train / 2,499 test jobs.
5. **Confirmatory/exploratory**: the characterization itself is descriptive, not a point-estimate hypothesis
   test in the original's sense.
6. **Effect sizes/CIs**: not applicable to the characterization itself; the associated R0/R1/R2 temporal
   results are reported under H1/H2 above.
7. **Limitations**: exactly one real train/test temporal partition exists — no repeated-shift design as the
   original's `drift_scale` sweep allowed.
8. **Final status**: **NOT DIRECTLY COMPARABLE** — different shift type (concept-only vs. compound
   concept+covariate); the real evidence neither replicates nor contradicts the original, it tests a
   structurally different condition. AIOps/AgentRx **NOT EVALUABLE**.

### H4 — covariate-shift / attack generalization

1. **Original hypothesis**: the frozen candidate survives synthetic feature-noise/dropout attacks, remaining
   competitive with calibrated confidence.
2. **Evidence**: the literal mechanism (synthetic feature corruption) is **NOT EVALUABLE** on real data — no
   real-data analogue exists and fabricating one is prohibited. The reframed, real, non-synthetic axis
   (unseen-workload-category holdout) shows: Alibaba T4-holdout R0 AUROC 0.571 (paired Δ +0.071
   [0.032,0.109]), R1 0.550 (+0.050 [0.012,0.087]), R2 0.509 (+0.009 [−0.031,0.050], not significant); AIOps
   db-holdout R0 0.748 (+0.248 [0.096,0.433]), R1 0.725 (+0.225 [0.065,0.410]), R2 0.446 (−0.054
   [−0.310,0.134], not significant).
3. **Datasets**: Alibaba, AIOps (exploratory).
4. **Independent N**: 2,062 jobs (Alibaba); 13 entities (AIOps).
5. **Confirmatory/exploratory**: Alibaba paired test is precise enough to distinguish small effects;
   AIOps is exploratory with very wide CIs.
6. **Effect sizes/CIs**: reported above.
7. **Limitations**: one held-out category per dataset, chosen by a fixed a priori rule, not a sweep.
8. **Final status**: **PARTIALLY SUPPORTED** for R0/R1 (small but real margin over no-signal on an entirely
   unseen category, on both datasets); **NOT SUPPORTED** for R2 (no significant effect on either dataset);
   **NOT DIRECTLY COMPARABLE** to the original's specific synthetic-attack mechanism. AgentRx **NOT
   EVALUABLE**.

### H5a — complementarity (does the signal add value beyond calibrated confidence)

1. **Original hypothesis**: does Failure Risk add information beyond calibrated confidence?
2. **Evidence**: none generated — no calibrated-confidence baseline exists anywhere in the real-data track,
   so there was never a second signal to test complementarity against.
3. **Datasets**: none.
4. **Final status**: **NOT EVALUABLE** — structural, not a result of any test that was run and came back
   negative.

### H5b — decision-cost policy

1. **Original hypothesis**: does converting risk scores into decisions (answer/review/abstain) produce a
   favorable cost outcome relative to doing nothing?
2. **Evidence**: none generated — no real, disclosed deployment cost model exists for any of the three
   datasets, and none was fabricated.
3. **Final status**: **NOT EVALUABLE**.

### H6 — diagnosis

1. **Original hypothesis**: can the pipeline diagnose the cause of a failure/anomaly?
2. **Evidence**: none generated in Phase 3.1-RD–3.5-RD. This is distinct from H5a/H5b/H7: AgentRx's organic
   `root_cause_failure_id`/`root_cause_reason` fields and AIOps's injected fault categories **do exist** and
   were explicitly preserved for this purpose in the frozen protocol (`docs/PHASE3_REAL_DATA_PROTOCOL.md`
   §3), but no authorized phase in this research program (protocol design through 3.6-RD synthesis) included
   running a diagnosis experiment.
3. **Final status**: **NOT EVALUABLE** — not attempted, not blocked by data unavailability. This is the one
   hypothesis in this table where the gap is scope, not data.

### H7 — recovery

1. **Original hypothesis**: can the pipeline recover from a diagnosed failure, and does that recovery help?
2. **Evidence**: none — no dataset (Alibaba, AIOps, AgentRx) records a recovery action or outcome field.
3. **Final status**: **NOT EVALUABLE / STRUCTURAL GAP** — no future phase can evaluate this under the
   currently held data without new data acquisition.

## 11. Original Phase 3 vs. real-data Phase 3 comparison

| Hypothesis | Relationship |
|---|---|
| H1 | Real data **extends** the original — same qualitative "beats no-signal" conclusion holds on Alibaba (confirmatory) and AIOps (exploratory); cannot be compared on the original's specific "beats calibrated confidence" framing since no such baseline exists in real data. |
| H2 | **Partially replicated** on the random split (representation-agnostic, as originally found); **newly discovered boundary condition** on the temporal split (representation sensitivity under real shift) that the original's single-condition synthetic design never had the opportunity to surface. |
| H3 | **Not directly comparable** — different shift type entirely (compound real shift vs. controlled concept-only synthetic shift). |
| H4 | **Not directly comparable** on mechanism (real categorical holdout vs. synthetic feature perturbation); where a loose qualitative comparison is possible, real data shows a smaller, more representation-dependent margin than the original's "remains competitive" finding. |
| H5a/H5b | **Not evaluable** — no real-data version of this question was ever askable, so no comparison to the original's INCONCLUSIVE finding is possible. |
| H6 | **Not evaluable** — not attempted, no comparison to the original's 0.683 pooled accuracy is possible yet. |
| H7 | **Not evaluable** — the original's own INCONCLUSIVE finding (0% successful reconfiguration recovery) has no real-data counterpart to compare against. |

No relationship above claims real data "disproved" or "validated" the original beyond what the actual
evidence in §10 supports.

## 12. Strongly supported findings

- A real, statistically clear supervised failure-risk signal exists in the Alibaba GPU2020 job-scheduling
  domain, at confirmatory-capable precision, on both a random and a temporal held-out population (§H1).
- Representation choice (R0 vs. R1 vs. R2) makes little difference under i.i.d.-like (random-split)
  conditions on Alibaba (§H2).

## 13. Partially supported findings

- The signal generalizes to entirely unseen GPU-type/object-family categories, but with a substantially
  smaller margin than in-distribution performance (§H4).
- The signal exists on AIOps, but only at exploratory precision — directionally consistent evidence, not
  confirmatory (§H1, §H4).

## 14. Negative findings (first-class results, not omitted)

- **R2 (PCA(2)) collapses to AUROC 0.395 — significantly WORSE than no-signal — on the Alibaba temporal
  split** (paired diff −0.105, CI [−0.129,−0.082]) (Phase 3.2-RD/3.4-RD).
- **R2 shows no statistically distinguishable improvement over no-signal under either unseen-workload
  condition tested** (Alibaba T4-holdout, AIOps db-holdout) (Phase 3.5-RD).
- The failure-risk signal's magnitude drops substantially under genuine unseen-workload-category
  generalization relative to in-distribution splits (Alibaba: 0.51–0.57 vs. 0.72–0.84) (Phase 3.5-RD).
- No calibrated-confidence-equivalent baseline exists anywhere in the real-data track — a structural
  limitation present since Phase 3.1-RD, not resolved by any subsequent phase.
- AgentRx's binary failure-risk task is not executable on either frozen sample — present since Phase 3.1-RD,
  unresolved by design (no unannotated trajectories were added to manufacture a negative class).

## 15. Inconclusive findings

- AIOps R2 vs. no-signal, both in the primary LOEO evaluation (Phase 3.1-RD/3.2-RD/3.4-RD, paired CI
  [−0.023,0.228]) and under unseen-family generalization (Phase 3.5-RD, CI [−0.310,0.134]).
- AIOps R1's improvement over no-signal is real but sits close to the CI boundary in more than one phase
  (Phase 3.4-RD paired [0.006,0.249]; Phase 3.5-RD unseen-family [0.065,0.410]) — treated as weak, not
  strong, evidence throughout.
- Whether R2's fragility reflects a general property of PCA(2) under any distribution change, or something
  specific to the particular shifts tested, remains open (§21 alternative explanations, carried from Phase
  3.3-RD/3.5-RD, not resolved here).

## 16. NOT_EVALUABLE findings

- AgentRx: H1–H4 (no negative class in either frozen sample).
- H5a (complementarity): no calibrated-confidence baseline exists.
- H5b (decision-cost policy): no real cost model exists or was fabricated.
- H6 (diagnosis): not attempted in any authorized phase, despite existing usable fields.
- H7 (recovery): no dataset records a recovery outcome.

## 17. Newly discovered findings (not present in, or not derivable from, the original Phase 3)

- **Representation sensitivity that only emerges under real distribution shift** — the original synthetic
  Phase 3.2/3.2C found representation-agnostic behavior and never tested it under a shifted condition; real
  data shows this agnosticism does *not* extend to distribution shift.
- **A candidate representation can be significantly worse than doing nothing** (R2 on Alibaba temporal) — no
  analogous result exists anywhere in the original Phase 3, where the weakest candidate (original Failure
  Memory) underperformed no-signal on AURC but was never shown to be *significantly* worse on AUROC via a
  paired test.
- **GPU-type carries a strong, direct association with job failure rate** (T4 jobs fail at 10.8% vs. 29.9%
  for non-T4) — an incidental finding surfaced by the Phase 3.5-RD holdout design, not something the original
  synthetic benchmark could have produced (it has no analogous categorical structure).
- **The signal's generalization margin is substantially smaller for genuinely unseen categories than for
  unseen time periods** — a distinction between two kinds of "generalization" that the original single-axis
  (concept-drift-only) Phase 3.3 design never had the structure to reveal.

## 18. Limitations

- No calibrated-confidence baseline exists in the real-data track, permanently narrowing every H1/H4/H5a
  comparison relative to the original's framing.
- AIOps's exploratory status (43 independent entities) means several results in this report (R1's marginal
  significance, R2's non-significance) could plausibly flip with a larger real dataset — this is disclosed,
  not treated as settled.
- AgentRx contributed zero quantitative evidence to this entire research program (Phase 3.1-RD–3.5-RD) due to
  its frozen sample's all-positive composition.
- Only one held-out condition per generalization axis was tested (one temporal split, one unseen GPU
  category, one unseen object family) — none of these are a sweep over the space of possible shifts/unseen
  conditions.

## 19. Structural gaps

H5a, H5b, H7 (§16) — these cannot be resolved by re-running anything in the current research program; they
require either new data (H7's recovery outcomes) or a real cost/baseline model that does not currently exist
(H5a, H5b) and was correctly not fabricated at any point.

## 20. Scientific interpretation

Real data both **confirms and complicates** the original Phase 3's central finding. It confirms that a
supervised classifier finds real, useful signal in operational failure data (H1) and that this signal is not
purely an artifact of representation choice under stable conditions (H2, random split). It complicates the
original's implicit assumption (never directly tested there, since only one representation was ever
evaluated under drift) that representation choice is a minor implementation detail: under real distribution
shift — whether temporal (Phase 3.3-RD/3.4-RD) or categorical (Phase 3.5-RD) — representation choice becomes
a first-order factor, capable of turning a working signal into an actively harmful one (R2). No claim is made
that this generalizes beyond the three representations and the specific real datasets tested here.

## 21. Phase 4 implications — recommendations for later planning (NOT implemented here)

These are recommendations only. No Phase 4 file was read, modified, or planned in detail as part of this
phase.

- **Regime/context awareness**: the real-data findings suggest that a failure-risk signal's reliability is
  not uniform across operating conditions — it degrades under both temporal shift and unseen-category
  conditions, and for at least one representation, can become actively counterproductive. Phase 4's failure
  memory / pattern-discovery components may need a mechanism to assess whether the current operating regime
  resembles the regime in which a stored failure experience was learned, before treating that experience as
  applicable — this is a direct, explicit implication of the R2-temporal-collapse and unseen-category-margin
  findings (Phase 3.2-RD/3.4-RD/3.5-RD), not a generic caution.
- **Distribution-shift awareness**: any Phase 4 component that reuses a fitted risk model across time or
  across workload categories should have a way to detect when it is operating outside the population it was
  validated on, given how differently R0/R1/R2 behaved between in-distribution and shifted/unseen conditions
  in this report.
- **Uncertainty estimation**: given how wide AIOps's confidence intervals are at 43 independent entities,
  Phase 4 components trained or validated on similarly small real populations should propagate that
  uncertainty rather than treating a point estimate as settled.
- **Abstention/safety gating**: the original Phase 3.6 found autonomous decision authority "not justified"
  even on synthetic data with a working signal; the real-data finding that a representation can be
  significantly *harmful* under shift (not just unhelpful) is an additional, concrete reason for caution
  before Phase 4 grants any automated system decision authority based on a fitted risk score without a
  shift-detection or abstention safeguard.
- **Memory applicability checks**: if Phase 4's failure memory stores experiences keyed partly by context
  (e.g., workload/GPU-type/time), the H2/H4 findings here directly motivate checking that a retrieved
  experience's context resembles the current context before applying it — retrieving an experience from a
  now-absent regime (analogous to this report's T4/db holdouts) produced a measurably weaker, sometimes null,
  signal.
- **No change needed**: nothing in this report suggests the core Phase 4.0/4.1/4.2 architecture (episodic
  data capture, failure memory, pattern discovery) is fundamentally unsound — the findings bear on *when* a
  stored experience should be trusted, not on whether storing and retrieving experiences is a reasonable
  design.

## 22. Future experiments (documented, not performed)

- H6 (diagnosis) on AgentRx's organic root-cause fields and AIOps's injected fault categories — data exists,
  scope did not include running it.
- A sweep over additional unseen-category holdouts (Alibaba: P100, V100, V100M32, UNKNOWN; AIOps: `os`) to
  determine whether the T4/`db` findings generalize across held-out choices.
- A dedicated mechanistic investigation of R2's fragility (e.g., PCA component loadings pre/post shift).
- A larger AIOps population, if more real fault/telemetry data becomes available, to narrow the wide CIs
  throughout this report.
- Any H5a/H5b/H7-equivalent experiment, contingent on acquiring a real cost model or recovery-outcome data
  that does not currently exist.

None of the above was performed in this phase, and none influenced any decision in §10.

## 23. Unified benchmark/dataset implications

Per every prior phase's preserved-field discipline, the eventual unified real-world benchmark should
continue to preserve, without forcing a common schema across datasets that don't naturally share one:

- **Common (cross-dataset) fields**: `source_dataset`, `source_record_id` (native: `job_name` / fault-log
  `index` / `trajectory_id`), `independent_unit_type` (job / entity / trajectory — explicit, not assumed),
  `split_membership` (including which generalization condition, e.g. "T4-holdout-test", a record belongs to),
  `label_provenance` (observed outcome / injected fault / organic annotation), `processing_version`,
  `representation_version` (R0/R1/R2 or future additions), `data_quality_flags`.
- **Dataset-specific fields, preserved not discarded**: Alibaba's `dominant_gpu_type`/machine-spec fields;
  AIOps's `cmdb_id` object-family and telemetry-coverage flags; AgentRx's `num_failures`/`failure_categories`/
  `root_cause_*` fields (with an explicit flag that these represent 100%-failure-composition samples, not a
  representative failure-rate population).
- **Explicit MISSING markers**, never imputed values, where a dataset structurally lacks a field another
  dataset has (e.g., AgentRx has no timestamp field at all).
- **This report adds one new preservation requirement**: for any future evaluation using a leave-category-out
  design (as Phase 3.5-RD did), the held-out category identity and the selection rule that chose it must be
  recorded alongside the split — reconstructing *why* a category was excluded, not just that it was.

No data was published or uploaded in this phase.

## 24. Reproducibility/provenance

Every number in this document was loaded via `json.load` from an existing frozen artifact and printed for
verification before being written here — no value was retyped from memory without a corresponding artifact
read in this phase's session. `configs/phase3_6_rd_decision.json` records the same evidence in
machine-readable form.

## 25. Final decision table

| Hypothesis | Original Phase 3 | Real-data evidence | Dataset(s) | Effective N | Evidence type | Final status | Key limitation |
|---|---|---|---|---|---|---|---|
| H1 | F beats no-signal 6/6 seeds, AUROC 0.6548 | AUROC 0.735 (random), 0.793 (temporal), 0.646 (AIOps) | Alibaba, AIOps | 1,503–2,499 jobs; 43 entities | Confirmatory (Alibaba); Exploratory (AIOps) | **SUPPORTED** (Alibaba) / **PARTIALLY SUPPORTED** (AIOps) / **NOT EVALUABLE** (AgentRx) | No calibrated-confidence baseline exists in real data |
| H2 | Supervision, not representation, is the mechanism | Robust on random split; R2 collapses under temporal shift | Alibaba, AIOps | as H1 | Confirmatory (Alibaba); Exploratory (AIOps) | **PARTIALLY SUPPORTED** (Alibaba) / **INCONCLUSIVE** (AIOps) / **NOT EVALUABLE** (AgentRx) | Only 3 representations tested |
| H3 | Generalizes across concept-only drift | Q1–Q3→Q4 is a compound concept+covariate shift | Alibaba (descriptive) | 6,177/2,499 | Descriptive | **NOT DIRECTLY COMPARABLE** | Single real temporal partition |
| H4 | Robust to synthetic covariate-shift attacks | Real unseen-category holdout: small real margin for R0/R1, none for R2 | Alibaba, AIOps | 2,062 jobs; 13 entities | Confirmatory-capable (Alibaba); Exploratory (AIOps) | **PARTIALLY SUPPORTED** (R0/R1) / **NOT SUPPORTED** (R2) / **NOT DIRECTLY COMPARABLE** to original mechanism | Single held-out category per dataset; literal mechanism not reproducible |
| H5a | F adds no value beyond B | No real baseline to test against | None | — | — | **NOT EVALUABLE** | Structural — no calibrated-confidence analogue |
| H5b | Risk policies cost less than nothing at base ratio, more at stricter ratio | No real cost model | None | — | — | **NOT EVALUABLE** | No cost model exists |
| H6 | Diagnosis accuracy 0.683 | Not attempted | None (data exists, unused) | — | — | **NOT EVALUABLE** | Scope gap, not data gap |
| H7 | 0% successful reconfiguration recovery | No recovery data | None | — | — | **NOT EVALUABLE / STRUCTURAL GAP** | No dataset records recovery outcomes |

## 26. Final research conclusions

The real-data replication of Phase 3 finds genuine, statistically supported evidence that a supervised
failure-risk signal exists in real operational data (Alibaba GPU scheduling, more tentatively AIOps
microservice telemetry), reproducing the qualitative core of the original synthetic finding. It does **not**
find that this signal, or the representation used to compute it, is uniformly robust: under real distribution
shift — whether across time or across previously-unseen workload categories — both the signal's strength and
its representation-dependence change substantially, and at least one tested representation (PCA(2)) can
become actively harmful rather than merely unhelpful. Four hypotheses (H5a, H5b, H6, H7) remain unevaluated —
three for structural reasons (no comparable baseline, no cost model, no recovery data) and one (H6) purely
because it was never attempted despite usable data existing. AgentRx contributed no quantitative evidence to
any hypothesis in this program due to its frozen sample's all-positive composition. These findings — positive,
negative, and unevaluated alike — are reported as the complete, honest state of the evidence; no result was
suppressed, and no hypothesis's status was inflated beyond what its confidence interval and independent
sample size support.

---

## Files created by this execution

- `configs/phase3_6_rd_decision.json`
- `docs/PHASE3_REAL_DATA_3_6_DECISION.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — final synthesis section)

No historical file (Phase 3.1-RD–3.5-RD artifacts, original Phase 3, Phase 4) was opened for writing at any
point in this phase. No evaluation script was executed.

---

## STOP — Phase 3.6-RD complete. Real-data Phase 3 replication research program complete pending review.

Phase 4 was not started, modified, planned in implementation detail, or touched in any way. Awaiting separate
review and explicit authorization before any Phase 4 work begins.


---

<a id="phase3-real-data-comparison"></a>
# PHASE3 REAL DATA COMPARISON
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_COMPARISON.md`  
**Role:** Cross-dataset real-data comparison summary.

# Phase 3 Real-Data Comparison — Original vs. Real-Data Findings

**Scope of this document**: only hypotheses with a result actually produced by executed real-data work are
recorded here. As of this update, that is **Phase 3.1-RD and Phase 3.2-RD**
(`docs/PHASE3_REAL_DATA_3_1_REPORT.md`, `docs/PHASE3_REAL_DATA_3_2_REPORT.md`, both 2026-08-13). H3–H7 have
no real-data result yet (Phase 3.3-RD…3.6-RD are not authorized) and are listed as `NOT YET RUN`, not as
findings.

This document does not modify, reinterpret, or re-score `docs/PHASE3_4_COMPARISON.md` or any other original
(synthetic) Phase 3 file. Original results below are quoted verbatim from the frozen reports.

---

## H1 — a supervised failure-risk signal exists beyond calibrated confidence

| Field | Content |
|---|---|
| **Original Phase 3 result** | Candidate F (`Phase2RepresentationSupervisedRisk`, established in Phase 3.2C): aggregate AUROC **0.6548** [0.6159, 0.6938] on synthetic regimes 3+4, beating Baseline A (no-signal, 0.5000) at 6/6 seeds. (Source: `docs/PHASE3_2C_CANDIDATE_ABLATION.md`, `docs/PHASE3_4_COMPARISON.md`.) |
| **Real-data result — Alibaba, random split** | Candidate F AUROC **0.735** [0.703, 0.766] vs. Baseline A 0.500 [0.500, 0.500]. n=1,503 test jobs. |
| **Real-data result — Alibaba, temporal split** | Candidate F AUROC **0.793** [0.774, 0.812] vs. Baseline A 0.500 [0.500, 0.500]. n=2,499 test jobs (Q4, base rate 43.4% vs. 20.1% in train). |
| **Real-data result — AIOps** | Candidate F (LOEO) AUROC **0.646** [0.536, 0.760] vs. Baseline A 0.500 [0.500, 0.500]. n=226 windows / 43 entities. **EXPLORATORY.** |
| **Real-data result — AgentRx (Magentic, τ-Retail)** | **NOT EVALUABLE.** Every trajectory in both frozen samples (44 Magentic, 29 τ-Retail) has ≥1 recorded failure — no negative class exists to build a binary risk classifier against. |
| **Direction of agreement/disagreement** | **Agrees directionally** on Alibaba (both splits) and AIOps: a supervised model exceeds no-signal by a wide margin in every case a comparison could be made. **Cannot adjudicate** on AgentRx. |
| **Confidence/uncertainty** | Alibaba: tight CIs, confirmatory-capable precision (CI half-widths ≈0.02–0.03 AUROC). AIOps: wide CI (half-width ≈0.11), exploratory only. AgentRx: no estimate exists. |
| **Dataset limitations** | Alibaba result is built on a narrower feature set than fully allowed (no `group_tag`/`machine_spec`/`user` — §8 of the 3.1-RD report) and on a fundamentally different prediction target (direct job-outcome prediction, not meta-level "will an upstream classifier be wrong" prediction — see interpretation below). AIOps result rests on only 43 independent entities. AgentRx result does not exist. |
| **Interpretation** | The real-data evidence **strengthens** the qualitative claim that a supervised failure-risk signal exists and clearly exceeds a no-signal baseline — this direction holds on every real dataset where a comparison was possible. The *magnitude* is **not comparable** across original and real-data results: the original Phase 3.1 task (predicting an upstream classifier's own errors) and the Alibaba/AIOps real-data tasks (predicting a job's or a service's actual failure outcome) are different prediction problems with different intrinsic difficulty. A higher real-data AUROC is not evidence the original synthetic result was too conservative, and a lower one would not have been evidence it was too optimistic — the tasks simply are not the same task. AgentRx's inability to run at all is itself informative: it shows the original H1 framing (binary failure occurrence) does not transfer cleanly to a dataset where the sampling process (annotate-because-a-failure-was-observed) makes failure occurrence deterministic within the annotated set. |

---

## H2 — mechanism is supervision, not representation

| Field | Content |
|---|---|
| **Original Phase 3 result** | Phase 3.2/3.2C: supervision, not representation, was the operative mechanism. A fixed/unlearned rule on a richer k-NN representation showed ~no signal (AUROC 0.5073); supervised learning on the *old, unmodified* PCA representation matched the richer-representation candidate (0.6548 vs. 0.5809), isolating supervision as the cause (`docs/PHASE3_2C_CANDIDATE_ABLATION.md`). |
| **Real-data result — Alibaba, random split** | Robust to representation: R0 (raw/scaled) 0.735 [0.703,0.766], R1 (log1p) 0.736 [0.705,0.767], R2 (PCA(2)) 0.720 [0.688,0.751] — all statistically indistinguishable. |
| **Real-data result — Alibaba, temporal split** | **Not robust to representation**: R0 0.793 [0.774,0.812], R1 0.843 [0.826,0.861] (materially higher, non-overlapping CI), R2 **0.395 [0.371,0.418]** (collapses below no-signal). |
| **Real-data result — AIOps** | R0 0.646 [0.536,0.760], R1 0.630 [0.506,0.749], R2 0.605 [0.477,0.728] — overlapping CIs, inconclusive; R2's CI includes 0.5. **EXPLORATORY.** |
| **Real-data result — AgentRx (Magentic, τ-Retail)** | **NOT EVALUABLE** — the frozen protocol's hypothesis-dataset mapping already marked H2 as `NOT_EVALUABLE` for both domains before Phase 3.1-RD ran, and Phase 3.1-RD's H1 blocker (no negative class) independently rules out any supervised classifier to test representation-robustness of. |
| **Direction of agreement/disagreement** | **Partially agrees, partially cannot generalize**: on Alibaba's random split, representation choice indeed makes little difference — consistent with the original's "supervision, not representation, is what matters." On Alibaba's temporal (distribution-shifted) split, representation choice matters a great deal, to the point of inverting a strong signal into a below-no-signal one for PCA(2) — a combination (representation × distribution shift) the original Phase 3.2/3.2C work never tested, so this does not contradict a specific original claim but does show the original conclusion should not be assumed to extend to a shifted-distribution setting. AIOps and AgentRx **cannot adjudicate**. |
| **Confidence/uncertainty** | Alibaba: tight CIs on both splits (confirmatory-capable precision); the temporal-split R2 result is a tight CI around a genuinely adverse point estimate, not a noisy one. AIOps: wide, overlapping CIs, exploratory only. AgentRx: no estimate exists. |
| **Dataset limitations** | Same feature-completeness limitations as H1 (§9 of the 3.2-RD report). Only 3 pre-registered representations were tested; PCA was tested only at n_components=2 (matching original methodology, not tuned) — no claim is made about PCA at other dimensionalities. |
| **Interpretation** | Real-data evidence **partially supports** the original H2 finding under i.i.d.-like conditions (Alibaba random split) but reveals a **boundary condition the original synthetic work did not examine**: under real distribution shift, representation choice can dominate the result, including producing a representation that actively hurts (PCA(2) on the Alibaba temporal split). This is reported as a genuine extension/complication of the original finding, not a contradiction of it, and not forced into agreement. Full detail in `docs/PHASE3_REAL_DATA_3_2_REPORT.md` §17. |

## H3 — concept-drift generalization

| Field | Content |
|---|---|
| **Original Phase 3 result** | Phase 3.3: the frozen Candidate F representation generalized across a **fixed-covariate-distribution, concept-only** drift axis (`drift_scale` varied at test time only): AUROC 0.698 (weaker drift, 0.5×), 0.655 (original), 0.602 (stronger drift, 2×) — all well above no-signal, all tracking the calibrated-confidence baseline within ~0.005 AUROC (`docs/PHASE3_3_GENERALIZATION.md`). Explicitly scoped as concept-drift-only, not covariate-shift. |
| **Real-data result — Alibaba, temporal split (Q1–Q3 train → Q4 test)** | R0 AUROC 0.793 [0.774,0.812], R1 0.843 [0.826,0.861], R2 0.395 [0.371,0.418] — reused verbatim from Phase 3.2-RD, now characterized (Phase 3.3-RD) against a **newly documented compound shift**: failure rate 20.1%→43.4% *and* a genuine covariate shift (mean/median resource-request sizes drop, dominant GPU type shifts from 62.1%→80.9% MISC). See `docs/PHASE3_REAL_DATA_3_3_REPORT.md` §9. |
| **Real-data result — AIOps** | **NOT EVALUABLE FOR THIS GENERALIZATION ANALYSIS** — no frozen train/test temporal partition exists for AIOps; one was not manufactured for this purpose. |
| **Real-data result — AgentRx** | **NOT EVALUABLE** — no timestamps exist in either domain (established in the frozen protocol), and no supervised classifier exists to test generalization of in the first place (H1 blocker). |
| **Direction of agreement/disagreement** | **Not directly comparable**, not replicated/contradicted. The original H3 experiment and this real-data result probe structurally different conditions: the original held covariates fixed and varied only the drift-generating relationship; the real Q1–Q3→Q4 split varies covariates *and* label rate simultaneously, and Phase 3.2-RD already showed representation choice interacts strongly with it (a factor the original's single-representation design never had occasion to surface). |
| **Confidence/uncertainty** | Alibaba: tight CIs (reused from Phase 3.2-RD, confirmatory-capable precision). The distribution-shift characterization itself (§9 of the 3.3-RD report) is descriptive, not an estimated quantity with its own CI. |
| **Dataset limitations** | Exactly one real train/test temporal partition exists (no repeated-shift design), so precision of "how generalization degrades with shift magnitude" (which the original could vary via `drift_scale`) cannot be assessed on real data the way it could on synthetic data. |
| **Interpretation** | The real-data evidence **cannot adjudicate** the original H3 finding directly — different shift type, different design. What it *does* newly show, which the original could not: under a real, compound (concept+covariate) shift, whether a supervised signal "generalizes" depends materially on representation choice (R1 improves, R2 collapses below no-signal) — a qualification of the general claim "the signal generalizes across drift" that only a multi-representation real-data design could reveal. This is reported as a genuine extension, not a contradiction, of the original's narrower (single-representation, concept-only) finding. Full detail in `docs/PHASE3_REAL_DATA_3_3_REPORT.md` §15–17. |

## Phase 3.4-RD — consolidated baseline-vs-candidate comparison (cross-cutting, not one H-hypothesis)

Mirroring the original (synthetic) Phase 3.4's design, this is a **consolidation phase, not a new
hypothesis test** — no new model was fit; Phase 3.1-RD's Baseline A and Phase 3.2-RD's R0/R1/R2 were
compared under a properly *paired* bootstrap (same test-set rows/entities resampled jointly for baseline and
candidate), which is statistically stronger than the unpaired, overlapping-CI comparisons used in Phase
3.1-RD/3.2-RD/3.3-RD.

| Field | Content |
|---|---|
| **Original Phase 3.4 result** | Consolidated ranking B (calibrated confidence) > F (selected candidate) > E/E′ > D > C > A (no signal). F beats no-signal 6/6 seeds (CI excludes 0) but does **not** consistently beat calibrated confidence (1/6 seeds, paired CI entirely negative). Complementarity with B explicitly not tested. Overall verdict: 🟡 INCONCLUSIVE. |
| **Real-data result** | No calibrated-confidence analogue exists in the real-data track, so the original's central question ("does the candidate beat the strongest reference") cannot be asked here — only "does it beat no-signal" (§26 of `docs/PHASE3_REAL_DATA_3_4_REPORT.md`). Answer, using a proper paired test: **yes, significantly**, for R0/R1 on both Alibaba splits and (at exploratory precision) on AIOps; **R2 significantly beats no-signal on the Alibaba random split but is significantly WORSE than no-signal on the Alibaba temporal split** (paired ΔAUROC −0.105, CI [−0.129,−0.082], entirely negative); AIOps R2's apparent edge over no-signal does not survive the paired test (CI includes 0). |
| **Direction of agreement/disagreement** | **Not directly comparable** on the "beats the strongest baseline" question (structural — no such baseline exists in real data). Where comparable ("beats no-signal"), real data **extends** the original's finding: most candidates replicate "clearly beats no-signal," but the real, multi-representation, multi-split design additionally surfaces a failure mode (R2's significant *harm* under distribution shift) the original single-representation, single-condition design could not have discovered. |
| **Interpretation** | This is reported as an extension of the original's cautionary conclusion, not a contradiction: the original warned that "beats no-signal" is not the same as "ready for deployment" (it fell short of showing F beats the strongest reference); the real-data result makes essentially the same caution more concrete by showing a candidate can beat no-signal on one population and actively harm relative to it on another. Full detail: `docs/PHASE3_REAL_DATA_3_4_REPORT.md`. |

## H4 — covariate-shift / attack generalization

| Field | Content |
|---|---|
| **Original Phase 3.4/3.5 note** | H4 in the frozen protocol's hypothesis-dataset mapping refers to "covariate-shift / attack generalization" — the original Phase 3.5's synthetic attack matrix (additive noise, feature dropout) on already-generated held-out synthetic samples. See `docs/PHASE3_5_ATTACK_GENERALIZATION.md`. |
| **Real-data result** | The literal mechanism is **NOT EVALUABLE** on real data — no already-existing real-data analogue of injected feature corruption exists, and fabricating one (synthetic noise/dropout on real Alibaba/AIOps records) is explicitly prohibited by this track's research-integrity rules. Phase 3.5-RD instead tested a related, explicitly reframed, real, non-synthetic axis the authorization permitted: **unseen-workload-category generalization** (Alibaba: train excludes all `dominant_gpu_type == "T4"` jobs, test = T4 only, n=2,062; AIOps: train excludes all `db`-family windows, test = `db` only, n=56). Full detail: `docs/PHASE3_REAL_DATA_3_5_REPORT.md`. |
| **Real-data result — Alibaba** | R0 AUROC 0.571 [0.532,0.609], paired Δ vs. no-signal +0.071 [0.032,0.109] (significant, small). R1 +0.050 [0.012,0.087] (significant, barely). R2 +0.009 [−0.031,0.050] (**not significant**). All three margins are substantially smaller than the same representations' in-distribution (random/temporal split) performance. |
| **Real-data result — AIOps** | R0 AUROC 0.748 [0.596,0.933], paired Δ +0.248 [0.096,0.433] (significant, large point estimate, wide CI, n=13 entities — **EXPLORATORY**). R1 similar. R2 −0.054 [−0.310,0.134] (**not significant**). |
| **Real-data result — AgentRx** | **NOT EVALUABLE** — unchanged H1 blocker (no negative class in either frozen sample). |
| **Direction of agreement/disagreement** | **Not directly comparable** to the original — different mechanism entirely (real categorical exclusion vs. synthetic post-hoc feature perturbation). Explicitly not forced into a false replication. |
| **Interpretation** | Where a loose qualitative parallel exists: the original found the frozen candidate "remains competitive under attack" — a relatively strong claim, tested via input corruption on an otherwise-identical population. This real-data finding is more modest and structurally different: the signal generalizes to a wholly unseen category, but with a visibly smaller margin than in-distribution performance, and R2 shows no reliable effect on either dataset under this condition (though, unlike the Phase 3.3-RD/3.4-RD temporal finding, not a significant *harm* here either — both R2 CIs straddle zero rather than sitting entirely below it). Reported as a distinct, complementary real-data finding, not a stronger or weaker version of the original's synthetic-attack result. |

## H5a — complementarity / H5b — decision-cost policy

**Synthesized in Phase 3.6-RD: NOT EVALUABLE, structural.** No calibrated-confidence-equivalent baseline
exists anywhere in the real-data track (established Phase 3.1-RD, unresolved through every subsequent
phase), so H5a (does the signal add value beyond a stronger reference) has never had a second signal to test
complementarity against. No real, disclosed deployment cost model exists for any of the three datasets and
none was fabricated, so H5b (decision-cost policy) has no basis to evaluate either. Neither is a result of a
test that ran and came back negative — both are the absence of a precondition for the test to exist at all.
Full detail: `docs/PHASE3_REAL_DATA_3_6_DECISION.md` §10 (H5a, H5b).

## H6 — diagnosis

**Synthesized in Phase 3.6-RD: NOT EVALUABLE — scope gap, not data gap.** Unlike H5a/H5b/H7, this is not a
structural absence: AgentRx's organic `root_cause_failure_id`/`root_cause_reason` fields and AIOps's injected
fault categories both exist and were explicitly preserved for this purpose in the frozen protocol
(`docs/PHASE3_REAL_DATA_PROTOCOL.md` §3). No authorized phase (protocol design through Phase 3.6-RD
synthesis) included running a diagnosis experiment against them. This is documented as a candidate future
experiment (`docs/PHASE3_REAL_DATA_3_6_DECISION.md` §22), not attempted here.

## H7 — recovery

**NOT EVALUABLE on any dataset**, per the frozen protocol's mapping (no dataset records a recovery
action/outcome). This is a structural limitation of the currently held data, not an execution gap — no
future authorized phase under the current data holdings can change this conclusion without new data
acquisition. Reconfirmed, unchanged, by the Phase 3.6-RD synthesis (`docs/PHASE3_REAL_DATA_3_6_DECISION.md`
§10, H7).

---

## Phase 3.6-RD — final synthesis

Phase 3.6-RD (2026-08-13) consolidated all of the above into a single final decision table and a set of
explicit Phase 4 recommendations, without running any new evaluation. Full detail, including the complete
strongly-supported/partially-supported/negative/inconclusive/not-evaluable/newly-discovered finding
breakdown and Phase 4 implications, is in `docs/PHASE3_REAL_DATA_3_6_DECISION.md` and the machine-readable
`configs/phase3_6_rd_decision.json`. The headline conclusion: real data reproduces the qualitative core of
the original Phase 3's H1 finding (a supervised signal exists) but reveals that neither the signal's strength
nor its representation-choice-independence is uniform across distribution-shift conditions — a boundary
condition the original single-representation, single-shift-type synthetic design never had the structure to
surface. Four hypotheses (H5a, H5b, H6, H7) remain unevaluated, three for structural reasons and one (H6)
purely from scope.

---

## Summary table

| Hypothesis | Status | Real-data direction vs. original |
|---|---|---|
| H1 | **Executed (Phase 3.1-RD)** | Agrees directionally (Alibaba, AIOps); cannot adjudicate (AgentRx) |
| H2 | **Executed (Phase 3.2-RD)** | Partially agrees (Alibaba random split); not robust under distribution shift (Alibaba temporal split — new finding, no original analogue); inconclusive (AIOps); cannot adjudicate (AgentRx) |
| H3 | **Executed (Phase 3.3-RD)** | Not directly comparable (different shift type: concept-only vs. compound concept+covariate); AIOps/AgentRx not evaluable |
| Phase 3.4-RD (consolidation, cross-cutting) | **Executed** | Not directly comparable on "beats strongest baseline" (no real analogue of B exists); extends the original's caution via a paired test showing R2 significantly harms relative to no-signal under Alibaba's temporal shift |
| H4 | **Executed (Phase 3.5-RD)** | Not directly comparable (real categorical-holdout vs. original's synthetic feature perturbation — literal mechanism NOT EVALUABLE on real data); real, reframed unseen-workload test shows a real but much smaller signal margin than in-distribution splits, with R2 showing no reliable effect on either dataset |
| H5a/H5b | **Synthesized (Phase 3.6-RD): NOT EVALUABLE, structural** | No real-data baseline/cost-model precondition exists to test against |
| H6 | **Synthesized (Phase 3.6-RD): NOT EVALUABLE, scope gap** | Usable fields exist (AgentRx root-cause, AIOps fault category) but no phase attempted this experiment |
| H7 | **Synthesized (Phase 3.6-RD): NOT EVALUABLE / STRUCTURAL GAP** | No dataset records recovery outcomes |

This document was updated by Phase 3.6-RD (2026-08-13) with the final synthesis. The real-data Phase 3
replication research program is now complete pending review; any further evaluation requires a new,
separately authorized phase.


---

<a id="phase4-plan"></a>
# PHASE4 PLAN
**Status: ACTIVE (amended)**  
**Original file:** `docs/PHASE4_PLAN.md`  
**Role:** The Phase 4 master plan. Sections 0-10 are the original frozen plan; Section 11 is an additive amendment covering the real-data-driven Phase 4 reboot. Nothing in sections 0-10 was rewritten.

# Phase 4 Plan — Self-Learning & Validation

**Status: APPROVED (reviewed and authorized).** Phase 4.0 is **COMPLETE**
— see [`docs/PHASE4_0_EPISODIC_DATA.md`](PHASE4_0_EPISODIC_DATA.md).
Phase 4.1 is **COMPLETE — 🟡 PASS WITH ISSUES** (H1 partially supported)
— see [`docs/PHASE4_1_FAILURE_MEMORY.md`](PHASE4_1_FAILURE_MEMORY.md).
Phase 4.2 is **COMPLETE — 🟡 INCONCLUSIVE** (H2 inconclusive, evidence
volume insufficient) — see
[`docs/PHASE4_2_FAILURE_PATTERNS.md`](PHASE4_2_FAILURE_PATTERNS.md).
Phase 4.3 has not started; per the authorization, subphases proceed one
at a time in frozen sequence, each implemented/tested/documented before
the next begins.

This document is the pre-registered plan required before any Phase 4 code
is written, per the project's research-integrity rule (see
[`docs/PHASE3_FREEZE.md`](PHASE3_FREEZE.md), which this plan does not
modify). It fixes subphase sequence, dependencies, hypotheses, data
protocol, metrics, and completion criteria *before* any Phase 4 result is
computed — the same discipline Phase 3.1's frozen protocol established
for Phase 3.

## 0. Where Phase 3 left off (the starting position, not re-litigated)

Frozen findings this plan must not silently overwrite (full detail in
[`PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`](PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md),
[`PHASE3_FREEZE.md`](PHASE3_FREEZE.md)):

- **B (calibrated confidence) is the strongest, cheapest signal at every
  axis tested.** F (Supervised Failure Risk) and B+F provide no measurable
  incremental value over B alone (Phase 3.4, 3.6 §4).
- **Diagnosis (condition attribution)** is a deterministic, zero-fitting
  rule — perfect on `feature_dropout`, weak on mild `feature_noise`
  (recall 42.5%).
- **Recovery**: retry succeeds ~55% of the time it fires (45% of
  "recoveries" are still wrong); reconfigure recovers **0/N** because its
  fallback signal (B) shares the same corruption as the primary signal.
- **Autonomous decision authority is NOT justified** by any Phase 3
  result. This conclusion stands until Phase 4 produces new,
  independently evaluated evidence.
- Reusable, frozen-in-place components (Phase 4 must not edit these
  in-place — see §5 isolation rules): `src/schema/events.py`
  (`ReliabilityEvent` already carries `workload_id`, `context`,
  `confidence`, `failure_risk`, `decision`, `outcome`, `failure_cluster`,
  `metadata`, `timestamp` — most of the Phase 4.1 field list already
  exists), `src/storage/` (SQLAlchemy persistence + repository),
  `src/failure_memory/` (existing embedding + clustering, currently used
  only for the F signal), `src/decision/policy.py` (the one authoritative
  decision policy), `src/evaluation/{diagnosis,recovery,decision_policy}.py`
  (deterministic Phase 3.6 rule/policy implementations).

## 1. Critical data gap (why Phase 4.0 exists)

Phase 3's benchmark (`src/data/synthetic.py`) generates **i.i.d.
classification samples** under a regime-drift/attack condition — there is
no notion of a *recurring workload* experiencing *repeated incidents over
time*, no recovery-attempt trace, and no "the system saw this failure
mode last week and is now facing it again." Phases 4.2 (pattern
learning), 4.3 (recovery strategy learning), 4.6 (continual learning),
and 4.7 (generalization) all require **episodic, temporally-ordered
incident data with repeatable workload/condition identity** — this does
not exist yet and must be built first.

**Phase 4.0 — Incident/Episode Data Generation** (prerequisite, not in
the original numbered list but required before 4.1 can be evaluated
meaningfully):

- Extend (not modify in place — new module `src/data/episodic.py`)
  `synthetic.py`'s regime/attack machinery to emit **episodes**: a
  sequence of `(workload_id, timestamp, context, true_label, model
  prediction, confidence, decision, outcome, recovery_action,
  recovery_outcome)` tuples, grouped into incidents, across many
  synthetic "workloads" (parameterized regime/attack combinations) that
  **recur** across simulated time with configurable recurrence rate,
  drift, and novel (held-out) conditions.
- Deterministic, seeded, documented generator — same reproducibility bar
  as `synthetic.py` (fixed seeds, closed-form ground truth for what
  "recurring" vs. "novel" means, so generalization in 4.7 can be checked
  against a known answer instead of an assumption).
- Deliverable: `src/data/episodic.py`, `docs/PHASE4_0_EPISODIC_DATA.md`
  (generator spec + leakage-relevant properties: what info is available
  at decision time vs. only after outcome is known).

## 2. Subphase sequence and dependencies

```
4.0 Episodic data generator
 └─▶ 4.1 Failure memory & experience schema/store
      └─▶ 4.2 Pattern learning  ──────────────┐
      └─▶ 4.3 Recovery strategy learning ─────┤
                                               ├─▶ 4.4 Safe learning & abstention integration
                                               │        (gates 4.2 + 4.3 outputs)
4.5 Learning protocol & data isolation ◀───────┘  (defined alongside 4.0, enforced from 4.1 onward)
      └─▶ 4.6 Continual learning experiments
      └─▶ 4.7 Generalization evaluation
              └─▶ 4.8 Learning validation & safety gates
                       └─▶ Phase 4 verification report
```

4.5 is not "step 5 chronologically" — its protocol (train/validation/
frozen-test split, freeze points) must be **written and frozen before
4.1's store is first populated with anything used for evaluation**, the
same way `configs/phase3_1_protocol.json` predated Phase 3.1's first
result. It is listed as 4.5 to match the requested numbering, but
enforced from 4.0 onward.

## 3. Data isolation protocol (write this before touching 4.1)

- **Learning/training split**: episodes from "known" workload/condition
  combinations, regime-2-equivalent role (matches Phase 3's regime-2 =
  "fit-only" convention) — failure memory is populated and pattern/
  recovery-strategy learning fits only here.
- **Validation split**: held-out episodes from known combinations, used
  for threshold/confidence-gate tuning (4.4) and early stopping in
  continual-learning experiments (4.6). May be touched repeatedly during
  development.
- **Frozen test split**: sealed before 4.6 begins, touched **exactly
  once** per pre-registered experiment, covering both (a) unseen episodes
  of known combinations and (b) entirely novel workload/condition
  combinations never in train or validation (required for 4.7).
- Freeze artifact: `configs/phase4_learning_protocol.json` (row-hash
  manifest of the frozen test split, same leakage-audit pattern as
  `phase3_1_leakage_audit.py` — a `phase4_leakage_audit.py` checks zero
  row-hash overlap between splits, and that no learned parameter's
  fitting code path ever touches the frozen split).
- **Learned-state versioning**: every fitted memory/pattern/policy
  artifact gets a content-hashed version id + manifest (training data
  version, code version, seed, timestamp) written alongside it — this is
  what 4.5's "how learned state is versioned" and the Research Integrity
  §5/§6 requirements need concretely.
- Rule, stated explicitly and enforced by the audit script: **once the
  frozen test split is evaluated for a given learned-state version, that
  version is retired** — no re-fitting and re-testing the same
  architecture against the same frozen split to chase a better number.

## 4. Subphase plans

Each subphase follows the Implementation Rule in the brief (inspect →
identify reuse → define hypothesis → define evaluation → smallest
research-valid version → test → evaluate → document). Below fixes the
hypothesis, baseline, and metrics for each — the "smallest valid version"
decision is made at implementation time per subphase, but must be
justified against the frozen protocol here, not decided ad hoc.

### 4.1 — Failure Memory & Experience Learning

- **Hypothesis (H1)**: a structured, indexed experience store built on
  `ReliabilityEvent` + episode outcome data can retrieve relevant past
  incidents for a new failure with better-than-chance similarity
  ranking, without becoming an unstructured log.
- **Reuse**: extend `src/storage/` (repository pattern) and
  `src/failure_memory/embedding.py` rather than building new persistence
  from scratch. New: `src/experience/` module for the
  store/retrieve/decay API, kept separate from `src/failure_memory/`
  (frozen) rather than editing it in place.
- **What is stored**: only fields listed in the brief that are
  reconstructable from schema/episode data — explicitly *not* raw
  input payloads beyond the existing `context: dict[str,float]`
  vector (no free-text, no PII — same constraint `SCHEMA.md` already
  enforces via `metadata`).
- **Staleness/decay**: recency-weighted retrieval score, decay function
  fixed before 4.6 experiments run (not tuned against frozen test data).
- **Metrics**: retrieval precision@k / recall@k against known
  ground-truth "same underlying condition" labels from the episodic
  generator (§4.0's known ground truth is what makes this measurable
  instead of assumed).
- **Baseline**: no-memory (uniform-random retrieval) and
  recency-only (most-recent-k, no similarity) retrieval.

### 4.2 — Failure Pattern Learning

- **Hypothesis (H2)**: recurring failure patterns (condition recurrence,
  temporal clustering, symptom→cause→outcome relationships) are
  detectable above chance in the episode stream, and the system can
  correctly separate observed evidence from inferred pattern from
  confirmed relationship from uncertain hypothesis (four explicit
  confidence tiers, not a single score).
- **Reuse**: `src/failure_memory/embedding.py` clustering as a candidate
  pattern-detection primitive (already shown modest signal in Phase
  3.2/3.2C); diagnosis taxonomy from `src/evaluation/diagnosis.py`
  (frozen, reused read-only) as one input feature, not retrained.
- **Metrics**: precision/recall of detected recurring patterns against
  §4.0's known ground-truth recurrence structure; calibration of the
  four-tier confidence labeling (does "confirmed" actually mean higher
  precision than "hypothesis," measured, not asserted).
- **Baseline**: no pattern learning (each incident treated
  independently) vs. naive frequency-count pattern flagging (no
  confidence tiering) vs. the proposed tiered approach.

### 4.3 — Recovery Strategy Learning

- **Hypothesis (H3)**: using historical recovery outcomes to select
  among {retry, rollback, restart, reconfigure, abstain, retrain,
  redeploy} produces a lower expected-cost / lower-unsafe-rate policy
  than Phase 3.6's fixed diagnosis→action rule, when experience
  relevance is evaluated (similarity, context compatibility, recency,
  evidence quantity, provenance) rather than applied blindly.
- **Explicit non-goal**: "past success implies future success" is
  disallowed by construction — every candidate strategy selection must
  attach a relevance/reliability score computed from the dimensions
  listed in the brief, and a strategy with low relevance score must be
  down-weighted or excluded, not used at full trust.
- **Reuse**: `src/evaluation/recovery.py` (frozen) as the Phase 3.6
  baseline policy, evaluated unmodified for comparison; new
  `src/experience/recovery_selector.py` as the learned alternative.
- **Metrics**: recovery success rate, unsafe-action rate (recovered but
  still wrong — Phase 3.6 §17's key finding), expected cost under the
  same frozen cost model as `configs/phase3_6_decision_recovery_protocol.json`
  (reused unmodified for comparability, not re-derived).
- **Baseline**: Phase 3.6's frozen diagnosis-gated recovery policy
  (retry/reconfigure/rollback, as-is) — this is the primary baseline for
  the whole of Phase 4.3, not a strawman.

### 4.4 — Safe Learning & Abstention

- **Hypothesis (H4)**: gating learned recovery/pattern knowledge by an
  evidence/confidence threshold reduces the unsafe-action rate relative
  to using learned knowledge unconditionally, at an acceptable utility
  cost (mirrors the cost-ratio sensitivity method from Phase 3.6 §7/§13).
- **Integration point**: extends `src/decision/policy.py`'s tiering
  logic (frozen — extend via a new decision layer that *consumes* its
  output, does not edit it in place) to add a fourth outcome: "abstain
  from applying learned knowledge, fall back to Phase 3.6's static
  policy" — i.e., a meta-abstention over the *learning* itself, distinct
  from abstention over the *answer*.
- **Metrics**: false-confidence rate (learned knowledge applied with high
  stated confidence but wrong), unsafe-autonomous-action rate with vs.
  without the gate, abstention-quality (does gating catch the cases where
  learned knowledge would have been wrong, at what precision/recall).
- **Baseline**: (a) no gate — always apply learned knowledge; (b) always
  abstain from learned knowledge (equivalent to pure Phase 3.6 policy);
  (c) the proposed evidence-gated policy. (b) is expected to be safest
  but least autonomous — the report must state where the proposed policy
  actually lands between (a) and (b), not assume it strictly dominates.

### 4.5 — Learning Protocol & Data Isolation

Protocol document + `phase4_leakage_audit.py`, written per §3 above,
frozen before 4.6. Deliverable is the audit passing with zero violations
on whatever is built in 4.1–4.4, re-run (not re-derived) before 4.6/4.7.

### 4.6 — Continual Learning Experiments

- **Hypothesis (H5)**: `Initial system → observe failures → learn →
  re-evaluate` produces a measurable, statistically distinguishable
  (bootstrap CI, same method as Phase 3.1 `bootstrap.py`, reused)
  improvement over a frozen-knowledge control on the metrics in §"Phase
  4.6" of the brief (detection, diagnosis, recovery success/selection,
  abstention, reliability, false recovery, overhead, latency,
  memory/compute cost).
- **Design**: multiple seeds (reuse Phase 3's seed convention `[1,2,3,4,5,42]`,
  primary seed 42) × multiple checkpoints along the episode stream
  (e.g., after 0/N, 1/N, ..., N/N training incidents) evaluated each time
  against the **same frozen validation split**, with the **frozen test
  split touched only once at the final checkpoint** per §3.
- **Controls needed to distinguish real learning from confounds** (the
  brief's explicit requirement): (a) frozen-knowledge control (same
  architecture, learning disabled after checkpoint 0) to separate
  learning from simple additional-observation noise; (b) shuffled-label
  control (experience store populated with mismatched
  incident↔outcome pairs) to detect memorization/overfitting rather than
  generalizable learning; (c) distribution-shift control (checkpoints
  compared only within the same underlying regime, to rule out the
  "improvement" being a change in test-stream difficulty rather than
  learning).
- **Baseline**: Phase 3.6's frozen policy (zero learning) is the headline
  comparison, per the brief's "compare against the relevant Phase 3
  baseline."

### 4.7 — Generalization of Learned Knowledge

- **Hypothesis (H6)**: knowledge learned from training-split incidents
  transfers with reduced-but-nonzero effectiveness to (a) unseen
  instances of known conditions, (b) entirely novel workload identities,
  (c) altered operating conditions, (d) novel symptom combinations —
  using §4.0's known ground-truth novelty labeling to measure this
  directly rather than assuming transfer.
- **Metrics**: same as 4.6, stratified by novelty category, each
  compared against the frozen-knowledge control from 4.6 at matched
  novelty category (a fair comparison needs the control to see the same
  novel cases, not just the learner).
- Explicit finding target: does performance degrade gracefully with
  novelty distance, or cliff sharply at any tested boundary — report
  whichever is observed.

### 4.8 — Learning Validation & Safety Gates

- **Hypothesis (H7)**: a predefined, reproducible validation procedure
  can correctly sort learned artifacts (a pattern, a recovery
  association, a policy update) into `validated / uncertain / invalid /
  unsafe`, and this sorting measurably improves downstream safety (lower
  unsafe-action rate) versus admitting all learned artifacts
  unconditionally.
- **Reuse**: this is 4.4's gate generalized from "gate a decision" to
  "gate a piece of learned state before it is ever eligible to influence
  a decision" — implemented as a promotion pipeline in front of the 4.1
  store, not a duplicate mechanism.
- **Metrics**: validation-outcome distribution, and (per the brief)
  auditability — every validation decision must log its inputs,
  thresholds, and outcome in a reproducible, queryable form (reuse
  `src/storage/repository.py` patterns).
- **Baseline**: unconditional admission of all learned artifacts (no
  gate) — same comparison structure as 4.4.

## 5. Metrics reference (definitions fixed before any Phase 4 result)

| Metric | Definition | Source data | Reused from Phase 3? |
|---|---|---|---|
| AUROC/AUPRC/ECE/AURC | Same as `src/evaluation/metrics.py` | frozen/held-out splits | Yes, unmodified |
| Bootstrap CI | Same as `src/evaluation/bootstrap.py` | per-seed results | Yes, unmodified |
| Retrieval precision@k/recall@k | New (4.1) | episodic ground-truth condition identity | No — new |
| Pattern precision/recall by tier | New (4.2) | episodic ground-truth recurrence | No — new |
| Recovery success/unsafe-action/expected cost | Same formulas as Phase 3.6 §7/§13/§17 | episodic recovery outcomes | Reused definitions, new data |
| False-confidence rate | New (4.4) | learned-knowledge applications vs. ground truth | No — new |
| Generalization gap | performance(novel) − performance(known), same metric | 4.7 stratified splits | No — new |
| Operational overhead | wall-clock + memory delta, learning vs. frozen-knowledge control | 4.6 runs | No — new |

Each new metric gets its own short spec (definition, rationale,
calculation method, data source, limitations) in the corresponding
subphase doc, per Research Integrity Requirement 2 — not merely listed
here.

## 6. Ablations (planned, not exhaustive — extend if a result motivates one)

- 4.2: pattern learning with vs. without the four-tier confidence
  labeling (does tiering matter, or would a single score do as well).
- 4.3: recovery selection with vs. without each relevance dimension
  (similarity / recency / evidence quantity) removed one at a time.
- 4.4: gate threshold sensitivity sweep (mirrors Phase 3.6's cost-ratio
  sensitivity sweep methodology).
- 4.6: with vs. without each control (b)/(c) from §4.6 above, to isolate
  which confound each control actually rules out.

## 7. Completion criteria checklist (mirrors the brief verbatim, tracked here)

- [ ] All planned subphases (4.0–4.8) implemented, or explicitly marked
      not-implemented with justification.
- [ ] Failure memory functional and provenance-aware.
- [ ] Learned knowledge influences decisions only through the 4.4/4.8
      controlled gate mechanism.
- [ ] Safety/abstention integrated (4.4).
- [ ] Learning/evaluation data isolation enforced and audited (4.5).
- [ ] Continual learning experimentally evaluated with controls (4.6).
- [ ] Generalization evaluated (4.7).
- [ ] Baselines (Phase 3.6 frozen policy) and ablations conducted.
- [ ] Results reproducible (seeds, versions, configs recorded).
- [ ] Negative/inconclusive findings documented, not omitted.
- [ ] No frozen-test contamination or metric manipulation (audited).
- [ ] All code/experiments/configs/docs committed.
- [ ] Formal Phase 4 verification report produced with an honest status:
      PASS / PASS WITH ISSUES / INCONCLUSIVE / FAIL.

## 8. Deliverables → subphase map

| # | Deliverable | Produced by |
|---|---|---|
| 1 | Failure memory architecture | 4.1 |
| 2 | Structured failure/experience representation | 4.1 |
| 3 | Experience retrieval mechanism | 4.1 |
| 4 | Failure pattern learning mechanism | 4.2 |
| 5 | Recovery strategy learning mechanism | 4.3 |
| 6 | Safety/abstention integration | 4.4 |
| 7 | Learning validation mechanism | 4.8 |
| 8 | Strict train/validation/test isolation | 4.0/4.5 |
| 9 | Continual learning evaluation framework | 4.6 |
| 10 | Generalization evaluation | 4.7 |
| 11 | Baseline comparison | 4.6/4.7 (vs. Phase 3.6 frozen) |
| 12 | Quantitative evaluation results | all |
| 13 | Ablation studies | 4.2/4.3/4.4/4.6 |
| 14 | Failure-case analysis | all, esp. 4.6/4.7 |
| 15 | Learning-state/provenance tracking | 4.1/4.5 |
| 16 | Reproducible experiment configs | all (`configs/phase4_*.json`) |
| 17 | Phase 4 documentation | `docs/PHASE4_*.md` per subphase |
| 18 | Phase 4 verification report | final, after 4.8 |

## 9. What this plan deliberately does not decide yet

Per the Implementation Rule, the *specific* model/algorithm choice for
each subphase (e.g., what similarity metric 4.1 retrieval uses, what
form the 4.3 relevance score takes) is decided at implementation time,
starting from the smallest research-valid version, and documented in
that subphase's own report — not pre-committed here. What *is* fixed
here is unbuildable-around-later: the sequence, the hypotheses, the
baselines, the isolation protocol, and the completion/status criteria.

## 10. Review decisions (recorded, not open anymore)

Reviewed and authorized. Decisions, verbatim in substance:

1. **Phase 4.0 — APPROVED.** Accepted as an explicit, in-scope
   prerequisite. Built per §1's spec: `src/data/episodic.py`, existing
   Phase 3 synthetic generator left unmodified, deterministic/seeded,
   decision-time vs. outcome-time fields kept distinct, known ground
   truth for recurrence/novelty, documented and tested before any
   subphase depends on it. **Status: COMPLETE** — see
   `docs/PHASE4_0_EPISODIC_DATA.md`.
2. **Frozen Phase 3 boundary — APPROVED, with clarification.** Phase 4
   extends via new modules (`src/data/episodic.py`, and `src/experience/`
   once Phase 4.1 begins) that *consume* frozen Phase 3 components
   read-only, rather than editing them in place. Concretely for Phase
   4.4's later gate: `Phase 3 decision/policy → Phase 4 learning layer →
   safety/abstention gate → final action`, not a rewrite of
   `src/decision/policy.py`. This boundary was followed exactly in Phase
   4.0 (verified structurally by the leakage audit's
   `no_regime_0_1_2_row_ever_emitted` check, not just by code review).
3. **Primary research question — APPROVED**, unchanged from §"Required
   Evaluation Philosophy" of the brief, framing the final verification
   report (deliverable 18). The report's status categories remain
   yes/partially/no/inconclusive — not structured to prove "yes."
4. **Research-integrity clarification on inconclusive results —
   APPROVED and binding for the rest of Phase 4.** An earlier
   subphase's INCONCLUSIVE (or any other) finding is never retroactively
   changed. A later subphase may add independently-justified new
   evidence; if that resolves the earlier uncertainty, the progression is
   documented explicitly (`Earlier experiment → INCONCLUSIVE`, `New
   experiment → additional evidence`, `Combined evidence → <verdict>`),
   never silently overwritten. Same discipline `docs/PHASE3_FREEZE.md`
   already established for Phase 3.

**Authorization scope**: proceed to Phase 4.0 only, which is now done.
Do not begin Phase 4.1 without a further go-ahead per the frozen
sequence in §2.

## 11. Amendment — real-data expansion, revised Phase 3, and the active Phase 4.1 reboot

*(Added after §0–§10 above; nothing above this section was edited or
retroactively changed.)*

After Phase 4.0/4.1/4.2 (§0–§10, all synthetic-data-only) were completed and
frozen, the project substantially expanded its evaluation data with three
real datasets (AgentRx, AIOps 2020, Alibaba GPU 2020 cluster trace — see
`data/`) and re-ran Phase 3 against them
(`docs/PHASE3_REAL_DATA_*.md`, decision in
`docs/PHASE3_REAL_DATA_3_6_DECISION.md`). Phase 4 was then deliberately
paused before continuing, to reassess Phase 4's design against the new data
and the revised Phase 3 findings — the real-data pipeline currently
produces detection only (no diagnosis/recovery/validation on real data, a
documented gap, see that decision doc's H6/H7).

**The old Phase 4.1 (§4.1 above, `docs/PHASE4_1_FAILURE_MEMORY.md`) and old
Phase 4.2 (§4.2 above, `docs/PHASE4_2_FAILURE_PATTERNS.md`) are NOT
retroactively changed by this amendment** — both remain frozen, exactly as
recorded, per this document's own §10 item 4 research-integrity rule.

A new, independent, additive package (`src/failure_experience/`) implements
the **current active Phase 4.1** against the post-expansion repository
state — see [`docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md`](PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md)
for the full audit, design, implementation, experiments, and status. It
does not import, edit, or extend-in-place `src/experience/` (old 4.1) or
`src/patterns/` (old 4.2). Phase 4.2 onward (pattern learning, recovery
policy learning, etc.) has not been redone or restarted — this amendment
covers Phase 4.1 only; the rest of the originally-planned sequence (§2, §4)
remains open and unauthorized pending a further go-ahead, same as before.


---

<a id="phase4-1-active-failure-experience"></a>
# PHASE4 1 ACTIVE FAILURE EXPERIENCE
**Status: ACTIVE / CURRENT**  
**Original file:** `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md`  
**Role:** ACTIVE Phase 4.1: the current FailureExperience representation/memory substrate, built on real + synthetic data. Status: PASS.

# Phase 4.1 (Active) — Failure Memory & Experience Representation

**Status: COMPLETE — see §16 for the formal verdict.**

**This document does NOT supersede, correct, or retroactively alter**
[`docs/PHASE4_1_FAILURE_MEMORY.md`](PHASE4_1_FAILURE_MEMORY.md) (old Phase
4.1, synthetic-data-only, status COMPLETE — PASS WITH ISSUES) or
[`docs/PHASE4_2_FAILURE_PATTERNS.md`](PHASE4_2_FAILURE_PATTERNS.md) (old
Phase 4.2, status COMPLETE — INCONCLUSIVE). Those remain frozen historical
artifacts, exactly as recorded, per the explicit project decision to treat
them as such (see §1). This document describes a **new, independent,
additive** package (`src/failure_experience/`) built after the project's
real-data expansion and revised (real-data) Phase 3, at a point where the
project deliberately paused before continuing Phase 4 to reassess its
design against the new data and evidence.

## 1. Why this document exists, and why it is not "Phase 4.1 v2"

Timeline, reconstructed from file dates and doc content (not asserted, this
is what the repository actually shows):

1. Old Phase 4.0/4.1/4.2 were built and frozen using a purely **synthetic**
   episodic generator (`src/data/episodic.py`,
   `experiments/results/phase4_0/episodes.json`) — the only data available
   at the time.
2. The project then substantially expanded its evaluation data foundation
   with three **real** datasets (`data/{raw,processed,...}/{agentrx,
   aiops_kpi,alibaba_gpu2020}/`) and re-ran Phase 3 against them
   (`docs/PHASE3_REAL_DATA_*.md`, culminating in
   `docs/PHASE3_REAL_DATA_3_6_DECISION.md`).
3. The revised, real-data Phase 3 found that the pipeline currently
   produces **detection only** (a calibrated risk score) on real data, with
   confirmatory precision on Alibaba, exploratory precision on AIOps, and
   not-evaluable on AgentRx (all-positive sample) — diagnosis, recovery, and
   validation were never run against real data (H6/H7 both NOT EVALUABLE in
   that decision doc, despite AgentRx/AIOps having usable ground-truth
   fields for exactly this purpose — a genuine, documented gap, not
   something this document invented).
4. Phase 4 was explicitly paused at that point for reassessment before
   continuing — this document is that reassessment's Phase 4.1 output.

Given (3), the old Phase 4.1's `Experience` schema
(`src/experience/schema.py`) is scoped to what the *synthetic* Phase 4.0
generator produced: a `ReliabilityEvent` plus an `EpisodeProvenance`
sidecar, built specifically to measure retrieval precision@k against a
generator's ground-truth `condition_id`. It has no field for diagnosis
*validation* (was the diagnosis later confirmed or contradicted?), no
recovery/validation representation beyond three flat fields
(`recovery_action`/`recovery_outcome`/`recovery_correct`), and — critically —
was never exercised against real data at all. Extending it in place would
mean editing a file the project has explicitly frozen; redesigning "Phase
4.1" without a new identity would silently imply the old, frozen PASS WITH
ISSUES verdict either still describes current work or has been quietly
superseded — both violate the project's own research-integrity rule
(`docs/PHASE3_FREEZE.md`, reaffirmed in `docs/PHASE4_PLAN.md` §10 item 4:
"An earlier subphase's finding is never retroactively changed").

**Decision** (per explicit user authorization for this document): implement
a new, richer canonical representation, `FailureExperience`
(`src/failure_experience/`), as the **current active Phase 4.1**, entirely
additive to and independent of `src/experience/` (old Phase 4.1) and
`src/patterns/` (old Phase 4.2) — neither of which is imported, edited, or
read for mutation anywhere in this package
(`tests/integration/test_failure_experience_pipeline.py::
TestPhase3IntegrationDoesNotTouchFrozenModules` asserts this directly, not
just by convention).

## 2. Objective and research question

Same central question as the original brief: **can operational failures be
represented as structured experiences that preserve sufficient contextual,
diagnostic, recovery, outcome, temporal, and provenance information to
support safe future learning?** — now asked against the actual current
state of the repository (real, heterogeneous, partially-instrumented data)
rather than a purpose-built synthetic generator.

This phase is **not** a learning system. Per Task 18 of the brief and
consistent with `docs/PHASE4_PLAN.md`'s frozen subphase sequence, no
pattern learning, recovery-policy learning, or continual learning is
implemented here — this is the substrate those would consume.

## 3. Audit — what exists, what was reused, what was built new

| Component | Source | Reuse decision | Justification |
|---|---|---|---|
| `src.schema.events.ReliabilityEvent` | `src/schema/events.py`, frozen | **Not extended in place** | `extra="forbid"` pydantic model with no diagnosis/recovery/validation slots; a parallel schema was built instead of loosening this frozen contract. |
| `src.storage.{db,models,repository}` | frozen | **Pattern reused, not the table** | Same SQLite+SQLAlchemy+repository architecture, new `FailureExperienceRecord` table in a **separate** database file (`data/failure_experience_dev.db`) — physically isolated from the frozen `data/unified_dev.db`. |
| `src.experience.schema.{Experience,EpisodeProvenance}` (old Phase 4.1) | `src/experience/`, frozen | **Not imported, not extended** | Purpose-built for synthetic retrieval-precision evaluation only; structurally cannot hold diagnosis-validation/recovery-validation data even for the synthetic source, let alone real data. Read (by the author, not by code) to understand its scope and avoid duplicating its retrieval-precision experiment. |
| `src.patterns.*` (old Phase 4.2) | `src/patterns/`, frozen | **Not touched** | Downstream of old Phase 4.1's schema; out of scope for this document (Task 18: do not implement pattern learning). |
| `src.evaluation.diagnosis`, `src.evaluation.recovery` | frozen, synthetic-only | **Reused (read-only) inside the synthetic-episodic source adapter only** | These are the components that actually produced the diagnosis/recovery/outcome fields already baked into `experiments/results/phase4_0/episodes.json`; the adapter (`src/failure_experience/sources/synthetic_episodic.py`) reads that frozen JSON file, it does not call `diagnosis.py`/`recovery.py` directly. |
| Real-data detection pipeline (`scripts/real_data/phase3_*_rd_*.py`) | frozen | **Not reused directly** | Per the audit, these scripts compute aggregate AUROC/AUPRC over a full evaluation split, not a per-record structured output; re-running them to get per-record scores was out of scope for Phase 4.1 (a reasonable Phase 4.1.x follow-on, not attempted here — see §11). |
| Alibaba split manifest (`data/audit/alibaba_gpu2020/splits_random_stratified.json`) | frozen | **Reused directly** | Per Task 7's explicit instruction to reuse an existing split registry rather than build a competing one; `src/failure_experience/sources/real_alibaba.py::_load_split_lookup` loads it read-only and stamps `workload_context.environment` with the train/val/test label. |
| AgentRx / AIOps raw+processed files | `data/{raw,processed,audit}/{agentrx,aiops_kpi}/` | **Read-only source data** | New adapters built for both; neither has a frozen split (documented gap, carried forward honestly — see §11). |

**What was found NOT to exist and had to be built from nothing**: any
structured schema that keeps diagnosis, recovery, and validation as
independently-typed, independently-versioned sub-objects with an explicit
observation/interpretation boundary; any persistent store or retrieval
interface for such a schema; any ingestion pipeline that normalizes
heterogeneous real datasets into one representation; any eligibility/
quarantine mechanism gating what's learnable.

## 4. The canonical `FailureExperience` schema

`src/failure_experience/schema.py`. A pydantic model (`extra="forbid"`,
frozen instances) composed of eleven typed, independently-validated
sub-objects, matching the brief's A–J categories one-to-one plus an
eligibility assessment (Task 6):

- **Identity** — `experience_id` (deterministic, sha256-derived, never
  random — see §6), `episode_id`, `observed_at`, `created_at`,
  `lifecycle_status`.
- **WorkloadContext** — `workload_id`, `workload_type`, `model_id/version`,
  `environment` (doubles as the split label where one exists — see §3),
  `deployment_config`, `runtime_context`.
- **Observations** — `telemetry`, `resource_metrics`, `performance_metrics`,
  `log_events`, `anomaly_signals`, `system_state`. Facts only — no field
  here can express an opinion about cause (§5).
- **FailureInfo** — `failure_type`, `failure_signature` (deterministic hash
  of type+component+workload_type, used as a retrieval key), `severity`,
  `detection_timestamp`, `affected_component`, `failure_status`.
- **Diagnosis** — `suspected_cause`, `confidence` (validated ∈[0,1]),
  `evidence`, `method`/`method_version`, `source` (`automated_system` |
  `human_dataset_annotation` | `not_attempted`), `later_validated`. An
  **interpretation**, never ground truth (§5).
- **RecoveryInfo** — `status` (`not_attempted` | `not_observed` |
  `attempted` — see §5 for why `not_observed` is a distinct state from
  `not_attempted`), `candidate_actions`, `selected_action`,
  `action_rationale`, `action_confidence`, `execution_result`,
  `rollback_info`, `retry_count`, `recovery_policy_version`.
- **ValidationInfo** — `pre_recovery_state`, `post_recovery_state`,
  `validation_metrics`, `validation_result` (`not_performed` | `passed` |
  `failed` | `partial`), `residual_failure`, `regression_indicators`,
  **`validated_cause`** — the later-confirmed root cause, kept in a
  *separate field from* `Diagnosis.suspected_cause`, never overwriting it
  (Task 5, see §5).
- **OutcomeInfo** — `recovery_success`, `task_success`,
  `recovery_latency_seconds`, `recovery_cost`, `attempts`, `final_status`
  (closed enum: `success | failure | partial_success | abstained |
  rolled_back | retried | worsened | unknown` — Task 4).
- **Provenance** — `source_dataset`, `source_workload`,
  `detector_version`, `diagnosis_component_version`,
  `recovery_policy_version`, `validation_component_version`,
  `memory_schema_version`, `ingestion_timestamp`, `dataset_content_hash`,
  `experiment_id`, `raw_record_ref` (identifying keys only, never a raw
  free-text payload).
- **TemporalLineage** — up to 7 optional timestamps (`observation_ts` …
  `outcome_ts`), validated **structurally** non-decreasing at construction
  time (a pydantic `model_validator`, not a convention — an out-of-order
  lineage cannot be constructed at all; see
  `tests/unit/test_failure_experience_schema.py::TestTemporalLineage`).
- **EligibilityAssessment** — see §7.

Full field reference is the source file's docstrings and type annotations
themselves (kept authoritative rather than duplicated verbatim here, per
the project's existing documentation style in `src/schema/events.py`).

## 5. Observation/interpretation separation, and preserving wrong diagnoses (Tasks 3 & 5)

Enforced by **type structure**, not convention: `Observations` and
`Diagnosis` are disjoint pydantic models with no shared fields — an
`Observations` instance cannot carry a `suspected_cause`, and a `Diagnosis`
instance cannot carry `telemetry`
(`tests/unit/test_failure_experience_schema.py::
TestObservationInterpretationSeparation`). A diagnosis is never silently
promoted to ground truth: `Diagnosis.later_validated` starts `None` and is
only ever informed by a **separate** `ValidationInfo.validated_cause`
field, which sits on a different sub-object entirely.

Critically, `ValidationInfo.validated_cause` **does not overwrite**
`Diagnosis.suspected_cause` — both persist on the same `FailureExperience`
simultaneously. `eligibility.py::_diagnosis_status` computes one of four
labels (`not_attempted` / `unvalidated` / `validated` / `contradicted`) by
**comparing** the two fields, never replacing one with the other. The
brief's worked example (initial diagnosis "configuration error", true cause
"memory exhaustion", rollback recovery, failure, later-validated actual
cause "memory exhaustion") is exactly the shape covered by
`tests/unit/test_failure_experience_schema.py::
TestFailedDiagnosisPreservation::
test_contradicted_diagnosis_is_preserved_not_overwritten` and
`tests/unit/test_failure_experience_eligibility.py::
TestContradictedDiagnosis`, both passing.

## 6. Determinism and idempotency

`deterministic_experience_id(source_dataset, episode_id, occurrence_key)`
is a sha256 truncation, never `uuid4` — re-ingesting the same source record
(even at a different wall-clock ingestion time) yields the same
`experience_id` and the same `content_hash()` (which explicitly excludes
`provenance.ingestion_timestamp` from its hash input, precisely so
idempotency can be detected — see
`tests/unit/test_failure_experience_schema.py::TestContentHash::
test_content_hash_ignores_ingestion_timestamp`).
`FailureExperienceRepository.save`/`save_many` use SQLAlchemy `merge`
(upsert), so re-ingesting a batch is a no-op on row count
(`tests/integration/test_failure_experience_pipeline.py::TestIdempotency`).

## 7. Learning eligibility (Task 6)

`src/failure_experience/eligibility.py::assess` computes explicit,
independently-visible evidence-quality fields — `observation_completeness`
(fraction of the 6 `Observations` slots populated), `provenance_completeness`
(fraction of 6 provenance fields populated), `diagnosis_status`,
`outcome_certainty`, `validation_status`, `data_integrity`,
`temporal_validity` — and applies a small, fully-listed decision table (not
a fitted or tuned score) to assign one of five `EligibilityRole` values:
`EXCLUDED` → `QUARANTINED` → `STORED` → `VALIDATED_USABLE` →
`LEARNING_ELIGIBLE`. Every assignment records its `reasons` as free-text,
so a human auditing the store can see *why* a given experience landed where
it did. The two fixed thresholds
(`MIN_OBSERVATION_COMPLETENESS_FOR_LEARNING = 0.5`,
`MIN_PROVENANCE_COMPLETENESS_FOR_LEARNING = 0.6`) are round, conservative
defaults chosen before any experiment ran — not tuned against Experiment
A–E's results (no code path in `eligibility.py` reads any experiment output
file).

A **contradicted** diagnosis is deliberately routed to `VALIDATED_USABLE`,
not `EXCLUDED` — Task 5 requires the record stay visible for future
learning (a system should be able to learn which observations produce
misleading diagnoses), it is simply excluded from diagnosis-dependent
learning paths, not from the store.

## 8. Storage architecture (Task 8)

SQLite via SQLAlchemy, reusing the exact engine/session/repository pattern
`src/storage/db.py` already established — a new, separate database file
(`data/failure_experience_dev.db`, override via
`FAILURE_EXPERIENCE_DATABASE_URL`), not a shared table with the frozen
`reliability_events` table. One row per `FailureExperience`: the full
validated object stored as a JSON blob (lossless round trip, no schema-
migration risk as the model evolves) plus indexed scalar columns mirroring
the hot retrieval filters (`workload_id`, `failure_type`,
`failure_signature`, `affected_component`, `final_status`,
`eligibility_role`, `observed_at`, `source_dataset`, `content_hash`). No
vector database, no normalized multi-table schema — at the scale this
system currently operates at (hundreds to low thousands of experiences),
that would be complexity without a corresponding capability gain (Task 8's
explicit instruction against defaulting to something heavier).

## 9. Retrieval interface (Task 10)

`src/failure_experience/retrieval.py::retrieve(repository, RetrievalQuery)`
— a plain filter composition (failure signature, failure type, workload,
component, source dataset, final status, minimum eligibility role, observed
before/after) over in-memory-filtered stored records, deterministically
sorted by `observed_at`. No semantic/embedding retrieval is implemented
(Task 10 explicitly says not to build this yet) — the interface is written
so a ranking layer could be added later without changing its contract.
Every result carries a `summary` dict answering the six questions Task 10
requires: what happened, why (per the system), what action, did it work,
how trustworthy, when
(`tests/integration/test_failure_experience_pipeline.py::
test_retrieval_summary_has_required_keys`).

## 10. Ingestion / normalization pipeline (Task 9)

```
raw dataset record (Alibaba CSV row / AIOps fault-window JSON /
AgentRx JSONL / frozen Phase 4.0 episode dict)
    -> source adapter (src/failure_experience/sources/*.py)
       maps to a NormalizedRecord (fixed, documented dict contract)
    -> ingest_record() (src/failure_experience/ingest.py)
       required-field check -> sub-object construction/validation
       -> failure_signature computation -> eligibility assessment
       -> lifecycle inference
    -> FailureExperience
```

`ingest_batch` never lets one bad record abort a batch — failures are
caught as `IngestionError`, collected in `IngestionResult.errors` with the
offending record's identifying keys, and the rest of the batch proceeds
(`tests/unit/test_failure_experience_ingest.py::
TestBatchIngestionDoesNotCrashOnPartialFailure`).

### Source adapters (Task 1 audit output, applied)

- **`sources/synthetic_episodic.py`** — reads the frozen
  `experiments/results/phase4_0/episodes.json` **read-only**; the only
  source with a full diagnosis→recovery→validation→outcome chain already
  present. `condition_id` (Phase 4.0's generator ground truth) is used only
  inside `ValidationInfo.validated_cause` (post-hoc/outcome-only), matching
  the decision-time/evaluation-only separation rule the old, frozen Phase
  4.1 already established for this same field.
- **`sources/real_agentrx.py`** — `data/processed/agentrx/*_joined.jsonl`.
  Agent-trajectory data: thin infrastructure telemetry by nature (no
  CPU/latency signal exists for an LLM-agent trajectory), but rich
  human-curated diagnosis (`root_cause_reason`, `failure_categories`, tagged
  `DiagnosisSource.HUMAN_DATASET_ANNOTATION`). Both inspected `*_joined.jsonl`
  files literally contain the string `"MISSING"` for every
  `recovery_action`/`recovery_outcome` — represented as
  `RecoveryStatus.NOT_OBSERVED`, not fabricated.
- **`sources/real_alibaba.py`** — `data/processed/alibaba_gpu2020/
  task_table.main_sample.csv`, failure = `status == "Failed"` (2,594
  available; **300 sampled**, seed 42, deterministic — see the module
  docstring for why full ingestion wasn't necessary for this
  demonstration; the sample-vs-available counts are always logged, never
  silently truncated). Resource-plan telemetry present
  (plan_cpu/mem/gpu), no diagnosis or recovery field exists in this dataset
  at all — represented honestly (`DiagnosisSource.NOT_ATTEMPTED`,
  `RecoveryStatus.NOT_OBSERVED`). Reuses the frozen Phase 3 real-data split
  manifest (`data/audit/alibaba_gpu2020/splits_random_stratified.json`) for
  `workload_context.environment`.
- **`sources/real_aiops.py`** — `data/audit/aiops_kpi/positive_windows.json`
  (81 injected-fault windows). Fault description/entity treated as a
  dataset-annotation-level diagnosis (`DiagnosisSource.
  HUMAN_DATASET_ANNOTATION`). **Known, documented limitation**: full
  per-minute telemetry (`data/processed/aiops_kpi/{business,platform}/*.csv`)
  is *not* joined into `Observations.telemetry` — only window metadata
  (duration, extractability) is captured. A genuine gap, not silently
  hidden (see §11). No recovery data, no frozen split manifest for this
  dataset (`environment="unsplit"`, matching the audit's finding that AIOps
  has no frozen train/test partition).

## 11. Known limitations (documented, not hidden)

- **AIOps telemetry join is shallow.** Only window-duration and
  extractability metadata are captured; the real per-minute business/
  platform KPI time series is not joined per-record. `Observations.
  completeness()` for AIOps experiences is correspondingly low (2/6 slots)
  — this is real, not an artifact of a bug, and is visible directly in
  Experiment A/B's per-source results.
- **AgentRx has no infrastructure telemetry at all** (0/6 `Observations`
  slots beyond `system_state`) — a genuinely different modality (LLM-agent
  trajectory vs. infra telemetry), not a defect in the adapter.
- **Real recovery/validation data does not exist anywhere in the current
  dataset suite** (confirmed by the pre-implementation audit, §3): every
  real-data `FailureExperience` has `RecoveryStatus.NOT_OBSERVED` and
  `ValidationResult.NOT_PERFORMED`. The schema supports richer recovery/
  validation representations (as demonstrated by the synthetic source), but
  no real experiment can currently populate them. This is a data
  availability gap upstream of Phase 4.1, not a schema gap.
- **AIOps and AgentRx have no frozen train/val/test split manifest** — only
  Alibaba does. `workload_context.environment` is `"unsplit"` for AIOps and
  not set (no field at all, `None`) for AgentRx; any future learning step
  consuming these sources must treat them as evaluation-only or define a
  new split before use — not silently assumed safe by this document.
- **Real-data per-record diagnosis confidence does not exist.** AgentRx and
  AIOps's "diagnosis" fields are categorical dataset annotations, not
  calibrated probabilities — `Diagnosis.confidence` is `None` for every
  real-data experience by design (a categorical label was not coerced into
  a fake confidence number).
- **The real-data detection pipeline's per-record risk score is not wired
  into any adapter.** Only aggregate AUROC/AUPRC exist in the frozen Phase
  3 real-data results; a genuine Phase 4.1.x follow-on (not fabricated
  here) would extend `scripts/real_data/phase3_*_rd_*.py` to emit
  per-record scores consumable as `Observations.performance_metrics`.
- **Reconstruction verification (§13) checks 7 documented field-groups, not
  byte-for-byte record equality** — `INTENTIONALLY_LOSSY_FIELDS` in
  `reconstruction.py` documents what's deliberately not preserved (e.g.
  AgentRx's free-text `instruction` field, dropped to avoid storing
  unstructured text beyond what the brief permits).

## 12. Baseline comparison to the old (frozen) Phase 4.1 (Task 15)

Not claimed "better" by field count alone — compared on the dimensions Task
15 lists, honestly, including where the old system wins:

| Dimension | Old Phase 4.1 (`src/experience/`) | Active Phase 4.1 (`src/failure_experience/`) |
|---|---|---|
| Information completeness | Narrow by design: `ReliabilityEvent` fields + 12-field `EpisodeProvenance` sidecar; sufficient for its one purpose (retrieval precision@k) | Broader: 11 typed sub-objects across identity/context/observation/failure/diagnosis/recovery/validation/outcome/provenance/lineage/eligibility |
| Provenance | `protocol_version` + `dataset_content_hash`, 2 fields | 10 explicit provenance fields including per-component versions |
| Temporal lineage | Single `step` integer (logical order only) | 7-stage explicit lineage with structural monotonicity validation |
| Validation support | None (no post-recovery validation concept) | Explicit `ValidationInfo` sub-object, incl. diagnosis contradiction tracking |
| Learning eligibility | None (implicit: everything in the store is usable) | Explicit 5-role eligibility with auditable reasons |
| Retrieval capability | **3 evaluated mechanisms (random/recency/similarity) with a rigorous, pre-registered precision@k/recall@k study** — the active Phase 4.1 has NOT run an equivalent retrieval-quality study; this is a genuine gap, not claimed to be superior. | Filter-based retrieval only; no similarity ranking, no evaluated precision@k |
| Reconstruction fidelity | Not evaluated in the old report | Evaluated directly (§13), 100% pass rate across all 4 sources on the checked field-groups |
| Data source breadth | Synthetic only | 3 real datasets + the same synthetic source, read read-only |
| Storage overhead | In-memory only (`ExperienceStore`), documented as adequate for its offline-benchmark scale | Persistent SQLite table; higher overhead, needed because this is meant to be a durable memory layer, not a one-shot benchmark structure |

**Honest summary**: the old Phase 4.1 is a narrower, more rigorously
*evaluated* mechanism for one specific question (does similarity retrieval
beat chance?) — that question and its PARTIALLY-SUPPORTED answer stand,
untouched. This document builds a broader, more structurally complete
*representation* substrate, but has not yet subjected its retrieval
mechanism to an equivalent precision/recall study — that remains open
future work (§14), not a claimed win.

## 13. Reconstruction / information-preservation verification (Task 12)

`src/failure_experience/reconstruction.py::verify_round_trip` checks 7
field-groups (failure identity, observations, diagnosis, recovery action,
outcome, timestamps, provenance) for every ingested record against its
source `NormalizedRecord`. Result (Experiment B, §14): **100% pass rate,
all 4 sources, all checked records** (961 total: 307 synthetic + 73 AgentRx
+ 500 Alibaba + 81 AIOps). `INTENTIONALLY_LOSSY_FIELDS` documents fields
this check does not require preserved verbatim (§11).

## 14. Experiments (Task 14) — results

Runnable via:
```bash
python benchmarks/phase4_1_active_experiments.py
```
Deterministic (Alibaba sampling seed=42, all other sources exhaustive over
available records); writes
`experiments/results/phase4_1_active/phase4_1_active_experiments.json`.

**Experiment A — Completeness.** 961 normalized records ingested across 4
sources, **0 invalid, 0 incomplete** (all source adapters produce
schema-conformant output by construction — the error path itself is
exercised directly by unit tests, not fabricated as a "0 errors" headline
result without that caveat). Per-source: synthetic 307/307 (of 960 total
episodes, only the 307 `is_failure=True` are in scope), AgentRx 73/73 (of 87
total trajectory records, 73 have `has_failure_annotation=True`), Alibaba
500/500 (of 2,594 available failed task rows, 500 sampled), AIOps 81/81 (all
81 positive fault windows).

**Experiment B — Information preservation.** 100% round-trip pass rate, all
4 sources (961/961 records, all 7 field-groups). See §13.

**Experiment C — Outcome fidelity.** Final-status distributions per source:
synthetic `{abstained: 78, failure: 184, unknown: 42, success: 3}`, AgentRx
`{failure: 73}`, Alibaba `{failure: 500}`, AIOps `{failure: 81}` (the latter
three are all-failure because none of those sources has recovery data — an
honest reflection of §11's limitation, not a modeling choice). The
synthetic action→outcome cross-tab is the key finding for Task 4's
requirement:

| `recovery.selected_action` | outcomes observed |
|---|---|
| `retry` | success: 3, failure: 1, unknown: 6 |
| `none` (no recovery) | abstained: 78, failure: 183 |
| `reconfigure` | unknown: 12 |
| `none_clean` | unknown: 23 |

**`retry` alone produces 3 distinct outcomes (success/failure/unknown)** —
directly demonstrating that action identity does not determine outcome;
context does. (This distribution surfaced a real bug during development:
an earlier version of the synthetic adapter checked `decision == "ABSTAIN"`
*before* checking whether a recovery had been attempted, which — because
every recovery attempt in this dataset happens to occur on an ABSTAIN
decision — silently collapsed every recovery's actual outcome into
"abstained". Fixed by re-ordering the check to prioritize recovery outcome;
the corrected crosstab above is what shipped. Left in this document because
it is a concrete illustration of exactly the outcome-collapsing failure
mode Task 4 warns against, caught by running the experiment rather than
assuming the adapter was correct.)

**Experiment D — Temporal integrity.** 961 experiences, **0 lineage
monotonicity violations** (structurally guaranteed by the pydantic
validator, empirically confirmed). Partitioning the full experience set at
the median `observed_at` cutoff: 481 before / 480 after, **sums to 961,
zero overlap** — directly demonstrates the "which experiences were
available before time T" capability required to prevent future information
leaking into an earlier evaluation boundary.

**Experiment E — Provenance integrity.** 50-record sample per source (200
total): **100% traceable** to a non-empty `raw_record_ref`, **100%** with a
`dataset_content_hash` present.

**Not fabricated**: no experiment result above was adjusted after being
computed; the Experiment C bug described above was found and fixed *before*
any result was written to this document, not after seeing an
inconvenient number.

## 15. Automated tests

75 new tests (`tests/unit/test_failure_experience_{schema,eligibility,
ingest}.py` [52 tests] + `tests/integration/test_failure_experience_
pipeline.py` [23 tests]) — covering schema validation, required/optional
fields, invalid records, batch ingestion with partial failure, source-
adapter correctness, persistence, retrieval (by signature/type/workload/
component/dataset/status/eligibility/temporal-range), idempotency,
round-trip reconstruction, provenance traceability, temporal-lineage
integrity, Alibaba split-label leakage protection, and a direct assertion
that this package never imports the frozen `src.experience`/`src.patterns`
packages. **Full repository suite: 360/360 passing** (`python -m pytest
tests/ -q`), including every pre-existing Phase 1–4.2 test — no regression.

## 16. Formal status

# 🟢 PASS

- Canonical `FailureExperience` representation implemented, with
  observation/interpretation separation enforced structurally (not by
  convention).
- Successful, failed, partial, abstained, and unresolved-recovery
  experiences are all representable and were all actually observed in
  Experiment C's real output (not merely designed-for).
- Failed/contradicted diagnoses are preserved, not overwritten (§5,
  directly tested).
- Provenance and temporal lineage are structurally enforced and empirically
  verified (Experiments D & E).
- Learning eligibility is explicit, auditable, and not tuned against any
  experiment's output.
- Persistent storage, ingestion/normalization, and a filter-based retrieval
  interface all exist and are tested end-to-end across all 4 sources.
- Reconstruction/information-preservation is directly verified (100% pass
  rate, documented lossy fields).
- Old Phase 4.1/4.2 and revised Phase 3 remain frozen and untouched
  (verified both by not editing those files and by a direct test
  asserting no import dependency on them).
- No Phase 4.2-class learning system was implemented (Task 18 respected).

**What is NOT claimed**: this document does not claim the new
representation is a strict improvement on the old, narrower Phase 4.1 —
§12 states plainly where the old system remains ahead (an evaluated
retrieval-quality study). It does not claim real recovery/validation data
exists where it does not (§11). It does not claim AIOps telemetry is fully
joined (§11). These are reported as open items for a future Phase 4.1.x or
Phase 4.2, not silently smoothed over.

## 17. Reproducibility

```bash
# tests
python -m pytest tests/unit/test_failure_experience_schema.py \
                  tests/unit/test_failure_experience_eligibility.py \
                  tests/unit/test_failure_experience_ingest.py \
                  tests/integration/test_failure_experience_pipeline.py -v
python -m pytest tests/ -q   # full repo suite, 360 tests

# experiments (deterministic; overwrites only files under
# experiments/results/phase4_1_active/)
python benchmarks/phase4_1_active_experiments.py
```

No step modifies `data/unified_dev.db` (new writes go to the separate
`data/failure_experience_dev.db`), any file under `experiments/results/
phase4_0/`, `experiments/results/phase4_1/`, `experiments/results/
phase4_2/`, or any `docs/PHASE3_*.md` / `docs/PHASE4_1_FAILURE_MEMORY.md` /
`docs/PHASE4_2_FAILURE_PATTERNS.md`.

## 18. Phase 4.2+ readiness

The memory layer is ready to be consumed by a future pattern-/policy-
learning phase **through the `EligibilityRole.LEARNING_ELIGIBLE` filter**
(`RetrievalQuery(min_eligibility=EligibilityRole.LEARNING_ELIGIBLE)`) —
no redesign of the storage or retrieval contract should be required. Before
a learning phase begins, it should additionally: (a) decide how to handle
sources with no frozen split (AIOps, AgentRx) — treat as evaluation-only
until a split is defined, per §11; (b) if real per-record diagnosis/
recovery data becomes available, extend the relevant source adapter (not
the core schema, which already has the fields) — no schema change needed;
(c) if a retrieval-quality study (precision@k-style) is wanted for the new
schema, design and pre-register it the same way the old Phase 4.1 did,
rather than assuming the broader representation is automatically better
for retrieval.


---

<a id="phase4-2-active-plan"></a>
# PHASE4 2 ACTIVE PLAN
**Status: PLANNING (not yet implemented)**  
**Original file:** `docs/PHASE4_2_ACTIVE_PLAN.md`  
**Role:** ACTIVE Phase 4.2 plan: reassessment and research plan for failure pattern learning on the post-real-data foundation. Planning only -- awaiting approval, not yet implemented.

# ACTIVE PHASE 4.2 — Failure Pattern Learning: Reassessment & Implementation Plan

**Status: PLANNING ONLY. No Phase 4.2 code, experiments, or models exist
yet.** This document is the complete research plan required before any
active Phase 4.2 implementation begins, per the same discipline
`docs/PHASE4_PLAN.md` and `docs/PHASE4_1_FAILURE_MEMORY.md`'s protocol
freezing already established for this project. Nothing under
`src/patterns/`, `docs/PHASE4_2_FAILURE_PATTERNS.md`,
`experiments/results/phase4_2/`, `src/failure_experience/`, any
`docs/PHASE3_*.md`, or any dataset file was modified while producing this
plan — every finding below came from read-only inspection (documented
inline with the exact command/file used, so it is checkable).

---

## 1. Historical context

```
OLD Phase 4.0 (synthetic episodic data)
  └─▶ OLD Phase 4.1 (src/experience/) → H1 PARTIALLY SUPPORTED (frozen)
       └─▶ OLD Phase 4.2 (src/patterns/) → H2 INCONCLUSIVE (frozen)
              │
              ▼ [project pauses old Phase 4 sequence]
REAL DATA EXPANSION (AgentRx, AIOps 2020, Alibaba GPU 2020)
  └─▶ REVISED real-data Phase 3 (docs/PHASE3_REAL_DATA_3_6_DECISION.md)
       └─▶ [deliberate pause + reassessment]
              └─▶ ACTIVE Phase 4.1 (src/failure_experience/) → PASS
                     └─▶ THIS DOCUMENT: ACTIVE Phase 4.2 reassessment & plan
```

The old Phase 4.2's `INCONCLUSIVE` verdict is **not touched** by anything in
this document (Task 13). Nothing here implies the old result was wrong,
right, or resolved — it is a separate, earlier experiment on separate,
frozen data.

## 2. Old Phase 4.2 audit (Task 1)

Read in full: `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/{schema,
discovery,metrics}.py`, `configs/phase4_2_pattern_protocol.json` (referenced
throughout the doc), `experiments/results/phase4_2/*.json`. Not modified.

| Question | Finding |
|---|---|
| 1. What it attempted to prove | Whether recurring `(workload_id, diagnosed_cause)` relationships in the synthetic episode stream are detectable above chance, with four-tier confidence separating observed/inferred/confirmed/uncertain evidence. |
| 2. Hypothesis | H2 (frozen, `configs/phase4_2_pattern_protocol.json`) — see quote in the brief §"Old Phase 4.2". |
| 3. Data used | `experiments/results/phase4_0/episodes.json` (the same frozen synthetic file the active Phase 4.1 also reuses read-only), restricted to `is_failure=True AND diagnosed_cause is not None` — CRITICAL-tier rows only (diagnosis is only computed for CRITICAL tier under the frozen Phase 3.6 policy). |
| 4. What "pattern" meant | A candidate keyed by `(workload_id, diagnosed_cause)`; the claim is a **symptom→cause** relationship — does this diagnosed cause, for this workload, reliably map to one true `condition_id`. |
| 5. Ground truth | `condition_id`, Phase 4.0's generator-assigned ground truth — evaluation/discovery-only, never exposed to `PatternQuery`. |
| 6. Metrics | Precision/recall of "flagged" candidates against test-split row coverage; tier calibration (true-structure rate per tier) — the latter could not actually be checked (§10 below). |
| 7. Baselines | A (no pattern learning), B (naive frequency, `n_train≥3`), C1 (proposed tiered), C2 (ablation: purity threshold only, no tiering). |
| 8. Why INCONCLUSIVE | Pre-registered `minimum_evaluable_n = 10` covered test rows; actual = 7. The rule (not the point estimates) determined the verdict — this was mandated regardless of which way the numbers leaned. For the record, point estimates were directionally unfavorable to the tiered method (B's precision 0.333 beat C1's 0.286 at equal recall). |
| 9. Reusable methodology | The **four-tier evidence concept** (recurrence fact vs. inferred relationship vs. validated relationship vs. insufficient evidence) is dataset-agnostic reasoning, not synthetic-specific. The **decision-time/evaluation-only structural type split** (`PatternQuery` excludes ground truth by construction) is a reusable design pattern. The **leakage-audit methodology** (contaminate train with test, verify candidates change) is directly reusable. |
| 10. Assumptions no longer valid | (a) That `diagnosed_cause` exists as a per-record field — it does not exist for ANY real dataset (Phase 3's real-data pipeline produces only an aggregate detection score, not a per-record diagnosis; see §4 below). (b) That a single `condition_id`-style ground truth exists to define "true structure" — no real dataset has this. (c) That workload identity recurs at a fine grain — false for Alibaba job-level (§4.4). (d) That temporal spacing is a generator artifact worth measuring on synthetic data — real datasets have genuine, non-deterministic temporal structure the synthetic generator's constant-gap round-robin schedule cannot represent (old Phase 4.2 §13 found **zero** temporal clustering, by construction, in the synthetic stream). |
| 11. Reusable read-only | `src/patterns/schema.py`'s tier-concept and `PatternQuery`-style structural leakage prevention (as a **design template**, not imported code — same relationship the old Phase 4.2 itself had to Phase 4.1's `DecisionTimeQuery`). The leakage-audit pattern (`benchmarks/phase4_2_leakage_audit.py`'s 5-check structure) as a template. |
| 12. NOT to be reused | The `(workload_id, diagnosed_cause)` candidate key itself (no real dataset has `diagnosed_cause`); the purity-against-`condition_id` metric (no real dataset has an analogous single ground-truth label); the exact tier thresholds (`TAU_INFERRED=0.6` etc. — tuned/chosen for a 28-row synthetic population, not re-derivable as appropriate for real data without a fresh, pre-registered choice). |
| 13. Compatibility with `FailureExperience` | **Not directly compatible.** Old `PatternCandidate`/`PatternQuery` are built on the old `Experience`/`EpisodeProvenance` types (`src/experience/schema.py`), which the active Phase 4.1 does not use. A new pattern representation must be built against `FailureExperience` (`src/failure_experience/schema.py`) fields (`failure.failure_signature`, `workload_context`, `diagnosis`, `outcome.final_status`, `eligibility.role`) — see §11. |

## 3. Active Phase 4.1 audit — what Phase 4.2 can actually consume (Task 2)

Re-read `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` and
`src/failure_experience/{schema,ingest,storage,retrieval,reconstruction,
sources/*}.py` in full for this plan. Below is the field-population audit
by dataset, derived from the source adapters themselves (not assumed):

| Information | Synthetic (phase4_0) | AgentRx | Alibaba | AIOps |
|---|---|---|---|---|
| Observed telemetry (`Observations.telemetry`) | Yes — 5 synthetic features per record | **No** — 0 fields (agent-trajectory data has no infra telemetry) | Yes — via `resource_metrics` (plan_cpu/mem/gpu), not `telemetry` | Partial — `resource_metrics.window_duration_minutes` only; no per-minute KPI join (documented shallow-join limitation) |
| Failure labels (`FailureInfo`) | `failure_type="synthetic_injected_condition"` (constant), `condition_id` is the real label but lives only in `ValidationInfo.validated_cause`, post-hoc | `failure_categories` list (multi-label), `failure_type`=first category | `failure_type="task_terminated_failed"` (constant — status-code derived, no finer typing) | `failure_type=fault_desrcibtion` (5 distinct values: network delay/CPU fault/network loss/db connection limit/db close) |
| Failure signature (`FailureInfo.failure_signature`) | hash(type, workload_id, workload_type) — low cardinality (1 workload_type) | hash(category, domain, "llm_agent_trajectory") | hash("task_terminated_failed", task_name, "alibaba_gpu_cluster_job") | hash(fault_desrcibtion, entity, workload_type) |
| Diagnosis (`Diagnosis`) | Present for 46/307 failures (reused frozen Phase 3.6 rule, CRITICAL-tier only) | Human-curated `root_cause_reason` text, `source=HUMAN_DATASET_ANNOTATION` | **`source=NOT_ATTEMPTED`** — no diagnosis field exists in this dataset at all | Fault description/entity as `HUMAN_DATASET_ANNOTATION` (injected-fault ground truth, not a live diagnosis) |
| Diagnosis confidence | **None** (deterministic rule has no confidence) | **None** (categorical annotation) | **None** (no diagnosis) | **None** (categorical annotation) |
| Temporal information | Synthetic `step` integer, deterministic round-robin (old Phase 4.2 §13: zero clustering, by construction) | Synthetic timestamp anchor (`sources/_util.py`, no real wall-clock exists) — **not usable for real temporal-clustering analysis** | Real trace-relative seconds (`start_time`/`end_time`), genuine ordering | **Real wall-clock** (`onset`, window bounds) — the only source with genuine, non-synthetic temporal structure |
| Workload identity | `workload_id` (4 distinct, each recurs many times by generator design) | `domain` (2 distinct: `tau_bench_retail`, `magentic_one_web_file_agent`) | `job_name` (unique per failed row in the sampled table — see §4.4, **does not recur**) / `task_name` (7 distinct, recurs heavily) | `entity` (16 distinct among faulted entities, recurs up to 10×) |
| Recurrence identity (usable key) | `(workload_id, diagnosed_cause)` — old Phase 4.2's key, still computable on this source only | `(domain, failure_category)` | `(task_name, gpu_type)` — NOT `(job_name, ...)` | `(entity, fault_desrcibtion)` |
| Recovery information | Present for 46/307 (retry/reconfigure/rollback + outcome) | **`NOT_OBSERVED`** (dataset literally encodes `"MISSING"`) | **`NOT_OBSERVED`** (no field in dataset) | **`NOT_OBSERVED`** (no field in dataset) |
| Validation information | Present for 4/307 (`recovery_correct` non-null) | **`NOT_PERFORMED`** | **`NOT_PERFORMED`** | **`NOT_PERFORMED`** |
| Outcome (`OutcomeInfo.final_status`) | `{abstained, failure, unknown, success}` all observed | `failure` only | `failure` only | `failure` only |
| Provenance | Full (10 fields) | Full, `dataset_content_hash` present | Full, incl. reused Phase 3 split label | Full |
| Train/val/test status | `environment` = split (from generator) | **No frozen split** (`environment` unset) | **Frozen split reused** (`environment` = train/val/test via `data/audit/alibaba_gpu2020/splits_random_stratified.json`) | **No frozen split** (`environment="unsplit"`, confirmed in Phase 3 real-data comparison doc) |

**This table is the single most important input to Task 3–6 below.** It
shows, concretely, that no uniform pattern-learning task is possible across
all four sources — they differ in workload-identity granularity, diagnosis
availability, temporal genuineness, and split availability along
independent axes.

## 4. Dataset-specific scientific validity (Task 4)

Additional read-only statistics computed for this plan (all reproducible;
exact code shown so the numbers are checkable, not asserted):

### 4.1 AgentRx

```python
# 87 total AgentRx records (tau_retail_joined.jsonl + magentic_joined.jsonl), 73 have has_failure_annotation=True
# domains: magentic_one_web_file_agent=44, tau_bench_retail=29
# 24 distinct individual failure_categories values across the 73 failures;
#   top individual categories: "Instruction/Plan Adherence Failure" (25),
#   "Misinterpretation of Tool Output" (24), "Guardrails Triggered" (23)
# 29 distinct (sorted) failure_category COMBINATIONS across 73 failures --
#   most common combo recurs 9 times (single-category "Intent Plan Misalignment")
```

- **Episode** = one agent trajectory (`trajectory_id`), already a complete
  unit (not decomposable into sub-events with the current joined data).
- **Failure** = `has_failure_annotation=True`; can co-occur with multiple
  `failure_categories` (multi-label, not single-label).
- **Pattern** = recurrence of a `(domain, failure_category)` or
  `(domain, category_combo)` pairing — this is a **behavioral/cognitive
  failure-mode recurrence pattern**, not an infrastructure failure pattern.
  AgentRx has zero CPU/memory/latency telemetry; forcing an
  infrastructure-failure framing onto it (as the original H2's "condition
  recurrence, symptom→cause" language implicitly assumes) would misrepresent
  the data. The valid framing is: *does this agent domain reliably exhibit
  the same class of reasoning/tool-use failure?*
- **Temporal recurrence**: **NOT CURRENTLY EVALUABLE** — no real timestamp
  exists in the joined data (`"timestamp": "MISSING"` in the raw file,
  confirmed directly), so occurrence ordering cannot be measured on
  wall-clock or trace-relative time at all, only on file-row order (which
  is not meaningful).
- **Repeated workload identity**: only at the `domain` granularity (2
  values) — individual `trajectory_id`s do not recur (each trajectory is a
  one-off episode). This is coarse but genuine.
- **Split status**: no frozen split. Only 73 usable failure rows total, 2
  domains — splitting further would leave very small per-domain cells.

**Verdict**: AgentRx supports a **descriptive, exploratory** domain×category
recurrence analysis; it does **not** currently support a temporally-ordered
or train/test-evaluated pattern-learning claim (no timestamp, no split, and
n=73 is small once split two ways).

### 4.2 AIOps 2020

```python
# 81 positive fault windows, 16 distinct entities (max 10 occurrences: docker_001)
# objects: docker=49, os=20, db=12; fault types: network delay=31, CPU fault=19,
#   network loss=19, db connection limit=7, db close=5
# Negative (non-fault) population EXISTS and was already frozen by real-data Phase 3 prep:
#   data/audit/aiops_kpi/negative_window_natural_population.json -- 45,911 candidate
#   normal windows across 43 entities / 15 days ("FULL eligible population, not the
#   extracted/sampled pool" per that file's own `note` field)
#   data/audit/aiops_kpi/negative_windows_sampled.json -- the actual sampled/frozen
#   negative set used by Phase 3's real-data evaluation (reusable read-only)
```

- **Episode** = one injected-fault window (`fault_index`).
- **Failure** = the fault itself; **fault type + entity are both directly
  observable ground-truth-quality labels** (injected by the 2020 challenge
  organizers, not inferred) — stronger label quality than AgentRx's
  human-annotated categories or Alibaba's status-code-only labeling.
- **Temporal recurrence**: **genuinely evaluable** — real `onset`
  timestamps exist across 11 distinct days; this is the *only* source with
  authentic (non-generator-determined) temporal structure, making it the
  right place to test whether faults cluster in time (the exact question
  old Phase 4.2 §13 found trivially null on synthetic data by construction).
- **Recurrence definition**: `(entity, fault_desrcibtion)` — e.g. does
  `docker_001` reliably fault with a specific fault type. With only 81
  positive windows over up to 16×5=80 possible combos, most cells will have
  n=1-2 — a real, load-bearing small-sample constraint, flagged honestly
  rather than hidden.
- **Shallow telemetry integration**: sufficient for entity/fault-type
  recurrence and temporal-clustering analysis (neither requires the
  per-minute KPI join). **Not** sufficient for a telemetry-signature-based
  pattern claim ("do these three metrics jointly predict this fault type")
  — that would require the deeper join flagged as a Phase 4.1 limitation.
  This plan does **not** require the deeper join for its smallest-valid
  version (§14); it is listed as an optional strengthening prerequisite
  (§12/Task 12).
- **No frozen split**: confirmed (`docs/PHASE3_REAL_DATA_COMPARISON.md`'s
  own H3 finding, carried into active Phase 4.1 §11 verbatim). Using AIOps
  for a train-fit-then-test-evaluate claim without first building a split
  would be exactly the "silently assume unsplit data is safe for learning"
  error Task 8 warns against.

**Verdict**: AIOps supports (a) a **descriptive** entity×fault-type
recurrence analysis, (b) a **genuinely novel, evaluable temporal-clustering
question** (do faults burst vs. arrive uniformly — using real timestamps,
unlike synthetic's null-by-construction case), using the already-frozen
negative-window population for a proper base-rate comparison if desired.
It does **not** currently support a scored train/test pattern-precision
claim (no split) — flagged as a prerequisite-gated capability, not silently
assumed away.

### 4.3 Alibaba GPU 2020

```python
# task_table.main_sample.csv (the frozen Phase 3 real-data cleaned sample): 11,750 rows, 2,594 Failed
# job_name recurrence among FAILED rows: 2,594 distinct job_names for 2,594 failed rows -- ZERO jobs
#   have more than one failed task row in this sample.
# Checked against the FULL cleaned population (task_table.clean.csv, 1,261,050 rows, 256,762 Failed):
#   256,755 distinct job_names among 256,762 failed rows -- only 7 jobs (out of 256,755) have >1
#   failed task. This is NOT a sampling artifact -- it is a genuine property of the underlying data
#   (per data/audit/alibaba_gpu2020/sampling_report.json, sampling was stratified by
#   status|gpu_type|quarter at the JOB level, one row per job -- but even the full unsampled
#   population shows job-level failure recurrence is a ~0.003% edge case).
# task_name recurrence among failed rows: 7 distinct values, "tensorflow"=2004/2594 (77.3%)
# gpu_type recurrence among failed rows: "MISC"=2057/2594 (79.3%)
# Rate comparison (failed vs. terminated), same sample:
#   gpu_type="MISC": 79.3% of failures vs. 52.2% of terminations (elevated)
#   task_name="tensorflow": 77.3% of failures vs. 46.7% of terminations (elevated)
```

- **Workload identity**: `job_name` does **not** recur (confirmed above,
  on both the sample and the full population) — a genuinely important,
  non-obvious finding that rules out a `job_name`-keyed pattern task
  entirely, for a real structural reason, not a code limitation.
  `task_name` (task *type*, e.g. "tensorflow", "worker") is the identity
  that actually recurs, and should be used instead.
- **Failure recurrence** = elevated failure *rate* for a
  `(task_name, gpu_type)` combination relative to the population base rate
  — a **different pattern shape** than old Phase 4.2's symptom→cause purity
  question (Alibaba has no diagnosis layer to be the "symptom" side; it
  does have a full success/failure population to compute rates from, which
  synthetic's CRITICAL-tier-only population did not).
- **Telemetry dimensions available**: `plan_cpu`, `plan_mem`, `plan_gpu`,
  `gpu_type`, `inst_num` — enough to define a small number of coarse
  resource-profile buckets if a richer-than-`(task_name, gpu_type)` pattern
  key is later wanted (not proposed as the primary key here, to keep the
  smallest-valid version simple — see §14).
- **Frozen split**: **yes**, reused directly from
  `data/audit/alibaba_gpu2020/splits_random_stratified.json` (already wired
  into `workload_context.environment` by the active Phase 4.1's adapter).
  A temporal split (`splits_temporal.json`) also exists and was already
  used by Phase 3's real-data H3 experiment — available if a
  temporally-honest (rather than random-stratified) split is preferred for
  Phase 4.2 (recommended — see §8).
- **Sample size**: 11,750 rows in the frozen cleaned sample (2,594 failed),
  vastly larger than old Phase 4.2's 28/4/14 train/val/test rows — the
  single-biggest scientific advantage of the real-data foundation for this
  question.

**Verdict**: Alibaba is the **strongest** candidate for a rigorously
train/val/test-evaluated pattern-learning hypothesis — real, adequate
sample size, a frozen (in fact, two frozen) split(s), and a genuine,
measurable, non-trivial recurrence signal (§4.3's rate comparison above).
It requires reformulating the pattern claim from "symptom→cause purity"
to "context→failure-rate elevation," a scope change this plan makes
explicitly (see §6).

### 4.4 Synthetic episodic data — role in active Phase 4.2

Per the brief's explicit instruction not to automatically discard or
equate it with real data:

- **Not used as a source of new real-world evidence** for the active
  Phase 4.2 hypotheses (§6) — its `condition_id`/`diagnosed_cause`
  structure exists nowhere in real data, so any result on it cannot
  generalize to a real-data claim.
- **Retained as a methodological validation / regression testbed**: the
  active Phase 4.2's new pattern-detection code (a *new* implementation, in
  a *new* namespace, never importing `src/patterns/`) can be run against
  this same frozen synthetic file to sanity-check that the new mechanism's
  behavior is reasonable on a dataset whose ground truth is fully known —
  analogous to a unit-test-with-real-shaped-data, not a Phase 4.2 result.
  Its role is explicitly **methodological validation and ablation
  support**, stated here rather than left ambiguous.
- **Not used for temporal-clustering analysis** — old Phase 4.2 §13 already
  established (and this document does not re-litigate) that the generator's
  round-robin schedule produces zero clustering by construction; re-running
  that exact check on the same frozen data would add no new information.

## 5. Operational definition(s) of "pattern" (Task 5)

The brief's four-tier vocabulary (`OBSERVED` / `INFERRED` / `CONFIRMED` /
`UNCERTAIN`) is **retained as a concept**, because it separates "this
recurs" from "this recurs *and* looks directionally real" from "this is
independently replicated" from "not enough evidence yet" — a distinction
that is dataset-agnostic and does not depend on synthetic-specific
mechanics. It is **not** retained as a fixed set of numeric thresholds (old
`TAU_INFERRED=0.6` etc. were chosen for a 28-row synthetic population and
have no claim to be appropriate elsewhere) — new, pre-registered thresholds
must be chosen per dataset before evaluation, exactly as the old protocol
did, not silently inherited.

**Two formally distinct pattern types** are defined (both measurable with
current data, on different datasets — see §10 for why they are not pooled):

### Pattern Type 1 — Context-conditioned failure-rate elevation (Alibaba primary; Alibaba is the only dataset with the population structure to support this rigorously)

| Property | Definition |
|---|---|
| Input representation | `(task_name, gpu_type)` pair, computed over ALL rows (Failed + Terminated + Running), not only failures |
| Unit of analysis | One candidate context key |
| Context | Alibaba GPU cluster job/task submissions |
| Minimum evidence | `n_train >= N_MIN` total (not-just-failed) occurrences of the key (threshold pre-registered before evaluation, not chosen post hoc — see §8) |
| Recurrence definition | The key itself recurring (`n_train >= N_MIN`) is the OBSERVED-tier bar; INFERRED requires the train-split failure rate for the key to exceed the train-split overall base rate by a pre-registered margin; CONFIRMED requires the SAME elevation to replicate on the validation split |
| Temporal constraints | None required for this pattern type (rate-based, not sequence-based) — Alibaba's split is available in both random-stratified and temporal form; the temporal split is preferred (§8) to avoid any risk of near-duplicate jobs leaking rate information across the random split |
| Ground truth | None needed beyond the observed Failed/Terminated/Running label itself — this is a directly observable outcome, not an inferred proxy |
| Observed vs. inferred | The *rate elevation* is inferred from observed labels; the underlying resource/task combination is directly observed |
| Confidence/evidence representation | Tier + `(n_train, train_rate, baseline_rate, n_validation, validation_rate)` |
| Evaluation target | Does a train-discovered elevated-rate context replicate its elevation on held-out (validation/test) data, at a rate better than a naive frequency-only baseline? |

### Pattern Type 2 — Recurring failure-mode / fault-entity association (AIOps + AgentRx, descriptive-only given no frozen split — see §8)

| Property | Definition |
|---|---|
| Input representation | AIOps: `(entity, fault_desrcibtion)`. AgentRx: `(domain, failure_category)` |
| Unit of analysis | One candidate association key |
| Context | AIOps: injected-fault windows. AgentRx: agent trajectories |
| Minimum evidence | `n >= 2` (matches old Phase 4.2's candidacy floor — still a defensible generic minimum for "this is not a singleton") |
| Recurrence definition | The exact key recurring at least twice in the available (unsplit) data |
| Temporal constraints | AIOps only: onset timestamps enable a genuine burstiness/temporal-clustering sub-analysis (gap variance vs. a uniform-arrival null), independent of the entity×fault-type association itself. AgentRx: **NOT CURRENTLY EVALUABLE** (no real timestamp exists) |
| Ground truth | AIOps: the injected fault label IS the ground truth (organizer-assigned) — recurrence of the label itself is the finding, there is no separate "true cause" to validate the label against. AgentRx: the human-annotated category IS the closest available ground truth, same structure |
| Observed vs. inferred | Purely OBSERVED-tier by construction for this pattern type on these two sources — see next point |
| Confidence/evidence representation | Because there is no frozen validation split for either source, **no candidate can ever reach the CONFIRMED tier** for Pattern Type 2 as currently scoped (CONFIRMED structurally requires independent validation-split replication) — this is stated as a structural ceiling, not an oversight. Candidates land in OBSERVED (n≥2, no purity claim needed since there's no wrong/right cause to be pure about) or are excluded (n<2) |
| Evaluation target | Descriptive report of recurring associations and (AIOps only) temporal clustering — **not** a scored precision/recall claim (no held-out set exists to score against) |

Any other pattern category from the brief's list (workload-specific
patterns beyond what's covered above, failure sequence patterns,
cross-episode chains, repeated anomaly trajectories, structurally-similar
failure-experience clustering) is marked:

**NOT CURRENTLY EVALUABLE** — reasons:
- *Failure sequence / progression patterns*: would require multiple
  ordered observations *within* one episode (a trajectory of states leading
  to failure), which none of the four sources currently expose at
  sub-episode granularity in the ingested `FailureExperience` records
  (AgentRx's `num_steps` is a count, not a per-step trace; Alibaba/AIOps
  are single-point-in-time task/fault records).
- *Cross-episode / cross-dataset structural-similarity clustering* (e.g.
  KMeans over `FailureExperience` embeddings): technically buildable (see
  §11's discussion of `src.failure_memory.embedding.FailureEmbedder`), but
  would conflate four incompatible modalities (§10) into one embedding
  space without a defensible shared feature set — not attempted as a
  primary mechanism; a candidate *ablation only within Alibaba* (§15), not
  a cross-dataset pattern claim.
- *Diagnosis→outcome / cause→outcome chains*: only synthetic has both a
  diagnosis and a validated outcome on the same records (46 recovery
  attempts, 4 validated) — reused as a **secondary, descriptive-only**
  analysis exactly as old Phase 4.2 §13 did (methodological validation
  role, §4.4), not a primary active-Phase-4.2 claim.

## 6. Reassessing H2 (Task 6)

**Decision: E — split into multiple independently-testable, dataset-scoped
hypotheses.** Justification: §3's field-population table and §4's
per-dataset audit show the four sources differ on every axis H2 implicitly
assumed uniform (workload-identity grain, presence of a diagnosis layer,
genuineness of temporal structure, split availability). Task 10 explicitly
forbids merging heterogeneous datasets merely for sample size; pooling them
under one H2 would either silently privilege whichever source has the most
rows (Alibaba, by two orders of magnitude) or require an artificial common
representation this audit found no defensible basis for (§5, "NOT
CURRENTLY EVALUABLE" list).

This is **new research**, not a "correction" of the old H2 — the old H2
remains exactly as frozen, evaluated on synthetic data, INCONCLUSIVE.

- **H2-Alibaba** (primary, rigorously evaluable): Certain
  `(task_name, gpu_type)` context combinations exhibit a failure-rate
  elevation, discoverable on train data, that replicates on held-out
  validation/test data at a rate better than a naive frequency-count
  baseline.
- **H2-AIOps** (exploratory/descriptive, not formally hypothesis-tested
  until a split exists — §8/§12): Fault entities exhibit recurring
  associations with specific fault types, and fault onsets are temporally
  clustered rather than uniformly distributed.
- **H2-AgentRx** (exploratory/descriptive, same constraint): Agent domains
  exhibit recurring associations with specific failure-mode categories.
- **Synthetic**: not a hypothesis-bearing source for active Phase 4.2 (§4.4)
  — used only for methodological validation of the new pattern-detection
  mechanism's implementation correctness.

## 7. Baselines (Task 7)

| Baseline | Applies to | Justification |
|---|---|---|
| A — no pattern learning (independent-incident treatment) | All | Same role as old Phase 4.2's baseline A: the floor every proposed mechanism must clear to justify existing at all. |
| B — naive frequency-count flagging (flag any key with `n_train >= N_MIN`, no rate/purity check) | H2-Alibaba | Directly comparable to old Phase 4.2's baseline B; still scientifically appropriate — it isolates whether *any* rate-awareness beyond raw recurrence count adds value. |
| C — proposed: tiered rate-elevation detection (Pattern Type 1, §5) | H2-Alibaba | The method under test. |
| D — existing frozen clustering (`src.failure_memory.embedding.FailureEmbedder`), as a candidate alternative context-bucketing mechanism instead of raw `(task_name, gpu_type)` keys | Optional ablation only (§15), not a primary baseline | Per §11's reuse audit: worth checking whether an embedding-based grouping outperforms the hand-chosen categorical key, but not assumed superior — same "reuse is not automatically adequate" posture old Phase 4.2 took toward this exact component. |

No baseline is proposed for H2-AIOps/H2-AgentRx beyond descriptive
frequency counts (Pattern Type 2, §5) — a precision/recall-style baseline
comparison requires a held-out set that does not exist for these two
sources (§8).

## 8. Evaluation protocol / leakage prevention (Task 8)

**Alibaba (H2-Alibaba)**:
- Reuse the frozen **temporal** split
  (`data/audit/alibaba_gpu2020/splits_temporal.json`) as primary, not the
  random-stratified split — a rate-elevation claim is more exposed to
  leakage under random splitting (near-duplicate jobs from the same
  submission burst could land in both train and test) than a
  strictly-temporal split guards against. The random-stratified split is
  reused as a secondary/sensitivity check, not the primary evaluation
  (mirrors Phase 3's real-data H3 experiment design, which used exactly
  this same distinction).
- **Discovery** (train only): compute `(task_name, gpu_type)` failure rates
  from train-split rows only.
- **Threshold/tier calibration** (validation only): CONFIRMED-tier
  replication check performed against validation-split rows only, same
  role as old Phase 4.2's validation use — never touches test.
- **Frozen test** (touched exactly once, at the end): final precision/
  recall of train-discovered, validation-confirmed candidates against
  test-split rate elevation.
- Information available at decision time vs. only after: a candidate's
  identity `(task_name, gpu_type)` is available at submission time (before
  the job's outcome is known); its *rate* is discovery/evaluation-only
  information, exactly parallel to `diagnosed_cause`/`condition_id`'s
  decision-time/evaluation-only split in old Phase 4.1/4.2 and active Phase
  4.1's `DecisionTimeQuery`/`PatternQuery`-style structural types. A new
  `PatternQuery`-equivalent type will be built (§11) that can carry
  `(task_name, gpu_type)` but structurally cannot carry a rate/label.
- Repeated incidents: since `job_name` does not recur (§4.3), there is no
  "same job appears in both train and test" leakage risk at the job level;
  the leakage risk is instead about `(task_name, gpu_type)` *tuples*
  recurring across the split boundary, which is expected and is precisely
  what discovery→replication is meant to measure (not a leak).

**AIOps and AgentRx**: **no frozen split currently exists for either.**
Per Task 8's explicit instruction not to silently assume unsplit data is
safe for learning, both are treated as **evaluation-only / descriptive**
for active Phase 4.2 — patterns are reported (recurrence counts, and for
AIOps, temporal clustering statistics) but **no train-fit-then-test-score
claim is made**. Building a frozen split for either is listed as optional
prerequisite work (§12), not silently worked around.

**Synthetic**: used only for methodological validation (§4.4); if that
validation run needs a split, it reuses the same frozen `split` field
Phase 4.0 already assigned (never re-derived).

## 9. Metrics (Task 9)

| Metric | Applies to | Definition | Data source | Notes |
|---|---|---|---|---|
| Rate-elevation precision | H2-Alibaba | Of candidates flagged (train-discovered, validation-confirmed) as elevated-risk, fraction whose test-split failure rate is *also* elevated over the test-split baseline by the same pre-registered margin | Alibaba test split | Directly analogous to old Phase 4.2's precision, but against a *rate* criterion instead of a single-label purity criterion |
| Rate-elevation recall | H2-Alibaba | Of all test-split `(task_name, gpu_type)` combinations whose test-split rate is actually elevated, fraction that were flagged by train discovery | Alibaba test split | |
| False pattern rate | H2-Alibaba | Of flagged candidates, fraction whose test-split rate is NOT elevated (= 1 − precision, reported separately per Task 9's explicit list) | Alibaba test split | |
| Tier calibration | H2-Alibaba | Does test-split precision actually increase CONFIRMED > INFERRED > OBSERVED, measured, not asserted | Alibaba test split, stratified by discovered tier | Mirrors old Phase 4.2's (unresolvable, due to n=7) tier-calibration goal — Alibaba's much larger n makes this plausibly checkable this time, not guaranteed |
| Recurrence detection rate | AIOps, AgentRx | Fraction of entities/domains with `n>=2` fault/failure occurrences whose top recurring key accounts for `>= X%` of their occurrences | Full (unsplit) AIOps/AgentRx data | Descriptive only, no precision/recall (no held-out set) |
| Temporal clustering statistic | AIOps only | Observed inter-fault-onset gap variance per entity vs. a uniform-arrival null (same statistic old Phase 4.2 §13 computed on synthetic, here computed on **real** onsets) | AIOps positive windows, real `onset` timestamps | The one metric where AIOps's genuine (non-generator) temporal structure adds new information the synthetic source structurally cannot |
| Pattern confidence calibration (four-tier) | H2-Alibaba only | See "Tier calibration" above | Alibaba | **NOT EVALUABLE** for AIOps/AgentRx — no CONFIRMED tier is reachable without a validation split (§5) |
| Detection lead time | **NOT EVALUABLE**, any dataset | Would require a live-deployment timeline (pattern discovered at time T, used to anticipate a failure at T+Δ) — no dataset here has that operational framing; all four are retrospective/offline record sets | — | Explicitly marked out of scope rather than silently defined away |
| Pattern stability | Optional secondary, Alibaba only | Do discovered candidates and their tiers stay materially the same if train/validation boundaries are perturbed (e.g. k-fold within train) | Alibaba train split | Proposed as an ablation-adjacent robustness check (§15), not a primary metric |

## 10. Cross-dataset comparability (Task 10)

**Evaluated independently per dataset, not pooled**, per §6/§9's structure.
No common numeric pattern-precision score is reported "across all
datasets" — the pattern types themselves differ (rate-elevation vs.
descriptive recurrence), the ground-truth quality differs (organizer-
injected labels vs. human annotation vs. no diagnosis layer at all), and
sample sizes differ by 2+ orders of magnitude. The final Phase 4.2 report
(when written, after implementation) must present results in per-dataset
sections, exactly as `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` already
does for Phase 4.1's four sources, and must not claim cross-dataset
generalization without a dedicated, separately-designed experiment for it
(Task 13's explicit prohibition).

A **shared abstraction does exist at the representation layer** —
`FailureExperience.failure.failure_signature` and
`FailureExperience.workload_context` are populated by all four sources and
could in principle support a uniform "candidate key = (workload_context
field, some other field)" query mechanism (§11's proposed `PatternQuery`
design reuses this). This is a shared *interface*, not a shared *dataset*
— each dataset still gets its own discovery run, its own thresholds, and
its own reported result.

## 11. Reuse / refactor decisions (Task 11)

| Component | Decision | Where |
|---|---|---|
| `src/failure_experience/*` (active Phase 4.1) | **Reuse directly, read-only**, as the sole data-access layer — pattern discovery queries `FailureExperienceRepository`/`retrieve()`, never re-parses raw source files itself | Active Phase 4.2 code imports `src.failure_experience`, never re-implements ingestion |
| `src/experience/`, `src/patterns/` (old, frozen) | **Do not import, do not edit.** Read for design-template understanding only (already done, §2) | N/A |
| `src/failure_memory/embedding.py` (`FailureEmbedder`) | **Candidate for one ablation only** (§15), not the primary mechanism — same "inspected, not defaulted-to" posture old Phase 4.2 took. Reused read-only if the ablation is run. | New ablation module only |
| `src/evaluation/diagnosis.py` | **Not reused** — real datasets have no field this frozen, synthetic-only rule could populate; already inapplicable outside the synthetic methodological-validation track (§4.4) | N/A |
| `data/audit/alibaba_gpu2020/splits_temporal.json`, `splits_random_stratified.json` | **Reuse directly** (§8) | New Alibaba pattern-discovery module |
| `data/audit/aiops_kpi/negative_windows_sampled.json`, `negative_window_natural_population.json` | **Reuse directly, read-only**, if a rate-based (not purely count-based) AIOps analysis is later added (optional strengthening, §12) — not required for the smallest-valid AIOps version (Pattern Type 2, count/recurrence only) | Optional AIOps rate-analysis module |
| New pattern representation (`PatternCandidate`, `PatternQuery`-equivalent) | **Build new**, in a new namespace, modeled on `src/failure_experience/eligibility.py`'s "explicit fields, explicit reasons" style and the old Phase 4.2's structural leakage-prevention *pattern* (not its code) | `src/failure_patterns/` (proposed new package name — see §14; deliberately distinct from both `src/patterns/` [old, frozen] and `src/failure_experience/` [active 4.1, a dependency not a peer]) |

## 12. Prerequisite data work assessment (Task 12)

| Candidate prerequisite | Required for smallest-valid version (§14)? | Dataset | Belongs in 4.2 itself? | Separate milestone? | Changes the research question? |
|---|---|---|---|---|---|
| Deeper AIOps telemetry join (per-minute KPI series) | **No** — Pattern Type 2 (entity×fault-type recurrence, temporal clustering) needs only window metadata, already present | AIOps | No | Yes, if ever pursued — would enable a *different*, stronger AIOps pattern type (telemetry-signature clustering) not proposed here | Yes — would upgrade AIOps from Pattern Type 2 to a Pattern-Type-1-style rate/signature claim, a scope change requiring its own hypothesis |
| Frozen train/val/test split for AIOps | **No** — §8 scopes AIOps to descriptive-only without one | AIOps | Could be done as a first step of 4.2 OR as a separate prerequisite; recommend separate, since split design (temporal vs. stratified, and by what unit — entity? day?) deserves its own brief protocol note, mirroring how Alibaba's split was built in the real-data Phase 3 track, not Phase 4.2 | Recommended separate, small milestone | No — same H2-AIOps question, just becomes formally testable instead of descriptive |
| Frozen split for AgentRx | **No** — same reasoning, descriptive-only scope | AgentRx | Same as above | Recommended separate, small milestone | No |
| Per-record Phase 3 real-data risk outputs (currently only aggregate AUROC/AUPRC exist) | **No** — H2-Alibaba's Pattern Type 1 uses raw resource-plan fields (`plan_cpu`/`gpu_type`) and the observed Failed/Terminated label directly, not a fitted risk score | Alibaba (and any future use on AIOps) | No | Yes, if ever pursued — would let a future pattern type use calibrated risk as a feature, not required here | No, but would enable an additional pattern type later |
| Workload-identity normalization | **No** — §4's audit already determined the correct identity grain per dataset (`task_name` not `job_name` for Alibaba; `domain` for AgentRx; `entity` for AIOps) | All | N/A | N/A | N/A |
| Recurrence labels | **No** — recurrence is computed directly from existing fields, not a separate label that needs producing | All | N/A | N/A | N/A |
| Additional real data | **No** — current three real datasets are sufficient for the smallest-valid version defined in §14 | — | N/A | N/A | N/A |
| Better provenance mapping | **No** — active Phase 4.1's provenance fields are already sufficient (100% traceability per its Experiment E) | — | N/A | N/A | N/A |

**Conclusion for Task 12**: no prerequisite blocks the smallest-valid
version of active Phase 4.2 (§14). Two genuinely useful prerequisites
(frozen splits for AIOps/AgentRx) are identified and recommended as small,
separate follow-on milestones that would *upgrade* those two sources from
descriptive to formally-tested, but their absence does not block starting
Phase 4.2 on Alibaba (primary) + descriptive AIOps/AgentRx + synthetic
methodological validation.

## 13. Research integrity safeguards (Task 13)

- Old Phase 4.2's `INCONCLUSIVE` verdict, `docs/PHASE4_2_FAILURE_PATTERNS.md`,
  `src/patterns/`, `configs/phase4_2_pattern_protocol.json`,
  `experiments/results/phase4_2/*` are **not modified** by this plan (this
  document only reads them, per the timestamps this task is bound by the
  same verification convention active Phase 4.1 used — file mtimes will be
  checked unchanged after this planning task, exactly as was done at the
  end of active Phase 4.1).
- No pattern type in §5 was chosen after looking at test-split outcomes —
  every dataset-specific statistic quoted in §4 was computed over the
  *full* dataset (train+val+test pooled, since no discovery/threshold
  decision was being made in this planning pass, only descriptive
  characterization) and is disclosed as such; §4's numbers must **not** be
  reused as if they were train-only discovery statistics once
  implementation begins — implementation must recompute train-only figures
  fresh, from the frozen split, not reuse this plan's pooled descriptive
  numbers as a shortcut.
- No recurrence, ground truth, or label was fabricated: AIOps's fault
  type/entity and AgentRx's failure category are dataset-provided
  annotations, used as such (`HUMAN_DATASET_ANNOTATION` /
  organizer-injected), never upgraded to a fabricated calibrated
  confidence.
- Cross-dataset generalization is not claimed anywhere in this plan (§10)
  and must not be claimed in the eventual results without a dedicated
  experiment designed for it.
- When active Phase 4.2 eventually runs, if any of its evidence bears on
  the old Phase 4.2's INCONCLUSIVE question, the final report must state
  the progression explicitly: `Old experiment (synthetic) → INCONCLUSIVE`,
  `New experiment (real data) → <whatever is found>`,
  `Combined interpretation → <stated explicitly>` — never a silent
  replacement, exactly as `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` §1
  already did for its own relationship to old Phase 4.1.

## 14. Smallest research-valid version (Task 14)

No GNNs, transformers, RL, LLMs, or graph mining — the audit found no
justification for that complexity. The recurrence/rate questions in §5 are
answerable with counting, rate comparison, and a simple pre-registered
tier rule (the same complexity class as old Phase 4.2, which is
appropriate — nothing in this audit found old Phase 4.2's *mechanism*
complexity to be the problem; its problem was evidence volume on a small
synthetic slice, which real data's larger Alibaba population directly
addresses).

**Proposed smallest-valid active Phase 4.2**, in one sentence per part:

1. `src/failure_patterns/schema.py` — new `PatternCandidate`/
   `PatternQuery`/`EvidenceTier` types, built against `FailureExperience`
   fields, structurally excluding rate/outcome from the query type (§8).
2. `src/failure_patterns/discovery_alibaba.py` — Pattern Type 1 discovery
   (`(task_name, gpu_type)` rate elevation) over Alibaba experiences
   retrieved via `src.failure_experience.retrieval`, using the frozen
   temporal split.
3. `src/failure_patterns/discovery_descriptive.py` — Pattern Type 2
   recurrence counting (+ temporal clustering for AIOps) over
   AIOps/AgentRx experiences, explicitly not tier-scored beyond OBSERVED.
4. `benchmarks/phase4_2_active_pattern_evaluate.py` — runs discovery +
   baselines A/B/C for Alibaba, descriptive reports for AIOps/AgentRx,
   methodological-validation run against synthetic.
5. `benchmarks/phase4_2_active_leakage_audit.py` — same 5-check style as
   old Phase 4.2's audit, adapted to the new types and Alibaba's temporal
   split.
6. Tests mirroring active Phase 4.1's structure: schema validation,
   discovery correctness on synthetic fixtures with known answers,
   leakage-contamination-changes-candidates test, integration test against
   real `src.failure_experience` data.
7. `docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` — the eventual results
   document (not written now — this plan only).

## 15. Ablations (Task 15)

| Ablation | Isolates | Dataset |
|---|---|---|
| Tiered (C) vs. flat-threshold-only (C′, no CONFIRMED validation-replication requirement) | Whether the validation-replication step adds value over a train-only purity/rate threshold | Alibaba |
| With vs. without temporal-split enforcement (compare temporal split result to random-stratified split result, §8) | Whether split methodology itself materially changes the finding — a sensitivity check, not a second primary result | Alibaba |
| `(task_name, gpu_type)` key vs. `FailureEmbedder`-clustered key | Whether the hand-chosen categorical key loses information a learned grouping would capture | Alibaba only (§11) |
| Recurrence threshold `N_MIN` sweep (e.g. 2/5/10/20) | Sensitivity of precision/recall to the discovery floor — mirrors Phase 3.6's cost-ratio sensitivity-sweep methodology this project already established | Alibaba |

**Not proposed**: an ablation removing "workload identity" or "temporal
information" wholesale (as the brief's generic list suggests) — for
Alibaba, workload identity (`task_name`) *is* the pattern key itself
(removing it removes the pattern definition, not a component of it); for
AIOps, temporal information is already isolated as its own metric (§9),
not blended into the primary recurrence metric, so there is nothing
additional an ablation would isolate.

## 16. Acceptance criteria (Task 16)

Distinguishing implementation correctness from hypothesis support, exactly
as old Phase 4.2's completion record did (its final status separated a
clean implementation PASS from an INCONCLUSIVE hypothesis result):

**PASS** requires ALL of:
- Implementation: schema, discovery, retrieval-integration, leakage audit
  (all checks passing, contamination test proves non-vacuous), tests all
  passing, full repo suite still green.
- Alibaba's `minimum_evaluable_n` (to be pre-registered before
  implementation, analogous to old Phase 4.2's 10 — likely higher here
  given Alibaba's much larger population, e.g. on the order of 50-100
  covered test rows, chosen from a generic small-sample convention, not
  reverse-engineered from a peek at the test split) is met.
- H2-Alibaba's pre-registered criterion is evaluated (whichever way it
  lands) — a **negative** or **null** finding, honestly reported with a
  valid, high-power experiment behind it, still qualifies as PASS on
  implementation/validity grounds; PASS is not defined as "the method
  wins."

**PASS WITH ISSUES**: implementation and evaluation are valid, but one or
more secondary items (e.g. the tier-calibration check, or the embedding
ablation) could not be meaningfully computed, OR the point estimates are
directionally unfavorable to the proposed method (mirrors old Phase 4.1's
own PASS WITH ISSUES framing) — reported plainly, not hidden.

**INCONCLUSIVE**: Alibaba's `minimum_evaluable_n` is not met despite
Alibaba's much larger population (would itself be a notable finding,
given the explicit expectation in §4.3 that power should not be the
bottleneck this time), OR the pre-registered tier thresholds produce a
degenerate candidate set (e.g. zero candidates reach any tier) making the
comparison uninformative — same posture as old Phase 4.2's honest
INCONCLUSIVE, not avoided by redefining the bar after the fact.

**FAIL**: leakage audit finds a real violation not caught before reporting
results, OR the implementation cannot process real `FailureExperience`
data end-to-end, OR a research-integrity violation (test-set tuning,
fabricated ground truth) is found.

AIOps/AgentRx's descriptive analyses do not carry a PASS/FAIL verdict of
their own (no hypothesis is being tested there per §6/§8) — they are
reported as findings, with a companion "NOT CURRENTLY EVALUABLE as a
scored hypothesis; would require [frozen split]" note, per §12.

## 17. Implementation sequence (Task 17, item 22)

1. Pre-register `configs/phase4_2_active_pattern_protocol.json` (thresholds,
   splits, minimum_evaluable_n, acceptance criteria) — frozen BEFORE any
   discovery code runs against real train data, exactly matching this
   project's established protocol-freezing discipline.
2. Build `src/failure_patterns/schema.py` (types) + unit tests against
   synthetic fixtures with known, hand-computed answers.
3. Build Alibaba discovery module (§14 item 2) against train split only;
   verify against the frozen protocol's thresholds.
4. Build the leakage audit; verify the contamination test is non-vacuous
   (old Phase 4.2's exact discipline).
5. Run validation-split tier calibration (CONFIRMED replication check).
6. One-time frozen test-split evaluation (Alibaba) — after this point, per
   `docs/PHASE4_PLAN.md` §3's "once evaluated, retired" rule, this
   particular Alibaba pattern-protocol version is not re-fit-and-re-tested.
7. Build AIOps/AgentRx descriptive modules (no train/test boundary to
   respect, but still must not compute or report anything framed as a
   scored precision/recall).
8. Run the synthetic methodological-validation pass.
9. Run ablations (§15).
10. Write `docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` with full results,
    the old→new progression statement (§13), and a formal status per §16.
11. Update `docs/PHASE4_PLAN.md` with the same kind of additive amendment
    section active Phase 4.1 added (§11 there) — never rewriting existing
    content.

## 18. Expected outputs

`src/failure_patterns/` (new package), `configs/phase4_2_active_pattern_
protocol.json`, `benchmarks/phase4_2_active_pattern_evaluate.py`,
`benchmarks/phase4_2_active_leakage_audit.py`,
`experiments/results/phase4_2_active/`, new unit + integration tests,
`docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md`, an additive amendment to
`docs/PHASE4_PLAN.md`.

## 19. Limitations (of this plan, stated up front)

- Alibaba's much larger sample size is expected to fix old Phase 4.2's
  specific `n_covered < 10` problem, but this is a **prediction**, not a
  guaranteed outcome — the frozen `minimum_evaluable_n` bar for Alibaba
  must still be checked, honestly, against whatever the real discovery run
  produces.
- AIOps/AgentRx remain descriptive-only under this plan; if that is judged
  insufficient for what "Phase 4.2" should deliver, the frozen-split
  prerequisite work (§12) should be authorized as a preceding milestone —
  this plan does not assume that authorization.
- The rate-elevation reformulation (§6) is a genuine, disclosed departure
  from the old symptom→cause framing — if a future reviewer judges this
  departure too large to still be called "Phase 4.2," that is a valid
  objection this plan surfaces rather than presupposes away; the
  alternative (forcing a `diagnosed_cause`-shaped question onto data that
  has no diagnosis layer) was judged worse (§4.3).
- No cross-dataset pattern claim is planned (§10) — if unified evidence
  across datasets is a project goal, it is out of scope for this plan and
  would need its own, separately-justified design.

## 20. Reproducibility requirements

Every discovery/evaluation script must take a fixed seed where randomness
is used (none is currently anticipated for Pattern Type 1's rate
comparison, which is deterministic; a seed will be needed only if the
`FailureEmbedder` ablation, §15, is run). All read paths are the same
frozen files already used by active Phase 4.1 and the real-data Phase 3
track — no new raw data ingestion is proposed. Results must be
regenerable by re-running the benchmark scripts against unchanged frozen
inputs, per the project's established convention.

## 21. Research-integrity safeguards — summary

See §13 (full detail). In short: old Phase 4.2 stays frozen; new evidence
is new evidence; no test-set tuning; no fabricated ground truth; no
cross-dataset generalization claims without a dedicated experiment; every
descriptive-only result (AIOps, AgentRx) is labeled as such, never
presented as a scored hypothesis test it structurally cannot be.

---

## FINAL OUTPUT (per the brief's required summary)

1. **Old Phase 4.2 status**: frozen, `INCONCLUSIVE` (evidence-volume
   insufficient, 7 < 10 covered test rows on synthetic CRITICAL-tier data).
   `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/`, its configs and
   results remain untouched by this plan.
2. **What active Phase 4.1 provides**: a canonical `FailureExperience`
   store across 4 sources (961 experiences), with the field-population
   profile in §3 — critically, no real dataset has a diagnosis-confidence
   or recovery/validation signal, and only Alibaba has a frozen split.
3. **Dataset-by-dataset suitability**: Alibaba — strong (large n, frozen
   split, genuine rate signal). AIOps — moderate/descriptive (real
   temporal structure, no split, small n). AgentRx — weak/descriptive (no
   telemetry, no timestamp, no split, small n, but genuine behavioral-
   failure-mode recurrence signal exists). Synthetic — methodological
   validation role only, not a hypothesis-bearing source.
4. **Does original H2 remain valid?** No, not unmodified — reformulated
   into per-dataset hypotheses (§6, decision E).
5. **Proposed research question**: does context (workload/task/entity/
   domain) reliably predict a specific failure mode or elevated failure
   rate, above chance, in a way that generalizes from discovery data to
   held-out data where a split exists, and remains honestly descriptive
   where it doesn't?
6. **Hypotheses**: H2-Alibaba (rate elevation, formally testable),
   H2-AIOps and H2-AgentRx (recurring association + AIOps temporal
   clustering, descriptive/exploratory pending a split).
7. **Pattern task definition**: two types, §5 — context-conditioned
   failure-rate elevation (Alibaba) and recurring failure-mode association
   (AIOps/AgentRx).
8. **Baselines**: no-pattern-learning, naive-frequency, proposed
   tiered-rate method, optional embedding-based grouping ablation (§7).
9. **Metrics**: rate-elevation precision/recall/false-pattern-rate/tier
   calibration (Alibaba); recurrence rate + temporal-clustering statistic
   (AIOps); recurrence rate only (AgentRx); several old-Phase-4.2-style
   metrics explicitly marked NOT EVALUABLE (detection lead time, all
   datasets; tier calibration, AIOps/AgentRx) (§9).
10. **Data-split/leakage protocol**: Alibaba's frozen temporal split
    (primary) + random-stratified (sensitivity check); AIOps/AgentRx
    treated as evaluation-only/descriptive, no train-test claim made
    (§8).
11. **Required prerequisite work**: none blocking; two optional,
    recommended follow-on milestones (frozen splits for AIOps and
    AgentRx) that would upgrade those sources from descriptive to
    formally testable (§12).
12. **Reuse/refactor decisions**: reuse `src/failure_experience/` directly
    as the data layer; reuse Alibaba's frozen splits and AIOps's frozen
    negative-window population directly; do not import old `src/patterns/`
    or `src/experience/`; build a new `src/failure_patterns/` package
    (§11).
13. **Proposed experiments**: Alibaba discovery/validation/test evaluation
    (primary), AIOps descriptive recurrence + temporal clustering,
    AgentRx descriptive recurrence, synthetic methodological validation
    (§14, §17).
14. **Proposed ablations**: tiered vs. flat threshold, temporal vs.
    random-stratified split, categorical key vs. embedding-clustered key,
    recurrence-threshold sweep (§15).
15. **Acceptance criteria**: PASS/PASS WITH ISSUES/INCONCLUSIVE/FAIL
    defined in §16, explicitly allowing a valid negative/null result to
    still be a scientifically successful PASS.
16. **Risks and limitations**: §19 — reformulation-validity risk, AIOps/
    AgentRx descriptive-only scope, no guarantee Alibaba's larger n
    resolves the power problem, no cross-dataset claim planned.
17. **Exact implementation plan**: §17 (11-step sequence), §14 (7-part
    smallest-valid architecture), §18 (expected file outputs).
18. **Recommendation**:

# READY FOR IMPLEMENTATION (scoped)

Ready to implement the smallest research-valid version defined in §14:
**Alibaba as the primary, rigorously-evaluated H2-Alibaba hypothesis**,
**AIOps and AgentRx as descriptive-only exploratory analyses** (not scored
hypothesis tests), and **synthetic data as a methodological-validation
track only**. The two optional prerequisite milestones (frozen splits for
AIOps/AgentRx, §12) are **not required to start** but are recommended as
follow-on work if formally-tested AIOps/AgentRx hypotheses are later
wanted — implementation should not silently attempt those without first
building and freezing the missing splits.

**Awaiting explicit approval before any implementation begins**, per the
task's instruction.
