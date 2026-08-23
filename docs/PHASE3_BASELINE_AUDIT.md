# PHASE 3 BASELINE AUDIT

**Status:** Phase 3.0 infrastructure checkpoint

**Scope:** Independent repository audit, V1.0 control verification, and preparation of isolated V1.1 experiment infrastructure. No V1.1 improvement experiment was run.

## 1. Repository state

| Item | Status | Finding |
|---|---|---|
| Repository | **VERIFIED** | `NaishaShetty/Autonomous-AI-Infrastructure-` |
| Branch | **VERIFIED** | `main` |
| HEAD | **VERIFIED** | `d977a32c2f20efa5f8e0d0349d40b270ecabeca2` |
| `origin/main` | **VERIFIED** | Same commit as `HEAD` at audit time |
| Working tree before implementation | **VERIFIED** | Clean; no staged, modified, or untracked files |
| Historical paths before implementation | **OBSERVED** | Present with committed protocol, manifest, result, summary, report, and per-seed artifacts |

The implementation in this checkpoint adds only Phase 3 bookkeeping, contract, documentation, tests, and reserved `experiments/results/v1_1/` directories. It does not alter the frozen V1 runtime or historical result directories.

## 2. Freeze verification

The documented V1 freeze commit is `[d977a32](https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/commit/d977a32c2f20efa5f8e0d0349d40b270ecabeca2)`. The repository matched that commit and `origin/main` before changes. The clean-state condition was therefore **VERIFIED at the start of Phase 3.0**. After this checkpoint, the working tree is intentionally non-clean because it contains the new Phase 3 changes; the frozen commit itself remains unchanged.

## 3. Test status

| Validation | Historical V1 expectation | Phase 3.0 observation |
|---|---:|---|
| Full suite before Phase 3 changes | 507 passed, 7 skipped, 0 failed | **OBSERVED:** 497 passed, 17 skipped, 0 failed in 216.35 seconds |
| Compilation | Passed | **VERIFIED:** `python3 -m compileall -q src tests` |
| Diff check | Passed | **VERIFIED:** `git diff --check` after implementation |
| Repository hygiene | Clean at freeze | **OBSERVED:** clean before implementation; expected Phase 3 changes afterward |
| Full suite after Phase 3 changes | 507 passed, 7 skipped, 0 failed | **VERIFIED:** 502 passed, 17 skipped, 0 failed in 300.23 seconds; the five added tests passed |
| New contract tests | Not applicable | **VERIFIED:** 5 passed |

The full-suite discrepancy is recorded rather than hidden. A Phase 3.0.1 detached-worktree run at the frozen V1 commit also produced 497/17, proving that the five Phase 3 additions are not the cause. The exact current 17 skips are all dataset-gated, but the historical seven skipped node IDs were not preserved in the repository; the historical mapping therefore remains **UNKNOWN**. No tests were changed to obtain the observed result. See the [V1 Control Reconciliation Report](V1_CONTROL_RECONCILIATION_REPORT.md).

## 4. Focused validation status

The V1 release documentation records 24 focused integration and persistence tests passing with zero failures [1]. The repository contains the corresponding closed-loop, Alibaba integration, failure-memory lifecycle, persistence, restart, safety, and runtime test modules. The exact historical 24-test core selection was recovered and independently reproduced with 24 passed, 0 failed, and 0 skipped; this is **VERIFIED**. The previous 28-test subset is not treated as equivalent.

The exact focused selection covering failure-memory lifecycle, persistence, startup restart, and closed-loop runtime collected 24 tests and produced **24 passed, 0 failed, 0 skipped**; this is **VERIFIED**. The new Phase 3 serialization, manifest, deterministic-identifier, and immutability tests are **VERIFIED** by the 5-test unit run above.

## 5. V1 reproduction status

The historical V1 integrated evaluation is documented as 8 independent jobs, 7 conditions, and 56 replay cases, with zero unsafe execution and conservative safety behavior [1] [2]. The historical artifact and runner references are present in the repository. The serialized artifacts and process-restart behavior are independently **VERIFIED**. The established Alibaba GPU2020 archives were restored from the project-documented official endpoint, all seven publisher checksums matched, the canonical preprocessing pipeline recreated the processed tables, and the canonical 56-case replay completed. The new replay is isolated under `experiments/results/v1_control_reconciliation/reproduced_56_case/`; the historical result remains unchanged. See [V1 REPRODUCIBILITY BOUNDARY & FINAL READINESS REPORT](V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md).

## 6. Current reliability model

The reliability path is **OBSERVED** from the implementation and audit documents. V1 uses a serialized reliability artifact containing a model, calibrator, feature schema, version identifiers, dataset identities, protocol information, metrics, and hashes. The documented runtime behavior is artifact loading with compatibility validation, explicit safe fallback when no artifact is available, no API-startup training, and same-process/process-restart validation. The model is not replaced or retuned in Phase 3.0.

The current data boundary is also **OBSERVED**: the Alibaba GPU2020 source is a research/evaluation source, not the project’s public dataset. Dataset provenance, split, calibration, and artifact identity must be declared in every future contract; unavailable local raw-data details remain **UNKNOWN** until data setup is performed.

## 7. Current runtime architecture

The canonical V1 composition is:

```text
OBSERVATION → FAILURE DETECTION → WORKLOAD RELIABILITY MODEL
→ RELIABILITY UNCERTAINTY → ABSTENTION DECISION
→ FAILURE MEMORY RETRIEVAL → MEMORY-DERIVED RISK
→ DIAGNOSIS → RECOVERY PLANNING → SAFETY GATE
→ CONTROLLED RECOVERY EXECUTION → INDEPENDENT VALIDATION
→ FAILURE EXPERIENCE → PERSISTENCE / MEMORY UPDATE
```

This separation is **VERIFIED as the documented architecture**. Workload failure risk, memory risk, reliability uncertainty, diagnosis uncertainty, and abstention decision remain distinct concepts; the Phase 3 contract does not introduce a generic replacement risk variable.

## 8. Current evaluation protocol

The V1 protocol is a bounded replay composition using the serialized artifact, observation and detection, workload-risk prediction, failure-memory retrieval, diagnosis, abstention, safety-gated controlled recovery, independent validation, and experience persistence [1]. Supported claims are limited to coherent composition and bounded scientific evidence. Production reliability, real-world autonomous recovery, broad generalization, operational deployment safety, and production readiness are **not established** by V1.

## 9. Dataset inventory

| Dataset/source | Purpose | Boundary and status |
|---|---|---|
| Alibaba GPU2020 | Research/evaluation reliability and closed-loop replay | **OBSERVED:** research/evaluation source; not the project’s public dataset |
| AIOps KPI | Real-data audit/evaluation path | **OBSERVED in test gating:** local marker may be absent; exact local availability is **UNKNOWN** |
| AgentRx | Real-data audit/evaluation path | **OBSERVED in test gating:** local marker may be absent; exact local availability is **UNKNOWN** |
| Synthetic V1 fixtures | Unit/integration/runtime testing | **OBSERVED:** repository test infrastructure; not evidence of production performance |

For each future experiment, source, raw/derived status, license/provenance, split, training use, calibration use, evaluation use, and redistribution status are mandatory metadata. Public dataset packaging is outside Phase 3.0.

## 10. Artifact inventory

**Verified repository artifacts** include frozen V1 experiment protocols, manifests, results, summaries, reports, per-seed outputs, reliability-runtime artifacts, and historical phase outputs. The new contract module uses canonical JSON and SHA-256; it never uses Python `hash()` for scientific identifiers. A finalized experiment contains `protocol.json`, `manifest.json`, `results.json`, `summary.json`, `report.md`, optional `per_seed/`, and a `.finalized` digest marker. Finalization is write-once and rejects later overwrites.

## 11. Historical experiment verification

The following historical directories were present before implementation and remain outside the new V1.1 tree:

```text
experiments/results/learning_influence/
experiments/results/generalization/
experiments/results/counterfactual_generalization/
experiments/results/memory_composition/
experiments/results/memory_composition_v2/
```

Their contents were not edited. This is **OBSERVED** from the pre-change Git state and the scoped implementation diff; a post-commit hash manifest should be used for any future independent audit.

## 12. Existing experiment infrastructure

The repository already provides reusable runners, benchmark scripts, JSON protocols and manifests, per-seed result serialization, metric implementations, artifact loading, leakage audits, and report files. Phase 3.0 adds a small generic layer rather than duplicating or refactoring that working V1 code:

* `src/phase3_contract.py` provides the required field contract, canonical serialization, deterministic identifiers, manifest validation, and immutable finalization.
* `configs/phase3_evaluation_contract.json` freezes the split, leakage, randomness, metric, scientific-template, and decision rules.
* `experiments/results/v1_1/` provides isolated category directories without speculative results.
* `tests/unit/test_phase3_contract.py` tests the new infrastructure.

## 13. V1 limitation inventory

The following are evidence-backed research questions, not claims of production weakness:

| Area | Evidence-backed limitation or uncertainty |
|---|---|
| Reliability | The current full-suite result differs from the historical documented count; cause requires environment/data reconciliation. |
| Features | The audited V1 feature boundary is fixed; whether additional non-leaking temporal features improve prediction is not yet tested under the locked contract. |
| Calibration | Calibration behavior is documented, but comparative calibration alternatives have not been run in Phase 3.0. |
| Abstention | V1 demonstrates conservative abstention behavior in bounded replay; its behavior outside that protocol is unknown. |
| Memory | Retrieval-order and conflicting-memory safety are documented for the bounded cases; broader memory distributions are not established. |
| Diagnosis | Diagnosis is composed in the replay, but independent generalization beyond the declared protocol is unknown. |
| Recovery | Recovery is controlled/simulated; real-world recovery safety is not established. |
| Robustness | Robustness to distribution shift and adversarial or noisy conditions requires separately locked experiments. |
| Evaluation | The 56-case result is bounded composition evidence and was not independently replayed here because local real-data availability is unresolved. |

## 14. Phase 3 experiment contract

Every future experiment must declare the 15 fields in `configs/phase3_evaluation_contract.json`, including hypothesis, frozen baseline, single intervention, dataset identity/version, split, feature set, model, calibration, seed, evaluation protocol, metrics, software version, and artifact identity. It must produce the standard artifacts where applicable and preserve negative results. The final test remains locked, model selection occurs on validation data, and metric definitions cannot change after candidate results are viewed.

## 15. Proposed first V1.1 hypothesis

**HYPOTHESIS:** Under the frozen V1 data boundary, split definitions, calibration protocol, and evaluation metrics, a justified classical candidate reliability model may improve calibrated failure-risk prediction relative to the V1 model without increasing unsafe downstream decisions. The first experiment should compare one candidate intervention at a time, with Logistic Regression as the initial candidate only if the baseline audit confirms compatible inputs and artifact interfaces.

This is a **PROPOSED** hypothesis, not an experimental result. No candidate model was trained or evaluated in Phase 3.0.

## 16. Phase 3.1 readiness decision

**READY WITH DECLARED LIMITATION.** The historical seven skipped node IDs are **UNRECOVERABLE FROM PRESERVED EVIDENCE**, but the established Alibaba data state was restored with matching publisher checksums, canonical preprocessing, and verified processed-table identity. The exact 24-test focused validation, serialized artifact/restart behavior, and canonical 56-case replay are independently verified. Phase 3.1 may proceed only under the explicit boundary in [V1 REPRODUCIBILITY BOUNDARY & FINAL READINESS REPORT](V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md).

Phase 3.0.2 formally closes the remaining reproducibility questions. Phase 3.1 may begin with the independently reproduced 56-case control, but must not claim that the historical seven skip identities were recovered or infer them from today’s 17.

## 17. Phase 3.4 calibration, uncertainty, and abstention readiness

Phase 3.4 was completed as an additive research layer around the frozen V1 control. The actual V1 calibration implementation was audited before intervention: the Alibaba risk path uses validation-fitted isotonic calibration with clipped probability output. One alternative, Platt scaling, was evaluated without changing V1. It worsened Brier score and ECE on both random-stratified and temporal future evaluation and was rejected.

Bootstrap model-variability uncertainty was the only uncertainty method tested. Higher uncertainty identified materially higher error rates, particularly on the temporal future population, so the finding is retained as **INTERESTING FINDING** rather than accepted integration. A validation-locked 80th-percentile uncertainty abstention rule retained meaningful coverage but increased temporal selective risk and was rejected. The single combined Platt-plus-uncertainty policy was also rejected. No Phase 3.4 component modifies V1 or enters production.

The full Phase 3.4 synthesis and immutable experiment records are stored under `experiments/results/v1_1/calibration_abstention/`. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed remains preserved; the exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

**Phase 3.4 readiness decision: V1 remains the sole production-eligible control.** A future study may investigate distribution-robust uncertainty across multiple pre-registered temporal folds, but any successful component must remain additive and undergo a separate consolidation experiment.

## 18. Phase 3.5 distribution-robust uncertainty readiness

Phase 3.5 constructed three additional research-only chronological future folds after a 40% warm-up. The unchanged nine-member bootstrap/model-variability estimator from Phase 3.4-B showed positive high-versus-low uncertainty error separation on all three folds. The signal is therefore retained as a robust diagnostic finding across the tested regimes.

The single pre-registered abstention policy, using the fold-validation 80th uncertainty percentile with a 0.50 minimum coverage gate, failed as an actionable control: it improved risk on one fold, degraded risk on two folds, and fell below the coverage gate on the first fold. The overall result is **NON-ACTIONABLE / HOLD** as research evidence. No Phase 3.5 component modifies V1 or enters production.

The complete fold definitions, per-fold results, policy analysis, plots, and immutable records are stored under `experiments/results/v1_1/distribution_robust_uncertainty/`. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed remains preserved; the exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

**Phase 3.5 readiness decision: V1 remains the sole production-eligible control.** A future phase may study safety-constrained use of diagnostic uncertainty across additional forward folds, but must create a new experiment ID and preserve the frozen V1 boundary.

## 19. Phase 3.6 V1 robustness and mechanism forensics readiness

Phase 3.6 was completed as a forensic-only additive study. Five isolated records were created under `experiments/results/v1_1/v1_forensics/`: data/evaluation forensics, feature forensics, coefficient/regularization forensics, a controlled model-complexity ladder, and a cross-temporal synthesis.

The evidence partially explains the random-versus-temporal behavior. The canonical populations differ in prevalence and feature distributions, and the controlled ladder shows the tested flexible alternatives improving or matching interpolation while failing on the temporal population. Feature ablations and coefficient analysis do not identify a single dominant feature or prove causality. Duplicate and group findings remain forensic cautions, not leakage claims. The result is classified as **partially genuine, dataset-dependent, and evaluation-dependent robustness; overall unresolved in causal mechanism**.

**Phase 3.6 readiness decision: HOLD as a bounded forensic conclusion.** V1 remains byte-for-byte/behaviorally frozen and remains the sole production-eligible control. No feature removal, coefficient update, calibration change, threshold change, runtime change, or V1.1 integration was performed. The historical aggregate V1 result of 507 passed / 7 skipped / 0 failed remains preserved; the exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

## 20. Phase 3.6.1 baseline identity and protocol reconciliation readiness

Phase 3.6.1 reconciled the numerical discrepancy between canonical V1 and the Phase 3.6 research-copy results. The canonical V1 metrics were independently reproduced by applying the preserved isotonic calibrators to the preserved numeric-only V1 model artifacts: random AUROC 0.7201 and temporal AUROC 0.8302. The Phase 3.6 copy was independently reproduced at random AUROC 0.7348 and temporal AUROC 0.7931.

The root cause is an **expected protocol difference**. Canonical V1 uses 14 numeric features, while the Phase 3.6 research-copy logistic model adds one-hot `dominant_gpu_type`. The Phase 3.6 copy also reports raw probabilities, while canonical Brier/ECE results use preserved calibrated outputs. The Gradient Boosting discrepancy is separately explained by configuration: Phase 3.1 uses learning rate 0.05 and maximum depth 2, while Phase 3.6-D uses learning rate 0.10 and maximum depth 3.

**Phase 3.6.1 readiness decision: canonical V1 remains unchanged.** Phase 3.6-D and 3.6-C are valid but non-equivalent research protocols; their comparisons must not be represented as direct canonical V1 reproductions. Phase 3.6-E’s mechanism conclusion is bounded accordingly. All prior evidence remains immutable, and the exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

## 21. Phase 3.6.2 matched-feature complexity and inductive-bias readiness

Phase 3.6.2 held constant the official Alibaba GPU2020 data, registered random/temporal rows, exact 14-feature numeric V1 matrix, train-only median imputation and standardization, validation-only isotonic calibration, and metric definitions. The frozen V1 control reproduced at random AUROC 0.7201 and temporal AUROC 0.8302. The Phase 3.1 Gradient Boosting configuration reproduced at 0.7472 random and 0.3336 temporal AUROC under the matched feature contract.

The matched ladder showed that the controlled C=0.1 linear variant remained close to V1, the predeclared limited-interaction model improved temporal AUROC to 0.8439, while the constrained Random Forest and matched Phase 3.1 Gradient Boosting collapsed temporally to 0.3204 and 0.3336. The evidence is therefore **diagnostically supportive but not sufficient for V1.1 integration**: flexible nonlinear alternatives can fail under the registered temporal shift, but the small interaction result prevents a universal claim that added expressiveness is harmful.

**Phase 3.6.2 readiness decision: HOLD as a bounded inductive-bias study.** V1 remains unchanged and remains the sole production-eligible control. No ladder candidate was integrated, and all prior evidence remains immutable. The exact seven historical skipped test-node identities remain unrecoverable from preserved evidence.

## 23. Phase 3.7 V1.1 candidate discovery and design

Phase 3.7 completed an evidence-grounded candidate discovery and design pass without modifying V1 or screening candidates on future-fold results. Five candidate categories were investigated: structured uncertainty/evidence request, distribution context, provenance-aware failure memory, constrained model disagreement, and explicit structured decision policy. Based on accumulated evidence, Candidates A and C were selected for future screening; no candidate was accepted or integrated.

The selected protocols freeze the canonical V1 control, matched 14-feature data contract, canonical temporal test, and all three Phase 3.5 chronological folds. They prohibit hyperparameter search, feature fishing, test-set selection, and future-fold tuning. The design-only outcome is **V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET**, with a primary **RELIABILITY/DECISION ARCHITECTURE** direction around frozen V1. The full inventory, selection record, protocols, and report are stored under `experiments/results/v1_1/candidate_discovery/3_7/`.

No candidate-specific experiment was executed in Phase 3.7; prior Phase 3 results are not relabeled as candidate results. The current full-suite attempt ran from `2026-08-23T08:51:32Z` to `2026-08-23T08:56:32Z`, reached approximately 49%, and timed out with exit code 124 while CPU-bound; it is recorded as incomplete rather than successful. The inherited verified 558-passed / 7-skipped result remains distinct. V1 remains the sole production-eligible control, and the historical seven skipped-node identities remain unrecoverable.

## References
[1]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_FINAL_EVALUATION.md "V1 final integrated evaluation"

[2]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_RELEASE_AUDIT.md "V1 release audit"

[3]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/calibration_abstention "Phase 3.4 calibration, uncertainty, and abstention evidence"

[4]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/PHASE3_BASELINE_AUDIT.md "Phase 3 baseline audit"

[5]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/distribution_robust_uncertainty "Phase 3.5 distribution-robust uncertainty evidence"

[6]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/v1_forensics "Phase 3.6 V1 robustness and mechanism forensics evidence"

[7]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/v1_forensics/3_6_1_baseline_reconciliation "Phase 3.6.1 baseline identity and protocol reconciliation evidence"

[8]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity "Phase 3.6.2 matched-feature complexity and inductive-bias evidence"

## 22. Phase 3.6.3 multi-temporal inductive-bias validation

Phase 3.6.3 extended the matched 14-feature complexity ladder across all three pre-registered authoritative chronological folds from Phase 3.5. The frozen V1 control, C=0.1 linear variant, limited-interaction model, constrained Random Forest, and matched Gradient Boosting configuration were evaluated with training-fitted median imputation and standardization, validation-only isotonic calibration, and unchanged AUROC/AUPRC/Brier/ECE definitions. No model, threshold, feature set, or protocol component was selected using future-fold results.

The limited-interaction model's Phase 3.6.2 temporal advantage did not persist consistently. Relative to V1, its AUROC delta was -0.0032 on Fold 1, -0.0718 on Fold 2, and +0.0123 on Fold 3: one AUROC win and two losses, with mean delta -0.0209 and worst-case delta -0.0718. Its corresponding AUPRC deltas were -0.0009, -0.1234, and +0.0468. The result is therefore **PARTIAL VALIDATION / REGIME-SENSITIVE**, not evidence of a temporally robust improvement. The three-fold evidence specifically rejects promoting the interaction model on the basis of the single canonical temporal split.

**Phase 3.6.3 readiness decision: HOLD.** V1 remains frozen and remains the sole production-eligible control. The interaction model and all other ladder candidates remain research-only; no feature, model, calibration, threshold, runtime, or integration change was made. The complete protocol, fold-level metrics, predictions, plots, report, and immutable SHA-256 finalization record are stored under `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/`. The historical aggregate V1 result and the unrecoverable historical seven skipped-node identities remain unchanged.

[9]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/tree/main/experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation "Phase 3.6.3 multi-temporal inductive-bias validation evidence"

## 24. Phase 3.8 Candidate A and Candidate C experimental screening

Phase 3.8 independently screened the two candidates selected in Phase 3.7. Candidate A preserved frozen V1 predictive outputs and added a deterministic, bounded evidence-request/escalation action layer. Candidate C added prior-only, provenance-aware failure-memory context without modifying V1 training or inference. The candidates were not combined.

Candidate A tied V1 on AUROC and AUPRC across the canonical random population, canonical temporal population, and all three Phase 3.5 future folds. This preserved predictive robustness but did not demonstrate a measurable operational safety benefit sufficient to justify the added policy; Candidate A is therefore **HOLD**. Candidate C produced three AUROC wins and two losses across the five populations, with mean AUROC delta `+0.00193` but mixed future-fold behavior and worst future-fold delta `-0.00020`. The small mixed effect did not establish robust temporal or safety benefit; this concrete implementation is **REJECTED**.

The final Phase 3.8 decision is **BOTH CANDIDATES REQUIRE FURTHER STUDY**. V1 remains frozen and remains the strongest validated control under the tested conditions. No V1.1 integration or Phase 3.9 consolidation is authorized. The complete protocols, per-population results, candidate reports, leakage audits, plots, synthesis, and immutable SHA-256 records are stored under `experiments/results/v1_1/candidate_screening/3_8/`.

The current full repository suite was attempted from `2026-08-23T09:10:29Z` to `2026-08-23T09:15:29Z`, reached approximately 48%, and timed out with exit code `124` while CPU-bound. This is recorded as an incomplete current run; the inherited verified result of 558 passed and 7 skipped remains distinct. Phase 3.8 focused tests passed with 8 tests, alongside compilation, diff, leakage-boundary, historical-path, and hash verification.

## 25. Phase 3.9 V1 decision-failure and information-gap forensics

Phase 3.9 analyzed frozen V1 decisions across the canonical random-stratified population, canonical temporal population, and Phase 3.5 Folds 1–3. The deterministic forensic definition was an incorrect V1 threshold decision at 0.5, with risk, calibrated risk, uncertainty, case identity, population, fold, and decision-time feature values retained. No error classifier, candidate model, feature search, or V1 modification was performed.

The failure taxonomy found 1,180 high-confidence errors and 1,523 low-confidence errors across the evaluated population-case records. High-confidence errors represented 43.66% of classified errors and were present in all evaluated populations; low-confidence errors represented 56.34% and were strongly concentrated in temporal populations. These categories are descriptive, not causal, and the population-case accounting intentionally preserves each registered evaluation boundary.

Cross-fold feature signatures were mixed. `n_tasks`, `n_distinct_task_names`, `mean_plan_mem`, and `max_plan_mem` showed directionally consistent exploratory associations across the canonical temporal population and Folds 1–3. Timing and CPU/GPU workload variables changed direction or magnitude materially and were classified as **UNSTABLE**. Therefore no universal causal failure mechanism was established.

The information-gap analysis classified V1 risk/workload inputs as decision-time and already used by V1; prior-failure similarity as potentially available but expensive and leakage-sensitive; final outcomes and future telemetry as post-outcome; and unavailable runtime context as unknown. The resulting architectural conclusion is **V1 FAILURE MECHANISM REMAINS UNRESOLVED**. No V1.1 integration is authorized. Any next study should first add rigorously timestamped observability/context instrumentation and test one narrow hypothesis across the existing future folds.

The complete case-level taxonomy, information-gap matrix, univariate and cross-fold signatures, opportunity map, plot, synthesis, and immutable SHA-256 records are stored under `experiments/results/v1_1/failure_forensics/3_9/`. The current full-suite attempt ran from `2026-08-23T09:24:11Z` to `2026-08-23T09:29:11Z`, reached approximately 48%, and timed out with exit code `124` while CPU-bound; the inherited 558-passed / 7-skipped result remains distinct.
