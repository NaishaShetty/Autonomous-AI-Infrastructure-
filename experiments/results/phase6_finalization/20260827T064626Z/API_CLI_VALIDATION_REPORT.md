# Phase 6.6 — API / CLI Demo Validation Report

## What was created

`scripts/demo_autonomy_loop.py` — drives ONE real episode through
`AutonomyPipeline.run_workload()` (`src/phase4/pipeline.py`) against this
project's own controlled subprocess runtime (`ControlledRuntime`,
`src/phase4/controlled_runtime.py`), printing each stage's real output:
observe, state history, predict, decide, diagnose, plan, safety-gate,
execute, validate, learn, final state.

## Actual captured output (real, not fabricated, from this session)

```
[observe]   workload_id=demo-workload-01 params={'mode': 'fail'}
[state]     RECEIVED -> OBSERVING -> PREDICTED -> DECIDING -> DIAGNOSING -> PLANNING -> SAFETY_CHECK -> EXECUTING -> VALIDATING -> NOT_RECOVERED -> COMPLETED
[predict]   prediction_score=0.09628362231445313
[decide]    decision=ANSWER
[diagnose]  primary_hypothesis=PROCESS_EXIT_FAILURE confidence=HIGH (class-matching only -- no independent causal ground truth)
[plan]      action=restart
[safety]    authorized=True reason=restart is SAFE and a declared candidate for PROCESS_NONZERO_EXIT; authorized
[execute]   real controlled-runtime execution: action_type=restart executed=True run_status=FAILED run_id=run-9009a424678642a68f7bd74120eda8fa note=re-invoked ControlledRuntime.run for restart
[validate]  independently-derived status=NOT_RECOVERED
[learn]     experience recorded=True memory_version=1
[final]     final_state=COMPLETED
```

**This scenario's recovery did not succeed** (`run_status=FAILED`,
`validate=NOT_RECOVERED`) — the deterministic `mode="fail"` scenario is a
guaranteed-failing workload used elsewhere in this project
(`scripts/run_phase4_5_pipeline_demo.py`'s own `recurring_failure`
episodes use the same mode), and this script does not cherry-pick a
different, always-succeeding scenario to make the output look better. The
pipeline still walks the full state machine to `COMPLETED` and correctly
records the outcome as `NOT_RECOVERED` rather than silently reporting
success.

## Other CLI/API surfaces re-verified this phase

- `python scripts/run_phase5_4_benchmark.py` — ran to completion,
  produced `experiments/results/phase5_benchmark_implementation/20260827T065455Z/`,
  `determinism_check` reported `{'task_results_identical': True,
  'ablation_results_identical': True, 'capability_matrix_identical': True,
  'split_assignments_identical': True}`, and its `capability_matrix`,
  `task_results`, and `ablation_results` were confirmed programmatically
  byte-identical to the frozen Phase 5.4 reference run
  (`experiments/results/phase5_benchmark_implementation/20260826T150824Z/`).
  This new timestamped directory is a Phase 6 verification artifact, not a
  new experiment — no metric, threshold, or label differs from the
  existing frozen reference.
- `python -m pytest tests/unit/test_phase54_benchmark.py -q` — **41
  passed** in 23.06s, this session.

## Defect found and fixed during this validation

The README's originally-drafted benchmark command,
`python -m src.benchmark.runner`, was tested directly and confirmed to do
nothing (`src/benchmark/runner.py` has no `__main__` guard: exit code 0,
zero output, zero files written). Corrected to
`python scripts/run_phase5_4_benchmark.py` in both `README.md` and this
report. See `README_AUDIT.md` for the full note.

## Conclusion

The CLI demo is real, runs against real project code, and reports its
actual (non-cherry-picked) outcome. The benchmark CLI entry point works
as documented after the correction above.
