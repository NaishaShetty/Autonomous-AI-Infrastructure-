# P3 Predictive-Observability Audit

Post-P5 remediation, Step 2 (P3-W1 / P3-W2). Performed **before** any P3
model re-training or re-evaluation, per the master remediation order:
observability first, predictability second, simple model third, complex
model only if justified — never the reverse.

For each of the 8 failure classes the controlled runtime supports, this
audit answers: what information exists before the outcome is decided; what
becomes available only after; what is currently missing; whether a genuine
precursor exists at all; and whether the failure mechanism is inherently
predictable from process-level telemetry in this environment. Findings are
based on direct reading of `src/phase4/controlled_runtime.py`'s subprocess
implementation (the actual mechanism each mode uses to succeed or fail) and
`src/phase4/prediction.py` / `prediction_features_v2.py`'s existing, already
partly-honest documentation (`prediction_features_v2.py`'s module docstring
in particular had already reasoned through several of these before this
audit — that reasoning is verified and extended here, not repeated
uncritically).

## Method

For every mode: (1) read the exact subprocess code that decides
success/failure; (2) determine the real-time gap, if any, between process
start and outcome determination; (3) determine what `telemetry_observed` /
other canonical events actually exist in that gap; (4) classify.

Classification labels used below:
- **REAL PRECURSOR** — a telemetry signal exists, before the outcome, that
  is mechanistically related to the outcome (not just correlated by
  construction of the synthetic corpus).
- **NO TEMPORAL WINDOW** — the outcome is decided so close to process start
  that no telemetry sample can occur before it, regardless of sampling
  rate; a precursor would require observation *before* the child process
  even starts.
- **EXOGENOUS / NOT OBSERVABLE THIS-EPISODE** — the deciding state lives
  outside this episode's own event stream (e.g., in the parent process's
  cross-call counters) and exposing it directly would encode the label,
  not a legitimate precursor.
- **DETERMINISTIC BY DESIGN** — the mode always produces the same outcome
  by construction; AUROC/AUPRC are mathematically undefined, not merely
  hard to estimate (already correctly handled by
  `prediction_eval_v2.py`'s `NOT_PREDICTABLE_SINGLE_CLASS` status).

## Per-failure-class findings

### `cpu` / PROCESS_TIMEOUT — REAL PRECURSOR (confirmed)

Mechanism: a busy-loop workload runs until `duration_seconds` elapses;
whether it finishes before the configured `timeout_seconds` decides the
label. There is a genuine, multi-sample telemetry window between process
start and outcome — the runtime polls every `telemetry_interval_seconds`
while the process is alive.

- **Available before decision:** `elapsed_ratio` (elapsed / configured
  timeout) — the single strongest, mechanistically real precursor this
  runtime can produce: a workload approaching its timeout without
  completing genuinely predicts a timeout. Also now available (real, not
  constant-zero — see engineering fix #3): `process_rss_bytes`,
  `process_cpu_percent`, `process_age_seconds`, host-level
  `system_available_memory_bytes`/`system_memory_percent`.
- **Missing:** true CPU utilization *of this specific process relative to
  its allotted share* (psutil's `cpu_percent` is host-wide-normalized, not
  cgroup/container-scoped — this sandbox has no cgroup/container isolation
  to measure against) and scheduling delay (no real scheduler exists in
  this single-process-per-workload sandbox to measure queueing against).
- **Prior evidence corrected:** before the RSS fix, `rss_ratio`/
  `anomaly_rate` were constant-zero, so the trained model was effectively
  a 1-feature (`elapsed_ratio`) model and measured ~0.63 AUC in an isolated
  run. With RSS now real, the same model/corpus/split measures ~0.50
  (chance) — see `ENGINEERING_FIXES_REPORT.md` item 3 for the full
  mechanism. This is not evidence that `elapsed_ratio` stopped being a
  real signal; it is evidence that adding uninformative, noisy RSS
  dimensions to a small-sample logistic fit can *destroy* an existing
  clean signal. **Recommendation for Step 3:** evaluate `elapsed_ratio`
  alone (or with a principled feature-selection step, decided *before*
  looking at test results) as its own candidate model, separately from the
  full-feature model, rather than concluding "cpu has no real precursor"
  from a diluted fit.

### `oom` / PROCESS_OOM — REAL PRECURSOR IN PRINCIPLE, TIMING-LIMITED IN PRACTICE

Mechanism: allocates `alloc_mb` in a tight, unpaced Python loop
(1MB `bytearray` per iteration, no sleep) against a `limit_mb` budget
(OS `RLIMIT_AS` on POSIX; a self-enforced admission check on Windows — see
`controlled_runtime.py`'s own honest labeling of the two paths). The loop
typically completes (succeeds or hits the limit) in low-single-digit
milliseconds for the `alloc_mb` values this project's `prediction_training.
scenario_for_seed` uses (8–300MB).

- **Available before decision, when it exists:** `rss_ratio` (now real —
  see fix #3) and `rss_growth_rate` (Phase 4.8's own feature-improvement
  candidate, added specifically for this family) — both mechanistically
  sound: RSS climbing toward the configured limit is a genuine precursor
  of hitting it.
- **The actual limiter is temporal resolution, not feature design.** With
  `telemetry_interval_seconds` typically 0.01–0.05s in this project's
  corpora, and the allocation loop often finishing faster than one polling
  interval, most `oom` runs get **0 or 1** telemetry sample *before* the
  outcome is already decided — `prediction_features_v2.py`'s own docstring
  already documented this correctly before this audit. A single sample
  (or none) cannot show a *growth rate*, and even a single RSS reading
  taken essentially at the moment of failure/completion is close to
  reading the outcome itself, not predicting it.
- **This is a genuine "insufficient observability," not "insufficient
  modeling," finding — exactly the P3-W1 hypothesis to check first.** It
  is not fixed by feature engineering; it would require either (a) slowing
  the allocation loop to a real, paced admission-check pattern (changing
  what is being simulated, not measuring it more finely — out of scope, it
  would stop being an honest simulation of a fast OOM), or (b) sampling at
  sub-millisecond resolution (impractical and would swamp the corpus
  generation with overhead, and would not reflect what any real
  production monitoring agent could realistically achieve either — most
  real OS-level memory monitors sample in the 100ms–1s range, not
  sub-millisecond). **Recommendation:** report OOM predictability
  separately for the (small) subset of runs that *did* get ≥2 telemetry
  samples before the outcome vs. the (larger) subset that got 0–1 — mixing
  them, as the current single-model-per-family evaluation does, guarantees
  a diluted, near-chance aggregate regardless of whether real signal
  exists in the observable subset.

### `resource_unavailable` / RESOURCE_UNAVAILABLE — WAS "NO TEMPORAL WINDOW"; NOW HAS A REAL PRECURSOR (fixed this step)

Mechanism (before this step's fix): a real socket `bind()` to a
contended port, at process start, with **zero** telemetry-sampling
iterations able to occur before the bind() call returns (the runtime's own
docstring, and `prediction_features_v2.py`'s docstring, already correctly
identified this: "decided by a single bind() syscall at/near execution
start").

- **Fixed this step (P3-W2):** added a real, independently-timed pre-flight
  probe — the parent process performs the exact same `bind()` attempt on
  the same port, strictly *before* spawning the child, and emits the
  result (`resource_available: bool`) as a `telemetry_observed` event
  timestamped before `execution_started`. This is not label leakage: it
  is an honest, real syscall against the real contended resource, timed
  genuinely before the decision boundary — the same pattern a real
  production scheduler already uses (checking resource availability before
  dispatch). See `test_resource_unavailable_gets_a_real_preflight_probe_before_the_subprocess_runs`.
  Full classification of the probe's own outcome (`GPU_AVAILABLE`-style
  explicit states, timeout/error handling) was not added here since a raw
  TCP `bind()` either succeeds or raises `OSError` — there is no
  timeout/race analogous to the GPU probe's external-tool subprocess call.
- **Caveat, stated honestly:** in this project's own synthetic corpus,
  whether the port is occupied is itself set by the corpus generator
  (`_occupy` in `scenario_for_seed`) and does not change between the
  pre-flight probe and the child's own bind() a few milliseconds later —
  so in this *specific* synthetic setting, the pre-flight probe should be
  expected to correlate near-perfectly with the outcome. That is an honest
  property of this controlled environment, not evidence the model is
  fabricated: a real production port-contention monitor would show the
  same near-perfect precursor relationship for the same reason (contention
  state doesn't typically flip in milliseconds). This should be reported
  as such in Step 3 — a real, understood, environment-explainable
  near-ceiling result — not an inflated, unexplained one.

### `flaky` / INTERMITTENT_TRANSIENT — EXOGENOUS / NOT OBSERVABLE THIS-EPISODE (confirmed, not a gap to close)

Mechanism: `ControlledRuntime._flaky_attempts[workload_id]` is a real,
monotonically-growing counter tracked in the **parent** process — the
child subprocess receives `attempt_index`/`fail_count` as its own launch
parameters and decides success/failure from them, but neither value is
ever written into any canonical event this episode's telemetry stream
exposes to a feature extractor (`workload_received`'s payload carries only
`self.config.as_dict()` and the environment identity, never the actual
per-call `params`/`extra` dict).

- **Why this is not simply "missing telemetry" to add:** `fail_count` is
  the literal ground-truth parameter that *defines* when the label flips
  (`attempt_index <= fail_count` ⟺ failure). Exposing it as a decision-time
  feature would not be a precursor, it would be the label formula itself.
  `attempt_index` alone (without `fail_count`) carries no information the
  model doesn't already implicitly have via workload identity plus
  history.
- **The one legitimate signal that could help here is cross-run, not
  within-episode:** `src/phase4/memory.py`'s `FailureMemoryStore`
  already tracks, per `(workload_id, environment_id, failure_class)`,
  prior validated outcomes — genuinely available before the current
  episode's own outcome, and explicitly excludes the current `run_id`
  (contract item 1/6). A feature like "how many of the last N runs of this
  `workload_id` failed" would be a legitimate precursor for a workload
  whose flakiness *pattern* repeats, without encoding this specific
  episode's own label. **Recommendation for Step 3:** if `flaky`
  prediction is pursued at all, it should be via a memory-derived feature
  in a repeated-workload evaluation design (which also serves the Step 6
  memory-remediation goal), not via anything added to this episode's own
  process telemetry — there is nothing more to add there.

### `network` / NETWORK_ERROR — DETERMINISTIC BY DESIGN

Mechanism: a single `connect()` attempt to a fixed, unroutable address
(`10.255.255.1:65530`), always fails identically in this sandbox. No
telemetry window exists (one syscall, no loop), and even if it did, the
outcome does not vary — there is nothing to predict. Correctly reported as
`NOT_PREDICTABLE_SINGLE_CLASS` by `prediction_eval_v2.py`, not a gap.

### `corruption` / DATA_CHECKSUM_MISMATCH — DETERMINISTIC BY DESIGN

Mechanism: writes real bytes, computes a real SHA-256, deliberately flips
one byte, always mismatches. Same conclusion as `network`: no window, no
variance, correctly reported as `NOT_PREDICTABLE_SINGLE_CLASS`.

### `fail` / NONZERO_EXIT — DETERMINISTIC BY DESIGN

`sys.exit(7)`, unconditionally. Same conclusion.

### `gpu` / GPU_DEVICE_UNAVAILABLE — ENVIRONMENT-DEPENDENT, NOW EXPLICITLY CLASSIFIED (fixed this step)

Mechanism: probes for a real GPU management tool and, if found, invokes it.
Whether this mode is single-class (deterministic on a given machine) or
genuinely bimodal depends entirely on the host: a machine with no GPU tool
on PATH is deterministically `UNKNOWN`→failure; a machine with a real GPU
(this development machine) is deterministically `GPU_AVAILABLE`→success;
only a probe race (`GPU_PROBE_TIMEOUT`/`GPU_PROBE_ERROR` competing with a
clean result on a borderline system) could make it genuinely bimodal on one
fixed machine across repeated runs. See engineering fix #2 and
`src/phase4/gpu_probe.py` for the now-explicit state classification
(`GPU_AVAILABLE`/`GPU_UNAVAILABLE`/`GPU_PROBE_TIMEOUT`/`GPU_PROBE_ERROR`/
`UNKNOWN`) and full provenance (host identity, tool, probe version,
timestamp, timeout). Prior GPU AUROC results in this project's history are
explicitly not treated as evidence of anything (per the master remediation
register's own instruction) — they were a boolean collapse of these five
distinct states on an unknown/unrecorded host configuration, which is
exactly the kind of unreplicable measurement this refactor makes
impossible to produce again (every future GPU-mode run now records which
of the five states it actually observed, and whether it was a forced test
override).
- **A pre-flight probe (same pattern as `resource_unavailable`) was
  considered and deliberately NOT added:** GPU hardware presence does not
  fluctuate within a run's lifetime the way port contention can be
  contended/released, so a pre-flight probe would face the exact same
  timeout/race exposure as the in-run probe already has — it would not add
  new information, only move the same probe earlier. Not adding
  speculative telemetry that would not change what's knowable is itself
  part of following the audit-before-features discipline this step is
  supposed to enforce.

## Summary table

| Failure class | Classification | Real precursor added/confirmed this step | Step 3 recommendation |
|---|---|---|---|
| `cpu` | REAL PRECURSOR | RSS defect fixed (was constant-zero) | Evaluate `elapsed_ratio`-only model alongside full-feature model |
| `oom` | REAL PRECURSOR, timing-limited | RSS/RSS-growth now real, not constant-zero | Split evaluation by samples-before-outcome (0–1 vs ≥2) instead of one pooled model |
| `resource_unavailable` | Was NO WINDOW → now REAL PRECURSOR | Pre-flight bind() probe added | Evaluate the new probe feature; expect and report a near-ceiling, environment-explained result honestly |
| `flaky` | EXOGENOUS / not this-episode | None added (would leak label) | Consider a memory-derived cross-run feature in a repeated-workload design (Step 6), not process telemetry |
| `network` | DETERMINISTIC BY DESIGN | — | No action; correctly reported as undefined |
| `corruption` | DETERMINISTIC BY DESIGN | — | No action; correctly reported as undefined |
| `fail` | DETERMINISTIC BY DESIGN | — | No action; correctly reported as undefined |
| `gpu` | Environment-dependent | Explicit-state classification + provenance | Report per-state breakdown; do not compute an AUROC across hosts with different states pooled |

## What this audit deliberately does not do

Per the master remediation order, this audit does not re-train, re-evaluate,
or report any AUROC/AUPRC/Brier/ECE number for any failure class — that is
Step 3's job, using this audit's findings to decide, before looking at test
results, which features to include per family and how to split/report OOM's
timing-limited subset. Doing that here would violate the
observability-before-predictability sequencing this remediation phase
exists to enforce.
