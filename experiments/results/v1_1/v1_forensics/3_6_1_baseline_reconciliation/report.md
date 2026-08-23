# PHASE 3.6.1 — BASELINE IDENTITY & PROTOCOL RECONCILIATION

## 1. Executive summary

The discrepancy is reproducible and explained. The data rows and registered random/temporal split identities match. The frozen V1 control is a **numeric-only** logistic pipeline using the 14 V1 numeric features. The Phase 3.6 research-copy logistic pipeline adds the categorical `dominant_gpu_type` feature with one-hot encoding. This changes the design matrix, coefficients, and predictions, producing 0.7348/0.7931 rather than canonical 0.7201/0.8302.

## 2. Original discrepancy

| Experiment | Random AUROC | Temporal AUROC | Random AUPRC | Temporal AUPRC | Random Brier | Temporal Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| Canonical V1 | 0.7201 | 0.8302 | 0.5397 | 0.7464 | 0.1444 | 0.2185 |
| Phase 3.6 research copy | 0.7348 | 0.7931 | 0.5373 | 0.6354 | 0.1635 | 0.2706 |
| Independent canonical reproduction | 0.7201 | 0.8302 | 0.5397 | 0.7464 | 0.1444 | 0.2185 |
| Independent research-copy reproduction | 0.7348 | 0.7931 | 0.5373 | 0.6354 | 0.1635 | 0.2706 |

Both independent reproductions match their respective recorded results.

## 3. Canonical V1 identity

The canonical artifact uses 14 numeric features, median imputation, standardization, and logistic regression with `max_iter=2000`, `random_state=42`. Its serialized model artifacts were loaded without retraining for the canonical reproduction.

## 4. Phase 3.6 research-copy identity

The Phase 3.6 runner refits a V1-compatible logistic model on `F + ['dominant_gpu_type']`. It therefore is not feature-equivalent to canonical V1, despite using the same row loader, nominal model family, and split files.

## 5–12. Identity reconciliation

The full required matrix is stored in `reconciliation_matrix.json`. Data source, processed data, row membership, numeric feature values, numeric scaling, and AUROC/AUPRC/Brier definitions match. Feature set, categorical encoding, fitted coefficients, calibration path, and ECE implementation do not match. The canonical model’s runtime calibration context is not reproduced by the raw Phase 3.6 copy.

| Component | Canonical V1 | Phase 3.6 Copy | Identical? | Impact |
|---|---|---|---|---|
| Dataset / rows | Official restored data and registered rows | Same | Yes | None |
| Features | 14 numeric | 14 numeric + `dominant_gpu_type` | No | Prediction/ranking changes |
| Preprocessing | Numeric median + standardization | Numeric preprocessing + one-hot category | No | Design matrix changes |
| Model | Serialized numeric-only LR | Refit LR in larger space | No | Coefficients/predictions change |
| Calibration | Canonical calibrated control context | Raw copy probabilities | No | Brier/ECE/risk differ |
| AUROC/AUPRC/Brier | sklearn definitions | Same definitions | Yes | None |
| ECE | Canonical reliability implementation | Copy’s 10 equal-width bins | No | ECE not directly comparable |

## 13–14. Independent reproductions

Canonical and Phase 3.6 copy reproductions match their respective historical numbers to recorded precision. This establishes reproducibility of both protocols, not equivalence of the protocols.

## 15. Gradient Boosting reconciliation

| Experiment | Random AUROC | Temporal AUROC | Identity |
|---|---:|---:|---|
| Phase 3.1 canonical candidate | 0.7472 | 0.3336 | Numeric features, learning rate 0.05, depth 2 |
| Phase 3.6-D research copy | 0.8070 | 0.2294 | Numeric features, learning rate 0.10, depth 3 |
| Independent Phase 3.1 reproduction | 0.7472 | 0.3336 | Matches Phase 3.1 configuration |
| Independent Phase 3.6-D reproduction | 0.8070 | 0.2294 | Matches Phase 3.6 configuration |

The GB discrepancy is explained by model configuration, specifically learning rate and maximum depth. It is not a split or metric discrepancy.

## 16. Root cause

The root cause is **protocol identity mismatch**: Phase 3.6’s logistic copy included `dominant_gpu_type` while canonical V1 is numeric-only, and Phase 3.6’s GB used a deeper, higher-learning-rate configuration than Phase 3.1. Calibration and ECE paths also differ for probability metrics.

## 17–19. Impact on Phase 3.6

**Phase 3.6-D: VALID BUT DIFFERENT PROTOCOL.** Its ladder is reproducible and scientifically useful as a comparison among the declared research copies, but it cannot be cited as a direct explanation of why canonical V1 is difficult to beat.

**Phase 3.6-C: VALID BUT DIFFERENT PROTOCOL / research-copy-specific.** The C ladder remains descriptive for the Phase 3.6 copy, but its absolute values are affected by the categorical feature mismatch and should not be relabeled as canonical V1 regularization evidence.

**Phase 3.6-E: REQUIRES BOUNDING, NOT DELETION.** The prior forensic conclusion must be narrowed: constrained linear structure remains a hypothesis supported by the broad temporal contrast, but the previous ladder did not hold feature space and all model identity dimensions constant against canonical V1.

## 20. Final scientific interpretation

The discrepancy is not a data or split failure. It is an expected protocol difference that was not explicitly reconciled before the Phase 3.6 comparisons. The correct interpretation is that Phase 3.6 produced valid non-equivalent research-copy evidence, while the direct canonical-V1 comparison claim is invalid without correction. No historical result is overwritten.

## 21. Limitations

The canonical V1 serialized artifact and the Phase 3.6 code path were reconciled; no new V1 training or optimization was performed. The original canonical control’s full calibration provenance is bounded by preserved artifacts. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recoverable from preserved evidence.

## 22. Required follow-up

Create a new reconciliation-controlled complexity study with exactly the frozen 14-feature V1 input space, matched model configuration declarations, and separate calibrated/raw metric reporting. Do not modify V1 or rewrite Phase 3.6 evidence.

**Primary classification: EXPECTED PROTOCOL DIFFERENCE.**
