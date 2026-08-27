"""Phase 5.2 canonical dataset construction package.

Read-only with respect to Phase 4 (`src/phase4`, `src/runtime`, `src/recovery`,
`src/failure_experience`, `src/decision`) and with respect to the frozen
Phase 5.1 specification directory
(`experiments/results/phase5_dataset_specification/20260826T053011Z/`).
Nothing in this package imports or executes Phase 4 runtime code; it only
reads already-generated, frozen JSON/JSONL evidence files from
`experiments/results/*` and produces new, additive output under
`experiments/results/phase5_dataset_construction/<timestamp>/`.
"""
