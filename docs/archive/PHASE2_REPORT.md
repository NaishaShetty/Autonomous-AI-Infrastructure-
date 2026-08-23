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
