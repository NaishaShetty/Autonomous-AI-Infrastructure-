# Phase 5.2 — Dataset Construction Report

Status: dataset constructed and mechanically validated against the
FROZEN Phase 5.1 specification
(`experiments/results/phase5_dataset_specification/20260826T053011Z/`).
Phase 4 and Phase 5.1 remain untouched (see §"Immutability confirmation").

## 1. Sources actually converted

| Source | Class (Phase 5.1 inventory) | Records extracted |
|---|---|---|
| `experiments/results/phase4_4_autonomy_pipeline/results.json` (`closed_loop_episodes.episodes`) | 2 (SRC-021) | 6 |
| `experiments/results/phase4_5_autonomy_pipeline_at_scale/continuous_mode_metrics.jsonl` | 2 (SRC-022) | 40 |
| `experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/episodes/arithmetic_episodes.json` | 1 (SRC-024/SRC-010) | 2,000 |
| `experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/classification_predictions.json` | 1 (SRC-024/SRC-011) | 660 |
| `experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/predictions/qa_predictions.json` | 1 (SRC-024/SRC-012) | 400 |
| **Total** | | **3,106** |

Sources inspected but NOT ingested as per-record content (aggregate-only,
no retained per-episode identity to join back to a record — genuine source
limitation, category (c)):
`experiments/results/post_p5_remediation/20260825T064402Z/raw/*.json`,
`experiments/results/post_p5_remediation_followups/20260825T144031Z/raw/*.json`,
`experiments/results/phase4_5b_recognition_and_agent_evaluation/results.json`,
`experiments/results/phase4_5_autonomy_pipeline_at_scale/results.json`,
`experiments/results/phase4_6_to_4_10/20260824T133029Z/raw/decisions/README.json`
(which itself discloses that per-episode Decision objects were never
separately dumped for that run).

Sources explicitly out of scope per Phase 5.1 (Gen-1/Gen-2/V1, engineering
artifacts, class-8 evidence): never read by `src/phase5/sources.py`.

## 2. Record counts

- Total records: **3,106**
- Episodes: 3,106 (1 record = 1 episode/task-instance at this construction's grain)
- Runs: 3,106
- Workloads: 3,104
- Environments (distinct `environment_id` values present): 1 (`UNSPECIFIED_PRE_4_9` — see limitation below)

## 3. Task-family distribution (agent_task track)

- `arithmetic_self_consistency`: 2,000
- `sentiment_softmax_margin`: 660
- `extractive_qa_span_logit`: 400

## 4. Failure-class distribution

- `NONE` (no failure / correct answer): 2,852
- `AGENT_INCORRECT_ANSWER`: 219
- `GENERIC_FAIL`: 13
- `NETWORK_FAILURE`: 11
- `PROCESS_OOM`: 10
- `PROCESS_TIMEOUT_CPU`: 1

## 5. Split counts

| split | records | workloads |
|---|---|---|
| train | 2,142 | — |
| calibration_validation | 482 | — |
| test | 482 | — |

Forbidden overlaps (train∩calib, train∩test, calib∩test, and workload_id
crossing a forbidden split): all **0** (`split_audit.json`).

## 6. Deterministic record-ID method (Open Question 1)

`src/phase5/record_id.py`: `record_id = sha256(dataset_version + 0x1F +
source_artifact_hash + 0x1F + source_record_id + 0x1F + episode_id + 0x1F +
record_type + 0x1F + sequence)[:24 hex chars]`, where `source_artifact_hash`
is the SHA-256 of the exact frozen source file's bytes and `sequence` is a
source-intrinsic, sorted index (never enumerate-over-unordered-iterable,
never filesystem/dict order). Regression test:
`tests/unit/test_phase52_record_id.py` (10 tests, including a
subprocess-based cross-`PYTHONHASHSEED` check proving independence from
Python's salted `hash()`) — **10/10 passed**.

## 7. Split/workload-ID compatibility (Open Question 2)

`scripts/phase5_dataset/validate_splits.py` mechanically checks
train/calibration/test disjointness at the record level and workload_id
non-crossing. Result: **0 overlaps, 0 workload violations**
(`split_audit.json`). Historical exact seed lists used by the original
Phase 4 protocols could not be recovered from the per-episode raw evidence
actually available (only 46 controlled-runtime episodes and 3,060
agent-task instances retain per-record identity; no per-record `seed`
field exists for the sentiment/QA sources, and the aggregate
`p4_step4_results.json` environment-generalization evidence has no
retained per-episode join key) — per the task's explicit instruction, this
was disclosed rather than invented, and splits were instead assigned via a
deterministic SHA-256 hash-partition of `workload_id` (the strongest
reproducible grouping key actually available), documented in
`build_dataset.py::_split_bucket`. The environment-axis
(development/held-out/robustness) boundary could not be mechanically
checked against real records for the same reason and is reported as a
disclosed limitation, not silently skipped (`SPLIT_VALIDATION_REPORT.md`).

## 8. Deterministic regeneration (Open Question 3)

`scripts/phase5_dataset/regeneration_check.py` ran `generate.py` twice into
two separate directories from the same frozen sources and diffed record
IDs, full record contents, split assignments, and every output file's
SHA-256. Result: **`overall_byte_identical: true`**
(`regeneration_audit.json`). One nondeterminism source was found and fixed
during development (see §9).

## 9. Implementation issues found and their classification

- **(a) Implementation bug, fixed**: the JSONL writer originally emitted
  explicit `null` for several optional sub-objects (`decision`,
  `diagnosis`, `recovery`, `validation`, `memory_interaction`,
  `generalization`, `prediction`, and the nested `recovery.reversible` /
  `recovery.authorized` leaves) whose `PHASE5_1_SCHEMA.json` definitions do
  not accept `null` (unlike `agent_output`, which has an explicit
  `oneOf [...​, {"type": "null"}]`). Fixed by omitting the key entirely
  when the value is not applicable — correct per the schema's own
  optionality (none of these keys are in `required`), and required no
  change to the frozen schema file. See `generate.py::_clean_record`.
- **(b) Genuine Phase 5.1 schema deficiency, disclosed, worked around
  additively**: `PHASE5_1_DATASET_SPECIFICATION.md` §4 states "every
  episode record carries an explicit `outcome_class`" as a named design
  requirement, but `PHASE5_1_SCHEMA.json` does not define `outcome_class`
  as a formal schema property or enum anywhere. Resolved by adding
  `outcome_class` as an additive, non-required top-level field (schema has
  no `additionalProperties: false`, so this is schema-compatible), value
  set documented in `DATASET_README.md`. The frozen schema file itself was
  NOT modified.
- **(c) Unavailable source evidence, disclosed, not invented**: no
  per-episode Phase-4.9 `environment_id`; no per-checkpoint observation
  telemetry rows; no ABSTAIN-decision episodes; no historical exact seed
  lists for the original train/calibration/test protocol. Each is stated
  explicitly in `DATASET_README.md`, `SPLIT_VALIDATION_REPORT.md`, and
  `NEGATIVE_RESULT_PRESERVATION_REPORT.md` rather than silently patched
  over.
- **(d) Documented ambiguity resolution**: agent-task raw evidence has no
  explicit `workload_id`/`run_id` distinction recorded by the source code
  path that produced `classification_predictions.json`/`qa_predictions.json`
  (only `example_id`); resolved by setting `workload_id = run_id =
  f"agent-{family}-{example_id}"` for those two families (1:1, no
  repeated-incident structure claimed), while arithmetic instances (which
  do carry a `seed` field) use `workload_id = f"agent-arithmetic-seed-{seed}"`
  distinct from `run_id = example_id`, consistent with Phase 5.1 §2's
  "or an agent TaskInstance seed" language.

## 10. Immutability confirmation

`git status --porcelain` and `git diff --stat` (captured at completion, see
`PHASE5_2_DATASET_AUDIT.md` §"Phase 4 / Phase 5.1 untouched") show zero
changes under `src/phase4/`, `src/runtime/`, `src/recovery/`,
`src/failure_experience/`, `src/decision/`,
`experiments/results/phase5_dataset_specification/20260826T053011Z/`, or
any existing `experiments/results/` subdirectory that predates this run.
All new files are additive, under
`experiments/results/phase5_dataset_construction/20260826T054422Z/`,
`src/phase5/`, `scripts/phase5_dataset/`, and
`tests/unit/test_phase52_record_id.py`.
