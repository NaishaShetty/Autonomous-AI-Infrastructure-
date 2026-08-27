# Phase 4.9 — Independent Controlled Environment Generalization

**Run:** `experiments/results/phase4_6_to_4_10/20260824T133029Z/` (same immutable run directory)
**Scope:** Priority 4. Tests whether the Phase 4.8 per-family prediction models generalize to genuinely different controlled environments — not merely different `run_id`/`environment_id` labels, which the task explicitly disallows as evidence of generalization.

## 1. Three genuinely distinct environments

`src/phase4/environments.py` defines three `ControlledRuntime` configurations that differ in real resource limits, real runtime configuration, and real dependency-contention conditions — not only a label:

| Environment | Role | Real difference from baseline |
|---|---|---|
| `baseline-cpu` | development | Reference config used by every prior phase (`timeout_seconds=0.15`, `telemetry_interval_seconds=0.01`) |
| `memory-constrained` | held-out | OOM budget genuinely 4x tighter (`limit_mb=8` vs `32`, `alloc_mb` scaled to match) **and** 5x finer telemetry sampling (`2ms` vs `10ms` poll interval) |
| `dependency-network-constrained` | robustness | Execution deadline genuinely halved (`timeout_seconds=0.08` vs `0.15`) **and** the contended-resource family genuinely more often contended (80% pre-occupied vs baseline's ~50%) |

Every environment records full metadata — identity, resource limits, runtime configuration, dependency conditions, telemetry capabilities, failure mechanisms, version — via `EnvironmentProfile.as_dict()` (`evaluation/generalization_metrics.json`'s `environments` key), not just a name.

## 2. Protocol

Per bimodal family (`cpu`, `oom`, `resource_unavailable`, `flaky`): fit and threshold-calibrate **only** on `baseline-cpu` (500 train / 150 validation seeds — the development environment). Freeze. Evaluate the identical frozen model+threshold, zero-shot, against a disjoint 150-seed test population generated **independently under each environment's own scenario generator and `RuntimeConfig`** (baseline itself, held-out, robustness). No held-out or robustness data ever influenced training, threshold selection, or feature choice.

## 3. Results — AUROC by family × environment, and degradation from development

| Family | Dev (baseline-cpu) | Held-out (memory-constrained) | Robustness (dependency-network-constrained) | Degradation (held-out) | Degradation (robustness) |
|---|---|---|---|---|---|
| `cpu` | 0.497 | 0.486 | *no failures in this environment's 150-seed test sample* | 0.011 | n/a |
| `oom` | **0.678** | 0.506 | 0.524 | **0.172** | **0.154** |
| `resource_unavailable` | 0.599 | 0.458 | 0.467 | 0.141 | 0.131 |
| `flaky` | 0.555 | 0.503 | 0.515 | 0.052 | 0.040 |

Full per-environment confusion matrices, precision/recall/F1, AUPRC, Brier, ECE, false-alarm rate, and lead-time stats: `evaluation/generalization_metrics.json`.

## 4. Interpretation

**The one family with a real, above-chance development-environment AUROC (`oom`, 0.678 — notably *higher* here than the near-chance figure Phase 4.8's replicated, negative-controlled evaluation found for `oom` on `baseline-cpu` alone, itself a reminder of how much a single train/val split can vary) collapses to chance level in BOTH other environments** — a genuine, measured generalization failure, not a labeling artifact: the memory-constrained environment's tighter OOM budget changes the real relationship between telemetry and outcome (a model that learned "how RSS behaves when the budget is 32MB" does not transfer to "how RSS behaves when the budget is 8MB"), and the same collapse appears even in the robustness environment, which didn't touch the OOM parameters at all — consistent with Phase 4.8's finding that this family's signal is weak and unstable to begin with.

`resource_unavailable` and `flaky` show smaller, still-negative-direction degradation, consistent with Phase 4.8's finding that neither had real signal in the first place — there is little "real skill" left to lose. `cpu`'s dev-environment AUROC was already at chance (0.497) in this run, so its held-out figure (0.486) is a near-identical near-chance result, and its robustness-environment population happened to contain no negative-class runs in this particular 150-seed sample (the tighter 0.08s deadline shifted the family's outcome distribution — itself a real, honest illustration of how a "robustness" environment's parameter change can alter which failure classes are even observable in a fixed-size sample), so no AUROC could be computed there — reported as `NOT_PREDICTABLE_SINGLE_CLASS_IN_THIS_ENVIRONMENT`, not fabricated.

**Conclusion: none of the four families demonstrate calibration or discrimination that survives a genuine change of environment.** Where Phase 4.8 already found near-chance in-environment signal, generalization is (trivially, honestly) also near-chance. Where Phase 4.8's split happened to show the strongest single-environment signal (`oom` at 0.678), that signal did not transfer — the single clearest piece of evidence in this whole priority that a model fit on this controlled runtime's telemetry does not currently generalize across genuinely different resource/timing/dependency conditions.

## 5. Test coverage

`tests/unit/test_environments.py` (7 tests): the three environments have distinct IDs/roles, differ in real runtime configuration and real resource limits (not just labels), record full required metadata, and produce genuinely different scenario parameters for the same seed.

```
python -m pytest tests/unit/test_environments.py -q
7 passed
```

## 6. Full repository regression check

`python -m pytest` (Python 3.12.13, pytest 9.1.1, 1316.02s): **801 passed, 5 failed** (up from 795 passed / 4 failed after Priority 3 — 7 new Priority 4 tests, plus one more instance of the known test-order/RNG-seed flakiness surfacing).

All 5 failures are instances of categories already flagged in the Phase 4.6–4.8 reports: 3 are the pre-existing environment-timing-sensitive tests (`test_phase44_pipeline.py`, 2× `test_phase45_pipeline_extensions.py`); 2 (`test_phase45b_prediction_scope_router.py` and `test_phase45b_prediction_scope_router_pipeline.py`) are the same known unpinned-`random_state` test-order sensitivity in existing, unmodified `prediction_training.py` code first observed during Priority 3 — which test in that pair fails (if any) depends on which other tests in the suite ran first and consumed global NumPy RNG state. None of the 5 touch `environments.py` or any Priority 1–4 code.

## 7. What Priority 4 does not claim

- Does not claim any of the three environments constitute distributed infrastructure, a real scheduler, multi-node execution, or GPU infrastructure — all three remain real local subprocess execution via `ControlledRuntime`, differing in configuration and scenario parameters, exactly as scoped ("we do NOT need to immediately build Kubernetes/Slurm/Ray").
- Given Phase 4.8's own finding that none of these families show robust in-environment signal, this priority's generalization results are consistent with, not independent confirmation beyond, that negative finding — the one apparent exception (`oom`'s dev-environment 0.678) is exactly the case generalization testing was designed to catch, and it did.
- Sample sizes per environment (150 test seeds, further split by family into tens of runs) are modest; the qualitative direction (near-chance, collapsing further out-of-environment) is consistent across all four families, but per-family confidence intervals were not separately computed here (Phase 4.8's replicated protocol is the source for those, in-environment only).
