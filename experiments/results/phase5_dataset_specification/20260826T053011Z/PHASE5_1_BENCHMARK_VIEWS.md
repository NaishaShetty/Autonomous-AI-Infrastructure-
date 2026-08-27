# Phase 5.1 — Benchmark-Ready Views (design only, not implemented)

Each view below is a projection of the canonical schema (`PHASE5_1_SCHEMA.json`)
for one capability. No view is implemented, trained against, or scored in
this phase — this is a design document.

---

## View 1: Agent Uncertainty

- **Required fields**: `agent_output.*` (task-family-specific: `agreement_rate`
  for arithmetic, `softmax_margin` for sentiment, `span_logit_confidence`
  for QA), `agent_output.is_correct`.
- **Labels**: `is_correct` — OBJECTIVE_GROUND_TRUTH.
- **Input boundary**: everything available at `AVAILABLE_AT_DECISION` for
  the agent's own output generation (samples/logits/margins already
  computed); must not include any post-decision retry information.
- **Output target**: a scalar confidence/uncertainty estimate, evaluated
  per task family separately — never pooled across arithmetic/sentiment/QA.
- **Forbidden future information**: `is_correct` itself, any recovery
  action taken after the decision.
- **Metrics**: AUROC, AUPRC, Brier score, ECE, risk-coverage curve —
  applicable to all three families in principle, but discrimination
  results differ sharply by family (arithmetic 0.953/0.636, sentiment
  0.659, QA 0.934 — do not average across families into one number).
- **Valid split**: sample-level `test`, per family, with `calibration_validation`
  reserved for any temperature scaling (sentiment only, per Step 5).
- **Known limitations**: sentiment's 4 candidate estimators are
  mathematically rank-equivalent (all identical AUROC) — a real ceiling,
  not fixable by choosing a different estimator; do not present a 5th
  candidate as a fix without new evidence.

## View 2: Abstention

- **Required fields**: `decision.action` (ABSTAIN vs. ANSWER/RETRY/REVIEW),
  `decision.safety_status`, `agent_output.is_correct` or
  `failure.failure_detected` (whichever the episode's track supplies).
- **Labels**: `is_correct`/`failure_detected` for coverage-conditioned
  accuracy; `decision.action` is itself MODEL_PREDICTION-derived, not
  ground truth.
- **Input boundary**: pre-decision only.
- **Output target**: abstain/act binary decision.
- **Forbidden future information**: outcome after the decision.
- **Metrics**: selective accuracy, coverage, error-at-coverage,
  risk-coverage curves.
- **Valid split**: `test`, thresholds fit on `calibration_validation` only.
- **Known limitations**: abstention behavior under conflicting memory or
  safety-conflicting observation was tested adversarially
  (`experiments/results/generalization/`) at 1.00 correct-abstention rate,
  but this is a small, controlled adversarial matrix, not a
  statistical-generalization claim at scale.

## View 3: Failure Prediction

- **Required fields**: `prediction.score`, `prediction.predictability_status`,
  `failure.failure_class`, `failure.failure_detected`,
  `observations[*]` (pre-failure telemetry only), `identity.environment_id`.
- **Labels**: `failure.failure_detected` (DERIVED_LABEL, per rule 6 of the
  leakage policy).
- **Input boundary**: telemetry strictly before `failure.failure_detected_time`
  (rolling-checkpoint discipline already used by `prediction_training.py`).
- **Output target**: binary/scored risk of eventual failure.
- **Forbidden future information**: any telemetry sample at or after the
  failure event; the diagnosis output; the recovery outcome.
- **Metrics**: precision/recall/F1, false-alarm-rate, specificity,
  lead-time/useful-lead-time (>10ms). AUROC/AUPRC reported alongside, but
  **false-alarm-rate at the calibrated threshold is the deciding metric**
  — an "always fires" pattern (false-alarm-rate≈1.00) must disqualify a
  family from `STRONG_EVIDENCE`/`PLAUSIBLE` regardless of a nominally
  positive AUROC, per the project's own P3-W5 discipline.
- **Valid split**: within-family only, run-level label-shuffled negative
  control, 3+ disjoint seed-range replicates (mirrors Phase 4.8).
- **Per-family status** (must be preserved exactly, not rounded up):
  `resource_unavailable` → STRONG_EVIDENCE (grade A); `oom` ≥2-observability-sample
  subset → real ranking edge but NOT_VALIDATED at the operating point
  (grade C→D, final); `cpu`, pooled `oom`, `flaky` → NOT_VALIDATED, final
  (grade D). None of these may be merged into one aggregate "failure
  prediction: works" claim.

## View 4: Failure Diagnosis

- **Required fields**: `diagnosis.suspected_cause`, `diagnosis.confidence`,
  `diagnosis.causal_status`, `diagnosis.memory_informed`,
  `failure.failure_class` (as the nearest available ground-truth proxy,
  itself not identical to "correct diagnosis").
- **Labels**: no direct ground-truth "correct diagnosis" label currently
  exists in the frozen evidence beyond `failure.failure_class` matching;
  `diagnosis.suspected_cause` remains MODEL_DIAGNOSIS regardless of match
  rate — a high match rate does not promote it to ground truth.
- **Input boundary**: current-run-only evidence
  (`_eligible_current_incident`), optionally memory-informed evidence
  respecting the memory temporal/scope contract.
- **Output target**: suspected_cause classification, with UNKNOWN as a
  valid class.
- **Forbidden future information**: evidence from a later run (leakage
  rule 2), recovery outcome.
- **Metrics**: not extensively re-evaluated as a fresh focus in later
  phases (grade B, "functioning, memory-aware, not a fresh evaluation
  focus" per the master record §22) — a future benchmark should not
  overstate available diagnosis-accuracy evidence beyond this.
- **Valid split**: `test`, with `run_id`-level exclusion enforced as in
  leakage rule 2.
- **Known limitations**: EVALUATION_INCIDENT_001 shows this is an area
  where a subtle current-vs-historical evidence boundary bug can silently
  contaminate results — any reproduction must re-verify the fixed boundary
  is in effect for the source evidence being used.

## View 5: Safe Recovery

- **Required fields**: `recovery.action_type`, `recovery.authorized`,
  `recovery.executed`, `safety.unsafe_authorization`, `validation.validation_status`.
- **Labels**: `validation.validation_status` (OBSERVED_OUTCOME_VALIDATED)
  is the only eligible recovery-outcome label; `recovery.executor_self_report`
  is never a label (leakage rule 8).
- **Input boundary**: the diagnosis/plan available at `PLANNING`/`SAFETY_CHECK`
  states; execution telemetry is post-decision and belongs only to the
  outcome side.
- **Output target**: action selection + binary recovered/not-recovered
  outcome.
- **Forbidden future information**: none beyond the general rule — this
  view's target *is* the post-decision outcome, so its "forbidden future
  information" constraint applies only to what may be fed back as *input*
  to action selection.
- **Metrics**: recovery-rate, failure-to-recovery rate, unnecessary-action
  rate, latency. `unsafe_authorization`/violations tracked as a hard
  zero-tolerance gate metric (not traded off against recovery-rate).
- **Valid split**: `test`; family-specific real-execution comparisons
  (e.g. `RECONFIGURE`-to-free-port 100% vs. `RETRY`-on-contended-port 0%,
  n=40 each, Wilson CIs) should be preserved as their own labeled
  sub-comparison, not pooled across actions.
- **Known limitations**: `GPU_DEVICE_FAILURE` has zero real executable
  recovery actions — this must appear in the view as `NOT_APPLICABLE`, not
  a missing row.

## View 6: Memory / Adaptation

- **Required fields**: `memory_interaction.*`, repeated `workload_id`
  sequences (see split policy §2), `decision.action` before/after a memory
  write for the same `workload_id`.
- **Labels**: whether the planner's chosen action changed after a relevant
  memory write became available — a DERIVED_LABEL from comparing two
  episodes' `decision.action` under the same `workload_id`/`environment_id`/
  `failure_class` scope.
- **Input boundary**: memory reads respecting `at_or_before` and
  `source_run_id != exclude_run_id`.
- **Output target**: action-selection change / success-rate improvement
  across repeated incidents.
- **Forbidden future information**: any memory record whose `recorded_at`
  postdates the querying episode's decision time (leakage rule 5, 9).
- **Metrics**: repeated-incident-improvement, ON-vs-OFF comparison,
  persistence/isolation verification (restart survives, cross-workload
  isolation holds).
- **Valid split**: requires genuinely repeated `workload_id`s across
  distinct `run_id`s — the ONLY evidence source in the frozen record that
  actually exercises this is the Step 6 repeated-incident experiment; the
  larger 300-episode Phase 4.10 run used unique `workload_id`s per episode
  and is NOT valid evidence for this view (§31 of the master record, §6 of
  the split policy) — this exclusion must be stated in the view's own
  documentation whenever this view is instantiated in the future.

## View 7: Cross-Environment Generalization

- **Required fields**: `generalization.fit_environment_id`,
  `generalization.eval_environment_role`, `generalization.zero_shot`,
  `generalization.degradation_from_dev`, plus the underlying
  prediction/uncertainty fields being generalized.
- **Labels**: same as the underlying capability (e.g. `failure.failure_detected`
  for OOM generalization).
- **Input boundary**: same as the underlying capability's pre-decision
  input, now drawn from `held_out`/`robustness` environments.
- **Output target**: same as underlying capability; reported as
  dev→held-out→robustness degradation, not a single blended number.
- **Forbidden future information**: same as underlying capability; plus,
  the `held_out`/`robustness` data must never appear with `zero_shot=false`.
- **Metrics**: held-out performance, degradation magnitude.
- **Valid split**: environment axis (§4 of split policy).
- **Per-family status**: OOM → grade A (AUROC 0.989 dev → 0.983 held-out →
  0.935 robustness, real environment-normalized feature); all other
  families → grade D (not demonstrated, not merely "not yet tried" for
  `resource_unavailable`, which had a real ranking-quality improvement
  that still did not clear the false-alarm-rate bar even combined with
  environment features).

## View 8: End-to-End Autonomy

- **Required fields**: the full episode record across all sub-objects
  (observation → prediction → decision → diagnosis → recovery → safety →
  validation → memory).
- **Labels**: composite; final `episode outcome_class` (RECOVERED /
  NOT_RECOVERED / ABSTAINED / UNKNOWN / COMPLETED).
- **Input boundary**: strictly staged per the `AutonomyState` machine —
  each stage may only consume information available at or before its own
  entry into that state.
- **Output target**: full-loop outcome and whether the loop respected
  every intermediate contract (temporal, safety, memory-scope).
- **Forbidden future information**: any stage consuming a later stage's
  output as if it were available earlier (e.g. `decision` must never
  consume `validation` fields).
- **Metrics**: end-to-end recovery rate, 0-unsafe-action rate (hard gate),
  full-suite reproducibility indicators (test-order independence) as a
  system-health metric alongside the research metrics.
- **Valid split**: `test`, environment axis as applicable.
- **Known limitations**: end-to-end independent-validation coverage is
  grade B ("not adversarially re-tested beyond existing Phase 4.4
  coverage," stated honestly in the Phase 4.10 audit) — a future benchmark
  should not claim this view has been adversarially stress-tested beyond
  that documented scope.
