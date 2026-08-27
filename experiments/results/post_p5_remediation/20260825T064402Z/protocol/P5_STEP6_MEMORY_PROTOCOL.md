# Step 6 Protocol — Repeated-Incident Memory Evaluation (P5-W1, P5-W2)

Pre-registered BEFORE running the experiment. Addresses the P5 finding
that memory ON/OFF produced no observable difference in the original
evaluation because every episode used a unique `workload_id` — memory had
nothing to retrieve. This step does not attempt to "prove memory works"
by construction; it measures whether accumulated experience changes real
decisions under conditions where it legitimately could, and reports
honestly if it does not.

## Hypothesis

For a **repeated** incident (same `workload_id`, same `environment_id`,
same `failure_class`, across multiple episodes with real process restarts
between them), a persisted `FailureMemoryStore` lets
`RuleBasedRecoveryPlanner`'s existing avoidance rule (skip a candidate
action once it has accumulated `>= min_failures_before_avoidance` [= 2,
the existing default, unmodified] confirmed failures with zero successes)
switch from a declared-order-first action that keeps failing to a
different action that would succeed — and that this switch happens NO
episode earlier than the (2 prior failures + 1 current) it structurally
requires, and never happens at all under a memory condition that never
accumulates cross-episode evidence.

## Scenario

`RESOURCE_UNAVAILABLE` (`resource_unavailable` mode) against a **real,
persistently held port** (a real socket bound and listening in the
experiment script's own process, independent of any single
`ControlledRuntime` instance, held for the entire experiment — modeling a
genuinely externally-owned, still-down dependency, not a self-contended
one). This mode's action candidates are `(RETRY, RECONFIGURE,
ESCALATE_TO_HUMAN, ABSTAIN)`, declared in that order in
`src/phase4/recovery.py::_CANDIDATES` (unchanged, not reordered for this
experiment) — `RETRY` targets the same port and is expected to fail every
time the port stays held (per `controlled_runtime.py`'s own documented
"the reservation is real and does not expire on its own"); `RECONFIGURE`
picks a different, free port (`_reduced_parameters`, unchanged existing
code) and is expected to succeed every time.

## Conditions (both use the exact same scenario, workload_id, and port)

- **Memory ON:** a `FailureMemoryStore` backed by a real SQLite file on
  disk. Between every episode, the pipeline, runtime, and in-process Python
  objects are **fully torn down and reconstructed from scratch** (a new
  `AutonomyPipeline`, new `ControlledRuntime`, new `FailureMemoryStore`
  instance opened against the SAME file path) — this is what "restart"
  means here: no Python object survives between episodes, only the
  on-disk file does.
- **Memory OFF:** identical scenario and teardown/reconstruction between
  episodes, except each episode's `FailureMemoryStore` is a fresh
  `:memory:`-backed instance (the existing default when no path is given)
  — no episode can ever see any other episode's outcome, by construction.

6 episodes per condition, run sequentially (ON condition fully run and
recorded, then OFF condition fully run and recorded — not interleaved, to
avoid any accidental port-state coupling between conditions; each
condition uses its own separately-bound persistent port).

## Metrics

Per episode, per condition: chosen action, validation status
(`RECOVERED`/`NOT_RECOVERED`), and the `memory_version`/prior-evidence
count the planner's decision was based on. Decision-change rate (does the
chosen action ever differ from episode 1's) and the episode index of any
change.

## Persistence/restart/isolation checks (P5-W2)

Separately from the 6+6 episode comparison above: one standalone
before/after-restart check — write one record, fully destroy every Python
object and reopen the same file path, confirm the record is retrievable,
`memory_version` is preserved, and a query scoped to a DIFFERENT
`workload_id`/`environment_id` retrieves nothing (cross-run/cross-scope
isolation, exercising the existing contract already implemented in
`src/phase4/memory.py`, not new code).

## Stopping rule

6 episodes per condition, run exactly once each, no re-running with
different episode counts or thresholds after seeing a result. If memory ON
does not show a decision change by episode 3 (2 prior failures + the
current episode, the earliest the existing unmodified avoidance rule can
structurally trigger), or if memory OFF also shows a change, that is
reported as a failure of the hypothesis, not iterated on with a different
`min_failures_before_avoidance` value chosen after seeing the result.
