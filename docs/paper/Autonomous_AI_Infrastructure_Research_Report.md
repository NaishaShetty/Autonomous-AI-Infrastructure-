# Autonomous AI Infrastructure: A Research Report on Calibrated Confidence, Failure Memory, and Recovery Learning in a Controlled Self-Healing System

*Markdown is the primary, canonical source for this report. A PDF could be
generated from it with a standard Markdown-to-PDF toolchain, but none was
found already configured in this environment during Phase 6, so no PDF
was produced or claimed here — see `RESEARCH_WRITEUP_AUDIT.md` in the
Phase 6 output directory.*

---

## 1. Abstract

This report documents a multi-phase research program that builds and
evaluates a self-healing AI/ML infrastructure system: a pipeline that
observes workload telemetry and real AI/ML agent output, estimates
calibrated confidence, predicts failures where evidence supports it,
diagnoses failure class, plans and safety-gates a recovery action,
executes it against a real controlled runtime, independently validates
the outcome, and updates a persistent failure-memory store. The project
began by auditing two independent prototype systems, migrated them into
one architecture (itself producing a negative finding), and proceeded
through six major phases culminating in a 3,106-record canonical dataset
and a 16-task, 8-track benchmark with an explicit per-task capability
matrix rather than one aggregate score. Headline results are mixed by
design: safety gating and calibrated-decision robustness are strongly
supported; three of four failure-prediction classes and all record-level
prediction/memory/generalization benchmark tasks are `NOT VALIDATED` or
`NOT_EVALUABLE`; diagnosis accuracy is real but strictly class-matching,
never causal; and controlled recovery-policy learning produced two
consecutive "hypothesis not supported" verdicts. This report preserves
every one of these findings explicitly rather than collapsing them into a
single "AI reliability" claim.

## 2. Introduction

Self-healing infrastructure is usually shipped as a single anomaly score
wired to a single remediation rule. That makes it structurally impossible
to answer basic questions in isolation: does persistent failure memory
actually help? does a learned policy beat a well-designed heuristic? does
a confidence signal generalize, or does it only look good on the data it
was tuned on? This project was built the opposite way: confidence
calibration, failure memory, pattern discovery, prediction, diagnosis, and
recovery selection are separate, independently testable modules behind one
decision policy, each with its own frozen protocol, leakage audit, and
(where applicable) an oracle reference bound or an adversarial baseline
designed so a trivial policy cannot appear to win.

## 3. Origin and predecessor systems

Two independently developed research prototypes preceded this project:

- **AI-Abstention-Engine** (~9,700 backend lines): confidence/abstention
  logic. An audit (`docs/archive/PHASE1_AUDIT_REPORT.md`) found a live
  confidence-scale bug (`global_reliability_score: 189.61` on a documented
  0–100 scale, from averaging two incompatible representations), a query
  that defaulted to abstention while its own explanation text claimed
  "Confidence 61%", a 404 on `/api/metrics`, and a committed database
  containing real personal emails and password hashes.
- **Introspective Failure Memory Model** (~1,560 backend lines): episodic
  failure memory and risk-coverage prediction. The audit found a real
  risk-coverage signal (baseline error 35.44% → 8.05% at 15% coverage) but
  no tests, in-memory-only storage, and a live 500 error from unhandled
  numpy JSON serialization.

Both systems were audited component-by-component *before* migration.
Phase 2 combined them into one pydantic-enforced architecture — confidence
type-constrained to `[0,1]` by construction, fixing every Phase 1 defect
structurally — and this migration itself produced a real negative
research finding (see §7). This was not a copy-paste merge: architectural
decisions (which modules to keep, which to rebuild, which vocabulary to
standardize on) are recorded in `docs/archive/PHASE2_REPORT.md` and
`docs/archive/ARCHITECTURE_MAP_BASELINE.md`.

## 4. Research question

> Given calibrated confidence, persistent failure memory, and a controlled
> recovery-selection environment, can a context-aware, learned recovery
> policy detect and diagnose failures, abstain when evidence is
> insufficient, and select a recovery action that measurably beats a
> strong, non-learned heuristic — without exceeding a zero-tolerance
> unsafe-action rate? Extended in Phase 4/5: can the same discipline be
> applied to a live, project-owned controlled runtime and a real AI/ML
> agent?

## 5. System architecture

The canonical runtime (`src/phase4/pipeline.py`, `AutonomyPipeline`) walks
an explicit state machine: `RECEIVED → OBSERVING → PREDICTED → DECIDING →
DIAGNOSING → PLANNING → SAFETY_CHECK → EXECUTING → VALIDATING → RECOVERED
/ NOT_RECOVERED / ABSTAINED → COMPLETED`. Two entry points exercise it:
`run_workload()` (process/infrastructure telemetry) and `run_agent_task()`
(a real AI/ML agent's output across three task families). Two earlier,
complete architecture generations remain frozen underneath it: Generation
1 (`src/failure_memory/`, `src/failure_patterns/`, synthetic data) and
Generation 2 / "V1" (`src/runtime/`, `src/recovery/`,
`src/failure_experience/`, `src/decision/policy.py`, Alibaba GPU2020 trace
replay, 56/56 replay cases, 0 unsafe executions). Full diagrams:
[`docs/architecture/`](../architecture/README.md).

## 6. The uncertainty and abstention architecture

Three genuinely different uncertainty mechanisms are used, one per task
family, never forced into a single blended signal:

- **Arithmetic self-consistency disagreement** — AUROC 0.953 (Phase 4.6
  scale), 0.955 (Phase 5.2 benchmark, n=310, `UNDERPOWERED` vs. a
  pre-registered minimum of 500).
- **Sentiment softmax-margin** — AUROC 0.659 (Phase 4.6 scale), 0.439
  (benchmark, n=113, `UNDERPOWERED`, near-chance). Post-P5 remediation
  Step 5 tested 4 candidate uncertainty estimators under a strict
  calibration/test split: all 4 produced mathematically identical AUROC
  (binary-classification confidence transforms are rank-equivalent) — a
  real, explained negative result, not a bug. Temperature scaling fixed
  calibration (ECE 0.089 → 0.023) while leaving discrimination unchanged.
- **Extractive QA span-logit margin** — AUROC 0.934 (Phase 4.6 scale),
  0.938 (benchmark, n=49, `UNDERPOWERED`).

## 7. The decision policy

`src/decision/policy.py`'s `DecisionPolicy` (frozen, reused rather than
rebuilt across every phase) is the single authoritative decision engine.
Phase 2's own negative finding: the failure-memory risk signal did **not**
improve calibrated abstention beyond confidence alone (selective risk
0.1667 vs. 0.2083 at 20% coverage; failure-memory correlation with
correctness 0.031 — essentially noise — vs. 0.200 for confidence). Two
profiles exist: **generic** (`answer_threshold=0.70`,
`abstain_threshold=0.40`) and the **agent-specific calibrated profile**
(`AgentDecisionCalibrationProfile`, Phase 4.7 — 4 fixed agreement-rate
buckets, Laplace-smoothed per-bucket estimates, a pre-registered
expected-utility formula). An 18-point pre-registered grid over
`COST_RETRY_PER_EXTRA_SAMPLE` × `BENEFIT_CORRECT` × `COST_WRONG_ANSWER`
produced byte-identical decisions/outcomes in all 18 configurations (final
accuracy 1.000 on a 40-seed/3-wrong-episode grid) — no fragility observed
within the pre-registered range, with the caveat that this small grid
limits how far "no fragility" generalizes.

## 8. Failure memory

`src/phase4/memory.py`'s `FailureMemoryStore` is a frozen contract, written
and frozen *before* any memory-read path was added to diagnosis: scoped by
`(workload_id, environment_id, failure_class)`, never by `run_id`;
temporally safe; versioned; fail-closed on under-specified queries. A
dedicated repeated-incident experiment (same workload, real process
restarts, memory ON vs. OFF) found: memory ON → retry → retry →
reconfigure → recovered; memory OFF → retry ×6. This is a real, measured
behavior change under real restarts. A separate, larger 300-episode
full-loop evaluation (Phase 4.10) found no observable ON/OFF difference —
traced to a structural cause (every episode used a distinct
`workload_id`, so no episode's stored experience was ever eligible for
retrieval by a later one), i.e. the memory-isolation contract working
exactly as designed, not evidence memory is inert. These two findings are
reported side by side, never merged.

## 9. Prediction

Prediction went through five evidentiary stages of increasing rigor (see
`docs/MASTER_RECORD_CONTENT.md` §13 for full detail): from a
deliberately-not-trained engineered risk score, to an ML-trained
`LogisticRegression` pipeline (aggregate AUC 0.515, near chance), to a
scope-routed evaluation, to a rigorous within-family re-evaluation with a
run-level label-shuffled negative control (`prediction_eval_v2.py`), to a
final post-remediation pass adding a false-alarm-rate/specificity check.
**Final result**: `resource_unavailable` is `STRONG_EVIDENCE` from a
genuine pre-flight-probe mechanism (combined-feature held-out AUROC up to
0.916); `cpu`, pooled `oom`, and `flaky` are `NOT VALIDATED` — each shows
an "always fires" pattern (false-alarm-rate ≈ 1.00) at its calibrated
threshold despite a nominal AUROC edge over a shuffled control, and this
does not survive replication for `cpu` (real 0.616 ± 0.045 vs. shuffled
0.389 ± 0.032, but FAR 1.00 ± 0.00). The `oom` ≥2-observability-sample
subset shows a real, replicated ranking edge (0.780 ± 0.096 vs. 0.625 ±
0.093 shuffled) but remains `NOT VALIDATED` at the operating point
(specificity 0.179 ± 0.254). **All four `PRED-*` benchmark tasks are
`NOT_EVALUABLE` at record level** — their only supporting evidence is
aggregate-level, with no per-episode join key in the canonical dataset.

## 10. Diagnosis

`DiagnosisEngine` achieves failure-class-matching accuracy of 1.0 (35/35)
on the Phase 5.2 dataset slice. This number is never reported without its
paired caveat: the false-causal-attribution-rate is *also* 1.0, because no
independent causal ground truth exists in either the Phase 4 evaluation
runs or the Phase 5.2 dataset — every diagnosis names a suspected cause,
none is independently verified. Class-matching accuracy is a defensible,
real claim; causal diagnosis is not claimed anywhere in this project.

## 11. Recovery planning, safety, execution, and validation

`RuleBasedRecoveryPlanner` selects among `RETRY`, `RESTART`, `ROLLBACK`,
`RECONFIGURE`, and escalation. `AdaptiveRecoveryPlanner` (Phase 4.5 gap
fixes) ranks actions with a Beta(1,1)-smoothed online success-rate
estimate, reaching 100% correct-action selection by episodes 951–1000
(from 98.0% at episodes 1–50) on a deliberately close pair of true
recovery probabilities (0.35 vs. 0.65), while the unmodified rule-based
planner stayed at 0.0% on the identical scenario. `RecoverySafetyGate`
gates every execution: a 6-case adversarial matrix (Phase 4.4/5) and a
16-case matrix (Phase 4.5 gap fixes) both produced 0 incorrectly
authorized. Execution is real for `RETRY`/`RESTART` (re-invokes
`ControlledRuntime`'s own subprocess boundary), `ROLLBACK` (replays a real
recorded checkpoint or honestly records "not executed"), and
`RECONFIGURE` (halves a real numeric load parameter or selects a free
port — measured to genuinely change the outcome: `RESOURCE_UNAVAILABLE`
100% recovery via `RECONFIGURE` to a free port vs. 0% via `RETRY` on the
contended one, n=40 each, Wilson 95% CI [0.91,1.0] vs. [0.0,0.09]).
`SignalRecoveryValidator` independently re-derives the outcome from raw
events through a fresh `MonitoringEngine`, tested against a deliberately
lying executor. On the Phase 5.2 benchmark dataset slice, the `REC-EVAL`
recovery success rate is **0/35 (0.0)** — a genuine negative finding on
this slice, reported as such.

## 12. Environment generalization

Phase 4.9 built an environment-aware feature
(`rss_ratio_env_normalized`) and found OOM failure-ranking AUROC transfers
well across environments — dev 0.989, held-out 0.983, robustness 0.935 —
while the *fixed decision threshold* does not transfer cleanly. **Ranking
generalization and operating-point generalization are two distinct claims
in this project's vocabulary and are never merged.** Both numbers are
Phase 4 aggregate-level findings; the Phase 5.2 canonical dataset
represents only 1 environment, so `GEN-RANKING-CONTRACT` and
`GEN-OPERATING-POINT-CONTRACT` are `NOT_EVALUABLE` at record level in the
benchmark.

## 13. Recovery-policy learning (Phase 4.3, 4.4)

A controlled, leakage-audited recovery-selection environment tested
whether a learned policy beats a serious fixed-priority baseline, both
single-step (4.3) and two-step/sequential-with-abstention (4.4). Both
produced **"PASS — hypothesis not supported"**: 4.3's effect was +0.011
against a required +0.15; 4.4's was −0.049 (significant, wrong direction).
A later, explicitly exploratory, post-hoc, **not pre-registered** analysis
(confirmed absent from either frozen protocol JSON by direct inspection)
found neither phase had checked, before freezing its 0.15-point threshold,
whether that much headroom existed between baseline and oracle bound — 4.3
had 0.060 available (40% of required), 4.4 had 0.029 (19%) — and that
4.4's negative effect is largely attributable to its metric scoring
abstention identically to failure. **This does not reopen either recorded
verdict**; it is a candidate hypothesis for a future, properly
pre-registered phase.

## 14. Dataset construction (Phase 5.1/5.2)

The Phase 5.2 canonical dataset (3,106 records: 3,060 `agent_task` + 46
`controlled_runtime`) was constructed entirely from this project's own
Phase 4 evaluation code — no third-party dataset content. Splits (grouped
by `workload_id`, 0 crossings): train=2,142, calibration_validation=482,
test=482. Every record traces to a named Phase 4 raw-evidence source
(`identity.source_artifact_version`) per the Phase 5.1 provenance
contract; no aggregate statistic was ever converted into a fabricated
per-record value. See [`docs/architecture/06_dataset_pipeline.md`](../architecture/06_dataset_pipeline.md).

## 15. Benchmark design (Phase 5.3/5.4)

16 tasks across 8 tracks, 33 metrics, 10 baselines (including adversarial
ones like `BASE-ALWAYS-ABSTAIN`, flagged `ALWAYS_ABSTAIN_NOT_SUCCESSFUL`,
so a trivial policy cannot appear to win), 5 ablations, 12 leakage rules.
No aggregate score is computed. Determinism is checked on every run (the
runner executes the benchmark twice) and was independently re-verified
byte-identical across separate process invocations on different days —
re-confirmed during Phase 6 (see §22).

## 16. Final benchmark capability matrix

| Track | Task | Status |
|---|---|---|
| uncertainty | UNC-ARITH, UNC-SENT, UNC-QA | UNDERPOWERED (×3) |
| abstention | ABST-ARITH, ABST-SENT, ABST-QA | PARTIALLY_VALIDATED (×3) |
| failure_prediction | PRED-RESOURCE-UNAVAILABLE, PRED-OOM, PRED-CPU, PRED-FLAKY | NOT_EVALUABLE (×4) |
| diagnosis | DIAG-EVAL | PARTIALLY_VALIDATED |
| recovery | REC-EVAL | PARTIALLY_VALIDATED |
| memory | MEM-EVAL | NOT_EVALUABLE |
| generalization | GEN-RANKING-CONTRACT, GEN-OPERATING-POINT-CONTRACT | NOT_EVALUABLE (×2) |
| end_to_end | E2E-EVAL | PARTIALLY_VALIDATED |

**0 VALIDATED · 6 PARTIALLY_VALIDATED · 3 UNDERPOWERED · 0 NOT_VALIDATED · 7 NOT_EVALUABLE.**
Full per-task evidence, sample sizes, and limitations:
[`BENCHMARK_CARD.md`](../../experiments/results/phase5_6_external_release/20260827T055356Z/BENCHMARK_CARD.md).

## 17. Public release (Phase 5.5/5.6)

Two Hugging Face packages were published: the dataset
(<https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-dataset>,
CC BY 4.0) and the benchmark
(<https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-benchmark>,
MIT). No model repository was published — no single trained-model
artifact in this project (the `RiskPredictor` / `PredictionScopeRouter`
behind the 4 `PRED-*` tasks) is independently validated at record level;
publishing one risked a reader treating an aggregate-only or explicitly
`NOT_EVALUABLE` predictor as a usable trained model.

## 18. Threats to validity

- **Single controlled runtime environment** — recovery execution evidence
  comes from this project's own local subprocess environment, not a
  production fleet; results may not transfer to real infrastructure.
- **Single represented environment in the canonical dataset** — the real
  multi-environment generalization numbers (§12) come from a separate
  Phase 4 evaluation, not the benchmark dataset itself.
- **No causal ground truth for diagnosis** — the 1.0 accuracy figure is
  strictly a class-matching measurement.
- **Small grids and sample sizes** — the decision-policy fragility check
  (§7) uses an 18-configuration grid; three benchmark uncertainty tasks
  are below their pre-registered minimum sample size.
- **Aggregate-vs-record-level evidence gap** — several real Phase 4
  findings (prediction, generalization) cannot currently be re-derived at
  record level from the Phase 5.2 dataset, and are marked `NOT_EVALUABLE`
  rather than scored from data that cannot support the score.

## 19. Related work positioning

This project does not claim to be a general-purpose LLM benchmark (GLUE/
SQuAD-style); its three agent-task families (arithmetic self-consistency,
sentiment, extractive QA) use deterministic templated corpora, disclosed
via an explicit `evidence_class` field on every relevant record. It
positions itself as a narrow, falsifiable capability-evaluation framework
for autonomous infrastructure agents, not a leaderboard competitor.

## 20. Reproducibility

Every phase has its own script(s) under `benchmarks/` or `scripts/` that
regenerate its results deterministically from a fixed seed. The Phase 5.6
release packages were independently clean-room reproduced (0 dependency
on this repository) with byte-identical results (modulo run metadata) to
the frozen Phase 5.4 reference.

## 21. Ethics and safety considerations

The safety gate (`RecoverySafetyGate.authorize()`) is called before every
execution; 0 incorrectly authorized actions across two independent
adversarial matrices (6-case and 16-case). `RecoveryCircuitBreaker` hard-caps
real recovery executions per `(workload_id, environment_id)`. No
production authentication, rate limiting, or deployment hardening exists
on the demo API — this is explicitly out of scope, not silently assumed
solved.

## 22. Phase 6 productization note

Phase 6 (this report is part of it) performed no new experiments, no
metric or threshold changes, and no label changes. It re-ran the frozen
Phase 5.4 benchmark once for verification and confirmed the
`capability_matrix`, `task_results`, and `ablation_results` were
byte-identical to the existing frozen reference run
(`experiments/results/phase5_benchmark_implementation/20260826T150824Z/`).
It also re-ran the full repository test suite; see
`experiments/results/phase6_finalization/<timestamp>/FINAL_SYSTEM_AUDIT.md`
for the exact current result and how it compares to the two previously
documented issue categories.

## 23. Limitations vs. future work

See the root `README.md`'s "Limitations vs. future work" section — this
report does not duplicate it to avoid the two documents drifting out of
sync; both are sourced from the same underlying evidence.

## 24. Data and code availability

- Code: <https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-> (MIT)
- Dataset: <https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-dataset> (CC BY 4.0)
- Benchmark: <https://huggingface.co/datasets/naishashetty/autonomous-ai-infrastructure-benchmark> (MIT)

## 25. Acknowledgments

This project's research discipline — measuring rather than assuming,
reporting negative results with the same weight as positive ones, and
gating every threshold behind a frozen protocol and leakage audit — is the
product of iterative self-auditing across Phases 1 through 5.6, documented
in full in `docs/MASTER_RECORD_CONTENT.md`.

## 26. Appendix: phase history table

| Phase | What it covers | Verdict |
|---|---|---|
| 1 | Audit of the two source prototypes | Concrete defects found, not assumed |
| 2 | Migration into one unified architecture | Failure-memory signal did not beat confidence alone (negative) |
| 3.1–3.6 | Synthetic reliability research, frozen | Confidence alone remained strongest signal at every axis tested |
| 3 real-data | Same questions on AgentRx/Alibaba GPU2020/AIOps 2020 | SUPPORTED (Alibaba), PARTIAL (AIOps), NOT EVALUABLE (AgentRx) |
| 4 (original, synthetic) | Failure memory (4.1) + pattern learning (4.2) | PARTIALLY SUPPORTED / INCONCLUSIVE |
| 4 (active, real-data) | Re-run of 4.1/4.2 + recovery learning (4.3/4.4) | PASS (4.1); INCONCLUSIVE (4.2); PASS — HYPOTHESIS NOT SUPPORTED (4.3, 4.4) |
| V1 (Gen 2) | Full closed-loop on Alibaba trace replay | Frozen, complete, 56/56 replay cases, 0 unsafe executions |
| 4.4/4.5 | Full loop connected | 668 passed / 17 skipped / 0 failed |
| 4.5 gap fixes | ML-trained prediction, persistent memory, widened taxonomy | 693 passed / 17 skipped / 0 failed |
| 4.5b | Scope-routed uncertainty; real AI/ML agent task | 735 passed / 17 skipped / 0 failed |
| 4.6–4.10 | Real HF models, calibrated retry, prediction re-evaluation, generalization | 808 passed / 3 failed (documented) |
| Post-P5 remediation (7 steps) | Systematic resolution of every named weakness | 837 passed / 0 failed |
| Post-P5 follow-ups (5 items) | 5 explicitly-recommended follow-ups | 837 passed / 0 failed |
| 5.1–5.6 | Dataset spec/construction, benchmark spec/implementation, finalization, external release | READY_FOR_PUBLICATION, published |
| 6 (this phase) | Productization: cleanup, diagrams, README, Docker, CI, demo, this report, final audit | See `PHASE6_FINALIZATION_REPORT.md` |

## 27. Citation

See [`CITATION.cff`](../../CITATION.cff) at the repository root.
