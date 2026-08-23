<a id="phase3-real-data-3-6-decision"></a>
# PHASE3 REAL DATA 3 6 DECISION
**Status: FROZEN HISTORICAL**  
**Original file:** `docs/PHASE3_REAL_DATA_3_6_DECISION.md`  
**Role:** Real-data Phase 3.6 final decision synthesis -- the document that triggered the Phase 4 pause/reassessment.

# Phase 3.6-RD — Final Decision and Synthesis — Real-Data Phase 3 Replication

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.6-RD
execution only (Phase 4 explicitly not authorized — planning, design, or implementation).

**This is a synthesis phase. No model was trained, no representation was tested, no split was created, and
no dataset was added in the production of this document. Every number below is quoted from a Phase
3.1-RD–3.5-RD result artifact, loaded and verified against the frozen files, not recomputed.**

---

## 1. Objective

Synthesize the complete Phase 3.1-RD–3.5-RD evidence into explicit, mechanically defensible hypothesis
decisions: what does the real-data replication actually allow us to conclude, and what does it not allow us
to conclude?

## 2. Scope

In scope: reading and synthesizing frozen evidence, hypothesis-by-hypothesis decisions, cross-phase and
original-vs-real-data comparison, Phase 4 *recommendations* (not implementation), unified-benchmark
documentation (not publication). Out of scope, and not performed: any new evaluation, model, representation,
split, dataset, or Phase 4 work of any kind.

## 3. Protocol version

`1.0` throughout — `configs/phase3_real_data_protocol.json`, unchanged.

## 4. Frozen evidence inventory

| Phase | Artifact(s) | What it established |
|---|---|---|
| 3.1-RD | `experiments/results/phase3_real_data/phase3_1/{alibaba_results,aiops_results,agentrx_descriptive}.json` | H1: a supervised signal exists (Alibaba, AIOps); AgentRx H1 not executable |
| 3.2-RD | `experiments/results/phase3_real_data/phase3_2/{alibaba_results,aiops_results}.json` | H2: representation robustness on random split, fragility under temporal shift |
| 3.3-RD | `experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json` | Characterized the Q1–Q3→Q4 compound covariate+label shift |
| 3.4-RD | `experiments/results/phase3_real_data/phase3_4/{alibaba_results,aiops_results}.json` | Paired baseline comparison; R2's temporal harm confirmed statistically |
| 3.5-RD | `experiments/results/phase3_real_data/phase3_5/{alibaba_results,aiops_results}.json` | Unseen-workload-category generalization; signal weakens substantially, R2 shows no reliable effect |

## 5. Integrity checks

| Check | Result |
|---|---|
| Phase 3.1-RD unchanged | Alibaba random AUROC re-read: `0.7348398689698409` (matches every prior citation) |
| Phase 3.2-RD unchanged | Alibaba temporal R2: `0.39450623763274134` (matches) |
| Phase 3.3-RD unchanged | Label shift figures re-read: `0.20106847984458476` / `0.4341736694677871` (matches) |
| Phase 3.4-RD unchanged | Temporal R2 paired diff: `-0.10549376236725871` (matches) |
| Phase 3.5-RD unchanged | Alibaba T4-holdout n_test: `2062` (matches) |
| Original Phase 3 unchanged | `experiments/results/phase3_1/aggregate_results.json` mtime/content unchanged |
| Phase 4 unchanged | `experiments/results/phase4_0/episodes.json`, `phase4_1/`, `phase4_2/` unchanged |
| Raw data unchanged | No `data/raw/` file accessed this phase (no evaluation script was run) |
| No new evaluation occurred | No script in this phase calls `.fit(`, `predict_proba(`, or any bootstrap resampling loop — verified by inspection of every file created (§Files created) |
| No historical result overwritten | Every historical artifact was opened read-only (`json.load`), never `json.dump`-ed back to its own path |
| All hypotheses represented | H1–H7 all appear in §10 and `configs/phase3_6_rd_decision.json`, including the four marked NOT EVALUABLE |
| All negative/inconclusive/NOT_EVALUABLE findings represented | §14–16 |

No integrity check failed.

## 6. Dataset summary

| Dataset | Domain | Nominal scale | Real evaluated N |
|---|---|---|---|
| Alibaba GPU2020 | Job scheduling/failure | 988,910 eligible jobs | 10,000-job main tier (random split, temporal split, T4-holdout) |
| AIOps 2020 | Microservice fault detection | 81 fault events, 15 telemetry days | 226 windows / 43 entities (LOEO, db-holdout) |
| AgentRx Magentic | LLM agent trajectory diagnosis | 58 trajectories | 44 annotated — NOT_EVALUABLE for binary risk |
| AgentRx τ-Retail | LLM agent trajectory diagnosis | 29 trajectories | 29 annotated — NOT_EVALUABLE for binary risk |

## 7. Independent-unit summary

| Dataset | Unit | Nominal count | Effective count used in inference |
|---|---|---|---|
| Alibaba | job | up to 10,000 | 1,503–2,499 per test population (never job rows counted as anything but 1 unit each) |
| AIOps | entity (`cmdb_id`) | 226 windows | **43 entities** (16 positive-bearing, 27 negative-only) — every bootstrap in every phase resampled at the entity level, never the window level |
| AgentRx | trajectory | 87 total in source files | 44 (Magentic) / 29 (τ-Retail) — never treated as interchangeable, never pooled |

226 AIOps windows were never treated as 226 independent observations at any point in this research program.

## 8. Power/evidence-strength summary

| Condition | Effective N | CI half-width (AUROC) | Confirmatory-capable? |
|---|---|---|---|
| Alibaba random split | 1,503 jobs | ±0.03 | Yes |
| Alibaba temporal split | 2,499 jobs | ±0.02 | Yes (for the metric itself; interpretation constrained by the shift, §H3) |
| Alibaba T4-holdout | 2,062 jobs | ±0.04 | Yes for the paired test, though effect sizes are small |
| AIOps LOEO | 43 entities | ±0.11 | No — exploratory |
| AIOps db-holdout | 13 entities (2 positive) | ±0.17–0.19 | No — exploratory, and `n_valid_resamples` dropped to 1,765/2,000 because some bootstrap draws contained zero positive entities |
| AgentRx | 44 / 29 trajectories | N/A — no classifier exists | Not evaluable |

## 9. Consolidated results table

| Dataset | Condition | Candidate | AUROC | AUPRC | 95% CI (AUROC) | Paired Δ vs. baseline | Type |
|---|---|---|---|---|---|---|---|
| Alibaba | random | Baseline A | 0.500 | 0.259 | [0.500,0.500] | — | Confirmatory |
| Alibaba | random | R0 | 0.735 | 0.537 | [0.703,0.766]* | +0.235 [0.203,0.266] | Confirmatory |
| Alibaba | random | R1 | 0.736 | 0.508 | [0.705,0.767]* | +0.236 [0.205,0.267] | Confirmatory |
| Alibaba | random | R2 | 0.720 | 0.491 | [0.688,0.751]* | +0.220 [0.188,0.251] | Confirmatory |
| Alibaba | temporal | Baseline A | 0.500 | 0.434 | [0.500,0.500] | — | Confirmatory |
| Alibaba | temporal | R0 | 0.793 | 0.635 | [0.774,0.812] | +0.293 [0.274,0.312] | Confirmatory |
| Alibaba | temporal | R1 | 0.843 | 0.735 | [0.826,0.861] | +0.343 [0.326,0.361] | Confirmatory |
| Alibaba | temporal | **R2** | **0.395** | 0.355 | [0.371,0.418] | **−0.105 [−0.129,−0.082]** | Confirmatory — **significant harm** |
| Alibaba | T4-holdout (unseen) | Baseline A | 0.500 | 0.108 | [0.500,0.500] | — | Confirmatory-capable |
| Alibaba | T4-holdout (unseen) | R0 | 0.571 | 0.146 | [0.532,0.609] | +0.071 [0.032,0.109] | Confirmatory-capable |
| Alibaba | T4-holdout (unseen) | R1 | 0.550 | 0.118 | [0.512,0.587] | +0.050 [0.012,0.087] | Confirmatory-capable, small |
| Alibaba | T4-holdout (unseen) | R2 | 0.509 | 0.119 | [0.469,0.550] | +0.009 [−0.031,0.050] | **Not significant** |
| AIOps | LOEO | Baseline A | 0.500 | 0.353 | [0.500,0.500] | — | Exploratory |
| AIOps | LOEO | R0 | 0.647 | 0.573 | [0.536,0.760] | +0.146 [0.036,0.260] | Exploratory |
| AIOps | LOEO | R1 | 0.630 | 0.574 | [0.506,0.749] | +0.130 [0.006,0.249] | Exploratory, borderline |
| AIOps | LOEO | R2 | 0.605 | 0.525 | [0.477,0.728] | +0.105 [−0.023,0.228] | Exploratory — **not significant** |
| AIOps | db-holdout (unseen) | Baseline A | 0.500 | 0.218 | [0.500,0.500] | — | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R0 | 0.748 | 0.518 | [0.596,0.933] | +0.248 [0.096,0.433] | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R1 | 0.725 | 0.490 | [0.565,0.910] | +0.225 [0.065,0.410] | Exploratory, tiny N |
| AIOps | db-holdout (unseen) | R2 | 0.446 | 0.331 | [0.190,0.634] | −0.054 [−0.310,0.134] | Exploratory — **not significant** |
| AgentRx | Magentic/τ-Retail | — | — | — | — | — | **NOT EVALUABLE** |

*Alibaba random-split candidate CIs shown are from Phase 3.2-RD's independently-computed (unpaired) bootstrap; the Phase 3.4-RD paired-difference CI is the methodologically stronger figure and is what's reported in the "Paired Δ" column throughout.

No cell was omitted regardless of outcome; R2's negative/non-significant results appear exactly as often as R0/R1's positive ones.

## 10. Hypothesis-by-hypothesis decisions

### H1 — a supervised failure-risk signal exists

1. **Original hypothesis**: a supervised failure-risk signal exists beyond calibrated confidence.
2. **Evidence**: Alibaba random AUROC 0.735 [0.703,0.766]; temporal 0.793 [0.774,0.812]; AIOps LOEO 0.646
   [0.536,0.760]; AgentRx not executable (§14).
3. **Datasets providing evidence**: Alibaba (both splits), AIOps.
4. **Independent N**: 1,503–2,499 jobs (Alibaba); 43 entities (AIOps).
5. **Confirmatory/exploratory**: Alibaba confirmatory-capable; AIOps exploratory.
6. **Effect sizes/CIs**: reported above; all exclude 0.5.
7. **Limitations**: no calibrated-confidence baseline exists in real data — this answers "beats no-signal,"
   a narrower claim than the original's "beats calibrated confidence."
8. **Final status**: **SUPPORTED** (Alibaba, confirmatory precision) / **PARTIALLY SUPPORTED** (AIOps,
   exploratory-only — directionally consistent, not confirmatory) / **NOT EVALUABLE** (AgentRx).

### H2 — mechanism is supervision, not representation

1. **Original hypothesis**: supervised learning, not richer representation, drives the effect.
2. **Evidence**: Alibaba random R0≈R1≈R2 (0.735/0.736/0.720, all overlapping); Alibaba temporal R0=0.793,
   R1=0.843, R2=**0.395** (R2 significantly below baseline, Phase 3.4-RD paired CI [−0.129,−0.082]); AIOps
   R0/R1/R2 overlapping, wide CIs.
3. **Datasets**: Alibaba (both splits), AIOps.
4. **Independent N**: as H1.
5. **Confirmatory/exploratory**: Alibaba confirmatory-capable for both splits; AIOps exploratory.
6. **Effect sizes/CIs**: reported above.
7. **Limitations**: only 3 representations tested; PCA at one dimensionality only.
8. **Final status**: **PARTIALLY SUPPORTED** — holds under i.i.d.-like conditions (random split) but does
   **NOT** hold under real distribution shift (temporal split), where representation choice dominates and
   can actively harm. **INCONCLUSIVE** (AIOps). **NOT EVALUABLE** (AgentRx).

### H3 — concept-drift generalization

1. **Original hypothesis**: the frozen candidate generalizes across concept drift with covariates held fixed.
2. **Evidence**: Alibaba's only real temporal partition (Q1–Q3→Q4) is a **compound** shift — label rate
   20.1%→43.4%, `mean_plan_gpu` 70.5→56.4, `dominant_gpu_type` MISC share 62.1%→80.9% — not a concept-only
   shift like the original's `drift_scale` mechanism.
3. **Datasets**: Alibaba only (descriptive characterization); AIOps/AgentRx not evaluable for this specific
   axis (no frozen temporal partition for AIOps; no timestamps for AgentRx).
4. **Independent N**: 6,177 train / 2,499 test jobs.
5. **Confirmatory/exploratory**: the characterization itself is descriptive, not a point-estimate hypothesis
   test in the original's sense.
6. **Effect sizes/CIs**: not applicable to the characterization itself; the associated R0/R1/R2 temporal
   results are reported under H1/H2 above.
7. **Limitations**: exactly one real train/test temporal partition exists — no repeated-shift design as the
   original's `drift_scale` sweep allowed.
8. **Final status**: **NOT DIRECTLY COMPARABLE** — different shift type (concept-only vs. compound
   concept+covariate); the real evidence neither replicates nor contradicts the original, it tests a
   structurally different condition. AIOps/AgentRx **NOT EVALUABLE**.

### H4 — covariate-shift / attack generalization

1. **Original hypothesis**: the frozen candidate survives synthetic feature-noise/dropout attacks, remaining
   competitive with calibrated confidence.
2. **Evidence**: the literal mechanism (synthetic feature corruption) is **NOT EVALUABLE** on real data — no
   real-data analogue exists and fabricating one is prohibited. The reframed, real, non-synthetic axis
   (unseen-workload-category holdout) shows: Alibaba T4-holdout R0 AUROC 0.571 (paired Δ +0.071
   [0.032,0.109]), R1 0.550 (+0.050 [0.012,0.087]), R2 0.509 (+0.009 [−0.031,0.050], not significant); AIOps
   db-holdout R0 0.748 (+0.248 [0.096,0.433]), R1 0.725 (+0.225 [0.065,0.410]), R2 0.446 (−0.054
   [−0.310,0.134], not significant).
3. **Datasets**: Alibaba, AIOps (exploratory).
4. **Independent N**: 2,062 jobs (Alibaba); 13 entities (AIOps).
5. **Confirmatory/exploratory**: Alibaba paired test is precise enough to distinguish small effects;
   AIOps is exploratory with very wide CIs.
6. **Effect sizes/CIs**: reported above.
7. **Limitations**: one held-out category per dataset, chosen by a fixed a priori rule, not a sweep.
8. **Final status**: **PARTIALLY SUPPORTED** for R0/R1 (small but real margin over no-signal on an entirely
   unseen category, on both datasets); **NOT SUPPORTED** for R2 (no significant effect on either dataset);
   **NOT DIRECTLY COMPARABLE** to the original's specific synthetic-attack mechanism. AgentRx **NOT
   EVALUABLE**.

### H5a — complementarity (does the signal add value beyond calibrated confidence)

1. **Original hypothesis**: does Failure Risk add information beyond calibrated confidence?
2. **Evidence**: none generated — no calibrated-confidence baseline exists anywhere in the real-data track,
   so there was never a second signal to test complementarity against.
3. **Datasets**: none.
4. **Final status**: **NOT EVALUABLE** — structural, not a result of any test that was run and came back
   negative.

### H5b — decision-cost policy

1. **Original hypothesis**: does converting risk scores into decisions (answer/review/abstain) produce a
   favorable cost outcome relative to doing nothing?
2. **Evidence**: none generated — no real, disclosed deployment cost model exists for any of the three
   datasets, and none was fabricated.
3. **Final status**: **NOT EVALUABLE**.

### H6 — diagnosis

1. **Original hypothesis**: can the pipeline diagnose the cause of a failure/anomaly?
2. **Evidence**: none generated in Phase 3.1-RD–3.5-RD. This is distinct from H5a/H5b/H7: AgentRx's organic
   `root_cause_failure_id`/`root_cause_reason` fields and AIOps's injected fault categories **do exist** and
   were explicitly preserved for this purpose in the frozen protocol (`docs/PHASE3_REAL_DATA_PROTOCOL.md`
   §3), but no authorized phase in this research program (protocol design through 3.6-RD synthesis) included
   running a diagnosis experiment.
3. **Final status**: **NOT EVALUABLE** — not attempted, not blocked by data unavailability. This is the one
   hypothesis in this table where the gap is scope, not data.

### H7 — recovery

1. **Original hypothesis**: can the pipeline recover from a diagnosed failure, and does that recovery help?
2. **Evidence**: none — no dataset (Alibaba, AIOps, AgentRx) records a recovery action or outcome field.
3. **Final status**: **NOT EVALUABLE / STRUCTURAL GAP** — no future phase can evaluate this under the
   currently held data without new data acquisition.

## 11. Original Phase 3 vs. real-data Phase 3 comparison

| Hypothesis | Relationship |
|---|---|
| H1 | Real data **extends** the original — same qualitative "beats no-signal" conclusion holds on Alibaba (confirmatory) and AIOps (exploratory); cannot be compared on the original's specific "beats calibrated confidence" framing since no such baseline exists in real data. |
| H2 | **Partially replicated** on the random split (representation-agnostic, as originally found); **newly discovered boundary condition** on the temporal split (representation sensitivity under real shift) that the original's single-condition synthetic design never had the opportunity to surface. |
| H3 | **Not directly comparable** — different shift type entirely (compound real shift vs. controlled concept-only synthetic shift). |
| H4 | **Not directly comparable** on mechanism (real categorical holdout vs. synthetic feature perturbation); where a loose qualitative comparison is possible, real data shows a smaller, more representation-dependent margin than the original's "remains competitive" finding. |
| H5a/H5b | **Not evaluable** — no real-data version of this question was ever askable, so no comparison to the original's INCONCLUSIVE finding is possible. |
| H6 | **Not evaluable** — not attempted, no comparison to the original's 0.683 pooled accuracy is possible yet. |
| H7 | **Not evaluable** — the original's own INCONCLUSIVE finding (0% successful reconfiguration recovery) has no real-data counterpart to compare against. |

No relationship above claims real data "disproved" or "validated" the original beyond what the actual
evidence in §10 supports.

## 12. Strongly supported findings

- A real, statistically clear supervised failure-risk signal exists in the Alibaba GPU2020 job-scheduling
  domain, at confirmatory-capable precision, on both a random and a temporal held-out population (§H1).
- Representation choice (R0 vs. R1 vs. R2) makes little difference under i.i.d.-like (random-split)
  conditions on Alibaba (§H2).

## 13. Partially supported findings

- The signal generalizes to entirely unseen GPU-type/object-family categories, but with a substantially
  smaller margin than in-distribution performance (§H4).
- The signal exists on AIOps, but only at exploratory precision — directionally consistent evidence, not
  confirmatory (§H1, §H4).

## 14. Negative findings (first-class results, not omitted)

- **R2 (PCA(2)) collapses to AUROC 0.395 — significantly WORSE than no-signal — on the Alibaba temporal
  split** (paired diff −0.105, CI [−0.129,−0.082]) (Phase 3.2-RD/3.4-RD).
- **R2 shows no statistically distinguishable improvement over no-signal under either unseen-workload
  condition tested** (Alibaba T4-holdout, AIOps db-holdout) (Phase 3.5-RD).
- The failure-risk signal's magnitude drops substantially under genuine unseen-workload-category
  generalization relative to in-distribution splits (Alibaba: 0.51–0.57 vs. 0.72–0.84) (Phase 3.5-RD).
- No calibrated-confidence-equivalent baseline exists anywhere in the real-data track — a structural
  limitation present since Phase 3.1-RD, not resolved by any subsequent phase.
- AgentRx's binary failure-risk task is not executable on either frozen sample — present since Phase 3.1-RD,
  unresolved by design (no unannotated trajectories were added to manufacture a negative class).

## 15. Inconclusive findings

- AIOps R2 vs. no-signal, both in the primary LOEO evaluation (Phase 3.1-RD/3.2-RD/3.4-RD, paired CI
  [−0.023,0.228]) and under unseen-family generalization (Phase 3.5-RD, CI [−0.310,0.134]).
- AIOps R1's improvement over no-signal is real but sits close to the CI boundary in more than one phase
  (Phase 3.4-RD paired [0.006,0.249]; Phase 3.5-RD unseen-family [0.065,0.410]) — treated as weak, not
  strong, evidence throughout.
- Whether R2's fragility reflects a general property of PCA(2) under any distribution change, or something
  specific to the particular shifts tested, remains open (§21 alternative explanations, carried from Phase
  3.3-RD/3.5-RD, not resolved here).

## 16. NOT_EVALUABLE findings

- AgentRx: H1–H4 (no negative class in either frozen sample).
- H5a (complementarity): no calibrated-confidence baseline exists.
- H5b (decision-cost policy): no real cost model exists or was fabricated.
- H6 (diagnosis): not attempted in any authorized phase, despite existing usable fields.
- H7 (recovery): no dataset records a recovery outcome.

## 17. Newly discovered findings (not present in, or not derivable from, the original Phase 3)

- **Representation sensitivity that only emerges under real distribution shift** — the original synthetic
  Phase 3.2/3.2C found representation-agnostic behavior and never tested it under a shifted condition; real
  data shows this agnosticism does *not* extend to distribution shift.
- **A candidate representation can be significantly worse than doing nothing** (R2 on Alibaba temporal) — no
  analogous result exists anywhere in the original Phase 3, where the weakest candidate (original Failure
  Memory) underperformed no-signal on AURC but was never shown to be *significantly* worse on AUROC via a
  paired test.
- **GPU-type carries a strong, direct association with job failure rate** (T4 jobs fail at 10.8% vs. 29.9%
  for non-T4) — an incidental finding surfaced by the Phase 3.5-RD holdout design, not something the original
  synthetic benchmark could have produced (it has no analogous categorical structure).
- **The signal's generalization margin is substantially smaller for genuinely unseen categories than for
  unseen time periods** — a distinction between two kinds of "generalization" that the original single-axis
  (concept-drift-only) Phase 3.3 design never had the structure to reveal.

## 18. Limitations

- No calibrated-confidence baseline exists in the real-data track, permanently narrowing every H1/H4/H5a
  comparison relative to the original's framing.
- AIOps's exploratory status (43 independent entities) means several results in this report (R1's marginal
  significance, R2's non-significance) could plausibly flip with a larger real dataset — this is disclosed,
  not treated as settled.
- AgentRx contributed zero quantitative evidence to this entire research program (Phase 3.1-RD–3.5-RD) due to
  its frozen sample's all-positive composition.
- Only one held-out condition per generalization axis was tested (one temporal split, one unseen GPU
  category, one unseen object family) — none of these are a sweep over the space of possible shifts/unseen
  conditions.

## 19. Structural gaps

H5a, H5b, H7 (§16) — these cannot be resolved by re-running anything in the current research program; they
require either new data (H7's recovery outcomes) or a real cost/baseline model that does not currently exist
(H5a, H5b) and was correctly not fabricated at any point.

## 20. Scientific interpretation

Real data both **confirms and complicates** the original Phase 3's central finding. It confirms that a
supervised classifier finds real, useful signal in operational failure data (H1) and that this signal is not
purely an artifact of representation choice under stable conditions (H2, random split). It complicates the
original's implicit assumption (never directly tested there, since only one representation was ever
evaluated under drift) that representation choice is a minor implementation detail: under real distribution
shift — whether temporal (Phase 3.3-RD/3.4-RD) or categorical (Phase 3.5-RD) — representation choice becomes
a first-order factor, capable of turning a working signal into an actively harmful one (R2). No claim is made
that this generalizes beyond the three representations and the specific real datasets tested here.

## 21. Phase 4 implications — recommendations for later planning (NOT implemented here)

These are recommendations only. No Phase 4 file was read, modified, or planned in detail as part of this
phase.

- **Regime/context awareness**: the real-data findings suggest that a failure-risk signal's reliability is
  not uniform across operating conditions — it degrades under both temporal shift and unseen-category
  conditions, and for at least one representation, can become actively counterproductive. Phase 4's failure
  memory / pattern-discovery components may need a mechanism to assess whether the current operating regime
  resembles the regime in which a stored failure experience was learned, before treating that experience as
  applicable — this is a direct, explicit implication of the R2-temporal-collapse and unseen-category-margin
  findings (Phase 3.2-RD/3.4-RD/3.5-RD), not a generic caution.
- **Distribution-shift awareness**: any Phase 4 component that reuses a fitted risk model across time or
  across workload categories should have a way to detect when it is operating outside the population it was
  validated on, given how differently R0/R1/R2 behaved between in-distribution and shifted/unseen conditions
  in this report.
- **Uncertainty estimation**: given how wide AIOps's confidence intervals are at 43 independent entities,
  Phase 4 components trained or validated on similarly small real populations should propagate that
  uncertainty rather than treating a point estimate as settled.
- **Abstention/safety gating**: the original Phase 3.6 found autonomous decision authority "not justified"
  even on synthetic data with a working signal; the real-data finding that a representation can be
  significantly *harmful* under shift (not just unhelpful) is an additional, concrete reason for caution
  before Phase 4 grants any automated system decision authority based on a fitted risk score without a
  shift-detection or abstention safeguard.
- **Memory applicability checks**: if Phase 4's failure memory stores experiences keyed partly by context
  (e.g., workload/GPU-type/time), the H2/H4 findings here directly motivate checking that a retrieved
  experience's context resembles the current context before applying it — retrieving an experience from a
  now-absent regime (analogous to this report's T4/db holdouts) produced a measurably weaker, sometimes null,
  signal.
- **No change needed**: nothing in this report suggests the core Phase 4.0/4.1/4.2 architecture (episodic
  data capture, failure memory, pattern discovery) is fundamentally unsound — the findings bear on *when* a
  stored experience should be trusted, not on whether storing and retrieving experiences is a reasonable
  design.

## 22. Future experiments (documented, not performed)

- H6 (diagnosis) on AgentRx's organic root-cause fields and AIOps's injected fault categories — data exists,
  scope did not include running it.
- A sweep over additional unseen-category holdouts (Alibaba: P100, V100, V100M32, UNKNOWN; AIOps: `os`) to
  determine whether the T4/`db` findings generalize across held-out choices.
- A dedicated mechanistic investigation of R2's fragility (e.g., PCA component loadings pre/post shift).
- A larger AIOps population, if more real fault/telemetry data becomes available, to narrow the wide CIs
  throughout this report.
- Any H5a/H5b/H7-equivalent experiment, contingent on acquiring a real cost model or recovery-outcome data
  that does not currently exist.

None of the above was performed in this phase, and none influenced any decision in §10.

## 23. Unified benchmark/dataset implications

Per every prior phase's preserved-field discipline, the eventual unified real-world benchmark should
continue to preserve, without forcing a common schema across datasets that don't naturally share one:

- **Common (cross-dataset) fields**: `source_dataset`, `source_record_id` (native: `job_name` / fault-log
  `index` / `trajectory_id`), `independent_unit_type` (job / entity / trajectory — explicit, not assumed),
  `split_membership` (including which generalization condition, e.g. "T4-holdout-test", a record belongs to),
  `label_provenance` (observed outcome / injected fault / organic annotation), `processing_version`,
  `representation_version` (R0/R1/R2 or future additions), `data_quality_flags`.
- **Dataset-specific fields, preserved not discarded**: Alibaba's `dominant_gpu_type`/machine-spec fields;
  AIOps's `cmdb_id` object-family and telemetry-coverage flags; AgentRx's `num_failures`/`failure_categories`/
  `root_cause_*` fields (with an explicit flag that these represent 100%-failure-composition samples, not a
  representative failure-rate population).
- **Explicit MISSING markers**, never imputed values, where a dataset structurally lacks a field another
  dataset has (e.g., AgentRx has no timestamp field at all).
- **This report adds one new preservation requirement**: for any future evaluation using a leave-category-out
  design (as Phase 3.5-RD did), the held-out category identity and the selection rule that chose it must be
  recorded alongside the split — reconstructing *why* a category was excluded, not just that it was.

No data was published or uploaded in this phase.

## 24. Reproducibility/provenance

Every number in this document was loaded via `json.load` from an existing frozen artifact and printed for
verification before being written here — no value was retyped from memory without a corresponding artifact
read in this phase's session. `configs/phase3_6_rd_decision.json` records the same evidence in
machine-readable form.

## 25. Final decision table

| Hypothesis | Original Phase 3 | Real-data evidence | Dataset(s) | Effective N | Evidence type | Final status | Key limitation |
|---|---|---|---|---|---|---|---|
| H1 | F beats no-signal 6/6 seeds, AUROC 0.6548 | AUROC 0.735 (random), 0.793 (temporal), 0.646 (AIOps) | Alibaba, AIOps | 1,503–2,499 jobs; 43 entities | Confirmatory (Alibaba); Exploratory (AIOps) | **SUPPORTED** (Alibaba) / **PARTIALLY SUPPORTED** (AIOps) / **NOT EVALUABLE** (AgentRx) | No calibrated-confidence baseline exists in real data |
| H2 | Supervision, not representation, is the mechanism | Robust on random split; R2 collapses under temporal shift | Alibaba, AIOps | as H1 | Confirmatory (Alibaba); Exploratory (AIOps) | **PARTIALLY SUPPORTED** (Alibaba) / **INCONCLUSIVE** (AIOps) / **NOT EVALUABLE** (AgentRx) | Only 3 representations tested |
| H3 | Generalizes across concept-only drift | Q1–Q3→Q4 is a compound concept+covariate shift | Alibaba (descriptive) | 6,177/2,499 | Descriptive | **NOT DIRECTLY COMPARABLE** | Single real temporal partition |
| H4 | Robust to synthetic covariate-shift attacks | Real unseen-category holdout: small real margin for R0/R1, none for R2 | Alibaba, AIOps | 2,062 jobs; 13 entities | Confirmatory-capable (Alibaba); Exploratory (AIOps) | **PARTIALLY SUPPORTED** (R0/R1) / **NOT SUPPORTED** (R2) / **NOT DIRECTLY COMPARABLE** to original mechanism | Single held-out category per dataset; literal mechanism not reproducible |
| H5a | F adds no value beyond B | No real baseline to test against | None | — | — | **NOT EVALUABLE** | Structural — no calibrated-confidence analogue |
| H5b | Risk policies cost less than nothing at base ratio, more at stricter ratio | No real cost model | None | — | — | **NOT EVALUABLE** | No cost model exists |
| H6 | Diagnosis accuracy 0.683 | Not attempted | None (data exists, unused) | — | — | **NOT EVALUABLE** | Scope gap, not data gap |
| H7 | 0% successful reconfiguration recovery | No recovery data | None | — | — | **NOT EVALUABLE / STRUCTURAL GAP** | No dataset records recovery outcomes |

## 26. Final research conclusions

The real-data replication of Phase 3 finds genuine, statistically supported evidence that a supervised
failure-risk signal exists in real operational data (Alibaba GPU scheduling, more tentatively AIOps
microservice telemetry), reproducing the qualitative core of the original synthetic finding. It does **not**
find that this signal, or the representation used to compute it, is uniformly robust: under real distribution
shift — whether across time or across previously-unseen workload categories — both the signal's strength and
its representation-dependence change substantially, and at least one tested representation (PCA(2)) can
become actively harmful rather than merely unhelpful. Four hypotheses (H5a, H5b, H6, H7) remain unevaluated —
three for structural reasons (no comparable baseline, no cost model, no recovery data) and one (H6) purely
because it was never attempted despite usable data existing. AgentRx contributed no quantitative evidence to
any hypothesis in this program due to its frozen sample's all-positive composition. These findings — positive,
negative, and unevaluated alike — are reported as the complete, honest state of the evidence; no result was
suppressed, and no hypothesis's status was inflated beyond what its confidence interval and independent
sample size support.

---

## Files created by this execution

- `configs/phase3_6_rd_decision.json`
- `docs/PHASE3_REAL_DATA_3_6_DECISION.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — final synthesis section)

No historical file (Phase 3.1-RD–3.5-RD artifacts, original Phase 3, Phase 4) was opened for writing at any
point in this phase. No evaluation script was executed.

---

## STOP — Phase 3.6-RD complete. Real-data Phase 3 replication research program complete pending review.

Phase 4 was not started, modified, planned in implementation detail, or touched in any way. Awaiting separate
review and explicit authorization before any Phase 4 work begins.
