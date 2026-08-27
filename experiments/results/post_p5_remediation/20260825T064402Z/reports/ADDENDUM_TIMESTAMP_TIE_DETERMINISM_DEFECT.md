# Addendum — Real Nondeterminism Defect in `run_agent_task`'s Prediction Boundary (Step 7)

Discovered during Step 7 final verification while investigating two more
full-suite test failures. This is a **separate, more significant** defect
from the `cpu`-family timing-margin issue documented in
`ADDENDUM_CPU_TIMING_DEFECT.md` — it affects the determinism of the core
agent-uncertainty decision path itself, not just corpus generation.

## The defect

`AutonomyPipeline.run_agent_task`'s (and the equivalent path in
`run_workload`) prediction-boundary temporal cut used **strict `<`**
against a microsecond-precision wall-clock timestamp string:

```python
prediction_prefix = [e for e in result.events if e.get("event_type") != "failure_detected" and (e.get("timestamp") or "") < failure_boundary]
```

Two events emitted in rapid succession — most importantly, the **last**
self-consistency sample and the `failure_detected` event immediately
following it — can legitimately share the exact same microsecond
timestamp on a fast machine. Strict `<` then silently **dropped that last
sample** from `prediction_prefix`. This matters far more than it might
sound: `AgentUncertaintyPredictor` reads `running_agreement_rate` from the
**last included sample**, i.e. the only one whose agreement rate reflects
**all** `n_samples`, not a partial subset. Losing it made a genuinely
high-disagreement wrong answer look artificially low-risk (fewer samples
observed → the predictor's running agreement rate could differ, in either
direction, from the true final value), which could silently change the
decision (e.g. autonomous `ANSWER` instead of `REVIEW`/`ABSTAIN`) for
exactly the highest-risk episodes — the ones abstention exists to catch.

**Confirmed as genuine, real nondeterminism, not RNG or system load:**
`agent_task.py`'s arithmetic and self-consistency logic is fully
deterministic given a seed (verified by direct code reading — no RNG or
timing dependency in the correctness computation itself, confirmed via
`grep` for `random`/`time.` in the module). Re-running the identical 15
known-wrong seeds through a fresh pipeline **three times in immediate
succession** on this platform produced **three different subsets** of
"missing" (silently-ABSTAIN'd-without-being-counted, or
incorrectly-ANSWER'd) episodes each time — proof this was real,
timestamp-collision-driven nondeterminism, not a data or logic bug tied to
any specific seed.

## Fix

Changed both occurrences (in `run_workload` and `run_agent_task`) from `<`
to `<=`. This matches the convention every other temporal-cut boundary in
this codebase already uses — `prediction.py::rolling_checkpoints` already
uses `<= ts` for the identical "at or before a boundary" semantic — `<`
here was the one inconsistent outlier, not an intentional design choice.
The `event_type != "failure_detected"` guard already independently
excludes the failure event itself regardless of this comparison, so
widening to `<=` cannot let the failure event's own evidence leak into its
own prediction.

**Verified fixed:** re-ran the same 15-seed reproduction three times after
the fix — zero missing episodes in all three runs (previously 4-6 missing,
different each time).

## Also fixed: test-counting logic conflated infra timeouts with wrong answers

While investigating, found a second, smaller, related issue in the tests
themselves (not the pipeline): both failing tests counted
`result.diagnosis is not None` as "this was a wrong answer," but a real
subprocess timeout (`AGENT_TASK_TIMEOUT` → diagnosis primary_hypothesis
`AGENT_RUNTIME_TIMEOUT`) also produces a non-None diagnosis and would have
been counted as a wrong answer too, even though it's infrastructure noise
unrelated to answer correctness. Fixed both tests
(`tests/integration/test_phase45b_agent_pipeline.py`,
`tests/integration/test_phase47_agent_calibration_pipeline.py`) to filter
specifically on `diagnosis.primary_hypothesis.name == "AGENT_INCORRECT_OUTPUT"`.
This did not turn out to be the primary cause of the observed failures
(no `AGENT_RUNTIME_TIMEOUT` diagnoses were actually observed in any
reproduction), but it is a real, independent correctness improvement to
the tests' own measurement, kept regardless.

## Regression test

`test_prediction_prefix_includes_a_sample_that_ties_the_failure_events_own_timestamp`
(`tests/integration/test_phase45b_agent_pipeline.py`) — constructs an
explicit timestamp tie (rather than relying on real timing to collide,
which would make the test itself flaky) and asserts the tied sample is
retained in `prediction_prefix`.

## Implication for the pre-remediation P5 headline results

The master remediation register's P5 baseline reported "final accuracy:
1.000, final error rate: 0.000, unsafe actions: 0" and a retry ablation
("retry OFF ≈3.0% error, retry ON 0.0% error") — both measured via this
exact `run_agent_task` code path. Since this defect could silently change
ANSWER-vs-REVIEW/ABSTAIN decisions run to run, it is possible (not
confirmed either way) that those specific historical numbers carry some
of the same nondeterminism this addendum fixes. This does not mean those
results were fabricated or wrong — retry's causal benefit (0.0% vs ~3.0%
error) is a large, qualitative effect unlikely to be fully explained by
occasional sample-dropping — but the exact reported decimal values should
not be treated as more precise than this newly-understood source of
variance allows. Re-running P5's final integrated evaluation with this fix
in place is recommended as a follow-up (not performed in this remediation
phase, to preserve budget for completing Step 7) so a version of those
headline numbers exists that is provably free of this specific defect.

## Severity and scope

This is the most significant defect found in this remediation phase: it
affected the determinism of the core "does the agent's self-consistency
disagreement get correctly escalated" decision — the P1/P2 abstention
mechanism's actual operating behavior — not merely a test's assertion
threshold or a corpus-generation detail. It is plausible this same defect
contributed to some of the full-suite instability noted throughout this
remediation phase (P1-W4) before its mechanism was understood. It does
not invalidate Step 5's P1-W1 sentiment finding (that investigation used
`classification_task.py`'s single-forward-pass path, which has no
comparable multi-event temporal-cut boundary) or Step 6's memory
experiment (which used `resource_unavailable`/OS-process events, not the
agent self-consistency path) — both are unaffected by this specific code
path.
