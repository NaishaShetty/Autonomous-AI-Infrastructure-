# Phase 5.1 — Publication Boundary

## 1. Classification scheme

| Category | Meaning |
|---|---|
| PUBLIC_DATASET_CONTENT | Fit for inclusion in a released, benchmark-ready dataset file |
| PUBLIC_METADATA | Not row-level content, but safe/useful to publish alongside (protocol docs, schema, split definitions, aggregate metrics) |
| RESEARCH_ONLY_INTERNAL_ARTIFACT | Useful for this project's own reproducibility, not intended for external release (e.g. full trained-model pickle artifacts, SQLite memory stores with local file paths) |
| ENGINEERING_ONLY_ARTIFACT | pytest logs, CI-style output, defect-tracking notes — excluded from any dataset release, public or internal-research |
| EXCLUDED | Must never be published under any circumstance in this dataset's scope |

## 2. Classification by evidence area

- **Controlled-runtime episode records** (observations, decisions,
  diagnoses, recovery actions, validations, memory interactions), Gen-3
  only, with `run_id`/`workload_id`/`memory_id` retained as opaque
  identifiers (not tied to any real external identity — this project's
  own runtime is local and project-owned, `docs/MASTER_RECORD_CONTENT.md`
  §10) → **PUBLIC_DATASET_CONTENT**.
- **Agent-task records** (arithmetic self-consistency, sentiment, QA),
  including the deterministic templated text corpora → **PUBLIC_DATASET_CONTENT**,
  with the templated/synthetic status (`evidence_class=7` for the text)
  disclosed in the record's own metadata, never presented as a standard
  external benchmark.
- **Schema, provenance contract, split policy, leakage policy, benchmark
  view designs** (this run's own deliverables) → **PUBLIC_METADATA**.
- **Aggregate metrics already published in frozen reports** (AUROC,
  false-alarm rate, recovery-rate numbers already stated in
  `docs/MASTER_RECORD_CONTENT.md`, `FINAL_PHASE4_CLOSURE_REPORT.md`) →
  **PUBLIC_METADATA** (they are already disclosed narratively; a
  structured re-statement is not a new disclosure).
- **Trained model artifacts** (`TrainedRiskPredictor`,
  `PredictionScopeRouter` pickled/versioned artifacts under
  `experiments/results/phase4_5_autonomy_pipeline_at_scale/prediction_artifact/`
  and `.../phase4_5b_recognition_and_agent_evaluation/prediction_scope_router_artifact/`)
  → **RESEARCH_ONLY_INTERNAL_ARTIFACT** by default. These are large,
  environment-specific, and not validated as usable detectors for most
  families (per the master record's own honest verdicts) — publishing them
  as if they were production-ready detectors would misrepresent the
  project's own findings. A future phase could choose to publish them
  alongside an explicit "NOT VALIDATED, see false-alarm-rate" disclosure,
  but that decision is out of scope for this specification.
- **Full SQLite `FailureMemoryStore` database files** (if any exist as
  physical files with local `path=`) → **RESEARCH_ONLY_INTERNAL_ARTIFACT**
  (may contain local file paths / host identity metadata in `provenance`;
  the *content* — `MemoryRecord` rows — is fine as PUBLIC_DATASET_CONTENT
  once re-exported through the canonical schema with host-identifying
  provenance fields stripped or coarsened, e.g. `platform.node()` and
  `host_identity` from `controlled_runtime.py`'s environment registration
  must be excluded or hashed, not published raw).
- **`pytest` suite outputs and CI-style logs** →
  **ENGINEERING_ONLY_ARTIFACT**, excluded from any dataset release.
- **Generation 1/2 (V1) evidence** → **EXCLUDED** from this dataset's
  scope entirely (different data-generating process; see
  `PHASE5_1_DATASET_SPECIFICATION.md` §6). Not "internal" — genuinely out
  of scope, may be published separately under its own already-existing
  frozen release boundary (`docs/archive/V1_RELEASE_AUDIT.md`'s own claim
  boundary governs that, not this specification).
- **`detectable_only_scope` AUC=0.857 mixing-artifact evidence** (class 8)
  → **RESEARCH_ONLY_INTERNAL_ARTIFACT**, retained with its disclosed
  caveat for methodological transparency; excluded from
  PUBLIC_DATASET_CONTENT as a label source, eligible for
  PUBLIC_METADATA only as a documented negative-finding narrative (already
  is one, in the master record).
- **Pre-RSS-telemetry-fix Windows OOM evidence** (class 8) →
  **RESEARCH_ONLY_INTERNAL_ARTIFACT**, retained as defect evidence only,
  never published as OOM-predictive PUBLIC_DATASET_CONTENT.
- **Real external datasets' raw content** (Alibaba GPU2020, AgentRx, AIOps
  2020) → **EXCLUDED from this dataset** (belongs to the Gen-1/2 tracks,
  out of scope) and in any case governed by their own publisher's license
  terms, not by this project's own publication decision — `docs/archive/DATA_SETUP.md`'s
  existing gitignore/marker-file mechanism already reflects this.
- **Host/platform metadata** (`platform.node()`, `platform.platform()`,
  `os.cpu_count()`, `host_identity`) embedded in `controlled_runtime.py`'s
  environment registration → **RESEARCH_ONLY_INTERNAL_ARTIFACT** by
  default; `host_identity` specifically should never appear in
  PUBLIC_DATASET_CONTENT (it is a real hostname, not a research-relevant
  identifier) — a future generation step must replace it with a
  coarsened/hashed `environment_id`-scoped value before any public release.

## 3. Don't over-publish, don't under-disclose

Per the design principle "don't publish huge raw internal artifacts merely
because they exist; don't silently discard scientifically important
evidence": the boundary above deliberately keeps every negative,
inconclusive, or non-validated result (§4 of the main specification) in
PUBLIC_DATASET_CONTENT or PUBLIC_METADATA — the exclusions in this
document are about artifact *type* (raw pickled model binaries, host
identity, CI logs, a different generation's data) and about *labeling
integrity* (never let a discredited mixing artifact become a public
label), never about hiding an unfavorable finding.

## 4. Versioned boundary

This boundary is versioned alongside the schema
(`phase5.1-schema-v1.0.0`). A future schema version may move an artifact
across categories (e.g. promoting a trained-model artifact to
PUBLIC_DATASET_CONTENT once a validated operating point exists for it),
but must record the change explicitly rather than silently reclassifying.
