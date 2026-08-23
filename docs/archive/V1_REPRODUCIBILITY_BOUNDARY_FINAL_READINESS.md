# V1 REPRODUCIBILITY BOUNDARY & FINAL READINESS REPORT

**Phase:** 3.0.2 — V1 reproducibility closure and Alibaba data restoration

**Repository:** `NaishaShetty/Autonomous-AI-Infrastructure-`

**Final readiness:** **READY WITH DECLARED LIMITATION**

## Executive conclusion

The established Alibaba GPU2020 data environment was legitimately restored from the project-documented official endpoint. All seven source archives matched the publisher SHA-256 values recorded in the project manifest. The project’s existing canonical cleaning, power-analysis, seed-42 sampling, linked-record extraction, and split-generation pipeline then recreated the expected processed data state without changing V1 code, thresholds, artifacts, or evaluation definitions. The final full suite on the restored environment completed with **512 passed, 7 skipped, and 0 failed**; the seven remaining skips are the unrelated dataset-gated tests documented in the reconciliation inventory.

Using that restored data state, the canonical V1 runner completed **8 independent jobs × 7 declared conditions = 56 replay cases**. The new replay outputs are isolated under `experiments/results/v1_control_reconciliation/reproduced_56_case/`; the historical `experiments/results/alibaba_closed_loop_v2/` directory was restored after the runner’s write behavior was detected, and remains unchanged in the final working tree.

The exact historical seven skipped test identities remain **UNRECOVERABLE FROM PRESERVED EVIDENCE**. The repository preserves the historical aggregate 507 passed / 7 skipped / 0 failed result but not the node-level historical pytest report or release environment manifest. This limitation does not prevent a fair Phase 3.1 comparison because the V1 data state, protocol, 56-case evaluation, focused control, artifact behavior, and restart behavior are now independently verified. Phase 3.1 must nevertheless preserve the distinction between verified evidence and the unrecovered historical skip-node mapping.

## 1. Repository state

| Field | Result | Status |
|---|---|---|
| Starting commit | `2cd669c448a40dd5987f3cade326f816dc698e7a` | **VERIFIED** |
| Starting branch | `main` | **VERIFIED** |
| Starting `origin/main` | Same as starting commit | **VERIFIED** |
| Phase 3.0.1 checkpoint | `2cd669c Reconcile frozen V1 control baseline` | **VERIFIED** |
| Canonical V1 freeze | `d977a32c2f20efa5f8e0d0349d40b270ecabeca2` | **VERIFIED** |
| V1 runtime/code changes | None | **VERIFIED** |
| Final historical-result protection | Historical paths restored and excluded from final changes | **VERIFIED** |
| Final full suite on restored data | 512 passed / 7 skipped / 0 failed | **VERIFIED** in 582.27 seconds |

## 2. Historical skip investigation

The search covered tracked repository files, reachable Git history and refs, pytest sources and configuration, release and freeze documentation, benchmark reports, experiment manifests, candidate XML/HTML/JSON test reports, environment and dependency manifests, local generated artifacts, archived filenames, and references to the aggregate 507/7 result.

The search found the historical aggregate count and the current frozen-commit skip conditions. It did not find a preserved node-level historical pytest report, a seven-node skip list, a CI artifact, or a historical release environment/data manifest sufficient to identify the seven nodes.

**Historical seven-skip mapping: UNRECOVERABLE FROM PRESERVED EVIDENCE.** The seven nodes are not inferred from today’s 17. The full current inventory and the earlier reconciliation remain in [`experiments/results/v1_control_reconciliation/test_inventory.json`](../experiments/results/v1_control_reconciliation/test_inventory.json) and [`skip_reconciliation.json`](../experiments/results/v1_control_reconciliation/skip_reconciliation.json).

## 3. Alibaba data discovery and restoration

The expected processed files were absent from the Git checkout and from the project-local machine search. The project documentation explicitly states that raw and processed research data are ignored and intentionally not committed. The documented acquisition procedure identifies the official Alibaba ClusterData GPU2020 source and its README-linked OSS endpoint.

The seven archives were restored into the ignored local boundary `data/raw/alibaba_gpu2020/`:

```text
pai_job_table.tar.gz
pai_task_table.tar.gz
pai_instance_table.tar.gz
pai_sensor_table.tar.gz
pai_group_tag_table.tar.gz
pai_machine_spec.tar.gz
pai_machine_metric.tar.gz
```

The source endpoint was:

```text
https://aliopentrace.oss-cn-beijing.aliyuncs.com/v2020GPUTraces/
```

All seven downloaded SHA-256 values matched the existing project manifest. No alternative release, synthetic data, approximate copy, manually reconstructed table, or undocumented preprocessing was used.

## 4. Data provenance, checksums, and processed-table verification

The restoration followed the existing project procedure exactly:

```text
official Alibaba GPU2020 archives
        ↓
publisher SHA-256 verification
        ↓
data/raw/alibaba_gpu2020/
        ↓
clean_alibaba_job_task.py
        ↓
alibaba_power_analysis.py
        ↓
alibaba_stratified_sampling.py
        ↓
alibaba_extract_linked_records.py
        ↓
alibaba_build_splits.py
        ↓
data/processed/alibaba_gpu2020/
```

The complete verification record is [`data/audit/alibaba_gpu2020/restored_data_verification.json`](../data/audit/alibaba_gpu2020/restored_data_verification.json). It records source identity, archive identity, publisher checksums, preprocessing scripts, seed, sampling configuration, split configuration, processed-table SHA-256 values, schemas, row counts, and provenance.

| Processed table | Rows | Bytes | SHA-256 recorded |
|---|---:|---:|---|
| `job_table.clean.csv` | 1,055,501 | 141,676,614 | Yes |
| `task_table.clean.csv` | 1,261,050 | 123,637,406 | Yes |
| `task_table.main_sample.csv` | 11,750 | 1,166,053 | Yes |
| `instance_table.main_sample.csv` | 60,005 | 16,186,944 | Yes |
| `sensor_table.main_sample.csv` | 26,350 | 9,229,394 | Yes |
| `machine_metric.main_sample.csv` | 19,841 | 4,346,867 | Yes |

The main-tier sampling selected 10,000 terminal jobs with seed 42. The generated split reports show 6,999 random-stratified training jobs, 1,498 validation jobs, 1,503 evaluation jobs, and the registered temporal train/validation/Q4 future partition. The raw and processed data remain outside GitHub under the project’s existing data policy.

## 5. 56-case replay result

The canonical command was:

```text
python3 -m scripts.run_alibaba_closed_loop_v2
```

It completed with:

```text
experiment_id: alibaba_closed_loop_v2
unique_jobs: 8
conditions: 7
cases: 56
status: completed
```

The independent verification output is stored in [`reproduced_56_case/`](../experiments/results/v1_control_reconciliation/reproduced_56_case/), including the results, summary, protocol, manifest, trace, and data-verification record. The protocol hash is `e9d86edb5ae5f638ea80b422f3e8e5eb1cb2e7e0ce6ab1b9c2371b6166aa4881`. The reproduced summary preserves the registered condition-level safety, recovery, retrieval, diagnosis, abstention, persistence, and workload-risk fields.

The runner initially wrote two historical files under `experiments/results/alibaba_closed_loop_v2/`. This was detected immediately; the changed historical files and the audit identity file were restored from Git before finalization. No historical result modification is included in the checkpoint.

## 6. Focused 24-test result

The authoritative focused validation remains:

```text
python3 -m pytest -q \
  tests/integration/test_failure_memory_lifecycle.py \
  tests/integration/test_failure_memory_persistence.py \
  tests/integration/test_persistence_pipeline.py \
  tests/integration/test_startup_persistence.py \
  tests/runtime/test_closed_loop_runtime.py
```

Result: **24 passed / 0 failed / 0 skipped**. This is **VERIFIED**. The earlier 28-test subset is not used as a replacement.

## 7. Reliability artifact and restart validation

The V1 serialized reliability artifacts were independently validated for artifact loading, component hashes, compatibility checks, cross-process restart, identical model outputs, persisted-memory reload, and runtime training=false. The artifact behavior is **VERIFIED**. The canonical 56-case replay also used the registered artifact and preserved artifact identity in its case outputs.

## 8. Reproducibility matrix

| Evidence | Historical | Independently verified | Final status |
|---|---|---|---|
| Full V1 suite | 507/7/0 | 497/17/0 at frozen commit; 512/7/0 after Phase 3 additions and Alibaba restoration | Partially reconciled |
| Exact focused validation | 24/0/0 | 24/0/0 | **Verified** |
| Reliability artifact | Documented | Reproduced | **Verified** |
| Process restart | Documented | Reproduced | **Verified** |
| Historical skip IDs | 7 nodes | Not recoverable from preserved evidence | **Declared limitation** |
| Alibaba data provenance | Established | Restored with matching publisher hashes and canonical processing | **Verified** |
| Processed tables | Established but uncommitted | Restored and hash/schema/row-count recorded | **Verified** |
| 56-case replay | 56 cases | 56 cases completed with restored data | **Verified** |

## 9. Scientific implications

The V1 control is now independently reproducible for the registered Alibaba data/protocol evaluation. The final restored-data suite also recovers the aggregate skip count to seven, but the exact historical seven skip-node identities remain a metadata limitation because no preserved node-level historical report was found; the current seven must not be asserted to be the historical seven. Any Phase 3.1 comparison may use the restored data environment, frozen V1 implementation, registered artifact, registered protocol, and independently reproduced 56-case control.

Phase 3.1 must not claim that the historical seven skipped node IDs were recovered. It must preserve the distinction between the independently reproduced 56-case evaluation and the historical aggregate full-suite report. If future changes alter the data version, preprocessing, sample IDs, protocol, artifact, thresholds, or evaluation definition, they must be registered as a different control rather than described as the same V1 replay.

## 10. Final readiness decision

# READY WITH DECLARED LIMITATION

The remaining limitation is precisely bounded: the seven historical skipped node identities are unavailable from preserved evidence. The exact Alibaba data state was restored and verified, the canonical 56-case evaluation was independently reproduced, the focused validation passed, artifact behavior was reproduced, and historical V1 outputs remain protected. This satisfies the conditions for fair, explicitly scoped Phase 3.1 comparisons.

## 11. Phase 3.1 operating boundary

Phase 3.1 begins with the following V1 control package:

1. Frozen V1 implementation at the canonical freeze commit.
2. Official Alibaba GPU2020 archives matching the project’s recorded publisher checksums.
3. Canonical project preprocessing with seed-42 main-tier sampling and registered splits.
4. Registered reliability artifacts, calibration, thresholds, memory fixtures, and evaluation protocol.
5. Independently reproduced 8-job × 7-condition = 56-case evaluation.
6. Independently verified 24-test focused control and artifact/restart behavior.
7. Explicit declaration that the historical seven skipped test node IDs remain unrecoverable.

Every Phase 3.1 report must keep this limitation visible. It must not use substitute data, modify V1 to improve replayability, overwrite historical result directories, or describe the unrecovered seven-node mapping as known.

## References

[1]: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020 "Official Alibaba ClusterData GPU2020 source"

[2]: https://github.com/qzweng/clusterdata-cluster-trace-gpu-v2020-data "README-linked Alibaba GPU2020 data repository"

[3]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_FINAL_EVALUATION.md "V1 final integrated evaluation"

[4]: https://github.com/NaishaShetty/Autonomous-AI-Infrastructure-/blob/main/docs/V1_RELEASE_AUDIT.md "V1 release audit"
