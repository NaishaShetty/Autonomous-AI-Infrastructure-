# Phase 5.3 — Benchmark Specification (Design Only)

Status: SPECIFICATION ONLY. No benchmark runner, scoring code, or training
code is implemented by this document or its companions. No model is
trained, no threshold tuned, no benchmark data generated, no canonical
dataset modified, nothing uploaded. This specification designs a complete
benchmark over the FROZEN Phase 5.2 canonical dataset
(`experiments/results/phase5_dataset_construction/20260826T054422Z/`,
`dataset_version = phase5.2-dataset-v1.0.0`), itself built against the
FROZEN Phase 5.1 schema
(`experiments/results/phase5_dataset_specification/20260826T053011Z/`,
`schema_version = phase5.1-schema-v1.0.0`).

## 0. Companions

- Machine-readable instance/label shape → `PHASE5_3_BENCHMARK_SCHEMA.json`
- Every task instance definition → `PHASE5_3_TASK_CATALOG.json`
- Every metric's full definition → `PHASE5_3_METRIC_CATALOG.json`
- Split construction rules → `PHASE5_3_SPLIT_POLICY.md`
- Leakage rules → `PHASE5_3_LEAKAGE_POLICY.md`
- Baseline ladder → `PHASE5_3_BASELINE_CATALOG.json`
- Ablation designs → `PHASE5_3_ABLATION_MATRIX.json`
- Honest per-track dataset support → `PHASE5_3_DATASET_COVERAGE.json`
- The five Phase 5.2 limitations, handled explicitly →
  `PHASE5_3_LIMITATIONS.md`
- Future release structure → `PHASE5_3_PUBLICATION_BOUNDARY.md`
- Determinism/versioning requirements → `PHASE5_3_REPRODUCIBILITY_PROTOCOL.md`
- Self-audit → `PHASE5_3_VALIDATION_REPORT.md`
- Overall summary → `PHASE5_3_SYNTHESIS.md`

## 1. Purpose

This benchmark exists to let a skeptical researcher determine whether the
autonomous system actually works — and, symmetrically, to let them prove
it does not, if that is what the evidence shows. Every task, metric, and
baseline in this specification is written so that a NEGATIVE finding is
just as reportable, just as first-class, and just as publishable as a
positive one. Several tracks in this specification (failure_prediction,
memory, generalization) are, by the honest evidence, currently
`NOT_EVALUABLE` or entirely unsupported by the canonical dataset — this is
stated plainly throughout, not softened, because a benchmark that only
reports what looks good is not a benchmark, it is marketing.

## 2. Benchmark vs. dataset — exact instance-derivation rule

A **dataset record** (one line of `all_records.jsonl`, conforming to
`PHASE5_1_SCHEMA.json`) is NOT a benchmark task instance. A **benchmark
task instance** is a task-specific projection:

```
instance = project(record, task_id) = {
    input:   task's decision_time_available_information fields, read from record
    hidden:  task's hidden_information fields, read from record but withheld
             from any system under test until scoring
    label:   the task's ground_truth_definition, computed from record
    split_assignment, environment_role: copied unmodified from record
}
```

- **One record can appear in multiple tracks.** For example, one
  `agent_task`/arithmetic record supplies input to both `UNC-ARITH`
  (uncertainty) and `ABST-ARITH` (abstention) — these are two DIFFERENT
  projections of the SAME record, using different `input`/`hidden` field
  sets and different labels. This is legitimate and does not constitute
  leakage or duplication, because:
  1. The two tasks ask genuinely different scientific questions (does the
     signal discriminate correct/incorrect vs. does a policy over that
     signal reduce selective risk) and are scored with disjoint metric
     sets.
  2. Neither task's `hidden` block ever leaks into the other task's
     `input` block — they are independently derived from the same
     underlying record, not chained.
  3. A model evaluated on both tasks is being asked two different
     questions about the same underlying event, exactly as a single
     exam question can appear, differently framed, on two different exam
     sections — this is not "training on the test set," because no
     fitting happens across the two projections.
- **What would constitute illegitimate duplication** (and is explicitly
  forbidden): using the SAME task's SAME projection of the SAME record in
  two different splits (already prevented at the dataset layer,
  `split_audit.json`, 0 overlaps) or silently re-deriving a second,
  differently-named task that is a trivial relabeling of an existing one
  purely to inflate the reported task count. Every task in
  `PHASE5_3_TASK_CATALOG.json` answers a genuinely distinct scientific
  question (§3 below).

## 3. Design principle applied per task

Every task in `PHASE5_3_TASK_CATALOG.json` answers all 12 required
questions: (1) scientific question, (2) supporting evidence, (3) ground
truth, (4) decision-time-available information, (5) information that must
be hidden, (6) baseline to beat, (7) negative control, (8) success metric,
(9) failure result definition, (10) inconclusive result definition, (11)
unavailable evidence, (12) independent reproducibility. Any task where an
honest answer to one of these is "this cannot currently be answered" is
marked `eligibility_status: LIMITED` or `NOT_EVALUABLE` rather than having
that question silently omitted — see the catalog's `_meta.note`.

## 4. The eight required tracks

Full per-track detail (all fields the brief requires — scientific
question, benchmark input/output, unit of evaluation, label/ground-truth
definitions, evidence available/prohibited, split requirements, metrics,
baseline, negative control, success/failure/inconclusive criteria, minimum
sample, statistical reporting, limitations, dataset coverage, and current
evaluability) lives in `PHASE5_3_TASK_CATALOG.json` (per-task) and
`PHASE5_3_DATASET_COVERAGE.json` (per-track rollup). Summary:

1. **Uncertainty** (`UNC-ARITH`/`UNC-SENT`/`UNC-QA`) — `FULLY_SUPPORTED`.
   Arithmetic self-consistency, sentiment softmax-margin, extractive QA
   span-logit are scored as three SEPARATE tasks with three separate
   AUROC/AUPRC/Brier/ECE/risk-coverage results — never pooled. The
   sentiment finding that temperature-scaling fixes ECE without touching
   AUROC is preserved as a required, explicit report line for `UNC-SENT`,
   never merged into an aggregate "uncertainty works" claim.

2. **Abstention** (`ABST-ARITH`/`ABST-SENT`/`ABST-QA`) — `PARTIALLY_SUPPORTED`.
   ANSWER/REVIEW/ABSTAIN/RETRY are kept as four distinct decision values;
   RETRY is legitimate only for the arithmetic family (extra
   self-consistency sampling), never automatically available for
   sentiment/QA. An always-abstain policy is explicitly disqualified by
   its own baseline definition (`BASE-ALWAYS-ABSTAIN`) requiring joint
   reporting of coverage alongside selective risk.

3. **Failure prediction** (`PRED-RESOURCE-UNAVAILABLE`/`PRED-OOM`/
   `PRED-CPU`/`PRED-FLAKY`) — `UNSUPPORTED_CONTRACT_ONLY` at record level
   in the current dataset (insufficient per-episode sample sizes; the
   headline verdicts are aggregate-only). PREDICTIVE RANKING (AUROC) and
   USABLE OPERATIONAL DETECTION (false-alarm-rate at a calibrated
   threshold) are two distinct, separately-reported axes throughout — an
   "always fires" pattern (false-alarm-rate ~1.0) disqualifies a family
   from any positive operational verdict regardless of AUROC, exactly
   preserving `resource_unavailable`=STRONG_EVIDENCE,
   `oom`(>=2-sample)=real-ranking-but-invalid-operating-point,
   `cpu`/pooled-`oom`/`flaky`=NOT_VALIDATED.

4. **Diagnosis** (`DIAG-EVAL`) — `PARTIALLY_SUPPORTED`. Failure-class
   identification / immediate mechanism / causal hypothesis / causal
   status / confidence / UNKNOWN are kept as distinct fields. Where causal
   ground truth is unavailable, the task reports
   `CAUSAL_GROUND_TRUTH_UNAVAILABLE` and evaluates only the legitimately-
   groundtruthed aspects (failure-class accuracy, evidence correctness,
   temporal integrity, contradiction handling, UNKNOWN handling,
   unsupported-cause rate where measurable). A system correctly emitting
   UNKNOWN is rewarded, never penalized, by `MET-UNKNOWN-HANDLING`.

5. **Recovery** (`REC-EVAL`) — `PARTIALLY_SUPPORTED`. ACTION SELECTED /
   ACTION EXECUTED / ACTION SUCCEEDED / ACTION INDEPENDENTLY VALIDATED are
   four distinct fields, never collapsed; `validation.validation_status`
   (OBSERVED_OUTCOME_VALIDATED) is the only eligible ground truth, never
   `recovery.executor_self_report`. A 0% recovery rate on a genuinely
   unfixable deterministic failure (e.g. `GPU_DEVICE_FAILURE`, which has
   zero real executable recovery actions) is explicitly `NOT_APPLICABLE`,
   not a bad result.

6. **Memory** (`MEM-EVAL`) — `UNSUPPORTED_CONTRACT_ONLY`. Memory exists /
   memory retrieved / memory influences decision / memory improves outcome
   are four separate claims with four separate metrics
   (`MET-MEMORY-RETRIEVAL-PRECISION`, decision-change rate, adaptation
   rate, recovery-improvement). The current canonical dataset has
   essentially no repeated-`workload_id` structure (3,104 workloads across
   3,106 episodes) — this task is a CONTRACT for future data, not a
   currently-scoreable benchmark, and is stated as such rather than
   quietly run on an unrepresentative handful of coincidental repeats.
   Cross-workload/cross-environment semantic-similarity-only retrieval is
   explicitly disqualifying.

7. **Generalization** (`GEN-RANKING-CONTRACT`/`GEN-OPERATING-POINT-CONTRACT`)
   — `UNSUPPORTED_CONTRACT_ONLY`, stated plainly: the current canonical
   dataset has only ONE represented environment
   (`identity.environment_id == UNSPECIFIED_PRE_4_9` for all 3,106
   records). A full environment-generalization benchmark is NOT
   EVALUABLE from it today. This specification instead defines the
   CONTRACT for a future/derived environment-aware evaluation, using
   Phase 4's actual three environments
   (`baseline_cpu`/`memory_constrained`/`dependency_network_constrained`),
   with held-out environments never usable for fitting. RANKING
   GENERALIZATION and OPERATING-POINT GENERALIZATION are two distinct
   metrics (`MET-RANKING-GENERALIZATION-DEGRADATION`,
   `MET-OPERATING-POINT-GENERALIZATION`), never collapsed — preserving the
   OOM finding that AUROC transferred 0.989->0.983->0.935 while the fixed
   decision threshold did not transfer cleanly.

8. **End-to-end** (`E2E-EVAL`) — `PARTIALLY_SUPPORTED` (n=46 controlled_
   runtime records; agent_task records do not exercise the full loop).
   Both component metrics (per-track, above) AND end-to-end metrics
   (`MET-END-TO-END-RECOVERY-RATE`, `MET-END-TO-END-UNSAFE-ACTION-RATE`)
   are required together, specifically so a strong recovery subsystem
   cannot mask a disqualified predictor, and good calibration cannot mask
   an unsafe recovery action — this joint-reporting requirement is
   `MET-END-TO-END-RECOVERY-RATE`'s own stated `forbidden_standalone_use`.

## 5. Baseline ladder

Ten baselines, each with a scientific justification tied to a specific
question it answers, are defined in `PHASE5_3_BASELINE_CATALOG.json`:
`BASE-RANDOM`, `BASE-ALWAYS-ANSWER`, `BASE-ALWAYS-ABSTAIN`,
`BASE-GENERIC-POLICY`, `BASE-CALIBRATED-MECHANISM-AWARE`,
`BASE-SIMPLE-STATISTICAL-PREDICTOR`, `BASE-NO-MEMORY-CONTROL`,
`BASE-NO-RETRY-CONTROL`, `BASE-PREDICTOR-DISABLED-CONTROL`,
`BASE-RAW-CONFIDENCE`. None is included arbitrarily; each maps to at least
one track where it is the specific floor, ceiling, or degenerate-policy
check that track's design principle requires.

## 6. Ablations

Five ablations are defined in `PHASE5_3_ABLATION_MATRIX.json`:
uncertainty-mechanism ON/OFF, calibrated-vs-generic policy, memory ON/OFF,
retry ON/OFF, predictor ON/OFF. Each states its
`causal_vs_correlational_status` explicitly. Two findings are preserved
exactly as the frozen evidence states them, not smoothed over:
- **Retry ON/OFF is genuinely causal** — disabling retry removed the WHOLE
  observed improvement (`docs/MASTER_RECORD_CONTENT.md` line ~651).
- **Predictor ON/OFF is confounded, disclosed as such** — little
  difference was observed in one sample specifically because retry alone
  was already highly effective; this is a SPECIFIC, DISCLOSED confound,
  never generalized into "the predictor doesn't matter."

## 7. Metric catalog

33 metrics are fully defined in `PHASE5_3_METRIC_CATALOG.json`, each with
mathematical definition, unit, interpretation, failure mode, minimum-sample
considerations, direction, and known pathological cases. Four standalone
uses are explicitly forbidden project-wide: F1 alone for imbalanced
prediction; AUROC alone for operational-readiness claims; accuracy alone
for abstention safety; executor-self-report alone for recovery success.

## 8. Statistical reporting

- Confidence intervals (bootstrap, seeded) are required for every ranking
  metric (AUROC/AUPRC); Wilson intervals for every proportion (recall,
  precision, false-alarm-rate, recovery-rate, coverage).
- Replicate means/std are required wherever the underlying evidence
  supports multiple disjoint seed-range replicates (mirroring Phase 4.8's
  3-replicate, 2,400-seed design where that specific design is being
  reused; the current Phase 5.2 dataset's own replicate structure is
  whatever `split_assignment_manifest.json` actually encodes, not
  invented).
- Any task/track below its own `minimum_sample_requirement` (per
  `PHASE5_3_TASK_CATALOG.json`) MUST be labeled
  `UNDERPOWERED/DESCRIPTIVE ONLY` in any report, never presented as a
  statistically significant finding. This applies today to essentially all
  of `failure_prediction`, `memory`, `DIAG-EVAL`'s per-failure-class
  breakdowns (most classes have n<30, one has n=1), and any
  `generalization` result (n=0 non-`UNSPECIFIED_PRE_4_9` records).

## 9. Leakage rules

Twelve explicit rules (a superset that also restates and specializes
`PHASE5_1_LEAKAGE_POLICY.md`'s 14 dataset-level rules for the benchmark-
instance-derivation layer) are given in `PHASE5_3_LEAKAGE_POLICY.md`,
covering: no future observations; no post-failure evidence for pre-failure
prediction; no recovery outcome as recovery-selection input; no diagnosis
output as ground truth; no executor self-report as validation; no test
labels during fitting; no held-out environment outcomes during fitting; no
repeated-workload crossing forbidden splits; no memory record written
after the evaluated decision; no cross-generation evidence contamination;
no benchmark-specific threshold tuning on test data; no feature selection
based on final test results.

## 10. The five Phase 5.2 limitations

Handled individually, in full, in `PHASE5_3_LIMITATIONS.md` — not
summarized further here to avoid duplicating that document.

## 11. Task granularity

The evaluation unit is stated per task, not assumed universally:
`one_agent_output` (uncertainty, abstention), `one_prediction_checkpoint`
(failure prediction — currently meaning the single retained end-of-episode
checkpoint, per Limitation 1), `one_decision` (abstention policy
simulation), `one_failure_episode` (diagnosis), `one_recovery_episode`
(recovery), `one_repeated_incident_sequence` (memory, currently
unsupported), `one_full_autonomy_loop` (end-to-end). See
`PHASE5_3_BENCHMARK_SCHEMA.json`'s `EvaluationUnit` enum and each task's
own `evaluation_unit` field.

## 12. Splits, versioning, reproducibility, publication boundary

Given their own full companion documents (§0 above); this section is
deliberately non-duplicative per the same discipline Phase 5.1 used for
itself.

## 13. Honesty statement

This specification's own honest self-assessment, if the described system
were scored against it today: **uncertainty** would score well and
differentiated by family; **abstention** could only be evaluated as a
simulated policy, not a real one; **failure prediction** would return
mostly `NOT_EVALUABLE` at the record level, with the aggregate evidence it
references showing genuine but narrow success (`resource_unavailable`)
alongside three disqualified families; **diagnosis** and **recovery**
would produce small-sample, partially-supported results; **memory** and
**generalization** would return `NOT_EVALUABLE` outright; **end-to-end**
would be limited to n=46. This is not a flaw in this specification — it is
the specification doing its job of refusing to manufacture a flattering
result where the evidence does not support one.
