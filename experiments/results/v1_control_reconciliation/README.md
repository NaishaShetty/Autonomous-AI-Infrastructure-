# V1 Control Reconciliation

This directory contains the Phase 3.0.1 reconciliation record for the frozen V1 control. It is separate from historical V1 evidence and contains no new improvement experiment.

| File | Purpose |
|---|---|
| `environment.json` | Repository, environment, command, duration, and data-availability record |
| `test_inventory.json` | Node-level inventory of all 17 current skips |
| `skip_reconciliation.json` | Historical 7-skip versus current 17-skip comparison |
| `focused_validation.json` | Exact 24-test focused validation result |
| `artifact_validation.json` | Serialized reliability-artifact and process-restart checks |
| `replay_status.json` | 56-case replay result and restored-data status |
| `reproducibility_boundary.json` | Permanent V1 reproducibility boundary and Phase 3.1 rules |
| `reproduced_56_case/` | Isolated canonical replay outputs, environment, trace, and data verification |
| `README.md` | This manifest |

The historical V1 result remains preserved. The Alibaba GPU2020 archives were restored from the project-documented official source, matched the recorded publisher checksums, and were processed with the canonical project pipeline. The independent 56-case replay is stored under `reproduced_56_case/`; no substitute data or fabricated replay was used. The historical seven skip-node identities remain unrecoverable from preserved node-level evidence.
