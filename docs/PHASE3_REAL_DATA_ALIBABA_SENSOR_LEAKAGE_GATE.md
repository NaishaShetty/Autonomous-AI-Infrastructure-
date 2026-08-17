# Alibaba GPU2020 — Sensor/Machine-Metric Leakage Gate Decision

**Status: RESOLVED (not "potentially leaking" — confirmed, from
official documentation, not inferred).**

## Question posed

Do `pai_sensor_table` and `pai_machine_metric` represent (A)
measurements available during execution / before the outcome, or (B)
full-lifetime/post-hoc aggregates that may be unavailable at
prediction time?

## Answer: (B), for both tables, confirmed by the publisher's own documentation

Source: `data/provenance/alibaba_gpu2020/official_README.md` (official
Alibaba clusterdata repo, fetched 2026-08-13).

- **`pai_sensor_table`**, quoted verbatim: *"all the sensor metrics
  (CPU, GPU, Memory, I/O) in this table are collected for each
  instance (indexed by `worker_name`) but not task, taking the
  average of all data in the instance's lifetime (except for `max_mem`
  and `max_gpu_wrk_mem` being the maximum)."*
- **`pai_machine_metric`**, quoted verbatim: *"these metrics are
  machine-level metrics, taking average of the sensor data during the
  instance's (indexed by `worker_name`) lifetime."* Its `start_time`/
  `end_time` columns are not an independent reporting window — they
  are literally copies of the parent instance's own launch/completion
  timestamps (per `pai_instance_table`'s documented fields).

An instance's "lifetime" runs from its `start_time` to its
`end_time` — and `end_time` is only known once the instance has
**already terminated** (successfully or via failure; see
`pai_instance_table.status`). A full-lifetime average by construction
incorporates information from the entire run, including its final
moments and its manner of ending — it cannot be computed at any point
strictly before the instance's outcome is already determined.

## Decision

Both tables are classified **CONFIRMED LEAKING** (not merely
"potentially leaking") for any task framed as *"predict failure before
it happens"* — i.e., any decision-time / pre-outcome evaluation.

**Exclusions:**
- No field from `pai_sensor_table` or `pai_machine_metric` may be used
  as a decision-time input feature in any Phase 3.1–3.6 real-data
  predictive evaluation (H1 representation, H3 F-vs-B, H4
  attack-generalization, H5 complementarity).
- `max_mem` and `max_gpu_wrk_mem` are lifetime *maxima*, not averages
  — same exclusion applies; a maximum over the full lifetime is at
  least as leaky as an average.

**Retained uses (must be clearly labeled as post-hoc, not predictive):**
- Descriptive/exploratory analysis: e.g., "did Failed instances show
  different average GPU utilization than Terminated instances?" is a
  valid post-hoc question and these tables are the right evidence for
  it.
- Diagnosis-adjacent analysis, if ever attempted: a *diagnosis* task
  (explaining why something already failed) may legitimately consume
  post-outcome information, unlike a *prediction* task — but this
  still needs to be evaluated separately from any pre-outcome claim
  and explicitly labeled as diagnosis-only, given neither table
  carries an actual failure-cause field (see the feasibility audit —
  H6 remains NOT EVALUABLE on Alibaba regardless of this gate, since
  there is no cause label to diagnose, only a terminal status).

## What this changes vs. the prior feasibility audit

The prior audit (before official docs were available) had:
- `pai_sensor_table`: flagged "leakage status unresolved," provisional
  "potentially leaking."
- `pai_machine_metric`: speculated its `start_time`/`end_time` might
  be an independent, possibly pre-outcome, reporting window —
  incorrect. It is the same full-instance-lifetime window as the
  sensor table, with the same leakage profile.

Both are now **definitively excluded** from decision-time feature
sets, not provisionally flagged. This is a stricter conclusion than
the audit's provisional stance, arrived at by consulting the official
schema rather than guessing — consistent with the "if timing cannot be
established with confidence, classify as leaking" instruction, except
here timing *was* established with confidence, and it confirms
leakage rather than merely failing to rule it out.

## Downstream consequence for representation experiments (H1/H5)

Any "richer representation" candidate built from Alibaba data for
Phase 3.2-equivalent real-data representation experiments must be
restricted to genuinely pre-outcome fields:
- `pai_job_table`: `user`, `start_time` (submission time only)
- `pai_task_table`: `task_name`, `inst_num`, `plan_cpu`, `plan_mem`,
  `plan_gpu`, `gpu_type`, task `start_time`
- `pai_instance_table`: `machine` (once scheduled), instance
  `start_time`
- `pai_group_tag_table`: `gpu_type_spec`, `group`, `workload` (sparse)
- `pai_machine_spec`: all fields (static machine properties, never
  leaking)

This is a **request/scheduling-time feature set**, not a
runtime-telemetry feature set — a materially weaker representation
than what the sensor/machine_metric tables would have offered, and
this constraint should be stated plainly in the eventual Phase 3.2
real-data results rather than worked around.
