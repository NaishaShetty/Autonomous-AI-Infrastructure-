# Phase 5.3 — Synthesis

## What was asked

Design (not implement) the complete benchmark specification for the
Autonomous AI Infrastructure project, on top of the frozen Phase 5.1
dataset specification and the frozen Phase 5.2 constructed dataset
(3,106 records). Follow the full 8-track, 12-question-per-task design
brief exactly, be honest about which tracks the current dataset actually
supports, and produce 15 required deliverables plus additional
machine-readable cross-reference files.

## What was delivered

15 required files plus 5 additional cross-reference files, all under
`experiments/results/phase5_benchmark_specification/20260826T055915Z/`:

- `PHASE5_3_BENCHMARK_SPECIFICATION.md` — narrative spec covering purpose,
  benchmark-vs-dataset instance derivation, all 8 tracks, baseline ladder,
  ablations, metric catalog summary, leakage rules, statistical reporting,
  task granularity, and an explicit honesty statement about how the system
  would score.
- `PHASE5_3_BENCHMARK_SCHEMA.json` — machine-readable task-instance shape,
  versioning policy.
- `PHASE5_3_TASK_CATALOG.json` — 16 task instances across 8 tracks, each
  answering all 12 required design-principle questions, each with an
  explicit `eligibility_status`.
- `PHASE5_3_METRIC_CATALOG.json` — 33 metrics, each with mathematical
  definition, unit, interpretation, failure mode, direction, pathological
  cases; 4 explicit forbidden-standalone-use rules.
- `PHASE5_3_SPLIT_POLICY.md`, `PHASE5_3_LEAKAGE_POLICY.md` (12 rules),
  `PHASE5_3_BASELINE_CATALOG.json` (10 baselines),
  `PHASE5_3_ABLATION_MATRIX.json` (5 ablations),
  `PHASE5_3_DATASET_COVERAGE.json` (per-track honest support status),
  `PHASE5_3_LIMITATIONS.md` (all 5 Phase 5.2 limitations, individually
  handled), `PHASE5_3_PUBLICATION_BOUNDARY.md`,
  `PHASE5_3_REPRODUCIBILITY_PROTOCOL.md`.
- `PHASE5_3_VALIDATION_REPORT.md` — the required self-audit checklist,
  each item checked against actual file content.
- `SHA256_MANIFEST.json` — generated last, over the full directory.
- Additional: `benchmark_track_matrix.json`, `benchmark_eligibility.json`,
  `metric_definitions.json`, `task_lineage.json`,
  `unsupported_capabilities.json`.

## What is honestly incomplete or limited

Of 16 defined tasks: 3 are `EVALUABLE` (the three uncertainty tasks), 6 are
`LIMITED` (the three abstention tasks, diagnosis, recovery, end-to-end),
and 7 are `NOT_EVALUABLE` from the current canonical dataset (all four
failure-prediction tasks, memory, both generalization tasks). Of the 8
tracks, only `uncertainty` is `FULLY_SUPPORTED`; `failure_prediction`,
`memory`, and `generalization` are `UNSUPPORTED_CONTRACT_ONLY`. This
distribution is a direct, honest consequence of the five Phase 5.2
limitations (no per-checkpoint telemetry, no per-episode environment_id,
no memory-write timestamps, no ABSTAIN episodes, aggregate-only headline
verdicts for several failure families) — none of it was worked around by
inventing evidence.

## Bottom line

This specification is deliberately harder on the system than a marketing
document would be: it names, for each of 8 tracks, exactly what a
skeptical reader could and could not conclude from the current dataset,
and it preserves every disclosed Phase 4 negative/inconclusive finding
(sentiment's calibration-without-discrimination ceiling, the always-fires
disqualification of cpu/pooled-oom/flaky prediction, the confounded
predictor-ablation result, the single-environment generalization gap)
exactly as the frozen record states them, rather than rounding any of them
up. Phase 4, Phase 5.1, and Phase 5.2 remain untouched — see
`PHASE5_3_VALIDATION_REPORT.md` for the git evidence.
