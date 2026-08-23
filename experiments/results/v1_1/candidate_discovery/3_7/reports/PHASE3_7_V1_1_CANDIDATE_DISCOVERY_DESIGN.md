# PHASE 3.7 — V1.1 CANDIDATE DISCOVERY & DESIGN

**Status:** Complete — design and discovery only  
**V1 status:** Frozen; no production modification  
**Final decision:** **V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET**  
**Primary architectural direction:** **RELIABILITY/DECISION ARCHITECTURE**

## 1. Executive Summary

Phase 3.7 converts the accumulated Phase 3 evidence into a small, falsifiable V1.1 research agenda. The evidence does not justify replacing the frozen V1 predictor with a more complex classifier. Flexible alternatives repeatedly failed under temporal shift, and the only favorable limited-interaction result failed to replicate across three authoritative future folds. In contrast, uncertainty remains diagnostically useful even though the previously tested abstention rule was not operationally acceptable.

Five candidate categories were investigated. Two are selected for **future experimental screening**: structured uncertainty with a bounded evidence-request policy, and provenance-aware failure-memory context. Both preserve V1 as the prediction anchor and target capabilities V1 does not currently provide. No candidate-specific screening experiment was executed in this discovery/design phase; therefore no candidate is promoted, integrated, or called production-ready.

## 2. Current V1 State

V1 remains the sole production-eligible control at canonical freeze commit `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. The 14-feature numeric contract, preprocessing, calibration, threshold, runtime, memory, diagnosis, recovery, and safety behavior remain untouched. The historical aggregate test result and the limitation that the seven historical skipped-node identities are unrecoverable remain preserved.

## 3. Evidence Synthesis from Phase 3.0–3.6.3

| Phase | Intervention or question | Outcome | Implication for Phase 3.7 |
|---|---|---|---|
| 3.0–3.0.2 | Baseline audit, V1 freeze, reconciliation, data restoration | V1 boundary and reproducibility contract established; skipped-node identity limitation remains | Preserve identity and provenance contracts in every candidate |
| 3.1 | Gradient Boosting reliability model | Random gain but temporal AUROC collapse | Do not pursue unconstrained capacity |
| 3.2 | Stability filtering and feature representations | Removing shifted clock features did not improve temporal performance | Simple feature removal is insufficient |
| 3.3 | Temporal selection, contextual representations, RF, drift abstention | No intervention accepted; drift abstention had an operational coverage problem | Do not repeat unchanged interventions |
| 3.4 | Platt calibration, uncertainty, uncertainty abstention | Platt worsened calibration; uncertainty was diagnostically useful; fixed abstention failed | Redesign how uncertainty informs actions |
| 3.5 | Multi-temporal uncertainty and abstention | Diagnostic separation persisted; policy remained non-actionable | Uncertainty merits contextual use, not naive thresholding |
| 3.6–3.6.2 | Forensics and matched complexity ladder | Constrained structure appeared more stable; limited interactions improved one temporal split | Require multi-temporal validation before any promotion |
| 3.6.3 | Three authoritative future folds | Interactions won 1/3 and lost 2/3; mean AUROC delta −0.0209; worst −0.0718 | Do not integrate the interaction candidate |

## 4. What V1 Does Well

V1 provides a compact, reproducible numeric predictor with a preserved calibration path and documented runtime integration. It is comparatively robust on the registered temporal population relative to flexible RF/GB alternatives. Its surrounding architecture already separates reliability scoring, uncertainty, abstention, diagnosis, recovery, safety gates, validation, and failure experience rather than collapsing these into one opaque score.

## 5. V1 Limitations

V1 does not provide a sufficiently rich, explicitly evaluated interpretation of uncertainty, distribution context, provenance of historical failures, or action selection under difficult cases. The predictor produces a risk estimate, but the project has not established a defensible way to convert difficult-case signals into warning, evidence request, escalation, or diagnostic actions while preserving useful coverage.

## 6. Unresolved Reliability Problems

The causal mechanism behind temporal robustness remains unresolved. It is not established whether uncertainty, drift context, memory context, or model disagreement can improve operational decisions. Historical skip-node identities are unrecoverable. Memory may be sparse or stale, distribution context may be confounded with prevalence, and any policy may introduce coverage or latency costs. These uncertainties are explicit rejection risks, not assumptions in favor of a candidate.

## 7. Previously Tested Approaches

Previous work tested model capacity, feature filtering, contextual representations, temporal validation selection, drift-aware abstention, calibration alternatives, uncertainty estimation, fixed abstention, and limited interactions. Negative and mixed results are retained. Phase 3.7 does not reopen the model-comparison ladder or modify the canonical feature contract.

## 8. Do-Not-Repeat Analysis

| Previous experiment | Intervention | Outcome | Limitation | Phase 3.7 treatment |
|---|---|---|---|---|
| 3.1 | Gradient Boosting | Rejected | Temporal collapse | Do not repeat |
| 3.2 | Stability filtering | Rejected | Temporal degradation | Do not repeat |
| 3.3-A | Temporal validation selection | Hold | Small/inconclusive gain | Not first priority |
| 3.3-B | Contextual representations | Rejected | Temporal degradation | Do not repeat unchanged |
| 3.3-C | Random Forest | Rejected | Temporal collapse | Do not repeat |
| 3.3-D | Drift abstention | Rejected | Operationally unusable coverage | Only redesign as context |
| 3.4-A | Platt calibration | Rejected | Calibration worsened | Do not repeat |
| 3.4-B | Uncertainty | Interesting | Diagnostic, not action-ready | Revisit in redesigned policy |
| 3.4-C | Uncertainty abstention | Rejected | Temporal risk worsened | Do not repeat same rule |
| 3.4-D | Combined calibration/uncertainty | Rejected | No safety/coverage improvement | Do not repeat |
| 3.5 | Multi-fold uncertainty | Hold | Diagnostic but non-actionable | Revisit only as redesigned architecture |
| 3.6.2 | Limited interactions | Promising one split | Failed multi-temporal validation | Do not integrate |
| 3.6.3 | Multi-temporal interactions | Hold | 1/3 wins, 2/3 losses | No immediate revisit |

## 9. Architectural Opportunity Analysis

The main weakness is not proven to be the V1 predictor. The strongest evidence instead points to a missing layer between a reliable base risk and an operational action. The recommended research direction is therefore a reliability/decision architecture around frozen V1: preserve V1 risk, add auditable uncertainty and context signals, and evaluate explicit actions such as warning, evidence request, escalation, and diagnosis.

This is an architectural hypothesis, not an instruction to add every component. Each component must earn inclusion through a pre-registered experiment. The design must include safe defaults, empty-context behavior, bounded latency, explicit provenance, and future-fold validation.

## 10. Candidate Inventory

The five investigated candidates are documented in `candidate_inventory/candidate_inventory.md`. They are: **A**, structured uncertainty and evidence-request policy; **B**, distribution-context monitor; **C**, provenance-aware failure-memory context; **D**, constrained model disagreement; and **E**, explicit structured decision policy.

## 11. Candidate Comparison

| Candidate | Capability | Evidence basis | Main risk | Novelty | Priority |
|---|---|---|---|---|---:|
| A | Interpret uncertainty through bounded evidence requests | Multi-fold uncertainty signal, failed fixed abstention | Coverage and arbitrary policy thresholds | Redesigns action use of uncertainty | 1 |
| C | Add provenance-aware prior failure context | Existing memory architecture and lifecycle evidence | Leakage, staleness, sparse retrieval | Tests memory as decision context, not predictor input | 2 |
| B | Detect out-of-regime context | Demonstrated temporal distribution shift | Excessive escalation or confounding | Separates drift from automatic abstention | 3 |
| D | Use constrained disagreement as difficulty signal | Complexity caution and complementary linear possibility | Correlated errors and instability | Keeps V1 as anchor | 4 |
| E | Evaluate explicit operational action mapping | Existing safety/diagnosis/recovery stages | Unsupported policy assumptions | Makes decision quality primary | 5 |

## 12. Candidate Selection Rationale

Candidates A and C are selected for future screening because they target missing capabilities rather than raw AUROC, preserve V1, have positive but incomplete evidence, and admit clear leakage and safety tests. Candidate B is plausible but should follow a clean redesign of drift evaluation. Candidate D lacks enough independent evidence to prioritize. Candidate E is a broader architecture wrapper and should be evaluated after at least one concrete signal has demonstrated value.

Selection does not mean acceptance. It only freezes a maximum-two screening agenda and prevents unrestricted search.

## 13. Research Hypotheses

**H1:** A structured uncertainty signal combined with bounded contextual evidence can improve decision safety without the coverage failure of standalone threshold abstention.

**H2:** Temporally eligible, provenance-tagged historical failure memory can improve current risk interpretation without modifying the frozen V1 predictor.

Both hypotheses are falsifiable and have predeclared rejection criteria in `candidate_protocols/selected_candidate_protocols.json`.

## 14. Experimental Protocols

The selected-candidate protocol freezes the Alibaba GPU2020 data identity, matched 14-feature contract, canonical temporal test, and all three Phase 3.5 authoritative chronological folds. It requires training-only fitting, validation-only policy calibration, unchanged V1 isotonic calibration, deterministic seed `3637`, no hyperparameter search, no future-fold selection, and direct V1 comparison using AUROC, AUPRC, Brier, ECE, coverage, selective risk, error rates, escalation, latency, and memory overhead where applicable.

Each future screening experiment must record data hashes, fold definitions, preprocessing, calibration, thresholds, software versions, seeds, artifact hashes, leakage results, and provenance. Finalization must be immutable. Candidate-specific model or policy execution is intentionally **not included in Phase 3.7 design completion**.

## 15. Candidate Experiment Results

No new candidate experiment was executed in Phase 3.7. This is an explicit design-phase boundary, not a missing result. The only valid candidate result at this stage is **not screened**. Existing Phase 3 evidence is used to rank directions, not relabeled as evidence for a new candidate.

## 16. Multi-Temporal Validation

Any future candidate screening must evaluate the canonical temporal test plus Phase 3.5 Folds 1–3. A candidate cannot be promoted from one favorable population. The Phase 3.6.3 interaction result demonstrates why: its single-split improvement did not survive the authoritative multi-fold test.

## 17. Safety / Reliability Analysis

A candidate is not acceptable on average AUROC alone. It must avoid catastrophic future-fold degradation, preserve useful coverage or justify its reduction, remain deterministic and bounded, avoid future information, respect V1 data boundaries, and show no unexplained temporal instability. Candidate A must additionally report action coverage and selective risk. Candidate C must additionally report retrieval leakage, empty-memory behavior, memory age, provenance quality, and overhead.

## 18. Failure Analysis

The principal foreseeable failures are policy over-abstention, escalation floods, stale or contaminated memory, non-stationary drift scores, sparse history, and false confidence from apparently similar failures. The protocol treats these as rejection conditions. If no candidate demonstrates reliable benefit, the correct result is that V1 remains the best control and further research is required.

## 19. Candidate Ranking

| Rank | Candidate | Status | Reason |
|---:|---|---|---|
| 1 | A — Structured uncertainty/evidence request | Selected for future screening | Strongest direct evidence and clear redesign of failed abstention |
| 2 | C — Provenance-aware failure memory | Selected for future screening | Addresses operational context while preserving predictor isolation |
| 3 | B — Distribution-context monitor | Reserve | Plausible but drift-action coupling needs stricter design |
| 4 | D — Constrained disagreement | Reserve | Insufficient independent evidence |
| 5 | E — Explicit policy wrapper | Reserve | Broad architecture candidate; depends on validated signals |

## 20. V1.1 Architecture Recommendation

The recommended architecture is **RELIABILITY/DECISION ARCHITECTURE**, not a better predictor: frozen V1 produces the base risk; separately validated uncertainty and/or provenance-aware context may inform an explicit, bounded decision layer; safe action, escalation, diagnosis, and recovery remain governed by existing safety boundaries. Components must be added only if experiments justify them.

## 21. Limitations

Phase 3.7 does not establish candidate performance because no new candidate screening was run. The Alibaba dataset remains a research/evaluation boundary. Historical skip-node identities remain unrecoverable. Candidate policy costs, latency budgets, and useful-coverage gates require project-level preregistration before screening. No causal claim is made about why V1 is temporally robust.

## 22. Final Decision

**V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET.** The defensible direction is a reliability/decision architecture around frozen V1, with Candidates A and C frozen for later screening. No candidate has sufficient evidence to proceed directly to integration.

## 23. Next Phase

Run the two selected candidate protocols independently, with candidate-specific tests, deterministic serialization, leakage audits, the canonical temporal test and all three Phase 3.5 folds. Report successful, failed, inconclusive, and unexpected outcomes without cherry-picking. Any candidate that survives must enter a later dedicated integration and broader validation phase.

## Required final candidate table

| Candidate | Main capability | Random performance | Temporal performance | Safety | Robustness | Novelty | Decision |
|---|---|---|---|---|---|---|---|
| A | Structured uncertainty/evidence request | Not screened | Not screened | Preregistered gates | Must pass four future populations | High | Selected for future screening |
| B | Distribution context | Not screened | Not screened | No blind abstention | Must pass four future populations | Medium | Reserve |
| C | Provenance-aware failure memory | Not screened | Not screened | Leakage and empty-memory gates | Must pass four future populations | High | Selected for future screening |
| D | Constrained disagreement | Not screened | Not screened | No predictor replacement | Must pass four future populations | Medium | Reserve |
| E | Explicit decision policy | Not screened | Not screened | Action and coverage gates | Must pass four future populations | Medium | Reserve |

## V1 versus candidates at this phase

| Metric | V1 | Candidate A | Candidate C | Delta / future deltas |
|---|---:|---:|---:|---|
| Random AUROC | Existing control | Not screened | Not screened | Not applicable |
| Temporal AUROC | Existing control | Not screened | Not screened | Not applicable |
| Random AUPRC | Existing control | Not screened | Not screened | Not applicable |
| Temporal AUPRC | Existing control | Not screened | Not screened | Not applicable |
| Temporal Brier | Existing control | Not screened | Not screened | Not applicable |
| Temporal ECE | Existing control | Not screened | Not screened | Not applicable |
| Coverage | Existing control | Not screened | Not screened | Not applicable |

## References

1. `docs/PHASE3_BASELINE_AUDIT.md` — master audit and Phase 3.6.3 closure.
2. `experiments/results/v1_1/calibration_abstention/` — calibration and uncertainty evidence.
3. `experiments/results/v1_1/distribution_robust_uncertainty/` — multi-temporal uncertainty evidence.
4. `experiments/results/v1_1/temporal_robustness/` — Phase 3.3 temporal interventions.
5. `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/` — matched multi-temporal complexity evidence.
6. `docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md` — failure-memory lifecycle and provenance boundary.
7. `experiments/results/v1_1/candidate_discovery/3_7/candidate_inventory/candidate_inventory.md` — full candidate inventory.
8. `experiments/results/v1_1/candidate_discovery/3_7/candidate_protocols/selected_candidate_protocols.json` — frozen screening protocols.

## Validation record

The required full-suite run was attempted as a bounded current run. It started at `2026-08-23T08:51:32Z`, ran for five minutes, reached approximately 49% collection progress, and terminated with exit code `124` at `2026-08-23T08:56:32Z` because the timeout expired while the suite remained CPU-bound. The last captured state was `.................` after the 49% progress line. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured log is preserved at `artifacts/full_suite_attempt.txt`.

The inherited verified suite result remains distinct: the preceding Phase 3.6.3 work recorded 558 passed and 7 skipped. Phase 3.7-specific validation is separate and currently consists of 7 focused tests passed, compilation passed, `git diff --check` passed, and finalized-artifact SHA-256 verification passed.
