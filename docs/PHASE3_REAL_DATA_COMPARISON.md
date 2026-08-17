# Phase 3 Real-Data Comparison — Original vs. Real-Data Findings

**Scope of this document**: only hypotheses with a result actually produced by executed real-data work are
recorded here. As of this update, that is **Phase 3.1-RD and Phase 3.2-RD**
(`docs/PHASE3_REAL_DATA_3_1_REPORT.md`, `docs/PHASE3_REAL_DATA_3_2_REPORT.md`, both 2026-08-13). H3–H7 have
no real-data result yet (Phase 3.3-RD…3.6-RD are not authorized) and are listed as `NOT YET RUN`, not as
findings.

This document does not modify, reinterpret, or re-score `docs/PHASE3_4_COMPARISON.md` or any other original
(synthetic) Phase 3 file. Original results below are quoted verbatim from the frozen reports.

---

## H1 — a supervised failure-risk signal exists beyond calibrated confidence

| Field | Content |
|---|---|
| **Original Phase 3 result** | Candidate F (`Phase2RepresentationSupervisedRisk`, established in Phase 3.2C): aggregate AUROC **0.6548** [0.6159, 0.6938] on synthetic regimes 3+4, beating Baseline A (no-signal, 0.5000) at 6/6 seeds. (Source: `docs/PHASE3_2C_CANDIDATE_ABLATION.md`, `docs/PHASE3_4_COMPARISON.md`.) |
| **Real-data result — Alibaba, random split** | Candidate F AUROC **0.735** [0.703, 0.766] vs. Baseline A 0.500 [0.500, 0.500]. n=1,503 test jobs. |
| **Real-data result — Alibaba, temporal split** | Candidate F AUROC **0.793** [0.774, 0.812] vs. Baseline A 0.500 [0.500, 0.500]. n=2,499 test jobs (Q4, base rate 43.4% vs. 20.1% in train). |
| **Real-data result — AIOps** | Candidate F (LOEO) AUROC **0.646** [0.536, 0.760] vs. Baseline A 0.500 [0.500, 0.500]. n=226 windows / 43 entities. **EXPLORATORY.** |
| **Real-data result — AgentRx (Magentic, τ-Retail)** | **NOT EVALUABLE.** Every trajectory in both frozen samples (44 Magentic, 29 τ-Retail) has ≥1 recorded failure — no negative class exists to build a binary risk classifier against. |
| **Direction of agreement/disagreement** | **Agrees directionally** on Alibaba (both splits) and AIOps: a supervised model exceeds no-signal by a wide margin in every case a comparison could be made. **Cannot adjudicate** on AgentRx. |
| **Confidence/uncertainty** | Alibaba: tight CIs, confirmatory-capable precision (CI half-widths ≈0.02–0.03 AUROC). AIOps: wide CI (half-width ≈0.11), exploratory only. AgentRx: no estimate exists. |
| **Dataset limitations** | Alibaba result is built on a narrower feature set than fully allowed (no `group_tag`/`machine_spec`/`user` — §8 of the 3.1-RD report) and on a fundamentally different prediction target (direct job-outcome prediction, not meta-level "will an upstream classifier be wrong" prediction — see interpretation below). AIOps result rests on only 43 independent entities. AgentRx result does not exist. |
| **Interpretation** | The real-data evidence **strengthens** the qualitative claim that a supervised failure-risk signal exists and clearly exceeds a no-signal baseline — this direction holds on every real dataset where a comparison was possible. The *magnitude* is **not comparable** across original and real-data results: the original Phase 3.1 task (predicting an upstream classifier's own errors) and the Alibaba/AIOps real-data tasks (predicting a job's or a service's actual failure outcome) are different prediction problems with different intrinsic difficulty. A higher real-data AUROC is not evidence the original synthetic result was too conservative, and a lower one would not have been evidence it was too optimistic — the tasks simply are not the same task. AgentRx's inability to run at all is itself informative: it shows the original H1 framing (binary failure occurrence) does not transfer cleanly to a dataset where the sampling process (annotate-because-a-failure-was-observed) makes failure occurrence deterministic within the annotated set. |

---

## H2 — mechanism is supervision, not representation

| Field | Content |
|---|---|
| **Original Phase 3 result** | Phase 3.2/3.2C: supervision, not representation, was the operative mechanism. A fixed/unlearned rule on a richer k-NN representation showed ~no signal (AUROC 0.5073); supervised learning on the *old, unmodified* PCA representation matched the richer-representation candidate (0.6548 vs. 0.5809), isolating supervision as the cause (`docs/PHASE3_2C_CANDIDATE_ABLATION.md`). |
| **Real-data result — Alibaba, random split** | Robust to representation: R0 (raw/scaled) 0.735 [0.703,0.766], R1 (log1p) 0.736 [0.705,0.767], R2 (PCA(2)) 0.720 [0.688,0.751] — all statistically indistinguishable. |
| **Real-data result — Alibaba, temporal split** | **Not robust to representation**: R0 0.793 [0.774,0.812], R1 0.843 [0.826,0.861] (materially higher, non-overlapping CI), R2 **0.395 [0.371,0.418]** (collapses below no-signal). |
| **Real-data result — AIOps** | R0 0.646 [0.536,0.760], R1 0.630 [0.506,0.749], R2 0.605 [0.477,0.728] — overlapping CIs, inconclusive; R2's CI includes 0.5. **EXPLORATORY.** |
| **Real-data result — AgentRx (Magentic, τ-Retail)** | **NOT EVALUABLE** — the frozen protocol's hypothesis-dataset mapping already marked H2 as `NOT_EVALUABLE` for both domains before Phase 3.1-RD ran, and Phase 3.1-RD's H1 blocker (no negative class) independently rules out any supervised classifier to test representation-robustness of. |
| **Direction of agreement/disagreement** | **Partially agrees, partially cannot generalize**: on Alibaba's random split, representation choice indeed makes little difference — consistent with the original's "supervision, not representation, is what matters." On Alibaba's temporal (distribution-shifted) split, representation choice matters a great deal, to the point of inverting a strong signal into a below-no-signal one for PCA(2) — a combination (representation × distribution shift) the original Phase 3.2/3.2C work never tested, so this does not contradict a specific original claim but does show the original conclusion should not be assumed to extend to a shifted-distribution setting. AIOps and AgentRx **cannot adjudicate**. |
| **Confidence/uncertainty** | Alibaba: tight CIs on both splits (confirmatory-capable precision); the temporal-split R2 result is a tight CI around a genuinely adverse point estimate, not a noisy one. AIOps: wide, overlapping CIs, exploratory only. AgentRx: no estimate exists. |
| **Dataset limitations** | Same feature-completeness limitations as H1 (§9 of the 3.2-RD report). Only 3 pre-registered representations were tested; PCA was tested only at n_components=2 (matching original methodology, not tuned) — no claim is made about PCA at other dimensionalities. |
| **Interpretation** | Real-data evidence **partially supports** the original H2 finding under i.i.d.-like conditions (Alibaba random split) but reveals a **boundary condition the original synthetic work did not examine**: under real distribution shift, representation choice can dominate the result, including producing a representation that actively hurts (PCA(2) on the Alibaba temporal split). This is reported as a genuine extension/complication of the original finding, not a contradiction of it, and not forced into agreement. Full detail in `docs/PHASE3_REAL_DATA_3_2_REPORT.md` §17. |

## H3 — concept-drift generalization

| Field | Content |
|---|---|
| **Original Phase 3 result** | Phase 3.3: the frozen Candidate F representation generalized across a **fixed-covariate-distribution, concept-only** drift axis (`drift_scale` varied at test time only): AUROC 0.698 (weaker drift, 0.5×), 0.655 (original), 0.602 (stronger drift, 2×) — all well above no-signal, all tracking the calibrated-confidence baseline within ~0.005 AUROC (`docs/PHASE3_3_GENERALIZATION.md`). Explicitly scoped as concept-drift-only, not covariate-shift. |
| **Real-data result — Alibaba, temporal split (Q1–Q3 train → Q4 test)** | R0 AUROC 0.793 [0.774,0.812], R1 0.843 [0.826,0.861], R2 0.395 [0.371,0.418] — reused verbatim from Phase 3.2-RD, now characterized (Phase 3.3-RD) against a **newly documented compound shift**: failure rate 20.1%→43.4% *and* a genuine covariate shift (mean/median resource-request sizes drop, dominant GPU type shifts from 62.1%→80.9% MISC). See `docs/PHASE3_REAL_DATA_3_3_REPORT.md` §9. |
| **Real-data result — AIOps** | **NOT EVALUABLE FOR THIS GENERALIZATION ANALYSIS** — no frozen train/test temporal partition exists for AIOps; one was not manufactured for this purpose. |
| **Real-data result — AgentRx** | **NOT EVALUABLE** — no timestamps exist in either domain (established in the frozen protocol), and no supervised classifier exists to test generalization of in the first place (H1 blocker). |
| **Direction of agreement/disagreement** | **Not directly comparable**, not replicated/contradicted. The original H3 experiment and this real-data result probe structurally different conditions: the original held covariates fixed and varied only the drift-generating relationship; the real Q1–Q3→Q4 split varies covariates *and* label rate simultaneously, and Phase 3.2-RD already showed representation choice interacts strongly with it (a factor the original's single-representation design never had occasion to surface). |
| **Confidence/uncertainty** | Alibaba: tight CIs (reused from Phase 3.2-RD, confirmatory-capable precision). The distribution-shift characterization itself (§9 of the 3.3-RD report) is descriptive, not an estimated quantity with its own CI. |
| **Dataset limitations** | Exactly one real train/test temporal partition exists (no repeated-shift design), so precision of "how generalization degrades with shift magnitude" (which the original could vary via `drift_scale`) cannot be assessed on real data the way it could on synthetic data. |
| **Interpretation** | The real-data evidence **cannot adjudicate** the original H3 finding directly — different shift type, different design. What it *does* newly show, which the original could not: under a real, compound (concept+covariate) shift, whether a supervised signal "generalizes" depends materially on representation choice (R1 improves, R2 collapses below no-signal) — a qualification of the general claim "the signal generalizes across drift" that only a multi-representation real-data design could reveal. This is reported as a genuine extension, not a contradiction, of the original's narrower (single-representation, concept-only) finding. Full detail in `docs/PHASE3_REAL_DATA_3_3_REPORT.md` §15–17. |

## Phase 3.4-RD — consolidated baseline-vs-candidate comparison (cross-cutting, not one H-hypothesis)

Mirroring the original (synthetic) Phase 3.4's design, this is a **consolidation phase, not a new
hypothesis test** — no new model was fit; Phase 3.1-RD's Baseline A and Phase 3.2-RD's R0/R1/R2 were
compared under a properly *paired* bootstrap (same test-set rows/entities resampled jointly for baseline and
candidate), which is statistically stronger than the unpaired, overlapping-CI comparisons used in Phase
3.1-RD/3.2-RD/3.3-RD.

| Field | Content |
|---|---|
| **Original Phase 3.4 result** | Consolidated ranking B (calibrated confidence) > F (selected candidate) > E/E′ > D > C > A (no signal). F beats no-signal 6/6 seeds (CI excludes 0) but does **not** consistently beat calibrated confidence (1/6 seeds, paired CI entirely negative). Complementarity with B explicitly not tested. Overall verdict: 🟡 INCONCLUSIVE. |
| **Real-data result** | No calibrated-confidence analogue exists in the real-data track, so the original's central question ("does the candidate beat the strongest reference") cannot be asked here — only "does it beat no-signal" (§26 of `docs/PHASE3_REAL_DATA_3_4_REPORT.md`). Answer, using a proper paired test: **yes, significantly**, for R0/R1 on both Alibaba splits and (at exploratory precision) on AIOps; **R2 significantly beats no-signal on the Alibaba random split but is significantly WORSE than no-signal on the Alibaba temporal split** (paired ΔAUROC −0.105, CI [−0.129,−0.082], entirely negative); AIOps R2's apparent edge over no-signal does not survive the paired test (CI includes 0). |
| **Direction of agreement/disagreement** | **Not directly comparable** on the "beats the strongest baseline" question (structural — no such baseline exists in real data). Where comparable ("beats no-signal"), real data **extends** the original's finding: most candidates replicate "clearly beats no-signal," but the real, multi-representation, multi-split design additionally surfaces a failure mode (R2's significant *harm* under distribution shift) the original single-representation, single-condition design could not have discovered. |
| **Interpretation** | This is reported as an extension of the original's cautionary conclusion, not a contradiction: the original warned that "beats no-signal" is not the same as "ready for deployment" (it fell short of showing F beats the strongest reference); the real-data result makes essentially the same caution more concrete by showing a candidate can beat no-signal on one population and actively harm relative to it on another. Full detail: `docs/PHASE3_REAL_DATA_3_4_REPORT.md`. |

## H4 — covariate-shift / attack generalization

| Field | Content |
|---|---|
| **Original Phase 3.4/3.5 note** | H4 in the frozen protocol's hypothesis-dataset mapping refers to "covariate-shift / attack generalization" — the original Phase 3.5's synthetic attack matrix (additive noise, feature dropout) on already-generated held-out synthetic samples. See `docs/PHASE3_5_ATTACK_GENERALIZATION.md`. |
| **Real-data result** | The literal mechanism is **NOT EVALUABLE** on real data — no already-existing real-data analogue of injected feature corruption exists, and fabricating one (synthetic noise/dropout on real Alibaba/AIOps records) is explicitly prohibited by this track's research-integrity rules. Phase 3.5-RD instead tested a related, explicitly reframed, real, non-synthetic axis the authorization permitted: **unseen-workload-category generalization** (Alibaba: train excludes all `dominant_gpu_type == "T4"` jobs, test = T4 only, n=2,062; AIOps: train excludes all `db`-family windows, test = `db` only, n=56). Full detail: `docs/PHASE3_REAL_DATA_3_5_REPORT.md`. |
| **Real-data result — Alibaba** | R0 AUROC 0.571 [0.532,0.609], paired Δ vs. no-signal +0.071 [0.032,0.109] (significant, small). R1 +0.050 [0.012,0.087] (significant, barely). R2 +0.009 [−0.031,0.050] (**not significant**). All three margins are substantially smaller than the same representations' in-distribution (random/temporal split) performance. |
| **Real-data result — AIOps** | R0 AUROC 0.748 [0.596,0.933], paired Δ +0.248 [0.096,0.433] (significant, large point estimate, wide CI, n=13 entities — **EXPLORATORY**). R1 similar. R2 −0.054 [−0.310,0.134] (**not significant**). |
| **Real-data result — AgentRx** | **NOT EVALUABLE** — unchanged H1 blocker (no negative class in either frozen sample). |
| **Direction of agreement/disagreement** | **Not directly comparable** to the original — different mechanism entirely (real categorical exclusion vs. synthetic post-hoc feature perturbation). Explicitly not forced into a false replication. |
| **Interpretation** | Where a loose qualitative parallel exists: the original found the frozen candidate "remains competitive under attack" — a relatively strong claim, tested via input corruption on an otherwise-identical population. This real-data finding is more modest and structurally different: the signal generalizes to a wholly unseen category, but with a visibly smaller margin than in-distribution performance, and R2 shows no reliable effect on either dataset under this condition (though, unlike the Phase 3.3-RD/3.4-RD temporal finding, not a significant *harm* here either — both R2 CIs straddle zero rather than sitting entirely below it). Reported as a distinct, complementary real-data finding, not a stronger or weaker version of the original's synthetic-attack result. |

## H5a — complementarity / H5b — decision-cost policy

**Synthesized in Phase 3.6-RD: NOT EVALUABLE, structural.** No calibrated-confidence-equivalent baseline
exists anywhere in the real-data track (established Phase 3.1-RD, unresolved through every subsequent
phase), so H5a (does the signal add value beyond a stronger reference) has never had a second signal to test
complementarity against. No real, disclosed deployment cost model exists for any of the three datasets and
none was fabricated, so H5b (decision-cost policy) has no basis to evaluate either. Neither is a result of a
test that ran and came back negative — both are the absence of a precondition for the test to exist at all.
Full detail: `docs/PHASE3_REAL_DATA_3_6_DECISION.md` §10 (H5a, H5b).

## H6 — diagnosis

**Synthesized in Phase 3.6-RD: NOT EVALUABLE — scope gap, not data gap.** Unlike H5a/H5b/H7, this is not a
structural absence: AgentRx's organic `root_cause_failure_id`/`root_cause_reason` fields and AIOps's injected
fault categories both exist and were explicitly preserved for this purpose in the frozen protocol
(`docs/PHASE3_REAL_DATA_PROTOCOL.md` §3). No authorized phase (protocol design through Phase 3.6-RD
synthesis) included running a diagnosis experiment against them. This is documented as a candidate future
experiment (`docs/PHASE3_REAL_DATA_3_6_DECISION.md` §22), not attempted here.

## H7 — recovery

**NOT EVALUABLE on any dataset**, per the frozen protocol's mapping (no dataset records a recovery
action/outcome). This is a structural limitation of the currently held data, not an execution gap — no
future authorized phase under the current data holdings can change this conclusion without new data
acquisition. Reconfirmed, unchanged, by the Phase 3.6-RD synthesis (`docs/PHASE3_REAL_DATA_3_6_DECISION.md`
§10, H7).

---

## Phase 3.6-RD — final synthesis

Phase 3.6-RD (2026-08-13) consolidated all of the above into a single final decision table and a set of
explicit Phase 4 recommendations, without running any new evaluation. Full detail, including the complete
strongly-supported/partially-supported/negative/inconclusive/not-evaluable/newly-discovered finding
breakdown and Phase 4 implications, is in `docs/PHASE3_REAL_DATA_3_6_DECISION.md` and the machine-readable
`configs/phase3_6_rd_decision.json`. The headline conclusion: real data reproduces the qualitative core of
the original Phase 3's H1 finding (a supervised signal exists) but reveals that neither the signal's strength
nor its representation-choice-independence is uniform across distribution-shift conditions — a boundary
condition the original single-representation, single-shift-type synthetic design never had the structure to
surface. Four hypotheses (H5a, H5b, H6, H7) remain unevaluated, three for structural reasons and one (H6)
purely from scope.

---

## Summary table

| Hypothesis | Status | Real-data direction vs. original |
|---|---|---|
| H1 | **Executed (Phase 3.1-RD)** | Agrees directionally (Alibaba, AIOps); cannot adjudicate (AgentRx) |
| H2 | **Executed (Phase 3.2-RD)** | Partially agrees (Alibaba random split); not robust under distribution shift (Alibaba temporal split — new finding, no original analogue); inconclusive (AIOps); cannot adjudicate (AgentRx) |
| H3 | **Executed (Phase 3.3-RD)** | Not directly comparable (different shift type: concept-only vs. compound concept+covariate); AIOps/AgentRx not evaluable |
| Phase 3.4-RD (consolidation, cross-cutting) | **Executed** | Not directly comparable on "beats strongest baseline" (no real analogue of B exists); extends the original's caution via a paired test showing R2 significantly harms relative to no-signal under Alibaba's temporal shift |
| H4 | **Executed (Phase 3.5-RD)** | Not directly comparable (real categorical-holdout vs. original's synthetic feature perturbation — literal mechanism NOT EVALUABLE on real data); real, reframed unseen-workload test shows a real but much smaller signal margin than in-distribution splits, with R2 showing no reliable effect on either dataset |
| H5a/H5b | **Synthesized (Phase 3.6-RD): NOT EVALUABLE, structural** | No real-data baseline/cost-model precondition exists to test against |
| H6 | **Synthesized (Phase 3.6-RD): NOT EVALUABLE, scope gap** | Usable fields exist (AgentRx root-cause, AIOps fault category) but no phase attempted this experiment |
| H7 | **Synthesized (Phase 3.6-RD): NOT EVALUABLE / STRUCTURAL GAP** | No dataset records recovery outcomes |

This document was updated by Phase 3.6-RD (2026-08-13) with the final synthesis. The real-data Phase 3
replication research program is now complete pending review; any further evaluation requires a new,
separately authorized phase.
