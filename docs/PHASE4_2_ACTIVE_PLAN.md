# ACTIVE PHASE 4.2 — Failure Pattern Learning: Reassessment & Implementation Plan

**Status: PLANNING ONLY. No Phase 4.2 code, experiments, or models exist
yet.** This document is the complete research plan required before any
active Phase 4.2 implementation begins, per the same discipline
`docs/PHASE4_PLAN.md` and `docs/PHASE4_1_FAILURE_MEMORY.md`'s protocol
freezing already established for this project. Nothing under
`src/patterns/`, `docs/PHASE4_2_FAILURE_PATTERNS.md`,
`experiments/results/phase4_2/`, `src/failure_experience/`, any
`docs/PHASE3_*.md`, or any dataset file was modified while producing this
plan — every finding below came from read-only inspection (documented
inline with the exact command/file used, so it is checkable).

---

## 1. Historical context

```
OLD Phase 4.0 (synthetic episodic data)
  └─▶ OLD Phase 4.1 (src/experience/) → H1 PARTIALLY SUPPORTED (frozen)
       └─▶ OLD Phase 4.2 (src/patterns/) → H2 INCONCLUSIVE (frozen)
              │
              ▼ [project pauses old Phase 4 sequence]
REAL DATA EXPANSION (AgentRx, AIOps 2020, Alibaba GPU 2020)
  └─▶ REVISED real-data Phase 3 (docs/PHASE3_REAL_DATA_3_6_DECISION.md)
       └─▶ [deliberate pause + reassessment]
              └─▶ ACTIVE Phase 4.1 (src/failure_experience/) → PASS
                     └─▶ THIS DOCUMENT: ACTIVE Phase 4.2 reassessment & plan
```

The old Phase 4.2's `INCONCLUSIVE` verdict is **not touched** by anything in
this document (Task 13). Nothing here implies the old result was wrong,
right, or resolved — it is a separate, earlier experiment on separate,
frozen data.

## 2. Old Phase 4.2 audit (Task 1)

Read in full: `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/{schema,
discovery,metrics}.py`, `configs/phase4_2_pattern_protocol.json` (referenced
throughout the doc), `experiments/results/phase4_2/*.json`. Not modified.

| Question | Finding |
|---|---|
| 1. What it attempted to prove | Whether recurring `(workload_id, diagnosed_cause)` relationships in the synthetic episode stream are detectable above chance, with four-tier confidence separating observed/inferred/confirmed/uncertain evidence. |
| 2. Hypothesis | H2 (frozen, `configs/phase4_2_pattern_protocol.json`) — see quote in the brief §"Old Phase 4.2". |
| 3. Data used | `experiments/results/phase4_0/episodes.json` (the same frozen synthetic file the active Phase 4.1 also reuses read-only), restricted to `is_failure=True AND diagnosed_cause is not None` — CRITICAL-tier rows only (diagnosis is only computed for CRITICAL tier under the frozen Phase 3.6 policy). |
| 4. What "pattern" meant | A candidate keyed by `(workload_id, diagnosed_cause)`; the claim is a **symptom→cause** relationship — does this diagnosed cause, for this workload, reliably map to one true `condition_id`. |
| 5. Ground truth | `condition_id`, Phase 4.0's generator-assigned ground truth — evaluation/discovery-only, never exposed to `PatternQuery`. |
| 6. Metrics | Precision/recall of "flagged" candidates against test-split row coverage; tier calibration (true-structure rate per tier) — the latter could not actually be checked (§10 below). |
| 7. Baselines | A (no pattern learning), B (naive frequency, `n_train≥3`), C1 (proposed tiered), C2 (ablation: purity threshold only, no tiering). |
| 8. Why INCONCLUSIVE | Pre-registered `minimum_evaluable_n = 10` covered test rows; actual = 7. The rule (not the point estimates) determined the verdict — this was mandated regardless of which way the numbers leaned. For the record, point estimates were directionally unfavorable to the tiered method (B's precision 0.333 beat C1's 0.286 at equal recall). |
| 9. Reusable methodology | The **four-tier evidence concept** (recurrence fact vs. inferred relationship vs. validated relationship vs. insufficient evidence) is dataset-agnostic reasoning, not synthetic-specific. The **decision-time/evaluation-only structural type split** (`PatternQuery` excludes ground truth by construction) is a reusable design pattern. The **leakage-audit methodology** (contaminate train with test, verify candidates change) is directly reusable. |
| 10. Assumptions no longer valid | (a) That `diagnosed_cause` exists as a per-record field — it does not exist for ANY real dataset (Phase 3's real-data pipeline produces only an aggregate detection score, not a per-record diagnosis; see §4 below). (b) That a single `condition_id`-style ground truth exists to define "true structure" — no real dataset has this. (c) That workload identity recurs at a fine grain — false for Alibaba job-level (§4.4). (d) That temporal spacing is a generator artifact worth measuring on synthetic data — real datasets have genuine, non-deterministic temporal structure the synthetic generator's constant-gap round-robin schedule cannot represent (old Phase 4.2 §13 found **zero** temporal clustering, by construction, in the synthetic stream). |
| 11. Reusable read-only | `src/patterns/schema.py`'s tier-concept and `PatternQuery`-style structural leakage prevention (as a **design template**, not imported code — same relationship the old Phase 4.2 itself had to Phase 4.1's `DecisionTimeQuery`). The leakage-audit pattern (`benchmarks/phase4_2_leakage_audit.py`'s 5-check structure) as a template. |
| 12. NOT to be reused | The `(workload_id, diagnosed_cause)` candidate key itself (no real dataset has `diagnosed_cause`); the purity-against-`condition_id` metric (no real dataset has an analogous single ground-truth label); the exact tier thresholds (`TAU_INFERRED=0.6` etc. — tuned/chosen for a 28-row synthetic population, not re-derivable as appropriate for real data without a fresh, pre-registered choice). |
| 13. Compatibility with `FailureExperience` | **Not directly compatible.** Old `PatternCandidate`/`PatternQuery` are built on the old `Experience`/`EpisodeProvenance` types (`src/experience/schema.py`), which the active Phase 4.1 does not use. A new pattern representation must be built against `FailureExperience` (`src/failure_experience/schema.py`) fields (`failure.failure_signature`, `workload_context`, `diagnosis`, `outcome.final_status`, `eligibility.role`) — see §11. |

## 3. Active Phase 4.1 audit — what Phase 4.2 can actually consume (Task 2)

Re-read `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` and
`src/failure_experience/{schema,ingest,storage,retrieval,reconstruction,
sources/*}.py` in full for this plan. Below is the field-population audit
by dataset, derived from the source adapters themselves (not assumed):

| Information | Synthetic (phase4_0) | AgentRx | Alibaba | AIOps |
|---|---|---|---|---|
| Observed telemetry (`Observations.telemetry`) | Yes — 5 synthetic features per record | **No** — 0 fields (agent-trajectory data has no infra telemetry) | Yes — via `resource_metrics` (plan_cpu/mem/gpu), not `telemetry` | Partial — `resource_metrics.window_duration_minutes` only; no per-minute KPI join (documented shallow-join limitation) |
| Failure labels (`FailureInfo`) | `failure_type="synthetic_injected_condition"` (constant), `condition_id` is the real label but lives only in `ValidationInfo.validated_cause`, post-hoc | `failure_categories` list (multi-label), `failure_type`=first category | `failure_type="task_terminated_failed"` (constant — status-code derived, no finer typing) | `failure_type=fault_desrcibtion` (5 distinct values: network delay/CPU fault/network loss/db connection limit/db close) |
| Failure signature (`FailureInfo.failure_signature`) | hash(type, workload_id, workload_type) — low cardinality (1 workload_type) | hash(category, domain, "llm_agent_trajectory") | hash("task_terminated_failed", task_name, "alibaba_gpu_cluster_job") | hash(fault_desrcibtion, entity, workload_type) |
| Diagnosis (`Diagnosis`) | Present for 46/307 failures (reused frozen Phase 3.6 rule, CRITICAL-tier only) | Human-curated `root_cause_reason` text, `source=HUMAN_DATASET_ANNOTATION` | **`source=NOT_ATTEMPTED`** — no diagnosis field exists in this dataset at all | Fault description/entity as `HUMAN_DATASET_ANNOTATION` (injected-fault ground truth, not a live diagnosis) |
| Diagnosis confidence | **None** (deterministic rule has no confidence) | **None** (categorical annotation) | **None** (no diagnosis) | **None** (categorical annotation) |
| Temporal information | Synthetic `step` integer, deterministic round-robin (old Phase 4.2 §13: zero clustering, by construction) | Synthetic timestamp anchor (`sources/_util.py`, no real wall-clock exists) — **not usable for real temporal-clustering analysis** | Real trace-relative seconds (`start_time`/`end_time`), genuine ordering | **Real wall-clock** (`onset`, window bounds) — the only source with genuine, non-synthetic temporal structure |
| Workload identity | `workload_id` (4 distinct, each recurs many times by generator design) | `domain` (2 distinct: `tau_bench_retail`, `magentic_one_web_file_agent`) | `job_name` (unique per failed row in the sampled table — see §4.4, **does not recur**) / `task_name` (7 distinct, recurs heavily) | `entity` (16 distinct among faulted entities, recurs up to 10×) |
| Recurrence identity (usable key) | `(workload_id, diagnosed_cause)` — old Phase 4.2's key, still computable on this source only | `(domain, failure_category)` | `(task_name, gpu_type)` — NOT `(job_name, ...)` | `(entity, fault_desrcibtion)` |
| Recovery information | Present for 46/307 (retry/reconfigure/rollback + outcome) | **`NOT_OBSERVED`** (dataset literally encodes `"MISSING"`) | **`NOT_OBSERVED`** (no field in dataset) | **`NOT_OBSERVED`** (no field in dataset) |
| Validation information | Present for 4/307 (`recovery_correct` non-null) | **`NOT_PERFORMED`** | **`NOT_PERFORMED`** | **`NOT_PERFORMED`** |
| Outcome (`OutcomeInfo.final_status`) | `{abstained, failure, unknown, success}` all observed | `failure` only | `failure` only | `failure` only |
| Provenance | Full (10 fields) | Full, `dataset_content_hash` present | Full, incl. reused Phase 3 split label | Full |
| Train/val/test status | `environment` = split (from generator) | **No frozen split** (`environment` unset) | **Frozen split reused** (`environment` = train/val/test via `data/audit/alibaba_gpu2020/splits_random_stratified.json`) | **No frozen split** (`environment="unsplit"`, confirmed in Phase 3 real-data comparison doc) |

**This table is the single most important input to Task 3–6 below.** It
shows, concretely, that no uniform pattern-learning task is possible across
all four sources — they differ in workload-identity granularity, diagnosis
availability, temporal genuineness, and split availability along
independent axes.

## 4. Dataset-specific scientific validity (Task 4)

Additional read-only statistics computed for this plan (all reproducible;
exact code shown so the numbers are checkable, not asserted):

### 4.1 AgentRx

```python
# 87 total AgentRx records (tau_retail_joined.jsonl + magentic_joined.jsonl), 73 have has_failure_annotation=True
# domains: magentic_one_web_file_agent=44, tau_bench_retail=29
# 24 distinct individual failure_categories values across the 73 failures;
#   top individual categories: "Instruction/Plan Adherence Failure" (25),
#   "Misinterpretation of Tool Output" (24), "Guardrails Triggered" (23)
# 29 distinct (sorted) failure_category COMBINATIONS across 73 failures --
#   most common combo recurs 9 times (single-category "Intent Plan Misalignment")
```

- **Episode** = one agent trajectory (`trajectory_id`), already a complete
  unit (not decomposable into sub-events with the current joined data).
- **Failure** = `has_failure_annotation=True`; can co-occur with multiple
  `failure_categories` (multi-label, not single-label).
- **Pattern** = recurrence of a `(domain, failure_category)` or
  `(domain, category_combo)` pairing — this is a **behavioral/cognitive
  failure-mode recurrence pattern**, not an infrastructure failure pattern.
  AgentRx has zero CPU/memory/latency telemetry; forcing an
  infrastructure-failure framing onto it (as the original H2's "condition
  recurrence, symptom→cause" language implicitly assumes) would misrepresent
  the data. The valid framing is: *does this agent domain reliably exhibit
  the same class of reasoning/tool-use failure?*
- **Temporal recurrence**: **NOT CURRENTLY EVALUABLE** — no real timestamp
  exists in the joined data (`"timestamp": "MISSING"` in the raw file,
  confirmed directly), so occurrence ordering cannot be measured on
  wall-clock or trace-relative time at all, only on file-row order (which
  is not meaningful).
- **Repeated workload identity**: only at the `domain` granularity (2
  values) — individual `trajectory_id`s do not recur (each trajectory is a
  one-off episode). This is coarse but genuine.
- **Split status**: no frozen split. Only 73 usable failure rows total, 2
  domains — splitting further would leave very small per-domain cells.

**Verdict**: AgentRx supports a **descriptive, exploratory** domain×category
recurrence analysis; it does **not** currently support a temporally-ordered
or train/test-evaluated pattern-learning claim (no timestamp, no split, and
n=73 is small once split two ways).

### 4.2 AIOps 2020

```python
# 81 positive fault windows, 16 distinct entities (max 10 occurrences: docker_001)
# objects: docker=49, os=20, db=12; fault types: network delay=31, CPU fault=19,
#   network loss=19, db connection limit=7, db close=5
# Negative (non-fault) population EXISTS and was already frozen by real-data Phase 3 prep:
#   data/audit/aiops_kpi/negative_window_natural_population.json -- 45,911 candidate
#   normal windows across 43 entities / 15 days ("FULL eligible population, not the
#   extracted/sampled pool" per that file's own `note` field)
#   data/audit/aiops_kpi/negative_windows_sampled.json -- the actual sampled/frozen
#   negative set used by Phase 3's real-data evaluation (reusable read-only)
```

- **Episode** = one injected-fault window (`fault_index`).
- **Failure** = the fault itself; **fault type + entity are both directly
  observable ground-truth-quality labels** (injected by the 2020 challenge
  organizers, not inferred) — stronger label quality than AgentRx's
  human-annotated categories or Alibaba's status-code-only labeling.
- **Temporal recurrence**: **genuinely evaluable** — real `onset`
  timestamps exist across 11 distinct days; this is the *only* source with
  authentic (non-generator-determined) temporal structure, making it the
  right place to test whether faults cluster in time (the exact question
  old Phase 4.2 §13 found trivially null on synthetic data by construction).
- **Recurrence definition**: `(entity, fault_desrcibtion)` — e.g. does
  `docker_001` reliably fault with a specific fault type. With only 81
  positive windows over up to 16×5=80 possible combos, most cells will have
  n=1-2 — a real, load-bearing small-sample constraint, flagged honestly
  rather than hidden.
- **Shallow telemetry integration**: sufficient for entity/fault-type
  recurrence and temporal-clustering analysis (neither requires the
  per-minute KPI join). **Not** sufficient for a telemetry-signature-based
  pattern claim ("do these three metrics jointly predict this fault type")
  — that would require the deeper join flagged as a Phase 4.1 limitation.
  This plan does **not** require the deeper join for its smallest-valid
  version (§14); it is listed as an optional strengthening prerequisite
  (§12/Task 12).
- **No frozen split**: confirmed (`docs/PHASE3_REAL_DATA_COMPARISON.md`'s
  own H3 finding, carried into active Phase 4.1 §11 verbatim). Using AIOps
  for a train-fit-then-test-evaluate claim without first building a split
  would be exactly the "silently assume unsplit data is safe for learning"
  error Task 8 warns against.

**Verdict**: AIOps supports (a) a **descriptive** entity×fault-type
recurrence analysis, (b) a **genuinely novel, evaluable temporal-clustering
question** (do faults burst vs. arrive uniformly — using real timestamps,
unlike synthetic's null-by-construction case), using the already-frozen
negative-window population for a proper base-rate comparison if desired.
It does **not** currently support a scored train/test pattern-precision
claim (no split) — flagged as a prerequisite-gated capability, not silently
assumed away.

### 4.3 Alibaba GPU 2020

```python
# task_table.main_sample.csv (the frozen Phase 3 real-data cleaned sample): 11,750 rows, 2,594 Failed
# job_name recurrence among FAILED rows: 2,594 distinct job_names for 2,594 failed rows -- ZERO jobs
#   have more than one failed task row in this sample.
# Checked against the FULL cleaned population (task_table.clean.csv, 1,261,050 rows, 256,762 Failed):
#   256,755 distinct job_names among 256,762 failed rows -- only 7 jobs (out of 256,755) have >1
#   failed task. This is NOT a sampling artifact -- it is a genuine property of the underlying data
#   (per data/audit/alibaba_gpu2020/sampling_report.json, sampling was stratified by
#   status|gpu_type|quarter at the JOB level, one row per job -- but even the full unsampled
#   population shows job-level failure recurrence is a ~0.003% edge case).
# task_name recurrence among failed rows: 7 distinct values, "tensorflow"=2004/2594 (77.3%)
# gpu_type recurrence among failed rows: "MISC"=2057/2594 (79.3%)
# Rate comparison (failed vs. terminated), same sample:
#   gpu_type="MISC": 79.3% of failures vs. 52.2% of terminations (elevated)
#   task_name="tensorflow": 77.3% of failures vs. 46.7% of terminations (elevated)
```

- **Workload identity**: `job_name` does **not** recur (confirmed above,
  on both the sample and the full population) — a genuinely important,
  non-obvious finding that rules out a `job_name`-keyed pattern task
  entirely, for a real structural reason, not a code limitation.
  `task_name` (task *type*, e.g. "tensorflow", "worker") is the identity
  that actually recurs, and should be used instead.
- **Failure recurrence** = elevated failure *rate* for a
  `(task_name, gpu_type)` combination relative to the population base rate
  — a **different pattern shape** than old Phase 4.2's symptom→cause purity
  question (Alibaba has no diagnosis layer to be the "symptom" side; it
  does have a full success/failure population to compute rates from, which
  synthetic's CRITICAL-tier-only population did not).
- **Telemetry dimensions available**: `plan_cpu`, `plan_mem`, `plan_gpu`,
  `gpu_type`, `inst_num` — enough to define a small number of coarse
  resource-profile buckets if a richer-than-`(task_name, gpu_type)` pattern
  key is later wanted (not proposed as the primary key here, to keep the
  smallest-valid version simple — see §14).
- **Frozen split**: **yes**, reused directly from
  `data/audit/alibaba_gpu2020/splits_random_stratified.json` (already wired
  into `workload_context.environment` by the active Phase 4.1's adapter).
  A temporal split (`splits_temporal.json`) also exists and was already
  used by Phase 3's real-data H3 experiment — available if a
  temporally-honest (rather than random-stratified) split is preferred for
  Phase 4.2 (recommended — see §8).
- **Sample size**: 11,750 rows in the frozen cleaned sample (2,594 failed),
  vastly larger than old Phase 4.2's 28/4/14 train/val/test rows — the
  single-biggest scientific advantage of the real-data foundation for this
  question.

**Verdict**: Alibaba is the **strongest** candidate for a rigorously
train/val/test-evaluated pattern-learning hypothesis — real, adequate
sample size, a frozen (in fact, two frozen) split(s), and a genuine,
measurable, non-trivial recurrence signal (§4.3's rate comparison above).
It requires reformulating the pattern claim from "symptom→cause purity"
to "context→failure-rate elevation," a scope change this plan makes
explicitly (see §6).

### 4.4 Synthetic episodic data — role in active Phase 4.2

Per the brief's explicit instruction not to automatically discard or
equate it with real data:

- **Not used as a source of new real-world evidence** for the active
  Phase 4.2 hypotheses (§6) — its `condition_id`/`diagnosed_cause`
  structure exists nowhere in real data, so any result on it cannot
  generalize to a real-data claim.
- **Retained as a methodological validation / regression testbed**: the
  active Phase 4.2's new pattern-detection code (a *new* implementation, in
  a *new* namespace, never importing `src/patterns/`) can be run against
  this same frozen synthetic file to sanity-check that the new mechanism's
  behavior is reasonable on a dataset whose ground truth is fully known —
  analogous to a unit-test-with-real-shaped-data, not a Phase 4.2 result.
  Its role is explicitly **methodological validation and ablation
  support**, stated here rather than left ambiguous.
- **Not used for temporal-clustering analysis** — old Phase 4.2 §13 already
  established (and this document does not re-litigate) that the generator's
  round-robin schedule produces zero clustering by construction; re-running
  that exact check on the same frozen data would add no new information.

## 5. Operational definition(s) of "pattern" (Task 5)

The brief's four-tier vocabulary (`OBSERVED` / `INFERRED` / `CONFIRMED` /
`UNCERTAIN`) is **retained as a concept**, because it separates "this
recurs" from "this recurs *and* looks directionally real" from "this is
independently replicated" from "not enough evidence yet" — a distinction
that is dataset-agnostic and does not depend on synthetic-specific
mechanics. It is **not** retained as a fixed set of numeric thresholds (old
`TAU_INFERRED=0.6` etc. were chosen for a 28-row synthetic population and
have no claim to be appropriate elsewhere) — new, pre-registered thresholds
must be chosen per dataset before evaluation, exactly as the old protocol
did, not silently inherited.

**Two formally distinct pattern types** are defined (both measurable with
current data, on different datasets — see §10 for why they are not pooled):

### Pattern Type 1 — Context-conditioned failure-rate elevation (Alibaba primary; Alibaba is the only dataset with the population structure to support this rigorously)

| Property | Definition |
|---|---|
| Input representation | `(task_name, gpu_type)` pair, computed over ALL rows (Failed + Terminated + Running), not only failures |
| Unit of analysis | One candidate context key |
| Context | Alibaba GPU cluster job/task submissions |
| Minimum evidence | `n_train >= N_MIN` total (not-just-failed) occurrences of the key (threshold pre-registered before evaluation, not chosen post hoc — see §8) |
| Recurrence definition | The key itself recurring (`n_train >= N_MIN`) is the OBSERVED-tier bar; INFERRED requires the train-split failure rate for the key to exceed the train-split overall base rate by a pre-registered margin; CONFIRMED requires the SAME elevation to replicate on the validation split |
| Temporal constraints | None required for this pattern type (rate-based, not sequence-based) — Alibaba's split is available in both random-stratified and temporal form; the temporal split is preferred (§8) to avoid any risk of near-duplicate jobs leaking rate information across the random split |
| Ground truth | None needed beyond the observed Failed/Terminated/Running label itself — this is a directly observable outcome, not an inferred proxy |
| Observed vs. inferred | The *rate elevation* is inferred from observed labels; the underlying resource/task combination is directly observed |
| Confidence/evidence representation | Tier + `(n_train, train_rate, baseline_rate, n_validation, validation_rate)` |
| Evaluation target | Does a train-discovered elevated-rate context replicate its elevation on held-out (validation/test) data, at a rate better than a naive frequency-only baseline? |

### Pattern Type 2 — Recurring failure-mode / fault-entity association (AIOps + AgentRx, descriptive-only given no frozen split — see §8)

| Property | Definition |
|---|---|
| Input representation | AIOps: `(entity, fault_desrcibtion)`. AgentRx: `(domain, failure_category)` |
| Unit of analysis | One candidate association key |
| Context | AIOps: injected-fault windows. AgentRx: agent trajectories |
| Minimum evidence | `n >= 2` (matches old Phase 4.2's candidacy floor — still a defensible generic minimum for "this is not a singleton") |
| Recurrence definition | The exact key recurring at least twice in the available (unsplit) data |
| Temporal constraints | AIOps only: onset timestamps enable a genuine burstiness/temporal-clustering sub-analysis (gap variance vs. a uniform-arrival null), independent of the entity×fault-type association itself. AgentRx: **NOT CURRENTLY EVALUABLE** (no real timestamp exists) |
| Ground truth | AIOps: the injected fault label IS the ground truth (organizer-assigned) — recurrence of the label itself is the finding, there is no separate "true cause" to validate the label against. AgentRx: the human-annotated category IS the closest available ground truth, same structure |
| Observed vs. inferred | Purely OBSERVED-tier by construction for this pattern type on these two sources — see next point |
| Confidence/evidence representation | Because there is no frozen validation split for either source, **no candidate can ever reach the CONFIRMED tier** for Pattern Type 2 as currently scoped (CONFIRMED structurally requires independent validation-split replication) — this is stated as a structural ceiling, not an oversight. Candidates land in OBSERVED (n≥2, no purity claim needed since there's no wrong/right cause to be pure about) or are excluded (n<2) |
| Evaluation target | Descriptive report of recurring associations and (AIOps only) temporal clustering — **not** a scored precision/recall claim (no held-out set exists to score against) |

Any other pattern category from the brief's list (workload-specific
patterns beyond what's covered above, failure sequence patterns,
cross-episode chains, repeated anomaly trajectories, structurally-similar
failure-experience clustering) is marked:

**NOT CURRENTLY EVALUABLE** — reasons:
- *Failure sequence / progression patterns*: would require multiple
  ordered observations *within* one episode (a trajectory of states leading
  to failure), which none of the four sources currently expose at
  sub-episode granularity in the ingested `FailureExperience` records
  (AgentRx's `num_steps` is a count, not a per-step trace; Alibaba/AIOps
  are single-point-in-time task/fault records).
- *Cross-episode / cross-dataset structural-similarity clustering* (e.g.
  KMeans over `FailureExperience` embeddings): technically buildable (see
  §11's discussion of `src.failure_memory.embedding.FailureEmbedder`), but
  would conflate four incompatible modalities (§10) into one embedding
  space without a defensible shared feature set — not attempted as a
  primary mechanism; a candidate *ablation only within Alibaba* (§15), not
  a cross-dataset pattern claim.
- *Diagnosis→outcome / cause→outcome chains*: only synthetic has both a
  diagnosis and a validated outcome on the same records (46 recovery
  attempts, 4 validated) — reused as a **secondary, descriptive-only**
  analysis exactly as old Phase 4.2 §13 did (methodological validation
  role, §4.4), not a primary active-Phase-4.2 claim.

## 6. Reassessing H2 (Task 6)

**Decision: E — split into multiple independently-testable, dataset-scoped
hypotheses.** Justification: §3's field-population table and §4's
per-dataset audit show the four sources differ on every axis H2 implicitly
assumed uniform (workload-identity grain, presence of a diagnosis layer,
genuineness of temporal structure, split availability). Task 10 explicitly
forbids merging heterogeneous datasets merely for sample size; pooling them
under one H2 would either silently privilege whichever source has the most
rows (Alibaba, by two orders of magnitude) or require an artificial common
representation this audit found no defensible basis for (§5, "NOT
CURRENTLY EVALUABLE" list).

This is **new research**, not a "correction" of the old H2 — the old H2
remains exactly as frozen, evaluated on synthetic data, INCONCLUSIVE.

- **H2-Alibaba** (primary, rigorously evaluable): Certain
  `(task_name, gpu_type)` context combinations exhibit a failure-rate
  elevation, discoverable on train data, that replicates on held-out
  validation/test data at a rate better than a naive frequency-count
  baseline.
- **H2-AIOps** (exploratory/descriptive, not formally hypothesis-tested
  until a split exists — §8/§12): Fault entities exhibit recurring
  associations with specific fault types, and fault onsets are temporally
  clustered rather than uniformly distributed.
- **H2-AgentRx** (exploratory/descriptive, same constraint): Agent domains
  exhibit recurring associations with specific failure-mode categories.
- **Synthetic**: not a hypothesis-bearing source for active Phase 4.2 (§4.4)
  — used only for methodological validation of the new pattern-detection
  mechanism's implementation correctness.

## 7. Baselines (Task 7)

| Baseline | Applies to | Justification |
|---|---|---|
| A — no pattern learning (independent-incident treatment) | All | Same role as old Phase 4.2's baseline A: the floor every proposed mechanism must clear to justify existing at all. |
| B — naive frequency-count flagging (flag any key with `n_train >= N_MIN`, no rate/purity check) | H2-Alibaba | Directly comparable to old Phase 4.2's baseline B; still scientifically appropriate — it isolates whether *any* rate-awareness beyond raw recurrence count adds value. |
| C — proposed: tiered rate-elevation detection (Pattern Type 1, §5) | H2-Alibaba | The method under test. |
| D — existing frozen clustering (`src.failure_memory.embedding.FailureEmbedder`), as a candidate alternative context-bucketing mechanism instead of raw `(task_name, gpu_type)` keys | Optional ablation only (§15), not a primary baseline | Per §11's reuse audit: worth checking whether an embedding-based grouping outperforms the hand-chosen categorical key, but not assumed superior — same "reuse is not automatically adequate" posture old Phase 4.2 took toward this exact component. |

No baseline is proposed for H2-AIOps/H2-AgentRx beyond descriptive
frequency counts (Pattern Type 2, §5) — a precision/recall-style baseline
comparison requires a held-out set that does not exist for these two
sources (§8).

## 8. Evaluation protocol / leakage prevention (Task 8)

**Alibaba (H2-Alibaba)**:
- Reuse the frozen **temporal** split
  (`data/audit/alibaba_gpu2020/splits_temporal.json`) as primary, not the
  random-stratified split — a rate-elevation claim is more exposed to
  leakage under random splitting (near-duplicate jobs from the same
  submission burst could land in both train and test) than a
  strictly-temporal split guards against. The random-stratified split is
  reused as a secondary/sensitivity check, not the primary evaluation
  (mirrors Phase 3's real-data H3 experiment design, which used exactly
  this same distinction).
- **Discovery** (train only): compute `(task_name, gpu_type)` failure rates
  from train-split rows only.
- **Threshold/tier calibration** (validation only): CONFIRMED-tier
  replication check performed against validation-split rows only, same
  role as old Phase 4.2's validation use — never touches test.
- **Frozen test** (touched exactly once, at the end): final precision/
  recall of train-discovered, validation-confirmed candidates against
  test-split rate elevation.
- Information available at decision time vs. only after: a candidate's
  identity `(task_name, gpu_type)` is available at submission time (before
  the job's outcome is known); its *rate* is discovery/evaluation-only
  information, exactly parallel to `diagnosed_cause`/`condition_id`'s
  decision-time/evaluation-only split in old Phase 4.1/4.2 and active Phase
  4.1's `DecisionTimeQuery`/`PatternQuery`-style structural types. A new
  `PatternQuery`-equivalent type will be built (§11) that can carry
  `(task_name, gpu_type)` but structurally cannot carry a rate/label.
- Repeated incidents: since `job_name` does not recur (§4.3), there is no
  "same job appears in both train and test" leakage risk at the job level;
  the leakage risk is instead about `(task_name, gpu_type)` *tuples*
  recurring across the split boundary, which is expected and is precisely
  what discovery→replication is meant to measure (not a leak).

**AIOps and AgentRx**: **no frozen split currently exists for either.**
Per Task 8's explicit instruction not to silently assume unsplit data is
safe for learning, both are treated as **evaluation-only / descriptive**
for active Phase 4.2 — patterns are reported (recurrence counts, and for
AIOps, temporal clustering statistics) but **no train-fit-then-test-score
claim is made**. Building a frozen split for either is listed as optional
prerequisite work (§12), not silently worked around.

**Synthetic**: used only for methodological validation (§4.4); if that
validation run needs a split, it reuses the same frozen `split` field
Phase 4.0 already assigned (never re-derived).

## 9. Metrics (Task 9)

| Metric | Applies to | Definition | Data source | Notes |
|---|---|---|---|---|
| Rate-elevation precision | H2-Alibaba | Of candidates flagged (train-discovered, validation-confirmed) as elevated-risk, fraction whose test-split failure rate is *also* elevated over the test-split baseline by the same pre-registered margin | Alibaba test split | Directly analogous to old Phase 4.2's precision, but against a *rate* criterion instead of a single-label purity criterion |
| Rate-elevation recall | H2-Alibaba | Of all test-split `(task_name, gpu_type)` combinations whose test-split rate is actually elevated, fraction that were flagged by train discovery | Alibaba test split | |
| False pattern rate | H2-Alibaba | Of flagged candidates, fraction whose test-split rate is NOT elevated (= 1 − precision, reported separately per Task 9's explicit list) | Alibaba test split | |
| Tier calibration | H2-Alibaba | Does test-split precision actually increase CONFIRMED > INFERRED > OBSERVED, measured, not asserted | Alibaba test split, stratified by discovered tier | Mirrors old Phase 4.2's (unresolvable, due to n=7) tier-calibration goal — Alibaba's much larger n makes this plausibly checkable this time, not guaranteed |
| Recurrence detection rate | AIOps, AgentRx | Fraction of entities/domains with `n>=2` fault/failure occurrences whose top recurring key accounts for `>= X%` of their occurrences | Full (unsplit) AIOps/AgentRx data | Descriptive only, no precision/recall (no held-out set) |
| Temporal clustering statistic | AIOps only | Observed inter-fault-onset gap variance per entity vs. a uniform-arrival null (same statistic old Phase 4.2 §13 computed on synthetic, here computed on **real** onsets) | AIOps positive windows, real `onset` timestamps | The one metric where AIOps's genuine (non-generator) temporal structure adds new information the synthetic source structurally cannot |
| Pattern confidence calibration (four-tier) | H2-Alibaba only | See "Tier calibration" above | Alibaba | **NOT EVALUABLE** for AIOps/AgentRx — no CONFIRMED tier is reachable without a validation split (§5) |
| Detection lead time | **NOT EVALUABLE**, any dataset | Would require a live-deployment timeline (pattern discovered at time T, used to anticipate a failure at T+Δ) — no dataset here has that operational framing; all four are retrospective/offline record sets | — | Explicitly marked out of scope rather than silently defined away |
| Pattern stability | Optional secondary, Alibaba only | Do discovered candidates and their tiers stay materially the same if train/validation boundaries are perturbed (e.g. k-fold within train) | Alibaba train split | Proposed as an ablation-adjacent robustness check (§15), not a primary metric |

## 10. Cross-dataset comparability (Task 10)

**Evaluated independently per dataset, not pooled**, per §6/§9's structure.
No common numeric pattern-precision score is reported "across all
datasets" — the pattern types themselves differ (rate-elevation vs.
descriptive recurrence), the ground-truth quality differs (organizer-
injected labels vs. human annotation vs. no diagnosis layer at all), and
sample sizes differ by 2+ orders of magnitude. The final Phase 4.2 report
(when written, after implementation) must present results in per-dataset
sections, exactly as `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` already
does for Phase 4.1's four sources, and must not claim cross-dataset
generalization without a dedicated, separately-designed experiment for it
(Task 13's explicit prohibition).

A **shared abstraction does exist at the representation layer** —
`FailureExperience.failure.failure_signature` and
`FailureExperience.workload_context` are populated by all four sources and
could in principle support a uniform "candidate key = (workload_context
field, some other field)" query mechanism (§11's proposed `PatternQuery`
design reuses this). This is a shared *interface*, not a shared *dataset*
— each dataset still gets its own discovery run, its own thresholds, and
its own reported result.

## 11. Reuse / refactor decisions (Task 11)

| Component | Decision | Where |
|---|---|---|
| `src/failure_experience/*` (active Phase 4.1) | **Reuse directly, read-only**, as the sole data-access layer — pattern discovery queries `FailureExperienceRepository`/`retrieve()`, never re-parses raw source files itself | Active Phase 4.2 code imports `src.failure_experience`, never re-implements ingestion |
| `src/experience/`, `src/patterns/` (old, frozen) | **Do not import, do not edit.** Read for design-template understanding only (already done, §2) | N/A |
| `src/failure_memory/embedding.py` (`FailureEmbedder`) | **Candidate for one ablation only** (§15), not the primary mechanism — same "inspected, not defaulted-to" posture old Phase 4.2 took. Reused read-only if the ablation is run. | New ablation module only |
| `src/evaluation/diagnosis.py` | **Not reused** — real datasets have no field this frozen, synthetic-only rule could populate; already inapplicable outside the synthetic methodological-validation track (§4.4) | N/A |
| `data/audit/alibaba_gpu2020/splits_temporal.json`, `splits_random_stratified.json` | **Reuse directly** (§8) | New Alibaba pattern-discovery module |
| `data/audit/aiops_kpi/negative_windows_sampled.json`, `negative_window_natural_population.json` | **Reuse directly, read-only**, if a rate-based (not purely count-based) AIOps analysis is later added (optional strengthening, §12) — not required for the smallest-valid AIOps version (Pattern Type 2, count/recurrence only) | Optional AIOps rate-analysis module |
| New pattern representation (`PatternCandidate`, `PatternQuery`-equivalent) | **Build new**, in a new namespace, modeled on `src/failure_experience/eligibility.py`'s "explicit fields, explicit reasons" style and the old Phase 4.2's structural leakage-prevention *pattern* (not its code) | `src/failure_patterns/` (proposed new package name — see §14; deliberately distinct from both `src/patterns/` [old, frozen] and `src/failure_experience/` [active 4.1, a dependency not a peer]) |

## 12. Prerequisite data work assessment (Task 12)

| Candidate prerequisite | Required for smallest-valid version (§14)? | Dataset | Belongs in 4.2 itself? | Separate milestone? | Changes the research question? |
|---|---|---|---|---|---|
| Deeper AIOps telemetry join (per-minute KPI series) | **No** — Pattern Type 2 (entity×fault-type recurrence, temporal clustering) needs only window metadata, already present | AIOps | No | Yes, if ever pursued — would enable a *different*, stronger AIOps pattern type (telemetry-signature clustering) not proposed here | Yes — would upgrade AIOps from Pattern Type 2 to a Pattern-Type-1-style rate/signature claim, a scope change requiring its own hypothesis |
| Frozen train/val/test split for AIOps | **No** — §8 scopes AIOps to descriptive-only without one | AIOps | Could be done as a first step of 4.2 OR as a separate prerequisite; recommend separate, since split design (temporal vs. stratified, and by what unit — entity? day?) deserves its own brief protocol note, mirroring how Alibaba's split was built in the real-data Phase 3 track, not Phase 4.2 | Recommended separate, small milestone | No — same H2-AIOps question, just becomes formally testable instead of descriptive |
| Frozen split for AgentRx | **No** — same reasoning, descriptive-only scope | AgentRx | Same as above | Recommended separate, small milestone | No |
| Per-record Phase 3 real-data risk outputs (currently only aggregate AUROC/AUPRC exist) | **No** — H2-Alibaba's Pattern Type 1 uses raw resource-plan fields (`plan_cpu`/`gpu_type`) and the observed Failed/Terminated label directly, not a fitted risk score | Alibaba (and any future use on AIOps) | No | Yes, if ever pursued — would let a future pattern type use calibrated risk as a feature, not required here | No, but would enable an additional pattern type later |
| Workload-identity normalization | **No** — §4's audit already determined the correct identity grain per dataset (`task_name` not `job_name` for Alibaba; `domain` for AgentRx; `entity` for AIOps) | All | N/A | N/A | N/A |
| Recurrence labels | **No** — recurrence is computed directly from existing fields, not a separate label that needs producing | All | N/A | N/A | N/A |
| Additional real data | **No** — current three real datasets are sufficient for the smallest-valid version defined in §14 | — | N/A | N/A | N/A |
| Better provenance mapping | **No** — active Phase 4.1's provenance fields are already sufficient (100% traceability per its Experiment E) | — | N/A | N/A | N/A |

**Conclusion for Task 12**: no prerequisite blocks the smallest-valid
version of active Phase 4.2 (§14). Two genuinely useful prerequisites
(frozen splits for AIOps/AgentRx) are identified and recommended as small,
separate follow-on milestones that would *upgrade* those two sources from
descriptive to formally-tested, but their absence does not block starting
Phase 4.2 on Alibaba (primary) + descriptive AIOps/AgentRx + synthetic
methodological validation.

## 13. Research integrity safeguards (Task 13)

- Old Phase 4.2's `INCONCLUSIVE` verdict, `docs/PHASE4_2_FAILURE_PATTERNS.md`,
  `src/patterns/`, `configs/phase4_2_pattern_protocol.json`,
  `experiments/results/phase4_2/*` are **not modified** by this plan (this
  document only reads them, per the timestamps this task is bound by the
  same verification convention active Phase 4.1 used — file mtimes will be
  checked unchanged after this planning task, exactly as was done at the
  end of active Phase 4.1).
- No pattern type in §5 was chosen after looking at test-split outcomes —
  every dataset-specific statistic quoted in §4 was computed over the
  *full* dataset (train+val+test pooled, since no discovery/threshold
  decision was being made in this planning pass, only descriptive
  characterization) and is disclosed as such; §4's numbers must **not** be
  reused as if they were train-only discovery statistics once
  implementation begins — implementation must recompute train-only figures
  fresh, from the frozen split, not reuse this plan's pooled descriptive
  numbers as a shortcut.
- No recurrence, ground truth, or label was fabricated: AIOps's fault
  type/entity and AgentRx's failure category are dataset-provided
  annotations, used as such (`HUMAN_DATASET_ANNOTATION` /
  organizer-injected), never upgraded to a fabricated calibrated
  confidence.
- Cross-dataset generalization is not claimed anywhere in this plan (§10)
  and must not be claimed in the eventual results without a dedicated
  experiment designed for it.
- When active Phase 4.2 eventually runs, if any of its evidence bears on
  the old Phase 4.2's INCONCLUSIVE question, the final report must state
  the progression explicitly: `Old experiment (synthetic) → INCONCLUSIVE`,
  `New experiment (real data) → <whatever is found>`,
  `Combined interpretation → <stated explicitly>` — never a silent
  replacement, exactly as `docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` §1
  already did for its own relationship to old Phase 4.1.

## 14. Smallest research-valid version (Task 14)

No GNNs, transformers, RL, LLMs, or graph mining — the audit found no
justification for that complexity. The recurrence/rate questions in §5 are
answerable with counting, rate comparison, and a simple pre-registered
tier rule (the same complexity class as old Phase 4.2, which is
appropriate — nothing in this audit found old Phase 4.2's *mechanism*
complexity to be the problem; its problem was evidence volume on a small
synthetic slice, which real data's larger Alibaba population directly
addresses).

**Proposed smallest-valid active Phase 4.2**, in one sentence per part:

1. `src/failure_patterns/schema.py` — new `PatternCandidate`/
   `PatternQuery`/`EvidenceTier` types, built against `FailureExperience`
   fields, structurally excluding rate/outcome from the query type (§8).
2. `src/failure_patterns/discovery_alibaba.py` — Pattern Type 1 discovery
   (`(task_name, gpu_type)` rate elevation) over Alibaba experiences
   retrieved via `src.failure_experience.retrieval`, using the frozen
   temporal split.
3. `src/failure_patterns/discovery_descriptive.py` — Pattern Type 2
   recurrence counting (+ temporal clustering for AIOps) over
   AIOps/AgentRx experiences, explicitly not tier-scored beyond OBSERVED.
4. `benchmarks/phase4_2_active_pattern_evaluate.py` — runs discovery +
   baselines A/B/C for Alibaba, descriptive reports for AIOps/AgentRx,
   methodological-validation run against synthetic.
5. `benchmarks/phase4_2_active_leakage_audit.py` — same 5-check style as
   old Phase 4.2's audit, adapted to the new types and Alibaba's temporal
   split.
6. Tests mirroring active Phase 4.1's structure: schema validation,
   discovery correctness on synthetic fixtures with known answers,
   leakage-contamination-changes-candidates test, integration test against
   real `src.failure_experience` data.
7. `docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` — the eventual results
   document (not written now — this plan only).

## 15. Ablations (Task 15)

| Ablation | Isolates | Dataset |
|---|---|---|
| Tiered (C) vs. flat-threshold-only (C′, no CONFIRMED validation-replication requirement) | Whether the validation-replication step adds value over a train-only purity/rate threshold | Alibaba |
| With vs. without temporal-split enforcement (compare temporal split result to random-stratified split result, §8) | Whether split methodology itself materially changes the finding — a sensitivity check, not a second primary result | Alibaba |
| `(task_name, gpu_type)` key vs. `FailureEmbedder`-clustered key | Whether the hand-chosen categorical key loses information a learned grouping would capture | Alibaba only (§11) |
| Recurrence threshold `N_MIN` sweep (e.g. 2/5/10/20) | Sensitivity of precision/recall to the discovery floor — mirrors Phase 3.6's cost-ratio sensitivity-sweep methodology this project already established | Alibaba |

**Not proposed**: an ablation removing "workload identity" or "temporal
information" wholesale (as the brief's generic list suggests) — for
Alibaba, workload identity (`task_name`) *is* the pattern key itself
(removing it removes the pattern definition, not a component of it); for
AIOps, temporal information is already isolated as its own metric (§9),
not blended into the primary recurrence metric, so there is nothing
additional an ablation would isolate.

## 16. Acceptance criteria (Task 16)

Distinguishing implementation correctness from hypothesis support, exactly
as old Phase 4.2's completion record did (its final status separated a
clean implementation PASS from an INCONCLUSIVE hypothesis result):

**PASS** requires ALL of:
- Implementation: schema, discovery, retrieval-integration, leakage audit
  (all checks passing, contamination test proves non-vacuous), tests all
  passing, full repo suite still green.
- Alibaba's `minimum_evaluable_n` (to be pre-registered before
  implementation, analogous to old Phase 4.2's 10 — likely higher here
  given Alibaba's much larger population, e.g. on the order of 50-100
  covered test rows, chosen from a generic small-sample convention, not
  reverse-engineered from a peek at the test split) is met.
- H2-Alibaba's pre-registered criterion is evaluated (whichever way it
  lands) — a **negative** or **null** finding, honestly reported with a
  valid, high-power experiment behind it, still qualifies as PASS on
  implementation/validity grounds; PASS is not defined as "the method
  wins."

**PASS WITH ISSUES**: implementation and evaluation are valid, but one or
more secondary items (e.g. the tier-calibration check, or the embedding
ablation) could not be meaningfully computed, OR the point estimates are
directionally unfavorable to the proposed method (mirrors old Phase 4.1's
own PASS WITH ISSUES framing) — reported plainly, not hidden.

**INCONCLUSIVE**: Alibaba's `minimum_evaluable_n` is not met despite
Alibaba's much larger population (would itself be a notable finding,
given the explicit expectation in §4.3 that power should not be the
bottleneck this time), OR the pre-registered tier thresholds produce a
degenerate candidate set (e.g. zero candidates reach any tier) making the
comparison uninformative — same posture as old Phase 4.2's honest
INCONCLUSIVE, not avoided by redefining the bar after the fact.

**FAIL**: leakage audit finds a real violation not caught before reporting
results, OR the implementation cannot process real `FailureExperience`
data end-to-end, OR a research-integrity violation (test-set tuning,
fabricated ground truth) is found.

AIOps/AgentRx's descriptive analyses do not carry a PASS/FAIL verdict of
their own (no hypothesis is being tested there per §6/§8) — they are
reported as findings, with a companion "NOT CURRENTLY EVALUABLE as a
scored hypothesis; would require [frozen split]" note, per §12.

## 17. Implementation sequence (Task 17, item 22)

1. Pre-register `configs/phase4_2_active_pattern_protocol.json` (thresholds,
   splits, minimum_evaluable_n, acceptance criteria) — frozen BEFORE any
   discovery code runs against real train data, exactly matching this
   project's established protocol-freezing discipline.
2. Build `src/failure_patterns/schema.py` (types) + unit tests against
   synthetic fixtures with known, hand-computed answers.
3. Build Alibaba discovery module (§14 item 2) against train split only;
   verify against the frozen protocol's thresholds.
4. Build the leakage audit; verify the contamination test is non-vacuous
   (old Phase 4.2's exact discipline).
5. Run validation-split tier calibration (CONFIRMED replication check).
6. One-time frozen test-split evaluation (Alibaba) — after this point, per
   `docs/PHASE4_PLAN.md` §3's "once evaluated, retired" rule, this
   particular Alibaba pattern-protocol version is not re-fit-and-re-tested.
7. Build AIOps/AgentRx descriptive modules (no train/test boundary to
   respect, but still must not compute or report anything framed as a
   scored precision/recall).
8. Run the synthetic methodological-validation pass.
9. Run ablations (§15).
10. Write `docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` with full results,
    the old→new progression statement (§13), and a formal status per §16.
11. Update `docs/PHASE4_PLAN.md` with the same kind of additive amendment
    section active Phase 4.1 added (§11 there) — never rewriting existing
    content.

## 18. Expected outputs

`src/failure_patterns/` (new package), `configs/phase4_2_active_pattern_
protocol.json`, `benchmarks/phase4_2_active_pattern_evaluate.py`,
`benchmarks/phase4_2_active_leakage_audit.py`,
`experiments/results/phase4_2_active/`, new unit + integration tests,
`docs/PHASE4_2_ACTIVE_FAILURE_PATTERNS.md`, an additive amendment to
`docs/PHASE4_PLAN.md`.

## 19. Limitations (of this plan, stated up front)

- Alibaba's much larger sample size is expected to fix old Phase 4.2's
  specific `n_covered < 10` problem, but this is a **prediction**, not a
  guaranteed outcome — the frozen `minimum_evaluable_n` bar for Alibaba
  must still be checked, honestly, against whatever the real discovery run
  produces.
- AIOps/AgentRx remain descriptive-only under this plan; if that is judged
  insufficient for what "Phase 4.2" should deliver, the frozen-split
  prerequisite work (§12) should be authorized as a preceding milestone —
  this plan does not assume that authorization.
- The rate-elevation reformulation (§6) is a genuine, disclosed departure
  from the old symptom→cause framing — if a future reviewer judges this
  departure too large to still be called "Phase 4.2," that is a valid
  objection this plan surfaces rather than presupposes away; the
  alternative (forcing a `diagnosed_cause`-shaped question onto data that
  has no diagnosis layer) was judged worse (§4.3).
- No cross-dataset pattern claim is planned (§10) — if unified evidence
  across datasets is a project goal, it is out of scope for this plan and
  would need its own, separately-justified design.

## 20. Reproducibility requirements

Every discovery/evaluation script must take a fixed seed where randomness
is used (none is currently anticipated for Pattern Type 1's rate
comparison, which is deterministic; a seed will be needed only if the
`FailureEmbedder` ablation, §15, is run). All read paths are the same
frozen files already used by active Phase 4.1 and the real-data Phase 3
track — no new raw data ingestion is proposed. Results must be
regenerable by re-running the benchmark scripts against unchanged frozen
inputs, per the project's established convention.

## 21. Research-integrity safeguards — summary

See §13 (full detail). In short: old Phase 4.2 stays frozen; new evidence
is new evidence; no test-set tuning; no fabricated ground truth; no
cross-dataset generalization claims without a dedicated experiment; every
descriptive-only result (AIOps, AgentRx) is labeled as such, never
presented as a scored hypothesis test it structurally cannot be.

---

## FINAL OUTPUT (per the brief's required summary)

1. **Old Phase 4.2 status**: frozen, `INCONCLUSIVE` (evidence-volume
   insufficient, 7 < 10 covered test rows on synthetic CRITICAL-tier data).
   `docs/PHASE4_2_FAILURE_PATTERNS.md`, `src/patterns/`, its configs and
   results remain untouched by this plan.
2. **What active Phase 4.1 provides**: a canonical `FailureExperience`
   store across 4 sources (961 experiences), with the field-population
   profile in §3 — critically, no real dataset has a diagnosis-confidence
   or recovery/validation signal, and only Alibaba has a frozen split.
3. **Dataset-by-dataset suitability**: Alibaba — strong (large n, frozen
   split, genuine rate signal). AIOps — moderate/descriptive (real
   temporal structure, no split, small n). AgentRx — weak/descriptive (no
   telemetry, no timestamp, no split, small n, but genuine behavioral-
   failure-mode recurrence signal exists). Synthetic — methodological
   validation role only, not a hypothesis-bearing source.
4. **Does original H2 remain valid?** No, not unmodified — reformulated
   into per-dataset hypotheses (§6, decision E).
5. **Proposed research question**: does context (workload/task/entity/
   domain) reliably predict a specific failure mode or elevated failure
   rate, above chance, in a way that generalizes from discovery data to
   held-out data where a split exists, and remains honestly descriptive
   where it doesn't?
6. **Hypotheses**: H2-Alibaba (rate elevation, formally testable),
   H2-AIOps and H2-AgentRx (recurring association + AIOps temporal
   clustering, descriptive/exploratory pending a split).
7. **Pattern task definition**: two types, §5 — context-conditioned
   failure-rate elevation (Alibaba) and recurring failure-mode association
   (AIOps/AgentRx).
8. **Baselines**: no-pattern-learning, naive-frequency, proposed
   tiered-rate method, optional embedding-based grouping ablation (§7).
9. **Metrics**: rate-elevation precision/recall/false-pattern-rate/tier
   calibration (Alibaba); recurrence rate + temporal-clustering statistic
   (AIOps); recurrence rate only (AgentRx); several old-Phase-4.2-style
   metrics explicitly marked NOT EVALUABLE (detection lead time, all
   datasets; tier calibration, AIOps/AgentRx) (§9).
10. **Data-split/leakage protocol**: Alibaba's frozen temporal split
    (primary) + random-stratified (sensitivity check); AIOps/AgentRx
    treated as evaluation-only/descriptive, no train-test claim made
    (§8).
11. **Required prerequisite work**: none blocking; two optional,
    recommended follow-on milestones (frozen splits for AIOps and
    AgentRx) that would upgrade those sources from descriptive to
    formally testable (§12).
12. **Reuse/refactor decisions**: reuse `src/failure_experience/` directly
    as the data layer; reuse Alibaba's frozen splits and AIOps's frozen
    negative-window population directly; do not import old `src/patterns/`
    or `src/experience/`; build a new `src/failure_patterns/` package
    (§11).
13. **Proposed experiments**: Alibaba discovery/validation/test evaluation
    (primary), AIOps descriptive recurrence + temporal clustering,
    AgentRx descriptive recurrence, synthetic methodological validation
    (§14, §17).
14. **Proposed ablations**: tiered vs. flat threshold, temporal vs.
    random-stratified split, categorical key vs. embedding-clustered key,
    recurrence-threshold sweep (§15).
15. **Acceptance criteria**: PASS/PASS WITH ISSUES/INCONCLUSIVE/FAIL
    defined in §16, explicitly allowing a valid negative/null result to
    still be a scientifically successful PASS.
16. **Risks and limitations**: §19 — reformulation-validity risk, AIOps/
    AgentRx descriptive-only scope, no guarantee Alibaba's larger n
    resolves the power problem, no cross-dataset claim planned.
17. **Exact implementation plan**: §17 (11-step sequence), §14 (7-part
    smallest-valid architecture), §18 (expected file outputs).
18. **Recommendation**:

# READY FOR IMPLEMENTATION (scoped)

Ready to implement the smallest research-valid version defined in §14:
**Alibaba as the primary, rigorously-evaluated H2-Alibaba hypothesis**,
**AIOps and AgentRx as descriptive-only exploratory analyses** (not scored
hypothesis tests), and **synthetic data as a methodological-validation
track only**. The two optional prerequisite milestones (frozen splits for
AIOps/AgentRx, §12) are **not required to start** but are recommended as
follow-on work if formally-tested AIOps/AgentRx hypotheses are later
wanted — implementation should not silently attempt those without first
building and freezing the missing splits.

**Awaiting explicit approval before any implementation begins**, per the
task's instruction.
