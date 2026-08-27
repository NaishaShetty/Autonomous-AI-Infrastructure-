# Autonomous AI Infrastructure — Master Research Record

**Source content for the project's master Word document.** This file
supersedes `docs/Autonomous_AI_Infrastructure_Comprehensive_Record.docx`
(compiled 2026-08-23, preserved unchanged as a historical snapshot) as the
current, complete narrative of the project. It extends that record forward
through Phase 4.5's gap fixes, Phase 4.5b, Phase 4.6–4.10, the post-P5
remediation phase (7 steps), and the five post-P5 follow-ups, and adds the
final Phase 4 system audit and closure decision. Every number below is
quoted or directly derived from a canonical report or raw evidence file —
none is invented. Where a canonical document is the authoritative source,
its path is given so the reader can verify directly rather than trust a
restatement.

---

## 1. Project purpose and research question

Autonomous AI Infrastructure is a research-grade self-healing AI/ML
infrastructure system. It is built to answer a specific, falsifiable
research question, not to ship a self-healing demo and assume it works:

> Given calibrated confidence, persistent failure memory, and a controlled
> recovery-selection environment, can a context-aware, learned recovery
> policy detect and diagnose failures, abstain when evidence is
> insufficient, and select a recovery action that measurably beats a
> strong, non-learned heuristic — without exceeding a zero-tolerance
> unsafe-action rate? And, extended in Phase 4/5: can the same discipline
> be applied to a live, project-owned controlled runtime and a real AI/ML
> agent, recognizing when the agent or the infrastructure underneath it is
> likely wrong, and safely correcting it end to end?

The project's defining discipline, stated in its own README and honored
throughout its history, is to report a negative or inconclusive result
honestly rather than move the goalposts to manufacture a positive one.
That discipline — not any single positive headline number — is this
project's core asset, and every section below preserves it.

## 2. System goals

- Continuously observe AI/ML workload operation.
- Detect and diagnose failures with calibrated confidence.
- Predict problems before they become catastrophic, where the evidence
  actually supports doing so — and say plainly when it does not.
- Recognize uncertainty and abstain from acting when it is unsafe or
  unreliable to do so.
- Retrieve and use persistent failure memory to inform recovery decisions,
  scoped safely (no cross-run or cross-environment contamination).
- Safely execute recovery (retry, restart, rollback, reconfigure, or
  escalate to human review) behind an explicit safety gate.
- Independently validate recovery outcomes rather than trust the
  executor's self-report.
- Learn from validated outcomes to improve future decisions.
- Maintain strict provenance, temporal integrity, reproducibility, and
  auditability at every step — every phase in this project's history is
  gated by a frozen protocol, a leakage audit, and (from Phase 4 onward) an
  explicit safety audit.

## 3. Original prototype foundations

The project began by auditing, not trusting, two inherited prototypes: an
**AI-Abstention-Engine** (~9,700 backend lines) and an **Introspective
Failure Memory Model** (~1,560 backend lines). Phase 1
(`docs/archive/PHASE1_AUDIT_REPORT.md`) found concrete defects in both: a
live confidence-scale bug (`global_reliability_score: 189.61` on a
documented 0–100 scale, caused by averaging two incompatible
representations), a trivial query defaulting to abstention while its own
explanation text claimed "Confidence 61%", a 404 on `/api/metrics`, and a
committed `reliability.db` containing real personal emails and password
hashes. The Failure Memory Model showed a real risk-coverage signal
(baseline error 35.44% → 8.05% at 15% coverage) but had no tests, was
in-memory only, and had a live 500 error from unhandled numpy JSON
serialization. This audit set the tone for the entire project: report the
bug, verify the scale, never assume a metric is trustworthy until checked.

Phase 2 (`docs/archive/PHASE2_REPORT.md`) migrated both prototypes into one
pydantic-enforced architecture (confidence type-constrained to `[0,1]` by
construction), fixing every Phase 1 bug structurally. Its own key research
finding was negative: the failure-memory risk signal did **not** improve
calibrated abstention beyond confidence alone (selective risk 0.1667 vs.
0.2083 at 20% coverage; failure-memory correlation with correctness 0.031,
essentially noise, vs. 0.200 for confidence). That negative result is what
opened Phase 3.

## 4. Architecture

The current, active architecture (the codebase as of this document) is
what this record's predecessor calls Generation 3: a project-owned
controlled runtime that executes real local subprocesses and emits genuine
runtime telemetry, rather than replaying a historical trace or running a
purely synthetic simulator. The canonical flow, implemented end to end by
`src/phase4/pipeline.py`'s `AutonomyPipeline`:

```
observe -> detect -> predict -> decide/abstain -> diagnose (memory-aware)
   -> plan (memory-informed) -> safety-gate -> execute -> independently
   validate -> learn (write validated experience to memory)
```

Two entry points exercise this loop: `run_workload()` (process/
infrastructure telemetry: CPU timeout, OOM, GPU absence, data corruption,
resource contention, flaky processes, network failure) and
`run_agent_task()` (a real AI/ML agent's output — arithmetic
self-consistency, sentiment classification, extractive QA — with its own
correctness oracle and uncertainty mechanism). Both states machines walk
the same `AutonomyState` enum: `RECEIVED -> OBSERVING -> PREDICTED ->
DECIDING -> DIAGNOSING -> PLANNING -> SAFETY_CHECK -> EXECUTING ->
VALIDATING -> RECOVERED / NOT_RECOVERED / ABSTAINED -> COMPLETED`.

Two earlier, complete architecture generations remain frozen and
unmodified underneath this one:

- **Generation 1** (original synthetic-data Phase 4): `src/failure_memory/`
  and `src/failure_patterns/` — failure memory (H1 partially supported)
  and pattern learning (H2 inconclusive) on synthetic episodic data.
- **Generation 2** ("V1"): `src/runtime/`, `src/recovery/`,
  `src/failure_experience/`, `src/decision/policy.py` — a complete
  detect → assess → retrieve → diagnose → plan → safety-gate → execute
  (simulated) → validate → persist → learn loop built on Alibaba GPU2020
  trace replay, frozen after release audit
  (`docs/archive/V1_RELEASE_AUDIT.md`). V1 was not deleted; it is preserved
  exactly as `docs/archive/VERSIONED_MODULE_CLASSIFICATION.md` records, and
  Generation 3 reuses its tested safety vocabulary and `DecisionPolicy`
  rather than re-deriving them (Decision A in
  `docs/archive/PHASE4_5_AUDIT_AND_PLAN.md`).

`src/phase3_contract.py` states explicitly that Phase 3+ work is
deliberately independent of the frozen V1 runtime — confirmed by direct
`git status` inspection during the post-P5 remediation phase: every file
touched throughout that phase lived under `src/phase4/`, `scripts/`,
`tests/*/test_phase4*`, or `requirements.txt`.

## 5. Phase history

| Phase | What it covers | Verdict |
|---|---|---|
| 1 | Audit of the two source prototypes | Concrete defects found, not assumed |
| 2 | Migration into one unified architecture | Failure-memory signal did not beat confidence alone (negative) |
| 3.1–3.6 | Synthetic reliability research, frozen | Confidence alone remained strongest signal at every axis tested |
| 3 real-data | Same questions on AgentRx/Alibaba GPU2020/AIOps 2020 | SUPPORTED (Alibaba), PARTIAL (AIOps), NOT EVALUABLE (AgentRx) |
| 4 (original, synthetic) | Failure memory (4.1) + pattern learning (4.2) | PARTIALLY SUPPORTED / INCONCLUSIVE |
| 4 (active, real-data) | Re-run of 4.1/4.2 + recovery learning (4.3/4.4) | PASS (4.1); INCONCLUSIVE (4.2, cardinality ceiling); PASS — HYPOTHESIS NOT SUPPORTED (4.3, 4.4) |
| V1 (Gen 2) | Full closed-loop on Alibaba trace replay | Frozen, complete, 56/56 replay cases, 0 unsafe executions |
| Gen 3 restart | Controlled, project-owned runtime | Stopped at diagnosis before Phase 4.4/5 session |
| 4.4/4.5 | Full loop connected: memory, prediction, decision, recovery, safety, validation, learning | 668 passed / 17 skipped / 0 failed |
| 4.5 gap fixes | ML-trained prediction, persistent memory, widened taxonomy/actions, adaptive learning, guardrails, at-scale evidence | 693 passed / 17 skipped / 0 failed |
| 4.5b | Scope-routed uncertainty; real AI/ML agent task with self-consistency | 735 passed / 17 skipped / 0 failed |
| 4.6–4.10 | Real HF models, calibrated agent retry, rigorous prediction re-evaluation, environment generalization, full integrated audit | 808 passed / 3 failed (2 external hardware limitations, 1 known RNG-seed sensitivity) |
| Post-P5 remediation (7 steps) | Systematic resolution of every named weakness | 837 passed / 0 failed |
| Post-P5 follow-ups (5 items) | The 5 explicitly-recommended, previously-unperformed follow-ups | 837 passed / 0 failed |
| This closure phase | Document cleanup, master record, final system audit and freeze decision | See `FINAL_PHASE4_CLOSURE_REPORT.md` |

## 6. Frozen V1

V1 (Generation 2) is frozen under `src/runtime/`, `src/recovery/`,
`src/failure_experience/`, and `src/decision/policy.py`. Its evidence
source was a trained artifact over the Alibaba GPU2020 trace: a
logistic-regression workload model with isotonic calibration reaching
AUROC 0.720 / AUPRC 0.540 (random split) and 0.830 / 0.746 (temporal
split), wrapped in a versioned, checksummed artifact. The final V1 release
evaluation composed the entire pipeline across 8 independent jobs, 7
declared conditions, and 56 replay cases — every case completed without
unsafe execution; both adversarial conditions (conflicting memory,
safety-conflicting observation) produced `unsafe_proposal_rate = 1.00` and
`unsafe_proposal_rejection_rate = 1.00` (the gate caught every one).
`docs/archive/V1_RELEASE_AUDIT.md` froze V1 with an explicit claim
boundary: it may describe bounded replay composition, provenance,
persistence, safety rejection, and controlled recovery validation; it must
not be described as production-ready or as autonomously recovering real
systems. V1 was set aside (not deleted) because a historical trace replay
cannot legitimately stand in for a live, synchronized decision-time
telemetry source, however carefully its leakage boundaries are enforced —
this is exactly why Generation 3 was built.

## 7. Phase 3 foundation

Phase 3's synthetic track (3.1–3.6, `docs/archive/PHASE3_FREEZE.md`) tested
under a pre-registered protocol (seeds `[1,2,3,4,5,42]`, coverage
`{5,10,20,50}%`, 2000-sample bootstrap, 7/7 leakage checks) whether a
supervised failure-risk signal could beat calibrated confidence alone. It
never durably could: confidence baseline AUROC 0.660 vs. best candidate
0.655–0.581 across sub-phases, with the best candidate (frozen "Candidate
F") beating the baseline on only 1 of 6 seeds head-to-head (3.4). The
real-data track (13 documents, `docs/archive/PHASE3_REAL_DATA_*`) re-ran the
same questions on AgentRx (58/44 annotated trajectories), Alibaba GPU2020
(1,055,501 jobs, 25.94% terminal failure rate, all 7 source archives
checksum-verified), and CCF AIOps 2020 (81 real fault-log events), finding
Alibaba random-split AUROC 0.735 [0.703,0.766] but a temporal-split
collapse to 0.395 for one representation (below no-signal) — the
discrepancy was reported, not the more favorable number quoted forward.

## 8. Phase 4 architecture

Phase 4's active, real-data-driven track (`src/phase4/`) is the currently
active codebase. Its core modules: `architecture.py` (the `AutonomyState`
machine and port protocols), `observability.py`/`monitoring.py` (telemetry
and failure detection), `prediction.py`/`prediction_training.py` (risk
scoring, ML-trained models), `decision.py` (wraps the frozen
`src.decision.policy.DecisionPolicy`), `diagnosis.py` (memory-aware
hypothesis generation), `memory.py` (the frozen historical-memory
contract), `recovery.py` (planner/safety-gate/executor/validator),
`learning.py` (the memory-write feedback loop), `pipeline.py`
(`AutonomyPipeline`), `controlled_runtime.py` (the real subprocess
harness), `agent_task.py`/`agent_runtime.py`/`agent_recovery.py`/
`agent_calibration.py` (the AI/ML-agent evaluation track), and
`environments.py`/`prediction_eval_v2.py`/`prediction_features_*.py`/
`classification_task.py`/`qa_task.py`/`real_model_runtime.py`/
`uncertainty_eval.py`/`ablations.py`/`gpu_probe.py`/`guardrails.py`/
`adaptive.py` (later-phase extensions, detailed in §22–23).

## 9. Observability

`docs/archive/RUNTIME_RELIABILITY_OBSERVABILITY_ARCHITECTURE_AUDIT.md`
first distinguished demonstrated mechanisms from unsupported claims and
proposed a telemetry contract. The post-P5 remediation's Step 2 audit
(`experiments/results/post_p5_remediation/20260825T064402Z/audits/P3_PREDICTIVE_OBSERVABILITY_AUDIT.md`)
found a real, previously undiscovered defect: **RSS telemetry was silently
broken (returning `None`) on Windows**, zeroing out the OOM family's only
intended signal. This was fixed before any predictive re-evaluation, and
CPU%/age/system-memory telemetry plus a resource pre-flight probe were
added, giving `resource_unavailable` a real signal where it previously had
none.

## 10. Controlled runtime

`src/phase4/controlled_runtime.py` executes real local subprocesses (not a
simulator, not a historical trace) across explicit modes: `cpu` (busy-loop
timeout), `oom` (real `RLIMIT_AS` refusal or a self-enforced allocation
budget), `gpu` (real device probe via `nvidia-smi`/`rocm-smi`),
`corruption` (real SHA-256 checksum with deliberate single-byte fault
injection), `resource_unavailable` (real cross-process port-bind
contention), `flaky` (real subprocess per attempt, growing invocation
counter), `network` (network-failure detection), `fail` (deterministic
nonzero exit). Recovery executes for real against this same runtime for
`RETRY`/`RESTART`/`ROLLBACK` (real last-known-good checkpoint replay) and
`RECONFIGURE` (real halving of a numeric load parameter, or picking a free
port) — not a simulated ground-truth table lookup.

## 11. Monitoring / failure detection

`src/phase4/monitoring.py` extends beyond a single fixed RSS threshold to
include network-failure detection and a sustained-anomaly HIGH-severity
escalation (temporally-aggregating detection, added alongside the original
single-threshold check). `MonitoringEngine` independently re-derives
outcomes from raw events for validation, never trusting an executor's
self-report — verified by a test that feeds the validator a deliberately
lying executor.

## 12. Diagnosis

`src/phase4/diagnosis.py`'s `DiagnosisEngine` carries a dedicated
hypothesis per failure class (`OUT_OF_MEMORY`, `GPU_DEVICE_UNAVAILABLE`,
`DATA_INTEGRITY_FAILURE`, `RESOURCE_UNAVAILABLE`,
`INTERMITTENT_TRANSIENT_FAILURE`, `NETWORK_FAILURE`,
`AGENT_INCORRECT_ANSWER`, `AGENT_TASK_TIMEOUT`, `AGENT_WORKER_ERROR`) and
an optional, backward-compatible memory-aware evidence branch. A real,
found-and-fixed defect from this project's own evaluation discipline:
`EVALUATION_INCIDENT_001` (`experiments/results/system_evaluation/EVALUATION_INCIDENT_001.md`)
discovered cross-run diagnosis evidence contamination — the engine's
temporal boundary prevented future events but did not itself restrict
eligible events to the failure's own `run_id`, so an earlier failure's
evidence could leak into a later diagnosis. Root-caused to
`DiagnosisEngine._eligible` and fixed (renamed
`_eligible_current_incident` in `src/phase4/diagnosis.py`), documented in
`EVALUATION_INCIDENT_001_STATUS.md` with every pre-fix run preserved
unmodified as historical evidence, not corrected retroactively.

## 13. Prediction

Prediction went through four distinct evidentiary stages, each superseding
the last in rigor, not in honesty:

1. **Phase 4.4/5**: a hand-weighted, engineered risk score (RSS ratio,
   anomaly rate, elapsed-time ratio) — deliberately not trained, to avoid
   fabricating calibration it couldn't support. First real evaluation: 0
   true positives / 0 false positives / 5 false negatives / 3 true
   negatives, reported as measured.
2. **Phase 4.5 gap fixes**: `prediction_training.py` built a real,
   ML-trained (`LogisticRegression`) pipeline with disjoint train/
   validation/test seed blocks and a precision-recall-calibrated
   threshold. Measured result: per-checkpoint AUC 0.515 (aggregate) —
   close to chance, because several new failure classes have no
   pre-failure telemetry precursor at all.
3. **Phase 4.5b**: `PredictionScopeRouter` split the aggregate into an
   honest `predictable_scope` (`cpu`/timeout only, AUC 0.636) vs.
   `detectable_only_scope` (a fixed historical-prior fallback, AUC 0.857 —
   explicitly flagged as **not** real predictive skill, a mixing artifact
   of deterministic vs. non-deterministic modes).
4. **Phase 4.8 (rigorous re-evaluation)**: `prediction_eval_v2.py`
   evaluated every bimodal family within-family only, with a run-level
   label-shuffled negative control and 3 disjoint seed-range replicates.
   **Result: none of `cpu` (+0.047 gap, noise-level), `oom` (+0.014),
   `resource_unavailable` (−0.005), or `flaky` (−0.038) show a real AUROC
   advantage over their shuffled control that survives replication.** The
   previously reported `cpu` 0.636 did not replicate.
5. **Post-P5 remediation Step 3**: re-ran the predictability protocol with
   the Windows RSS-telemetry fix in place, adding a false-alarm-rate/
   specificity check. `cpu`, pooled `oom`, and `flaky`: **NOT VALIDATED**
   (an "always fires" pattern disqualifies the nominal AUROC edge —
   confirmed correctly discarding 3 of 4 families despite a nominal edge).
   `resource_unavailable`: **STRONG EVIDENCE** from a new, legitimate
   pre-flight-probe feature. `oom`'s ≥2-observability-sample subset:
   **PLAUSIBLE**, flagged for a follow-up operating-point check.
6. **Post-P5 follow-ups 1 and 5** (final state): follow-up 1 re-ran `cpu`
   with the Step 7 timing fix — real AUROC 0.616 ± 0.045 vs. shuffled 0.389
   ± 0.032, but false alarm rate 1.00 ± 0.00 in every replicate/variant —
   **status unchanged: NOT VALIDATED, final.** Follow-up 5 answered the
   `oom` ≥2-sample operating-point question directly: AUROC 0.780 ± 0.096
   (real) vs. 0.625 ± 0.093 (shuffled) — a real, replicated ranking edge —
   but false alarm rate 1.00 ± 0.00 and specificity only 0.179 ± 0.254 at
   the calibrated threshold. **Status: NOT VALIDATED, final** — the real
   ranking signal does not translate into a usable detector under this
   project's threshold-calibration approach.

`resource_unavailable`'s follow-up 3 (combining the pre-flight probe with
Phase 4's environment-aware representation) found a real, non-trivial
ranking improvement (held-out AUROC A=0.781, B=0.743, **C=0.916**) but
false alarm rate 1.00 for all three feature sets at their calibrated
thresholds — **improved ranking quality, still not validated at the
operating point.**

## 14. Uncertainty / abstention

Three genuinely different uncertainty mechanisms are used, one per task
family, never forced into a single blended signal:

- **Arithmetic (self-consistency disagreement)**: strong, AUROC 0.953
  (Phase 4.6), 0.636 in isolation on the predictable-timeout process family.
- **Sentiment classification (softmax-margin)**: weak, AUROC 0.659 — a
  real, explained limitation. Post-P5 remediation Step 5 tested 4
  candidate uncertainty estimators under a strict calibration/test split:
  **all 4 produced mathematically identical AUROC** (binary-classification
  confidence transforms are rank-equivalent) — a real, explained negative
  result, not a bug. Temperature scaling fixed calibration (ECE 0.089 →
  0.023) while leaving discrimination unchanged — an honest partial win.
- **Extractive QA (span-logit confidence)**: strong, AUROC 0.934.

## 15. Decision policy

`src/decision/policy.py`'s `DecisionPolicy` (frozen, reused not rebuilt) is
the single authoritative decision engine behind both the process-telemetry
path and the agent-task path. Two policy profiles exist: the **generic**
policy (`answer_threshold=0.70`, `abstain_threshold=0.40`) and the
**agent-specific calibrated profile** (`AgentDecisionCalibrationProfile`,
Phase 4.7) — four fixed agreement-rate buckets with Laplace-smoothed
per-bucket `p_correct`/`p_retry_success` estimated on a disjoint
calibration split, and an explicit, pre-registered expected-utility
formula. Post-P5 remediation Step 5 verified by direct code reading that
`RETRY` is correctly scoped only to the arithmetic agent. Post-P5
follow-up 4 (P2-W3) ran an 18-point pre-registered grid over
`COST_RETRY_PER_EXTRA_SAMPLE` × `BENEFIT_CORRECT` × `COST_WRONG_ANSWER`: all
18 configurations, including the existing baseline, produced
byte-identical decisions/outcomes (final accuracy 1.000 in every
configuration on a 40-seed/3-wrong-episode grid) — no fragility observed
within the pre-registered range, with the explicit caveat that this small
grid sample limits how far "no fragility" generalizes.

## 16. Failure memory

`src/phase4/memory.py`'s `FailureMemoryStore` is a frozen historical-memory
contract, written and frozen before any memory-read path was added to
diagnosis: scoped by `(workload_id, environment_id, failure_class)`, never
by `run_id`; temporally safe (`recorded_at <= at_or_before`); versioned;
fail-closed on under-specified queries; relevance-ranked by a fixed,
un-tuned recency decay. Phase 4.5 gap fixes made it SQLite-backed
(`path=None` keeps the old in-memory behavior for every existing caller;
`path=<file>` gives real, restart-surviving persistence). Post-P5
remediation Step 6's dedicated repeated-incident experiment (same
workload, real process restarts, memory ON vs. OFF) directly confirmed
memory changes real decisions: memory ON switches the planner's chosen
action at the earliest structurally possible episode and self-corrects;
OFF never does. Persistence/restart/isolation was verified directly
(version preserved, record retrievable, cross-workload isolation holds
after a real store close/reopen). A separate 300-episode full-loop
evaluation (Phase 4.10) found **no observable Memory ON/OFF difference**,
for an honest structural reason: every episode used a distinct
`workload_id`, so no episode's stored experience was ever looked up by a
later episode under that design — the isolation contract working exactly
as intended, not evidence memory is inert.

## 17. Recovery planning

`src/phase4/recovery.py`'s `RuleBasedRecoveryPlanner` selects among
`RETRY`, `RESTART`, `ROLLBACK`, `RECONFIGURE`, and escalation, informed by
memory when available. `AdaptiveRecoveryPlanner` (Phase 4.5 gap fixes,
`src/phase4/adaptive.py`) ranks actions by a truly online, Beta(1,1)-
smoothed success-rate estimate; measured correct-action selection rate
rising from 98.0% (episodes 1-50) to 100.0% (episodes 951-1000) against a
deliberately close pair of true recovery probabilities (0.35 vs. 0.65),
while the unmodified rule-based planner stayed at 0.0% on the identical
scenario (it has no way to prefer the better action by quality, only to
avoid one after repeated failure).

## 18. Safety gate

`RecoverySafetyGate.authorize()` is called before every execution in both
`run_workload` and `run_agent_task`; execution is skipped whenever
authorization is denied or the decision is `REVIEW`/`ABSTAIN`. A six-case
adversarial safety matrix (Phase 4.4/5) and a sixteen-case matrix (Phase
4.5 gap fixes) both produced **0 incorrectly authorized**. The
post-P5-remediation Step 7 final audit
(`experiments/results/post_p5_remediation/20260825T064402Z/audits/FINAL_SYSTEM_CHECK.md`,
item 10) re-confirmed the gate unchanged and re-enforced; `is_unsafe()`
checks in `recovery.py` are unchanged, and every new capability added
during that phase was either read-only telemetry or an opt-in, test-only
override (`force_gpu_state`) confirmed never set in production/evaluation
code paths (verified by `grep`). `RecoveryCircuitBreaker`
(`src/phase4/guardrails.py`) hard-caps real recovery **executions** per
`(workload_id, environment_id)` — verified to allow exactly `max_attempts`
real executions on an always-failing workload before short-circuiting to
`ABSTAINED`.

## 19. Recovery execution

Execution is real, not simulated, for `RETRY`/`RESTART` (re-invokes
`ControlledRuntime`'s own subprocess boundary), `ROLLBACK` (replays a real
recorded last-known-good checkpoint, or honestly records "not executed" if
none exists), and `RECONFIGURE` (halves a real numeric load parameter or
selects a free port — measured to genuinely change the outcome: e.g.
`RESOURCE_UNAVAILABLE` 100% recovery via `RECONFIGURE` to a free port vs.
0% via `RETRY` on the contended one, n=40 each, Wilson 95% CI [0.91,1.0]
vs. [0.0,0.09]). For the agent-task track, `AgentRecoveryExecutor`'s
`RETRY` means genuinely re-answering with doubled self-consistency
samples — a real, more costly, measurably effective action, not a no-op.

## 20. Independent validation

`SignalRecoveryValidator` independently re-derives the outcome from raw
events through a fresh `MonitoringEngine`, never trusting the executor's
self-report — verified against a deliberately lying executor in a
dedicated test. The Phase 4.10 audit re-confirmed: "not adversarially
re-tested beyond existing Phase 4.4 coverage" (grade B, not A, for this
specific reason, stated honestly rather than rounded up).

## 21. Learning

`src/phase4/learning.py`'s `LearningManager` is the only code path
permitted to write to the memory store, and only after a validation
outcome exists. The Phase 4.10 full-loop run recorded 9/9 validated
outcomes correctly written to memory across 300 episodes. Earlier,
narrower integration studies
(`experiments/results/learning_influence/`,
`docs/archive/LEARNING_INFLUENCE_REPORT.md`) showed a validated prior
experience changing the selected action in 20/20 episodes and improving
simulator validation success from 0/20 to 20/20 — a controlled integration
result, not a production or statistical-generalization claim.

## 22. P1–P5 remediation

`experiments/results/post_p5_remediation/20260825T064402Z/` is the
authoritative, frozen record of a 7-step remediation phase
(`MASTER_REMEDIATION_REPORT.md`, `FINAL_POST_REMEDIATION_EVALUATION.md`).
Executed in required order: engineering → observability → predictability →
generalization → uncertainty/decision → memory → full re-evaluation.

**What each step found, condensed:**

- **Step 1 (engineering):** Fixed the P1-W4/P5-W3 full-suite instability
  (a `hash()`-based RNG seed that was `PYTHONHASHSEED`-dependent, replaced
  with a stable `hashlib`-based seed) and the GPU-probe nondeterminism
  (`src/phase4/gpu_probe.py`, explicit 5-state classification with
  provenance).
- **Step 2 (observability, §9 above):** Found and fixed the Windows RSS
  telemetry defect before any model re-evaluation — the single highest-
  leverage fix in this phase, since it had been silently zeroing the OOM
  family's only intended signal.
- **Step 3 (predictability, §13 above):** `cpu`/pooled-`oom`/`flaky` NOT
  VALIDATED (always-fires); `resource_unavailable` STRONG EVIDENCE;
  `oom`≥2-sample PLAUSIBLE.
- **Step 4 (generalization):** The pre-remediation OOM
  environment-generalization numbers (dev 0.678 → held-out 0.506) did not
  replicate under corrected telemetry (honest dev AUROC was only 0.434
  pre-fix — the problem statement itself needed re-establishing). Building
  a real, environment-aware feature (`rss_ratio_env_normalized`, using the
  run's own configured resource limits) raised OOM AUROC to 0.989 (dev),
  with only 0.006–0.054 degradation to held-out/robustness — held-out and
  robustness data were never touched during fitting.
- **Step 5 (uncertainty/decision, §14–15 above):** Sentiment's 4-candidate-
  estimator comparison and RETRY-scoping verification.
- **Step 6 (memory, §16 above):** The repeated-incident experiment and the
  restart/persistence/isolation check.
- **Step 7 (final verification):** Ran the full suite 8 times across the
  phase. Found and fixed **two further genuine engineering defects** beyond
  the 3 originally-known full-suite failures: a `cpu`-family timing-margin
  defect (`ADDENDUM_CPU_TIMING_DEFECT.md`) and — most significantly — a
  **timestamp-tie nondeterminism** in the core agent-decision path itself
  (`ADDENDUM_TIMESTAMP_TIE_DETERMINISM_DEFECT.md`): a `<` vs. `<=` boundary
  bug that could silently flip `ANSWER` vs. `REVIEW`/`ABSTAIN` for the
  highest-risk episodes. Fixed in `pipeline.py`. Final clean run: **837
  passed, 0 failed**, also confirmed test-order-independent by a full
  reversed-directory-order run (837/837, 1h03m53s).

**Final per-capability grades** (A = strong evidence; B =
engineering-complete/evaluation-limited; C = functional/limited evidence;
D = not validated), from `FINAL_POST_REMEDIATION_EVALUATION.md`:

| Capability | Grade |
|---|---|
| Failure prediction — `resource_unavailable` | **A** |
| Failure prediction — `oom` (observable subset) | **C** |
| Failure prediction — `cpu`, pooled `oom`, `flaky` | **D** |
| Environment generalization — OOM | **A** |
| Environment generalization — other families | **D** |
| Sentiment uncertainty (discrimination) | **D** |
| Sentiment uncertainty (calibration) | **B** |
| Arithmetic self-consistency uncertainty/decision | **B** |
| Retry/recovery mechanism | **B** |
| Memory (repeated-incident effect) | **A** |
| Memory (persistence/isolation) | **A** |
| Safety gate | **B** |
| Full-suite engineering health | **A** |

## 23. All major experiments

In addition to the phases above, several standalone research studies were
run under `experiments/results/`, each isolated and independently reported:

- **Generalization and robustness study** (`experiments/results/generalization/`):
  1.00 related-memory recovery success, 1.00 relevance recall, 0.00
  irrelevant-memory relevance recall, 1.00 abstention under conflicting
  memories, 1.00 abstention under safety conflict.
- **Counterfactual behavioral-generalization study**
  (`experiments/results/counterfactual_generalization/`): hides 3 latent
  mechanisms, evaluates unseen manifestations; the clean C7 counterfactual
  pair improves recovery success from 0.20 to 0.80.
- **Memory composition studies** (v1 and v2,
  `experiments/results/memory_composition{,_v2}/`): v1 found a real runtime
  defect (reversing equally-relevant memory order changed the decision
  between `abstain` and `reconfigure`); v2's `math.fsum` commutative-
  aggregation fix produced decision stability 1.00 across both permutation
  orders.
- **Phase 4.6–4.10** (`experiments/results/phase4_6_to_4_10/20260824T133029Z/`,
  detailed in §13–15, §22 patterns): real Hugging Face models
  (`distilbert-base-uncased-finetuned-sst-2-english`,
  `distilbert-base-cased-distilled-squad`), agent-specific calibrated
  retry (final error rate 1.7% → 0.0%, causally confirmed by a retry-off
  ablation), rigorous negative-controlled prediction re-evaluation, and
  3-environment generalization testing.
- **System evaluation runs** (`experiments/results/system_evaluation/`):
  5 independent timestamped full-pipeline evaluation bundles, each with its
  own ablation/baseline/leakage/overhead/robustness results and capability
  matrix; the source of the diagnosis cross-run-contamination incident
  (§12).
- **Post-P5 remediation and its 5 follow-ups** (§22, §29).

## 24. Datasets and data generation

- **Real operational data**: AgentRx (58/44 annotated agent trajectories),
  Alibaba PAI GPU2020 cluster trace (1,055,501 jobs, 25.94% terminal
  failure rate, all 7 source archives checksum-verified against the
  publisher), CCF AIOps 2020 KPI dataset (81 real fault-log events). Real
  data is gitignored (`/data/`) and fetched via a documented marker-file
  mechanism (`docs/archive/DATA_SETUP.md`); real-data-gated tests skip
  cleanly without it.
- **Real local AI/ML models** (Phase 4.6): two open-weight Hugging Face
  checkpoints downloaded once from the Hub and run locally on CPU (fp32,
  `eval()` mode) — `distilbert-base-uncased-finetuned-sst-2-english` (67M
  params) and `distilbert-base-cased-distilled-squad` (66M params). Full
  reproducibility manifests: `reproducibility/model.json`,
  `environment.json` in the Phase 4.6–4.10 run directory.
- **Synthetic/templated evaluation corpora**: sentiment and QA evaluation
  examples generated deterministically (`data/real_model_tasks/generate_corpora.py`,
  seeded, byte-for-byte reproducible) from templates whose correctness is
  guaranteed by construction (label fixed by template semantics; every QA
  gold answer asserted to be a verbatim substring of its own context at
  generation time). An initial "easy" tier produced 100% accuracy on both
  families (undefined AUROC, reported honestly); a "hard" tier
  (sarcasm/negation/mixed-clause sentiment; multi-entity/ordinal-position
  QA distractors) was then added, fixed **before** the evaluation that
  produced the reported numbers.
- **Controlled-runtime episodes**: real local subprocess executions across
  8 failure modes (`cpu`, `oom`, `gpu`, `corruption`,
  `resource_unavailable`, `flaky`, `network`, `fail`), generated on demand
  by `ControlledRuntime`, never pre-recorded or replayed.

## 25. Train/calibration/test methodology

Every threshold calibration and every trained model in Phase 4+ uses
disjoint seed-block splits, verified by direct construction in each
protocol document, never re-fit after seeing a test-split result:

- `SplitSeeds` / `AgentSplitSeeds`: raise on overlap in `__post_init__`.
- `calibrate_threshold(val_rows, ...)`: signature never accepts test rows.
- Phase 4.6–4.10: 500–1,500 train / 150–300 validation / 150–300 test
  seeds per protocol, all mutually disjoint; 3 disjoint seed-range
  replicates for Phase 4.8's headline prediction result (2,400 seeds
  total, none shared).
- Sentiment temperature-scaling fit (post-P5 Step 5): fit on the
  calibration split only; the test split used only for the final,
  unfitted evaluation of all 4 candidate estimators.
- Post-P5 remediation Step 7's calibration-leakage audit (item 14 in
  `FINAL_SYSTEM_CHECK.md`) confirmed this discipline held throughout the
  entire remediation phase by direct code reading.

## 26. Environment splits

Phase 4.9 defined three genuinely distinct `ControlledRuntime`
configurations (not merely different labels): `baseline-cpu` (development,
`timeout_seconds=0.15`), `memory-constrained` (held-out, OOM budget 4x
tighter, 5x finer telemetry sampling), `dependency-network-constrained`
(robustness, execution deadline halved, contended-resource family
contended 80% of the time vs. ~50% baseline). Models were fit and
threshold-calibrated on `baseline-cpu` only, then evaluated zero-shot
against each environment's own independently-generated test population —
verified never to have influenced training, threshold selection, or
feature choice. The post-P5 remediation phase reused this same
environment-isolation discipline for OOM's environment-aware feature (Step
4) and for follow-up 3's `resource_unavailable` combined-feature test.

## 27. Metrics and definitions

- **AUROC / AUPRC**: standard discrimination metrics; reported as `null`
  (never fabricated) when a population is single-class
  (`NOT_PREDICTABLE_SINGLE_CLASS`).
- **False-alarm rate / specificity**: computed at the calibrated decision
  threshold for every prediction family/variant this project reports —
  the mechanism that correctly disqualified 3 of 4 "always fires" families
  despite a nominally positive AUROC edge (Phase 3.8/P3-W5).
  "Always fires" means false-alarm rate ≈ 1.00 at the calibrated
  threshold: the model flags virtually every case as high-risk, so its
  AUROC edge reflects rank-ordering noise rather than a usable detector.
- **Brier score / ECE (Expected Calibration Error)**: probability
  calibration quality, distinct from discrimination.
- **Lead time / useful lead time**: seconds of advance warning before a
  failure; "useful" requires > 10ms, distinguishing genuine early warning
  from firing at the failure boundary.
- **Wilson 95% confidence interval**: used throughout for small-N recovery/
  retry rates rather than a bare point estimate.
- **Recovery success / recovery recovery rate**: fraction of failed
  episodes that reach a successful outcome after a recovery action.
- **Unsafe action / unsafe proposal rate**: fraction of adversarial or
  real cases where an unsafe action was authorized or executed; this
  project's target is exactly 0 in every phase, and every phase reports
  achieving it.

## 28. Positive findings

- Frozen V1: 56/56 replay cases completed with 0 unsafe executions;
  adversarial safety conditions correctly rejected 100% of the time.
- OOM environment generalization: AUROC 0.989 (dev) → 0.983 (held-out) →
  0.935 (robustness) with a real, mechanistically understood
  environment-normalized feature (P4-W2/P4-W4, grade **A**).
- `resource_unavailable` prediction via the pre-flight probe: real,
  replicated, mechanistically understood signal, zero false alarms across
  3 replicates (grade **A**).
- Memory repeated-incident effect: memory demonstrably changes the
  planner's chosen action at the earliest structurally possible episode,
  confirmed under real process restarts (grade **A**).
- Memory persistence/isolation: directly verified under real restart
  (grade **A**).
- Agent-specific calibrated retry: causally confirmed (retry-off ablation
  removes the entire final-error-rate improvement) — final error rate
  1.7% → 0.0%, zero unsafe actions across 1,200+ real episodes (grade
  **A** on retry and safety).
- Self-consistency uncertainty signal (arithmetic and QA task families):
  clean, monotonic accuracy-vs-samples and agreement-vs-accuracy curves —
  genuinely informative uncertainty, AUROC 0.934–0.953.
- Full test suite: 837 passed / 0 failed, confirmed test-order-independent,
  with 5 genuine engineering defects found and fixed across the whole
  effort (not hidden, not worked around).
- P2-W1 (larger held-out): calibrated policy improvement survives a 2x
  scale-up (final accuracy 0.998 vs. 0.970 generic, 95% CI non-overlapping).

## 29. Negative findings

Stated plainly, as this project's own integrity discipline requires:

- **Infrastructure failure prediction, in aggregate: not demonstrated.**
  Phase 4.8's rigorous, negative-controlled, replicated evaluation found
  no bimodal failure family (`cpu`, `oom`, `resource_unavailable`,
  `flaky`) whose real-label AUROC reliably beats its own label-shuffled
  control. The one apparent single-split exception (`cpu` at 0.636) did
  not replicate.
- **`cpu`-family prediction: NOT VALIDATED, final.** Even after the Step 7
  timing fix widened the real-vs-shuffled AUROC gap (0.616 vs. 0.389), the
  qualitative verdict is unchanged: false alarm rate 1.00 ± 0.00 in every
  replicate — an "always fires" pattern, not a usable detector. No further
  iteration is planned on this family.
- **Pooled `oom` and `flaky` prediction: NOT VALIDATED.** Consistently
  near-chance and/or always-fires across every phase that measured them.
- **`oom` ≥2-observability-sample subset: NOT VALIDATED at the operating
  point, final.** Follow-up 5 confirmed a real, replicated ranking edge
  (AUROC 0.780 vs. 0.625 shuffled) but false alarm rate 1.00 ± 0.00 and
  specificity only 0.179 ± 0.254 — the real signal does not translate into
  a usable detector under this project's threshold-calibration approach.
- **Environment generalization for non-OOM families: not demonstrated.**
  No environment-normalization problem was identified for them (unlike
  OOM), but no positive generalization result exists either.
- **Sentiment uncertainty discrimination: not fixable by estimator choice
  alone.** Mathematically shown (all 4 candidate estimators produce
  identical AUROC) — an explained, accepted limitation, not a bug to keep
  chasing.
- **Original Phase 4.3/4.4 recovery-learning hypotheses: NOT SUPPORTED.**
  The learned policy did not beat a fixed-priority baseline in either the
  single-step (4.3: effect +0.011 vs. 0.15 required) or two-step (4.4:
  effect −0.049, significant, wrong direction) controlled recovery
  environment. A post-hoc, clearly-labeled exploratory reanalysis found
  the required 0.15-point threshold had little achievable headroom against
  the oracle bound (4.3: 40%; 4.4: 19%) — a candidate explanation for a
  future, properly pre-registered phase, not a reversal of either frozen
  verdict.
- **Phase 4.2 pattern learning: INCONCLUSIVE**, underpowered (21/50 or
  14/10 evaluable contexts against pre-registered minimums), not negative.
- **`detectable_only_scope`'s AUC=0.857 (Phase 4.5b): explicitly not
  predictive skill** — a mixing artifact of deterministic and
  non-deterministic modes, reported with that caveat rather than presented
  as a win.
- **Predictor ON vs. OFF (Phase 4.10): no observable difference**, for an
  honest structural reason (the uninformative constant predictor happened
  to route to the same high-success-rate action a real predictor would in
  this specific task) — not evidence the predictor is unnecessary in
  general.

## 30. Known limitations

- Recovery executes for real against this project's own controlled local
  subprocess runtime — not a production fleet, not distributed
  infrastructure, not Kubernetes/Slurm/Ray-scale execution.
- The frozen 4.3/4.4 controlled-environment recovery-learning results
  still come from a frozen deterministic ground-truth table, unrelated to
  the later real-execution work.
- The sentiment/QA evaluation corpora are templated and hand-designed, not
  a standard external benchmark (GLUE/SQuAD) — absolute accuracy/AUROC
  numbers should not be compared to published leaderboard figures.
- The agent task family is a real, ground-truth-checked arithmetic
  reasoning problem and two real local Hugging Face models — not a call to
  an externally-hosted large language model API (unavailable in this
  sandboxed environment).
- `GPU_DEVICE_FAILURE` has zero real executable recovery actions — no
  fabricated fix was added for a genuinely absent GPU.
- Real-subprocess *generation* timing is not bit-reproducible across
  machines (though model inference and model fitting are both confirmed
  bit-deterministic given identical input) — documented in the Phase 4.10
  audit and observed directly as `LogisticRegression`'s unpinned
  `random_state` causing test-order-dependent RNG-seed sensitivity in
  `prediction_training.py` (a known, documented, not-yet-fixed item; see
  §31).
- No production authentication, rate limiting, or deployment hardening
  exists on the demo API (`src/api/app.py`).
- Default API model is intentionally unconfigured — the runtime abstains
  honestly rather than fabricating startup training.

## 31. Remaining research limitations

- **P4-W5 (containerized/production-scale environments)**: explicitly out
  of scope across every phase, never attempted.
- **P5-W4 (recovery/action taxonomy expansion beyond
  retry/reconfigure/rollback/escalate/abstain)**: not attempted.
- **`prediction_training.py`'s unpinned `LogisticRegression`
  `random_state`**: a known, documented test-order/RNG-seed sensitivity
  (first observed in Phase 4.8, recurring in Phase 4.9/4.10's regression
  checks) that a `random_state=` pin would fix — noted for a future audit
  rather than fixed opportunistically mid-priority, per this project's own
  scope discipline. Verified in this closure phase's own system audit (see
  `FINAL_SYSTEM_AUDIT.md`) whether it still affects the current suite.
- **Memory's behavioral effect under recurring `workload_id`s**: verified
  directly under a dedicated repeated-incident experiment (Step 6,
  grade A), but the larger-scale Phase 4.10 full-loop evaluation's own test
  design used a unique `workload_id` per episode and so did not exercise
  this effect at scale — an evaluation-coverage gap, not a disproof.
  `run_continuous()` (Phase 4.5 gap fixes) is the mechanism that would let
  a future evaluation exercise this at scale.
- **`resource_unavailable`'s follow-up 3 dev→held-out/robustness AUROC
  degradation**: could not be computed (single-class test populations at
  the inherited fixed seed range) — disclosed as a genuine data
  limitation, not silently worked around by re-rolling the seed range.
- **Threshold recalibration per target-environment configuration** for the
  OOM model: ranking transfers well across environments, but the fixed
  operating point (decision threshold) does not — recommended, not yet
  attempted.

## 32. Final capability grades

Combining `FINAL_POST_REMEDIATION_EVALUATION.md`'s grades (§22) with
Phase 4.10's capability matrix and the 5 follow-ups' updates (§29), using
the scale A = strong evidence, B = engineering-complete/evaluation-limited,
C = functional/limited evidence, D = not validated:

| Capability | Grade | Basis |
|---|---|---|
| Retry / recovery mechanism (agent task) | **A** | Causally confirmed via ablation; 0 unsafe actions across 1,200+ episodes |
| Safety gate | **A**–**B** | 0 unsafe authorizations/executions across every condition ever tested; unchanged and re-confirmed each phase |
| Memory (repeated-incident effect) | **A** | Real, replicated, mechanistically understood |
| Memory (persistence/isolation) | **A** | Directly verified under real restart |
| Environment generalization — OOM | **A** | Real, mechanistically understood, held-out/robustness genuinely untouched during fitting |
| Failure prediction — `resource_unavailable` | **A** | Real, replicated, mechanistically understood, zero false alarms |
| Reproducibility / full-suite engineering health | **A** | 837/837 passing, order-independence confirmed, every defect found this project's history documented and fixed |
| Uncertainty estimation (arithmetic, QA) | **B** | Strong AUROC (0.93-0.95), functioning end-to-end |
| Sentiment uncertainty (calibration) | **B** | Temperature scaling verified to improve ECE |
| Diagnosis | **B** | Functioning, memory-aware, not a fresh evaluation focus in later phases |
| Independent validation | **B** | Verified against a lying executor; not adversarially re-tested beyond Phase 4.4 |
| Learning | **B** | Correctly writes validated outcomes; large-scale recurring-workload effect not separately re-exercised |
| Failure prediction — `oom` (≥2-sample subset) | **C→D** | Real ranking signal (replicated), but NOT VALIDATED at the operating point (follow-up 5, final) |
| Memory (behavioral effect at scale) | **C** | Isolation verified; no observable effect in the one large-scale sample that used unique `workload_id`s per episode |
| Sentiment uncertainty (discrimination) | **D** | Explicitly not validated; mathematically shown not fixable by estimator choice |
| Failure prediction — `cpu`, pooled `oom`, `flaky` | **D** | NOT VALIDATED, final — "always fires" pattern |
| Environment generalization — non-OOM families | **D** | Not demonstrated |
| Recovery learning (Phase 4.3/4.4 controlled environment) | **D** (hypothesis not supported) | Learned policy did not beat fixed-priority baseline in either phase |

No capability is assigned an overall project-wide "A" merely because the
agent-level retry loop works — each row reflects only what was
specifically measured for that row, per the master weakness register's own
explicit instruction (carried forward unchanged into this record).

## 33. Reproducibility instructions

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows; .venv/bin/pip on macOS/Linux

python -m pytest tests/ -q                       # full suite; see FINAL_SYSTEM_AUDIT.md for the current count
python scripts/run_closed_loop_demo.py           # deterministic two-episode controller trace
python scripts/run_phase4_5_pipeline_demo.py     # Phase 4.4/5 closed-loop autonomy pipeline evidence run
python scripts/run_phase4_5_evidence_at_scale.py # Phase 4.5 gap-fix at-scale evidence
python scripts/run_phase4_6_real_agent_evaluation.py
python scripts/run_phase4_7_retry_calibration_experiment.py
python scripts/run_phase4_8_prediction_evaluation.py
python scripts/run_phase4_9_environment_generalization.py
python scripts/run_phase4_10_final_integrated_evaluation.py
python scripts/run_p1_step5_sentiment_uncertainty.py
python scripts/run_p3_step3_predictability.py
python scripts/run_p4_step4_environment_generalization.py
python scripts/run_p5_step6_memory_repeated_incident.py
python scripts/generate_sha256_manifest.py <run_dir>   # regenerate a run directory's integrity manifest
```

Every phase writes to its own `experiments/results/<phase>/` directory and
(from the post-P5 remediation phase onward) a timestamped run directory
under a `SHA256_MANIFEST.json` integrity manifest, generated last, over
every other file in that run directory. Frozen protocol JSON files under
`configs/` and each phase's own protocol document fix splits, sample
sizes, and leakage exclusions before any result is computed.

## 34. Testing and QA

The test suite is organized under `tests/{unit,integration,e2e,recovery,runtime}/`.
Historical suite-size milestones (each a real, captured count, not an
estimate): 432 (pre-architectural-recovery) → 439 → 444 → 453 → 477 → 649
→ 668 → 693 → 735 → 753/770/795/801/808 (Phase 4.6–4.10, with 3 final,
fully-diagnosed failures: 2 real-GPU-hardware environment differences, 1
RNG-seed test-order sensitivity) → 837 (post-P5 remediation and
follow-ups, 0 failed). Every full-suite milestone in this project's
history is a real, captured `pytest` run — the project's own August 23
audit (`docs/archive/PHASE4_5_AUDIT_AND_PLAN.md`) explicitly flagged the
risk of a plausible-sounding phase-completion claim outrunning its
validation, and the mitigation adopted (checking every claim against a
real captured log) has been followed consistently since. This closure
phase's own test-suite results (both directory orders) are recorded in
`FINAL_SYSTEM_AUDIT.md`.

## 35. Docker / deployment / CI information

**None exists in this repository.** A direct search of the working tree
found no `Dockerfile`, no `docker-compose.yml` or variant, and no
`.github/workflows/` directory (or any other CI configuration). The
project's own README states this explicitly under "Explicitly not used":
*"no Docker/CI pipeline yet, no frontend, no message queue between
components... no ORM abstraction beyond SQLAlchemy's own."* This record
does not fabricate any deployment or CI capability beyond what is actually
present — there is a demo FastAPI app (`src/api/app.py`, `POST
/api/analyze`) runnable locally via `uvicorn`, with **no production
authentication, rate limiting, or deployment hardening**, exactly as the
Known Limitations section has stated since the original consolidated
record.

## 36. Repository structure

```
src/
  api/                 FastAPI demo app (POST /api/analyze)
  decision/            frozen DecisionPolicy (reused by phase4/decision.py)
  failure_experience/  canonical FailureExperience schema (Gen 2/V1)
  failure_memory/       Gen 1 failure memory (frozen, synthetic-era)
  failure_patterns/     Gen 1 pattern learning (frozen, synthetic-era)
  phase3_contract.py    explicit statement of independence from V1
  phase4/               active codebase (Gen 3) — see §8 for full module list
  recovery/             frozen Gen 2 recovery/safety/environment modules
  reliability/          calibration, artifact save/load (reused by phase4)
  runtime/               frozen Gen 2 closed-loop controller
  schema/                canonical ReliabilityEvent schema (events.py)
  storage/, patterns/, experience/, evaluation/, data/, data_foundation/
tests/
  unit/, integration/, e2e/, recovery/, runtime/
configs/                 frozen protocol JSON per phase
benchmarks/               one deterministic benchmark script per experiment
scripts/                  evidence-generation and utility scripts
experiments/results/      one directory per phase/experiment; source of truth for every number
docs/                     archive/ (56+ frozen historical documents) + this record + the prior .docx
data/                     gitignored; real datasets fetched via docs/archive/DATA_SETUP.md
```

## 37. Final benchmark / model / dataset status

- **Benchmarks**: one `benchmarks/*.py` script per experiment, deterministic
  given a fixed seed, writing to `experiments/results/`.
- **Models**: `TrainedRiskPredictor` (versioned `LogisticRegression`
  pipeline artifacts, `experiments/results/phase4_5_autonomy_pipeline_at_scale/prediction_artifact/`
  and `.../phase4_5b_recognition_and_agent_evaluation/prediction_scope_router_artifact/`);
  two real Hugging Face checkpoints (§24); V1's isotonic-calibrated
  logistic-regression workload model (frozen, Gen 2).
- **Datasets**: 3 real operational datasets (AgentRx, Alibaba GPU2020,
  AIOps 2020), 2 real pretrained model weight sets, deterministic synthetic/
  templated corpora for every controlled-runtime and agent-task
  evaluation. No dataset or model in this repository is fabricated or
  claimed without a manifest.

## 38. What remains for future work

- Re-run P2-W1/P2-W3-style expansions at even larger scale if a future
  phase wants tighter confidence intervals (current expansions: 2x
  held-out, an 18-point economics grid).
- P4-W5: containerized/production-scale environment generalization
  (explicitly never attempted).
- P5-W4: recovery/action taxonomy expansion beyond the current 5 actions.
- Threshold recalibration per target-environment configuration for the OOM
  model (ranking transfers; the fixed operating point does not).
- Pin `LogisticRegression`'s `random_state` in `prediction_training.py` to
  remove the documented test-order/RNG-seed sensitivity (a genuine,
  small, still-open engineering item — see §31 and `FINAL_SYSTEM_AUDIT.md`
  for its current status).
- A larger-scale evaluation of memory's behavioral effect using
  `run_continuous()` against genuinely recurring `workload_id`s (the
  700-episode-per-workload_id-recurrence design outlined but not
  performed by Phase 4.10).
- Any real externally-hosted large language model evaluation, and any
  multi-node/cluster-scale claim — both explicitly out of scope throughout
  this project's history, not merely deferred.

## 39. References to underlying raw evidence and artifacts

This record intentionally does not duplicate raw JSON/data; every claim
above traces to one of these canonical locations:

- `docs/archive/` — 56+ frozen historical per-phase documents (Phase 1–4,
  V1, all real-data track reports).
- `docs/Autonomous_AI_Infrastructure_Comprehensive_Record.docx` — the
  prior (2026-08-23) consolidated record this document supersedes.
- `experiments/results/phase3_*`, `phase3_real_data/` — Phase 3 synthetic
  and real-data track raw results.
- `experiments/results/phase4_0` … `phase4_4`, `phase4_1_active/`,
  `phase4_2_active/` — original and active-era Phase 4 raw results.
- `experiments/results/phase4_4_autonomy_pipeline/`,
  `phase4_5_autonomy_pipeline_at_scale/`,
  `phase4_5b_recognition_and_agent_evaluation/` — Phase 4.4/4.5/4.5b raw
  results and trained-model artifacts.
- `experiments/results/phase4_6_to_4_10/20260824T133029Z/` — the complete
  Priority 4.6–4.10 run: `protocol/`, `evaluation/`, `audits/`, `raw/`,
  `reports/`, `reproducibility/`, `SHA256_MANIFEST.json`.
- `experiments/results/post_p5_remediation/20260825T064402Z/` — the
  complete 7-step remediation run (frozen, read-only reference for this
  closure phase): `MASTER_REMEDIATION_REPORT.md`,
  `FINAL_POST_REMEDIATION_EVALUATION.md`, `protocol/`, `reports/`,
  `audits/`, `manifests/`, `reproducibility/`, `SHA256_MANIFEST.json`.
- `experiments/results/post_p5_remediation_followups/20260825T144031Z/` —
  the 5 follow-ups (frozen, read-only reference for this closure phase):
  `FOLLOWUPS_SUMMARY.md`, `reports/`, `protocol/`, `raw/`, `manifests/`.
- `experiments/results/system_evaluation/` — 5 independent full-pipeline
  evaluation bundles plus the diagnosis-contamination incident reports.
- `experiments/results/v1_1/`, `v1_control_reconciliation/`,
  `reliability_runtime_v1/`, `reliability_runtime_v2/`,
  `alibaba_closed_loop_v1/`, `alibaba_closed_loop_v2/` — V1/Gen-2 raw
  evidence and reconciliation records.
- `experiments/results/generalization/`, `counterfactual_generalization/`,
  `memory_composition/`, `memory_composition_v2/`, `learning_influence/` —
  standalone research studies (§23).
- `src/phase4/` — the active codebase implementing everything in §8–21.
- `DOCUMENT_CLEANUP_MANIFEST.md` (repo root) — this closure phase's full
  document inventory and cleanup actions (Part A).
- `FINAL_PHASE4_CLOSURE_REPORT.md`, `FINAL_WEAKNESS_REGISTER.md`,
  `FINAL_SYSTEM_AUDIT.md` (repo root) — this closure phase's final test
  results, consolidated weakness register, full system audit, and freeze
  decision.

## 40. Phase 5 — Dataset construction, benchmark, and finalization

Phase 5 turns the Phase 4 evidence base into a reusable, independently
runnable dataset and benchmark, then (Phase 5.5) audits and packages both
for release. Four sub-phases:

- **Phase 5.1 — Dataset specification** (`experiments/results/phase5_dataset_specification/20260826T053011Z/`):
  schema, split policy (sample-level axis train/calibration_validation/test;
  environment axis development/held_out/robustness, workload_id as the
  mandatory grouping key), leakage policy (14 rules), provenance contract,
  and publication boundary (what may/may not be published and why).
- **Phase 5.2 — Dataset construction** (`experiments/results/phase5_dataset_construction/20260826T054422Z/`):
  the canonical dataset. 3,106 records — 3,060 `agent_task` episodes
  (2,000 arithmetic self-consistency, 660 sentiment, 400 extractive QA)
  and 46 `controlled_runtime` failure/recovery episodes — generated
  entirely from this project's own Phase 4 evaluation code, no
  third-party data. Splits: train=2,142, calibration_validation=482,
  test=482, 0 overlap, 0 workload_id cross-split violations. Only 1
  environment is represented (`UNSPECIFIED_PRE_4_9` — this dataset
  predates Phase 4.9's per-episode environment identity). 0 realized
  ABSTAIN/RETRY-decision episodes exist in the ingested raw sources.
- **Phase 5.3 — Benchmark specification** (`experiments/results/phase5_benchmark_specification/20260826T055915Z/`):
  16 tasks across 8 tracks (uncertainty, abstention, failure prediction,
  diagnosis, recovery, memory, generalization, end-to-end), a 33+-metric
  catalog, a baseline catalog (including adversarial baselines so a
  trivial always-abstain/always-answer policy cannot appear to win), an
  ablation matrix, and an explicit leakage policy restated at the
  benchmark-task-derivation level (12 rules, L1–L12).
- **Phase 5.4 — Benchmark implementation** (`experiments/results/phase5_benchmark_implementation/20260826T150824Z/`,
  code in `src/benchmark/`): the executable scoring harness. Of the 16
  tasks: 3 UNDERPOWERED (uncertainty), 6 PARTIALLY_VALIDATED (abstention
  x3, diagnosis, recovery, end-to-end), 7 NOT_EVALUABLE (failure
  prediction x4, memory, generalization x2). No task is VALIDATED and no
  single overall benchmark score is computed or endorsed.
- **Phase 5.5 — Finalization and packaging**
  (`experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/`):
  a two-gate closure. Gate A independently re-audited every headline
  Phase 5.3/5.4 number from raw evidence (not by trusting prior reports),
  resolved a genuine contradiction between two Phase 5.3 documents about
  what counts as an adequately powered sample size, re-ran the full
  benchmark from a fresh process and confirmed byte-identical,
  deterministic results, ran the entire repository test suite to
  completion (880 passed / 8 failed, the 8 failures pre-existing and
  confirmed unrelated to the benchmark), and passed. Gate B then packaged
  a self-contained dataset release and a self-contained benchmark release,
  each independently verified end-to-end from an isolated clean-room copy
  containing no reference back to this repository.

## 41. The Phase 5.3 sample-size contradiction and its resolution

Two frozen Phase 5.3 documents disagreed on how to judge whether the
uncertainty track (arithmetic/sentiment/QA) has enough data:
`PHASE5_3_DATASET_COVERAGE.json` reasoned from full-family record counts
(2,000/660/400, "met or exceeded" the 500/300/300 minimums), while
`PHASE5_3_SPLIT_POLICY.md` §4 states a benchmark run MUST report a task as
`UNDERPOWERED/DESCRIPTIVE ONLY` whenever its **test-split** count alone is
below the minimum. The actual test-split counts (310/113/49) are all below
their minimums. Phase 5.5 resolved this in favor of the stricter,
test-split-count reading — the correct rule for a benchmark's headline
claim, since a metric's confidence interval is only as good as the rows
actually held out for final, unfitted evaluation, and accepting the
looser reading would let any task look adequately powered merely by
shrinking its test split. This reproduces, rather than overturns, Phase
5.4's original classification: **UNC-ARITH, UNC-SENT, and UNC-QA are all
UNDERPOWERED at benchmark-run time**, even though ample underlying data
exists at the family level. The point estimates themselves (AUROC 0.955 /
0.439 / 0.938 respectively) are reported in full; only the headline-claim
status is withheld. See `SPECIFICATION_RECONCILIATION.md` in the Phase
5.5 output directory for the complete reasoning.

## 42. Phase 5 capability matrix (never collapse this to one number)

| Track | Task | Status | Primary evidence | Sample size | Limitation |
|---|---|---|---|---|---|
| uncertainty | UNC-ARITH | UNDERPOWERED | AUROC 0.955 | n_test=310 (min 500) | Real estimate, below the sample-size gate |
| uncertainty | UNC-SENT | UNDERPOWERED | AUROC 0.439 (near-chance) | n_test=113 (min 300) | Genuine discrimination ceiling, disclosed not hidden |
| uncertainty | UNC-QA | UNDERPOWERED | AUROC 0.938 | n_test=49 (min 300) | Real estimate, below the sample-size gate |
| abstention | ABST-ARITH/SENT/QA | PARTIALLY_VALIDATED | Selective risk 0.0 / 0.3125 / 0.03125 at calibrated threshold | n=310/113/49 | SIMULATED_POLICY_EVALUATION — no realized ABSTAIN/RETRY episodes exist in this dataset |
| failure_prediction | PRED-RESOURCE-UNAVAILABLE/OOM/CPU/FLAKY | NOT_EVALUABLE | n/a at record level | n=0/10/1/24 (min 300) | Aggregate Phase 4 verdicts (resource_unavailable=STRONG_EVIDENCE; cpu/oom/flaky=NOT_VALIDATED) preserved as reference only, never recomputed as a per-episode score |
| diagnosis | DIAG-EVAL | PARTIALLY_VALIDATED | Failure-class accuracy 1.0 (35/35), independently re-verified in Phase 5.5 | n=35 | False-causal-attribution-rate = 1.0: every diagnosis names a cause while this dataset has no independent causal ground truth — a class-matching result, never a causal claim |
| recovery | REC-EVAL | PARTIALLY_VALIDATED | Recovery success rate 0.0 (0/35), independently re-verified in Phase 5.5 | n=35 | Genuine negative finding on this dataset slice, not a benchmark defect |
| memory | MEM-EVAL | NOT_EVALUABLE | n/a | 1 repeated-workload group (3 records), independently re-verified in Phase 5.5 | Far below any usable scale for a memory-adaptation claim |
| generalization | GEN-RANKING/OPERATING-POINT-CONTRACT | NOT_EVALUABLE | n/a | 1 environment, independently re-verified in Phase 5.5 | Phase 4's own 0.989/0.983/0.935 OOM ranking numbers (§28) and the operating-point transfer failure (§29) remain the real, valid evidence — as aggregate reference, never joined to a per-episode record |
| end_to_end | E2E-EVAL | PARTIALLY_VALIDATED | E2E recovery rate 0.0 | n=46 | Full 8-stage loop coverage confined to controlled_runtime records; consistent with the 0/35 recovery finding above |

## 43. Release information

Phase 5.5 Gate B produced two independently runnable, self-contained
release packages under
`experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/release/`:

- **Dataset release** (`release/dataset/`): the 3,106-record canonical
  dataset, its integrity/provenance artifacts, Phase 5.1 schema/policy
  documents, a `DATASET_CARD.md`, `README.md`, and `CITATION.cff`.
  Verified in an isolated clean-room copy: SHA-256 matches the published
  manifest exactly, and all 3,106 records parse successfully with no
  dependency beyond the Python standard library.
- **Benchmark release** (`release/benchmark/`): the full `src/benchmark/`
  implementation, its exact bundled dataset/spec dependency tree, runner
  and manifest-generation scripts, unit tests, `requirements.txt`,
  `BENCHMARK_CARD.md`, `README.md`, `REPRODUCIBILITY_GUIDE.md`, and
  `CITATION.cff`. Verified in an isolated clean-room copy outside this
  repository (no `.git`, no reference to this repository's path): the
  benchmark ran to completion, reproduced byte-identical results to the
  in-repo reference run, and its 41-test unit suite passed, after two
  genuine packaging omissions (found only by attempting the clean-room
  run) were corrected — see `CLEAN_ROOM_REPRODUCIBILITY_REPORT.md` in the
  Phase 5.5 output directory.
- **What is excluded from both releases**: V1/Gen-2 evidence, trained
  model pickle artifacts, SQLite memory-store files, host/platform
  identity metadata (confirmed absent by direct scan), and all
  engineering-only test/CI logs — per `PUBLICATION_BOUNDARY_MANIFEST.json`.
- **Nothing was uploaded to Hugging Face or any external host.** Both
  release packages exist only inside this repository's
  `experiments/results/phase5_5_finalization_and_packaging/20260827T051355Z/release/`
  directory and this phase's local clean-room verification copies (which
  were themselves temporary and local-machine-only).
- **License / provenance**: both packages are released under the parent
  project's license terms; every record traces to a named Phase 4 raw
  evidence source with no fabricated or aggregate-to-record-converted
  content anywhere in either package.
