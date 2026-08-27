# Final System Check — Step 7

Covers the mandatory checklist from the master remediation register's
"FINAL COMPLETE SYSTEM CHECK" section. Each item states what was actually
done, what evidence supports it, and — where a check is a review of
already-implemented/already-tested mechanisms rather than a new
experiment — says so plainly rather than implying new work occurred.

## 1-4. Test suites, repeated runs

- New remediation tests: all pass (see each step's report for individual
  confirmation — Steps 1-6 each ran their own new tests to green before
  moving on).
- Full Phase 4 test suite: passes as part of the full repository suite
  below (no separate Phase-4-only run was needed; the full suite includes
  every Phase 4 test).
- Full repository suite: run **8 times** across this remediation phase
  (`full_run2` through `full_run8` in the working session), the first few
  during Steps 1-3, the last four specifically during Step 7 verification.
  Final clean result: **837 passed, 0 failed** (53 min, fully isolated,
  no competing load). Three of the four Step 7 runs surfaced genuine,
  distinct defects (documented in `ADDENDUM_CPU_TIMING_DEFECT.md` and
  `ADDENDUM_TIMESTAMP_TIE_DETERMINISM_DEFECT.md`) that were root-caused
  and fixed, not suppressed or waited-out.
- Repeated runs under timing/RNG suspicion: performed extensively during
  the timestamp-tie investigation (the same 15-seed reproduction was run
  3+ times before and after the fix, specifically to distinguish real
  nondeterminism from a one-off).

## 5. Test-order independence check

Full suite run with **reversed directory order**
(`tests/unit tests/runtime tests/recovery tests/e2e tests/integration`
instead of the default alphabetical
`tests/e2e tests/integration tests/recovery tests/runtime tests/unit`)
— chosen because the most severe defect found this phase (the
timestamp-tie nondeterminism) manifested specifically when many
`AutonomyPipeline`/`AgentTaskRuntime` calls accumulated on shared
instances across a long run, making cross-file/cross-order state leakage
the most plausible remaining order-sensitivity to check for.

First attempt used an incomplete directory list (missed `tests/e2e` and
`tests/recovery`, an error in constructing the check itself — caught by
comparing `--collect-only` counts, 771 vs. the expected 837, before
trusting the result) and surfaced one real, but separate, finding: a test
(`test_router_produces_a_real_prediction_score_for_a_predictable_mode_run`)
asserted diagnosis follow-through without accounting for the pipeline's
legitimate `ABSTAIN`-skips-diagnosis design — fixed, not an engineering
defect (see `reports/ADDENDUM_ABSTAIN_SKIPS_DIAGNOSIS_TEST_GAP.md`).

**Result with the corrected, complete reversed-order run (837/837 tests
collected, confirmed matching the default-order count): 837 passed, 0
failed** (1h03m53s). Test-order independence confirmed.

## 6. Temporal leakage audit

Reviewed (not newly built — this audit verifies existing, already-tested
discipline):
- `rolling_checkpoints` (`prediction.py`) constructs every checkpoint
  prefix from events at-or-before that checkpoint's own timestamp,
  excluding the run's own `failure_detected` event by construction —
  verified by `test_rolling_checkpoints_never_include_the_runs_own_failure_event`.
- `run_agent_task`'s prediction-boundary cut (the exact line fixed this
  step) constructs `prediction_prefix` from events at-or-before the
  failure boundary, never after — the `<=` fix widened inclusion up to
  the boundary, never past it; verified by the new
  `test_prediction_prefix_includes_a_sample_that_ties_the_failure_events_own_timestamp`
  regression test.
- `FailureMemoryStore.retrieve` enforces `recorded_at <= at_or_before`
  (contract item 2, `memory.py`) — verified in Step 6's restart/
  persistence check and by the pre-existing memory contract test suite.
- Step 3/4's train/validation/test splits use disjoint, non-overlapping
  seed ranges throughout (verified by direct construction in each
  protocol document) — no test-split seed was ever used for training or
  calibration in any step this phase.

## 7. Cross-run contamination audit

- `FailureMemoryStore.retrieve` explicitly excludes the querying episode's
  own `run_id` (contract item 1) — this is the exact mechanism verified
  directly in Step 6's memory experiment (memory ON correctly never used
  the CURRENT episode's own outcome, only genuinely prior episodes').
- `ControlledRuntime`/`AgentTaskRuntime` each construct a fresh `run_id`
  (`uuid4`-based) per `.run()` call — collision-astronomically-unlikely,
  and every event carries its owning `run_id`/`job_id` explicitly.

## 8. Cross-environment contamination audit

- Step 4's three environments (`baseline_cpu`/`memory_constrained`/
  `dependency_network_constrained`) each construct an independent
  `ControlledRuntime` with their own `environment_id`; the frozen model
  was fit ONLY on `baseline_cpu` data and evaluated zero-shot elsewhere —
  verified directly by the protocol's own construction (`generate_dual_corpus_for_environment`
  is called once per environment with that environment's own config) and
  by Step 4's reported per-environment metrics never mixing populations.
- `FailureMemoryStore.retrieve` scopes by `environment_id` as well as
  `workload_id` (contract item 1) — same mechanism as cross-run isolation
  above, shared code path.

## 9. Provenance audit

Every canonical event emitted by `controlled_runtime.py` and
`agent_runtime.py` carries a `provenance` dict (`source`,
`source_version`, `extraction_method`, `transformation`,
`transformation_version`, `timestamp_source`, `timestamp_quality`) and a
`schema_version` — unchanged, pre-existing discipline, confirmed still
intact by direct inspection of events captured during this phase's
reproductions (e.g. the seed=27/44 event traces captured while debugging
the timestamp-tie defect all carried full provenance blocks). The new
GPU probe states (Step 2) and resource pre-flight probe (Step 2) both
carry their own explicit provenance fields (`gpu_probe_state`, `forced`,
`probe_version` / `resource_available`), extending the existing
convention rather than deviating from it.

## 10. Safety audit

- `AutonomyPipeline`'s safety gate (`self.gate.authorize(action, diagnosis)`)
  is called before every execution in both `run_workload` and
  `run_agent_task`, and execution is skipped whenever authorization is
  denied OR the decision was REVIEW/ABSTAIN — unchanged this phase, still
  enforced (see `pipeline.py`'s `if not authorized or decision.decision
  not in ("ANSWER", "RETRY"): ... no execution`).
- `is_unsafe()` checks in `recovery.py` are unchanged; no new action type
  was added this phase, so no new safety-classification surface was
  introduced.
- Every new capability added this phase is either read-only telemetry
  (GPU probe, resource pre-flight probe, RSS/CPU/memory sampling) or an
  opt-in, explicitly-labeled test-only override (`force_gpu_state`) that
  production/evaluation code paths never set — confirmed by `grep` for
  `force_gpu_state` across `src/` (only appears in the definition and in
  test files, never in any script under `scripts/`).

## 11. Memory persistence/restart audit

Performed as Step 6's dedicated experiment — see
`reports/MEMORY_REMEDIATION_REPORT.md`. Not repeated here.

## 12. Replay determinism audit

`test_restart_and_persistent_replay_are_identical`
(`tests/unit/test_phase412_controlled_runtime.py`) and Step 6's own
`restart_persistence_check` (memory-specific) both directly verify replay
identity across a real store close/reopen. No replay-determinism defect
was found this phase; the timestamp-tie defect found was a
**live-decision** nondeterminism (which decision a fresh run makes), not
a replay-of-recorded-events nondeterminism (replaying the SAME already-
recorded events was never shown to differ) — an important distinction
stated explicitly since the two are easy to conflate.

## 13. Prediction negative-control audit

Performed throughout Step 3 (shuffled-label controls for every
family/variant, `_stable_seed`-derived, now process-independent per the
Step 1 fix) and referenced in Step 5 (temperature-scaling calibration
candidate, evaluated on a held-out calibration split only). No prediction
result in this remediation phase was reported without an accompanying
shuffled-control comparison where a real/shuffled distinction was
meaningful (Steps 3, 4).

## 14. Calibration leakage audit

Every threshold calibration in this phase (`calibrate_threshold`, Steps
3/4; the sentiment temperature fit, Step 5) was fit on a validation/
calibration split disjoint from both train and test, and never re-fit
after seeing a test-split result — verified directly by each step's
protocol document specifying the split before running, and by direct
code reading of `calibrate_threshold`'s signature (`val_rows`, never
`test_rows`) and `run_p1_step5_sentiment_uncertainty.py`'s temperature
fit (`calibration` split only, `test` split used only for the final,
unfitted evaluation of all 4 candidates).

## 15. Final V1 frozen-control integrity audit

`src/phase3_contract.py` states explicitly: *"This module is deliberately
independent of the frozen V1 runtime."* Confirmed by direct `git status`
inspection: **every file modified or added during this entire remediation
phase lives under `src/phase4/`, `scripts/` (new Phase-4-specific
scripts), `tests/*/test_phase4*` or `tests/*/test_p{1,3,4,5}_step*`, or
`requirements.txt`** (three new library pins: `torch`, `transformers`,
`psutil` — none of which alter any existing V1 code). No file under
`src/phase3_contract.py`, any V1-tagged runtime module, or any other
frozen-control artifact was touched.
