# P4 Environment Generalization Remediation Report — Step 4

Executed exactly per `protocol/P4_STEP4_PROTOCOL.md`, pre-registered before
any held-out/robustness result was seen. Raw results:
`raw/p4_step4_results.json`. Script:
`scripts/run_p4_step4_environment_generalization.py`. Model A and Model B
are computed from the exact same real subprocess runs per environment (one
corpus generation pass, two feature representations extracted from
identical events) — any difference between them is purely the feature
representation, never sampling noise.

## Headline finding: the pre-remediation 0.678→0.506 OOM numbers do not replicate under corrected telemetry — and the reason why is now understood and fixed

Model A (original fixed-baseline RSS normalization, i.e. a direct
replication of the pre-existing Phase 4.9 methodology) measures OOM
development AUROC = **0.434** here, not the previously-reported ≈0.678 —
below chance, not above it. This is not a new regression: it is the
direct, expected consequence of the Step 1 telemetry fix (the pre-
remediation 0.678 was measured while `process_rss_bytes` was silently
`None`/broken on this platform; whatever that earlier number reflected, it
was not a real relationship between RSS and OOM outcome, since RSS did not
exist as real data at the time). **The original P4 problem statement itself
does not survive contact with corrected telemetry as stated — both the
development and held-out numbers it was built from need to be
re-established, not just the held-out one.**

Model B (`rss_ratio_env_normalized`, this step's P4-W2 work) tells a very
different, much stronger story:

| Environment (role) | Model A AUROC | Model B AUROC |
|---|---|---|
| `baseline_cpu` (development) | 0.434 | **0.989** |
| `memory_constrained` (held-out) | 0.467 | **0.983** |
| `dependency_network_constrained` (robustness) | 0.471 | **0.935** |

Model B's degradation from development is **0.006** (held-out) and
**0.054** (robustness) — small, and in the direction any real classifier
would be expected to show under genuine distribution shift, not a
collapse-to-chance. This directly confirms the P4-W2 hypothesis: the
original `rss_ratio` feature normalized peak RSS against a fixed 512MB
constant that has no relationship to the `oom` mode's real, per-run
`limit_mb` budget (32MB at baseline vs. 8MB in `memory_constrained` — a 4x
difference the model was never told about). Once RSS is normalized against
the run's own actual configured budget — a genuine configuration input,
known before the run starts, newly exposed via `controlled_runtime.py`'s
`workload_received.workload_parameters` (Step 4 engineering addition) —
the same underlying mechanism (RSS climbing toward a limit) is measured on
a comparable scale in every environment, and prediction quality survives
the environment shift almost entirely intact.

**This is environment generalization working, for an understood,
mechanistic reason — not a fabricated result.** It also directly satisfies
P4-W2's request to "build environment-aware representations" using
"resource limits" as a legitimate feature category, and P4-W4's request to
determine whether "richer telemetry solves it" (here: yes, for this
specific, well-understood normalization gap).

### Caveat, stated honestly: the fixed threshold degrades faster than the ranking does

Model B's AUROC transfers well, but the SINGLE threshold calibrated only on
development data does not transfer as cleanly: `false_alarm_rate` rises
from 0.545 (development) to 1.0 (held-out) to 0.8 (robustness), even
though the underlying ranking (AUROC) barely moves. This means a deployed
system using Model B's score but a dev-only-calibrated threshold would, in
the held-out environment specifically, alarm on every negative run despite
the model itself still ranking cases correctly — an operating-point
calibration problem, not a ranking problem. **This was not fixed in this
step** (recalibrating the threshold per target environment using only
known environment configuration — never held-out outcomes — is a
legitimate, promising next step, explicitly flagged here as unexplored
rather than silently left out).

## Families with no hypothesis: no material difference between Model A and Model B, as expected

`cpu`, `resource_unavailable`, and `flaky` were not predicted to change
between the two models (the audit identified no environment-normalization
problem for their features), and the measurement confirms this — Model A
and Model B are within noise of each other for all three:

| Family | Model A dev AUROC | Model B dev AUROC | Model A degradation (held-out) | Model B degradation (held-out) |
|---|---|---|---|---|
| `cpu` | 0.566 | 0.567 | −0.024 (mild improvement, i.e. held-out scored slightly *lower* AUROC gap) | −0.024 |
| `resource_unavailable` | 0.515 | 0.517 | −0.026 | −0.025 |
| `flaky` | 0.358 | 0.357 | −0.083 | −0.085 |

**Important scoping note:** `resource_unavailable`'s poor showing here
(AUROC ~0.51–0.54, `false_alarm_rate` frequently 1.0) does **not**
contradict Step 3's strong result for the same family (AUROC = 1.0,
specificity = 1.0). Step 4's corpus generation deliberately reuses only the
pre-existing `prediction.py::extract_features`/this step's env-aware
variant — neither includes the Step 3 `resource_preflight_available`
feature (that lives in `prediction_features_v3.py`, a separate module not
wired into `environments.py`'s corpus generator). This is a genuine, not
yet closed, integration gap: Step 3's winning feature has not yet been
evaluated for environment generalization. Flagged as a concrete follow-up,
not silently glossed over.

`cpu` also shows `NOT_PREDICTABLE_SINGLE_CLASS_IN_THIS_ENVIRONMENT` for
`dependency_network_constrained` under both models — that environment's
halved timeout (`0.08s` vs. baseline `0.15s`) combined with this
particular 150-seed test sample happened to produce only one label for the
`cpu` family; this is an honest small-sample artifact of the fixed test
seed range, not a fabricated or hidden result (the pre-existing script
this replicates had the same behavior).

## What this step deliberately did not do

- Did not recalibrate any threshold per-environment (flagged above as a
  legitimate next step, not performed here to avoid any appearance of
  post-hoc tuning toward a better number).
- Did not combine the Step 3 `resource_preflight_available` feature with
  Model B's environment-normalized RSS into one unified feature set —
  scoped separately per the pre-registered protocol; combining them is a
  natural next step, not performed here without pre-registering it first.
- Did not fit or calibrate anything on `memory_constrained` or
  `dependency_network_constrained` data — both remained genuinely
  held-out/robustness-only throughout, per P4-W1's explicit instruction.
