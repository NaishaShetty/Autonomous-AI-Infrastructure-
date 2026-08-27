# Phase 5.3 — Limitations

Status: SPECIFICATION ONLY. This document gives each of the five
Phase 5.2-disclosed dataset limitations its own explicit benchmark-spec
handling, per the task brief's requirement that none be glossed over.

## Limitation 1 — No per-checkpoint observation telemetry

**Source of the gap**: the two per-episode controlled_runtime raw sources
(`phase4_4_autonomy_pipeline/results.json`,
`phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl`) retain
only episode-level summaries; `observations: []` is empty for every one of
the 3,106 records (`DATASET_README.md`).

**Benchmark-spec handling**:
- No task in `PHASE5_3_TASK_CATALOG.json` claims a fine-grained
  rolling-prediction result (i.e. "prediction confidence at checkpoint k of
  n"). All prediction tasks (PRED-*) are scored at the
  `one_prediction_checkpoint` granularity meaning exactly one
  end-of-episode prediction per episode, not a rolling trajectory.
- **Future data requirement**: a rolling-prediction benchmark would require
  a source that retains `process_rss_bytes`/`process_cpu_percent` (or
  equivalent) at each checkpoint, with an explicit checkpoint index and
  timestamp, joined to the same `episode_id`.
- Episode-level vs rolling evaluation is kept explicitly distinct in
  `PHASE5_3_BENCHMARK_SCHEMA.json`'s `EvaluationUnit` enum
  (`one_prediction_checkpoint` is defined to mean "the checkpoint actually
  retained," which today is exactly one per episode — this specification
  does not claim it means "one of many rolling checkpoints").

## Limitation 2 — No real per-episode environment_id

**Source of the gap**: every record's `identity.environment_id` is
`UNSPECIFIED_PRE_4_9`; the sources ingested predate Phase 4.9's
`EnvironmentProfile` introduction or never carried it per-record
(`split_audit.json`'s `environment_axis_check`).

**Benchmark-spec handling**:
- The **generalization track (Track 7) is marked `NOT_EVALUABLE` from
  current canonical dataset records**, stated plainly, not softened — see
  `GEN-RANKING-CONTRACT` and `GEN-OPERATING-POINT-CONTRACT` in
  `PHASE5_3_TASK_CATALOG.json`, both `eligibility_status:
  NOT_EVALUABLE`, `dataset_coverage_status: UNSUPPORTED_CONTRACT_ONLY`.
- **What evidence would be needed**: a per-episode field carrying one of
  `phase4.9-env-baseline-cpu` / `-memory-constrained` /
  `-dependency-network-constrained`, joined to the same `run_id`/
  `episode_id` already in the dataset — not a new identifier scheme, the
  exact one Phase 4.9 already defines.
- **Not lost, just not in the canonical per-episode dataset**: Phase 4's
  own environment-generalization evidence (OOM AUROC 0.989 dev -> 0.983
  held-out -> 0.935 robustness; the "ranking transfers, operating point
  does not" finding) is preserved as `PUBLIC_METADATA` in
  `docs/MASTER_RECORD_CONTENT.md` and the `post_p5_remediation*` aggregate
  artifacts. This benchmark specification references that evidence (see
  the `supporting_evidence` field of `GEN-RANKING-CONTRACT`/
  `GEN-OPERATING-POINT-CONTRACT`) without fabricating it into fake
  per-episode records.

## Limitation 3 — No memory-write timestamps

**Source of the gap**: `memory_used` is retained only as a boolean flag;
no `MemoryRecord`/`memory_id` write timestamp exists in the ingested
sources (`DATASET_README.md`).

**Benchmark-spec handling**:
- The memory benchmark (Track 6, `MEM-EVAL`) is restricted to demonstrated
  temporal information only — since no temporal information about memory
  writes is demonstrated at all in the current dataset, `MEM-EVAL` is
  marked `NOT_EVALUABLE` / `UNSUPPORTED_CONTRACT_ONLY`, not merely
  `LIMITED`.
- **Future schema requirement**: `memory_interaction.write_time` (or
  equivalent `recorded_at`) as a required, non-null field whenever
  `memory_used = true`, sourced from `LearningManager`'s actual write path
  (which Phase 5.1's own schema and leakage rule 9 already assume exists at
  the live-code level — the gap is in what Phase 5.2's specific ingested
  sources retained, not in the underlying system's own capability).

## Limitation 4 — No ABSTAIN episodes in ingested sources

**Source of the gap**: `decision` values observed across all 3,106 records
are only `ANSWER` (4), `REVIEW` (1), or absent/`NOT_APPLICABLE` (3,101);
zero `ABSTAIN` or `RETRY` decisions exist
(`dataset_statistics.json` `by_decision_type`).

**Benchmark-spec handling**:
- The **abstention contract** (Track 2) is defined so that a policy CAN be
  simulated post-hoc over the retained uncertainty signal
  (agreement_rate/softmax_margin/span_logit_confidence) and scored against
  `agent_output.is_correct` — this part IS currently evaluable
  (`ABST-ARITH`/`ABST-SENT`/`ABST-QA`, `dataset_coverage_status:
  PARTIALLY_SUPPORTED`).
- What is **NOT** currently evaluable: any claim about a REALIZED
  ABSTAIN/RETRY decision's actual observed downstream effect (e.g. "how
  often did a real ABSTAIN decision avoid a real wrong answer") — there is
  no such realized decision in the dataset to measure. This distinction is
  stated explicitly in each abstention task's `unavailable_evidence` field.
- Metrics that require a realized ABSTAIN population
  (e.g. a "false-abstention rate on episodes the system actually chose to
  abstain on, using the REAL decision log rather than a simulated policy")
  are marked `NOT_EVALUABLE` at the per-task level, not silently computed
  on the simulated substitute as if it were the same thing.

## Limitation 5 — Aggregate-only Phase 4 results (cpu/oom/flaky NOT_VALIDATED, generalization, ablations)

**Source of the gap**: `resource_unavailable`, pooled `oom`,
`cpu`, `flaky` family-level predictability verdicts and the environment-
generalization results live in aggregate evaluation artifacts
(`post_p5_remediation/`, `post_p5_remediation_followups/`) with no
retained per-episode join key (`PHASE5_2_DATASET_CONSTRUCTION_REPORT.md`
§1, §9(c); `NEGATIVE_RESULT_PRESERVATION_REPORT.md`).

**Benchmark-spec handling — explicit disposition of each**:
- **Become benchmark metadata** (referenced, not duplicated, as
  `supporting_evidence` in the relevant task definitions): the exact
  numeric verdicts (resource_unavailable STRONG_EVIDENCE; oom AUROC 0.780
  ranking-real-but-operating-point-invalid; cpu/flaky NOT_VALIDATED
  always-fires; OOM environment generalization 0.989/0.983/0.935) — all
  four appear as `supporting_evidence` text in `PRED-RESOURCE-UNAVAILABLE`,
  `PRED-OOM`, `PRED-CPU`, `PRED-FLAKY`, `GEN-RANKING-CONTRACT`,
  `GEN-OPERATING-POINT-CONTRACT`.
- **Become validation evidence/context, not benchmark instances**: the
  aggregate files themselves remain `PUBLIC_METADATA` per
  `PHASE5_1_PUBLICATION_BOUNDARY.md`'s existing classification — this
  specification does not re-classify them.
- **Cannot become record-level benchmark instances**: none of the four
  families above have a task marked `EVALUABLE` at the record level in
  `PHASE5_3_TASK_CATALOG.json` — all four are `NOT_EVALUABLE` /
  `UNSUPPORTED_CONTRACT_ONLY`, precisely because no per-episode join key
  exists to construct real record-level task instances. This specification
  explicitly refuses to force them into the dataset — consistent with
  `PHASE5_2_SYNTHESIS.md`'s own stated boundary ("did not invent joins that
  the frozen evidence does not support").

## Cross-cutting statement

None of these five limitations is treated as a defect to silently patch
around. Each blocks specific, named benchmark tasks from being
`EVALUABLE`, and each blocked task is explicitly marked `LIMITED` or
`NOT_EVALUABLE` in `PHASE5_3_TASK_CATALOG.json` rather than omitted or
quietly downgraded in scope. A future Phase 5.4 (dataset extension) could
resolve any of these five limitations only by ingesting genuinely new
per-episode evidence that retains the missing join keys/timestamps/fields
— never by inferring or fabricating them from the aggregate evidence that
already exists.
