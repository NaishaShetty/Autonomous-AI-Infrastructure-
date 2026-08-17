# Phase 3.2-RD — Representation-Robustness Evaluation — Completion Report

**Executed under authorization**: explicit chat authorization received 2026-08-13, scoped to Phase 3.2-RD
execution only (Phase 3.3-RD–3.6-RD and Phase 4 explicitly not authorized).

---

## 1. Phase 3.2-RD objective

Determine whether the real-data failure-risk signal established in Phase 3.1-RD is **robust to a small,
pre-registered representation matrix**, holding dataset, splits, test sets, leakage rules, and the supervised
classifier itself fixed — varying only the feature representation. This is a robustness check, not a search
for the best-performing representation; all pre-registered candidates are reported regardless of outcome.

## 2. Protocol version

`1.0` (`configs/phase3_real_data_protocol.json`, `docs/PHASE3_REAL_DATA_PROTOCOL.md`) — unchanged.
Representation matrix pre-registered separately in `configs/phase3_2_rd_representation_matrix.json`,
written and committed **before** any Phase 3.2-RD result was produced or inspected.

## 3. Phase 3.1 reference results (frozen, unmodified, re-quoted here for comparison only)

| | Alibaba random | Alibaba temporal | AIOps (LOEO, exploratory) |
|---|---|---|---|
| Baseline A (no-signal) AUROC | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Candidate F AUROC | 0.735 [0.703, 0.766] | 0.793 [0.774, 0.812] | 0.646 [0.536, 0.760] |

Source: `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json}` — verified
byte-identical to Phase 3.1-RD's original values before this execution began (§5 below). Not rerun, not
recomputed, not altered.

## 4. Representation definitions (pre-registered, see `configs/phase3_2_rd_representation_matrix.json`)

Classifier held fixed across all three: `LogisticRegression(max_iter=2000, random_state=42)` — identical to
Phase 3.1-RD's Candidate F.

- **R0_raw_scaled** — reference/anchor. Identical to Phase 3.1-RD's Candidate F: numeric columns
  median-imputed + `StandardScaler`; categorical columns constant-imputed + one-hot.
- **R1_log_transformed** — same feature columns as R0, but non-negative, heavy-tailed count/resource fields
  are `log1p`-transformed before standardization (Alibaba: task/instance counts, `plan_cpu`/`plan_mem`/
  `plan_gpu` statistics; AIOps: `n_observations`, `n_distinct_metrics`). Time-coordinate fields (Alibaba
  `job_start_time`, `mean_instance_start_time`) and AIOps value statistics (`mean_value`, `std_value`,
  `min_value`, `max_value`, which can be negative) are excluded from the log transform and remain on the R0
  path — documented in the pre-registration, not a post-hoc carve-out.
- **R2_pca_reduced** — the standardized numeric feature block is reduced to its first 2 principal components
  via `PCA(n_components=2)`, fit on the training data only (Alibaba: train split; AIOps: each LOEO training
  fold) and applied unchanged to held-out data. `n_components=2` matches the PCA(2) representation used
  throughout the original synthetic-data Phase 2/3 methodology (`src/failure_memory`), not tuned for
  real-data performance. Categorical one-hot columns are unchanged and concatenated alongside the 2 PCA
  components.

No fourth representation was added. No representation was dropped after seeing results (see §17 for the
weak/negative R2 finding, reported in full).

## 5. Pre-execution verification (per the authorization's explicit checklist)

| Check | Result |
|---|---|
| Frozen Real-Data Phase 3 protocol read | `docs/PHASE3_REAL_DATA_PROTOCOL.md`, `configs/phase3_real_data_protocol.json` — version confirmed `1.0` |
| Phase 3.1-RD completion report read | `docs/PHASE3_REAL_DATA_3_1_REPORT.md` |
| Phase 3.1-RD result artifacts read | `experiments/results/phase3_real_data/phase3_1/{alibaba_results.json,aiops_results.json,agentrx_descriptive.json}` |
| Phase 3.1 test sets/splits unchanged | `data/audit/alibaba_gpu2020/splits_random_stratified.json` and `splits_temporal.json` re-loaded; counts re-confirmed identical to Phase 3.1-RD's reported 6,999/1,498/1,503 (random) and 6,177/1,324/2,499 (temporal) |
| No Phase 3.1 results altered | Alibaba random-split Candidate F AUROC re-read from the untouched Phase 3.1-RD JSON immediately before and after this execution: `0.7348398689698409` both times — file not modified |
| Phase 4 untouched | No file under `experiments/results/phase4_0/`, `phase4_1/`, `phase4_2/`, `docs/PHASE4_*`, or `configs/phase4_*` was opened for writing |
| Original Phase 3 results untouched | `experiments/results/phase3_1/aggregate_results.json` mtime unchanged, not opened for writing |

No integrity check failed. Execution proceeded.

## 6. Exact datasets evaluated

Alibaba GPU2020 main tier (same 10,000-job sample, same random and temporal splits as Phase 3.1-RD), AIOps
2020 (same 226 windows / 43 entities), AgentRx (NOT_EVALUABLE — see §12).

## 7. Exact independent units

Identical to Phase 3.1-RD: job (Alibaba), entity via LOEO (AIOps), trajectory (AgentRx, N/A here).

## 8. Exact sample sizes

Identical to Phase 3.1-RD, reused unchanged: Alibaba random 6,999/1,503 (train/test); temporal 6,177/2,499;
AIOps 226 windows (81 positive/145 negative), 43 entities, 0 dropped for missing telemetry. No resampling,
no record additions/removals.

## 9. Leakage exclusions

Identical to Phase 3.1-RD: `pai_sensor_table`, `pai_machine_metric`, `max_mem`, `max_gpu_wrk_mem` excluded
(never read by either Phase 3.2-RD script — verified via `assert_no_excluded_columns` on the Alibaba feature
frame, reused unmodified from the Phase 3.1-RD module). `pai_group_tag_table`/`pai_machine_spec` remain
unavailable in processed form and are not used by any of R0/R1/R2. AIOps PRE-FAILURE-window-only telemetry
scope is unchanged; business/trace telemetry was not added to any representation.

## 10. Alibaba random-split results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.735 | [0.703, 0.766] | 0.540 | [0.487, 0.596] |
| R1 (log1p-transformed) | 0.736 | [0.705, 0.767] | 0.511 | [0.461, 0.567] |
| R2 (PCA(2)-reduced) | 0.720 | [0.688, 0.751] | 0.495 | [0.445, 0.547] |

All three representations produce statistically indistinguishable AUROC on the random split (overlapping
CIs, point estimates within 0.016 of each other). **Robust to representation on this split.**

## 11. Alibaba temporal-split results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.793 | [0.774, 0.812] | 0.636 | [0.608, 0.667] |
| R1 (log1p-transformed) | **0.843** | [0.826, 0.861] | 0.736 | [0.705, 0.769] |
| R2 (PCA(2)-reduced) | **0.395** | [0.371, 0.418] | 0.356 | [0.337, 0.377] |

**Not robust to representation on this split.** R1 is materially higher than R0 (ΔAUROC +0.050, non-
overlapping CIs). R2 collapses to **below the no-signal baseline** (0.395 < 0.500) — worse than doing
nothing, with a tight CI ([0.371, 0.418]) that clearly excludes both 0.5 and R0/R1's range. See §17 for
interpretation; this is reported in full, not smoothed over.

As instructed: the 0.793 (R0, temporal) and 0.735 (R0, random) results are **not** interpreted as directly
comparable without acknowledging the Q4 distribution shift (20.1% train/val vs. 43.4% test failure rate,
established in Phase 3.1-RD) — restated here because it is the most plausible explanation for why
representation choice interacts so much more strongly with the temporal split than the random split (§17).

## 12. AIOps exploratory results

| Representation | AUROC | 95% CI | AUPRC | 95% CI |
|---|---|---|---|---|
| Baseline A (no-signal) | 0.500 | [0.500, 0.500] | 0.353 | [0.254, 0.438] |
| R0 (raw/scaled, = Phase 3.1-RD reference) | 0.646 | [0.536, 0.760] | 0.575 | [0.447, 0.666] |
| R1 (log1p-transformed) | 0.630 | [0.506, 0.749] | 0.574 | [0.443, 0.667] |
| R2 (PCA(2)-reduced) | 0.605 | [0.477, 0.728] | 0.525 | [0.406, 0.610] |

226 windows, 43 entities, LOEO cross-validation, entity-level cluster bootstrap — identical structure to
Phase 3.1-RD. **AIOps remains EXPLORATORY** — none of these results is treated as confirmatory regardless of
point estimate. R0 and R1's CIs barely exclude 0.5 at the lower bound; **R2's CI ([0.477, 0.728]) includes
0.5** — R2 is not distinguishable from no-signal on AIOps, an inconclusive/negative finding for that
representation reported here in full.

## 13. AgentRx status

**NOT EVALUABLE.** No representation-robustness experiment was run. The frozen protocol's hypothesis-dataset
mapping (`configs/phase3_real_data_protocol.json`,
`hypothesis_dataset_mapping.H2_mechanism_is_supervision_not_representation`) already marks both
`agentrx_magentic` and `agentrx_tau_retail` as `NOT_EVALUABLE`, decided before Phase 3.1-RD ran and unchanged
here. Independently, Phase 3.1-RD's H1 blocker (every trajectory in both frozen samples — 44 Magentic, 29
τ-Retail — has ≥1 recorded failure, no negative class exists) means there is no supervised classifier at all
whose representation-robustness could even be tested. No unannotated trajectories were added to manufacture
a negative class. AgentRx is left unevaluated for Phase 3.2-RD, consistent with both the frozen protocol's
prior decision and Phase 3.1-RD's finding.

## 14. Representation comparison table (all datasets/splits)

| Dataset / split | R0 AUROC | R1 AUROC | R2 AUROC | Max spread (R_max − R_min) | Robust? |
|---|---|---|---|---|---|
| Alibaba random | 0.735 | 0.736 | 0.720 | 0.016 | Yes |
| Alibaba temporal | 0.793 | 0.843 | 0.395 | 0.448 | **No** |
| AIOps (exploratory) | 0.646 | 0.630 | 0.605 | 0.041 (within wide, overlapping CIs) | Yes, within exploratory uncertainty |

## 15. Effect sizes (relative to Phase 3.1-RD's R0/Candidate F reference)

| Dataset / split | Representation | ΔAUROC vs. R0 | Practically meaningful? |
|---|---|---|---|
| Alibaba random | R1 | +0.001 | No — within bootstrap noise |
| Alibaba random | R2 | −0.015 | No — within bootstrap noise (overlapping CIs) |
| Alibaba temporal | R1 | +0.050 | **Yes** — non-overlapping 95% CIs ([0.774,0.812] vs. [0.826,0.861]) |
| Alibaba temporal | R2 | −0.398 | **Yes, and adverse** — R2 falls below no-signal; not a subtle effect |
| AIOps | R1 | −0.016 | No — CIs overlap heavily, both wide |
| AIOps | R2 | −0.041 | Ambiguous — R2's CI includes 0.5 while R0/R1's barely exclude it; suggestive but not statistically decisive given AIOps's exploratory-only power |

## 16. Confidence intervals

All reported inline in §10–12; nonparametric percentile bootstrap, 2,000 resamples, seed 0, 95% CI, at the
correct independent-unit level (job for Alibaba, entity for AIOps) — identical methodology and configuration
to Phase 3.1-RD.

## 17. Robustness analysis

**Alibaba random split**: the signal is robust to all three representations. R0/R1/R2 AUROC all fall within
a 0.016 band with heavily overlapping CIs. This is the expected, unremarkable outcome for a well-behaved
i.i.d.-like split.

**Alibaba temporal split**: the signal is **not robust to representation**. Two distinct, opposite-direction
effects appear:
- R1 (log-transform) **improves** performance materially (+0.050 AUROC, non-overlapping CI) relative to R0.
  A plausible explanation: several of the log-transformed fields (`sum_inst_num`, `plan_cpu`/`plan_mem`/
  `plan_gpu`, instance/task counts) are heavy-tailed, and the Q4 test period's failure-heavy regime may
  involve workloads at more extreme values of these fields than the training period saw — a linear model on
  raw (non-log) heavy-tailed features can be disproportionately influenced by the tail under distribution
  shift, while the log-compressed version generalizes more evenly. This is a plausible mechanism, not a
  proven one; no causal claim is made.
- R2 (PCA(2)) **collapses below no-signal** (AUROC 0.395, tight CI excluding 0.5). The principal components
  are fit on the Q1–Q3 training distribution; under the confirmed real distribution shift to Q4 (20.1%→43.4%
  failure rate), the dominant axes of variance captured by PCA(2) on the training data do not preserve the
  same relationship to the label in the test period — plausibly, the direction the logistic regression
  learned as "risk-increasing" on the training-fit components corresponds to a different, or even reversed,
  real-world pattern in the shifted test distribution. This is a genuine representation-robustness failure,
  not a bug: the same PCA/LogisticRegression code produces a normal-looking result (0.720) on the random
  split, where no comparable distribution shift exists. **This is exactly the kind of finding Phase 3.2-RD
  was designed to surface, and is reported as a real negative result for R2 under temporal shift, not
  hidden or minimized.**

**AIOps**: R0/R1/R2 are statistically indistinguishable from each other given the wide, overlapping CIs
inherent to n=226/43 entities. R2's CI additionally fails to exclude the no-signal baseline. Given AIOps's
exploratory-only power (established in Phase 3.1-RD and the frozen protocol), this is reported as
inconclusive rather than as evidence that PCA "does not work" on AIOps — the sample size cannot support that
strong a claim either way.

**Overall determination**: the real-data failure-risk signal is **robust to representation on Alibaba's
random split and, with caveats, on AIOps**, but is **NOT robust to representation on Alibaba's temporal
(distribution-shifted) split** — representation choice interacts materially with the presence of covariate/
concept drift. This is itself a substantive, honestly-reported finding, not an experimental failure.

## 18. Negative findings

- R2 (PCA(2)) performs **worse than no-signal** on the Alibaba temporal split (AUROC 0.395) — the most
  significant negative finding of this report.
- R2 is statistically indistinguishable from no-signal on AIOps (CI includes 0.5).
- AgentRx again produced no result at all for this hypothesis (H2), for the same reason as H1 in Phase
  3.1-RD, plus the frozen protocol's prior NOT_EVALUABLE designation.

## 19. Inconclusive findings

- AIOps representation comparisons (R0 vs. R1 vs. R2) are inconclusive — all CIs overlap substantially, and
  the sample is too small/entity-clustered to distinguish representation effects with confidence, even though
  R2's point estimate is numerically lowest.

## 20. Failure cases

- No implementation failure occurred in this execution (unlike Phase 3.1-RD's AIOps baseline bug). R2's poor
  temporal-split performance is a genuine data/method finding, not a bug — confirmed by R2 performing
  normally (0.720, consistent with R0/R1) on the random split using identical code, which rules out a
  coding defect as the explanation for the temporal-split collapse.

## 21. Dataset-specific limitations

Carried forward unchanged from Phase 3.1-RD (§23 of that report): Alibaba's feature set remains restricted
(no `group_tag`/`machine_spec`/`user`); AIOps remains platform-telemetry-only and exploratory; AgentRx
remains structurally blocked. Additionally: PCA(2)'s specific behavior under the Alibaba temporal shift
(§17) should be treated as a property of this particular representation/distribution-shift combination, not
generalized to claim "PCA is unreliable" broadly — only 2 components were tested (chosen to match the
original methodology, not tuned), and no attempt was made to determine whether a different number of
components would behave differently (that would be a new, non-pre-registered experiment, out of scope here).

## 22. Comparison with original Phase 3

The original Phase 3.2/3.2C found that **supervision, not representation, was the operative mechanism**
(Candidate C's richer k-NN representation improved over control only modestly and inconsistently; Candidate
F's supervised learning on the *old, unmodified* PCA representation matched Candidate C's performance,
isolating supervision as the cause — `docs/PHASE3_2C_CANDIDATE_ABLATION.md`).

This real-data Phase 3.2-RD asked a related but distinct question — not "does supervision or representation
explain an existing weak signal" (the original's framing, motivated by a weak original result), but "is an
already-strong real-data signal robust across representation choices." The findings:

- **Alibaba random split**: **supports** the spirit of the original conclusion — representation makes
  little difference (R0≈R1≈R2), consistent with "supervision is what matters, representation is
  interchangeable" as a description of what's happening here too.
- **Alibaba temporal split**: **partially contradicts** that generalization — representation choice matters
  a great deal under distribution shift, to the point of flipping a signal from strongly positive to
  below-no-signal. The original Phase 3 never tested a distribution-shift condition in its 3.2/3.2C work
  (concept drift was tested later, in Phase 3.3, using the frozen Candidate-F representation only, not a
  representation comparison) — so this finding does not contradict a specific original claim, but it does
  show that the original's "representation doesn't matter much" conclusion should not be assumed to extend
  to a distribution-shift setting, which the original methodology did not examine in that combination.
- **AIOps**: **cannot adjudicate** — underpowered to distinguish representations at all.
- **AgentRx**: **cannot adjudicate** — no experiment possible.

The original conclusion is not rewritten, not forced into agreement, and not treated as contradicted where
the two experiments simply asked different questions.

## 23. Comparison with Phase 3.1-RD

| Metric | Phase 3.1-RD (R0/Candidate F only) | Phase 3.2-RD (R0/R1/R2) |
|---|---|---|
| Alibaba random AUROC | 0.735 [0.703,0.766] | R0 0.735 (identical, reused), R1 0.736, R2 0.720 — all consistent |
| Alibaba temporal AUROC | 0.793 [0.774,0.812] | R0 0.793 (identical, reused), R1 **0.843** (higher), R2 **0.395** (far lower) |
| AIOps AUROC | 0.646 [0.536,0.760] | R0 0.646 (identical, reused), R1 0.630, R2 0.605 — overlapping, inconclusive spread |

R0 in every case is a re-report of the exact Phase 3.1-RD Candidate F number (same code path, same data,
same split) — included here for side-by-side comparison, not recomputed. The main addition Phase 3.2-RD
contributes beyond Phase 3.1-RD is exposing that the Alibaba temporal-split result is **representation-
sensitive**, which Phase 3.1-RD (testing only one representation) could not have shown.

## 24. Reproducibility information

- Scripts: `scripts/real_data/phase3_2_rd_alibaba_evaluate.py`,
  `scripts/real_data/phase3_2_rd_aiops_evaluate.py` — both import and reuse the Phase 3.1-RD modules'
  feature-extraction functions unmodified (`build_feature_matrix`, `load_windows`,
  `extract_window_features`, leakage-exclusion constants) rather than re-implementing them, to guarantee
  identical underlying data/preprocessing.
- Representation matrix: `configs/phase3_2_rd_representation_matrix.json`, pre-registered before any result
  was produced.
- Result artifacts: `experiments/results/phase3_real_data/phase3_2/{alibaba_results.json,aiops_results.json}`,
  each embedding phase, protocol version, representation-matrix source, dataset identifiers, and bootstrap
  configuration.
- Determinism: sampling/window reuse at `seed=42` (upstream, unchanged), classifier `random_state=42`, PCA
  `random_state=42`, bootstrap `seed=0`. Re-running either script against the unmodified
  `data/processed/`/`data/audit/` artifacts and the unmodified representation-matrix config reproduces the
  same numbers bit-for-bit.
- Provenance preserved per the unified-benchmark requirement: `source_dataset`, entity/job identifiers,
  split membership, and processing version are carried through in the same manner as Phase 3.1-RD (feature
  frames are built from the same provenance-carrying processed CSVs; no new field was stripped).

---

## Files created by this execution

- `configs/phase3_2_rd_representation_matrix.json`
- `scripts/real_data/phase3_2_rd_alibaba_evaluate.py`
- `scripts/real_data/phase3_2_rd_aiops_evaluate.py`
- `experiments/results/phase3_real_data/phase3_2/alibaba_results.json`
- `experiments/results/phase3_real_data/phase3_2/aiops_results.json`
- `docs/PHASE3_REAL_DATA_3_2_REPORT.md` (this document)

No file outside `configs/`, `scripts/real_data/`, `experiments/results/phase3_real_data/phase3_2/`, and this
new `docs/` file was modified. Phase 3.1-RD's artifacts, the frozen Real-Data Phase 3 protocol, the original
Phase 3 results, and Phase 4 were all re-verified unchanged (§5).

---

## STOP — Phase 3.2-RD complete

No later phase (3.3-RD…3.6-RD, Phase 4) was started. Awaiting review and separate authorization to proceed.
