# PHASE 3.2 — TEMPORAL GENERALIZATION & FEATURE STABILITY REPORT

**Repository:** `NaishaShetty/Autonomous-AI-Infrastructure-`

**Phase:** 3.2

**Decision:** **REJECT** the tested intervention for V1.1 integration; preserve the findings and continue research only with a newly locked protocol.

## 1. Research question

Why does the reliability signal generalize differently under random-stratified and temporal evaluation, and can future-distribution robustness be improved without sacrificing V1’s reliable behavior?

## 2. Phase 3.1 findings

The frozen V1 logistic model achieved AUROC 0.7201 and AUPRC 0.5397 on the random-stratified evaluation and AUROC 0.8302 and AUPRC 0.7464 on the temporal future evaluation. The Phase 3.1 Gradient Boosting candidate improved the random-stratified metrics to AUROC 0.7472 and AUPRC 0.6149, but failed on the temporal future evaluation with AUROC 0.3336, AUPRC 0.4154, Brier score 0.3685, ECE 0.3374, and selective risk 0.6259. It was rejected, and its complete negative result remains immutable at [`gradient_boosting_same_features_v1/`](../reliability_model/gradient_boosting_same_features_v1/).

## 3. Stage A methodology

The audit used the established restored Alibaba GPU2020 data state, the canonical feature builder, the registered random-stratified and temporal splits, and the preserved V1 and Phase 3.1 candidate artifacts. It did not alter data, splits, features, thresholds, calibration, V1 artifacts, or historical results. Distribution shift was quantified with standardized mean difference, Kolmogorov–Smirnov statistic, Wasserstein distance, and population stability index. These measures jointly distinguish location shift, distributional separation, and bin-stability movement. Feature-target drift was assessed with univariate AUROC and Spearman association changes. Model behavior was assessed through probability ranges, error rates, time quartiles, risk buckets, V1 standardized coefficients, and Gradient Boosting feature importances.

The machine-readable Stage A record is [`stage_a_audit.json`](stage_a_audit.json).

## 4. Population comparison

The principal population difference is not a random-sampling artifact. The temporal future evaluation contains 2,499 jobs and has a failure prevalence of 0.4342, compared with 6,999 random-stratified training jobs at 0.2595 and 1,503 random-stratified test jobs at 0.2588. The future rate is 0.1747 higher than training, a 67.3% relative increase. The temporal train population contains 6,177 jobs and the temporal validation population 1,324 jobs.

| Population | Jobs | Failure rate | Time range |
|---|---:|---:|---:|
| Random train | 6,999 | 0.2595 | Recorded in audit JSON |
| Random validation | 1,498 | 0.2597 | Recorded in audit JSON |
| Random test | 1,503 | 0.2588 | Recorded in audit JSON |
| Temporal train | 6,177 | 0.2595 | Recorded in audit JSON |
| Temporal validation | 1,324 | 0.2598 | Recorded in audit JSON |
| Temporal future test | 2,499 | 0.4342 | Recorded in audit JSON |

The future population is later in time and materially more failure-prone. Prevalence shift can affect precision-recall and calibration, but it cannot by itself establish the cause of the AUROC collapse; feature and feature-target drift provide additional evidence.

## 5. Feature distribution shift

The complete 14-feature table is in `stage_a_audit.json`. The strongest shift is in the two clock-time features: `job_start_time` and `mean_instance_start_time` both have standardized mean difference approximately 1.5734 and KS statistic 1.0000 between temporal training and future evaluation. Their time ranges are disjoint by construction of the registered temporal split. The next strongest shifts are resource-planning features: `max_plan_cpu` has standardized mean difference −0.3870, KS 0.3160, and PSI 0.6084; `mean_plan_cpu` has standardized mean difference −0.3808, KS 0.3156, and PSI 0.6019; and both GPU planning features have PSI approximately 0.3563.

| Feature | Standardized mean difference | KS statistic | PSI | Stability |
|---|---:|---:|---:|---|
| `job_start_time` | 1.5734 | 1.0000 | 0.0000* | Strongly shifted |
| `mean_instance_start_time` | 1.5734 | 1.0000 | 0.0000* | Strongly shifted |
| `max_plan_cpu` | −0.3870 | 0.3160 | 0.6084 | Strongly shifted |
| `mean_plan_cpu` | −0.3808 | 0.3156 | 0.6019 | Strongly shifted |
| `max_plan_gpu` | −0.2109 | 0.2215 | 0.3563 | Strongly shifted |
| `mean_plan_gpu` | −0.2105 | 0.2215 | 0.3563 | Strongly shifted |
| `n_distinct_task_names` | −0.1683 | 0.0674 | 0.0369 | Moderately shifted |
| `n_tasks` | −0.1683 | 0.0674 | 0.0369 | Moderately shifted |
| `sum_inst_num` | −0.1027 | 0.1084 | 0.0477 | Moderately shifted |
| `n_instances` | −0.0970 | 0.1252 | 0.0501 | Moderately shifted |
| `n_distinct_machines` | −0.0949 | 0.1207 | 0.0473 | Moderately shifted |
| `n_distinct_gpu_types` | 0.0457 | 0.0085 | 0.0043 | Stable |
| `max_plan_mem` | −0.0135 | 0.0622 | 0.0787 | Stable |
| `mean_plan_mem` | −0.0002 | 0.0685 | 0.0399 | Stable |

*The PSI implementation uses train-quantile bins; the disjoint clock-time ranges produce a degenerate bin geometry, so the KS statistic and standardized mean difference are the decisive indicators for those two features rather than the zero PSI value.

## 6. Feature stability

The audit classifies six features as strongly shifted, five as moderately shifted, and three as stable under the declared combined criteria. The classification is descriptive, not a claim that every shifted feature is causal. In particular, the clock-time features are direct markers of the temporal boundary, while CPU and GPU planning features show material distribution movement and may encode a changing workload mix.

## 7. Feature-target relationship drift

Feature distributions and feature-target relationships both change. The largest univariate AUROC losses occur for `mean_plan_cpu` (0.4978 in temporal training to 0.1866 in the future test), `max_plan_cpu` (0.4819 to 0.1846), `mean_instance_start_time` (0.5033 to 0.2207), and the two GPU planning features (approximately 0.4832 to 0.3266). Their Spearman associations also move substantially, with `mean_plan_cpu` changing from −0.0036 to −0.5745 and `max_plan_cpu` from −0.0317 to −0.5870. These observations support relationship drift rather than prevalence shift alone. They do not prove a causal mechanism.

## 8. Model behavior analysis

On the random evaluation, V1’s independently refit diagnostic model had uncalibrated AUROC 0.7143 while GB had 0.7359; GB error rate was 0.1690 versus V1’s 0.2681. On the temporal future evaluation, V1 had AUROC 0.7817 and GB 0.2661 in the diagnostic refit, with error rates 0.4342 and 0.4350 respectively. GB’s random-test feature importance was concentrated in `mean_plan_cpu` (0.3214), `max_plan_cpu` (0.2482), and `job_start_time` (0.1342), precisely among the features exhibiting strong temporal movement. V1’s largest standardized coefficients were assigned to `mean_plan_mem`, `sum_inst_num`, `n_instances`, and `max_plan_cpu`, so V1 is not shift-free; its simpler functional form nevertheless retained substantially better temporal ranking.

GB’s temporal probabilities were compressed toward low risk and its calibrated future accepted subset had selective risk 0.6259 at the locked threshold. This is consistent with a model whose learned relationships do not transfer to the future population. The audit does not claim that GB extrapolation alone explains the failure; the evidence supports the combined mechanism of covariate shift plus relationship drift interacting with GB’s nonlinear reliance on CPU/time structure.

## 9. Error stratification

The complete time-quartile and risk-bucket error stratification is preserved in `stage_a_audit.json`. The key pattern is that GB’s temporal future probability ranking is poor across the full evaluation population rather than being limited to a cherry-picked subgroup: its future AUROC is 0.2661 in the diagnostic model and 0.3336 in the locked Phase 3.1 result. The candidate’s high-risk acceptance behavior is especially problematic because the locked threshold accepts a future subset with selective risk 0.6259. V1’s future diagnostic AUROC remains 0.7817, showing that the temporal failure is not an unavoidable property of the evaluation data.

## 10. Evidence-backed failure mechanisms

The strongest supported mechanism is **temporal covariate shift combined with feature-target relationship drift**. Future time features are disjoint from temporal training, CPU and GPU planning distributions shift materially, and CPU planning relationships reverse or strengthen in the future data. A second supported mechanism is **model sensitivity to unstable nonlinear structure**: GB’s random-test importance is concentrated in shifted CPU/time features, while its future ranking collapses. A third possibility is calibration transfer failure, because candidate future ECE is 0.3374, but calibration drift is not sufficient as the primary explanation because the uncalibrated GB AUROC also collapses to 0.2661. These are evidence-backed hypotheses, not causal identification.

## 11. Selected intervention

Stage B selected one intervention: **feature-stability filtering**. The two clock-time features, `job_start_time` and `mean_instance_start_time`, were removed because they had KS statistic 1.0 and standardized mean difference approximately 1.57 between temporal training and future evaluation. This intervention was selected from Stage A distribution evidence before running the intervention; no future labels, test metric, threshold, or repeated search was used to choose it. The remaining 12 V1 features, V1 preprocessing, registered splits, validation isotonic calibration, and locked threshold were unchanged.

## 12. Experimental protocol

The intervention used the restored official Alibaba GPU2020 data, canonical preprocessing, seed 42, the registered random-stratified and temporal splits, and validation-only isotonic calibration. It was compared directly with frozen V1 and, for context, the rejected Phase 3.1 GB result. Results are stored under [`stable_feature_filtering_time_features/`](stable_feature_filtering_time_features/). No V1 or Phase 3.1 artifact was overwritten.

## 13. Results

| Split | Metric | V1 | Stability-filtered candidate | Delta vs V1 |
|---|---|---:|---:|---:|
| Random-stratified | AUROC | 0.7201 | 0.7105 | −0.0096 |
| Random-stratified | AUPRC | 0.5397 | 0.5090 | −0.0307 |
| Random-stratified | Brier | 0.1444 | 0.1486 | +0.0042 |
| Random-stratified | ECE | 0.0215 | 0.0110 | −0.0105 |
| Random-stratified | Coverage | Registered V1 value | 0.0645 | — |
| Random-stratified | Selective risk | Registered V1 value | 0.1031 | — |
| Temporal future | AUROC | 0.8302 | 0.7286 | −0.1016 |
| Temporal future | AUPRC | 0.7464 | 0.6175 | −0.1289 |
| Temporal future | Brier | 0.2185 | 0.2905 | +0.0720 |
| Temporal future | ECE | 0.2162 | 0.2550 | +0.0389 |
| Temporal future | Coverage | Registered V1 value | 0.0220 | — |
| Temporal future | Selective risk | Registered V1 value | 0.0364 | — |

The intervention improved neither random nor temporal discrimination relative to V1. It reduced temporal coverage sharply and improved the accepted subset’s failure rate, but that is not sufficient to justify integration because it did so by abstaining on 97.8% of future cases while losing substantial ranking and probabilistic quality.

## 14. Random versus temporal comparison

The intervention did not validate the simple hypothesis that removing the two clock-time features would restore temporal robustness. It improved temporal AUROC relative to the rejected GB candidate (0.7286 versus 0.3336) but remained materially below V1 (0.8302), while temporal AUPRC and Brier score also worsened relative to V1. The result indicates that clock-time distribution shift is real but not the sole cause of the GB failure. Removing those features also removes signal that V1 uses successfully under the locked temporal protocol.

## 15. Safety impact

The intervention was evaluated offline through the existing abstention metrics and was not integrated into the runtime or used to retune safety policy. No unsafe proposal or unsafe execution was introduced by the offline artifact. Nevertheless, the candidate’s temporal coverage of 0.0220 means it abstains almost universally under the locked threshold. This is an operational and decision-quality regression, not an acceptable safety improvement. The rejected GB’s temporal selective risk of 0.6259 remains an important negative comparator.

## 16. Reproducibility

The Stage A audit and Stage B intervention are stored as immutable, machine-readable outputs. Candidate model and calibrator artifacts reload with identical predictions, runtime training remains false, and finalized hashes are recorded under `stable_feature_filtering_time_features/`. The experiment uses deterministic seed 42 and no hidden hyperparameter search. The full V1 suite and focused control were preserved; the historical V1 seven-skip node identities remain unrecovered from preserved evidence.

## 17. Limitations

This is one controlled intervention and cannot identify all causes of temporal generalization failure. The temporal test labels were used for locked audit and final evaluation, not intervention tuning, but the analysis cannot establish causality. The data is bounded to Alibaba GPU2020 and the project’s registered job-level protocol. Early-warning lead-time metrics are not supported by the existing V1 protocol and are therefore not fabricated. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed is preserved, but the exact seven historical skipped test-node identities were not recovered from preserved evidence. The V1 data state, protocol, artifact, focused validation, restart behavior, and canonical 56-case evaluation were independently verified.

## 18. Decision

# REJECT

Reject the tested stability-filtering intervention for V1.1 integration. It did not improve temporal generalization over V1: temporal AUROC fell by 0.1016, AUPRC by 0.1289, Brier score worsened by 0.0720, ECE worsened by 0.0389, and coverage collapsed to 2.2%. The result is scientifically useful because it rules out removal of the two clock-time features as a sufficient fix and confirms that the GB failure cannot be repaired by this single filter alone.

V1 remains frozen, the Phase 3.1 GB result remains rejected, and both negative results are preserved.

## 19. Next research question

Can a predeclared distribution-aware training or robust-model-selection intervention address the observed CPU/GPU relationship drift while preserving V1’s temporal discrimination, calibration, and operational coverage without tuning on the temporal test set?

## References

[1]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md "V1 reproducibility boundary and final readiness"

[2]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/experiments/results/reliability_runtime_v2/protocol.json "Registered V1 reliability runtime protocol"

[3]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1/report.md "Phase 3.1 rejected Gradient Boosting experiment"

[4]: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020 "Official Alibaba ClusterData GPU2020 source"
