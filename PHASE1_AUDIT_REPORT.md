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
