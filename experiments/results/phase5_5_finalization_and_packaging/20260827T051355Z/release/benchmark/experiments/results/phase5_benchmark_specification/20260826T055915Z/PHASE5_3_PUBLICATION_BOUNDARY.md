# Phase 5.3 — Benchmark Publication Boundary

Status: SPECIFICATION ONLY. No Hugging Face upload, and no upload of any
kind, occurs in this phase. This document defines the FUTURE release
structure a subsequent, separately-gated implementation phase would follow,
extending `PHASE5_1_PUBLICATION_BOUNDARY.md`'s categories to benchmark-
specific artifacts.

## 1. Release structure (future, not executed here)

| Category | Meaning |
|---|---|
| PUBLIC_DATASET | The Phase 5.2 canonical records themselves, re-published unchanged |
| PUBLIC_BENCHMARK_CODE | Task-instance derivation code, scoring code, metric implementations (not yet written — this phase is specification only) |
| PUBLIC_BENCHMARK_CARD | A model/dataset-card-style document: tracks, tasks, metrics, known limitations, honest current scores per track |
| PUBLIC_DOCUMENTATION | This specification and its companions (schema, split policy, leakage policy, metric/baseline/ablation catalogs) |
| RESEARCH_ONLY_ARTIFACTS | Full per-instance prediction dumps, trained baseline model weights, intermediate scoring logs |
| EXCLUDED_ARTIFACTS | Anything already `EXCLUDED` under `PHASE5_1_PUBLICATION_BOUNDARY.md` (Gen-1/2 evidence, raw external dataset content, host identity) |

## 2. Classification of specific future artifacts

- **Raw dataset records** (`all_records.jsonl` and its two track files) →
  already classified `PUBLIC_DATASET_CONTENT` by
  `PHASE5_1_PUBLICATION_BOUNDARY.md`; this specification does not
  reclassify them. → **PUBLIC_DATASET**.
- **Derived benchmark task-instance files** (the projection this
  specification defines — `input`/`hidden`/`label` per
  `PHASE5_3_BENCHMARK_SCHEMA.json`'s top-level object) → **PUBLIC_DATASET**,
  once actually generated (not yet generated — this phase is
  specification only), because they contain no information beyond a
  re-arrangement of already-public dataset content, with the `hidden`
  block simply un-populated until scoring time.
- **Benchmark scoring/derivation code** (not yet written) → intended for
  **PUBLIC_BENCHMARK_CODE** once implemented, so external researchers can
  independently reproduce every metric in `PHASE5_3_METRIC_CATALOG.json`.
- **Labels/ground truth** (e.g. `agent_output.is_correct`,
  `failure.failure_detected`, `validation.validation_status`) → already
  `PUBLIC_DATASET_CONTENT` at the dataset level; remain so at the
  benchmark level, EXCEPT any label whose disclosure would let a test-set
  submission trivially cheat (none identified currently, since ground
  truth for `test`-split instances would need to be withheld from a
  submission at scoring time even though it is "public" in the dataset
  sense — this is a **submission-protocol** distinction, not a
  publication-boundary one: the data can be public while a live
  leaderboard still withholds `test` labels operationally, exactly as
  standard ML benchmark practice does).
- **Evaluation outputs / benchmark results** (aggregate metrics, per-track
  scorecards) → **PUBLIC_BENCHMARK_CARD** once real evaluation is run in a
  future phase; must include every NOT_VALIDATED/NOT_EVALUABLE/LIMITED
  status alongside any positive result, per the "don't publish only
  flattering numbers" instruction running through this whole specification.
- **Model predictions from a system under test** (if/when third-party
  submissions are scored) → **RESEARCH_ONLY_ARTIFACTS** by default (may
  contain submitter-specific implementation detail not intended for public
  re-distribution without the submitter's consent); aggregate scores
  derived from them are what becomes public, not the raw prediction dumps
  themselves, unless a submitter explicitly opts in to publishing their
  own raw outputs.
- **Trained baseline models** (e.g. BASE-SIMPLE-STATISTICAL-PREDICTOR, once
  actually fit in a future implementation phase) → inherits
  `PHASE5_1_PUBLICATION_BOUNDARY.md`'s treatment of trained-model
  artifacts: **RESEARCH_ONLY_INTERNAL_ARTIFACT** by default, given that
  several families (`cpu`, pooled `oom`, `flaky`) are NOT_VALIDATED and
  publishing a trained detector for them without the disqualifying
  false-alarm-rate context attached would misrepresent the project's own
  findings — any future public release of these MUST carry the
  NOT_VALIDATED/false-alarm-rate disclosure inline, not as a footnote.

## 3. Don't over-publish, don't under-disclose (restated for the benchmark layer)

- Nothing in this benchmark specification's design changes any
  classification made in `PHASE5_1_PUBLICATION_BOUNDARY.md` for the
  underlying dataset — it only adds classifications for the NEW artifact
  types a benchmark layer introduces (task-instance files, scoring code,
  benchmark cards, submission outputs).
- Every `NOT_EVALUABLE`/`UNSUPPORTED_CONTRACT_ONLY` task in
  `PHASE5_3_TASK_CATALOG.json` is intended to remain fully visible in any
  future `PUBLIC_BENCHMARK_CARD` — the point of marking a track
  not-currently-evaluable is to disclose the gap publicly, not to hide the
  track from the benchmark's public description.

## 4. This phase's actual boundary

**No file was uploaded anywhere in this phase.** All artifacts described
above as "future" are unimplemented; every deliverable actually produced
by this phase lives under
`experiments/results/phase5_benchmark_specification/20260826T055915Z/`
and is itself `PUBLIC_METADATA` per the same rule Phase 5.1's own
companion documents used for themselves.
