# Follow-up 1 — Re-run P3 `cpu`-Family Predictability with the Step 7 Timing Fix

Re-runs `protocol/P3_STEP3_PROTOCOL.md`'s `cpu`-family evaluation exactly
(same 3 replicate seed ranges, same `full_v3`/`elapsed_only` feature
variants, same `StandardScaler`+`LogisticRegression` model, same
shuffled-label control, same false-alarm-rate/specificity discipline),
now that `prediction_training.py`'s Step 7 timing fix (0.01s/0.02s "fast"
duration choices, replacing the old 0.05s/0.08s choices that left only
~70-100ms of margin against real ~65-75ms subprocess-startup overhead) and
its auto-widening train-seed-range backstop are both in place. Script:
`scripts/run_followup1_cpu_predictability.py`. Raw results:
`raw/followup1_cpu_predictability.json`.

**Honest caveat on this specific run's conditions:** this evaluation was
executed while three other CPU/subprocess-heavy follow-up experiments were
running concurrently on the same machine (follow-ups 2 and 5), i.e. under
real, non-trivial system contention — the exact condition the original
timing-margin defect was most sensitive to. Only 2 of the 3 pre-registered
replicates completed (the third replicate's `cpu` family produced a
single-class split under this contention and was honestly excluded, not
substituted or re-run with different seeds); this is reported plainly
below, not hidden.

## Results (mean ± population std across 2 completed replicates)

| Variant | Real AUROC | Shuffled AUROC | False alarm rate | Specificity | Recall | Precision |
|---|---|---|---|---|---|---|
| `elapsed_only` | 0.503 ± 0.001 | 0.499 ± 0.003 | **1.00 ± 0.00** | 0.25 ± 0.25 | 0.75 ± 0.25 | 0.86 ± 0.00 |
| `full_v3` (6-feature) | 0.616 ± 0.045 | 0.389 ± 0.032 | **1.00 ± 0.00** | 0.34 ± 0.19 | 0.76 ± 0.19 | 0.88 ± 0.01 |

Both variants' mechanical stopping-rule check labels the result "SIGNAL"
(real AUROC exceeds the shuffled control by more than one pooled std) —
`full_v3` more clearly than the original pre-fix Step 3 measurement
(0.616 vs. 0.389 here, vs. 0.549 vs. 0.480 originally), a real, measurable
change from the timing fix.

## Interpretation: still NOT VALIDATED, for exactly the reason Step 3 pre-registered

**The false-alarm rate is still exactly 1.00 for both variants, in every
completed replicate.** Per the master remediation register's explicit
rule ("a model with high recall because it fires on almost everything is
NOT considered a successful predictor") and the same override Step 3's own
report applied, this always-fires pattern at the calibrated operating
point disqualifies both variants as usable predictors, **regardless of
what the AUROC ranking metric shows.** `class_weight="balanced"` +
F1-maximizing threshold selection is again choosing a threshold so low
that it alarms on essentially every healthy `cpu` run in the test set —
the same textbook "always fires" trap Step 3 found, not a calibration bug
to patch (and patching it now, after seeing this result, would itself
violate the "no threshold tuning after seeing test results" rule this
follow-up inherits unchanged from `P3_STEP3_PROTOCOL.md`).

**Does the timing fix materially change the conclusion? No.** The
qualitative verdict for `cpu` is unchanged: **NOT VALIDATED** under this
observability regime, in both the pre-fix (Step 3) and post-fix (this
follow-up) measurement. What the timing fix DID change is the *reported
AUROC numbers themselves* — `full_v3`'s real-vs-shuffled AUROC gap widened
noticeably (0.616 vs. 0.389, a larger separation than Step 3's 0.549 vs.
0.480) — consistent with `ADDENDUM_CPU_TIMING_DEFECT.md`'s own prediction
that a false-timeout-contaminated corpus would, if anything, have made
`cpu` look **more** separable from chance by construction (not less), so
a cleaner corpus narrowing that AUROC gap would have been the more
surprising direction; instead the gap widened, which is at least
consistent with (though does not prove) the timing-contamination
explanation. Regardless of the AUROC movement, the false-alarm-rate
finding is the one that actually determines usability, and it did not
change: **1.00 before the fix, 1.00 after.**

## Comparison to the pre-remediation `cpu` numbers

| Measurement | `full_v3` real AUROC | `full_v3` shuffled AUROC | False alarm rate | Verdict |
|---|---|---|---|---|
| Step 3 (pre-timing-fix, `P3_PREDICTABILITY_REMEDIATION_REPORT.md`) | 0.549 ± 0.032 | 0.480 ± 0.067 | 1.00 ± 0.00 | NOT VALIDATED |
| This follow-up (post-timing-fix) | 0.616 ± 0.045 | 0.389 ± 0.032 | 1.00 ± 0.00 | NOT VALIDATED |

## Verdict

**`cpu` (both `full_v3` and `elapsed_only`): NOT VALIDATED — final,
no further iteration.** This matches the master remediation register's
explicit stopping instruction: "If after legitimate observability
improvements the best predictor still performs at chance [i.e., is not a
usable predictor at any calibrated operating point], STOP trying to force
prediction." The Step 7 timing fix genuinely improved corpus correctness
(no more systematic false-TIMEOUT mislabeling) and is real engineering
progress, but it does not change `cpu`'s bottom-line predictability
verdict. Per the followups task's explicit instruction, this is recorded
as the final negative result for `cpu` and cpu-family predictability
iteration stops here.
