# Addendum — Test Assumption Gap: ABSTAIN Legitimately Skips Diagnosis (Step 7)

Found while re-running the (corrected) test-order independence check.
**Not an engineering defect** — the pipeline behaved exactly as designed;
one test's assertion didn't account for a legitimate, intentional code
path.

## What happened

`test_router_produces_a_real_prediction_score_for_a_predictable_mode_run`
(`tests/integration/test_phase45b_prediction_scope_router_pipeline.py`)
asserted `result.diagnosis is not None` unconditionally after running a
clear, unambiguous `cpu` timeout (`duration_seconds=0.4` against
`timeout_seconds=0.15`). It failed with `diagnosis` being `None`.

Root cause: `pipeline.py::run_workload` (and `run_agent_task`, already
covered by a similar fix earlier this phase) has an explicit, deliberate
early-return when the decision layer's calibrated policy chooses
`ABSTAIN`: *"no diagnosis attempted, per DECIDING->ABSTAINED being a
direct allowed transition"* — diagnosis is only attempted when the
pipeline has decided to trust the prediction enough to act on it at all.
This is correct, intentional architecture (abstention as a first-class
outcome), not a bug.

The specific test trains a fresh `PredictionScopeRouter` from a real,
auto-widened (per `ADDENDUM_CPU_TIMING_DEFECT.md`'s fix) corpus each time
it runs, so its calibrated threshold has some real run-to-run variability.
For some calibration outcomes, a genuinely clear timeout can still land in
the ABSTAIN band. The test's assertion was simply too strong — asserting
diagnosis follow-through as if it were guaranteed, when the pipeline's own
design says otherwise.

## Fix

Relaxed the assertion: diagnosis follow-through is checked only when
`result.decision.decision != "ABSTAIN"`. The test's actual core claim — a
real, well-formed prediction score was produced — remains asserted
unconditionally and was never the part that failed.

Verified: 3 consecutive full-file reruns, all passing (some runs abstain,
some don't; both are now correctly treated as valid).

## Why this wasn't caught earlier

This is the same class of gap fixed earlier in
`test_high_disagreement_wrong_answers_are_escalated_or_abstained_not_silently_autonomous`
and `test_default_pipeline_mostly_escalates_wrong_answers_to_review_matching_phase45b_finding`
(both in the agent-task path) — but this occurrence is in the
OS-process/`run_workload` path, a separate code path with its own copy of
the same ABSTAIN-skips-diagnosis logic. It was not caught by the earlier
fixes because those only touched `run_agent_task`'s tests. No further
occurrences of this specific pattern were found by a targeted search
(`grep -rn "diagnosis is not None" tests/`) beyond the three now fixed.
