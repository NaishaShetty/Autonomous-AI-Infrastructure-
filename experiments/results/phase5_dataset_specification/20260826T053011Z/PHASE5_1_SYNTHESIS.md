# Phase 5.1 — Synthesis and Specification Audit

## 1. Summary

This run designs (does not construct) a canonical dataset specification and
provenance contract over the frozen Phase 4 evidence. Ten files were
produced in this run directory:
`PHASE5_1_DATASET_SPECIFICATION.md`, `PHASE5_1_PROVENANCE_CONTRACT.md`,
`PHASE5_1_SCHEMA.json`, `PHASE5_1_SOURCE_INVENTORY.json`,
`PHASE5_1_SPLIT_POLICY.md`, `PHASE5_1_LEAKAGE_POLICY.md`,
`PHASE5_1_PUBLICATION_BOUNDARY.md`, `PHASE5_1_BENCHMARK_VIEWS.md`,
`PHASE5_1_FIELD_LINEAGE.json`, this file. `SHA256_MANIFEST.json` is
generated after this file, last, over the full directory.

## 2. Specification audit checklist (required by the task)

- [x] **Every proposed field has a source or explicit "not currently
  available" status.** `PHASE5_1_FIELD_LINEAGE.json` lists every schema
  field with `availability = AVAILABLE | PARTIALLY_AVAILABLE |
  NOT_CURRENTLY_AVAILABLE` and a `source`; a dedicated
  `fields_explicitly_not_currently_available` block names 5 items with
  reasons (human annotation, diagnosis ground-truth match label,
  per-environment OOM threshold recalibration, resource_unavailable
  held-out/robustness degradation, large-scale repeated-workload memory
  effect).
- [x] **No field silently invents data.** `PHASE5_1_PROVENANCE_CONTRACT.md`
  §2 states the four permitted rules (directly observed / deterministically
  derived / model output / explicitly unavailable) and forbids anything
  outside them; `PHASE5_1_SCHEMA.json` marks nullable/optional exactly
  where the underlying evidence can be absent (e.g.
  `observations[].process_rss_bytes` typed `["integer","null"]` to reflect
  the real, documented Windows RSS defect rather than defaulting to 0).
- [x] **Every label has a defined origin; ground truth separated from
  model output.** `PHASE5_1_PROVENANCE_CONTRACT.md` §3 table maps every
  label category (objective ground truth / observed outcome / executor
  self-report / derived label / model prediction / model diagnosis /
  human annotation / UNKNOWN / UNAVAILABLE / NOT_APPLICABLE) to a `LabelType`
  enum value in the schema, with a hard rule that MODEL_PREDICTION/
  MODEL_DIAGNOSIS can never populate another record's ground_truth field.
- [x] **Temporal availability is explicit; future information cannot enter
  pre-decision inputs.** `Availability` enum (mirroring
  `src/data_foundation/foundation.py` exactly) is a required field on
  every temporal-bearing record; `PHASE5_1_LEAKAGE_POLICY.md` rules 1 and
  10 state the enforcement explicitly, referencing the live
  `ensure_decision_snapshot()`/`DecisionTimeContract.validate()` code that
  already enforces this at runtime.
- [x] **Run/workload/environment lineage is explicit.** §2 of
  `PHASE5_1_DATASET_SPECIFICATION.md` gives the full
  dataset→track→environment→workload→run→episode hierarchy with an
  explanation of why each level exists, sourced directly from
  `architecture.py`/`environments.py`/`memory.py`/`agent_task.py` reading,
  not assumed.
- [x] **Repeated incidents cannot leak across splits.** `PHASE5_1_SPLIT_POLICY.md`
  §2 identifies `workload_id` as the mandatory grouping key, justified by
  the Step 6 repeated-incident experiment's own scoping discipline;
  `PHASE5_1_LEAKAGE_POLICY.md` rule 5 restates it as a leakage rule.
- [x] **Train/calibration/test and environment-held-out boundaries are
  explicit.** `PHASE5_1_SPLIT_POLICY.md` §3-4 define both axes
  independently and state they must never be conflated; the schema's
  `split_assignment` enum keeps both axes visible in one field without
  merging their meaning.
- [x] **Synthetic/test evidence is clearly labeled.** `evidence_class`
  (1-8) is a required field on every record; class 7
  (non-research synthetic fixtures — templated sentiment/QA text) and
  class 6 (engineering test artifacts) are distinct from class 1/2 (real
  controlled-runtime evidence), per `PHASE5_1_SOURCE_INVENTORY.json`.
- [x] **Negative results can be represented.** `PredictabilityStatus`
  includes `NOT_VALIDATED` and `NOT_PREDICTABLE_SINGLE_CLASS` as first-class
  values (not merely a low score); `CapabilityGrade` includes `D`; §4 of
  the main specification states explicitly that no query pattern in this
  design filters out abstained/failed/UNKNOWN records.
- [x] **UNKNOWN/UNAVAILABLE/NOT_APPLICABLE are distinct.** All three are
  distinct enum values in `LabelType` and used distinctly throughout the
  schema (e.g. `diagnosis.suspected_cause: null` = UNKNOWN;
  `GPU_DEVICE_FAILURE` recovery = NOT_APPLICABLE per Benchmark View 5;
  telemetry never captured on a given platform = UNAVAILABLE).
- [x] **Unsupported capabilities are not fabricated.** `PHASE5_1_SOURCE_INVENTORY.json`
  class 8 explicitly names the two known unsupported-evidence cases
  (`detectable_only_scope` AUC=0.857 mixing artifact; pre-RSS-fix Windows
  OOM evidence) and bars them from ever becoming a label source
  (`PHASE5_1_PUBLICATION_BOUNDARY.md` §2).
- [x] **Every benchmark view has defined inputs/targets; metric
  applicability is defined.** All 8 views in `PHASE5_1_BENCHMARK_VIEWS.md`
  follow the same structure (required fields, labels, input boundary,
  output target, forbidden future information, metrics, valid split, known
  limitations); metrics are matched to task/family per the task brief's own
  metric-compatibility table (e.g. lead-time only applies to prediction,
  not to abstention; recovery-rate only to recovery, not to uncertainty).
- [x] **Public-vs-internal evidence boundaries are defined; schema is
  versioned; provenance is reproducible.** `PHASE5_1_PUBLICATION_BOUNDARY.md`
  classifies every evidence area into 5 categories; `PHASE5_1_SCHEMA.json`'s
  `_versioning_policy` block states the semantic-versioning compatibility
  policy, deprecation policy, and immutable-identifier list;
  `PHASE5_1_PROVENANCE_CONTRACT.md` §4 gives the exact reproducibility
  chain (checksummed run directory → module version constant → git commit).
- [x] **Phase 4 frozen evidence is untouched.** See §3 below for the actual
  `git status`/`git diff --stat` evidence.
- [x] **No model training occurred; no benchmark implementation occurred;
  no upload occurred.** No `python scripts/run_phase4_*` script was
  executed in this session; no `Bash` call in this session invoked any
  training, evaluation, or upload command. Only read-only inspection
  (`Read`, `Grep`) of frozen source files and `git status`/`git diff`
  checks were performed, plus `Write`/`Edit` calls limited to the new
  `experiments/results/phase5_dataset_specification/20260826T053011Z/`
  directory.

## 3. Phase 4 untouched — evidence

`git status --short` scoped to every frozen path named in the task's
absolute rules, captured after all deliverables above were written:

```
A  docs/archive/PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md
A  docs/archive/PHASE4_5_GAP_FIXES_REPORT.md
 M src/phase4/controlled_runtime.py
 M src/phase4/pipeline.py
 M src/phase4/prediction_training.py
?? DOCUMENT_CLEANUP_MANIFEST.md
?? FINAL_PHASE4_CLOSURE_REPORT.md
?? FINAL_SYSTEM_AUDIT.md
?? FINAL_WEAKNESS_REGISTER.md
?? experiments/results/post_p5_remediation/
?? experiments/results/post_p5_remediation_followups/
?? src/phase4/ablations.py
?? src/phase4/agent_calibration.py
?? src/phase4/classification_task.py
?? src/phase4/environments.py
?? src/phase4/gpu_probe.py
?? src/phase4/prediction_eval_v2.py
?? src/phase4/prediction_features_env.py
?? src/phase4/prediction_features_p4_preflight.py
?? src/phase4/prediction_features_v2.py
?? src/phase4/prediction_features_v3.py
?? src/phase4/qa_task.py
?? src/phase4/real_model_runtime.py
?? src/phase4/uncertainty_eval.py
```

**Every one of these lines is pre-existing repository state from before
this session began** — it is byte-identical to the `gitStatus` snapshot
supplied at the start of this task (staged renames, modified
`src/phase4/*` files, and untracked closure-phase artifacts, all already
present prior to any action taken in this session). This session's own
actions consisted exclusively of: (a) `Read`/`Grep` calls (read-only) over
`docs/MASTER_RECORD_CONTENT.md`, `FINAL_PHASE4_CLOSURE_REPORT.md`,
`FINAL_WEAKNESS_REGISTER.md`, `src/phase4/architecture.py`,
`src/phase4/memory.py`, `src/data_foundation/foundation.py`,
`src/phase4/diagnosis.py` (grep only), `src/phase4/environments.py`,
`src/phase4/agent_task.py` (partial), `src/phase4/controlled_runtime.py`
(grep only), `scripts/generate_sha256_manifest.py`; (b) `Bash` calls
limited to `git log`, `git status`, `ls`, `date -u`, `mkdir`, and JSON
validation (`python -c "import json..."`); (c) `Write` calls limited to
the 11 new files under
`experiments/results/phase5_dataset_specification/20260826T053011Z/`. No
`Edit` call was made against any pre-existing file in this session.

## 4. Unresolved schema questions (disclosed, not hidden)

- Whether `record_id` should be a stable hash (chosen here) or an
  incrementing counter is not yet settled against how a future generation
  script will actually be implemented — either satisfies immutability, but
  the choice affects how easily two independent generation runs produce
  identical IDs (a hash does; a counter does not without extra care).
- Whether trained-model artifacts should ever be promoted from
  RESEARCH_ONLY_INTERNAL_ARTIFACT to PUBLIC_DATASET_CONTENT once a
  genuinely validated operating point exists for `resource_unavailable`
  or the OOM ≥2-sample subset is a policy decision this specification
  intentionally defers to a future phase (see
  `PHASE5_1_PUBLICATION_BOUNDARY.md` §4).
- The exact mechanics of the group-based split enforcement
  (`workload_id`-disjointness) when combined with the pre-existing
  seed-block-disjointness discipline have been stated as compatible
  constraints (`PHASE5_1_SPLIT_POLICY.md` §2) but not mechanically proven
  against every historical protocol's actual seed lists — a future
  implementation phase should verify this by direct construction, exactly
  as `SplitSeeds.__post_init__` already does for seed overlap.

## 5. This closure of Phase 5.1

Phase 5.1 (dataset specification and provenance contract) is complete as a
design artifact. It authorizes no dataset construction, no benchmark
implementation, no model training, and no upload — those remain explicitly
future work, gated on this specification being reviewed and, if approved,
followed by a separate implementation phase.
