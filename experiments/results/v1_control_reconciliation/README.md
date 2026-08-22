# V1 Control Reconciliation

This directory contains the Phase 3.0.1 reconciliation record for the frozen V1 control. It is separate from historical V1 evidence and contains no new improvement experiment.

| File | Purpose |
|---|---|
| `environment.json` | Repository, environment, command, duration, and data-availability record |
| `test_inventory.json` | Node-level inventory of all 17 current skips |
| `skip_reconciliation.json` | Historical 7-skip versus current 17-skip comparison |
| `focused_validation.json` | Exact 24-test focused validation result |
| `artifact_validation.json` | Serialized reliability-artifact and process-restart checks |
| `replay_status.json` | 56-case dependency graph and blocking reason |
| `README.md` | This manifest |

The historical V1 result remains preserved. The missing Alibaba GPU2020 processed inputs were not substituted, synthesized, downloaded under a different identity, or used to fabricate a replay.
