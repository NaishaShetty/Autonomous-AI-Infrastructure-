# Evaluation Incident 001 — Status

This file supersedes nothing in `EVALUATION_INCIDENT_001.md`. That report and
every prior `run_*` directory in this folder remain unmodified, historical
evidence, including any run that itself shows a `FAIL` leakage status — those
are preserved as pre-fix/reproduction evidence, not corrected retroactively.

## Status: FIXED

## Root cause

`DiagnosisEngine._eligible` (now `_eligible_current_incident` in
`src/phase4/diagnosis.py`) enforced only a temporal boundary
(`timestamp <= diagnosis_boundary`) over the complete event replay handed to
it. It never restricted eligible events to the failure's own `run_id`, so an
earlier run's `failure_detected` event — timestamped before the current
failure's boundary — was structurally indistinguishable from current-run
evidence. A second bug in `DiagnosisEngine.diagnose` compounded this: any
event with `event_type == 'failure_detected'`, from any run, was treated as
direct failure evidence regardless of whether it matched the current
failure's `evidence_references`.

## Fix (code change)

`src/phase4/diagnosis.py`:

1. `_eligible_current_incident(events, failure, boundary)` now requires
   `event['job_id'] (or 'run_id') == failure['run_id']` in addition to the
   existing temporal boundary, and additionally guards on `workload_id` /
   `environment_id` when the failure declares them. The safety boundary is
   enforced inside the diagnosis layer itself — callers do not need to
   pre-filter events by run.
2. `diagnose()` no longer admits any `failure_detected` event as evidence;
   only events whose `event_id` is in the failure's own
   `evidence_references` are treated as direct failure observations.
3. `foundation_references` on every `StructuredDiagnosis` now records
   `evidence_scope: CURRENT_RUN_ONLY`, `run_id`, `workload_id`, and
   `environment_id`, so a consumer can verify the scope a diagnosis was
   produced under without re-deriving it.

No historical-memory input exists in the current architecture. Cross-run
evidence is therefore excluded entirely rather than reclassified as
`HISTORICAL_MEMORY` — that classification is reserved for a future,
explicitly authorized memory-integrated diagnosis path, which is not
implemented today.

## Regression coverage

`tests/unit/test_phase43_diagnosis.py` adds:

- `test_current_incident_scope_rejects_prior_events_from_other_runs`
- `test_current_incident_scope_rejects_all_prior_runs_even_with_shared_workload_and_environment`
- `test_same_run_future_and_other_identity_events_are_rejected`

alongside the pre-existing `test_future_events_do_not_change_boundary_diagnosis`
(temporal safety) and `test_unknown_when_no_eligible_evidence`. Together these
cover: cross-run rejection under a shared workload/environment, rejection of
same-run future events, rejection of events carrying a mismatched
`workload_id`/`environment_id`, and the pre-existing temporal-leakage
guarantee.

## Pre-fix vs post-fix evidence

- **Pre-fix / reproduction:** `run_20260823T125539Z` and
  `run_20260823T125602Z` deliberately pass the complete event replay to the
  unscoped-path check and record `unscoped_cross_run_evidence_count` of 7 and
  8 respectively, status `FAIL`. These runs are preserved unmodified as the
  documented reproduction of the incident.
- **Post-fix:** `run_20260823T133417Z` runs the same deliberately-unscoped
  check against the corrected `DiagnosisEngine` and records
  `unscoped_cross_run_evidence_count: 0`, status `PASS`. The full repository
  test suite also passed completely in this run (649 passed, 0 failed, 0
  skipped) after a separate, unrelated test-infrastructure fix (see below).
  `run_20260823T132857Z` is an intermediate post-fix run whose test-suite
  measurement is `INCOMPLETE` only because the evaluation runner's own pytest
  subprocess timeout (300s) was shorter than the suite's actual runtime
  (~451-527s on this machine); the runner's timeout was corrected to 900s and
  `run_20260823T133417Z` is the run that reflects the correction. Detection
  and leakage results in `run_20260823T132857Z` are otherwise valid.

## Unrelated defect found and fixed during this audit

`tests/unit/test_phase37_candidate_discovery.py::test_report_contains_required_direction_and_no_integration`
failed on this Windows machine because `REPORT.read_text()` used the platform
default encoding (cp1252) to read a UTF-8 report file containing an em dash,
producing a decode mismatch unrelated to diagnosis or contamination. Fixed by
reading with `encoding="utf-8"` explicitly. No historical report content was
changed. This is a general portability lesson: `Path.read_text()` calls that
compare against non-ASCII literals should specify `encoding="utf-8"`
explicitly rather than relying on the platform default; a systematic sweep of
the other 22 files using bare `.read_text()` was not performed because none
of them currently fail, and blanket-editing passing tests was out of scope
for this corrective pass.
