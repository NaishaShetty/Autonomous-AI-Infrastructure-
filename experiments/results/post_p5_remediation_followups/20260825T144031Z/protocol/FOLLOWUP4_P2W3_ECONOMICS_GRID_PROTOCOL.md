# Follow-up 4 (P2-W3) -- Retry Economics Sensitivity Grid: Pre-Registration

Written and committed to disk BEFORE `scripts/run_followup4_p2_heldout_and_economics.py`
was run. The grid values below are fixed; none were chosen or adjusted
after seeing any outcome.

## What is being swept

`src/phase4/agent_calibration.py` fixes three utility constants used by
`AgentDecisionCalibrationProfile.utility_for_bucket` as documented,
judgment-call defaults (module docstring, "not fit or tuned against any
evaluation outcome"):

- `BENEFIT_CORRECT` (baseline 1.0)
- `COST_WRONG_ANSWER` (baseline 1.0)
- `COST_RETRY_PER_EXTRA_SAMPLE` (baseline 0.01)

This follow-up asks whether the calibrated policy's *decisions* (and
downstream accuracy/error/retry-rate/safety numbers) are reasonably stable
across a range of plausible values for these three constants, or whether
the policy is fragile to the exact judgment call made at design time.

## Grid (fixed before running)

```
COST_RETRY_PER_EXTRA_SAMPLE in [0.0, 0.01, 0.05]
BENEFIT_CORRECT              in [1.0, 2.0]
COST_WRONG_ANSWER            in [0.5, 1.0, 2.0]
```

Full Cartesian product: 3 x 2 x 3 = **18 configurations**, including the
project's existing baseline (`COST_RETRY_PER_EXTRA_SAMPLE=0.01,
BENEFIT_CORRECT=1.0, COST_WRONG_ANSWER=1.0`) as configuration #1 for direct
comparison against every prior report's numbers.

`COST_REVIEW` (0.30) and `COST_ABSTAIN` (0.40) are held fixed at their
existing values throughout -- the task named only the three constants
above; sweeping five simultaneously would make the grid too sparse to
interpret at this sample size.

## Method

1. `AgentDecisionCalibrationProfile` is fit EXACTLY ONCE, on the existing,
   unchanged CALIBRATION split (`range(10_000, 12_000)`, identical to
   every prior report). Only `utility_for_bucket`'s downstream decision
   depends on the three swept constants -- `bucket_stats` (the fitted
   empirical frequencies) do not, so re-fitting per grid point would be
   wasted, disallowed-looking re-fitting for no reason. Instead, the three
   module-level constants in `src.phase4.agent_calibration` are
   monkey-patched (module attribute assignment, restored after each
   configuration) immediately before `profile.decide(...)` is called for
   that configuration's episodes, then restored -- this changes ONLY the
   utility arithmetic, never the fitted bucket statistics.
2. Each configuration is evaluated on the SAME fixed set of 40 fresh test
   seeds, `range(90_000, 90_040)` -- disjoint from train/calibration/every
   prior test split used in this remediation phase and its follow-ups.
3. No threshold, bucket edge, or grid value is changed after seeing any
   configuration's result. All 18 configurations are run and reported;
   none are dropped or re-run.

## Metrics reported per configuration

Decision distribution (ANSWER/RETRY/REVIEW/ABSTAIN counts), retry rate,
final accuracy, final error rate, mean realized expected utility (per the
profile's own utility formula, at the decision actually taken),
unnecessary-retry rate (retry attempted on an episode that was not
initially wrong -- structurally near-zero by this profile's design, kept
for completeness), wrong-answer cost incurred, recovery benefit realized,
unsafe action count.

## What would count as "the calibrated policy is not reasonable" here

If final error rate or unsafe-action count moves sharply and
non-monotonically across nearby grid points (suggesting the decision boundary
is on a knife's edge rather than a stable region), or if any configuration
produces a materially worse final error rate than never retrying at all,
that is reported as a real finding, not smoothed over.
