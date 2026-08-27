# Phase 5.1 — Canonical Dataset Specification

Status: DESIGN/SPECIFICATION ONLY. No dataset is constructed, no benchmark is
implemented, no model is trained, nothing is uploaded, and no Phase 4 script
is executed by this document or its companions. This specification designs
a canonical dataset and provenance contract over the now-**FROZEN** Phase 4
evidence base (see `FINAL_PHASE4_CLOSURE_REPORT.md`, `PHASE 4 STATUS =
FROZEN`). It touches no file under `experiments/results/` other than the
new `phase5_dataset_specification/` directory this run writes to, and no
file under `src/phase4/`, `src/runtime/`, `src/recovery/`,
`src/failure_experience/`, `src/decision/`, or `docs/archive/`.

## 0. How this document relates to its companions

This file is the narrative entry point. It is deliberately non-duplicative:
- Source classification detail → `PHASE5_1_SOURCE_INVENTORY.json`
- Field-by-field provenance → `PHASE5_1_PROVENANCE_CONTRACT.md` and
  `PHASE5_1_FIELD_LINEAGE.json`
- Machine-readable schema → `PHASE5_1_SCHEMA.json`
- Split design → `PHASE5_1_SPLIT_POLICY.md`
- Leakage rules → `PHASE5_1_LEAKAGE_POLICY.md`
- Public/internal boundary → `PHASE5_1_PUBLICATION_BOUNDARY.md`
- Benchmark-ready view designs → `PHASE5_1_BENCHMARK_VIEWS.md`
- Self-audit against the required checklist → `PHASE5_1_SYNTHESIS.md`

## 1. Step 1 audit summary

The full classification of every evidence source is in
`PHASE5_1_SOURCE_INVENTORY.json` (43 sources, classes 1–8). In condensed
form, the Phase 4 evidence base separates into three genuinely distinct
data-generating processes that must never be merged:

1. **Generation 3 (Gen 3) controlled-runtime evidence** — `src/phase4/*`,
   `experiments/results/phase4_4_autonomy_pipeline/` through
   `post_p5_remediation_followups/20260825T144031Z/`, `system_evaluation/`,
   `generalization/`, `counterfactual_generalization/`,
   `memory_composition{,_v2}/`, `learning_influence/`. Real local
   subprocess execution, real telemetry, real recovery execution, real
   HF-model inference on templated text. This is the ONLY evidence class
   this Phase 5.1 dataset design targets.
2. **Generation 2 / V1 (frozen, historical)** — `src/runtime/`,
   `src/recovery/`, `src/failure_experience/`, `src/decision/policy.py`,
   `experiments/results/v1_1/`, `v1_control_reconciliation/`,
   `reliability_runtime_v{1,2}/`, `alibaba_closed_loop_v{1,2}/`. A
   different data-generating process (historical Alibaba GPU2020 trace
   replay, not live execution). Out of scope for this dataset; referenced
   only to explain why it is excluded (§6).
3. **Generation 1 / Phase 3 (frozen, historical)** — `src/failure_memory/`,
   `src/failure_patterns/`, `experiments/results/phase3_*`. Synthetic
   episodic data and real-data-track (Alibaba/AgentRx/AIOps) evidence used
   for an earlier, since-superseded research question. Out of scope.

Within the Gen-3 evidence, the audit found the honesty discipline (§29 of
`docs/MASTER_RECORD_CONTENT.md`) already does most of the work a dataset
provenance contract needs: every metric traces to a specific report and
raw-evidence path, negative results are never hidden, and known defects
(Windows RSS telemetry, GPU-probe nondeterminism, timestamp-tie boundary
bug, `LogisticRegression` unpinned `random_state`) are explicitly disclosed
rather than silently corrected retroactively. This specification's job is
to turn that narrative discipline into a machine-checkable schema and
lineage contract.

## 2. Canonical dataset unit

**Investigated, not assumed.** Reading `src/phase4/architecture.py`,
`controlled_runtime.py`, `environments.py`, `prediction_training.py`,
`memory.py`, and `agent_task.py` together, the evidence supports exactly
this hierarchy — no level is invented, and none of the evidence supports a
finer or coarser canonical level than what is listed:

```
dataset (phase5.1 release)
 └─ track                  ("controlled_runtime" | "agent_task")
     └─ environment        (EnvironmentProfile: baseline_cpu | memory_constrained
                             | dependency_network_constrained)  [environment_id]
         └─ workload        (a scenario instance: workload_id, e.g.
                             "<environment_id>-<split>-seed-<seed>",
                             or an agent TaskInstance seed)       [workload_id]
             └─ run          (one ControlledRuntime.run() invocation, or one
                              run_agent_task() invocation)         [run_id]
                 └─ episode  (one full AutonomyState walk:
                              RECEIVED..COMPLETED)                 [episode_id]
                     ├─ observation(s)      (telemetry_observed / checkpoint rows)
                     ├─ prediction          (Prediction, at most one per episode)
                     ├─ decision            (Decision, exactly one per episode)
                     ├─ diagnosis           (Diagnosis, zero or more, one per
                                             DIAGNOSING state entry)
                     ├─ recovery_action     (RecoveryAction + execution result,
                                             zero or more, one per PLANNING->
                                             EXECUTING cycle)
                     ├─ validation_outcome  (ValidationOutcome, one per
                                             recovery_action)
                     ├─ memory_interaction  (zero or more MemoryMatch reads +
                                             at most one MemoryRecord write,
                                             the write only after validation)
                     └─ agent_output        (agent-task track only: TaskInstance
                                             + SelfConsistencyResult / QA span
                                             result / sentiment result)
```

**Why each level exists, and why not a different level:**

- **track**: `run_workload()` and `run_agent_task()` are two structurally
  different entry points into the same `AutonomyState` machine
  (`docs/MASTER_RECORD_CONTENT.md` §4). They have different observation
  spaces (process telemetry vs. agent self-consistency/softmax-margin/
  span-logit), different failure taxonomies, and different oracle
  definitions. Merging them into one generic "agent" record — as the
  design principles explicitly forbid — would erase the very distinction
  (arithmetic self-consistency vs. sentiment softmax-margin vs. QA
  span-logit) that Phase 4's own uncertainty findings depend on (§14 of
  the master record: three "genuinely different uncertainty mechanisms...
  never forced into a single blended signal").
- **environment**: `environments.py` defines three environments as
  genuinely different `RuntimeConfig`/resource-limit/dependency-condition
  populations, not merely different labels attached to identical runs (the
  module's own docstring insists on this). `environment_id` is the correct
  and only level at which "was this fit on this data or evaluated zero-shot
  against it" can be asked — this is the DEVELOPMENT/HELD-OUT/ROBUSTNESS
  boundary Phase 4.9 established and post-P5 remediation reused.
- **workload**: `FailureMemoryStore` scopes memory strictly by
  `(workload_id, environment_id, failure_class)`, never by `run_id`
  (`memory.py` docstring, contract item 1). This is the level at which
  "is this a repeated incident" is defined — the memory repeated-incident
  experiment (Step 6) is built entirely on recognizing the *same*
  `workload_id` recurring across separate `run_id`s. A dataset that
  discarded `workload_id` in favor of `run_id` alone could not represent
  repeated-incident structure at all.
- **run**: One `ControlledRuntime.run()` call (or one `run_agent_task()`
  call) is the atomic unit of "did a failure happen and was it detected" —
  it owns exactly one `run_id`, one set of raw telemetry events, and at
  most one ground-truth failure occurrence. `DiagnosisEngine`'s fixed
  cross-run-contamination bug (`_eligible_current_incident`,
  `EVALUATION_INCIDENT_001`) is precisely a bug in respecting this boundary
  — evidence that `run_id` is a load-bearing identity level, not a
  convenience field.
- **episode**: The `AutonomyState` walk (`architecture.py`) is the unit
  that owns exactly one `Decision`, zero-or-one `Prediction`, and the
  recovery/validation/learning cycle that follows it. A run can, in
  principle, revisit `DIAGNOSING` after `NOT_RECOVERED` (see the
  `ALLOWED` transition table: `NOT_RECOVERED -> {DIAGNOSING, COMPLETED}`),
  so `episode_id` is tracked distinctly from `run_id` to represent
  multi-attempt recovery within one run without conflating attempts.
- **sub-episode records** (observation, prediction, decision, diagnosis,
  recovery_action, validation_outcome, memory_interaction, agent_output):
  each is a distinct frozen dataclass in `architecture.py`/`memory.py`/
  `agent_task.py` with its own identity field
  (`prediction_id`/`decision_id`/`diagnosis_id`/`action_id`/`memory_id`) and
  its own `provenance`. Collapsing them into a single flat "event" row
  would destroy the temporal/authority distinctions §3 below depends on
  (e.g. a `Diagnosis` output must never silently become a `MemoryRecord`'s
  `validated_outcome` — they are different objects with different
  authorities by design).

### Relationships (explicit)

- **run vs. episode**: 1 run → 1..N episodes (N=1 in the common case; N>1
  only when `NOT_RECOVERED` routes back to `DIAGNOSING`).
- **workload vs. run**: 1 workload_id → 1..N runs (N>1 is exactly the
  "repeated incident" case memory scoping is built to recognize).
- **environment vs. workload**: 1 environment_id → many workload_ids; a
  workload_id's scenario-generating function (`scenario_fn`) is itself
  environment-specific (`_scenario_baseline` vs.
  `_scenario_memory_constrained` vs. `_scenario_dependency_constrained`),
  so a workload_id implicitly belongs to exactly one environment and must
  never be evaluated as if generated by another.
- **failure incident vs. decision boundary**: a failure incident is
  identified by a `failure_detected`/`failure_classified` event pair inside
  one run; the decision boundary is the `prediction_decision_time` inside
  `DecisionTimeContract` — everything at or before that instant is eligible
  input to `Decision`; everything after is an outcome, never an input
  (§3.1 leakage rule).
- **recovery attempt vs. memory incident history**: a recovery attempt is
  one `recovery_action` + its `validation_outcome`, produced by the CURRENT
  episode; "memory incident history" is the set of *other* episodes'
  already-closed, already-validated `MemoryRecord`s visible to
  `FailureMemoryStore.retrieve()` at this episode's `at_or_before` boundary
  — structurally guaranteed never to include the current run
  (`source_run_id != exclude_run_id` in `memory.py::retrieve`).

## 3. Design-principle compliance summary

Each of the 8 mandated principles is addressed in a dedicated companion
document; this section states how, briefly, so the mapping is explicit:

1. **Provenance first** → every schema field in `PHASE5_1_SCHEMA.json` has
   a `provenance` object; every field's source is enumerated in
   `PHASE5_1_FIELD_LINEAGE.json`. No field is defined without a traced
   source; fields with no current source are marked
   `"availability": "NOT_CURRENTLY_AVAILABLE"` rather than omitted silently.
2. **Temporal integrity** → `PHASE5_1_LEAKAGE_POLICY.md` §1, built directly
   on `Availability` (`BEFORE`/`AT`/`AFTER`/`OUTCOME`/`UNKNOWN`/
   `UNAVAILABLE`) from `src/data_foundation/foundation.py`, already
   load-bearing in the live code (`ensure_decision_snapshot` rejects
   anything not `BEFORE`/`AT`).
3. **No data leakage** → `PHASE5_1_LEAKAGE_POLICY.md`, one rule per leakage
   vector named in the task brief.
4. **Preserve negative results** → §4 below and `PHASE5_1_SYNTHESIS.md`
   checklist item; the schema's `outcome_class` and `capability_grade`
   fields are designed to represent NOT_VALIDATED/ABSTAINED/UNKNOWN
   equally to RECOVERED/ANSWER, never filtered out.
5. **Do not mix evidence classes** → `evidence_class` is a first-class,
   required schema field on every record (enum matching
   `PHASE5_1_SOURCE_INVENTORY.json`'s 8 classes).
6. **Preserve experimental boundaries** → `experimental_boundary` field
   (`controlled_runtime_evidence` | `research_evaluation_evidence` |
   `benchmark_ready_evidence` | `engineering_only_evidence`), see
   `PHASE5_1_PUBLICATION_BOUNDARY.md`.
7. **Reproducibility** → `dataset_version`, `schema_version`,
   `source_artifact_version`, ID fields, seeds, software/runtime versions,
   checksums — all present in `PHASE5_1_SCHEMA.json`'s `identity` and
   `reproducibility` blocks.
8. **Immutability** → §5 below; the dataset generation procedure (not yet
   implemented) would be a pure function of frozen evidence +
   this specification, never of a mutable intermediate.

## 4. Preserving negative results (explicit)

The frozen record is unusually rich in honestly-reported negative and
inconclusive results (`docs/MASTER_RECORD_CONTENT.md` §29). This dataset
design is built so none of these can be filtered out by a naive "keep only
successful episodes" query:

- Every episode record carries an explicit `outcome_class` including
  `NOT_RECOVERED`, `ABSTAINED`, `UNKNOWN` — not just `RECOVERED`.
- Every prediction record carries `predictability_status` (one of
  `STRONG_EVIDENCE`, `PLAUSIBLE`, `NOT_VALIDATED`, `NOT_PREDICTABLE_SINGLE_CLASS`,
  `NOT_EVALUATED`) rather than only a numeric score, so a near-chance or
  always-fires model is represented, not discarded.
- Every diagnosis record allows `suspected_cause = null` (`UNKNOWN`
  diagnosis) as a valid, retained value.
- Capability-grade fields (`A`/`B`/`C`/`D`) from the master record's own
  grading system (§22/§32) are attached at the benchmark-view level
  (`PHASE5_1_BENCHMARK_VIEWS.md`) precisely so a `D`-graded capability
  (e.g. `cpu` prediction, sentiment discrimination, Phase 4.3/4.4 recovery
  learning) is present in the dataset with its grade, not excluded because
  it "didn't work."
- The `detectable_only_scope` AUC=0.857 mixing artifact (class 8,
  `SRC-042`) is retained in the source inventory and explicitly flagged
  `unsupported_as_label = true` — it is preserved as a documented
  cautionary finding, not silently dropped, but it is barred from ever
  becoming a ground-truth label.

## 5. Immutability and generation procedure (design, not implementation)

The canonical dataset (once actually built, in a later phase) would be
generated by a pure, versioned function:

```
canonical_dataset = generate(
    frozen_evidence_paths = [<SRC-001..041 raw/derived paths>],
    generation_spec_version = "phase5.1-generation-spec-v1",
    schema_version = SCHEMA_VERSION (see PHASE5_1_SCHEMA.json),
)
```

No step of that function may write back to any frozen evidence path; the
function's own output is itself versioned and checksummed
(`SHA256_MANIFEST.json` convention, reusing
`scripts/generate_sha256_manifest.py`'s exact method — sorted `rglob`,
SHA-256 per file, manifest excluded from its own hash listing, written
last). This specification defines the function's *contract* (inputs,
schema, splits, leakage rules); it does not implement it, per the task's
explicit prohibition on constructing the dataset in this phase.

## 6. What is explicitly excluded from the canonical dataset

- All Generation 1 and Generation 2 (V1) evidence (§1, classes 4). A future
  phase could design an explicit, separately-versioned cross-generation
  comparison view, but that is not this specification's scope and nothing
  here should be read as inviting silent merging.
- `.docx`/duplicated convenience outputs (class 5).
- Raw pytest logs and other engineering-only artifacts (class 6) — useful
  for reproducibility verification, not dataset content.
- Any pre-RSS-telemetry-fix OOM evidence, evaluated as OOM signal (class 8,
  `SRC-043`) — retained only as evidence of the defect itself, tagged as
  such, never as OOM predictive evidence.
- `detectable_only_scope`'s AUC=0.857 as a label source (class 8, `SRC-042`).

## 7. Confirmation of Phase 4 immutability during this work

This file and its ten companions are new files under
`experiments/results/phase5_dataset_specification/20260826T053011Z/`. No
existing Phase 4 evidence, report, or source file was opened in write mode
by this work. See `PHASE5_1_SYNTHESIS.md` §"Phase 4 untouched" for the
`git status`/`git diff --stat` evidence captured at completion.
