# Phase 3.6 — Diagnosis, Abstention & Recovery

**Status: COMPLETE.** This document is the Phase 3.6 deliverable.

Companion artifacts: [`configs/phase3_6_decision_recovery_protocol.json`](../configs/phase3_6_decision_recovery_protocol.json), [`benchmarks/phase3_6_{complementarity,decision_policy,diagnosis,recovery,leakage_audit,export_csv}.py`](../benchmarks/), [`experiments/results/phase3_6/`](../experiments/results/phase3_6/), [`tests/integration/test_phase3_6_*.py`](../tests/integration/).

## 1. Objective

Determine whether the available risk signals (calibrated confidence B,
Supervised Failure Risk F, and their simple combination) can safely
support failure diagnosis, abstention, and recovery decisions — and what
the actual consequences of those decisions are — without assuming the
answer is "yes."

## 2. Relationship to Phase 3.1–3.5

Phase 3.4 found F does not beat B (🟡 INCONCLUSIVE, frozen, not
revisited). Phase 3.5 found F's standing relative to B/C/A persists under
synthetic covariate-shift attacks (🟢 GENERALIZATION SUPPORTED, in the
narrow sense that F doesn't collapse relative to B). Phase 3.6 moves from
**prediction** to **decision, action, and outcome**: given these already
-established scores, does turning them into abstain/review/recover
decisions produce a safe, useful system? It reuses F, B, and Phase 3.5's
attack machinery entirely unmodified.

## 3. Frozen protocol

`configs/phase3_6_decision_recovery_protocol.json`, written before any
Phase 3.6 result was computed. Inherits Phase 3.1's seeds
`[1,2,3,4,5,42]`, primary seed `42`, coverage points, and bootstrap
settings unchanged. Defines: the complementarity model, tier thresholds,
cost model (with disclosed sensitivity ratios), diagnosis taxonomy/rule,
recovery policy, and acceptance criteria — all fixed before evaluation.

## 4. Complementarity experiment (3.6.1)

`CombinedRisk`: a 2-input `LogisticRegression(max_iter=1000,
random_state=seed)` on `[1-confidence, F.risk(...)]`, fit once per seed on
regime-2 data only (verified: fit array length == regime-2 size, zero
row-hash overlap with the test stream).

| Candidate | AUROC | AUPRC | AURC | ECE |
|---|---|---|---|---|
| B alone | 0.6599 [0.6185, 0.7013] | 0.3835 | 0.1941 | 0.0823 |
| F alone | 0.6548 [0.6159, 0.6938] | 0.3912 | 0.1972 | 0.0753 |
| **B+F combined** | **0.6593 [0.6176, 0.7010]** | 0.3962 | 0.1944 | 0.0789 |

Paired per-seed: BF − B AUROC mean = **−0.0006**, 95% CI **[−0.0058,
0.0046]** — includes zero. BF beats B on only **2/6** seeds.

**Interpretation: Case B — B+F ≈ B.** The combined model is
statistically indistinguishable from B alone on every metric. **F does
not add measurable incremental predictive information beyond calibrated
confidence on this benchmark.** This is consistent with, and sharpens,
Phase 3.4's inconclusive finding: it is not just that F fails to beat B,
but that even a simple, well-specified combination of the two collapses
back to B's own performance — the strongest evidence yet in this project
that F's signal substantially overlaps with B's.

## 5. Operational decision policy (3.6.2)

Four risk tiers (LOW/MEDIUM/HIGH/CRITICAL) map onto the existing
`Decision` enum (ANSWER/REVIEW/ABSTAIN/ABSTAIN respectively). Evaluated
policies: `no_risk_policy` (always ANSWER), and one policy each for B, F,
BF_combined.

## 6. Threshold methodology

Per (candidate, seed): `t_50`, `t_80`, `t_95` = the 50th/80th/95th
percentile of that candidate's risk score on **regime-2 data only**
(never test), reusing the already-frozen Phase 3.1 coverage points
(5/20/50%) as the tier cut fractions rather than inventing new
percentiles. A test-time score is tiered by comparison against these
frozen cutoffs. Verified by the leakage audit (section 11) that these
arrays never include a test-stream row.

## 7. Cost model

Explicitly a **synthetic research assumption**, not a real cost
measurement (see disclaimer in the protocol file):

| Outcome | Cost |
|---|---|
| ANSWER, correct | 0.0 |
| ANSWER, incorrect | 5.0 |
| REVIEW, correct | 0.2 |
| REVIEW, incorrect | 5.2 |
| ABSTAIN, would have been correct (false abstention) | 1.0 |
| ABSTAIN, would have been incorrect (correct catch) | 0.3 |

Ordering (`abstain_incorrect < abstain_correct < answer_incorrect`) is
fixed before evaluation. Sensitivity analysis re-runs with
`answer_incorrect` at 2×, 5× (base), 10× the false-abstention cost.

## 8. Abstention methodology (3.6.4)

Reuses `precision_recall_at_coverage` directly at the frozen 5/10/20/50%
coverage points, reframed: precision = 1 − false-abstention-rate at that
abstention level; recall = failure-recall-among-abstained.

## 9. Diagnosis methodology (3.6.3)

**Scope discipline first:** the clean benchmark alone provides no causal
labels — every ordinary failure has the same "cause" (Bayes error near
the decision boundary). What Phase 3.5's attacks provide, that the clean
benchmark does not, is **known ground-truth condition identity** (we
chose which corruption was applied). Phase 3.6's diagnosis task is
therefore **condition attribution** — "which known corruption mechanism
produced this failure" — not deep causal inference, and is described that
way throughout, not oversold.

Because attacks are only ever applied to held-out regimes 3/4 (by Phase
3.5's own design, to avoid leaking attack identity into fitting), there
is no attacked regime-2 data to train a diagnosis *classifier* on without
either fabricating training data or leaking test-condition labels. The
diagnosis method used is therefore a **deterministic, zero-fitting rule**
(`src/evaluation/diagnosis.py`), not a trained model — carrying no
leakage risk by construction:

1. ≥2 exactly-zero features → `feature_dropout`
2. else `mean(x²) > 2.0` → `feature_noise`
3. else → `clean`

The threshold (2.0) is derived from the generator's own algebra (clean
E[x²]=1.0, mild-noise E[x²]=1.25, severe-noise E[x²]=3.25) — fixed before
any result was computed. Evaluated on failure samples pooled across
clean + all 3 attack conditions, per seed.

## 10. Recovery methodology (3.6.5)

Three deterministic actions, eligible only for CRITICAL-tier samples
(top 5%):

- **Retry** (trigger: diagnosed `feature_noise`): re-roll a *new*
  noise realization for the same sample (`attack_ordinal + 100`,
  deterministic), re-score with the same candidate/thresholds.
- **Reconfigure** (trigger: diagnosed `feature_dropout`): re-score using
  **B alone**, ignoring F/BF, against B's own thresholds.
- **Rollback** (trigger: diagnosed `clean`, or retry/reconfigure failed
  to clear HIGH): ABSTAIN — the universal safe fallback.

**Explicit structural non-action:** for diagnosed `clean`, no retry is
attempted at all — the workload model and its input are both
deterministic, so retrying an unattacked, unchanged sample against a
frozen model is provably a no-op. Stated as a finding, not silently
skipped. `max_retries = 1`; no timeout is fabricated (offline synthetic
benchmark, not applicable). Compared against `no_recovery` and
`retry_only` (retry-if-diagnosed-noise, no reconfigure attempted at all)
baselines, for three acting candidates (B, F, BF).

## 11. Leakage audit

`benchmarks/phase3_6_leakage_audit.py` — **all 8 checks passed**:
`threshold_and_complementarity_fit_only_on_regime2`,
`cost_model_matches_frozen_protocol`,
`tier_assignment_does_not_use_ground_truth`,
`diagnosis_is_deterministic_and_unfit`,
`recovery_policy_no_fit_calls`,
`diagnosis_precedes_outcome_check_in_recovery`, `seeds_unchanged`,
`duplicate_samples_regime2_vs_test`. No STOP condition triggered.

## 12. Prediction results

See section 4 (B/F/BF AUROC/AUPRC/AURC/ECE) — no change from Phase 3.4's
frozen clean-benchmark numbers; B remains the strongest single signal.

## 13. Decision results

Cross-seed means at the base cost ratio (5.0):

| Policy | Unsafe action rate | Abstention rate | Expected cost | Utility retention |
|---|---|---|---|---|
| no_risk_policy | 0.2806 | 0.000 | 1.4028 | 1.000 |
| **B** | **0.2258** | 0.297 | **1.0602** | 0.703 |
| F | 0.2481 | 0.195 | 1.1966 | 0.805 |
| BF_combined | 0.2475 | 0.195 | 1.1934 | 0.805 |

**Sensitivity across cost ratios (2×/5×/10×):** at ratio 2.0, *every*
risk-based policy has HIGHER expected cost than doing nothing
(no_risk_policy = 0.561; B = 0.579; F = 0.598; BF = 0.596) — abstention
only pays off once missing a failure is costly enough. At ratios 5.0 and
10.0, B is cheapest of all four policies; F and BF beat no_risk_policy at
both of those ratios too. Per the protocol's pre-registered acceptance
rule (preference must hold at ≥2/3 ratios), **B, F, and BF are all
preferred over no-intervention — but B is the uniformly best-costing
policy at every ratio tested**, trading more abstention (29.7% vs.
19.5%) for a lower unsafe-action rate and lower cost than F/BF at every
tested ratio.

## 14. Abstention results

At 5% coverage (highest-risk 5% abstained): B → 43.6% precision / 8.0%
recall; F → 43.8% / 8.1%; BF → near-identical to F (all three numbers
reproduce Phase 3.4's clean-condition figures exactly, since this reuses
the same scores). No abstention policy is dramatically more effective
than another at catching failures early — consistent with section 4's
complementarity finding.

## 15. Diagnosis results

Pooled across all 6 seeds (32,000 failure samples):

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| clean | 0.393 | 0.928 | 0.552 | 5,050 |
| feature_noise | 0.937 | 0.425 | 0.585 | 12,585 |
| feature_dropout | **1.000** | **1.000** | **1.000** | 6,363 |

Overall accuracy **0.683**, macro F1 **0.712**.

**Reading this honestly:** dropout is perfectly diagnosable (it's a
deterministic, unambiguous corruption). Feature-noise recall is only
42.5% — as predicted a priori (E[x²]=1.25 for mild noise heavily
overlaps clean's E[x²]=1.0), most **mild**-noise failures are
misdiagnosed as `clean`, dragging "clean" precision down to 0.393 (most
things the rule calls "clean" are actually misdiagnosed noise failures).
This is exactly the limitation the frozen protocol predicted before
running any evaluation — not a surprise, and not concealed.

## 16. Recovery results

Recovery-eligible (CRITICAL-tier) population, pooled across seeds and all
4 conditions:

| Acting candidate | Attempt rate | Success rate | Failure rate |
|---|---|---|---|
| B | 14.0% [10.7%, 17.3%] | 54.7% | 45.3% |
| F | 23.4% [17.7%, 29.2%] | 55.7% | 44.3% |
| BF | 24.4% [17.1%, 31.7%] | 55.0% | 45.0% |

**`retry_only` and `diagnosis_gated` produced numerically IDENTICAL
results for all three acting candidates, every seed.** Investigated
directly (not assumed): **zero** feature_dropout-diagnosed CRITICAL
samples were ever recovered by reconfiguration, for any acting candidate,
in any seed checked. Verified structurally: **reconfiguring to B alone
does not help under feature_dropout, because B's calibrated confidence is
computed from the SAME corrupted context and is equally elevated** — B is
not an independent fallback signal here, it shares the corruption's
effect. This is a genuine negative result about the reconfigure action
specifically, not a bug (confirmed: `check_diagnosis_precedes_outcome_
check_in_recovery` passes; the branch is exercised, just never succeeds).

Retry (for feature_noise) recovers 14–24% of the CRITICAL population
depending on acting candidate, but only about **55% of recoveries are
actually correct** — retry is close to a coin flip once it does clear the
risk threshold.

## 17. Safety analysis

- **No recovery action ever converts a would-have-succeeded sample into a
  failure** — recovery only changes ABSTAIN into ANSWER/REVIEW, it never
  changes what the underlying (already frozen) workload model would have
  predicted. The only safety risk recovery introduces is **accepting a
  sample that is still actually wrong** (recovery_failure_rate,
  ~44–45%), i.e. exactly the risk category the frozen protocol requires
  reporting as "unsafe recovery."
- Reconfigure is safe by construction here (it never actually recovers
  anything, so it cannot introduce a new failure) — but that also means
  it provides zero benefit, which is itself worth flagging as wasted
  complexity, not a success.
- Retry's ~45% failure-rate-among-recoveries means **roughly 1 in 2
  "recovered" decisions under this policy is actually still a failure
  that would have been safely caught by rollback instead.** This is the
  single most important safety finding of Phase 3.6: **retry-based
  recovery, as currently defined, is not obviously safer than simply
  abstaining on every CRITICAL case.**

## 18. Utility analysis

Recovery's utility_retention_after_recovery (fraction of the CRITICAL
population it manages to answer instead of abstaining) ranges 14–24%
depending on acting candidate — a real but modest utility gain, bought at
the safety cost in section 17. B's lower recovery-attempt-rate (14.0%
vs. F/BF's ~23–24%) reflects B's smaller CRITICAL population to begin
with (B abstains more broadly per section 13), not a difference in
retry's per-attempt effectiveness (success rates are within 1–2 points of
each other across all three acting candidates).

## 19. Failure cases

- **Reconfigure recovering 0/N samples across every check performed** —
  reported prominently, not smoothed into an aggregate "recovery works"
  number.
- **Retry's ~45% failure rate** — nearly half of "successful" (tier
  -reducing) retries are still wrong. A system trusting retry's tier
  outcome alone, without checking the actual result, would be unsafe
  close to half the time on this subset.
- **Diagnosis misdiagnosing the majority of mild-noise failures as
  `clean`** — meaning under the full recovery policy, most mild-noise
  CRITICAL failures never reach the retry branch at all; they roll back
  via the `clean` branch instead (a safe outcome, but not the intended
  diagnosis-routing behavior).
- **At cost ratio 2.0, every intervention policy costs more than doing
  nothing** — reported, not hidden behind the base-ratio-5.0 headline
  number.

## 20. Limitations

- The cost model is a labeled synthetic assumption; no claim is made
  that its specific numbers reflect any real deployment's costs — only
  the qualitative ranking behavior (do interventions help, and under what
  ratio) is meant to generalize as a methodology.
- Diagnosis is condition-attribution against self-generated ground truth,
  not causal inference in an operational sense; it cannot distinguish
  finer-grained real-world failure causes this benchmark cannot
  represent.
- Recovery's "retry" and "reconfigure" actions are specific to this
  benchmark's mechanics (re-rollable synthetic noise; a second risk
  signal computed from the same corrupted input) and are not directly
  transferable design patterns to a real system without re-justification.
- Six seeds remains a small cross-seed sample; several recovery CIs
  (especially B's, with the smallest eligible population) are wide.

## 21. Threats to validity

- B and F/BF share the same underlying calibrator, which is why
  reconfigure-to-B provides no protection under feature_dropout — this is
  a structural property of this specific architecture, not a general law
  about confidence-based fallbacks.
- The diagnosis rule's threshold was derived from exact knowledge of the
  attack's construction (this project generated it); a real anomaly
  -detection rule would not have this privileged information.
- Recovery evaluation reuses Phase 3.5's synthetic attack conditions
  exclusively; no validation against any other corruption family was
  performed.

## 22. What Phase 3.6 establishes

- **F does not add measurable incremental value beyond calibrated
  confidence**, even under the most permissive test available (a
  simple, dedicated 2-feature combiner) — the clearest, most direct
  evidence in this project's history against F's incremental utility.
- **Risk-based decision policies (B, F, or BF) reduce expected cost and
  unsafe-action rate relative to no intervention**, but only once missing
  a failure is assumed sufficiently more costly than an unnecessary
  abstention (≥5× in this study) — the benefit is not unconditional.
- **B alone is the most cost-efficient decision policy tested** at every
  cost ratio evaluated, consistent with section 4's complementarity
  finding.
- **Diagnosis (condition attribution) is possible but imperfect** on this
  benchmark: dropout is perfectly detectable, feature-noise is
  detectable mostly at severe magnitude, mild-severity corruption is
  frequently indistinguishable from ordinary clean failures.
- **Retry-based recovery is real but risky** (~55% success among
  recoveries); **reconfigure-based recovery, as currently designed,
  provides zero measured benefit** because its fallback signal (B) is
  not independent of the corruption affecting the primary signal.

## 23. What Phase 3.6 does NOT establish

- That F is useless in general — only that it adds no measured value on
  this specific synthetic benchmark, under this specific combination
  method.
- That any specific cost ratio (2×, 5×, or 10×) is the "correct" one for
  any real system — these are labeled research assumptions.
- That the diagnosis taxonomy or recovery actions generalize beyond this
  benchmark's specific, self-generated attack mechanisms.
- That retry or reconfigure, as implemented, are safe or effective
  recovery strategies for a real deployed system — retry's near-50%
  failure-among-recoveries rate argues directly against that.
- Any form of production readiness, deployment safety, or autonomous
  reliability.

## 24. Formal decision

# 🟡 INCONCLUSIVE

Some components work as intended and produce genuinely useful,
honestly-measured evidence (decision policies reduce cost/unsafe-action
rate under a defensible cost assumption; dropout diagnosis is reliable;
retry recovers a meaningful fraction of CRITICAL cases). But the
evidence is **not sufficient for safe autonomous decision authority**:
complementarity is now more clearly negative than before (Case B, not
just inconclusive), reconfigure-based recovery provides zero measured
benefit, and retry-based recovery is wrong on roughly 45% of the cases it
"recovers" — a failure rate too high to trust unsupervised. **Calibrated
confidence (B) alone remains at least as good as, and operationally
cheaper than, every more complex alternative tested in this phase.**

**Is autonomous authority justified?** **No.** Per the frozen gate
(section 33 of the brief), Phase 3.6 being 🟡 does not itself authorize
anything, and even a 🟢 would not have. F/BF are not shown to add
value over B; retry's failure rate is a direct safety concern;
reconfigure does not work. Any authority granted must remain bounded,
reversible, monitored, and auditable — none of that infrastructure exists
yet, and this phase does not build it.

**What must happen next:** (1) given B alone is now the leading candidate
at every measured axis, seriously reconsider whether F/BF-based
components are worth their added complexity; (2) if retry-based recovery
is pursued further, its near-50% failure-among-recoveries rate must be
addressed (e.g. requiring a second confirmation signal after retry)
before any real trust is placed in it; (3) reconfigure needs a genuinely
independent fallback signal, not B, to have any chance of helping under
feature_dropout; (4) no further phase should proceed to deployment,
production infrastructure, or autonomous control on the strength of this
result.
