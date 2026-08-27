# Follow-up 4 — P2-W1 (Larger Held-Out Evaluation) + P2-W3 (Retry Economics Sensitivity Grid)

Script: `scripts/run_followup4_p2_heldout_and_economics.py`. P2-W3's grid
was pre-registered before running in
`protocol/FOLLOWUP4_P2W3_ECONOMICS_GRID_PROTOCOL.md`. Raw results:
`raw/followup4_p2w1_heldout.json`, `raw/followup4_p2w3_economics_grid.json`.

## P2-W1: larger held-out evaluation

600 fresh, disjoint seeds (`range(80_000, 80_600)`) — 2x the size of the
original Phase 4.7/4.10 test set (300), and disjoint from train,
calibration, the original test, and follow-up 2's fresh test range. The
calibration profile is the same frozen, unmodified
`AgentDecisionCalibrationProfile` every prior report used — no threshold
was tuned on this larger set.

| Policy | n | Initial acc. | Final acc. | Final error rate | Retry rate (of wrong) | % wrong corrected | Retry recovery rate | Unsafe actions |
|---|---|---|---|---|---|---|---|---|
| Generic | 600 | 0.970 | 0.970 | 0.0300 | 0.0 | 0.0 | — | 0 |
| **Calibrated** | 600 | 0.967 | **0.998** | **0.0017** | 1.0 | **0.95** | 0.95 | 0 |

95% Wilson CIs on final accuracy: generic 0.953–0.981; calibrated
0.991–1.000 (`retry_recovery_rate` 95% CI: 0.764–0.991, n=20 retried).

**The calibrated policy's improvement survives at 2x the sample size**:
final accuracy is 0.998 vs. generic's 0.970, and 19 of 20 initially-wrong
episodes (95%) were corrected by retry. This is consistent (within CI)
with follow-up 2's fresh-300-seed measurement (0.997 final accuracy,
93.75% retry recovery) — the two independent samples agree, which is
itself evidence the earlier finding is not a small-sample artifact.
`calibrated_improvement_survives = true` per the script's own explicit
comparison field (raw JSON).

## P2-W3: retry economics sensitivity grid

18 pre-registered configurations (3 `COST_RETRY_PER_EXTRA_SAMPLE` values x
2 `BENEFIT_CORRECT` values x 3 `COST_WRONG_ANSWER` values), each evaluated
on the same fixed 40-seed grid set (`range(90_000, 90_040)`), via
module-attribute monkey-patching of `src.phase4.agent_calibration`'s three
utility constants around the same once-fitted profile (bucket statistics
never refit; see the protocol doc for why re-fitting per grid point is
unnecessary).

**Result: all 18 configurations, including the project's existing
baseline (config 7: `cost_retry=0.01, benefit_correct=1.0,
cost_wrong=1.0`), produced byte-identical decisions and outcomes** — final
accuracy 1.000, final error rate 0.000, 3/3 initially-wrong episodes
retried and all 3 recovered, zero unsafe actions, across the entire
pre-registered range.

`summary.final_error_rate_range = 0.0`, `summary.unsafe_action_count_max
= 0` (raw JSON) — the grid produced no variation at all in this sample.

## Honest interpretation — this is a real but statistically thin result

**The calibrated policy is not fragile across this pre-registered range of
plausible utility-constant values — every configuration made the same
decisions.** This is a genuine, useful finding: it means the policy's
retry/answer/review boundary is not sitting on a knife's edge with respect
to these three constants, at least not within the 0.0-0.05 /
0.5-2.0 / 0.5-2.0 ranges swept.

**However, this grid's statistical power is honestly limited: only 3 of
40 grid-set episodes were initially wrong, so every configuration's
decision differences (if any existed) would have had to show up across
only 3 retry decisions.** A grid this small cannot rule out that some
narrower or more extreme constant combination (outside the pre-registered
range, which was fixed before running per the protocol and not expanded
after seeing this flat result) would move the decision boundary. The
followups task's own criterion for "the calibrated policy is not
reasonable" (sharp, non-monotonic movement in final error rate or unsafe
actions across nearby grid points) was not observed — but with zero
observed variation at all, this grid's result is better read as "no
evidence of fragility within this range, at this sample size" rather than
"fragility is ruled out in general." This limitation is stated plainly
rather than treated as a stronger result than it is.

## Verdict

- **P2-W1: the calibrated policy's improvement over the generic policy
  SURVIVES at 2x the original held-out sample size**, with results
  consistent (within CI) across two independent fresh samples (this
  follow-up's 600-seed set and follow-up 2's 300-seed set). **STATUS:
  VALIDATED (survives expansion).**
- **P2-W3: the calibrated policy is stable (no decision or outcome
  variation) across the full pre-registered 18-point utility-constant
  grid**, with the explicit, disclosed caveat that this grid's own sample
  (3 wrong-initially episodes per configuration) is small and this result
  should be read as "no fragility observed in this range" rather than a
  fully powered robustness guarantee. **STATUS: NO FRAGILITY OBSERVED
  (limited statistical power, disclosed).**
