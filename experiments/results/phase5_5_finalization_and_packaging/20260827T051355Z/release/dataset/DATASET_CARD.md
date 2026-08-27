# Dataset Card — Phase 5.2 Canonical Dataset

dataset_version: `phase5.2-dataset-v1.0.0` | schema_version:
`phase5.1-schema-v1.0.0`

## Summary

3,106 records: 3,060 `agent_task` episodes (2,000 arithmetic
self-consistency, 660 sentiment, 400 extractive QA) and 46
`controlled_runtime` failure/recovery episodes, generated entirely by
this project's own Phase 4 agent-task and controlled-runtime evaluation
code — no third-party dataset content.

- Splits (sample-level axis): train=2,142, calibration_validation=482,
  test=482. 0 record_id or workload_id crosses a split boundary.
- Environments: 1 (`UNSPECIFIED_PRE_4_9` — this dataset predates Phase
  4.9's per-episode environment identity; see Limitations).
- Workloads: 3,104 distinct `workload_id` values across 3,106 records —
  1 group of 3 records (`workload-recurring`) shares a workload_id
  (a genuine, small, Phase-4.4-origin repeated-incident sequence,
  entirely within one split; far below any scale needed for a
  memory-adaptation claim).

## What it is for

Evaluating narrow, falsifiable capability claims about an autonomous
agent system: uncertainty calibration, abstention-policy simulation,
diagnosis (failure-class matching only), recovery outcome (from
independent validation, never self-report), and disclosed limitations for
failure prediction, memory adaptation, and environment generalization.
Paired with the benchmark release package for exact task definitions.

## What it is NOT for

- Not a general-purpose LLM benchmark — the 3 agent-task families
  (arithmetic self-consistency, sentiment, extractive QA) use
  deterministic templated text corpora, disclosed via `evidence_class=7`
  on the relevant records, never presented as a standard external
  benchmark like GLUE/SQuAD.
- Not a multi-environment generalization dataset — only 1 environment is
  represented.
- Not a repeated-incident / memory-adaptation dataset at any usable scale
  — only 1 small group (3 records) of this kind exists.
- Not evidence of causal failure diagnosis — diagnosis records carry a
  `suspected_cause` field but no independent causal ground truth exists in
  this dataset; only failure-class-label matching is a defensible claim.

## Schema

See `docs/PHASE5_1_SCHEMA.json`. Every record carries `identity`
(record/episode/run/workload/environment ids, track, seed),
`agent_output` (family-specific output + `is_correct`),
`failure`/`diagnosis`/`recovery`/`validation`/`safety` (controlled_runtime
only), `labels`, `split_assignment`, `temporal`, `provenance`.

## Splits and leakage

See `docs/PHASE5_1_SPLIT_POLICY.md` and `docs/PHASE5_1_LEAKAGE_POLICY.md`.
Grouping key is `workload_id`; a record's split assignment is fixed at
construction time and never re-derived by any consuming benchmark.

## Provenance

See `docs/PHASE5_1_PROVENANCE_CONTRACT.md`. Every record traces to a named
Phase 4 raw-evidence source (`identity.source_artifact_version`); no
aggregate statistic was ever converted into a fabricated per-record value.

## Publication boundary

See `docs/PHASE5_1_PUBLICATION_BOUNDARY.md`. This release excludes: V1/
Gen-2 evidence, trained-model pickled artifacts, SQLite memory-store
files, host/platform identity metadata (confirmed absent from all 3,106
records by direct scan), and any engineering-only test/CI artifact.

## Negative and limited results preserved

This dataset does not hide unfavorable findings: `by_recovery_outcome`
shows 0 `RECOVERED` outcomes among the 35 failure episodes with a
validation record; `by_uncertainty_mechanism` retains the sentiment
family's near-chance discrimination un-averaged with the stronger
arithmetic/QA families; `environments: 1` and `workloads: 3104` are
reported as literal counts, not narratively softened.

## Known limitations

1. No per-checkpoint observation telemetry — `observations` is empty for
   every record; only end-of-episode summaries exist.
2. No real per-episode `environment_id` — all records carry
   `UNSPECIFIED_PRE_4_9`.
3. No memory-write timestamps.
4. No realized ABSTAIN/RETRY-decision episodes exist in the ingested raw
   sources (`by_decision_type` has no such key).
5. Aggregate-only source evidence for several Phase 4 failure-prediction
   verdicts (no per-episode join key for `resource_unavailable`,
   `PROCESS_OOM` combined-feature evaluation, etc.) — those verdicts
   remain valid as project-level findings but are not re-derivable as
   record-level scores from this dataset.

## License / provenance statement

Generated entirely by this project's own code; no external dataset
content is included. Released under the parent project's license terms.
