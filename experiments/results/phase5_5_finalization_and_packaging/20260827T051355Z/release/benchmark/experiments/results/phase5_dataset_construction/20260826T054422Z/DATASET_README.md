# Phase 5.2 Canonical Dataset — README

`dataset_version = phase5.2-dataset-v1.0.0`, built against
`schema_version = phase5.1-schema-v1.0.0` (frozen at
`experiments/results/phase5_dataset_specification/20260826T053011Z/PHASE5_1_SCHEMA.json`).

## What this is

3,106 canonical, schema-validated records extracted from the frozen,
Generation-3 (Gen-3) Phase 4 evidence base — real local subprocess
executions (`controlled_runtime` track, 46 records) and real HuggingFace
model inference on three distinct agent task families (`agent_task` track,
3,060 records: 2,000 arithmetic self-consistency, 660 sentiment
softmax-margin, 400 extractive QA span-logit). No Phase 4 code was executed
to produce this dataset — every record is a deterministic re-expression of
already-generated, already-frozen JSON/JSONL evidence files.

## Directory layout

```
dataset/
  controlled_runtime/records.jsonl   (46 records)
  agent_task/records.jsonl           (3,060 records)
  all_records.jsonl                  (3,106 records, sorted by record_id)
dataset_metadata.json                (version, source sha256 hashes, schema version)
dataset_statistics.json              (full distributional breakdown)
lineage.json                         (source file -> record_id[] map)
split_assignment_manifest.json       (record_id -> split_assignment)
SHA256_MANIFEST.json                 (checksum of every file in this directory)
```

Plus one report + one machine-readable audit per validation dimension (schema,
splits, leakage, provenance, record-id/duplicates, publication boundary,
regeneration, negative-result preservation) — see
`PHASE5_2_DATASET_AUDIT.md` for the full checklist and where each result lives.

## How to read one record

Each line of `all_records.jsonl` is one canonical episode/task-instance
record matching `PHASE5_1_SCHEMA.json`'s top-level object. Key fields:

- `identity.record_id` — deterministic SHA-256-derived ID (see
  `src/phase5/record_id.py`; never filesystem-order- or hash()-dependent).
- `identity.track` — `"controlled_runtime"` or `"agent_task"`, never merged.
- `provenance` — traces every record to one specific frozen source file and
  its exact SHA-256 (see `dataset_metadata.json`).
- `failure` / `diagnosis` / `recovery` / `validation` — kept as **separate**
  fields with distinct `label_type`s so that ground truth
  (`OBJECTIVE_GROUND_TRUTH`, `OBSERVED_OUTCOME_VALIDATED`), model output
  (`MODEL_PREDICTION`, `MODEL_DIAGNOSIS`), and unvalidated executor
  self-report (`EXECUTOR_SELF_REPORT_UNVALIDATED`) are never collapsed into
  one value — see `PROVENANCE_VALIDATION_REPORT.md`.
- `split_assignment` — `train` / `calibration_validation` / `test`, grouped
  by `workload_id` (never split across a shared workload — see
  `SPLIT_VALIDATION_REPORT.md`).
- `outcome_class` — an additive, non-schema-required field
  (`RECOVERED`/`NOT_RECOVERED`/`ABSTAINED`/`NO_FAILURE`/`UNKNOWN` for
  controlled_runtime; `ANSWERED_CORRECT`/`ANSWERED_INCORRECT` for
  agent_task) added to fulfil the Phase 5.1 narrative design principle
  ("every episode record carries an explicit outcome_class") which the
  frozen `PHASE5_1_SCHEMA.json` itself does not define as a formal property
  — see `PHASE5_2_DATASET_AUDIT.md`'s schema-deficiency note.

## What is honestly NOT in this release

- No per-checkpoint `observations[]` telemetry rows — the two per-episode
  raw sources used (`phase4_4_autonomy_pipeline/results.json`,
  `phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl`) do
  not retain checkpoint-level `process_rss_bytes`/`process_cpu_percent`
  rows, only episode-level summaries.
- No real per-episode Phase-4.9 `environment_id`
  (`phase4.9-env-baseline-cpu` / `-memory-constrained` /
  `-dependency-network-constrained`) — every record's `environment_id` is
  `UNSPECIFIED_PRE_4_9` because no per-episode source available to this
  construction carries that field; the Phase-4.9 evidence that does exist
  is aggregate-only. See `SPLIT_VALIDATION_REPORT.md`.
- No `MemoryRecord`/`memory_id` write timestamps — `memory_used` is
  retained as a boolean flag only.
- No ABSTAIN-decision episodes — none exist in the specific raw files
  ingested (see `NEGATIVE_RESULT_PRESERVATION_REPORT.md`).
- Trained model artifacts (`prediction_artifact/`,
  `prediction_scope_router_artifact/`) and SQLite memory-store files were
  never read as content sources (per `PHASE5_1_PUBLICATION_BOUNDARY.md`,
  they are `RESEARCH_ONLY_INTERNAL_ARTIFACT`, out of scope for this
  release).

## Reproducing this dataset

```
python scripts/phase5_dataset/generate.py <output_dir>
python scripts/phase5_dataset/validate_schema.py <output_dir>
python scripts/phase5_dataset/validate_splits.py <output_dir>
python scripts/phase5_dataset/validate_leakage.py <output_dir>
python scripts/phase5_dataset/validate_provenance.py <output_dir>
python scripts/phase5_dataset/validate_record_ids.py <output_dir>
python scripts/phase5_dataset/validate_publication_boundary.py <output_dir>
python scripts/generate_sha256_manifest.py <output_dir>
```

Running `generate.py` twice from the same frozen sources produces
byte-identical output (`regeneration_audit.json`,
`overall_byte_identical: true`).
