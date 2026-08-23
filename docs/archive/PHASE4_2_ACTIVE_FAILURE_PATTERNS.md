<a id="active-phase-42--failure-pattern-learning-real-data-foundation"></a>
# ACTIVE Phase 4.2 — Failure Pattern Learning (Real-Data Foundation)

**Status: COMPLETE.** This is the results document for the milestone
authorized by `docs/PROJECT_HISTORY.md`'s "ACTIVE PHASE 4.2 — Failure
Pattern Learning: Reassessment & Implementation Plan" section (original
file `docs/PHASE4_2_ACTIVE_PLAN.md`). It reports implementation,
experiments, ablations, and a final verdict — it does not re-derive the
plan (see that section for the full audit/reassessment).

Companion artifacts: `configs/phase4_2_active_pattern_protocol.json`
(frozen protocol), `src/failure_patterns/` (new implementation),
`benchmarks/phase4_2_active_pattern_evaluate.py`,
`benchmarks/phase4_2_active_leakage_audit.py`,
`experiments/results/phase4_2_active/*.json` (all raw results),
`tests/unit/test_failure_patterns_{schema,discovery}.py`,
`tests/integration/test_phase4_2_active_integration.py`.

---

## 1. Historical context

```
OLD Phase 4.0 (synthetic episodic data)
  └─▶ OLD Phase 4.1 (src/experience/) → H1 PARTIALLY SUPPORTED (frozen)
       └─▶ OLD Phase 4.2 (src/patterns/) → H2 INCONCLUSIVE (frozen)
              │
              ▼ [project pauses old Phase 4 sequence]
REAL DATA EXPANSION (AgentRx, AIOps 2020, Alibaba GPU 2020)
  └─▶ REVISED real-data Phase 3
       └─▶ ACTIVE Phase 4.1 (src/failure_experience/) → PASS
              └─▶ ACTIVE Phase 4.2 PLAN (#project-history--consolidated-documentation) → approved
                     └─▶ THIS DOCUMENT: ACTIVE Phase 4.2 implementation + results
```

## 2. Relationship to old Phase 4.2

The historical Phase 4.2 result — `INCONCLUSIVE`, because pre-registered
`minimum_evaluable_n=10` covered test rows was not met (actual: 7) — is
**frozen and untouched**. `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/`,
`configs/phase4_2_pattern_protocol.json`, and
`experiments/results/phase4_2/*` were not modified by this milestone; the
leakage audit's check 6 (§15 below) verifies this by hash comparison.

This document is **new research**, not a correction of the old result:

| | Old Phase 4.2 | Active Phase 4.2 (this document) |
|---|---|---|
| Data | Synthetic (`experiments/results/phase4_0/episodes.json`), CRITICAL-tier only | Real Alibaba GPU 2020 trace (11,750 rows) primary; AIOps/AgentRx descriptive |
| Candidate key | `(workload_id, diagnosed_cause)` | `(task_name, gpu_type)` |
| Claim | symptom → cause purity | context → failure-rate elevation |
| `minimum_evaluable_n` | 10 (met: 7, INCONCLUSIVE) | 50 (met: 21, **INCONCLUSIVE**) |
| Verdict | 🟡 INCONCLUSIVE | 🟡 **INCONCLUSIVE** (see §16) |

Both experiments independently land on INCONCLUSIVE, for a related but
distinct reason each time (insufficient row-level coverage on synthetic
data vs. an insufficient number of distinct high-granularity context keys
on real data — see §19). This is a genuine, disclosed finding, not a
coincidence papered over.

## 3. Research question

Does context (a task's `(task_name, gpu_type)` combination in a real GPU
cluster trace) reliably predict an elevated failure rate, above chance and
above a naive frequency baseline, in a way that a train-discovered claim
generalizes to held-out validation/test data?

## 4. Hypotheses

- **H2-Alibaba** (primary, rigorously evaluated): certain `(task_name,
  gpu_type)` context combinations exhibit a failure-rate elevation,
  discoverable on train data, that replicates on held-out
  validation/test data at a rate better than a naive frequency-count
  baseline.
- **H2-AIOps** (descriptive/exploratory): fault entities exhibit recurring
  associations with specific fault types; fault onsets are temporally
  clustered.
- **H2-AgentRx** (descriptive/exploratory): agent domains exhibit
  recurring associations with specific behavioral failure-mode categories.

## 5. Dataset descriptions

**Alibaba GPU 2020** — `data/processed/alibaba_gpu2020/task_table.main_sample.csv`,
11,750 rows: 8,905 Terminated, 2,594 Failed, 251 Running. 7 distinct
`task_name` values (`tensorflow` 6,165 rows), 6 distinct `gpu_type` values
including the empty-string "no GPU" category (`MISC` 6,723 rows). Two
frozen splits exist: temporal (primary, by submission time) and
random-stratified (secondary sensitivity check).

**AIOps 2020** — `data/audit/aiops_kpi/positive_windows.json`, 81 injected
fault windows, 16 distinct entities, 5 distinct fault types, real UTC
onset timestamps across 11 distinct days. No frozen split.

**AgentRx** — `data/processed/agentrx/{tau_retail,magentic}_joined.jsonl`,
73 failure-annotated agent trajectories across 2 domains, human-annotated
multi-label failure categories. No real timestamp, no frozen split.

**Synthetic (Phase 4.0)** — `experiments/results/phase4_0/episodes.json`,
960 rows, frozen. Used only for methodological validation (§13), never as
real-world evidence.

## 6. Pattern definitions

**Pattern Type 1 (Alibaba, primary)**: a `(task_name, gpu_type)` context.
Computed over ALL rows for a split (Failed + Terminated + Running), not
only failures — the failure *rate* for that context is compared against
the split's pooled baseline rate. See
`configs/phase4_2_active_pattern_protocol.json`'s `pattern_definition`.

**Pattern Type 2 (AIOps/AgentRx, descriptive)**: a recurring association
key — `(entity, fault_desrcibtion)` for AIOps, `(domain, failure_category)`
for AgentRx — reported as a bare occurrence count, no train/test claim.

## 7. Architecture

New package `src/failure_patterns/` (never imports the old, frozen
`src/patterns/` — verified by `tests/integration/test_phase4_2_active_integration.py::test_new_package_does_not_import_old_patterns_package`):

- `schema.py` — `EvidenceTier`, `PatternQuery` (structurally decision-time-only,
  exactly 2 fields, no rate/outcome field exists to leak), `PatternCandidate`,
  `AlibabaTestOutcome`, `DescriptiveAssociation`.
- `discovery_alibaba.py` — Pattern Type 1: `discover()` (train-only),
  `confirm()` (validation-only), `evaluate_test()` (test-only, called once).
- `discovery_descriptive.py` — Pattern Type 2: `aiops_recurrence()`,
  `aiops_temporal_clustering()`, `agentrx_recurrence()`.
- `metrics.py` — baselines A/B/C/C′/C″ and precision/recall/false-pattern-rate/tier-calibration.

### Data-access decision (disclosed, not silently worked around)

`discovery_alibaba.py` reads `data/processed/alibaba_gpu2020/task_table.main_sample.csv`
directly (via the same `DATA_PATH`/`SPLITS_PATH`/hash/split-lookup helpers
already defined in `src.failure_experience.sources.real_alibaba`, imported
rather than re-implemented) instead of sourcing population counts through
`src.failure_experience.retrieval`. Reason: the active Phase 4.1
`FailureExperience` store is, by design, a store of FAILURE incidents only
— `real_alibaba.load_failed_rows()` filters to `status=='Failed'` before
any `FailureExperience` is constructed, and further downsamples to a fixed
300/500-row sample. Pattern Type 1 structurally requires the full
Failed+Terminated+Running population as its rate denominator, which no
amount of querying `FailureExperience` can supply — that denominator was
never ingested in the first place. This is disclosed in the protocol's
`data_access_decision` block and exercised by an integration test
(`test_alibaba_population_matches_failure_experience_context_keys`) that
cross-checks FailureExperience-ingested Alibaba failures against this
module's population, proving the two representations describe the same
underlying data.

AIOps and AgentRx have no such population/denominator requirement (both
are per-episode failure recurrence counting) and are sourced entirely
through `src.failure_experience.ingest.ingest_batch` +
`src.failure_experience.sources.{real_aiops,real_agentrx}.load_normalized()`,
exactly as the plan requires.

## 8. Protocol (frozen before real-data discovery)

`configs/phase4_2_active_pattern_protocol.json`, frozen before any
discovery code ran against train/validation/test data. Key parameters:

| Parameter | Value | Rationale (abbreviated — full text in the protocol file) |
|---|---|---|
| Candidate key | `(task_name, gpu_type)` | `job_name` does not recur (0/2594 failed rows share one); `task_name` does |
| `N_MIN_CANDIDATE` | 5 | bare "not a singleton" floor, scaled from old Phase 4.2's n≥2 for a two-outcome rate estimate |
| `N_MIN_TRUSTED` | 20 | standard small-sample convention for trusting a proportion estimate |
| `MARGIN_TRAIN` | 0.10 (10pp absolute) | pre-registered, dataset-independent practical effect size |
| `MARGIN_VALIDATION` | 0.05 (5pp) | half of train margin, reflecting far smaller validation-split n per key |
| `N_MIN_VALIDATION` | 5 | floor before a replication check is attempted at all |
| **`minimum_evaluable_n`** | **50** | margin-of-error argument: 95% CI half-width for a worst-case p=0.5 binomial proportion at n=50 is ≈0.139 — the number below which a precision/recall point estimate (and a 4-way tier split) is not treated as informative. Fixed as ONE exact number before any discovery/validation/test code ran, from a generic convention, independent of Alibaba's realized covered-candidate count. |

## 9. Data splits

**Primary**: `data/audit/alibaba_gpu2020/splits_temporal.json` — train
7,380 rows / val 1,559 / test 2,811 (by `job_name`, temporal). **Secondary
sensitivity check**: `splits_random_stratified.json` — train 8,221 / val
1,762 / test 1,767. Per instruction, the temporal split is never replaced
by the random split even though the random split produced a more
favorable result (§14).

## 10. Leakage prevention

- `discover()` and `confirm()` each `assert` every input row belongs to
  the correct split (`train` / `val` respectively) — passing a row from
  the wrong split raises `AssertionError` immediately, not silently.
- `PatternQuery` is a 2-field frozen dataclass (`task_name`, `gpu_type`
  only) — structurally cannot carry a rate/outcome/label; verified by
  field introspection in the leakage audit (check 3) and a unit test that
  constructing it with an extra field raises `TypeError`.
- Test rows are loaded into memory only inside
  `evaluate_test()`/`all_test_candidates()`, called exactly once per
  experiment run, after discovery and validation-confirmation are frozen.
- Full leakage-audit results: §15.

## 11. Baselines

| Baseline | Definition |
|---|---|
| A — no pattern learning | never flags anything |
| B — naive frequency | flag iff `n_train >= N_MIN_TRUSTED` (20), no rate check |
| C — proposed (tiered) | flag iff tier ∈ {INFERRED, CONFIRMED} |
| C′ — ablation (no trusted-n floor) | flag iff elevation clears margin, using only `N_MIN_CANDIDATE` (5) |
| C″ — ablation (CONFIRMED-only) | flag iff tier == CONFIRMED |
| D — embedding-based grouping | **NOT IMPLEMENTED** — optional per the plan, deprioritized as non-load-bearing for the primary hypothesis; disclosed in the protocol, not silently dropped |

## 12. Metrics

Exact formulas, numerators, denominators, and limitations are specified in
`configs/phase4_2_active_pattern_protocol.json`'s `metrics` block
(rate-elevation precision/recall, false-pattern-rate, tier calibration,
pattern stability).

## 13. Experiments and results

### 13.1 Alibaba — primary (temporal split)

- Train baseline failure rate: **16.83%**. Validation baseline: **17.13%**.
  **Test baseline: 38.60%** — a large distributional shift from train/val
  to test (see §19, a genuine limitation this temporal split exposes).
- 31 candidates discovered on train (`n_train >= 5`): 17 OBSERVED, 6
  provisionally INFERRED, 8 UNCERTAIN.
- After validation-confirmation: **all 6** provisionally-INFERRED
  candidates replicated and were upgraded to **CONFIRMED**; 0 remained
  plain INFERRED.
- **`n_evaluable_test_candidates = 21`** (contexts with `n_test >= 5`),
  against the pre-registered **`minimum_evaluable_n = 50`**.
  **⇒ 21 < 50 — the minimum-evaluable-n criterion is NOT met.**

| Method | n_flagged | precision | recall | false_pattern_rate |
|---|---|---|---|---|
| A (no learning) | 0 | — | 0.0 | — |
| B (naive frequency) | 23 | 0.143 | 1.0 | 0.857 |
| **C (proposed, tiered)** | 6 | **0.333** | 0.667 | 0.667 |
| C′ (no trusted-n floor) | 6 | 0.333 | 0.667 | 0.667 |
| C″ (CONFIRMED-only) | 6 | 0.333 | 0.667 | 0.667 |

Tier calibration (test-split elevation rate): OBSERVED 0.067 (15
evaluable), INFERRED — (0 evaluable, no plain-INFERRED candidates
survived confirmation), CONFIRMED **0.333** (6 evaluable). CONFIRMED >
OBSERVED holds directionally, but INFERRED is empty so the full
three-way ordering cannot be checked.

C, C′, and C″ produced **identical** flagged sets on this run — every
provisionally-INFERRED candidate both cleared `N_MIN_TRUSTED` and
replicated on validation, so the three baselines' distinguishing
mechanisms (the trusted-n floor and the validation-replication
requirement) made no observable difference here. This null-ablation
result is reported as found, not adjusted (§17).

### 13.2 Alibaba — secondary sensitivity check (random-stratified split)

Train baseline **16.77%**, val **16.63%**, **test 16.92%** — no material
distribution shift (unlike the temporal split). `n_evaluable_test_candidates
= 20` (also below 50). Point estimates:

| Method | n_flagged | precision | recall |
|---|---|---|---|
| B (naive frequency) | 23 | 0.316 | 1.0 |
| **C (proposed, tiered)** | 6 | **0.833** | 0.833 |
| C″ (CONFIRMED-only) | 4 | 1.0 | 0.667 |

On this split C clearly outperforms B on precision. **This is not
substituted in as the primary result** — the temporal split remains
primary per the frozen protocol, precisely because it is more exposed to
detecting scientifically important effects like the test-period base-rate
shift found in §13.1, which the random split's stratification
structurally hides. The gap between the two splits' results is itself a
disclosed finding (§19).

### 13.3 AIOps — descriptive

81 experiences ingested, 0 ingestion errors. 36 distinct `(entity,
fault_desrcibtion)` keys, **24 recurring (n≥2)** — top: `(docker_001,
network delay)` n=5. **Temporal clustering** (real onset timestamps,
coefficient-of-variation vs. a homogeneous-Poisson null of CV=1): of 16
entities, several with ≥3 onsets show CV > 1 (e.g. `docker_001`: 10
onsets, CV=2.41; `docker_003`: 6 onsets, CV=1.84) — consistent with
**clustered/bursty** fault onsets, not uniform arrival. This is the one
metric where AIOps's genuine (non-generator) temporal structure adds
information the synthetic source structurally cannot (old Phase 4.2 found
zero clustering on synthetic data, by construction).

### 13.4 AgentRx — descriptive

73 experiences ingested, 0 errors. 2 domains (`tau_bench_retail` n=29,
`magentic_one_web_file_agent` n=44). Most frequent recurring associations:
`(magentic_one_web_file_agent, Guardrails Triggered)` n=23,
`(magentic_one_web_file_agent, Instruction/Plan Adherence Failure)` n=25
(multi-label). Framed explicitly as **behavioral/agent failure-mode
recurrence**, not infrastructure failure patterns (AgentRx has no
telemetry). Temporal clustering: **NOT CURRENTLY EVALUABLE** (no real
timestamp exists in the raw data).

## 14. Ablations

| Ablation | Result |
|---|---|
| Tiered (C) vs. CONFIRMED-only (C″) | identical flagged set on temporal split (§13.1); on random-stratified, C″ trades recall (0.667 vs 0.833) for perfect precision (1.0 vs 0.833) — a real, disclosed difference on the secondary split only |
| N_MIN_TRUSTED floor (C vs. C′) | identical on both splits — no context in the 5–19 `n_train` range cleared the elevation margin regardless of the floor, on either split |
| Temporal vs. random-stratified split | materially different point estimates (§13.1 vs §13.2), driven primarily by the test-period base-rate shift the temporal split exposes — reported as a genuine sensitivity finding, not resolved by picking the better-looking split |
| N_MIN_TRUSTED sweep {5,10,20,40} | **identical** flagged set and metrics at every value tested (`experiments/results/phase4_2_active/ablation_n_min_trusted_sweep.json`) — the primary result is insensitive to this threshold in the tested range, a genuine finding, not a bug (verified: no candidate in the 5–19 or 20–39 `n_train` band is close enough to the elevation margin to be threshold-sensitive) |
| Pattern stability (train split in half) | 23 candidates common to both halves; 18/23 (78.3%) retained the same tier — moderate but not high stability, disclosed as a limitation |

## 15. Leakage audit

`benchmarks/phase4_2_active_leakage_audit.py`,
`experiments/results/phase4_2_active/leakage_audit.json`: **all 7 checks
passed** (`all_passed: true`).

1. Test labels cannot enter discovery — PASS (`discover()` raises on a
   non-train row).
2. Validation cannot leak into train discovery — PASS (`confirm()` raises
   on a non-validation row).
3. `PatternQuery` structurally excludes outcome/rate fields — PASS
   (exactly 2 fields, `task_name`/`gpu_type`).
4. **Non-vacuous contamination test** — PASS. Injecting 40 synthetic
   Failed rows (2× its own `n_train=20`) for the smallest OBSERVED-tier
   context, `(xComputeWorker, "")`, into a contaminated train set changed
   its discovered tier from OBSERVED to INFERRED — proving the discovery
   mechanism is genuinely sensitive to train-split contents, which is what
   makes checks 1–2's split assertions load-bearing rather than decorative.
5. Temporal split boundary respected — PASS (every `job_name` in the
   frozen manifest belongs to exactly one split).
6. Historical frozen artifacts unmodified — PASS (byte-identical hashes
   for `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/*.py`,
   `configs/phase4_2_pattern_protocol.json`,
   `experiments/results/phase4_2/*.json`).
7. No post-test tuning — PASS (protocol file's SHA-256 recorded at
   test-evaluation time matches its hash on disk now).

## 16. Test results

`27` new unit + integration tests
(`tests/unit/test_failure_patterns_schema.py`,
`tests/unit/test_failure_patterns_discovery.py`,
`tests/integration/test_phase4_2_active_integration.py`), covering schema
validation/leakage-structure, discovery tier assignment on hand-computed
fixtures (candidacy floor, UNCERTAIN/OBSERVED/INFERRED/CONFIRMED
transitions, split-boundary assertions), baseline/metric correctness, and
integration against real `FailureExperience` data for all three real
sources. **Full repository suite: 387 passed, 0 failed** (includes the 27
new tests; no regressions in the pre-existing 360).

## 17. Statistical interpretation

The test-split point estimates (precision 0.333, recall 0.667 for method
C on the primary temporal split) are computed over only **6 flagged
candidates and 3 true-elevated candidates** — far below the pre-registered
`minimum_evaluable_n=50`. Per the frozen acceptance criteria, this makes
the comparison **not informative on its own terms**: at n this small, a
single candidate's classification changes the precision estimate by
±0.167–0.33. No statistical test beyond the pre-registered margin/tier
framework was run given this — a formal significance test over a
6-candidate sample would not add real information. The random-stratified
sensitivity check (§13.2) shows what a similarly-small-n comparison looks
like without the temporal base-rate shift confound, but is explicitly not
substituted for the primary result.

## 18. Limitations

- **`minimum_evaluable_n=50` was structurally very hard for this dataset
  to reach**, independent of any statistical significance question: with
  only 7 `task_name` and 6 `gpu_type` values, there are at most ~37
  distinct `(task_name, gpu_type)` combinations in the entire dataset —
  the ceiling on `n_evaluable_test_candidates` is set by the *cardinality
  of the candidate-key space*, not by the sample size (11,750 rows). No
  amount of additional Alibaba rows sampled the same way would raise this
  ceiling much past ~30–37. This is a genuinely important, disclosed
  finding: real data's larger row count does not automatically translate
  into a larger *evaluable-candidate* count when the candidate key itself
  is coarse-grained.
- **Test-split base-rate drift** on the primary temporal split (38.6% vs.
  16.8–17.1% train/val) suggests the trace's later time period behaves
  materially differently — a real property of the data, not a code issue,
  but it complicates interpreting a fixed absolute margin (`MARGIN_TRAIN
  = 0.10`) consistently across splits with very different baselines.
- Pattern stability (train-half split) was only 78.3% — a majority but not
  a strong majority of candidates keep their tier under a coarse
  robustness perturbation.
- AIOps/AgentRx remain descriptive-only (no frozen split for either); this
  was a pre-registered scope limitation, not an oversight.
- The `FailureEmbedder`-based grouping ablation (D) was not implemented,
  per the plan's own "not the primary method, do not add unneeded
  complexity" guidance.

## 19. Unexpected findings

- The candidate-key cardinality ceiling (§18) was not anticipated in the
  approved plan, which expected Alibaba's much larger row count to
  straightforwardly fix old Phase 4.2's evidence-volume problem. It
  partially did (31 candidates discovered vs. old Phase 4.2's handful),
  but the *coverage* metric (`n_evaluable_test_candidates`) is bounded by
  a different quantity than raw row count, and remained below the
  pre-registered bar.
- The temporal split's large train→test base-rate shift (16.8% → 38.6%)
  is itself a substantive, real-data finding about the Alibaba trace's
  later time period, surfaced only because the temporal split (chosen for
  principled leakage-avoidance reasons, §9) was used as primary.
- Three of the five method variants (C, C′, C″) and the entire
  `N_MIN_TRUSTED` sweep collapsed to identical results — an honest signal
  that, on this particular real population, the tiering machinery's finer
  distinctions are not (yet) doing separable work; a larger or
  differently-shaped population might separate them.

## 20. Failed approaches

None of the implemented mechanisms failed outright (no leakage violation,
no fabricated evidence, no broken pipeline). The one approach considered
and explicitly not pursued was forcing `job_name`-level recurrence (ruled
out during planning — `job_name` essentially never recurs among failed
rows) and the embedding-based grouping ablation (deprioritized, §11/§18).

## 21. Research-integrity verification

- No threshold, baseline, candidate, or hypothesis was changed after
  observing test-split results (protocol content hash matches at
  test-evaluation time and now — leakage audit check 7).
- Old Phase 4.2 is untouched (leakage audit check 6, byte-identical
  hashes).
- No fabricated data, labels, or timestamps — AIOps fault
  types/entities and AgentRx failure categories are dataset-provided
  annotations; Alibaba status is the raw `status` field.
- Cross-dataset generalization is not claimed anywhere in this document —
  Alibaba, AIOps, and AgentRx results are each reported independently,
  with no pooled or averaged metric across them.
- The random-stratified split's more favorable result (§13.2) was not
  substituted for the temporal split's primary result, even though it
  looks better.
- The N_MIN_TRUSTED sweep's flat/identical results were reported as
  found, not treated as a signal to adjust the frozen primary threshold.

## 22. Final verdict

**INCONCLUSIVE.**

Per the frozen acceptance criteria
(`configs/phase4_2_active_pattern_protocol.json`'s `acceptance_criteria`):
`n_evaluable_test_candidates = 21 < minimum_evaluable_n = 50` on the
primary temporal split. This is a valid, pre-registered, honestly-computed
insufficiency finding — the implementation is complete and correct
(leakage audit all-pass, 387/387 tests green, real end-to-end pipeline
from `FailureExperience`/raw CSV through discovery → validation → frozen
test evaluation), but the evidence volume at the required candidate
granularity does not clear the bar fixed before evaluation began. This
mirrors, for a structurally different reason (candidate-key cardinality
ceiling vs. row-level coverage), the same category of honest INCONCLUSIVE
verdict old Phase 4.2 reached on synthetic data (§2).

The directional point estimates (method C beats baseline B on precision
on both splits; C, C′, C″ show a real precision/recall trade only on the
sensitivity split) are reported for completeness but are explicitly **not
treated as informative** given `n < minimum_evaluable_n`, per the frozen
protocol's own rule that the evidence-volume gate — not which way the
numbers lean — determines the verdict.

### Readiness for the next phase

The implementation, data-access layer, leakage-audit methodology, and
descriptive AIOps/AgentRx findings are all reusable, validated
infrastructure for a future milestone. Two concrete, disclosed paths would
plausibly resolve the INCONCLUSIVE verdict without touching this
milestone's frozen protocol or results:

1. A coarser or richer candidate key (e.g. adding a resource-profile
   bucket dimension to `(task_name, gpu_type)`) would raise the
   candidate-key cardinality ceiling identified in §18 — a genuine scope
   change requiring its own pre-registered protocol, not a retrofit onto
   this one.
2. Building the frozen AIOps/AgentRx splits recommended-but-not-required
   by the approved plan would upgrade those two sources from
   descriptive-only to formally testable, independent of the Alibaba
   result.

Neither is undertaken here — this milestone's scope was the plan's
smallest research-valid version, executed to completion and honestly
reported.


---

# Post-Phase-4.2 Reassessment — What Should the Next Milestone Be?

**Status: PLANNING ONLY. No code, datasets, protocols, or historical/active
results were modified to produce this document.** Read-only analysis of
`README.md` (which now contains the former `docs/PROJECT_HISTORY.md` and
`docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` content, merged and deleted as
separate files in a prior session step — see that file's own top banner),
`configs/phase4_2_active_pattern_protocol.json`, `src/failure_patterns/`,
`src/failure_experience/`, and (read-only, for historical comparison) the
frozen old `src/patterns/` / old Phase 4.2 documentation.

> **ACTIVE PHASE 4.2 = COMPLETE. VERDICT = INCONCLUSIVE.** Nothing in this
> document changes, reinterprets, or "fixes" that verdict. This document
> answers a different question: given that verdict and everything else
> now known, what is the strongest next milestone?

---

## 1. Executive summary

Active Phase 4.2 (`(task_name, gpu_type)` failure-rate-elevation discovery
on the real Alibaba GPU 2020 trace) is complete, methodologically sound
(leakage audit 7/7, 387/387 tests green, no test-set tuning), and
**INCONCLUSIVE**: the pre-registered `minimum_evaluable_n=50` covered-test-
candidate bar was not met (actual: 21). This was not a data-volume problem
(11,750 rows) but a **candidate-key cardinality problem** — the
`(task_name, gpu_type)` key only ever has ~30–37 possible values in this
dataset, capping the evaluable-candidate count regardless of row count.
The temporal split (primary, correctly chosen for leakage reasons) also
exposed a large train→test base-rate shift (16.8% → 38.6%) that a
random-stratified split would have hidden.

The recommended next milestone is **not** another attempt to rescue
Alibaba pattern-learning to a PASS, and **not** automatically "Phase 4.3."
Weighing scientific value, dependence on existing validated work, data
availability, and contribution to the eventual autonomous self-healing
loop, this document recommends:

**Primary recommendation: build a controlled, frozen recovery-outcome
dataset and evaluation harness** (a new, small, purpose-built data
milestone — not a redo of pattern learning) — because every real dataset
in the project has `RecoveryStatus.NOT_OBSERVED` / `ValidationResult.NOT_PERFORMED`
for effectively all records, which is the single capability gap on the
critical path from "failure memory" (Active Phase 4.1, PASS) toward
"autonomous recovery" (the project's stated ultimate objective), and no
amount of further pattern-learning on the existing real data can supply
it — it is a **structural absence in the source data**, not an analysis
limitation.

**Secondary option**: Option A (richer Alibaba context) — plausible,
bounded, cheap, but a genuinely new pre-registered experiment, not a
guaranteed fix; worth pursuing in parallel or after, not instead of, the
primary recommendation. **Deferred**: Option B (frozen AIOps/AgentRx
splits) — real value, but secondary to the recovery-data gap. **Rejected
for now**: any threshold/complexity change aimed at Alibaba's existing
result, and any move to pool datasets or add model complexity.

---

## 2. Current project state

```
Phase 1 (prototype audit) -> Phase 2 (migration/integration)
  -> Phase 3.1-3.6 (synthetic) -> FROZEN
  -> OLD Phase 4.0/4.1/4.2 (synthetic) -> FROZEN
       (4.1: H1 PARTIALLY SUPPORTED | 4.2: H2 INCONCLUSIVE)
  -> Real-data expansion (AgentRx, AIOps 2020, Alibaba GPU 2020)
  -> Revised real-data Phase 3.1-3.6 -> FROZEN
  -> ACTIVE Phase 4.1 (src/failure_experience/) -> PASS
  -> ACTIVE Phase 4.2 (src/failure_patterns/) -> INCONCLUSIVE   <-- WE ARE HERE
  -> ??? (this document's subject)
```

Everything through Active Phase 4.2 is complete, tested, and frozen where
appropriate. No implementation work is authorized by this document.

## 3. Historical Phase 4 lineage (preserved, not reinterpreted)

| Generation | Data | Candidate/claim | Verdict | Status |
|---|---|---|---|---|
| Old Phase 4.1 | synthetic | retrieval precision | H1 PARTIALLY SUPPORTED | frozen |
| Old Phase 4.2 | synthetic, CRITICAL-tier only | `(workload_id, diagnosed_cause)` symptom→cause purity | H2 INCONCLUSIVE (7 < `minimum_evaluable_n=10`) | frozen |
| Active Phase 4.1 | real (Alibaba/AIOps/AgentRx) + synthetic | `FailureExperience` representation/retrieval | PASS | active/current |
| Active Phase 4.2 | real Alibaba primary; AIOps/AgentRx descriptive | `(task_name, gpu_type)` context→rate-elevation | **H2-Alibaba INCONCLUSIVE** (21 < `minimum_evaluable_n=50`) | active/current, complete |

Both Phase 4.2 generations reached INCONCLUSIVE for related-but-distinct
reasons: old Phase 4.2 lacked row-level coverage on a tiny synthetic
CRITICAL-tier slice; active Phase 4.2 had ample rows but a coarse,
low-cardinality candidate key. Neither is "worse" than the other; they
are independent, honestly negative-on-evidence-volume results. Neither is
touched by this document.

## 4. Active Phase 4.1 findings (foundation, PASS)

- Canonical `FailureExperience` schema/storage/retrieval spans 4 sources
  (synthetic, AgentRx, AIOps, Alibaba), 961 experiences.
- **Structural gaps, confirmed by the field-population audit** (carried
  forward unchanged from the Active Phase 4.2 planning stage, §3 of the
  plan): no real dataset has diagnosis *confidence*; recovery is
  `NOT_OBSERVED` and validation is `NOT_PERFORMED` for all three real
  sources; only Alibaba has a frozen split; AIOps has the only genuine
  (non-synthetic) temporal structure; AgentRx has no telemetry and no
  usable timestamp.
- The schema already has slots for recovery/validation/diagnosis-
  confidence — extending a source adapter, not the schema, is what a
  future capability upgrade would require (§18 of the Active Phase 4.1
  report, "Phase 4.2+ readiness").

## 5. Active Phase 4.2 findings (complete, INCONCLUSIVE)

Alibaba (primary, temporal split): 31 candidates discovered on train
(`n_train>=5`), 6 CONFIRMED after validation-replication, 0 remaining
plain INFERRED, 17 OBSERVED, 8 UNCERTAIN. `n_evaluable_test_candidates=21`
against frozen `minimum_evaluable_n=50` → **INCONCLUSIVE by the frozen
rule**, independent of the point estimates. Point estimates for
completeness only (method C precision 0.333 vs. baseline B 0.143 on
temporal; 0.833 vs. 0.316 on the random-stratified sensitivity split, not
substituted as primary). Leakage audit 7/7 pass including a non-vacuous
contamination test. AIOps: 24 recurring `(entity, fault)` associations,
descriptive; real-timestamp temporal clustering shows CV>1 (bursty) for
several entities — a genuinely new finding real data made possible.
AgentRx: 2-domain behavioral failure-mode recurrence, descriptive, no
temporal claim (no real timestamp). Synthetic: methodological validation
only, never treated as real-world evidence.

## 6. What Active Phase 4.2 established

**A. Strong evidence**
- The pattern-discovery mechanism (schema, discovery, validation-
  confirmation, frozen one-time test evaluation) is implemented correctly
  and leak-free — the leakage audit's non-vacuous contamination check
  (tier flip on injected data) proves the split-boundary assertions are
  load-bearing, not decorative.
- `job_name` does not recur among failed Alibaba rows (confirmed on both
  the 11,750-row sample and the 1.26M-row full population, 7/256,755) —
  a genuine, load-bearing structural fact ruling out job-level recurrence
  keys permanently, not just for this experiment.
- AIOps fault onsets are temporally clustered (CV>1 for several entities
  with ≥3 onsets) using real wall-clock timestamps — the first time in
  this project's history a temporal-clustering claim has been checkable
  on genuine (non-generator) data.

**B. Directional but insufficient evidence**
- Method C (tiered rate-elevation) beats baseline B (naive frequency) on
  precision on both the primary temporal split (0.333 vs 0.143) and the
  sensitivity split (0.833 vs 0.316) — directionally consistent, but
  computed over 6 and 4-6 flagged candidates respectively, far below the
  bar the protocol itself pre-registered as informative.
- All 6 provisionally-INFERRED Alibaba candidates replicated to CONFIRMED
  on validation — directionally suggests the elevation signal, where it
  exists, is not noise, but n=6 is too small to generalize the claim
  "validation-replication reliably filters noise."

**C. Descriptive findings**
- AIOps `(entity, fault)` recurrence (24 pairs) and temporal clustering.
- AgentRx `(domain, failure_category)` recurrence, multi-label, 2 domains.
- Both are explicitly non-hypothesis-bearing (no frozen split for either).

**D. Methodological findings**
- The `(task_name, gpu_type)` candidate space has a hard cardinality
  ceiling (~30–37 keys) independent of row count — real data's larger N
  does not automatically translate into a larger *evaluable-candidate*
  count when the candidate key is coarse. This is the single most
  important methodological finding of the milestone.
- Three method variants (C, C′, C″) and a 4-point `N_MIN_TRUSTED` sweep
  collapsed to identical results on the primary split — on this
  population, the tiering machinery's finer distinctions did not
  separate, an honest null, not a bug (verified by inspecting the actual
  per-candidate rates against the margin).
- Temporal vs. random-stratified splits produce materially different
  point estimates, traced to a genuine train→test base-rate shift
  (16.8%→38.6%) the temporal split exposes and the stratified split
  structurally hides.

**E. Negative/null findings**
- The `N_MIN_TRUSTED` sweep {5,10,20,40}: zero sensitivity in the tested
  range — no candidate near the margin boundary in that band.
- Pattern stability under a train-half split: 78.3% — moderate, not
  strong, robustness.

**F. Inconclusive findings**
- H2-Alibaba itself: the primary, pre-registered verdict.

**G. Important limitations**
- No real recovery or validation data exists in any real source
  (`RecoveryStatus.NOT_OBSERVED` / `ValidationResult.NOT_PERFORMED`
  essentially everywhere) — a limitation of Active Phase 4.1's *inputs*,
  not its design, and unaffected by anything Phase 4.2 could have done.
- AIOps/AgentRx remain split-free and therefore permanently descriptive
  under the current data.
- The embedding-based grouping ablation (Option D in the frozen protocol)
  was not implemented — deprioritized, not evidence against it.

**H. New research opportunities** — see §10.

## 7. What Active 4.2 did NOT establish

- It did **not** establish that context→failure-rate elevation is false —
  INCONCLUSIVE is not a negative result on the hypothesis, it is an
  evidence-volume gate failure, by the protocol's own pre-registered
  design.
- It did **not** establish that `(task_name, gpu_type)` is the wrong
  representation — only that it is a *low-cardinality* one for this
  dataset; a richer key was never tested.
- It did **not** establish anything about AIOps/AgentRx as formal,
  scored hypotheses — both remain descriptive by construction (no split).
- It did **not** establish cross-dataset generalization of any kind — no
  such claim was made or is supported.
- It did **not** establish that the tiering machinery (vs. a flat
  threshold) is unnecessary in general — only that it made no observable
  difference on this specific, small, primary-split candidate set.

## 8. Key limitations (carried into planning)

1. Candidate-key cardinality ceiling (Alibaba).
2. No real recovery/validation data (all three real sources).
3. No frozen split for AIOps or AgentRx.
4. Train→test base-rate drift on Alibaba's temporal split.
5. Small absolute candidate counts throughout (6–31), which will continue
   to limit statistical power for any `(task_name, gpu_type)`-shaped
   question on this dataset, richer key or not.

## 9. New discoveries (beyond the pre-registered questions)

- The candidate-cardinality ceiling itself (§6.D) — not anticipated by
  the approved plan, which expected Alibaba's row count to straightforwardly
  fix the evidence-volume problem old Phase 4.2 had.
- The temporal base-rate shift — a genuine property of the Alibaba trace's
  later time period, only visible because the (correctly chosen) temporal
  split was used as primary.
- AIOps fault clustering (CV>1) — first genuine temporal-clustering
  evidence this project has produced on any dataset.

## 10. Candidate next milestones

**A. Richer Alibaba context / redesigned pattern hypothesis.** Add a
dimension (e.g. a coarse resource-profile bucket from `plan_cpu`/
`plan_mem`/`plan_gpu`/`inst_num`) to `(task_name, gpu_type)`. This is a
**new hypothesis** (H2-Alibaba-v2, not a re-run of H2-Alibaba) requiring
its own pre-registered protocol — increasing cardinality without a
principled bucketing risks trading the coverage problem for a sparsity/
singleton-candidate problem (more keys, thinner evidence per key,
`N_MIN_CANDIDATE`/`N_MIN_TRUSTED` would need independent re-derivation).
Leakage-safe in principle (all fields are decision-time-observable,
pre-outcome resource-plan values). Real data-engineering cost is low
(same CSV, same splits); scientific cost is a new pre-registration and
possibly another INCONCLUSIVE result if bucket granularity is chosen
poorly.

**B. Formal AIOps temporal-pattern benchmark.** Requires building and
freezing a train/val/test split for AIOps first (a genuine prerequisite
milestone, likely by entity or by day, given only 81 positive windows and
16 entities — small-sample risk is real and should be sized honestly
before committing). Would let the already-observed CV>1 clustering become
a formally tested claim rather than descriptive. Independent of Alibaba;
does not touch the INCONCLUSIVE result.

**C. Formal AgentRx behavioral-pattern benchmark.** Same split-freezing
prerequisite as B, compounded by (a) no real timestamp at all (rules out
any temporal claim permanently, not just currently) and (b) only 73
usable failure rows across 2 domains — a formal split there would leave
very thin per-domain/per-category cells. Lower expected information gain
than B for comparable engineering cost.

**D. Recovery-learning/evaluation foundation.** Build a small, controlled,
frozen dataset of failure→recovery-action→outcome triples (synthetic-
but-realistic, clearly labeled as controlled/non-observational, per §15
below), plus the evaluation harness to score a recovery-selection
mechanism against it. Directly targets the largest, most consistently
recurring limitation across *every* real dataset in this project (§6.G,
§8.2) and is the most direct unblocked step toward the project's own
stated end-to-end objective (§11 below). Does not depend on Alibaba's
verdict at all.

**E. Failure prediction** (predict failure before it happens, using
`Observations`/telemetry). Real telemetry exists for synthetic and
partially for Alibaba/AIOps; AgentRx has none. Would reuse Phase 3's
already-frozen risk-scoring infrastructure as a starting point rather
than building from scratch — but Phase 3's real-data track already
produced comparison results for exactly this class of question (see the
Phase 3 real-data comparison document); a new failure-prediction
milestone would need to explain what it adds beyond that existing,
frozen work, or risk being a re-run under a new name.

**F. Diagnosis improvement.** No real dataset has diagnosis *confidence*
(§4); all three real sources' "diagnosis" is either absent (Alibaba),
categorical human annotation (AgentRx, AIOps). There is no live
diagnosis *component* to improve — this would mean building one from
scratch, which is a much larger scope than "improvement" implies, and has
no existing partial implementation to extend.

**G. Uncertainty/abstention integration.** The frozen Phase 3 track
(3.1–3.6, real-data revision) already built and evaluated a calibrated-
confidence/abstention decision policy; this capability already exists and
is frozen/validated. Re-opening it is not obviously justified by anything
Active Phase 4.2 found — no evidence from this milestone bears on
abstention quality one way or the other.

**H. Do nothing / conclude the pattern-learning line is not currently
justified to continue as a standalone track.** A legitimate option per
the task's own framing (§2 of the brief) — evaluated in the decision
matrix below, not assumed.

## 11. Reconstructing the overall Phase 4 purpose

The stated end-to-end loop is: observe → detect → diagnose → estimate
uncertainty → abstain-if-unsafe → recall prior experience → choose
recovery → execute → validate → learn → improve. Mapped against current
state:

| Stage | Status |
|---|---|
| Observe / detect | done (Phase 1–3, frozen) |
| Estimate uncertainty / abstain | done (Phase 3, frozen) |
| Recall prior experience | done (Active Phase 4.1, PASS) |
| Recognize recurring context (pattern learning) | attempted, INCONCLUSIVE (Active Phase 4.2) |
| **Diagnose** (real, confident) | **not built — no real data supports it** |
| **Choose recovery action** | **not built — no real data supports it** |
| **Execute recovery** | **not built** |
| **Validate recovery outcome** | **not built — no real data supports it** |
| Learn from result / improve | depends entirely on the three bolded rows above existing first |

The highest-value missing capability is not further pattern-mining on
observation-only data — it is that **every downstream stage past
"recall prior experience" requires recovery/validation data that
currently does not exist in real form anywhere in this project.** This is
the load-bearing conclusion behind the primary recommendation (§12).

## 12. Comparative decision matrix

| Option | Scientific value | Depends on existing work | Data availability | Methodological risk | Expected info gain | Impl. complexity | Relevance to self-healing | Falsifiable? | Scope-creep risk |
|---|---|---|---|---|---|---|---|---|---|
| A. Richer Alibaba context | Medium | High (reuses discovery machinery) | Available now (same CSV) | Medium (bucket choice affects sparsity) | Medium | Low–Medium | Low–Medium (still pattern-only) | Yes | Low |
| B. Frozen AIOps split | Medium | Medium (reuses FailureExperience) | Needs new split-freezing work; small N (81) | Medium (small-sample) | Medium | Low–Medium | Low–Medium | Yes | Low |
| C. Frozen AgentRx split | Low–Medium | Medium | Needs new split-freezing work; very small N (73), no timestamp | Medium–High | Low–Medium | Low–Medium | Low | Yes | Low |
| D. Recovery-learning foundation | **High** | Builds on Phase 4.1 schema (already has the fields) | **Must be newly constructed** (no real data exists) | Medium (must not be confused with real evidence — see §15) | **High** (unblocks the entire downstream loop) | Medium–High | **High** — directly enables recovery/validation stages | Yes | Medium (must be scoped tightly, see §15) |
| E. Failure prediction | Medium | High (reuses Phase 3) | Partial (telemetry uneven across sources) | Medium (risk of redoing frozen Phase 3 work) | Low–Medium | Medium | Medium | Yes | Medium |
| F. Diagnosis improvement | Low (no foundation to improve) | Low | Poor (no confidence field populated anywhere real) | High (building from scratch) | Low | High | Medium | Uncertain | High |
| G. Uncertainty/abstention | Low (already done, frozen) | High | Good | Low | Low | Low | Low (already solved) | N/A | Low |
| H. Halt pattern-learning track | N/A (a decision, not an experiment) | — | — | Low | — | None | Neutral | N/A | None |

## 13. Recommended next milestone

**Primary: Option D — Recovery-Learning/Evaluation Foundation.**

Justification: it is the option most directly blocked by a **data gap**
rather than an analysis gap (unlike A/B/C, which are all "try harder on
existing observation-only data"), it has the highest expected information
gain relative to the project's own stated end-to-end objective (§11), it
builds on already-validated Active Phase 4.1 infrastructure (the schema
already has `RecoveryInfo`/`ValidationInfo`/`OutcomeInfo` fields — no
schema redesign needed, per the Active Phase 4.1 report's own §18
readiness note), and it does not depend in any way on Alibaba's
INCONCLUSIVE verdict being resolved first.

**Secondary**: Option A (richer Alibaba context) — cheap, bounded,
scientifically legitimate as a *new* pre-registered experiment; can run
in parallel with, or after, Option D without resource conflict.

**Deferred**: Option B (frozen AIOps split) — real value, smaller
expected gain than D, worth doing once D's higher-priority work is
underway.

**Explicitly rejected for now**: Option C (AgentRx formal split — data
too thin and lacks any timestamp, poor expected return), Option E
(failure prediction — risks redoing frozen Phase 3 work without a clear
delta), Option F (diagnosis improvement — no existing foundation to
build from, disproportionate scope), Option G (abstention integration —
already solved, no new evidence motivates revisiting it), Option H (halt
entirely — rejected because A remains legitimately cheap future work, not
because pattern-learning "must" continue).

## 14. What should NOT be done (and why)

- **Lowering `minimum_evaluable_n` below 50 to obtain a PASS** — it was
  frozen before discovery from a documented statistical rationale; changing
  it now would be retroactive protocol tuning on the exact experiment it
  gated, i.e. test-adjacent tuning. Any new evidence-volume criterion must
  belong to a *new* pre-registered experiment (e.g. Option A), never a
  retrofit onto the existing frozen one.
- **Changing the Alibaba candidate key and calling it the same H2** — a
  richer key (Option A) is legitimate only as an explicitly new hypothesis
  (H2-Alibaba-v2), not a silent redefinition of H2-Alibaba.
- **Selecting the random-stratified split as primary because it scored
  better** — already explicitly rejected during Active Phase 4.2 and
  re-affirmed here; it would hide the genuine base-rate-shift finding.
- **Pooling AgentRx/AIOps/Alibaba into one metric** — the three datasets
  differ in ground-truth quality, granularity, and split availability;
  no shared metric would be meaningful, and Active Phase 4.2 explicitly
  avoided this.
- **Adding a GNN/transformer because the simple method was inconclusive**
  — the inconclusive result was an evidence-volume gate failure, not a
  model-capacity failure; more model complexity cannot manufacture more
  distinct `(task_name, gpu_type)` values, so it would not address the
  actual bottleneck (§6.D).
- **Tuning thresholds using the existing test results** — the frozen
  protocol's test split was touched exactly once; re-tuning against it
  now would violate that discipline retroactively.
- **Creating labels after seeing test behavior** — not applicable to any
  option above as scoped, but stated as a standing constraint on Option D
  in particular (§15) given synthetic/controlled data is involved there.
- **Turning AIOps/AgentRx descriptive findings into formal evidence
  without first building a frozen split** — both remain descriptive until
  Option B/C's prerequisite work is separately authorized and executed.
- **Rewriting the old Phase 4.2 INCONCLUSIVE result** — out of scope
  categorically; not touched by anything in this document.

## 15. The recovery-learning gap — is it the right next research direction?

**Yes, conditionally on tight scoping.** Reasoning:

- Every real dataset in this project reports `RecoveryStatus.NOT_OBSERVED`
  or has no recovery field at all; `ValidationResult.NOT_PERFORMED` is
  likewise universal. This is not an artifact of how Active Phase 4.1
  ingested the data — the raw datasets themselves (Alibaba: no recovery
  field in the schema at all; AgentRx: `recovery_action`/`recovery_outcome`
  literally the string `"MISSING"`; AIOps: no recovery field) structurally
  do not contain this information. No further real-data ingestion work
  can produce it.
- The schema (`RecoveryInfo`, `ValidationInfo`, `OutcomeInfo`) already
  supports it — this is a data-construction task, not a schema-design task.

**What would be needed (planning only, not implemented here):**
- **Data**: a small, purpose-built set of failure→recovery→outcome
  episodes. Two legitimate sources: (a) controlled synthetic scenarios
  built the same disciplined way Phase 4.0 built its episodic generator
  (documented generator logic, known ground truth, frozen split), or (b)
  a genuinely observational source if one becomes available (not assumed
  here).
- **Failure scenarios**: should span the failure *types* already
  represented in `FailureExperience` (resource exhaustion / task
  termination analogous to Alibaba, fault-injection analogous to AIOps,
  behavioral/agent failure analogous to AgentRx) so any recovery-policy
  work can eventually be evaluated per-scenario-family, not pooled.
- **Recovery actions**: an explicit, small, enumerable action vocabulary
  (e.g. retry / reconfigure / rollback / escalate-to-human), matching
  `RecoveryInfo.candidate_actions`/`selected_action`'s existing shape —
  not invented ad hoc per scenario.
- **Validation criteria**: explicit, pre-registered pass/fail/partial
  criteria per scenario family (mirrors `ValidationInfo.validation_result`),
  decided before any recovery outcomes are generated/observed.
- **Preserving research validity**: any synthetic-controlled recovery
  data must be labeled, in its own frozen protocol and in every downstream
  report, as **controlled/methodological**, exactly as Phase 4.0's
  synthetic data is labeled today — never presented as real-world
  recovery evidence. If it is ever blended with real observational data,
  the blend must be disclosed per-record (a `source_dataset`/provenance
  field already exists for this in the schema), never silently pooled.

This is assessed as **plausible and well-motivated by the evidence**, not
proven necessary by a single experiment — consistent with the required
OBSERVED/INFERRED/RECOMMENDED/NOT-YET-TESTED distinction in §17.

## 16. New research question (for the recommended milestone)

**Research question**: Given a controlled, frozen set of failure→recovery
→outcome episodes spanning the failure-type families already represented
in `FailureExperience`, can a recovery-selection mechanism, evaluated
against a validation-criteria protocol pre-registered before any outcome
is observed, choose recovery actions that outperform a fixed/naive
recovery policy (e.g. "always retry") at a statistically meaningful
sample size?

## 17. Hypothesis(es) — for the recommended milestone

- **H4.3-Recovery** (working label, pending the numbering decision in
  §18): a context-aware recovery-selection mechanism, trained/discovered
  on the controlled recovery dataset's train split, achieves higher
  validated-success rate on held-out episodes than a fixed-policy
  baseline, at a rate exceeding a pre-registered minimum effect size.
- This is explicitly **NOT YET TESTED** — nothing in Active Phase 4.2 or
  this reassessment provides evidence for or against it; it is a proposal
  for a new, separately-designed experiment.

## 18. Milestone numbering

**Not automatically "Phase 4.3."** Two considerations: (a) the recovery-
learning foundation is closer to a **prerequisite data-construction
milestone** than a hypothesis-testing research phase in the same sense as
4.1/4.2 (it must exist before any recovery-policy *experiment* can be
pre-registered) — it may be more accurate to call it **Phase 4.3a
(recovery data & evaluation foundation)**, with a subsequent **Phase 4.3b
(recovery-policy hypothesis test)** once 4.3a exists, mirroring how this
project already separates "build the substrate" (Active Phase 4.1) from
"test a hypothesis on it" (Active Phase 4.2). (b) If Option A (richer
Alibaba context) is pursued in parallel, it is legitimately **Phase
4.2-v2** (a new, explicitly-labeled hypothesis on the same substrate,
per §14's prohibition on silently redefining H2-Alibaba) rather than
"4.3," since it does not depend on or supersede a recovery-data milestone.
Final numbering is a documentation choice to make when the corresponding
plan document is written — not decided further here.

## 19. Prerequisites, risks, acceptance criteria (for Option D, sketch only)

**Prerequisites**: (1) an explicit, frozen scenario-family taxonomy; (2)
an explicit, frozen recovery-action vocabulary; (3) an explicit, frozen
validation-criteria protocol per scenario family — all decided *before*
any episode is generated, mirroring Phase 4.0's own discipline.

**Risks**: controlled/synthetic recovery data could be mistaken for real
evidence if not rigorously labeled at every reporting layer (mitigated by
§15's disclosure requirement); scenario design could inadvertently bake
in the answer (mitigated by designing scenarios before any policy
mechanism is chosen, and by an adversarial/leakage-audit pass analogous
to every prior phase's).

**Acceptance criteria (sketch, to be formalized in the milestone's own
protocol, not here)**: PASS requires a valid, pre-registered comparison
against a fixed-policy baseline at a pre-registered minimum sample size,
regardless of which way the result leans (same discipline as every prior
phase in this project).

## 20. Final recommendation

**READY FOR NEXT MILESTONE PLANNING** — specifically, for a dedicated
planning pass (following this project's established plan → freeze →
implement → evaluate discipline) that formalizes Option D (recovery-
learning/evaluation foundation) into its own approved plan document,
analogous to how `docs/PHASE4_2_ACTIVE_PLAN.md`'s content was produced
before Active Phase 4.2 began. Option A (richer Alibaba context) is
**also** ready for planning in parallel, as a lower-priority, lower-cost
track. No further implementation, data changes, or experiments are
authorized by this document itself.

---

# Additive amendment — Active Phase 4.3 implemented (post-dates the reassessment above)

**Status: COMPLETE.** This reassessment's Option D was subsequently
implemented as **one complete Active Phase 4.3 milestone** (not split into
"4.3a/4.3b" as §18 above speculated) per the milestone's own governing
instructions. Full protocol, taxonomy, action vocabulary, environment,
baselines, proposed mechanism, tests, leakage audit, experiments,
ablations, and final verdict are documented in
[`docs/PHASE4_3_RECOVERY_LEARNING.md`](PHASE4_3_RECOVERY_LEARNING.md).

**Correction (2026-08-17):** the Phase 4.3 numbers originally quoted here
were invalidated by a non-determinism bug in `src/recovery/environment.py`
(`transition()` seeded its RNG from the builtin `hash()` of a string,
which is randomized per-process by `PYTHONHASHSEED` unless disabled —
three fresh runs produced three different success rates). Fixed by seeding
`random.Random()` with the string itself instead of `hash()` of it; the
dataset was regenerated and every number below is the corrected,
verified-deterministic (5-run-identical) result. Full account:
`docs/PHASE4_3_RECOVERY_LEARNING.md` §35.

**Final verdict: PASS — HYPOTHESIS NOT SUPPORTED.** On a controlled,
frozen, 2,320-episode synthetic dataset (`src/recovery/`,
`data/controlled_recovery/`), the proposed context-aware
`EmpiricalRecoveryPolicy` beat a random-action baseline decisively (55.1%
vs 22.5% validated success, p≈1.3×10⁻⁴⁸) but was statistically
indistinguishable from a fixed rule-based priority baseline (55.1% vs
54.0%, effect 0.0111 versus a pre-registered minimum of 0.15, p=0.451, not
significant — and stable across 5 independent dataset draws using the
same full statistical pipeline as the primary evaluation, effect range
[−0.003, +0.028]). Mean recovery utility was effectively tied with the
fixed-priority baseline (H3-UTILITY not supported under the frozen `>=`
rule). It never selected the frozen vocabulary's one unsafe action
(0/720), and a dedicated ablation confirmed the safety mask is load-bearing
(removing it raised the unsafe rate to 8.9%). Leakage audit 9/9. Full
repository test suite: **408/408 data-independent tests pass on any clean
checkout; 425/425 including the 17 real-data-dependent tests requires
local data setup** (raw AgentRx/AIOps/Alibaba datasets are gitignored, not
committed — see [`docs/DATA_SETUP.md`](docs/DATA_SETUP.md) and
[`scripts/fetch_or_document_real_data.md`](scripts/fetch_or_document_real_data.md)
for exact sources and the reproduction pipeline; without that setup, those
17 tests skip cleanly with a pointer to this doc rather than erroring).
Sample size 4.16× the pre-registered floor.
This document (the reassessment above) and every prior frozen artifact
(old/Active Phase 4.1, old/Active Phase 4.2 — including Active Phase 4.2's
`INCONCLUSIVE` verdict — the revised real-data Phase 3 track) are
**unmodified** by Phase 4.3; nothing above this amendment was edited to
produce it.
