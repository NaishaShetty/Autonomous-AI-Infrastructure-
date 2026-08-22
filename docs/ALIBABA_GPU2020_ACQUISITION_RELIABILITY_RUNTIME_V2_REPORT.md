# Alibaba GPU2020 Acquisition and Reliability Runtime v2

**Status:** Reproduced on top of the current `origin/main` history.
**Dataset:** Alibaba PAI GPU cluster trace 2020.
**Repository base:** `e2e88d9e8d95891a40757a008bf04b327d67df9a`.
**Protocol:** `experiments/results/reliability_runtime_v2/protocol.json`.

## Result

The official README-linked Alibaba GPU2020 data repository was reacquired, reconstructed, and verified against all seven publisher checksums. The raw archives are stored under the ignored, read-only boundary `data/raw/alibaba_gpu2020/`; processed tables are under `data/processed/alibaba_gpu2020/`. Raw data is intentionally not committed. Provenance and hashes are recorded in `data/audit/alibaba_gpu2020/dataset_manifest.json` and the identity audit.

The narrow data gate passed for predicting terminal `Failed` versus `Terminated` at the independent `job_name` level using pre-outcome request and scheduling features. The sensor and machine-metric tables were excluded because they are lifetime aggregates and are not available at the prediction point. The result does not support live telemetry prediction, diagnosis, recovery effectiveness, production readiness, or production autonomous self-healing.

## Provenance and data quality

The authoritative source is Alibaba’s official Cluster Trace Program GPU2020 README [1], published with the NSDI paper [2]. The official README-linked data repository [3] was used for split archive acquisition. The dataset-specific license is CC BY 4.0 [4]. The verified archive SHA-256 values are preserved in the manifest and audit utility.

The observed tables contain 1,055,501 jobs, 1,261,050 tasks, 7,522,002 instances, 3,033,232 sensor rows, and 2,009,423 machine-metric rows. There are 988,910 terminal jobs and 256,762 failed terminal jobs. Running and waiting jobs are right-censored and excluded. No malformed rows, negative planned resources, or schema mismatches were found by the streaming audit.

The canonical deterministic main-tier sample contains 10,000 terminal jobs. Random-stratified splits contain 6,999 train, 1,498 validation, and 1,503 evaluation jobs. Temporal splits contain 6,177 train, 1,324 validation, and 2,499 future evaluation jobs. Job identity is disjoint across all splits. A machine-disjoint split was not claimed because job-to-machine relations are many-to-many.

## Modeling protocol

The artifact model is deterministic logistic regression over 14 numeric scheduling-time features. Median imputation and standardization are fit on train only. Isotonic positive-failure-risk calibration is fit on validation only. The final test partitions are untouched for model and threshold selection. B0 is the train base-rate constant; B1 is the registered `max_plan_gpu` threshold; B2 is the supervised logistic model.

| Split | B0 AUROC / AUPRC | B1 AUROC / AUPRC | B2 calibrated AUROC / AUPRC | B2 calibrated Brier / ECE |
|---|---:|---:|---:|---:|
| Random-stratified | 0.500 / 0.259 | 0.394 / 0.229 | **0.720 / 0.540** | **0.144 / 0.021** |
| Temporal future | 0.500 / 0.434 | 0.262 / 0.389 | **0.830 / 0.746** | **0.219 / 0.216** |

These are point estimates on the registered evaluation splits. The temporal failure-rate shift from approximately 20.1% in train/validation to 43.4% in Q4 is reported explicitly; temporal calibration is consequently weaker and should not be generalized beyond the declared trace and protocol.

The abstention policy is conservative. Random evaluation coverage is 6.52% with selective risk 0.112; temporal coverage and selective-risk values are recorded in `results.json`. These are descriptive results under the registered threshold rule, not an operational cost-optimized policy.

## Artifact and runtime integration

Artifacts are saved under `experiments/results/reliability_runtime_v2/artifacts/{random,temporal}/`. Each contains model and calibrator components plus a manifest with model and calibrator versions, feature schema, train/validation/evaluation identities, protocol hash, repository commit, evaluation and calibration metrics, component hashes, and aggregate artifact hash. Both artifacts passed `TRAIN → SAVE → RELOAD → SAME INPUT → SAME OUTPUT`.

The replay proof is `scripts/run_reliability_runtime_v2_replay.py`, with trace at `experiments/results/reliability_runtime_v2/logs/runtime_replay.json`. It verifies dataset-replay provenance, structured detection provenance, artifact identity, confidence, risk, uncertainty, decision, episode identity, diagnosis, simulated recovery, validation, and experience persistence. Runtime construction loads an existing artifact only when configured; it never trains during API startup. The replay uses simulated detector/recovery components and is bounded evidence only.

A 50-observation local sandbox timing check reports a safe fallback median of approximately 0.165 ms and an artifact-loaded median of approximately 1.002 ms, for a local median delta of approximately 0.837 ms. This is not a production performance benchmark.

## Reproducibility and safety

The v2 runner uses seed 42, records dataset and protocol hashes, and preserves the current repository commit. Re-running the deterministic training/evaluation path produces identical metrics and component behavior. Historical result paths under `experiments/results/learning_influence/`, `generalization/`, `counterfactual_generalization/`, `memory_composition/`, and `memory_composition_v2/` remain untouched. Raw and processed data remain ignored and are not staged.

The supported claim is limited to: **the declared scheduling-time failure-risk model and artifact-loaded runtime path were validated on Alibaba GPU2020 under the registered job-level temporal/entity leakage-safe protocol.** No claim of production readiness, general real-world reliability, or production autonomous self-healing is made.

## References

[1]: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020 "Alibaba Cluster Trace Program GPU2020 README"

[2]: https://www.usenix.org/conference/nsdi22/presentation/weng "Weng et al., MLaaS in the Wild, USENIX NSDI 2022"

[3]: https://github.com/qzweng/clusterdata-cluster-trace-gpu-v2020-data "Official README-linked Alibaba GPU2020 data repository"

[4]: https://raw.githubusercontent.com/alibaba/clusterdata/master/cluster-trace-gpu-v2020/LICENSE "Alibaba GPU2020 dataset license"
