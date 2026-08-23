# PHASE 3.8 — CANDIDATE A & C EXPERIMENTAL SCREENING

## 1. Executive Summary

Phase 3.8 independently screened Candidate A and Candidate C around the frozen V1 predictor. Candidate A preserved V1 predictive outputs and added a bounded evidence-request/escalation action layer. Candidate C added prior-only, provenance-aware failure-memory context without changing V1 training. Candidate A tied V1 on all predictive metrics by design and requires an operational decision benefit that was not demonstrated by this implementation. Candidate C showed small mixed predictive changes but no robust temporal improvement. The final decision is **BOTH CANDIDATES REQUIRE FURTHER STUDY**; V1 remains the control and no integration is authorized.

## 2. Phase Objective

The objective was to determine whether either independently screened additive layer improves operational safety, contextual decision quality, or reliability without sacrificing temporal robustness. The objective was not to force a winner or maximize AUROC.

## 3. Frozen V1 Control

V1 remained frozen at `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. The 14-feature numeric contract, preprocessing, validation-only isotonic calibration, and registered populations were preserved. Candidate outputs were compared against the same V1-derived scores for each population.

## 4. Candidate A Protocol

Candidate A used V1 calibrated risk and an output-side uncertainty signal to choose among `NORMAL`, `REQUEST_EVIDENCE`, and `ESCALATE`. The requested evidence was limited to pre-outcome `n_tasks`, `n_instances`, and `mean_plan_cpu`; missing evidence fell back deterministically. No future labels or results were used, and V1 scores were not recalibrated or retrained.

## 5. Candidate C Protocol

Candidate C built memory only from failed training-boundary jobs. Retrieval required a strict prior timestamp, complete provenance, a fixed standardized-distance threshold, and deterministic empty-memory fallback. The memory context was external to V1 prediction and candidates were not combined.

## 6. Dataset and Evaluation Boundary

The official restored Alibaba GPU2020 dataset and matched 14-feature numeric contract were used. Populations were the canonical random-stratified evaluation, canonical temporal future evaluation, and Phase 3.5 Folds 1–3 in their registered order. No new or removed folds were introduced.

## 7. Leakage and Provenance Controls

Candidate A used only decision-time pre-outcome fields. Candidate C used only training-boundary failed jobs, required strict timestamp eligibility, and rejected missing provenance. Both audits recorded `future_labels_used: false`, `future_fold_results_used_for_configuration: false`, and `v1_predictor_modified: false`. Leakage audits passed for the implemented screening records.

## 8. Candidate A Results

Candidate A produced exactly zero AUROC and AUPRC deltas on all five populations because its intervention intentionally preserved V1 predictive scores. Its value, if any, must therefore come from action quality rather than predictive ranking.

## 9. Candidate A Multi-Temporal Results

Candidate A had 0 wins, 0 losses, and 5 ties on AUROC versus V1. Its future-fold AUROC delta was 0.000000 on Fold 1, Fold 2, and Fold 3. This preserves ranking robustness but does not demonstrate an operational improvement.

## 10. Candidate A Safety Analysis

The evidence-request rate, coverage, selective risk, escalation rate, unresolved-request rate, and latency cost are serialized per population. The policy did not catastrophically degrade predictive metrics and did not use future information. However, this run does not establish a meaningful safety improvement over V1. Candidate A is therefore **HOLD**, not promising.

## 11. Candidate A Decision

**HOLD.** Candidate A is a valid additive research implementation, but the current screening does not demonstrate the required measurable decision-safety benefit sufficient to justify complexity.

## 12. Candidate C Results

Candidate C changed only the contextual decision-layer score. Across all five populations it achieved 3 AUROC wins and 2 losses, with mean delta 0.001931, median delta 0.000086, and worst delta -0.000202.

## 13. Candidate C Multi-Temporal Results

Candidate C's AUROC deltas on Fold 1, Fold 2, and Fold 3 were -0.000089, -0.000202, 0.000106. The candidate therefore did not establish consistent future-regime benefit. The small positive mean across all populations is not sufficient to override mixed chronological results.

## 14. Candidate C Safety Analysis

No catastrophic fold failure occurred in the implemented score comparison, but the candidate introduced a nonzero contextual modification and retrieval cost. Strict prior-only memory construction and provenance checks passed. Safety benefit was not established, so the candidate cannot proceed to integration.

## 15. Candidate C Memory Analysis

Memory availability, empty-memory behavior, stale-memory rate, conflict rate, retrieval latency, and overhead are serialized for every population. The current fixed retrieval implementation observed no conflicts and no stale-memory use because only eligible training-boundary records were accepted. This is a property of the screened construction, not evidence that memory is universally reliable.

## 16. Cross-Candidate Comparison

| Candidate | Primary capability | Temporal robustness | Safety | Coverage | Operational cost | Evidence quality | Decision |
|---|---|---|---|---|---|---|---|
| V1 Control | Base calibrated risk | Control | Control | Baseline | Baseline | Established | CONTROL |
| Candidate A | Evidence request and escalation | Predictive tie on all populations | No demonstrated benefit | Action-dependent | Request/latency cost | Valid but insufficient | HOLD |
| Candidate C | Prior failure context | Mixed; 1 loss on Fold 1 and 1 loss on Fold 2 | Leakage gates passed; benefit unproven | Full score coverage | Retrieval overhead | Valid but insufficient | REJECT |

## 17. Failure Analysis

Candidate A did not demonstrate that an evidence request resolves difficult cases well enough to improve outcomes. Candidate C's small score modifier improved some populations and worsened others, including two future folds; memory availability alone is not evidence of utility. Neither failure justifies combining the candidates or inventing a new candidate to rescue the phase.

## 18. Negative Results

The absence of a Candidate A predictive change and the mixed Candidate C temporal deltas are first-class results. No favorable population was selected, no unfavorable fold was removed, and no thresholds or memory parameters were retuned after observing results.

## 19. Reproducibility

The runner, protocol, per-population JSON records, predictions, leakage audits, reports, plot, and SHA-256 finalization manifest are stored under this directory. Candidate A and Candidate C were executed independently with seed `3637`; the combined candidate was not created.

## 20. Limitations

The dataset is a research/evaluation boundary. The evidence-request source is a bounded proxy for additional contextual evidence rather than a live external evidence service. Candidate C's memory is a controlled research construction and does not establish benefit on richer operational episodes. Historical skipped-node identities remain unrecoverable. The current repository full-suite attempt must be interpreted separately if it times out.

## 21. V1 vs Candidate Summary

| Metric | Frozen V1 | Candidate A | Candidate C |
|---|---:|---:|---:|
| Random AUROC | Control | Same by design | Delta 0.009753 |
| Temporal AUROC | Control | Same by design | Delta 0.000086 |
| Mean future AUROC delta | 0 | 0.000000 | 0.001931 |
| Worst future AUROC delta | 0 | 0.000000 | -0.000202 |
| Coverage | Baseline | Action-dependent | Full score coverage |
| Selective risk | Baseline | Serialized per population | Serialized per population |
| Escalation rate | Baseline | Serialized per population | Memory-use proxy serialized |
| Latency | Baseline | Request cost serialized | Retrieval cost serialized |
| Memory overhead | Baseline | None | Serialized per population |

## 22. Final Research Decision

**BOTH CANDIDATES REQUIRE FURTHER STUDY.** Candidate A is HOLD because the action-layer benefit was not established. Candidate C is REJECT for this concrete implementation because its temporal benefit was mixed and its positive mean was insufficient to justify memory complexity. V1 remains frozen and remains the strongest validated control under the tested conditions.

## 23. Recommendation for Phase 3.9

Do not begin consolidation or integration. If research continues, redesign only one candidate at a time with a new explicit hypothesis, stronger operational outcome labels, and a predeclared cost model. Do not combine Candidate A and C to rescue either result. A later phase may revisit the reliability/decision architecture only after a candidate independently satisfies all multi-temporal, leakage, safety, and reproducibility gates.

## References

1. `docs/PHASE3_BASELINE_AUDIT.md`
2. `experiments/results/v1_1/candidate_discovery/3_7/`
3. `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/`
4. `docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md`


## Validation record

The required current full repository suite was attempted from `2026-08-23T09:10:29Z` to `2026-08-23T09:15:29Z`. It reached approximately 48% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

Phase 3.8 focused validation passed: 8 candidate-screening tests, deterministic contract checks, compilation, and artifact hash checks. Historical-path protection and `git diff --check` are required before commit.
