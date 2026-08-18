<a id="phase4-1-failure-memory"></a>
# PHASE4 1 FAILURE MEMORY
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE4_1_FAILURE_MEMORY.md`  
**Role:** OLD Phase 4.1: synthetic-only failure memory / experience retrieval (H1 PARTIALLY SUPPORTED). Superseded in role, not in content, by the ACTIVE Phase 4.1 later in this document -- see the Active Phase 4 Reassessment section for the relationship.

# Phase 4.1 — Failure Memory & Experience Learning

**Status: COMPLETE.** This document is the Phase 4.1 deliverable, per
[`docs/PHASE4_PLAN.md`](PHASE4_PLAN.md).

Companion artifacts: [`configs/phase4_1_experience_protocol.json`](../configs/phase4_1_experience_protocol.json),
[`src/experience/`](../src/experience/),
[`benchmarks/phase4_1_retrieval_evaluate.py`](../benchmarks/phase4_1_retrieval_evaluate.py),
[`benchmarks/phase4_1_leakage_audit.py`](../benchmarks/phase4_1_leakage_audit.py),
[`experiments/results/phase4_1/`](../experiments/results/phase4_1/),
[`tests/unit/test_experience_schema.py`](../tests/unit/test_experience_schema.py),
[`tests/integration/test_phase4_1_retrieval.py`](../tests/integration/test_phase4_1_retrieval.py).

## 1. Objective and hypothesis

**H1** (fixed before evaluation, `configs/phase4_1_experience_protocol.json`):
a structured, indexed experience store built on `ReliabilityEvent` +
episode outcome data can retrieve relevant past incidents for a new
failure with better-than-chance similarity ranking, without becoming an
unstructured log.

## 2. What was reused (inspected first, per 4.1.1)

- `src.schema.events.ReliabilityEvent` — the experience representation is
  built ON this, not a parallel schema. `workload_id`, `context`,
  `confidence`, `failure_risk`, `decision`, `abstained`, `is_failure`,
  `outcome`, `metadata` are used directly; nothing was duplicated.
- `src.storage.repository.EventRepository` / `src.storage.db` — reused
  unmodified for optional persistence (`ExperienceStore.persist`).
- `src.failure_memory.embedding.FailureEmbedder` — reused unmodified for
  the proposed method's similarity computation (identical embedding
  formula to `src.failure_memory.memory.FailureMemory.retrieve`, not
  reimplemented).
- `src.evaluation.diagnosis.diagnose` (indirectly, via Phase 4.0's
  `diagnosed_cause` field) — the decision-time proxy for condition
  identity.
- Phase 4.0's `experiments/results/phase4_0/episodes.json` — the sole
  data source; not regenerated, not modified.
- `docs/PHASE3_FREEZE.md` and `docs/PHASE4_PLAN.md` section 3 (isolation
  protocol) — governed every split-usage decision below.

No frozen Phase 3 file was edited. `src/failure_memory/` is unchanged;
`src/experience/` is new, additive code that calls into it read-only.

## 3. What was newly implemented

`src/experience/`:
- `schema.py` — `EpisodeProvenance` (episodic metadata `ReliabilityEvent`
  has no field for: `condition_id` ground truth, occurrence/step/split,
  diagnosis, recovery trace, protocol/dataset version), `DecisionTimeQuery`
  (the only type retrieval functions accept — structurally excludes
  `condition_id`/outcome/recovery fields, not just by convention; see
  §5), `Experience` (event + provenance), `experience_from_episode_record`
  (builder), `deterministic_event_id` (reproducible, not `uuid4`-random,
  so store content-hashing is meaningful).
- `store.py` — `ExperienceStore` (in-memory; `add`/`add_many`,
  `fit_embedder`, `retrieve_random`/`retrieve_recency`/`retrieve_similarity`,
  `persist`, `content_hash`), `build_store_from_episode_records`
  (split/failure-filtered builder).
- `metrics.py` — `precision_at_k`, `recall_at_k`,
  `same_workload_and_condition_rate` (secondary diagnostic),
  `count_relevant_in_store`.

`configs/phase4_1_experience_protocol.json` — frozen before evaluation:
data source and split rules, relevance definition, the 3 retrieval
methods, `k ∈ {1,3,5}`, the decay ablation (validation-only), and
pre-registered H1 acceptance criteria.

## 4. Data used / excluded

**Store population**: `split == "train"` AND `is_failure == true` rows
only (178 of Phase 4.0's 960 rows). Restricting to failures matches
`FailureMemory`'s existing store-only-failures convention (not a new
scope decision).

**Query sets**: `is_failure == true` rows from `split == "validation"`
(decay ablation only) and `split == "test"` (primary reported evaluation),
further split into `known_combo_test` (n=51) and `novel_combo_test`
(n=28), `all_test` = both pooled (n=79).

**Excluded**: every `validation`/`test` row, and every `is_failure ==
false` row, is never added to the store — enforced by
`build_store_from_episode_records`'s filter and verified by the leakage
audit (§6).

## 5. Decision-time vs. outcome vs. evaluation-only information

Enforced structurally, not by convention: `DecisionTimeQuery`
(`context`, `confidence`, `workload_id`, `tier`, `diagnosed_cause`,
`step`) has no field for `condition_id`, `true_label`, `outcome`,
`is_failure`, or any `recovery_*` value —
`tests/unit/test_experience_schema.py::
test_decision_time_query_has_no_outcome_or_ground_truth_fields` asserts
this directly against the dataclass's field set, so it fails loudly if
the type is ever extended carelessly. `condition_id` (Phase 4.0's
generator ground truth) is passed to `precision_at_k`/`recall_at_k`
directly by the benchmark script — never through a query object — and is
documented in `metrics.py`'s module docstring as evaluation-only.

## 6. Leakage/integrity audit — all 6 checks passed

`benchmarks/phase4_1_leakage_audit.py`: `store_contains_only_train_split`,
`store_contains_only_is_failure_true_rows`,
`decision_time_query_excludes_ground_truth_and_outcome_fields`,
`store_content_hash_is_deterministic`,
`no_validation_or_test_event_id_present_in_store`,
`retrieval_on_empty_store_returns_empty_not_error`. Result:
`experiments/results/phase4_1/leakage_audit.json`, `all_passed: true`.

## 7. Baselines and proposed method (4.1.6)

- **A — no-memory/uniform-random**: `retrieve_random(query, k, seed=42)`,
  ignores query content entirely.
- **B — recency-only**: `retrieve_recency(query, k)`, k most recent
  stored experiences by `step`, ignores content.
- **C — similarity (proposed)**: `retrieve_similarity(query, k,
  decay_lambda=0.0)`, k-nearest by `FailureEmbedder` embedding distance
  over context + confidence — the smallest research-valid mechanism
  (4.1.9), no recency weighting in the primary result.

No baseline was added or removed after seeing a result.

## 8. Metrics (4.1.7)

**Precision@k** = (# retrieved among top-k sharing `condition_id` with
the query) / (# actually retrieved, ≤ k). **Recall@k** = (# retrieved
among top-k sharing `condition_id`) / (total # train-split failures in
the store sharing that `condition_id`). Both `None` (not fabricated 0.0)
when undefined (empty retrieval / zero relevant population). 95%
percentile bootstrap CIs (1000 resamples, seed 0) over per-query values —
a small new utility (`_bootstrap_mean_ci`), documented as not reusing
`src.evaluation.bootstrap.bootstrap_ci` because that function's
`metric_fn(y_true, y_score)` signature doesn't fit a per-query-array use
case.

## 9. Results

Store size: 178 (train-split failures). Query groups: `all_test` n=79,
`known_combo_test` n=51, `novel_combo_test` n=28.

**Precision@k, mean [95% CI]:**

| Group | Method | k=1 | k=3 | k=5 |
|---|---|---|---|---|
| all_test | A random | 0.278 [0.190, 0.367] | 0.253 [0.224, 0.283] | 0.218 [0.180, 0.261] |
| all_test | B recency | 0.165 [0.089, 0.253] | 0.165 [0.089, 0.253] | 0.165 [0.089, 0.253] |
| all_test | **C similarity** | 0.241 [0.152, 0.342] | **0.283 [0.215, 0.354]** | 0.256 [0.208, 0.309] |
| known_combo_test | A random | 0.314 [0.176, 0.451] | 0.255 [0.216, 0.288] | 0.255 [0.192, 0.314] |
| known_combo_test | B recency | 0.255 [0.137, 0.373] | 0.255 [0.137, 0.373] | 0.255 [0.137, 0.373] |
| known_combo_test | **C similarity** | 0.314 [0.196, 0.431] | **0.346 [0.268, 0.418]** | 0.298 [0.239, 0.361] |
| novel_combo_test | A random | 0.214 [0.071, 0.358] | 0.250 [0.190, 0.298] | **0.150 [0.114, 0.179]** |
| novel_combo_test | B recency | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| novel_combo_test | C similarity | 0.107 [0.000, 0.250] | 0.167 [0.071, 0.274] | 0.179 [0.107, 0.264] |

Full precision/recall (all k, both metrics, all groups) + the decay
ablation: `experiments/results/phase4_1/retrieval_results.json`.

**Decay ablation (validation split only, precision@k, method C):**
`decay_lambda ∈ {0.0, 0.01, 0.05, 0.1}` produced precision@1/3/5 of
`{0.40, 0.35, 0.33}`, `{0.44, 0.34, 0.30}`, `{0.36, 0.37, 0.30}`, `{0.36,
0.34, 0.32}` respectively — no `decay_lambda` value shows a consistent
improvement over `0.0` across k; differences are within what 25-query
validation noise would produce. **Conclusion: no recency weighting is
adopted.** The primary reported method C result (`decay_lambda=0.0`)
stands as the frozen default per the protocol — this ablation was
evaluated, found not to help, and reported as a negative finding, not
silently dropped.

## 10. Is H1 supported? — Per the pre-registered acceptance criteria

Applying `configs/phase4_1_experience_protocol.json`'s
`acceptance_criteria` exactly as written (CI *lower bound* of C must
exceed *both* baselines' point estimates, same group/k):

- **`known_combo_test`, k=3**: C = 0.346, CI = [0.268, 0.418] — CI lower
  bound (0.268) exceeds both A's (0.255) and B's (0.255) point estimates.
  **Criterion met.**
- **`all_test`**, every k, and **`known_combo_test`** at k=1/k=5: C's CI
  lower bound does NOT clear both baselines (closest miss:
  `all_test` k=5, CI low 0.208 vs. A's 0.218). **Criterion not met.**
- **`novel_combo_test`**: C never clears baseline A at any k, and at k=1
  C (0.107) is numerically *below* A (0.214) — random guessing
  outperforms similarity retrieval on this group at k=1. **Criterion not
  met; directionally unfavorable to C.**

Per the protocol's `H1_partially_supported` definition ("Method C beats
both baselines by the criterion above on SOME but not all k values, or
on known_combo_test but not novel_combo_test"), this is exactly that
case.

## 11. Formal decision

# 🟡 H1: PARTIALLY SUPPORTED

Structured similarity retrieval clears the pre-registered bar against
both no-memory-random and recency-only baselines in exactly one tested
condition (`known_combo_test`, k=3), and is directionally favorable
(though not statistically clearing the bar) at most other known-combo
k's. It reliably, consistently beats the recency-only baseline (B) across
every group and k — recency alone carries no useful signal here, which
is itself a finding (B's precision is flat across k because it always
retrieves the same fixed most-recent-k set for every query, evidently a
population whose condition mix does not track any individual query's
condition). It does **not** reliably beat pure random retrieval (A) on
pooled `all_test`, and on `novel_combo_test` it is sometimes *worse* than
random at k=1.

## 12. Failure-case analysis

- **Why C underperforms A on `novel_combo_test` at k=1**: novel-combo
  queries come from a workload/condition pair the store has zero
  matching examples of; the nearest store neighbor by raw embedding
  distance is then whatever failure (any workload, any condition)
  happens to sit closest in the 2-PCA-component + confidence-derived
  embedding space — which is not guaranteed to share the query's
  condition, and single-nearest-neighbor (k=1) has no averaging effect to
  dampen an unlucky closest match. Random retrieval, by chance, sometimes
  does better simply because the store's overall composition happens to
  favor conditions common across workloads.
- **Why recency-only (B) is flat and weak**: `retrieve_recency` returns
  the same fixed set of the most-recent-`step` stored experiences for
  every query, regardless of content — precision@k is therefore just that
  fixed set's own condition-match rate against whichever query is asked,
  which cannot adapt to different queries; it collapses to near-zero on
  `novel_combo_test` because that fixed recent set essentially never
  happens to share a novel query's specific condition.
- **Sample-size caution**: `novel_combo_test` (n=28) and even
  `known_combo_test` (n=51) are small; several CIs are wide and
  overlapping between methods (e.g. `all_test` k=1 and k=3 for A vs. C).
  The one criterion-clearing result (`known_combo_test`, k=3) should be
  read as suggestive, not decisive, given six query-group/k combinations
  were checked and only one cleared the bar — some chance this reflects
  multiple-comparisons noise rather than a robust effect; this is stated
  as a limitation, not adjusted away post hoc (no correction was
  pre-registered, so none is applied retroactively either).

## 13. Limitations

- Relevance is defined at the `condition_id` (corruption-mechanism)
  level, not workload-specific — a deliberate, documented scope choice
  (§8), not an oversight; `same_workload_and_condition_rate` exists as a
  secondary diagnostic but was not the primary metric.
- The embedding (`FailureEmbedder`: 2-component PCA + 2
  confidence-derived scalars) is the exact, unmodified Phase 2/3
  representation — no new representation was developed for Phase 4.1;
  if H1's partial support is representation-limited rather than
  retrieval-mechanism-limited, this evaluation cannot distinguish the two
  (a Phase 4.2 concern, not addressed here).
- `novel_combo_test`'s "novelty" is exactly Phase 4.0's documented scope
  (workload/condition combination novelty, not novel corruption
  mechanisms) — carried forward from `docs/PHASE4_0_EPISODIC_DATA.md`
  section 8 verbatim, per the review requirement that this limitation
  remain part of the record.
- No persistence-layer evaluation was performed at scale (the `persist`/
  reload round trip is tested for correctness on 5 rows, not benchmarked
  for retrieval performance from a reloaded store — out of scope, no
  Phase 4.1 experiment needed it).

## 14. Progression note (per the review's research-integrity clarification)

Phase 3.6 (frozen) found F/BF add no measured value over calibrated
confidence B for *prediction*. Phase 4.1 asks a structurally different
question — can *retrieval over stored failure history* (not a fitted
risk score) find relevant past incidents — and finds partial,
condition-dependent support. These are independent findings about
different mechanisms; Phase 3.6's result is not touched, revisited, or
implied to be resolved by this one. If a later Phase 4 subphase (e.g.
4.2's pattern learning, which may use a different or enriched
representation) produces evidence that further resolves whether
retrieval-based memory is useful, that will be recorded as: **Phase 4.1
→ PARTIALLY SUPPORTED (this document) → new Phase 4.X evidence →
combined conclusion**, in a new document — not by editing this one.

## 15. Deliverables checklist

1. `src/experience/` implementation — done (`schema.py`, `store.py`, `metrics.py`).
2. Phase 4.1 tests — done (6 unit + 12 integration = 18, all passing).
3. Retrieval/evaluation benchmark — done (`benchmarks/phase4_1_retrieval_evaluate.py`).
4. Baseline implementations — done (A, B in `ExperienceStore`).
5. Reproducible configuration — done (`configs/phase4_1_experience_protocol.json`).
6. Learned-state/provenance artifact — done (`ExperienceStore.content_hash()`, recorded in `retrieval_results.json`).
7. Phase 4.1 experiment results — done (`experiments/results/phase4_1/retrieval_results.json`).
8. Failure-case analysis — done (§12).
9. Metric definitions — done (§8, `src/experience/metrics.py` docstrings).
10. `docs/PHASE4_1_FAILURE_MEMORY.md` — this document.
11. Full test-suite results — 244/244 pre-existing + 18 new = 262/262 (see completion report).
12. Phase 4.1 verification/completion record — §11 (formal decision) + this checklist.

## 16. Final status

# 🟡 PASS WITH ISSUES

Implementation, evaluation, documentation, and research-integrity checks
are complete. H1 is **partially supported**: the proposed mechanism is
implemented correctly, is measurably better than the recency baseline
everywhere and better than random in the one condition it was
pre-registered to be judged strongest in (`known_combo_test`), but does
not clear the pre-registered bar against random retrieval when pooled,
and is directionally unfavorable on the hardest (`novel_combo_test`)
group at low k. This is reported as-is — a mixed, not uniformly positive,
result — consistent with the research-integrity requirement not to treat
implementation success as hypothesis support.
