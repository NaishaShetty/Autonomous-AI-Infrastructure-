# Phase 3.4-RD — Consolidated Baseline-vs-Candidate Comparison — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.4-RD
execution only (Phase 3.5-RD, 3.6-RD, and Phase 4 explicitly not authorized).

---

## 1. Objective

Following the original (synthetic) Phase 3.4's design (`docs/PHASE3_4_COMPARISON.md`): consolidate everything
evaluated so far into one comparison, under the same frozen protocol, with **no new model fitting, training,
or tuning**. Answer: do the candidate representations (R0/R1/R2) actually improve over the frozen baseline
(no-signal) when compared under identical data/splits/metrics/statistics, with a properly *paired* statistical
test where the same test-set examples support pairing?

## 2. Protocol version

`1.0` — unchanged. Representation matrix (`configs/phase3_2_rd_representation_matrix.json`) — unchanged,
reused as-is.

## 3. Exact baseline definition

**Baseline A (no-signal)**, frozen in Phase 3.1-RD: a fixed constant score (Alibaba: train-split empirical
failure prevalence; AIOps: overall 226-window pool prevalence). This is the **only** baseline that exists
uniformly across the real-data track.

**Documented departure from the original Phase 3.4's baseline choice**: the original synthetic Phase 3.4
treated *calibrated confidence* (Baseline B) as the strongest existing reference and asked whether the
selected candidate beat *that*. No analogue of calibrated confidence exists anywhere in the real-data track
— established in `docs/PHASE3_REAL_DATA_3_1_REPORT.md` §15 ("no dataset has a pre-existing upstream classifier
whose confidence output could be measured") and unchanged since. Baseline A is therefore the necessary and
only frozen baseline Phase 3.4-RD can compare against; this is a structural fact about the available real
data, not a choice made for convenience. Full pre-registration:
`configs/phase3_4_rd_comparison_matrix.json`.

## 4. Exact candidate definitions

R0 (raw/scaled), R1 (log1p-transformed), R2 (PCA(2)-reduced) — identical, unmodified, frozen in Phase
3.2-RD (`configs/phase3_2_rd_representation_matrix.json`). No fourth candidate was added; none was dropped.

## 5. Pre-registered comparison matrix

Written to `configs/phase3_4_rd_comparison_matrix.json` before any Phase 3.4-RD computation was run. Fixes:
exact baseline (§3), exact candidates (§4), exact datasets/splits (Alibaba random + temporal, AIOps LOEO;
AgentRx `NOT_EVALUABLE`), and the statistical unit for each (job / entity / not applicable).

## 6. Integrity checks

| Check | Result |
|---|---|
| Protocol unchanged | `protocol_version` re-read as `1.0` |
| Phase 3.1-RD results unchanged | Alibaba random Candidate F AUROC re-read: `0.7348398689698409` (matches); AIOps Candidate F AUROC: `0.6455824250651649` (matches) |
| Phase 3.2-RD results unchanged | Alibaba temporal R2 AUROC: `0.39450623763274134` (matches); AIOps R0 AUROC: `0.6455824250651649` (matches) |
| Phase 3.3-RD results unchanged | Distribution-shift artifact `n_train`/`n_test`: `6177`/`2499` (matches) |
| Original Phase 3 unchanged | `experiments/results/phase3_1/aggregate_results.json` mtime/content unchanged from before this phase |
| Phase 4 unchanged | `experiments/results/phase4_0/episodes.json` mtime/content unchanged |
| Raw data unchanged | No `data/raw/` file opened by any Phase 3.4-RD script |
| Splits unchanged | Random 6,999/1,498/1,503; temporal 6,177/1,324/2,499 — identical |
| Sample populations unchanged | AIOps 81 positive / 145 negative / 43 entities; AgentRx 44/29 annotated, 0 with zero failures — identical |
| All matrix candidates evaluated/reported | R0, R1, R2, and Baseline A all reported for every applicable dataset/split (§10–12) |
| No test-set tuning | No hyperparameter, threshold, or candidate selection decision was made using any Phase 3.4-RD test result |
| Correct independent-unit inference | Job-level paired bootstrap (Alibaba); entity-level paired cluster bootstrap (AIOps) |

**One process error occurred and is disclosed in full, not minimized**: while investigating a score-verification
discrepancy (§Implementation issues), the standalone script `scripts/real_data/phase3_1_rd_alibaba_evaluate.py`
was re-run directly, which overwrote `experiments/results/phase3_real_data/phase3_1/alibaba_results.json` —
a file this authorization explicitly required to remain unmodified. **The rewritten file's content was
verified field-by-field against the values already on record in this conversation and in
`docs/PHASE3_REAL_DATA_3_1_REPORT.md`, and matched bit-for-bit in every field.** No actual change occurred to
the frozen Phase 3.1-RD result; only the file's modification timestamp changed. This should not have happened
regardless of the outcome being harmless, and is reported here rather than silently passed over.

No other integrity check failed.

## 7. Dataset/sample information

Identical to Phase 3.1-RD/3.2-RD/3.3-RD throughout: Alibaba main tier 10,000 jobs (random split
6,999/1,498/1,503; temporal split 6,177/1,324/2,499); AIOps 226 windows / 43 entities; AgentRx 44 (Magentic)
+ 29 (τ-Retail) annotated trajectories, `NOT_EVALUABLE`.

## 8. Independent units

Job (Alibaba, paired bootstrap over test-set rows), entity (AIOps, paired cluster bootstrap over the 43
entities), not applicable (AgentRx).

## 9. Leakage exclusions

Unchanged: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded; `pai_group_tag_table`/
`pai_machine_spec` remain unavailable in processed form and are not used; feature availability is identical
between baseline and every candidate (all four share the exact same input feature columns, differing only in
representation transform) — no "STOP" condition (feature availability differing between baseline and
candidate) was triggered, because it never arose.

## 10. Alibaba random-split results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.735 | 0.537 | +0.235 | [0.203, 0.266] |
| R1 (log1p) | 0.736 | 0.508 | +0.236 | [0.205, 0.267] |
| R2 (PCA(2)) | 0.720 | 0.491 | +0.220 | [0.188, 0.251] |

All three candidates clearly and significantly beat Baseline A (every paired-difference CI excludes 0, all
positive). R0/R1/R2 are close to each other; no candidate's CI over the other two's point estimates suggests
a clearly superior choice on this split — consistent with Phase 3.2-RD's original "robust to representation on
the random split" finding, now confirmed with a proper paired test rather than an overlapping-CI heuristic.

## 11. Alibaba temporal-split results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.793 | 0.635 | +0.293 | [0.274, 0.312] |
| R1 (log1p) | 0.843 | 0.735 | +0.343 | [0.326, 0.361] |
| R2 (PCA(2)) | 0.395 | 0.355 | **−0.105** | **[−0.129, −0.082]** |

R0 and R1 both clearly and significantly beat Baseline A. **R2 is significantly WORSE than doing nothing** —
its paired-difference CI is entirely negative and excludes 0, which is a materially stronger and more
rigorous statement than the earlier, unpaired observation that R2's point estimate merely fell below 0.5:
this paired test directly establishes that R2 costs, not just fails to help, relative to the no-signal
baseline on this exact test set. Reported prominently, exactly as required.

## 12. AIOps results

| Candidate | AUROC | AUPRC | Paired ΔAUROC vs. Baseline A | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | — | — | — |
| R0 (raw/scaled) | 0.647 | 0.573 | +0.146 | [0.036, 0.260] |
| R1 (log1p) | 0.631 | 0.573 | +0.130 | [0.006, 0.249] |
| R2 (PCA(2)) | 0.604 | 0.516 | +0.105 | **[−0.023, 0.228]** |

**EXPLORATORY, unchanged classification.** R0 and R1's paired-difference CIs exclude 0 (R1 only barely, lower
bound 0.006), providing some evidence both beat no-signal. **R2's paired-difference CI includes 0**
([−0.023, 0.228]) — under this more rigorous paired entity-cluster test, R2's apparent improvement over
Baseline A on AIOps is **not statistically distinguishable from no effect**. This is a materially more
cautious conclusion than the unpaired Phase 3.2-RD framing ("all similar, wide overlapping CIs") — the paired
design sharpens the AIOps R2 finding specifically into an explicit non-result, reported as such.

## 13. AgentRx status

**NOT EVALUABLE.** Both frozen samples (44 Magentic, 29 τ-Retail annotated trajectories) contain zero
trajectories with `num_failures = 0` — reconfirmed unchanged this phase. No unannotated trajectory was added;
the two domains were not pooled; no comparison was attempted.

## 14. Baseline-vs-candidate comparison (consolidated table)

| Dataset | Split | Baseline | Candidate | AUROC | 95% CI (paired Δ) | Interpretation |
|---|---|---|---|---|---|---|
| Alibaba | random | A (0.500) | R0 | 0.735 | +0.235 [0.203,0.266] | Clear, significant improvement |
| Alibaba | random | A (0.500) | R1 | 0.736 | +0.236 [0.205,0.267] | Clear, significant improvement |
| Alibaba | random | A (0.500) | R2 | 0.720 | +0.220 [0.188,0.251] | Clear, significant improvement |
| Alibaba | temporal | A (0.500) | R0 | 0.793 | +0.293 [0.274,0.312] | Clear, significant improvement |
| Alibaba | temporal | A (0.500) | R1 | 0.843 | +0.343 [0.326,0.361] | Clear, significant improvement (largest of any row) |
| Alibaba | temporal | A (0.500) | R2 | 0.395 | **−0.105 [−0.129,−0.082]** | **Clear, significant HARM** — worse than doing nothing |
| AIOps | LOEO (exploratory) | A (0.500) | R0 | 0.647 | +0.146 [0.036,0.260] | Improvement, exploratory precision |
| AIOps | LOEO (exploratory) | A (0.500) | R1 | 0.631 | +0.130 [0.006,0.249] | Improvement, exploratory precision (borderline) |
| AIOps | LOEO (exploratory) | A (0.500) | R2 | 0.604 | +0.105 [−0.023,0.228] | **Inconclusive** — CI includes 0 |
| AgentRx | — | — | — | — | — | NOT EVALUABLE |

No candidate was hidden; no row omitted regardless of outcome.

## 15. AUROC/AUPRC

Reported inline in §10–12. AUPRC point estimates track the same ordering as AUROC within each split/dataset,
with one exception already known from Phase 3.1-RD/3.2-RD: because Q4's positive prevalence (43.4%) sets
AUPRC's uninformative floor much higher than 0.5, R2's temporal AUPRC (0.355) sits **below** that floor
(0.434 disclosed in Phase 3.3-RD §11) — reconfirmed here, consistent with its negative paired AUROC effect.

## 16. Effect sizes

Reported as the paired mean difference in §10–12/§14 (not merely the difference of independently-computed
point estimates) — this is the methodologically stronger choice given the same test-set rows/entities
support every candidate.

## 17. 95% CIs

All from paired bootstrap (job-level for Alibaba, entity-cluster-level for AIOps), 2,000 resamples, seed 0,
95% percentile CI — reported alongside every effect size, never in isolation.

## 18. Statistical comparisons

The paired design (resampling the same test rows/entities jointly across baseline and candidate) is the
"appropriate paired comparison" called for when comparing correlated predictions on the same test examples —
it directly answers whether a *specific* candidate's improvement (or harm) over the baseline is distinguishable
from zero on *this* test set, which an unpaired CI-overlap heuristic (used in Phase 3.1-RD/3.2-RD/3.3-RD)
only approximates. No new statistical test was invented after seeing any result — the paired-bootstrap
design was fixed in §5's pre-registration, before any Phase 3.4-RD number was computed.

## 19. Positive findings

- On both Alibaba splits, R0 and R1 significantly and substantially beat the no-signal baseline, with tight,
  clearly-positive CIs.
- R1 achieves the single largest paired improvement of any row in this report (+0.343 AUROC on the temporal
  split) — reported factually, not as a general endorsement (see §"What this does NOT establish").
- AIOps R0 and R1 show paired evidence of improvement over no-signal even under the stricter entity-cluster
  paired test, though at exploratory precision.

## 20. Negative findings

- **R2 (PCA(2)) is significantly WORSE than the no-signal baseline on the Alibaba temporal split** — the
  paired test makes this a stronger, more direct statement than the earlier phases' framing. Reported
  prominently, as required.
- AIOps R2's apparent improvement over no-signal does not survive the paired entity-cluster test (CI includes
  0) — a genuine negative/non-finding for that specific candidate on that specific dataset, not hidden.

## 21. Inconclusive findings

- AIOps R1's paired CI [0.006, 0.249] barely excludes 0 — treated as weak, not strong, evidence; not upgraded
  to a confident claim merely because the interval technically excludes zero.
- Whether R1's temporal-split advantage over R0 (+0.050 AUROC, established in Phase 3.2-RD/3.3-RD) reflects a
  generally superior representation or a shift-specific artifact remains open — this phase adds a paired
  confirmation that the *baseline* comparison holds, but does not add a new R1-vs-R0 head-to-head paired test
  (that would be a different, new statistical comparison not specified in the pre-registered matrix, and is
  not performed here).

## 22. Distribution-shift interpretation

Per the authorization's explicit instruction: the Alibaba temporal test set carries ~43.4% failure prevalence
and the covariate shift already characterized in Phase 3.3-RD (reduced resource requests, GPU-type composition
shift toward MISC). Every temporal-split number in this report is a description of performance **on that
specific shifted population**, not a general statement about "temporal generalization ability" independent of
what that population looks like. R2's negative paired effect is interpreted in this light: it is a
demonstrated harm on this specific real, shifted evaluation population, not a claim about PCA(2)'s behavior
under distribution shift in general.

## 23. Comparison with Phase 3.1-RD

Phase 3.1-RD established Baseline A and Candidate F (=R0) with a single-representation, unpaired-CI
methodology. This phase reuses that baseline unmodified and adds a paired comparison that the original
Phase 3.1-RD design did not attempt (it had only one candidate to compare, so a baseline-vs-candidate pairing
was implicit in its bootstrap CI, not an explicit paired-difference statistic). No Phase 3.1-RD number changed.

## 24. Comparison with Phase 3.2-RD

Phase 3.2-RD established R0/R1/R2 and interpreted their relationship to Baseline A using independently-computed,
overlapping-CI comparisons (not paired). This phase's paired-difference results are consistent in direction
with every Phase 3.2-RD conclusion but are **more decisive** in two places: (a) Alibaba temporal R2's harm
relative to Baseline A is now a directly-tested, CI-excludes-zero finding rather than an inference from "R2's
point estimate is below 0.5"; (b) AIOps R2's improvement over Baseline A is now shown to be statistically
indistinguishable from zero under a paired test, sharpening Phase 3.2-RD's vaguer "overlapping CIs, inconclusive"
language into an explicit non-finding.

## 25. Comparison with Phase 3.3-RD

Phase 3.3-RD characterized the covariate shift underlying the Alibaba temporal split and offered hypotheses
for R1's improvement / R2's collapse, without re-testing the baseline comparison. This phase supplies that
missing baseline-paired test, confirming (not re-deriving differently) that R0 and R1 both significantly
beat no-signal under the shift while R2 does not merely underperform but actively harms relative to no-signal.

## 26. Comparison with original Phase 3.4

| Field | Content |
|---|---|
| **Original Phase 3.4 result** | Consolidated ranking B > F > E/E′ > D > C > A; F "does not consistently outperform calibrated confidence" (1/6 seeds, paired CI entirely negative); complementarity with B explicitly **not established**; overall verdict **🟡 INCONCLUSIVE**. |
| **Real-data result** | No calibrated-confidence baseline exists to test against (§3) — the real-data track cannot ask "does the candidate beat the strongest reference" in the original's sense, only "does it beat no-signal," which every candidate except AIOps-R2 answers affirmatively, and Alibaba-temporal-R2 answers with a significant **negative** result. |
| **Direction of agreement/disagreement** | **Not directly comparable** for the "beats the strongest baseline" question (no real-data analogue of B exists). Where a comparison IS possible (beats no-signal), the real-data finding is **stronger** than the original's: the original's candidate F beat no-signal 6/6 seeds with CI excluding 0; the real-data candidates mostly replicate that "clearly beats no-signal" pattern, but ALSO surface a failure mode (R2's significant harm) that the original single-representation design never had occasion to discover, since it only ever tested one representation per candidate mechanism. |
| **Confidence/uncertainty** | Alibaba: tight paired CIs, confirmatory-capable. AIOps: wider paired CIs, exploratory, and this phase specifically demonstrates R2's AIOps improvement does not survive the stricter paired test. |
| **Dataset limitations** | Same as prior phases — narrower Alibaba feature set, platform-telemetry-only AIOps features, no AgentRx comparison possible. |
| **Interpretation** | This phase **extends** rather than replicates or contradicts the original Phase 3.4: it answers the "beats baseline" half of the original's question (which real data supports strongly, with one significant exception) while being structurally unable to answer the "beats the strongest reference" half (no such reference exists in real data). The original's caution — that a candidate beating no-signal is not the same as a candidate being ready for deployment — is echoed here even more starkly by R2's Alibaba-temporal result: a candidate can beat no-signal on one population (random split) and be significantly *worse* than no-signal on another (temporal split), a distinction the original synthetic Phase 3.4, evaluated on one fixed benchmark condition, could not have surfaced. |

## 27. Limitations

- No calibrated-confidence-equivalent baseline exists for any real dataset, so the "strongest reference"
  question the original Phase 3.4 answered cannot be asked here at all (§26).
- The paired bootstrap tests one candidate against Baseline A at a time; no paired R0-vs-R1 or R0-vs-R2
  head-to-head test was run (not part of the pre-registered comparison matrix — see §21).
- AIOps's paired test, while more rigorous than Phase 3.2-RD's unpaired framing, still operates on only 43
  independent entities — the R1 result in particular sits close to the CI boundary and should not be treated
  as strong evidence in either direction.
- AgentRx contributes nothing to this phase.

## 28. Implementation issues

- **Solver-level floating-point non-determinism, discovered and characterized in this phase**: re-fitting the
  identical `LogisticRegression` (fixed `random_state=42`, identical input data) in a different process/
  invocation context reproduces the frozen AUROC to within a small but non-zero tolerance, not bit-for-bit.
  Isolated and confirmed **not a logic bug**: the relevant pipeline-construction functions across
  `phase3_1_rd_alibaba_evaluate.py`/`phase3_2_rd_alibaba_evaluate.py` (and the AIOps equivalents) were
  verified to produce byte-identical scores and coefficients (max absolute difference `0.0`) when fit on the
  same data within a single process. The remaining cross-invocation drift (~7e-5 AUROC for Alibaba's single
  fit per split; ~1.1e-3 for AIOps's 43-fit LOEO, where small per-fit drift has more opportunities to
  accumulate) is consistent with floating-point non-associativity in the BLAS/LAPACK routines the `lbfgs`
  solver calls, sensitive to how much other computation ran earlier in the same process. This revises, without
  rewriting, a claim made in the Phase 3.1-RD/3.2-RD reports that results "reproduce bit-for-bit" — that claim
  should be read as "reproduce to within ~1e-3 solver tolerance," which is what was actually verified here.
  The magnitude in every case is one to three orders of magnitude smaller than any effect size this research
  program reports (≥0.02) and changes no qualitative conclusion in any prior phase.
- **A process error**: `scripts/real_data/phase3_1_rd_alibaba_evaluate.py` was run directly during the
  investigation of the above, overwriting the Phase 3.1-RD Alibaba result file. Content was verified
  unchanged (§6). Going forward, no Phase 3.1-RD/3.2-RD/3.3-RD script is re-run directly under this or any
  future phase; verification against frozen results is performed by loading their JSON output only or, where
  score-level recomputation is genuinely needed (as here), by writing to a new phase-specific output path.

## 29. Reproducibility information

- New scripts: `scripts/real_data/phase3_4_rd_alibaba_compare.py`, `scripts/real_data/phase3_4_rd_aiops_compare.py`.
  Both re-derive scores deterministically (fixed seeds throughout) and verify against the frozen Phase
  3.1-RD/3.2-RD result files within the disclosed, justified tolerances (§28) before computing any new
  statistic; both raise `ProtocolDiscrepancyError` and halt on any mismatch beyond tolerance.
- Result artifacts: `experiments/results/phase3_real_data/phase3_4/{alibaba_results.json,aiops_results.json}`,
  each recording the comparison-matrix source, verification mismatches (if any, within tolerance), and full
  bootstrap configuration.
- Provenance preserved: identical processed-data sources, split-membership files, and representation
  definitions as every prior phase; no field stripped or renamed.

---

## What this report does NOT establish

- That R1 is "the best" representation in any general sense — it shows the largest improvement on the
  Alibaba temporal split specifically, under that split's specific distribution shift; no claim is made about
  its performance under any other, untested shift.
- That R2 is unusable in general — it performs comparably to R0/R1 on the Alibaba random split; its failure
  is specific to the temporal (shifted) evaluation.
- Any complementarity or ensembling result — not tested, exactly as the original Phase 3.4 also declined to
  test this (docs/PHASE3_4_COMPARISON.md §12/§18).
- Real-world deployment readiness for any candidate — ranking-quality metrics under a paired statistical test
  are not a substitute for a deployment-context cost/threshold analysis (not run in this phase).

## Files created by this execution

- `configs/phase3_4_rd_comparison_matrix.json`
- `scripts/real_data/phase3_4_rd_alibaba_compare.py`
- `scripts/real_data/phase3_4_rd_aiops_compare.py`
- `experiments/results/phase3_real_data/phase3_4/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_4/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_4_REPORT.md` (this document)
- `docs/PHASE3_REAL_DATA_COMPARISON.md` (updated by addition only — new H2-extension/H1-consolidation notes; see that file's Phase 3.4-RD section)

No file outside `configs/`, `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_4/`, and these
two `docs/` files was modified, with the single disclosed exception in §6/§28 (content-verified unchanged).

---

## STOP — Phase 3.4-RD complete

No later phase (3.5-RD, 3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.
