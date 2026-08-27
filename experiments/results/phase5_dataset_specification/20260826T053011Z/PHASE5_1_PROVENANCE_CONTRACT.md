# Phase 5.1 — Provenance Contract

This contract states, once, the rules that every field in
`PHASE5_1_SCHEMA.json` must satisfy, and the mechanism by which any consumer
can verify a given record's provenance without trusting a restatement.

## 1. Provenance object (attached to every record)

Every record at every canonical level (§2 of the main specification) carries
a `provenance` object with these sub-fields, modeled directly on
`src/data_foundation/foundation.py::Provenance` (already load-bearing in the
live code, reused rather than redesigned):

| Field | Meaning | Required? |
|---|---|---|
| `source` | which `src/phase4/*.py` module or `experiments/results/...` path produced this value | yes |
| `source_version` | the module's own version constant (e.g. `RUNTIME_VERSION`, `MEMORY_CONTRACT_VERSION`, `ENVIRONMENTS_VERSION`) at generation time | yes |
| `source_record_id` | the upstream identity (event_id / run_id / memory_id / prediction_id, as applicable) this value was read from | yes |
| `extraction_method` | how the value was obtained (`direct_telemetry_read`, `sql_query`, `deterministic_derivation`, `model_inference`, `human_report_transcription`) | yes |
| `transformation` | any deterministic transform applied (e.g. `feature_vector_extraction`, `rolling_checkpoint_slice`) | if applicable, else `"identity"` |
| `transformation_version` | version of the transform code | if `transformation != "identity"` |
| `timestamp_quality` | one of `EXACT`, `SYNCHRONIZED`, `APPROXIMATE`, `INFERRED`, `UNKNOWN` (from `TimestampQuality`) | yes |
| `checksum` | SHA-256 of the immediate upstream artifact, where the artifact is a file (e.g. a `SHA256_MANIFEST.json` entry) | where applicable |
| `evidence_class` | 1–8, per `PHASE5_1_SOURCE_INVENTORY.json`'s classification scheme | yes |
| `frozen_run_dir` | the specific timestamped `experiments/results/<phase>/<UTC-timestamp>/` this value traces to, if any | where applicable |

## 2. No unexplained derived values (rule)

A field is permitted in the schema only if one of the following holds:

- **(a) Directly observed**: it is copied, without transformation, from a
  `CanonicalEvent.payload`, a `MemoryRecord` column, or a dataclass field
  already present in `src/phase4/*`. `extraction_method = "direct_telemetry_read"`
  or `"sql_query"`.
- **(b) Deterministically derived**: it is computed by a named, versioned
  function from (a)-type fields, with the function's identity recorded in
  `transformation`/`transformation_version`. Example: `rss_ratio_env_normalized`
  derived from `process_rss_bytes` and the run's own configured
  `oom_limit_mb_*_variant` (Phase 4.9/post-P5 Step 4 feature).
- **(c) Model output**: it is the output of a named, versioned model
  (`TrainedRiskPredictor`, `PredictionScopeRouter`, `DiagnosisEngine`,
  `AdaptiveRecoveryPlanner`) with the model's own artifact version recorded.
  Model outputs are never permitted to silently become (a)-type fields
  elsewhere in the schema (§3).
- **(d) Explicitly unavailable**: the field's `availability` is
  `NOT_CURRENTLY_AVAILABLE`, `UNAVAILABLE` (matching `Availability.UNAVAILABLE`),
  or `NOT_APPLICABLE`, with a one-line reason.

Nothing else is permitted. A field with no traceable rule under (a)-(d) does
not belong in the schema and must not be added by a future generation script
without amending this contract first.

## 3. Ground truth vs. model output vs. self-report (the load-bearing distinction)

This project's own frozen evidence already draws this line in code, not
just prose — the provenance contract makes it a schema-level constraint:

| Category | Example | Who determines it | Can it become ground truth? |
|---|---|---|---|
| Objective ground truth | `SelfConsistencyResult.is_correct` (arithmetic), QA gold-answer match, sentiment template label | Constructed by the generator, checked by real computation, never read by the agent | Yes — it is ground truth by construction |
| Observed outcome | `ValidationOutcome.status` from `SignalRecoveryValidator` (independently re-derives from raw events) | `MonitoringEngine`'s independent re-derivation | Yes, for recovery outcome only, and only via the validator, never via the executor |
| Executor self-report | the recovery executor's own claimed result | `RecoveryExecutor` | **No.** Retained as a distinct field (`executor_self_report`) for audit/discrepancy analysis, never copied into `validated_outcome` |
| Derived label | e.g. `label = 1 if failure_events else 0` in `CorpusRow` generation | Deterministic derivation from raw events | Yes, if the derivation is itself deterministic and versioned |
| Model prediction | `Prediction.score`, `TrainedRiskPredictor` output | `src/phase4/prediction.py` / `prediction_training.py` | **No.** Always tagged `label_type = "MODEL_PREDICTION"` |
| Model diagnosis | `Diagnosis.suspected_cause` | `DiagnosisEngine` | **No.** Always tagged `label_type = "MODEL_DIAGNOSIS"`, even when `confidence = HIGH` |
| Human/engineering annotation | none currently exists in Phase 4 evidence | N/A | N/A — schema reserves the enum value but no current field uses it |
| UNKNOWN | `Diagnosis.suspected_cause = null`, `AutonomyState.UNKNOWN` | System, when evidence is genuinely insufficient | Retained as UNKNOWN, never coerced to a guessed value |
| UNAVAILABLE | e.g. GPU telemetry when no device exists | System | Retained as UNAVAILABLE, never coerced to 0/None-as-negative |
| NOT_APPLICABLE | e.g. `retry_success_rate` for a non-arithmetic task family | Schema-level, by task-family/failure-class eligibility | Retained as NOT_APPLICABLE, distinct from UNAVAILABLE |

**Hard rule**: a record with `label_type = "MODEL_PREDICTION"` or
`"MODEL_DIAGNOSIS"` must never appear in the `ground_truth` field of any
other record, in this dataset or any future one built from this
specification. This is the schema-level enforcement of the master record's
own repeated statement (§20, §29, memory contract docstring) that
diagnosis and self-reports are not ground truth.

## 4. Reproducibility chain

Each record's provenance chain must be walkable, without re-execution, back
to one of:

1. A file under a frozen, checksum-manifested `experiments/results/<phase>/<timestamp>/`
   directory (verify via that directory's own `SHA256_MANIFEST.json`).
2. A `src/phase4/*.py` module version constant, cross-referenced against the
   git commit this specification was written against
   (`8086e7185d0917e8431749db0f0c47ba18088eb5`, per the task's stated HEAD).
3. An external dataset checksum (Alibaba GPU2020 / AgentRx / AIOps 2020),
   per `docs/archive/DATA_SETUP.md` — used only by the explicitly
   out-of-scope Gen 1/2 tracks, never by the Gen-3 dataset this
   specification targets.

## 5. What this contract does NOT do

It does not re-verify, recompute, or re-derive any number from the frozen
evidence. It states the rule a future generation script must follow when it
reads that evidence. No Phase 4 file was written to in producing this
contract.
