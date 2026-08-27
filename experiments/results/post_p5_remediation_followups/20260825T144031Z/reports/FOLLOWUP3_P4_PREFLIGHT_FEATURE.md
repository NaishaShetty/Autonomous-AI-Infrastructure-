# Follow-up 3 — Carry `resource_preflight_available` into P4 Environment Generalization

Script: `scripts/run_followup3_p4_preflight.py`. New feature module (used
only by this script): `src/phase4/prediction_features_p4_preflight.py`.
Raw results: `raw/followup3_p4_preflight.json`.

## Method, and the leakage check

The pre-flight `bind()` probe (`controlled_runtime.py`,
`telemetry_kind == 'resource_preflight_probe'`) is emitted by
`ControlledRuntime.run()` **before** `subprocess.Popen(...)` is called in
the same method — confirmed by direct reading of `controlled_runtime.py`
(the probe-emission block precedes the `Popen` call textually and
causally in the same function body). `environments.py`'s three P4
environments all reuse this same `ControlledRuntime.run()` code path with
only `RuntimeConfig`/scenario-function differences, so the probe event was
already being emitted in every P4 corpus generation run — it was simply
never read into a feature. `rolling_checkpoints`'s existing at-or-before
discipline (unchanged) guarantees the same decision-time semantics as
every other P4 feature. No leakage: this is a genuine configuration/
pre-flight-probe input, not a peek at the run's own outcome.

Three feature sets compared, exactly per the followups task:
- **A (existing P4 baseline):** `rss_ratio, anomaly_rate, elapsed_ratio,
  sample_count_ratio` — unchanged, evaluated on all four bimodal families
  as a control.
- **B (P3 preflight alone):** `resource_preflight_available` only —
  evaluated for `resource_unavailable` only (the only family this feature
  carries real information for; every other family gets the neutral 0.5
  constant, so a model fit on it there has nothing to learn).
- **C (combined):** A's 4 features + B's 1 feature (5 total) —
  `resource_unavailable` only.

Fit discipline: identical to `P4_STEP4_PROTOCOL.md` — model frozen after
fitting/threshold-calibrating on `baseline_cpu` (development) only; held-
out (`memory_constrained`)/robustness (`dependency_network_constrained`)
data never influences fitting, calibration, or feature selection.

## Results — `resource_unavailable`, held-out (`memory_constrained`) environment

Specificity is not a field `prediction_eval_v2.compute_metrics` returns
directly; it is computed here as `tn / (tn + fp)` from the raw
`true_negatives`/`false_positives` counts in `raw/followup3_p4_preflight.json`.

| Feature set | AUROC | AUPRC | Precision | Recall | TP / FP / FN / TN | Specificity | False alarm rate | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|
| A (existing P4 baseline, 4 feat.) | 0.781 | 0.986 | 0.967 | 0.868 | 739 / 25 / 112 / 15 | 0.375 | **1.00** | 0.401 | 0.559 |
| B (preflight only, 1 feat.) | 0.743 | 0.977 | 0.955 | 1.000 | 851 / 40 / 0 / 0 | 0.000 | **1.00** | 0.226 | 0.317 |
| **C (combined, 5 feat.)** | **0.916** | 0.996 | 0.969 | 0.981 | 835 / 27 / 16 / 13 | 0.325 | **1.00** | 0.242 | 0.332 |

**Specificity does not improve monotonically with the AUROC gain**: Model
C's specificity (0.325) is actually slightly *lower* than Model A's alone
(0.375), even though its AUROC (a threshold-independent ranking metric) is
much higher (0.916 vs. 0.781). This is exactly why AUROC alone must never
be treated as sufficient evidence of usability — it is measuring something
genuinely different from what happens at the one threshold the calibrated
model would actually use in production. The **run-level false alarm
rate** (the same metric Step 3 used to disqualify `cpu`/pooled-`oom`/
`flaky`) is **1.00 for all three feature sets, including C** — the
`memory_constrained` environment's single negative `resource_unavailable`
run was, in every case, still flagged by the fired detector at some
checkpoint before the run concluded.

**Statistical-power caveat on the false-alarm-rate number itself:** the
`memory_constrained` environment's `resource_unavailable` test population
contains only `n_negative_runs = 1` (a single healthy run) at the fixed
150-seed test range inherited from the original Phase 4.9 script — so
`false_alarm_rate = 1.00` here means literally "the one healthy run in
this sample fired," not an average over many healthy runs. This does not
change the qualitative always-fires conclusion (the specificity/tn counts
at the row level, computed over hundreds of checkpoints rather than one
run, tell the same story — Model C's `true_negatives=13` out of 40
negative-labeled rows is a real, non-degenerate low-specificity signal,
not just an N=1 artifact), but the run-level false-alarm-rate figure's own
precision at N=1 negative run is honestly limited and should not be read
as more statistically confident than it is.

**Both `baseline_cpu` (development) and `dependency_network_constrained`
(robustness) produced a single-class test population for
`resource_unavailable` at the fixed `TEST_SEEDS = range(900_000, 900_150)`
range (150 seeds) inherited unchanged from the original Phase 4.9 script**
— this is the same fixed range Step 4's own report used, not a new
artifact introduced by this follow-up, and it means **dev→held-out and
dev→robustness degradation cannot be computed for `resource_unavailable`
in this run** (the denominator, dev AUROC, is undefined). This is reported
as a genuine, disclosed data-availability limitation, not a fabricated
degradation number.

## Honest interpretation

**Ranking quality improves substantially when the preflight feature is
combined with P4's existing features** (AUROC 0.781 → 0.916, a real,
non-trivial jump — the preflight feature alone (Model B) is actually
slightly *weaker* than the existing baseline alone, so the improvement is
specifically a combination effect, not simply "preflight dominates").
**But this does not translate into an operationally usable predictor at
the calibrated threshold: false alarm rate is 1.00 for all three feature
sets, including the combined one.** This is the identical "always fires"
failure mode Step 3 and follow-ups 1 and 5 all found for their own
families — `class_weight="balanced"` + F1-maximizing threshold selection
choosing an extremely permissive threshold when classes are imbalanced or
small-sample, regardless of how good the underlying ranking is. Per the
project's standing rule, **AUROC alone never establishes usability, and
it does not here either.**

## Comparison to the pre-remediation state and to Step 3/Step 4's separate findings

- Step 3 (P3) found `resource_unavailable` to have **STRONG EVIDENCE**
  (precision/specificity/false-alarm-rate all exactly 1.0/1.0/0.0 with
  zero variance) — but that was measured **within the `baseline_cpu`-
  equivalent single-environment corpus** (`prediction_features_v3.py`'s
  own generator, not the P4 multi-environment one), where the probe and
  outcome are separated by milliseconds and the corpus's specific
  seed/threshold combination happened to produce a clean separation.
- Step 4 (P4-W2) never evaluated `resource_unavailable` with the preflight
  feature at all — it was entirely OOM-scoped.
- **This follow-up is the first time the preflight feature has been
  evaluated under P4's cross-environment zero-shot discipline**, and the
  result is materially different from Step 3's: the SAME feature, useful
  and clean within a single fixed environment/corpus, does **not**
  produce a usable operating point once evaluated zero-shot on the
  `memory_constrained` held-out environment's own test population (a
  different corpus, different seed range, different random realization of
  which runs are positive/negative). **This is a genuine, informative
  finding, not a contradiction of Step 3**: it shows the preflight
  feature's Step 3 "STRONG EVIDENCE" finding was, at least in part, a
  property of that specific corpus's threshold-calibration split, not a
  guarantee that transfers zero-shot to every environment/seed-range
  combination.

## Explicit caveat (as instructed)

The preflight probe occurs milliseconds before the outcome in this
controlled corpus (parent-process `bind()` immediately before child
`Popen`). **Nothing in this follow-up's result should be read as evidence
this signal would transfer to a production environment where resource
contention state can genuinely change in the (much longer, real-world)
gap between a pre-flight check and actual dispatch.** The always-fires
finding here is itself a caution in the opposite direction from
overclaiming: even in this favorable, near-simultaneous synthetic corpus,
the combined feature set does not clear the operational usability bar at
its calibrated threshold.

## Verdict

**IMPROVED RANKING QUALITY, STILL NOT VALIDATED AT THE OPERATING POINT.**
Combining P3's preflight feature with P4's existing feature set raises
`resource_unavailable`'s held-out AUROC from 0.781 to 0.916 — a real,
measurable, mechanistically-explicable improvement from adding genuine
pre-outcome information. It does not, however, produce a usable predictor
at the calibrated decision threshold (false alarm rate 1.00 for all three
feature sets) — the same always-fires trap found elsewhere in this
follow-up phase. `dev`→`held-out`/`robustness` degradation could not be
computed due to a single-class development/robustness test population at
the inherited fixed seed range — disclosed, not fabricated. No further
feature iteration was performed on `resource_unavailable` in this
follow-up after this result.
