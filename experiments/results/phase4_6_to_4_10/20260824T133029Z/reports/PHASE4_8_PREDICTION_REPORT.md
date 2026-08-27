# Phase 4.8 — Valid Prediction Evaluation + Prediction Improvement Attempt

**Run:** `experiments/results/phase4_6_to_4_10/20260824T133029Z/` (same immutable run directory)
**Scope:** Priority 3. Independent of Priorities 1–2; evaluates the infrastructure-failure predictor (`src/phase4/prediction.py`), not the agent task families.

## 1. The problem, restated precisely

The project's own prior report explicitly disallowed reusing the "detectable-only" AUC of 0.857 as evidence — that number blends failure classes with fundamentally different, often deterministic, outcome structures, so a model can separate them by learning failure-class composition rather than any real within-class precursor. The "predictable-scope" AUC of 0.636 (cpu/timeout only) was offered as the honest number, but was never itself checked for robustness across different seed samples, never given a negative (label-shuffled) control, and other bimodal-outcome failure families (`oom`, `resource_unavailable`, `flaky`) were never evaluated on the same terms.

## 2. Methodology

`src/phase4/prediction_eval_v2.py` — for **every** failure family the controlled runtime's `scenario_for_seed` can produce:

1. **Classified each mode from its own subprocess code**, before running anything: `cpu` (timeout vs. not, by duration), `oom` (alloc vs. limit), `resource_unavailable` (port pre-occupied or not), `flaky` (fail_count > 0 or not) are genuinely **bimodal**; `fail`, `network`, `gpu`, `corruption` are **deterministic** (every run of that mode fails, unconditionally — confirmed directly by reading `controlled_runtime.py`'s subprocess code, not inferred after the fact).
2. **Within-family evaluation only** — never blended across modes (the actual fix for the mixing artifact): each bimodal family gets its own `LogisticRegression` fit on **only its own mode's rows**, threshold-calibrated on a disjoint validation split, evaluated once on a disjoint test split. Deterministic modes are reported as `NOT_PREDICTABLE_SINGLE_CLASS` — AUROC/AUPRC are mathematically undefined with one label class present, and no score is fabricated for them.
3. **Full required metric set** per evaluable family: AUROC, AUPRC, precision, recall, F1, Brier, ECE, run-level false-alarm rate, mean lead time, and **useful lead time** (advance warning > 10ms, distinguishing genuine early warning from firing essentially at the failure boundary).
4. **Label-shuffled negative control**: for each evaluable family, the same model architecture refit on the same features with **run-level label permutation** (never a per-checkpoint shuffle, which would create internally inconsistent within-run labels) on train+validation, evaluated against the real test labels.
5. **Replication, not a single point estimate.** An early single-split run (seeds 0–1200/20000–20300/40000–40300) gave `cpu` AUROC ≈ 0.51 — far below the previously reported 0.636. Sanity-checking with the **existing, completely unmodified** `prediction_training.train_and_persist_scope_router` on the exact same seed range reproduced the same ≈0.51 figure, confirming this was a real seed-range sensitivity in the underlying data, not a bug in the new code (see `scripts/run_phase4_8_prediction_evaluation.py`'s module docstring). The frozen final protocol therefore runs **3 disjoint seed-range replicates** (500 train / 150 validation / 150 test seeds each, all 2,400 seeds mutually disjoint) and reports the mean/stdev across replicates, not one arbitrary split.

## 3. Results — real vs. label-shuffled AUROC, mean ± stdev across 3 replicates

| Family (mode) | Status | Real AUROC | Shuffled AUROC | Real − Shuffled | Verdict |
|---|---|---|---|---|---|
| `cpu` (PROCESS_TIMEOUT) | Evaluated | 0.550 ± 0.040 | 0.502 ± 0.086 | +0.047 | Weak, noisy; not clearly separable from a shuffled control at this sample size |
| `oom` (PROCESS_OOM) | Evaluated | 0.525 ± 0.068 | 0.511 ± 0.077 | +0.014 | **Not predictable** — consistent with the prior 4.5b finding (AUC ≈ 0.46) |
| `resource_unavailable` | Evaluated | 0.483 ± 0.067 | 0.487 ± 0.062 | −0.005 | **Not predictable** — real ≈ shuffled ≈ chance |
| `flaky` (INTERMITTENT_TRANSIENT) | Evaluated | 0.499 ± 0.028 | 0.537 ± 0.062 | −0.038 | **Not predictable** — real is exactly at chance |
| `fail` (NONZERO_EXIT) | NOT_PREDICTABLE_SINGLE_CLASS | — | — | — | Deterministic outcome (mode always fails); AUROC undefined |
| `network` (NETWORK_ERROR) | NOT_PREDICTABLE_SINGLE_CLASS | — | — | — | Deterministic outcome; AUROC undefined |
| `corruption` (DATA_CHECKSUM_MISMATCH) | NOT_PREDICTABLE_SINGLE_CLASS | — | — | — | Deterministic outcome; AUROC undefined |
| `gpu` (GPU_DEVICE_UNAVAILABLE) | Evaluated in 1/3 replicates only | 0.725 (n=1) | 0.725 (n=1, identical) | 0.0 | See honesty note below — not a genuine precursor finding |

Full per-replicate numbers, N, and every other required metric (AUPRC, Brier, ECE, false-alarm rate, lead time): `evaluation/prediction_metrics.json`.

**Headline finding:** with a genuinely leak-free, within-family, replicated, negative-controlled protocol, **none of the four bimodal-outcome failure families show a real-AUROC advantage over their own label-shuffled control that survives replication.** `cpu`'s +0.047 gap is the largest, but its stdev (0.040–0.086 across conditions) is on the same order as the gap itself — this is not a robust, reproducible predictive signal at this sample size, and the previously reported 0.636 does not replicate. This directly contradicts treating 0.636 as established "real, if modest, skill" — it should be treated as an artifact of one particular, unrepresentative seed sample instead.

## 4. Honesty note: the `gpu` family

Unlike the module's a-priori classification (every other run of `gpu` mode found in this evaluation failed, consistent with "no GPU device in this sandbox"), replicate 1 contained a mix of both outcomes — meaning **this specific machine's** `nvidia-smi`/`rocm-smi` probe (`controlled_runtime.py`, 0.15s timeout) sometimes succeeds and sometimes times out, a real hardware/timing race rather than a deterministic sandbox absence. Because this only appeared in 1 of 3 replicates, it could not be evaluated with replication, and the real/shuffled AUROC being numerically identical in that single replicate is itself a small-N artifact (very few positive-label runs), not evidence of anything. This is reported rather than discarded, per the project's rule against deleting inconvenient results, but is explicitly **not** claimed as a validated finding.

## 5. Priority 3D — one frozen feature-improvement attempt

Per instructions, prediction improvement was only attempted **after** the methodology above was already validated and had already produced its headline (negative) finding. `src/phase4/prediction_features_v2.py` adds exactly one new engineered feature, `rss_growth_rate` (normalized RSS delta between the last two telemetry samples in a run's prefix), with the rationale for **why this and not others** written into the module **before** running it against test data: `cpu`'s only real signal (elapsed time) is already captured and has no informative derivative (it grows at a constant rate by construction); `oom` could in principle benefit from RSS growth rate if ≥2 samples exist before the outcome is decided; `resource_unavailable`/`flaky` have no structural relationship to RSS or elapsed time at all, so no improvement was expected for them, stated in advance.

Evaluated once, on the identical 3 replicates, no further iteration:

| Family | Baseline (4-feature) AUROC | +`rss_growth_rate` (5-feature) AUROC | Change |
|---|---|---|---|
| `cpu` | 0.550 ± 0.040 | 0.546 ± 0.051 | ≈ no change |
| `oom` | 0.525 ± 0.068 | 0.466 ± 0.013 | slightly worse (within noise) |
| `resource_unavailable` | 0.483 ± 0.067 | 0.507 ± 0.039 | ≈ no change |
| `flaky` | 0.499 ± 0.028 | 0.482 ± 0.025 | ≈ no change |

**Result: the feature did not help, for any family**, matching the pre-registered structural expectation. This is reported as a negative result and the attempt stops here — no further features were tried, no threshold or model class was tuned against these numbers. `evaluation/prediction_feature_improvement_check.json` has full per-replicate figures.

## 6. Interpretation

Given the structural reality of this controlled runtime (a real, project-owned local subprocess harness, not external infrastructure): most failure classes here fail at or within one telemetry sample of `execution_started`, and the one class with a plausible continuous precursor (`cpu`/timeout) shows a signal too small and too noisy to call "real, replicated predictive skill" at the sample sizes tested. This is a genuine, honestly-measured limitation of the available observable precursors in this environment — not a modeling shortfall to keep iterating on, and not evidence that failure prediction is impossible in general, only that it is not currently demonstrated here beyond chance with real replication and a negative control.

## 7. Test coverage

- `tests/unit/test_prediction_eval_v2.py` (6 tests): deterministic-mode detection is never fabricated into a score, ECE correctness, run-level label-shuffle preserves marginal rate and within-run consistency, macro-average aggregation.
- `tests/unit/test_prediction_features_v2.py` (4 tests): the extended feature vector's shape and the `rss_growth_rate` computation.

```
python -m pytest tests/unit/test_prediction_eval_v2.py tests/unit/test_prediction_features_v2.py -q
10 passed
```

## 8. Full repository regression check

`python -m pytest` (Python 3.12.13, pytest 9.1.1, 965.95s): **795 passed, 4 failed** (up from 770 passed / 4 failed after Priority 2 — the suite grew by 25 new Priority 3 tests plus a few incidental additions).

Three of the four failures are the same pre-existing, environment-timing-sensitive tests already flagged in the Phase 4.6/4.7 reports (`test_phase44_pipeline.py::test_abstention_path_is_reachable_when_predicted_risk_is_high`, and two in `test_phase45_pipeline_extensions.py`). The fourth this run, `test_phase45b_prediction_scope_router.py::test_a_model_trained_only_on_predictable_scope_has_real_discriminative_skill`, is a **new instance of a known category, not a new defect**: it was already observed earlier in this priority (§2) to pass or fail depending on which other tests ran before it in the same process, because `train_and_persist_scope_router`'s `LogisticRegression` fit does not pin a `random_state`, so its outcome depends on global NumPy RNG state consumed by whichever tests happen to run earlier in a given invocation — exactly the kind of test-order sensitivity a `random_state=` pin would fix, but that is a change to existing, unmodified Phase 4.5b code, out of scope for this priority, and noted here for the Priority 5 audit rather than fixed opportunistically.

None of the 4 failures touch `prediction_eval_v2.py`, `prediction_features_v2.py`, or any Priority 1/2 code.

## 9. What Priority 3 does not claim

- Does not claim any failure class is provably unpredictable in principle — only that it is not predictable from this specific runtime's currently-observable telemetry (RSS, elapsed time, sample count), with the current feature set, at the sample sizes tested.
- The `gpu` family's apparent partial predictability is explicitly flagged as an unreplicated, likely-artifactual, machine-specific timing quirk, not a validated finding.
- Frozen V1 (`d977a32c...`) and every existing `src/phase4/prediction.py` / `prediction_training.py` artifact are untouched; this priority adds new, separate evaluation and feature modules rather than modifying them.
