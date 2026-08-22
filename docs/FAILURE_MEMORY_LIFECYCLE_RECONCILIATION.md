# Failure-Memory Lifecycle Reconciliation

## Diagnosis before changes

The current `origin/main` baseline produced 499 passing tests, 7 skips, and 5 failures. Four failures are in `tests/runtime/test_closed_loop_runtime.py`; one is in `tests/e2e/test_full_pipeline.py`.

The four runtime failures are contract mismatches plus one incomplete implementation detail:

| Failure | Diagnosis |
|---|---|
| Recovered episode reports `learning_update.updated == False` | `RuntimeLearningManager` correctly calls `ingest(..., rebuild=True)`, but `FailureMemory.rebuild()` promotes `_version` without updating the public `_memory_version`, fit count, timestamp, or pending count. The update is performed but its observable version remains stale. |
| Unsafe recovery path reports `learning_update.updated == False` | The same stale public-version bookkeeping defect occurs after a confirmed detected failure whose recovery is rejected by the safety gate. |
| `ingest()` leaves `memory_version == 0` after synchronous rebuild | `rebuild()` and `fit()` contain inconsistent metadata promotion. `fit()` updates `_memory_version`; `rebuild()` does not. The intended synchronous path is present, but its observable state is incomplete. |
| Dirty-memory query is expected to raise | The legacy test encodes an older contract. The active lifecycle tests require a previously valid model to remain serviceable after a failed rebuild while marked dirty, so the old assertion must be reconciled to the current atomic-promotion contract rather than restoring an unsafe query prohibition. |
| API test cannot force a confirmed failure | The current API deliberately builds an unconfigured safe runtime that abstains because API startup must not train. The test assumes the older trained synthetic default and is outdated relative to the current serving contract. It must assert safe abstention/no memory mutation, while trained-pipeline persistence is covered separately by lifecycle and restart tests. |

## Contract decision

The implementation is not reverted to a store-equals-learn model. The intended lifecycle remains:

```text
STORE → MARK DIRTY → REBUILD → VALIDATE → ATOMICALLY PROMOTE → SERVE
```

A successful synchronous rebuild must update all public version/bookkeeping fields. A failed rebuild must preserve the last valid active model, retain the dirty marker, and allow a later explicit retry. The API default must remain an abstaining, no-startup-training configuration when no artifact is supplied.

Tests are changed only where they encode the obsolete contract. New regression coverage will assert metadata promotion, atomic failure behavior, safe API fallback, process restart, and explicit real-data integration ordering.
