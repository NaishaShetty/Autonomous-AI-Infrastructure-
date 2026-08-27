# Post-P5-Remediation Follow-Ups — Summary

Run directory: `experiments/results/post_p5_remediation_followups/20260825T144031Z/`

Executes the five bounded follow-ups explicitly recommended (but not
performed) by `experiments/results/post_p5_remediation/20260825T064402Z/FINAL_POST_REMEDIATION_EVALUATION.md`'s
"Immediate recommended follow-ups" section. That run directory (protocol,
raw data, reports) is unchanged, read-only reference — nothing there was
modified or overwritten by this work. Full detail for each follow-up is in
its own report under `reports/`; this document is the required top-level
summary.

## Follow-up 1 — `cpu`-family predictability, re-run with the Step 7 timing fix

**Tested:** Re-ran Step 3's exact `cpu`-family protocol (`full_v3` +
`elapsed_only` variants, 3 replicates) now that `prediction_training.py`'s
0.01s/0.02s timing fix is in place. 2 of 3 replicates completed (one
single-class split under this run's real concurrent system load, honestly
excluded rather than substituted).

**Key metrics:** `full_v3` real AUROC 0.616 ± 0.045 vs. shuffled 0.389 ±
0.032; false alarm rate **1.00 ± 0.00** in every replicate/variant.

**Changed the prior conclusion?** No. The timing fix measurably changed
the reported AUROC numbers (real-vs-shuffled gap widened) but did not
change the qualitative verdict: still always-fires at the calibrated
threshold.

**Status: NOT VALIDATED (confirmed unchanged after timing fix) — final,
no further cpu-family iteration.**

## Follow-up 2 — P5 integrated evaluation, re-run with the Step 7 timestamp-tie fix

**Tested:** Re-ran the calibrated-vs-generic policy comparison and the
memory/retry/predictor ablations on a fresh, disjoint 300-seed held-out
set, using the exact `AutonomyPipeline.run_agent_task` code path the
addendum named. Included an explicit same-seed re-run to directly verify
determinism.

**Key metrics:** Calibrated final accuracy 0.997 (vs. generic 0.957);
final error rate 0.0033 (vs. generic 0.0433); retry recovery rate 0.938
(15/16); zero unsafe actions in every condition; the calibrated condition
was byte-identical across two consecutive runs on the same seeds
(decision distribution, final accuracy, retry count all matched exactly).

**Changed the prior conclusion?** The qualitative finding (calibrated +
retry dramatically reduces error) survives unchanged. The exact
"1.000/0.000" decimal headline does not — this fresh, defect-free
measurement shows 0.997/0.0033, a small, expected, honestly-reported
difference from measuring a different (and now provably deterministic)
sample, not a contradiction of the original finding.

**Status: FIXED, RE-CONFIRMED** (determinism verified directly; headline
direction survives; exact decimals superseded by a defect-free
measurement).

## Follow-up 3 — carry `resource_preflight_available` into P4 environment generalization

**Tested:** Added the P3 pre-flight-probe feature into P4's
environment-generalization pipeline (new module
`src/phase4/prediction_features_p4_preflight.py`), compared existing P4
baseline (A), preflight-alone (B), and combined (C) feature sets for
`resource_unavailable`, fit on `baseline_cpu` only, evaluated zero-shot.

**Key metrics:** Held-out (`memory_constrained`) AUROC: A=0.781,
B=0.743, **C=0.916** — a real, non-trivial ranking improvement from
combining the features. But false alarm rate = **1.00 for all three**
feature sets at their calibrated thresholds (specificity 0.375 / 0.000 /
0.325 respectively — C is not even the highest). Dev/robustness
degradation could not be computed (single-class test population at the
inherited fixed seed range for `resource_unavailable` in both the
development and robustness environments).

**Changed the prior conclusion?** Adds a new, more nuanced finding: the
preflight feature genuinely improves ranking quality when combined with
existing features, but does not by itself make `resource_unavailable`
generalization operationally usable — the same always-fires
threshold-calibration problem found throughout this project's other
families also applies here.

**Status: IMPROVED RANKING QUALITY, STILL NOT VALIDATED AT THE OPERATING
POINT.**

## Follow-up 4 — P2-W1 (larger held-out) + P2-W3 (retry economics grid)

**Tested:** P2-W1: generic-vs-calibrated comparison on a fresh 600-seed
held-out set (2x the original). P2-W3: an 18-point pre-registered grid
over `COST_RETRY_PER_EXTRA_SAMPLE` x `BENEFIT_CORRECT` x
`COST_WRONG_ANSWER`, evaluated on a fixed 40-seed set, via
module-attribute monkey-patching around the same frozen calibration
profile.

**Key metrics:** P2-W1 calibrated final accuracy 0.998 vs. generic 0.970
(95% CI 0.991-1.000 vs. 0.953-0.981); retry recovery 95% (19/20). P2-W3:
all 18 configurations, including the project's existing baseline,
produced byte-identical decisions/outcomes (final accuracy 1.000 in
every configuration, on this small 40-seed/3-wrong-episode grid set).

**Changed the prior conclusion?** No — both results support and extend
the existing calibrated-policy finding. P2-W1 confirms the improvement
survives at larger scale. P2-W3 finds no evidence of fragility within the
pre-registered range, with the explicit, honest caveat that the grid's
own sample (3 wrong-initially episodes per configuration) limits how
confidently "no fragility" generalizes beyond this specific check.

**Status: P2-W1 VALIDATED (survives 2x expansion); P2-W3 NO FRAGILITY
OBSERVED (limited statistical power, disclosed).**

## Follow-up 5 — OOM operating-point follow-up (>=2 pre-outcome samples)

**Tested:** Froze Step 3's exact `oom`-family predictor and features; split
TEST evaluation (never re-thresholded) into the `>=2 samples`
sufficient-observability subset and the `0-1 samples` control, across the
same 3 pre-registered replicates.

**Key metrics:** `>=2 samples`: AUROC 0.780 ± 0.096 (real) vs. 0.625 ±
0.093 (shuffled) — a real, replicated ranking edge — but false alarm rate
**1.00 ± 0.00** and specificity only 0.179 ± 0.254 at the calibrated
threshold. `0-1 samples` control: weaker ranking edge (0.627 vs. 0.594)
and the same always-fires problem (false alarm rate 1.00).

**Changed the prior conclusion?** Directly answers the operating-point
question Step 3 explicitly left open ("neither subset has been shown to
produce a usable (non-always-firing) predictor"). Answer: it does not.
The real ranking signal Step 3 found for the `>=2 samples` subset is
confirmed as real and replicated, but does not translate into a usable
detector under the project's existing threshold-calibration approach.

**Status: NOT VALIDATED (both subsets) — final, no further iteration on
frozen `oom` predictor/features.**

## Engineering defects found or fixed this phase

**None.** No new engineering defect was discovered while executing any of
the five follow-ups. All five ran on top of the Step 7 fixes already
present in the working tree (`prediction_training.py`'s timing fix,
`pipeline.py`'s `<=` timestamp-tie fix, both verified present by direct
code reading before use) without requiring any further source change.
Two new, narrowly-scoped, read-only feature/evaluation modules were added
specifically for these follow-ups (`src/phase4/prediction_features_p4_preflight.py`
for follow-up 3) alongside five new evaluation scripts
(`scripts/run_followup{1..5}_*.py`) — none of these modify any existing
frozen behavior; they only add new, additive feature-extraction and
evaluation code paths, exactly as the follow-ups' scope required.

## Full test suite

`python -m pytest tests/ -q`: **837 passed, 0 failed** (2076.80s / 34m36s),
run after all five follow-ups completed, confirming nothing in this phase
broke any existing test.

## What was explicitly NOT done in this phase (stated plainly)

- P4-W5 (containerized/production-scale environments) and P5-W4 (recovery
  taxonomy expansion) — named in the original master register as
  out-of-scope follow-ups, not part of this phase's five bounded items,
  and still not attempted.
- Follow-up 3's dev→held-out/dev→robustness AUROC degradation for
  `resource_unavailable` could not be computed (single-class test
  populations at the inherited fixed seed range) — disclosed as a data
  limitation, not silently worked around by choosing a different seed
  range after the fact.
- No threshold, feature, or protocol was changed after seeing any result
  in any of the five follow-ups, per each follow-up's own pre-registered
  (or directly inherited, for follow-ups 1 and 5) stopping rule.

## Manifest

See `manifests/` for the file listing of every artifact this run
directory contains.
