# Phase 5.2 Split Validation Report

Total records: 3106

## Per-split counts

| split | records | workloads | runs | episodes |
|---|---|---|---|---|
| calibration_validation | 482 | 480 | 482 | 482 |
| test | 482 | 482 | 482 | 482 |
| train | 2142 | 2142 | 2142 | 2142 |

## Forbidden overlap counts (must all be zero)

- train ∩ calibration_validation = 0
- train ∩ test = 0
- calibration_validation ∩ test = 0
- workload_id records crossing a forbidden split boundary = 0

**Overall: PASS -- all forbidden overlaps are zero**

## Environment-axis (held-out/robustness) boundary check

Status: DISCLOSED LIMITATION / NOT APPLICABLE to the current record set.
No source used in this construction carries a genuine per-episode Phase-4.9 EnvironmentId (phase4.9-env-baseline-cpu / -memory-constrained / -dependency-network-constrained); every extracted record's identity.environment_id is UNSPECIFIED_PRE_4_9 because the only sources with real per-episode raw evidence available to this construction (phase4_4_autonomy_pipeline/results.json, phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl, phase4_6_to_4_10 agent-task raw evidence) predate Phase 4.9's EnvironmentProfile introduction or do not carry it at the per-record level. The Phase-4.9/post-P5-Step-4 environment-role evidence that DOES exist (experiments/results/post_p5_remediation/20260825T064402Z/raw/p4_step4_results.json) is aggregate-only (per-environment metric rollups, no retained per-episode/per-run identity), so it cannot be joined back to individual dataset records without fabricating a join key. This is classified as (c) unavailable source evidence, disclosed rather than worked around by inventing environment_id values.

## Known coverage gap (Phase 5.1 Split Policy §6)

Per PHASE5_1_SPLIT_POLICY.md §6, prior full-loop evaluation runs used a unique workload_id per episode by design in some runs, meaning the workload-grouping rule is exercised only where multiple records genuinely share a workload_id (this happens for the arithmetic self-consistency family, grouped by seed, and for the controlled-runtime `workload-recurring` repeated-incident episodes in Phase 4.4). Other workload_ids in this dataset are 1:1 with a single record by construction (agent sentiment/QA task instances, most controlled-runtime episodes) -- this is a coverage characteristic of the source evidence, not a flaw in the split policy or its enforcement.
