# Evaluation Incident 001 — Cross-run diagnosis evidence contamination

## Discovered in

`run_20260823T125455Z`, preserved without modification.

## Observation

The first fresh failure was passed to `DiagnosisEngine.diagnose()` with the
complete event-log replay. The engine's temporal boundary prevents future
events, but it does not itself restrict eligible events to the failure's
`run_id`. Consequently, the diagnosis of the later timeout included the
earlier nonzero-exit `failure_detected` event as evidence.

## Impact

The first run's diagnosis evidence is not valid for a per-incident diagnosis
claim. Its apparent top-1 failure-class accuracy must not be interpreted as a
valid independent diagnosis result.

## Response

No project subsystem, frozen artifact, threshold, or model was changed. A
subsequent evaluation run will pass only same-run events to the existing
diagnosis API and will explicitly test the unscoped path as a failed
cross-run-contamination check. The original result remains available as raw
evidence.
