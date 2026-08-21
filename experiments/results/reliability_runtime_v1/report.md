# Reliability Runtime v1 — Dataset Audit and Training Gate Report

## Executive conclusion

This phase asked whether a useful failure-risk model could be trained from appropriate operational data, calibrated without leakage, serialized with complete provenance, loaded by the canonical runtime, and evaluated for abstention safety. The repository contains detailed historical audits and adapters for Alibaba GPU2020, AIOps 2020, AgentRx, replay sources, and synthetic streams. However, the current checkout contains **none of the referenced `data/raw`, `data/processed`, or `data/audit` files**. The correct scientific outcome is therefore a **data-gate stop**: no model was trained, no reliability artifact was generated, and no performance, calibration, or abstention improvement claim is made.

> The absence of suitable local data is an experimental result and a stopping condition, not permission to substitute simulator records or frozen experiment outputs.

## 1. Dataset audit

The audit classified each candidate using the repository’s existing feasibility and protocol documentation, together with the source adapters. Alibaba GPU2020 is the strongest potential candidate for supervised failure-risk prediction because it has a job-level outcome and documented train/validation/test splits, but its decision-time feature set is primarily scheduling/specification information and several raw telemetry tables are explicitly prohibited because they contain lifetime aggregates. AIOps is useful for exploratory pre-failure anomaly detection and replay, but its current adapter does not join the time-series telemetry, the effective independent sample is entity-level, and the available fault labels are injected-fault labels. AgentRx is trajectory and diagnosis data without infrastructure telemetry, timestamps, or recovery outcomes. Synthetic episodic data is control evidence only.

| Candidate | Classification | Independent unit | Prediction suitability | Calibration suitability | Current decision |
|---|---|---|---|---|---|
| Alibaba GPU2020 | Potential A with complete raw data; B/C in this checkout | `job_name` | Potentially suitable using pre-outcome scheduling features and frozen splits | Potentially suitable with complete train/validation/evaluation data | Do not train; files absent |
| AIOps 2020 | B/C, exploratory only | Fault entity / `cmdb_id` | Possible only with strict pre-failure windows and joined telemetry | Weak; entity clustering and coverage limitations require exploratory interpretation | Do not train; files absent |
| AgentRx Magentic | C, replay/diagnosis only | `trajectory_id` | Not an operational telemetry prediction dataset | Not suitable for this milestone | Do not train |
| AgentRx τ-Retail | C, replay/diagnosis only | `trajectory_id` | Not an operational telemetry prediction dataset | Not suitable for this milestone | Do not train |
| Existing runtime replay sources | C, replay only | Source-defined identity | Depends entirely on supplied records and labels | Depends on an external labeled dataset | Use only after valid artifact exists |
| Phase 4 synthetic episodic stream | E, synthetic/control only | Synthetic episode/workload | Simulator-method validation only | Not transferable to operational calibration | Never use as real-data training evidence |

The adapter-level limitations are material. AgentRx labels and root-cause annotations are post-hoc and recovery is not observed. AIOps positive-window metadata does not itself provide the joined time-series feature frame. Alibaba’s adapter samples failed rows and exposes resource-plan fields, but a valid predictive training frame requires the complete raw source population, explicit split membership, pre-outcome feature extraction, and leakage exclusions. None of those raw files are available in the checkout.

## 2. Chosen dataset and justification

No dataset was selected for training. Alibaba GPU2020 is the **conditional future candidate** because the frozen protocol defines an independent job unit and both random-stratified and relative-time splits. It was not treated as available merely because its historical documentation exists. The current data-presence check found all candidate operational directories absent, so proceeding would violate the instruction to stop when leakage or data sufficiency cannot be established.

## 3. Prediction task

The declared task is: given decision-time observations at time `t`, predict whether a workload failure occurs within a dataset-supported horizon `H`. The observation window, horizon, positive event, negative event, censoring rule, feature availability time, and label availability time must be instantiated from the selected dataset before feature extraction. Since the required data files are absent, `H` and the final feature frame were not invented.

## 4. Temporal and leakage protocol

The implementation adds `src/reliability/evaluation.py`, which requires explicit split and independent-group fields, rejects groups crossing train/validation/evaluation boundaries, requires declared decision-time features, and rejects post-outcome fields such as future labels, post-failure state, outcome, or recovery results. The frozen dataset rules remain authoritative: Alibaba uses job-level and temporal/group-aware splits; AIOps uses pre-failure windows and entity-aware evaluation; AgentRx remains trajectory-disjoint and not a live telemetry prediction source.

No evaluation data may be used for feature selection, threshold tuning, calibration, horizon selection, or memory seeding. If those conditions cannot be proven, the training gate remains closed.

## 5. Baselines

The protocol defines a constant base-rate predictor, an observed-signal threshold detector, a simple logistic-regression model, and the existing runtime reliability implementation as baselines. The baseline hierarchy is intentionally conservative: no complex model is introduced before a simple supervised signal is demonstrated on an appropriate dataset.

## 6. Model

The intended model is the existing `src/reliability/workload_model.py` logistic-regression wrapper, not a parallel reliability stack. The runtime-compatible output remains a failure-risk/confidence assessment with model identity, artifact identity, timestamp/context, and provenance. No model object was created in this phase because the data gate failed.

## 7. Calibration

The existing calibrator now exposes `fit_train_calibration`, which separates classifier fitting from isotonic calibration on an explicitly supplied validation/development set. The compatibility `fit` method remains available for existing callers, but future research protocols should use the explicit train/calibration boundary. Planned metrics are Brier score, expected calibration error, reliability bins, and—where data support it—calibration slope/intercept.

No calibration metrics are reported because no calibration data were available.

## 8. Metrics

| Metric family | Result |
|---|---|
| AUROC / AUPRC | Not run; no training/evaluation frame |
| Brier score / log loss | Not run |
| Expected calibration error | Not run |
| Reliability diagram | Not generated |
| Failure detection metrics | Not evaluated on real data |
| Prediction metrics | Not evaluated |
| Runtime risk correspondence | Not established |

## 9. Abstention results

Coverage, selective risk, abstention rate, accepted-case failure rate, abstained-case failure rate, and unsafe-decision rate were not evaluated because no valid labeled evaluation set exists in the checkout. The existing runtime’s unconfigured abstainer remains a safety fallback, not an evaluated trained reliability policy.

## 10. Detection results

The existing detector remains separate from prediction and diagnosis. This phase did not alter the detector or reinterpret observed threshold violations as future failure-risk labels. No real-data detection result is claimed.

## 11. Prediction results

No prediction result exists. In particular, the phase does not convert the prior simulator smoke path, replay adapters, or frozen learning-influence outputs into model-performance evidence.

## 12. Runtime artifact integration

The artifact infrastructure remains available and was strengthened for this phase. Artifact creation now rejects overlapping training, validation, and evaluation dataset identities before serialization. Artifact loading can validate expected artifact, model, calibrator, and feature-schema versions. Invalid, missing, malformed, corrupted, incompatible, or leakage-violating artifacts are expected to fail safely; missing configuration continues to select the explicit abstaining runtime assessor rather than training at API startup.

No artifact was generated because training was correctly blocked.

## 13. Runtime trace evidence

The prior canonical smoke path remains valid as a bounded simulator integration proof. It demonstrates source provenance, detection, abstention, diagnosis, recovery, independent validation, and experience persistence. It does **not** demonstrate that a trained operational reliability artifact was consumed, because no such artifact exists in this phase.

## 14. Failure-mode tests

The artifact test surface covers valid round-trip loading, component hash validation, malformed/missing artifact handling, feature-schema mismatch, disjoint-dataset rejection, and safe no-training defaults. Version compatibility checks are now explicit in the loader API. A future data-backed experiment must add a corrupted-artifact and evaluation-data-leakage attempt to the experiment log before promotion.

## 15. Runtime overhead

No new inference benchmark is claimed. The implementation adds only deterministic validation and provenance handling around offline artifacts. A reproducible overhead measurement should be performed after a valid artifact is available, covering normalization, detection, inference, artifact loading, and provenance recording separately.

## 16. Reproducibility

The experiment runner is `scripts/run_reliability_runtime_v1.py`. It records the protocol SHA-256, repository commit, candidate data-directory presence, seed, software version, and data-gate status. The recorded protocol hash is `53e13b526892a74502d4ad38ff3f7ade86b568f4c0ee80bec4a6a9fea2a5d315`, and the run was made at repository commit `200b40fbbbbaed979929f104918e04d7e17af7f5`. Two repeated runs are only meaningful after the data gate is satisfied; the current runner is deterministic and produces no model artifact.

## 17. Frozen-path verification

The new experiment writes only to `experiments/results/reliability_runtime_v1/`. The following historical paths were not modified:

| Frozen path | Status |
|---|---|
| `experiments/results/learning_influence/` | Unchanged |
| `experiments/results/generalization/` | Unchanged |
| `experiments/results/counterfactual_generalization/` | Unchanged |
| `experiments/results/memory_composition/` | Unchanged |
| `experiments/results/memory_composition_v2/` | Unchanged |

## 18. Full test results

The complete suite after this phase recorded **486 passed, 17 skipped, and 0 failures**, with one existing FastAPI/httpx deprecation warning. The data-gate runner completed successfully with status `data_gate_blocked`; the canonical simulator smoke path also completed, but remains bounded simulator evidence rather than model evaluation.

## 19. Supported claims

The phase supports the following claims: the repository has a documented, explicit dataset suitability audit; the current checkout lacks the operational data required for training; the correct protocol behavior is to stop before training; the existing artifact boundary can represent provenance and reject invalid dataset/version conditions; and the new evaluation primitives express group-disjointness, feature-availability, calibration, and abstention requirements.

## 20. Unsupported claims

This phase does not support claims that a trained reliability model is useful, calibrated, superior to a baseline, predictive of operational failure, or safe for production decisions. It does not support a claim that replay or simulation is equivalent to live telemetry, and it does not support production self-healing.

## 21. Limitations

The principal limitation is data availability in the current checkout. Historical audit documents describe datasets that are not present as files. The remaining limitations are inherited from those audits: Alibaba machine-disjoint generalization is unresolved; AIOps has entity dependence, incomplete coverage, and injected faults; AgentRx lacks operational telemetry and timestamps; and no held real-data artifact can be loaded into the runtime.

## 22. Exact commit hash

This report records the pre-change baseline commit `200b40fbbbbaed979929f104918e04d7e17af7f5`. The final implementation commit must be recorded after validation and push.

## References

[1]: ../../docs/PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md "Frozen Phase 3 real-data feasibility audit"
[2]: ../../docs/PHASE3_REAL_DATA_PROTOCOL.md "Frozen Phase 3 real-data protocol"
[3]: ../../docs/RUNTIME_RELIABILITY_OBSERVABILITY_IMPLEMENTATION_REPORT.md "Runtime reliability and observability implementation report"
