# PHASE 3.1 — RELIABILITY MODEL RESEARCH REPORT

**Experiment:** `phase31_reliability_gradient_boosting_same_features_v1`

**Decision:** **REJECT** for V1.1 integration.

## 1. Research question

Can a model-only Gradient Boosting intervention improve workload-failure reliability relative to frozen V1 while maintaining calibration, early-warning usefulness, downstream safety, reproducibility, and practical cost?

## 2. Hypothesis

The null hypothesis was that the candidate would provide no meaningful improvement over V1 under the locked protocol. The alternative hypothesis was that the candidate would improve discrimination without unacceptable calibration, safety, or decision-time regression. The hypothesis and decision rule were written before final evaluation and were not changed after observing results.

## 3. V1 baseline

V1.0 is the immutable control at freeze commit `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. Its registered reliability artifact is a deterministic logistic-regression workload-risk model with train-fitted median imputation and standardization, validation-fitted isotonic risk calibration, and a locked accept-risk threshold of 0.1 in the runtime evaluation. V1’s historical seven skipped test-node identities remain unrecoverable from preserved evidence, while its data, protocol, focused validation, artifact behavior, restart behavior, and canonical 56-case evaluation are independently verified.

## 4. V1 reliability-model audit

| Contract item | Frozen V1 finding |
|---|---|
| Model | `EncodedWorkloadRiskModel` wrapping scikit-learn `LogisticRegression(max_iter=2000, random_state=42)` |
| Features | 14 numeric pre-outcome request/scheduling features |
| Feature ordering | `job_start_time`, `n_tasks`, `n_distinct_task_names`, `sum_inst_num`, `mean_plan_cpu`, `max_plan_cpu`, `mean_plan_mem`, `max_plan_mem`, `mean_plan_gpu`, `max_plan_gpu`, `n_distinct_gpu_types`, `n_instances`, `n_distinct_machines`, `mean_instance_start_time` |
| Preprocessing | Median imputation and standardization fit on training data only |
| Training | Alibaba GPU2020 main-tier jobs, job-disjoint registered random-stratified and temporal splits |
| Calibration | Validation-only isotonic regression on candidate/V1 risk scores |
| Threshold | Registered accept-risk threshold 0.1 for this comparison |
| Artifact | Versioned serialized model/calibrator with manifest, hashes, protocol and dataset identities |
| Runtime interface | Decision-time feature vector to failure-risk probability, confidence/margin, entropy, and downstream runtime metadata |
| Decision-time constraints | No target outcome, end time, post-failure fields, telemetry aggregates, runtime training, or test-set tuning |

## 5. Candidate selection rationale

The single candidate was `GradientBoostingClassifier` with 100 estimators, learning rate 0.05, maximum depth 2, and random state 42. It was selected because shallow additive tree boosting can represent nonlinear interactions among the same scheduling features while remaining classical, inspectable, deterministic under the declared seed, and computationally practical. The expected advantage was improved discrimination and probability ranking under heterogeneous resource combinations. Known risks were temporal instability, overfitting to the training distribution, and degraded probability calibration. No feature, split, memory, diagnosis, recovery, abstention, or safety intervention was combined with this model change.

## 6. Dataset and provenance

The experiment used the restored official Alibaba GPU2020 data state, the project’s publisher-checksum-verified archives, canonical preprocessing, seed-42 main-tier sampling, and registered random-stratified and temporal splits. No new data was created. The data verification record is [`data_verification.json`](../../../v1_control_reconciliation/reproduced_56_case/data_verification.json) in the Phase 3.0.2 reconciliation output, and the locked experiment protocol is [`protocol.json`](protocol.json).

## 7. Feature boundary

The candidate used exactly the 14 V1 numeric features listed in the audit table. No new temporal, telemetry, resource, rolling-window, interaction, categorical, memory, diagnosis, recovery, or safety features were added. The candidate’s feature-space identity is recorded as `feature_space_unchanged: true` for both splits.

## 8. Training protocol

For each registered split, the candidate preprocessing and model were fit on the training jobs only. The model was evaluated on validation to fit the isotonic calibrator, and the final evaluation partition was not used for model or calibration selection. The candidate was deterministic with seed 42. No hyperparameter sweep was performed. Software and protocol metadata are recorded in `protocol.json` and `manifest.json`.

## 9. Calibration protocol

The candidate raw failure-risk probabilities were calibrated using isotonic regression fit only on the registered validation partition. The same calibration treatment and locked threshold were used for both random-stratified and temporal evaluations. Raw and calibrated candidate metrics are both preserved in `results.json`; the comparison uses calibrated probabilities for the principal Brier, ECE, coverage, and selective-risk interpretation.

## 10. Evaluation protocol and metrics

The candidate and V1 control were compared on the same registered evaluation partitions. The declared metrics were AUROC, AUPRC, Brier score, ECE, log loss, coverage, selective risk, abstention behavior, artifact size/reproducibility, and downstream safety indicators. The existing reliability-model protocol does not provide a valid independent detection-lead-time measure for this model-only comparison, so no fabricated early-warning number is reported.

## 11. Results

| Split | Metric | V1.0 | Candidate | Delta (candidate − V1) | Interpretation |
|---|---|---:|---:|---:|---|
| Random-stratified | AUROC | 0.7201 | 0.7472 | +0.0271 | Candidate improves |
| Random-stratified | AUPRC | 0.5397 | 0.6149 | +0.0752 | Candidate improves |
| Random-stratified | Brier | 0.1444 | 0.1281 | −0.0163 | Candidate improves |
| Random-stratified | ECE | 0.0215 | 0.0083 | −0.0132 | Candidate improves |
| Random-stratified | Coverage at risk < 0.1 | Registered V1 value | 0.0918 | — | Candidate is conservative |
| Random-stratified | Selective risk | Registered V1 value | 0.0290 | — | Candidate accepted subset is low-risk |
| Temporal future | AUROC | 0.8302 | 0.3336 | −0.4966 | Severe regression |
| Temporal future | AUPRC | 0.7464 | 0.4154 | −0.3310 | Severe regression |
| Temporal future | Brier | 0.2185 | 0.3685 | +0.1500 | Regression |
| Temporal future | ECE | 0.2162 | 0.3374 | +0.1212 | Regression |
| Temporal future | Coverage at risk < 0.1 | Registered V1 value | 0.5658 | — | Candidate accepts a high-risk subset |
| Temporal future | Selective risk | Registered V1 value | 0.6259 | — | Unsafe decision-quality signal |

The complete metrics, reliability bins, bootstrap intervals, condition counts, and artifact hashes are in `results.json`. The random-stratified improvement is not sufficient because the temporal future holdout is a registered primary generalization check and the candidate fails it materially.

## 12. Statistical analysis

A deterministic bootstrap with 1,000 valid resamples and seed 314159 was used for candidate AUROC and AUPRC summaries. On the random-stratified split, candidate AUROC bootstrap mean was 0.7482 with 95% interval [0.7202, 0.7780], and AUPRC mean was 0.6155 with interval [0.5767, 0.6541]. On the temporal split, candidate AUROC bootstrap mean was 0.3332 with interval [0.3109, 0.3541], and AUPRC mean was 0.4156 with interval [0.3959, 0.4347]. These intervals describe candidate uncertainty; they do not convert the single locked comparison into a claim of statistical superiority.

The effect pattern is directionally inconsistent across splits: positive on random-stratified data and strongly negative on future temporal data. This is evidence of distribution-shift fragility, not a reliable improvement.

## 13. Downstream safety impact

The model-only candidate was not integrated into the production runtime or used to retune downstream policies. Its locked threshold behavior was evaluated through the existing abstention metric helper. No unsafe proposal or unsafe execution was introduced by the offline candidate artifact, and runtime training remained false. However, the temporal candidate selective risk of 0.6259 at the locked risk threshold is an unacceptable decision-quality warning: the candidate would accept a materially high-failure subset under the future distribution. This is sufficient to reject integration even without a measured unsafe-execution increase.

## 14. Reproducibility

Candidate model and calibrator artifacts were serialized separately for each split. Reloaded inference exactly matched the in-memory calibrated outputs for both splits. The model and calibrator SHA-256 values are recorded in `results.json` and `manifest.json`. The experiment output was finalized with `.finalized` and `finalized.json`; the runner refuses to overwrite a finalized experiment directory. The full locked protocol, results, summary, manifest, per-split artifacts, and environment are preserved in this directory.

## 15. Limitations

The candidate used one predeclared deterministic seed because the selected scikit-learn configuration is deterministic at the declared random state; no selective seed dropping occurred. The comparison is bounded to Alibaba GPU2020 job-level failure-risk prediction under the registered feature and split protocol. It does not establish production reliability, live telemetry prediction, autonomous recovery effectiveness, or generalization beyond the declared trace. The exact historical seven skipped test identities remain an archival limitation and are not inferred from current test counts.

## 16. Decision

# REJECT

The candidate is rejected for V1.1 integration. Although it improves random-stratified discrimination and calibration, it catastrophically regresses on the registered temporal future split, worsening AUROC, AUPRC, Brier score, ECE, and selective risk. The evidence therefore does not meet the predeclared requirement of meaningful multi-dimensional improvement without unacceptable generalization or decision-quality regression.

The negative result is preserved as a first-class Phase 3.1 finding. V1 remains unchanged. Final verification completed with **515 passed, 7 skipped, and 0 failed** across the full suite, including the three candidate unit tests.

## 17. Recommendation for next experiment

Do not integrate this candidate and do not retune it against the temporal test set. A follow-up may investigate explicitly predeclared temporal-robust model selection or feature-shift diagnostics, but that would be a new experiment with its own locked protocol. Any future candidate must preserve the same V1 feature/data boundary unless a later phase explicitly opens feature research.

## References

[1]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md "V1 reproducibility boundary and final readiness"

[2]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/experiments/results/reliability_runtime_v2/protocol.json "Registered V1 reliability runtime protocol"

[3]: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020 "Official Alibaba ClusterData GPU2020 source"
