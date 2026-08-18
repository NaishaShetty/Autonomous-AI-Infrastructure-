# Active Phase 4.4 — Sequential Recovery with Abstention: Frozen Protocol

Status: FROZEN — do not edit after implementation begins. Any change after
this point requires explicit written justification appended to a "deviations"
section at the bottom, never a silent edit.

## 1. Motivation

Phase 4.3 established that a single-step, outcome-aware learned policy does
not meaningfully beat a strong fixed-priority heuristic (effect size
+0.0111 vs. a required +0.15, not significant, robust across 5 independent
seeds). The identified reason: a single decision point gives a static rule
everything it needs — there is no history for a learner to exploit that the
rule can't already encode.

Phase 4.4 tests whether that changes when recovery becomes sequential: the
policy acts, observes a noisy intermediate outcome, and can act once more —
the minimal condition under which a fixed rule cannot condition on "the
first action already failed," but a learned policy can.

## 2. Research question and hypotheses (FROZEN)

**RQ:** Given a controlled, frozen set of two-step failure-recovery
episodes, with abstain/escalate available at each step, does a
history-aware recovery policy achieve a higher validated success rate than
the strongest fixed two-step baseline, without exceeding the safety
threshold?

**H4 (primary):** The proposed sequential policy has a higher validated
recovery success rate than the strongest fixed-policy baseline, with a
minimum meaningful effect of **0.15** (unchanged from H3, for direct
comparability) and statistical significance (paired McNemar on identical
test episodes, alpha=0.05, Holm correction across the hypothesis family as
in 4.3).

**H4-SAFETY:** Unsafe-action rate <= 0% across the frozen test set (same
threshold as H3-SAFETY).

**H4-UTILITY:** Mean recovery utility (cost- and latency-adjusted, same
construction as 4.3) of the proposed policy >= the strongest baseline's.

**H4-ABSTENTION:** Restricted to the dependency_failure family (the
"unrecoverable tail," where 4.3's oracle itself only reached ~28% success):
the proposed policy's abstain/escalate rate is higher than a fixed policy
with no abstention mechanism, AND overall utility on the other three
families is not reduced relative to a no-abstention variant of the same
policy (i.e., abstention must not be "free" — it has to actually trade
off against attempting recovery, or the test is vacuous the way 4.3's was).

**H4-ABLATION (SingleStepEmpirical):** The two-step proposed policy beats a
version of itself that is identical but forced to terminate after step 1
(i.e., it gets one attempt, not two). This isolates whether any H4 win is
from genuine history-conditioning or merely from having more attempts.
Frozen threshold: same 0.15 minimum effect, informational rather than a
pass/fail gate on the overall Phase 4.4 verdict, but must be reported
alongside H4 in the final results regardless of outcome.

## 3. Environment design (FROZEN)

- **Step budget: 2.** (act -> observe -> act -> validate). Chosen
  deliberately as the minimal sequential setting, given 4.3's own finding
  that finer-grained context fragmentation hurt performance — 2 steps
  tests the core hypothesis without inheriting that problem. Raising this
  to 3 is an explicit candidate for a *future* phase only after 2-step
  results are in, not a mid-experiment escalation.
- **Per-step observation:** ternary signal after step 1's action —
  `improved` / `no_change` / `worsened`. Noise level (probability the
  signal misrepresents the true post-action state) is NOT fixed here — it
  is determined by the VALIDATION-only sweep in Section 7 before test-set
  generation, exactly as 4.3 froze `min_evidence` via a VALIDATION sweep.
- **Terminal conditions:** success at step 1 (episode ends early), success
  at step 2, exhausted 2-step budget (failure), or abstain/escalate at
  either step (its own outcome class, scored per H4-ABSTENTION).
- **Action vocabulary:** unchanged from 4.3 — retry / restart / rollback /
  reconfigure / escalate_to_human / abstain / force_restart.
  `force_restart` remains the sole unsafe action. No new actions are
  introduced in 4.4.
- **Failure families:** unchanged from 4.3 — resource_exhaustion,
  transient_failure, configuration_failure, dependency_failure.

## 4. Decision-time information boundary (FROZEN)

`DecisionContext` at step 2 = everything available at step 1 (scenario ID,
family, noisy symptom/severity, workload type, candidate actions) PLUS the
step-1 action taken and its noisy observation. It must NOT contain: hidden
cause, this episode's final outcome, step-2's outcome before it happens, or
any information from other episodes. Enforced via strict schema validation
(extra fields rejected, not merely ignored). A contamination test —
constructing a `DecisionContext` that attempts to smuggle hidden-cause or
future-outcome fields — must be written and confirmed to fail/reject before
any policy code is written against this schema.

## 5. Baselines (FROZEN)

1. **FixedPrioritySequential** — a hand-written rule that DOES condition on
   the step-1 observation (e.g., "if step 1 = worsened, escalate on step
   2"; "if step 1 = improved, retry the same action"). This must be
   designed with the same seriousness 4.3 gave FixedPriorityPolicy — it is
   the thing H4 has to beat, not a strawman. Author this rule using domain
   reasoning only, before looking at any generated data.
2. **RandomValidSequential** — random safe action at each step,
   independent of history.
3. **Oracle** — hidden-ground-truth reference upper bound. Not a competing
   policy.
4. **SingleStepEmpirical (ablation baseline)** — Phase 4.3's trained
   EmpiricalRecoveryPolicy, applied once at step 1, then forced to
   terminate regardless of outcome (no step 2). Used for H4-ABLATION.

## 6. Proposed policy (FROZEN design, not FROZEN hyperparameters)

Start from Phase 4.3's `EmpiricalRecoveryPolicy` retrieval hierarchy,
extended with step-1 action and observation as additional context keys in
the hierarchical backoff (family+symptom+severity+step1_action+step1_obs+
action -> ... -> family+action, same Laplace-smoothing approach as 4.3). Do
not introduce RL, sequence models, or neural architectures for this phase —
if this simple extension ties its baseline the way 4.3's did, that is
itself the finding, exactly as it was last time.

## 7. Observation-noise calibration sweep (FROZEN procedure, values TBD on VALIDATION only)

Before test-set generation, sweep the step-1 observation's false-signal
rate over **{0.05, 0.10, 0.20, 0.30, 0.40}** on VALIDATION only. For each
candidate rate, measure: (a) whether FixedPrioritySequential and the
proposed policy are distinguishable at all (a rate so high both baselines
collapse to chance is unusable), and (b) whether a trivial rule
("if worsened, escalate; else repeat") gets near-ceiling performance (a
rate so low it trivializes the problem is equally unusable). Select the
rate that maximizes the VALIDATION-set performance gap between a naive
step-1-only baseline and a rule that genuinely uses the step-1 observation
— i.e., the rate at which the observation is informative enough to matter
but not enough to be a lookup table. Freeze the selected rate into
`observation_noise_rate` in the companion JSON config before generating
TEST. This sweep, and only this sweep, may touch VALIDATION before TEST
generation; it may never touch TEST.

## 8. Dataset, splits, sample size

- Disjoint seed-range splits per arm, same methodology as 4.3 (0 overlaps,
  0 collisions required, audited the same way).
- Sample size: re-run the two-proportion power calculation
  (`src/recovery/sample_size.py`-equivalent) using the same p1/p2/alpha/
  power framing as 4.3 (p1=0.55, p2=0.40, alpha=0.05, power=0.80) as a
  starting point — recompute rather than reuse 4.3's literal 173/arm
  number, since the McNemar variance structure for a 2-step outcome may
  differ. Report the recomputed minimum and set TEST size to at least
  3-4x that floor, as 4.3 did.
- TRAIN episodes resolved via uniform random exploration over the 2-step
  action space (both steps), producing genuine 2-step historical
  experience for the empirical learner. VALIDATION and TEST generated as
  scenario-only manifests, resolved only at evaluation time (unchanged
  principle from 4.3).

## 9. Leakage audit (extends 4.3's 9 checks; FROZEN)

All 9 of 4.3's checks, adapted for 2 steps, PLUS:
10. **Cross-step leakage**: step-1 `DecisionContext` cannot see step-2
    action/observation/outcome (structurally impossible by construction,
    verified by a dedicated test).
11. **Path-normalization correctness from commit 1**: the historical-hash
    baseline file uses `.as_posix()` keys from the start (the bug found and
    fixed in 4.3 must not be reintroduced here).
12. **Non-vacuous first baseline**: the frozen-directory hash baseline
    records `baseline_commit` explicitly on first write; a bare
    "no prior baseline, wrote snapshot" is documented as informational
    only, not a pass, matching the fix applied to 4.3's audit script.

## 10. Explicit prohibitions (standing policy, carried forward)

Do not lower the 0.15 threshold after seeing results. Do not change the
observation-noise rate after TEST generation. Do not swap the frozen split
for a more favorable one. Do not add model complexity (RL, sequence
models, neural nets) merely because the simple extension ties its
baseline — report the tie as a finding, the same way 4.3 did. Do not
claim real-world validity for what is controlled/synthetic evidence. Do
not modify Phase 4.2 or 4.3's frozen artifacts, thresholds, or results.

## Deviations log (append-only; empty at freeze time)

(none yet)
