# PHASE 3.9 — V1 DECISION-FAILURE & INFORMATION-GAP FORENSICS

## 1. Executive Summary

Phase 3.9 performed deterministic forensic analysis of frozen V1 across the canonical random-stratified population, canonical temporal population, and Phase 3.5 Folds 1–3. It classified every case using the canonical 0.5 threshold, compared correct and incorrect decisions, quantified decision-time feature signatures, and separated decision-time information from post-outcome or unknown information.

The strongest finding is that V1 errors have observable signatures in several decision-time variables, but the direction and magnitude are often unstable across future regimes. No causal mechanism was established. The evidence supports a cautious observability/information research direction, not a new predictor or immediate V1.1 integration.

## 2. Research Question

The question was whether V1 errors are caused by observable decision-time information that the architecture fails to use, or whether many errors are fundamentally unresolvable from available information. The analysis does not assume either outcome.

## 3. Frozen V1 Control

V1 remained frozen at `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. The 14-feature numeric contract, preprocessing, isotonic calibration boundary, threshold definition, canonical splits, and historical artifacts were not modified. Phase 3.9 trained no error classifier and performed no model search.

## 4. Phase 3 Evidence Context

Phase 3.8 left Candidate A at HOLD and Candidate C rejected for its tested implementation. Phase 3.6.3 showed that a single favorable temporal result did not establish robustness. These results motivate forensic analysis rather than another blind intervention.

## 5. Data and Evaluation Boundaries

The official restored Alibaba GPU2020 data and registered populations were used. Every population was analyzed in its registered identity and order. The case-level table contains V1 inputs and forensic labels; post-outcome labels are not represented as decision-time features.

## 6. Failure Definition

A V1 failure is an incorrect binary decision at the canonical threshold of 0.5: `predicted_label != true label`. Risk, calibrated risk, uncertainty, population, fold identity, and case identifier are recorded. Uncertainty is the deterministic diagnostic `1 - abs(2*risk - 1)`.

## 7. V1 Failure Taxonomy

The final primary taxonomy is deliberately small and mutually exclusive: correct, high-confidence error, and low-confidence error. Secondary tags are multi-label and descriptive, including false-positive, false-negative, temporal-regime, and feature-missingness tags. Unsupported causal, severity, and memory-mechanism categories were not manufactured.

## 8. Failure Case Distribution

| Failure Category | Cases | % of failures | % of all cases | Temporal presence | Cross-fold stability | Decision-time information | Confidence |
|---|---:|---:|---:|---|---|---|---|
| high_confidence_error | 1180 | 43.66% | 11.80% | True | ROBUST | A — observable and already used by V1 | HIGH |
| low_confidence_error | 1523 | 56.34% | 15.23% | True | REGIME-SPECIFIC | A — observable and already used by V1 | HIGH |

Population-level metrics and case distributions are stored in `tables/population_metrics.json` and `failure_taxonomy/failure_cases/`.

## 9. High-Confidence Error Analysis

High-confidence errors are cases with uncertainty at or below 0.50. They are potentially more operationally dangerous than low-confidence errors, but high confidence is not evidence of causality. Their prevalence and feature distributions are recorded in the case-level table and univariate signature table.

## 10. Low-Confidence Error Analysis

Low-confidence errors remain diagnostically distinct from high-confidence errors. The analysis preserves them as a separate primary category and does not assume that low confidence automatically makes an error actionable.

## 11. Random vs Temporal Failure Comparison

Random and temporal populations were analyzed using the same failure definition and feature contract. Temporal error signatures differ materially in several variables, but this difference is not by itself evidence of a general mechanism; it may reflect distribution shift. The canonical temporal population and each future fold remain separately reported.

## 12. Cross-Fold Error Signatures

Cross-fold signatures were computed using standardized mean differences between incorrect and correct cases for each V1 feature. Signatures are marked ROBUST only when direction and meaningful magnitude are consistent across canonical temporal and all three future folds. Direction changes are marked UNSTABLE. Several timing/resource variables are unstable, limiting confidence in a universal failure mechanism.

## 13. Decision-Time Information Availability

A value is classified as decision-time only when its role is part of the pre-outcome feature contract. Dataset presence alone does not prove runtime availability. Post-decision telemetry, final outcomes, future memory, and evaluation labels are forensic-only and cannot be proposed as original decision-time information.

## 14. Information-Gap Matrix

| Failure Category | Information Needed | Available at Decision Time? | Already Used by V1? | Potentially Useful? | Acquisition Cost | Leakage Risk | Classification |
|---|---|---|---|---|---|---|---|
| high/low-confidence error | V1 risk and calibrated score | DECISION-TIME | True | Yes, policy interpretation | None | Low | A |
| temporal-regime error | job start time and workload/resource summary | DECISION-TIME | True | Possibly; signatures are exploratory | None in current contract | Low | A |
| missingness-associated error | feature presence at decision time | DECISION-TIME | Yes, through imputation | Possibly | Low | Low | A |
| prior failure similarity | temporally eligible failure memory | Potentially available | False | Unproven; Candidate C rejected | Medium/high | High unless prior-only | C |
| future telemetry or final outcome | post-decision resource state/outcome | POST-OUTCOME | False | Forensic explanation only | Not applicable | Prohibited | D |
| unmaterialized queue/machine context | runtime context not in processed contract | UNKNOWN | False | Unknown | Unknown | Unknown | F |

## 15. Observable vs Post-Outcome Information

The risk score, workload summaries, timestamps, and missingness indicators are observable within the declared V1 boundary and already used by V1. Prior failure similarity is potentially observable but operationally expensive and leakage-sensitive; Candidate C did not establish benefit. Final outcomes and future telemetry are post-outcome and can explain an error retrospectively but cannot safely correct the original prediction.

## 16. Error Signature Analysis

Univariate SMD, KS, missingness differences, and univariate error AUROC are exploratory association measures. They do not establish causality. The full deterministic table is `error_signatures/univariate/univariate_signatures.csv`; cross-fold comparison is `error_signatures/cross_fold/cross_fold_signatures.csv`.

## 17. Failure Concentration

Failures are concentrated differently by population, and timing/resource variables show population-dependent separation. Concentration is quantified in the case-level tables rather than inferred only from plots. No unsupported workload class or severity class was invented.

## 18. Failure Stability

The available evidence supports **UNSTABLE** or **REGIME-SPECIFIC** signatures more strongly than a single robust mechanism. A future mechanism should be called robust only after consistent direction and effect across canonical temporal and Folds 1–3.

## 19. Failure Severity Limitations

The benchmark provides binary failure labels, not operational consequence, recovery cost, safety severity, or business impact. Therefore this phase does not fabricate harmless/important/high-risk severity classes.

## 20. Architectural Opportunity Map

| Rank | Opportunity | Evidence strength | Decision-time availability | Risk | Recommendation |
|---:|---|---|---|---|---|
| 1 | Bounded evidence request or escalation | High; reproduced in prior phases | Risk/uncertainty available | Coverage/latency and policy overfit | **TEST NEXT** |
| 2 | Separate diagnostic context, not blind abstention | Medium; exploratory cross-fold analysis | 14 numeric features available | Regime instability | **TEST NEXT** |
| 3 | New strict retrieval study | Medium; architecture exists but Candidate C rejected | Potentially prior-only | Leakage/staleness/overhead | **RESERVE** |
| 4 | Instrumentation for later diagnosis only | High that information exists only after outcome | Not decision-time | Cannot solve original error | **RESERVE** |

The smallest defensible opportunity is an observability/decision-context study, not a replacement predictor. Any future intervention must remain additive and must prove benefit under the full temporal boundary.

## 21. Previously Tested Approaches

The phase explicitly accounts for model capacity, feature filtering, contextual representations, calibration alternatives, uncertainty, abstention, drift-aware abstention, limited interactions, structured evidence requests, and failure-memory context. Their results are preserved in the Phase 3 audit and Phase 3.8 records; none is reclassified as successful by this forensic analysis.

## 22. Do-Not-Repeat Findings

Do not repeat unrestricted GB/RF search, feature fishing, naive uncertainty abstention, the rejected Candidate C implementation, or single-fold interaction selection. A future study must state how it differs and what new evidence justifies reconsideration.

## 23. Candidate Future Directions

The most defensible future directions are: first, instrument a narrowly defined decision-time context signal and test whether it is stable before changing actions; second, study uncertainty as an interpretable diagnostic with explicit operational cost. Prior-only memory remains reserve until provenance, staleness, and utility are demonstrated with a stronger operational episode dataset.

## 24. Opportunity Ranking

The opportunity ranking prioritizes decision-time availability, cross-fold stability, safety, low complexity, and evaluability. The ranking is a research recommendation, not an accepted V1.1 candidate.

## 25. Safety and Operational Considerations

No future outcome may enter a decision-time signal. Any added context must have an availability timestamp, provenance, bounded latency, deterministic fallback, and leakage audit. A regime-specific signature must not trigger a universal policy without additional evidence.

## 26. Limitations

The data does not expose full operational consequence, live queue context, complete machine context, or all runtime provenance. The analysis is observational and exploratory. Missing historical skip-node identities remain unrecoverable. Absence of a stable signature is not proof that no hidden mechanism exists.

## 27. Final Research Decision

**V1 FAILURE MECHANISM REMAINS UNRESOLVED.** There are observable associations, but the principal signatures are unstable across future regimes and no causal or operationally validated information gap has been demonstrated. V1 remains frozen and no V1.1 integration is authorized.

## 28. Recommendation for Next Phase

Do not begin V1.1 integration. If research continues, first collect or expose a rigorously timestamped decision-time context/observability trace, then preregister one narrow hypothesis. Re-evaluate only on the existing canonical temporal test and Phase 3.5 Folds 1–3; do not create a rescue fold or combine failed candidates.

## References

1. `docs/PHASE3_BASELINE_AUDIT.md`
2. `experiments/results/v1_1/candidate_screening/3_8/PHASE3_8_SYNTHESIS.md`
3. `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/`
4. `docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md`


## Validation record

The required current full repository suite was attempted from `2026-08-23T09:24:11Z` to `2026-08-23T09:29:11Z`. It reached approximately 48% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

Phase 3.9 focused validation passed: 8 forensic tests, compilation, diff check, leakage-boundary checks, historical-path protection, and SHA-256 verification.
