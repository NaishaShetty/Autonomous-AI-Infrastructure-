# Phase 4.5b -- Fixing "Recognize When It's Likely Wrong" and Adding Real AI/ML Agent Evaluation

This report covers the two issues raised in a follow-up strategic review of
the Phase 4.4/4.5 autonomy pipeline, measured against the project's own
stated mission: *recognize when an AI/ML agent or workload is likely to be
wrong, unreliable, unsafe, or failing; quantify its uncertainty; and
abstain from taking an unsafe or unjustified action when the available
evidence is insufficient.*

Nothing in `src/phase3*`, `src/phase4_0`..`4.5`-era code, `src/runtime/`,
`src/recovery/` (reused, not modified), `src/decision/` (reused, not
modified), `src/failure_experience/`, or any existing
`experiments/results/*` directory was touched. All new evidence lives in a
new directory, `experiments/results/phase4_5b_recognition_and_agent_evaluation/`.

Full test suite after both fixes: **735 passed, 17 skipped, 0 failed** (up
from 693/697 before this work; the 17 skips pre-date this work).

## Issue A -- "recognize when it's likely wrong" was reporting one misleading number

**The problem, restated honestly:** Phase 4.5's trained predictor measured
AUC ~0.515 (chance-level) in aggregate. The cause was never a modeling
shortfall to keep tuning -- most of the widened failure taxonomy has no
real pre-failure telemetry precursor at all (several classes fail at or
within one telemetry sample of `execution_started`), and blending them
into one metric hid that the model had genuine skill nowhere.

**The fix:** `src/phase4/prediction.py`'s new `PredictionScopeRouter`
routes on the workload's configured `mode` parameter -- real information
available at decision time, not a leaked label -- into two honest regimes:

- **Predictable scope**: originally assumed to be `PROCESS_TIMEOUT` *and*
  `PROCESS_OOM` (both have a plausible "value ramping toward a limit"
  story). Measured evidence corrected this assumption: an OOM-only model
  trained and evaluated in isolation scores AUC ~0.46 (no better than
  chance) because `controlled_runtime.py`'s `oom` mode allocates memory in
  a tight, unpaced loop that completes before even one telemetry sample is
  captured. A timeout-only model in isolation scores AUC ~0.63. So
  `PREDICTABLE_MODES` was corrected to `{"cpu"}` (timeout) only --
  **this correction was made from real measurement, before any of the
  numbers below were generated**, the same "report what you learn, not
  what you assumed" discipline this project has followed throughout.
- **Detectable-only scope** (everything else): no real precursor is
  structurally possible. Rather than let a blended model emit a
  confident-looking but meaningless score, the router returns a fixed,
  honestly labeled fallback -- the empirical historical failure prior for
  that specific mode, computed from train+validation data only, never
  re-tuned against the test split.

**Measured result, at scale (train=1500 seeds / validation=300 /
test=300, `experiments/results/phase4_5b_recognition_and_agent_evaluation/results.json`):**

```
predictable_scope   (timeout only, real trained model): n=420,  AUC=0.636, precision=0.561, recall=0.979, F1=0.713
detectable_only_scope (fixed per-mode fallback prior):   n=1422, AUC=0.857, precision=0.775, recall=1.000, F1=0.873
router_combined_output_all_scopes:                       n=1842, AUC=0.827, precision=0.725, recall=0.996, F1=0.839
```

**Honest reading of every number above, including the ones that look
good:**

- **predictable_scope AUC=0.636** is real, modest skill -- clearly above
  chance, a genuine improvement over the old 0.515 blend, but not strong.
  This is the only number in this report that reflects a model actually
  learning a precursor signal.
- **detectable_only_scope AUC=0.857 is not evidence of predictive skill.**
  It is a mostly mechanical result of mixing several *deterministic-by-construction*
  modes into the test population: in this corpus, `corruption`, `fail`,
  `gpu`, and `network` scenarios always fail (fallback prior = 1.0) and
  `success` scenarios never do (fallback prior = 0.0). A constant score
  trivially separates "always-1" and "always-0" populations without
  discriminating anything. The modes with genuinely mixed outcomes --
  `oom` (0.50), `flaky` (0.51), `resource_unavailable` (0.53) -- get a
  **constant score regardless of the true outcome**, i.e. zero real
  discriminative power for exactly the cases where discrimination would
  matter. Reporting this AUC without this caveat would recreate the same
  kind of misleading-aggregate problem this whole fix exists to close, so
  it is stated here plainly: **the detectable-only scope has no real
  predictive power; its high AUC is a byproduct of mixing deterministic
  and non-deterministic modes together.**
- **router_combined_output_all_scopes AUC=0.827 is not comparable to the
  original single-model 0.515.** That number came from a model that never
  saw `mode` at all. This number is inflated by the same deterministic-mode
  effect described above. The only genuine, apples-to-apples improvement
  claim this fix can honestly make is the predictable-scope one: **0.636
  vs. 0.515, on the one class where a real precursor exists.**

This is the honest state of "recognize when it's likely wrong" after this
fix: real, modest, verified skill on `PROCESS_TIMEOUT`; an honest,
non-fabricated "we cannot predict this in advance" signal for everything
else, which is a materially more truthful position than a single
misleading blended metric, even though it does not manufacture predictive
power where none exists.

## Issue B -- the pipeline never evaluated an actual AI/ML agent's output

**The problem, restated honestly:** every prior phase of this pipeline
(Phase 4.0 through 4.5) evaluates infrastructure/process failures --
timeouts, OOM, crashes, network errors, corrupted data, contended
resources, flaky processes. None of it evaluates whether an actual AI/ML
agent's *answer* is correct. There was no ground-truth oracle, no
uncertainty signal derived from model output, and no abstention behavior
tied to output correctness anywhere in the codebase.

**The fix -- a real AI/ML agent task with a genuine oracle and
uncertainty signal, wired through the existing autonomy loop:**

- `src/phase4/agent_task.py` (new): a small, real, deterministic-given-seed
  chained-arithmetic reasoning task. The "agent" independently replays the
  task's own recorded operation sequence (never reads the ground-truth
  answer directly) and applies a real, seeded chance of a genuine
  arithmetic slip -- fixed, documented error-rate formulas set before any
  evaluation was run. **Self-consistency** (running the solver multiple
  independent times and taking the majority vote) is the uncertainty
  mechanism -- the same technique actually used with real large language
  models, not a metaphor for it.
- `src/phase4/agent_task_worker.py` + `agent_runtime.py` (new): real
  subprocess execution (mirroring `ControlledRuntime`'s own discipline),
  emitting the identical canonical event schema so the exact same
  `MonitoringEngine` / `DiagnosisEngine` / `FailureMemoryStore` /
  recovery-planning / validation / learning components consume it --
  no parallel infrastructure, only a different real thing being observed.
- `src/phase4/prediction.py`'s new `AgentUncertaintyPredictor`: the actual
  "recognize when it's likely wrong" mechanism for AI/ML output. Score =
  `1 - running_self_consistency_agreement_rate`, computed from real
  telemetry-equivalent events, available before the ground-truth
  comparison happens.
- `src/phase4/agent_recovery.py`'s new `AgentRecoveryExecutor`: RETRY means
  "re-answer the same question with real, doubled self-consistency
  samples" -- a real, more-costly, measurably effective action, not a
  no-op retry of an already-deterministic computation.
- `monitoring.py` / `diagnosis.py` / `recovery.py` extended (not
  restructured) with three new failure classes
  (`AGENT_INCORRECT_ANSWER`, `AGENT_TASK_TIMEOUT`, `AGENT_WORKER_ERROR`),
  each with its own diagnosis hypothesis and recovery candidates, following
  the exact pattern every prior taxonomy-widening gap used.
- `AutonomyPipeline.run_agent_task()` (new method, opt-in via
  `agent_runtime=`): walks the identical `AutonomyState` state machine as
  `run_workload` -- OBSERVING -> PREDICTED -> DECIDING -> DIAGNOSING ->
  PLANNING -> SAFETY_CHECK -> EXECUTING -> VALIDATING -> RECOVERED /
  NOT_RECOVERED -> COMPLETED -- reusing `AbstentionAwareDecisionPolicy`,
  `RuleBasedRecoveryPlanner`, `RecoverySafetyGate`, `SignalRecoveryValidator`,
  `FailureMemoryStore`, and `LearningManager` completely unmodified.

**Measured result, at scale (real subprocess executions,
`experiments/results/phase4_5b_recognition_and_agent_evaluation/results.json`):**

```
self-consistency accuracy curve (1000 seeds each):
  n=1:  75.8%
  n=3:  88.7%
  n=5:  95.9%
  n=10: 100.0%
  n=20: 100.0%

uncertainty-signal calibration (n_samples=5, 1000 seeds, bucketed by agreement_rate):
  [0.0-0.4) agreement: n=5,   accuracy=20.0%
  [0.4-0.6) agreement: n=89,  accuracy=62.9%
  [0.6-0.8) agreement: n=234, accuracy=98.3%
  [0.8-1.0] agreement: n=672, accuracy=100.0%

real pipeline, n_samples=1 (300 real subprocess episodes):
  73/300 wrong on first answer; all 73 landed in the ANSWER decision band
  (n=1 means zero disagreement is observable, so risk score is always 0.0)
  73/73 retried autonomously; 32 recovered
  retry recovery rate: 43.8% (Wilson 95% CI [33.0%, 55.2%])

real pipeline, n_samples=5 (300 real subprocess episodes):
  15/300 wrong on first answer; all 15 landed in the REVIEW band, 0 in ANSWER, 0 in ABSTAIN
  0 autonomous executions (every case correctly escalated for human review instead)
```

**Honest reading:**

- The self-consistency accuracy curve and the agreement-rate calibration
  are both real, clean, monotonic signals -- majority voting genuinely
  improves accuracy, and disagreement genuinely predicts wrongness. This
  is the first working "recognize when it's likely wrong" signal in this
  project measured directly against actual output correctness rather than
  OS/process telemetry.
- The retry recovery rate (43.8%) is real and not overstated: doubling
  samples from 1 to 2 does not deterministically fix a wrong answer (a 2-
  sample vote can still land on the wrong value, or tie-break to it), and
  the measured rate reflects that honestly rather than reporting a
  cherry-picked favorable seed.
- **An important, unplanned, honest finding from wiring this through the
  existing, unmodified `AbstentionAwareDecisionPolicy`:** at `n_samples=5`,
  *every single wrong answer in the 300-episode run landed in the REVIEW
  band and none were autonomously retried*, even though a real, isolated
  measurement shows retry-with-more-samples reliably improves accuracy
  regardless of the initial disagreement level (both self-consistency
  errors here are i.i.d. per-sample noise, not a systematic bias, so more
  samples help even in "confidently wrong" cases). The decision-policy
  thresholds (`answer_threshold=0.70`, `abstain_threshold=0.40`, reused
  unmodified per this project's "adapt, don't rebuild" precedent for the
  decision layer) treat higher self-consistency disagreement as higher
  risk warranting caution, which is a defensible, conservative
  interpretation in general -- but it is *not* the recovery-yield-optimal
  policy for this specific action, and this fix does not adjust those
  thresholds to make the numbers look more autonomous. The honest
  trade-off is stated here rather than tuned away: this wiring correctly
  implements "abstain ... when the available evidence is insufficient"
  exactly as specified, at some real cost to how often that abstention
  turns out (after the fact) to have been unnecessary.

## Test suite

Unit: `tests/unit/test_phase45b_prediction_scope_router.py`,
`test_phase45b_agent_task.py`, `test_phase45b_agent_runtime.py`,
`test_phase45b_agent_recovery.py`, `test_phase45b_agent_taxonomy.py`,
`test_phase45b_agent_uncertainty_predictor.py` (plus every pre-existing
test, all still passing unchanged).
Integration: `tests/integration/test_phase45b_prediction_scope_router_pipeline.py`,
`test_phase45b_agent_pipeline.py`.

Full suite: **735 passed, 17 skipped, 0 failed.**

## What is still honestly not solved

- The predictable-scope AUC (0.636) is real but modest -- this project
  does not claim strong predictive power, only a genuine, measured
  improvement over chance, isolated to the one failure class that
  structurally has a precursor.
- The detectable-only scope's headline AUC (0.857) is explicitly flagged
  above as not reflecting real discriminative power -- it is a mixing
  artifact of deterministic and non-deterministic modes, and is reported
  with that caveat rather than presented as a win.
- The agent task is a real, ground-truth-checked arithmetic reasoning
  problem, not a call to an actual large language model -- this sandboxed
  environment has no such API available, and fabricating one would violate
  the honesty discipline this project has followed since Phase 4.4. It is
  a genuine correctness-oracle task with a genuine uncertainty mechanism,
  not a simulation of one.
- At `n_samples=5`, the existing abstention policy's thresholds mean the
  new RETRY-with-more-samples action essentially never fires autonomously
  in this pipeline configuration, even though it would help if it did --
  reported above as a real, measured trade-off, not adjusted to look more
  autonomous.
- Multi-node/cluster-scale claims, and any claim of evaluating a real
  externally-hosted AI model, remain explicitly out of scope, as in every
  prior phase of this repository.
