# Follow-up 5 — OOM Operating-Point Follow-up (>=2 Pre-Outcome Samples Subset)

Script: `scripts/run_followup5_oom_operating_point.py`. Raw results:
`raw/followup5_oom_operating_point.json`.

## Method — frozen predictor, no redesign

Uses the exact same `oom`-family predictor Step 3 used
(`prediction_features_v3.py`'s 6-feature `full_v3` interface,
`StandardScaler`+`LogisticRegression`), the same 3 pre-registered
replicate seed ranges as `protocol/P3_STEP3_PROTOCOL.md`. The model and
its `calibrate_threshold`-selected threshold are fit **once per
replicate, on the full `oom` family population** (train+validation) —
identical to how Step 3 fit its pooled/split evaluations. Only the TEST
evaluation is then split into the `>=2 pre-outcome samples` subset and the
`0-1 samples` control subset; the threshold is never re-selected using
either subset's outcomes, and no new feature or model was introduced.

## Results (mean ± population std across 3 replicates)

| Subset | AUROC (real) | AUROC (shuffled) | AUPRC | Precision | Recall | Specificity | False alarm rate | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|
| `>=2 samples` (sufficient observability) | 0.780 ± 0.096 | 0.625 ± 0.093 | 0.986 | 0.959 | 0.891 | **0.179 ± 0.254** | **1.00 ± 0.00** | 0.200 | 0.330 |
| `0-1 samples` (control) | 0.627 ± 0.032 | 0.594 ± 0.045 | 0.977 | 0.962 | 0.925 | **0.167 ± 0.236** | **1.00 ± 0.00** | 0.166 | 0.281 |

Both subsets' real AUROC exceeds their own shuffled control by more than
one pooled std in this run (`>=2 samples`: 0.780 vs. 0.625+0.093=0.718;
`0-1 samples`: 0.627 vs. 0.594+0.045=0.639, a much narrower margin) — the
mechanical ranking-only check would nominally call both "SIGNAL," with the
`>=2 samples` subset's separation noticeably cleaner, consistent with
Step 3's own finding and the P3 audit's underlying hypothesis (a real
telemetry precursor exists specifically when at least 2 samples were
observed before the outcome).

## The operating-point question this follow-up exists to answer

**Answer: NO — the `>=2 samples` subset is NOT operationally usable at
its calibrated threshold. False alarm rate is 1.00 in all 3 replicates,
identical to the pooled `oom` result Step 3 already disqualified.**
Specificity averages only 0.179 (i.e., roughly 82% of healthy runs in this
subset are still incorrectly flagged at the calibrated operating point).
This is the same textbook always-fires pattern found throughout Step 3
and every other follow-up in this phase: `class_weight="balanced"` +
F1-maximizing threshold selection chooses an extremely permissive
threshold whenever the classes are imbalanced (as `oom` genuinely is —
very few negative/non-failing runs relative to positive/failing ones in
this corpus), and a high nominal AUROC ranking gap over a shuffled control
does not, by itself, imply the resulting calibrated classifier is useful
at the one threshold it would actually operate at.

**The `0-1 samples` control subset shows the same always-fires pattern**
(false alarm rate also 1.00, specificity 0.167) — but with a much weaker
real-vs-shuffled AUROC separation, consistent with the audit's original
"no temporal window" hypothesis for this subset (the underlying ranking
signal is close to chance to begin with, so there is even less reason to
expect a usable classifier here).

## Is the >=2-sample signal a "plausible ranking signal" or "merely a ranking artifact"?

**Both, in the precise sense the followups task asks to distinguish.**
The AUROC-vs-shuffled-control separation is real and replicates across
all 3 independent seed-range replicates (individual replicate AUROCs:
0.914, 0.694, 0.733 — all three above their own replicate's shuffled
control) — this is a genuine ranking signal, not noise, and Step 3's
"PLAUSIBLE, UNCONFIRMED USEFUL PREDICTOR" characterization for this
subset's ranking quality is confirmed, not overturned, by this follow-up.
**But ranking quality and operating-point usability are different
properties, and this follow-up's whole purpose was to check the second
one, which Step 3 explicitly left unchecked.** At the one threshold this
predictor would actually be deployed at (the F1-maximizing threshold
selected on the calibration split, never touched using test outcomes),
it fires on essentially every healthy run — an always-fires classifier,
not a usable early-warning system, regardless of its ranking quality.

## Verdict

**`oom` `>=2-sample` subset: NOT VALIDATED at its calibrated operating
point — always-fires (false_alarm_rate=1.00, specificity=0.18), despite a
real, replicated ranking-quality edge over its shuffled control.**
**`oom` `0-1-sample` subset (control): NOT VALIDATED — same always-fires
problem, on a weaker underlying ranking signal, consistent with the
audit's "no temporal window" hypothesis.**

Per the followups task's explicit instruction, this negative result is
recorded as final: **no further feature/model/threshold iteration was
performed on either `oom` subset after this result.** The predictor and
its features are frozen, exactly as instructed, and this follow-up does
not propose a redesign — it answers the operating-point question Step 3
left open, and the honest answer is that the observability-sufficient
subset's real ranking signal does not yet translate into a usable
detector under this project's existing threshold-calibration approach
(`class_weight="balanced"` + F1-maximizing `calibrate_threshold`). A
future phase wanting to make this subset usable would need to address the
threshold-selection method itself (e.g., optimizing directly for a
false-alarm-rate constraint rather than F1) — out of scope for this
follow-up, which was explicitly bounded to evaluation, not redesign.
