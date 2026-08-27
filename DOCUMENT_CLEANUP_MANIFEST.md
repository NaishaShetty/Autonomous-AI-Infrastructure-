# Document Cleanup Manifest

Produced during the Phase 4 closure pass (2026-08-25). Covers every document
under `docs/` (including `docs/archive/`), every subdirectory under
`experiments/results/`, and top-level project documentation
(`README.md`, and the absence of a root `CLAUDE.md`).

**Governing rule applied throughout:** never delete frozen evidence,
canonical protocols, raw evaluation outputs, SHA-256 manifests,
reproducibility artifacts, historical audit reports, benchmark evidence,
dataset manifests, source provenance, or experiment configurations. Prefer
archiving over deleting. When uncertain, keep and note the uncertainty.
Nothing under `experiments/results/post_p5_remediation/20260825T064402Z/` or
`experiments/results/post_p5_remediation_followups/20260825T144031Z/` was
touched, read-modified, or moved.

## Deletion policy update (applied retroactively to this manifest)

A mid-task instruction changed the disposition rule for four specific
categories: exact duplicates (hash-verified), documents superseded by a
clear canonical replacement, redundant generated summaries, and temporary/
debug notes with no unique evidence — these are now to be **deleted
outright** (recorded here, recoverable via git history) rather than merely
archived, while every absolute protection from the original instructions
remains in force unchanged (never delete frozen V1 evidence, canonical
protocols, raw evaluation outputs, SHA-256 manifests, reproducibility
artifacts, historical audit reports, benchmark evidence, dataset
manifests, source provenance, experiment configurations; nothing under
either frozen post-P5 run directory; keep-when-uncertain still applies).

**Re-applying this rule to every finding in this manifest changes nothing
about which files are affected, only what a small number of them are
labeled** — because this inventory, done with SHA-256 verification before
this instruction arrived, had already found that every actual duplicate
hash collision lives entirely inside a raw-evidence directory this task's
absolute protections forbid deleting from (the "Duplicate-hash findings"
table above), and the only two files actually moved
(`PHASE4_5_GAP_FIXES_REPORT.md`, `PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md`)
are unique canonical reports, not duplicates or redundant summaries — they
were moved because the project's own established convention is to relocate
(not delete) an original once its content is folded into the consolidated
record, and nothing in the new instruction asks for a canonical report
with unique content to be deleted. Re-checked against the new criteria
specifically:

- **Exact duplicates (hash-verified)**: the 5 collision groups above are
  all inside `experiments/results/` — raw evidence/raw-evidence-adjacent
  placeholders, explicitly protected. **Not deleted.**
- **Superseded document with a clear canonical replacement**: the `.docx`
  master record is superseded in *scope* by `docs/MASTER_RECORD_CONTENT.md`
  going forward, but it is a real historical snapshot (dated 2026-08-23,
  referenced by README, and the user's own stated plan is to build a new
  `.docx` from the new content separately) rather than a redundant copy of
  the same content in the same format — kept, per "err toward keeping when
  uncertain."
- **Redundant generated summary**: none found. Every `docs/archive/`
  document carries unique, non-overlapping phase content (frozen protocols
  and results specific to that phase); none is a regenerated restatement of
  another kept document.
- **Temporary/debug note with no unique evidence**: none found outside
  `experiments/results/` (where the two `EVALUATION_INCIDENT_001*.md`
  files are themselves the canonical incident record, not disposable debug
  notes, and are explicitly preserved by the project's own integrity rule
  cited in `EVALUATION_INCIDENT_001_STATUS.md`).

**Net result of applying the updated policy: zero additional deletions.**
This is not a failure to comply with the updated instruction — it reflects
that this repository's `docs/` and `experiments/results/` trees had
already been through one careful consolidation pass (the `.docx`
compilation on 2026-08-23, which itself states it moved, not duplicated,
every original document) before this closure phase began, so no
undiscovered duplicate/superseded/redundant/temporary document remained
for this pass to find. If a future session adds a new document that
duplicates existing canonical content, this updated deletion policy — not
the original archive-only one — is what should be applied to it.

## Summary

- **Documents inventoried:** 57 files under `docs/` (56 in `docs/archive/`
  prior to this pass, plus the 1 `.docx` master record) + 2 files that were
  at `docs/` root + ~30 experiment result directories under
  `experiments/results/` (several hundred individual artifact files) +
  `README.md`.
- **Moved (not deleted):** 2 files (see below).
- **Deleted:** 0 files. No byte-identical duplicate was found anywhere that
  met the bar for deletion (verified by SHA-256; see "Duplicate-hash
  findings" below — every hash collision found was either intentional
  dual-naming of the same raw-evidence content, or an empty placeholder
  stub, and in every case both copies live inside a raw-evidence directory
  this task's rules forbid deleting from).
- **Kept unchanged:** everything else — all 56 pre-existing `docs/archive/`
  files, the `.docx` master record, and all ~30 `experiments/results/`
  subdirectories in their entirety.

## docs/ — per-file classification

`docs/archive/` already represents a prior, careful consolidation pass (see
the `.docx` record's own "How to read this document" section): the 56
per-phase documents there are already tagged `Status: FROZEN HISTORICAL` /
`ACTIVE` / `PLANNING` in their own headers, were deliberately preserved
rather than deleted when the `.docx` was first compiled, and this task's
own rules classify essentially all of them as **canonical protocol** or
**canonical report** documents (frozen research records). No further
archival action was taken on any of them — moving frozen historical
records into a second, nested archive location would only make them harder
to find, not safer. Full per-file list and one-line classification:

| File | Classification | Action |
|---|---|---|
| `ALIBABA_CLOSED_LOOP_INTEGRATION_REPORT.md` | canonical report (V1 architecture) | kept |
| `ALIBABA_GPU2020_ACQUISITION_RELIABILITY_RUNTIME_V2_REPORT.md` | canonical report | kept |
| `ARCHITECTURAL_RECOVERY_IMPLEMENTATION_REPORT.md` | canonical report | kept |
| `ARCHITECTURE_MAP_BASELINE.md` | canonical protocol (baseline classification) | kept |
| `DATA_SETUP.md` | canonical protocol (data-fetch instructions, still referenced) | kept |
| `FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md` | canonical report | kept |
| `GENERALIZATION_EXPERIMENT_REPORT.md` | canonical report | kept |
| `LEARNING_INFLUENCE_REPORT.md` | canonical report | kept |
| `MASTER_IMPLEMENTATION_REPORT.md` | canonical report | kept |
| `PHASE1_AUDIT_REPORT.md` | canonical report (frozen historical) | kept |
| `PHASE2_REPORT.md` | canonical report (frozen historical) | kept |
| `PHASE3_1_EVALUATION_PROTOCOL.md` … `PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md` (6 files) | canonical protocol/report (frozen historical, synthetic track) | kept |
| `PHASE3_BASELINE_AUDIT.md` | canonical report | kept |
| `PHASE3_FREEZE.md` | canonical protocol (freeze declaration) | kept |
| `PHASE3_REAL_DATA_3_1_REPORT.md` … `PHASE3_REAL_DATA_3_6_DECISION.md` (6 files) | canonical report (frozen historical, real-data track) | kept |
| `PHASE3_REAL_DATA_3_3_REPORT.md` | **anomaly, kept as-is** — contains unrelated content (a farming-simulation-game economics plan), already identified and explained in the `.docx` record's Section 9 as a probable accidental file-save error onto the wrong path. The actual Phase 3.3-RD findings survive, quoted independently inside `PHASE3_REAL_DATA_3_4_REPORT.md` and `PHASE3_REAL_DATA_COMPARISON.md`. Not touched: the misplaced content might belong to another of the user's projects and overwriting or deleting it could destroy work with no other copy. | kept, anomaly documented |
| `PHASE3_REAL_DATA_AIOPS_NEGATIVE_WINDOW_PROTOCOL.md`, `_AIOPS_PREPARATION_COMPLETE.md`, `_AIOPS_PROTOCOL.md` | canonical protocol | kept |
| `PHASE3_REAL_DATA_ALIBABA_SENSOR_LEAKAGE_GATE.md` | canonical protocol (leakage gate) | kept |
| `PHASE3_REAL_DATA_CLEANING_REPORT.md` | canonical report | kept |
| `PHASE3_REAL_DATA_COMPARISON.md` | canonical report | kept |
| `PHASE3_REAL_DATA_FEASIBILITY_AUDIT.md` | canonical report | kept |
| `PHASE3_REAL_DATA_PROTOCOL.md` | canonical protocol (frozen, all 3 datasets) | kept |
| `PHASE4_0_EPISODIC_DATA.md` | canonical report (frozen historical) | kept |
| `PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md` | canonical report (active substrate) | kept |
| `PHASE4_1_FAILURE_MEMORY.md` | canonical report (frozen historical, superseded in role not content) | kept |
| `PHASE4_2_ACTIVE_FAILURE_PATTERNS.md` | canonical report | kept |
| `PHASE4_2_ACTIVE_PLAN.md` | canonical protocol (planning) | kept |
| `PHASE4_2_FAILURE_PATTERNS.md` | canonical report (frozen historical) | kept |
| `PHASE4_3_AMENDMENT_1_ORACLE_RELATIVE.md` | canonical report (exploratory, clearly labeled) | kept |
| `PHASE4_3_RECOVERY_LEARNING.md` | canonical report | kept |
| `PHASE4_4_AMENDMENT_1_ORACLE_RELATIVE_AND_ABSTENTION_CREDIT.md` | canonical report (exploratory, clearly labeled) | kept |
| `PHASE4_4_PROTOCOL.md` | canonical protocol (frozen) | kept |
| `PHASE4_5_AUDIT_AND_PLAN.md` | canonical report (architecture audit) | kept |
| `PHASE4_PLAN.md` | canonical protocol (master plan, amended) | kept |
| `POST_PUSH_RECONCILIATION_SUMMARY.md` | canonical report (incident record) | kept |
| `RELIABILITY_MODEL_INTEGRATION_AUDIT.md` | canonical report | kept |
| `RUNTIME_RELIABILITY_OBSERVABILITY_ARCHITECTURE_AUDIT.md` | canonical report | kept |
| `RUNTIME_RELIABILITY_OBSERVABILITY_IMPLEMENTATION_REPORT.md` | canonical report | kept |
| `SCHEMA.md` | canonical protocol (schema reference, still in active use) | kept |
| `V1_CONTROL_RECONCILIATION_REPORT.md` | canonical report | kept |
| `V1_FINAL_EVALUATION.md` | canonical report (freeze evidence) | kept |
| `V1_RELEASE_AUDIT.md` | canonical report (freeze decision) | kept |
| `V1_REPRODUCIBILITY_BOUNDARY_FINAL_READINESS.md` | canonical report | kept |
| `VERSIONED_MODULE_CLASSIFICATION.md` | canonical protocol (module boundary reference) | kept |
| `PHASE4_5_GAP_FIXES_REPORT.md` | canonical report, **moved** | moved from `docs/` root to `docs/archive/` — its content is now folded into `docs/MASTER_RECORD_CONTENT.md` (successor source to the `.docx`), and the project's own established convention (documented in the `.docx`'s "How to read this document" section) is to move a document's original into `docs/archive/` once its content has been folded into the consolidated record, never to delete it. Byte-for-byte content unchanged. |
| `PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md` | canonical report, **moved** | same reasoning and mechanism as above |
| `Autonomous_AI_Infrastructure_Comprehensive_Record.docx` | canonical report (prior master record) | kept, unchanged — superseded in scope by `docs/MASTER_RECORD_CONTENT.md` going forward (which is Markdown source for a future, more current `.docx`), but the existing file is a real historical artifact (it records exactly what was known as of 2026-08-23) and is not deleted. |

## experiments/results/ — per-directory classification

Every subdirectory under `experiments/results/` is **raw evidence /
artifact** or **canonical report**, per this task's own rule that raw
evaluation outputs (JSON, `.pkl`/joblib, SQLite, manifests, protocols) must
never be deleted. No file was moved or deleted in any of the following.
Directories, in the order listed by `ls`:

| Directory | Contents | Classification |
|---|---|---|
| `alibaba_closed_loop_v1/`, `alibaba_closed_loop_v2/` | protocol/results/summary/manifest JSON, trace logs | raw evidence + canonical report data |
| `counterfactual_generalization/` | protocol, per-seed results, `report.md` | raw evidence + canonical report |
| `generalization/` | results/manifest/summary JSON | raw evidence |
| `learning_influence/` | control/learned/comparison JSON, protocol | raw evidence |
| `memory_composition/`, `memory_composition_v2/` | per-seed results, ablations, `report.md` | raw evidence + canonical report |
| `phase3_1` … `phase3_6` | aggregate/per-seed results, bootstrap CIs, leakage audits | raw evidence (frozen Phase 3 synthetic track) |
| `phase3_real_data/` | per-sub-phase real-dataset results (AgentRx/AIOps/Alibaba) | raw evidence (frozen Phase 3 real-data track) |
| `phase4_0` … `phase4_4` | episodes, leakage audits, pattern/retrieval/recovery results, amendment analyses | raw evidence (frozen Phase 4 synthetic-era and active-era results) |
| `phase4_1_active/`, `phase4_2_active/` | active-era real-data results, ablations | raw evidence |
| `phase4_4_autonomy_pipeline/` | closed-loop pipeline results | raw evidence |
| `phase4_5_autonomy_pipeline_at_scale/` | continuous-mode metrics, prediction model artifact (`.pkl`), results | raw evidence + model artifact |
| `phase4_5b_recognition_and_agent_evaluation/` | scope-router artifact (`.pkl`), fallback priors, results | raw evidence + model artifact |
| `phase4_6_to_4_10/20260824T133029Z/` | full Priority 4.6-4.10 run: audits/, evaluation/, protocol/, raw/, reports/, reproducibility/, `SHA256_MANIFEST.json` | raw evidence + canonical reports + integrity manifest |
| `post_p5_remediation/20260825T064402Z/` | **frozen reference, not touched this phase** | canonical report + raw evidence + integrity manifest |
| `post_p5_remediation_followups/20260825T144031Z/` | **frozen reference, not touched this phase** | canonical report + raw evidence |
| `reliability_runtime_v1/`, `reliability_runtime_v2/` | dataset audit, protocol, results, `report.md` | raw evidence + canonical report |
| `system_evaluation/` | 5 timestamped `run_*/` directories (each a full self-contained evaluation bundle: ablation/baseline/leakage/metrics/overhead/robustness JSON, `CAPABILITY_MATRIX.md`, `SYSTEM_EVALUATION_REPORT.md`, `controlled_runtime.sqlite`) + 2 incident reports at the directory root | raw evidence (5 independent timestamped runs) + canonical incident reports |
| `v1_1/` | per-area README stubs, `PHASE32`/`PHASE33`/`PHASE34` synthesis reports, temporal-generalization manifest/audit | canonical report + some placeholder stubs (see below) |
| `v1_control_reconciliation/` | reproduced-case protocol/results/trace, environment/replay/skip-reconciliation JSON, test inventory | raw evidence + canonical report |

### Duplicate-hash findings (SHA-256 verified, all kept)

A full SHA-256 comparison was run across every `.md` file under `docs/` and
`experiments/results/` to check for exact-duplicate candidates per this
task's deletion rule ("only truly delete if byte-identical AND recorded
here"). Five hash collisions were found; **none were deleted**, for the
reasons below — every one lives entirely inside a raw-evidence directory
this task's rules forbid deleting from, and in every case the duplication
appears intentional or harmless rather than an accidental copy-paste error:

| Hash (truncated) | Files | Reason kept |
|---|---|---|
| `0181440b…` | `v1_1/phase_diagnosis/4_3/reports/PHASE4_3_CAUSAL_UNDERSTANDING_REPORT.md` = `PHASE4_3_DIAGNOSIS_REPORT.md` | Same content filed under two report names within one phase's raw-evidence directory (likely a deliberate dual-reference so either name resolves); both are raw evidence, deletion is out of scope regardless. |
| `149460d1…` | `system_evaluation/run_20260823T{125455,125539,125602,132857,133417}Z/CAPABILITY_MATRIX.md` (5 copies) | Each timestamped run directory is a self-contained evidence bundle; the capability matrix is static content that does not vary by run and is copied into each bundle by design, exactly like each run's shared protocol/config would be. Raw evidence; not deleted. |
| `21d69d62…` | `v1_1/phase_monitoring_failure_detection/4_2/reports/PHASE4_2_FAILURE_DETECTION_REPORT.md` = `PHASE4_2_MONITORING_REPORT.md` | Same pattern as the first row. |
| `32f5cea7…` | `v1_1/{abstention,calibration,consolidation,diagnosis,features,memory,recovery,reliability_model,robustness}/README.md` (9 copies) | Each is a one-line placeholder stub reading `# Reserved for finalized Phase 3.1 experiment artifacts.` — empty scaffolding, not real duplicated content; harmless either way, kept unchanged rather than risk removing a directory marker something else might reference. |
| `e1188360…` | `v1_1/phase4_observability_hardening/4_1/reports/PHASE4_1_OBSERVABILITY_HARDENING_REPORT.md` = `PHASE4_1_RUNTIME_OBSERVABILITY_REPORT.md` | Same pattern as the first row. |

No other document anywhere in `docs/` or `experiments/results/` shares a
hash with any other document.

## Other project-level documentation

| File | Classification | Action |
|---|---|---|
| `README.md` | canonical report (project overview) | kept, unchanged. Note: its "Current Results" section predates this phase's remediation/follow-up work (it stops at the Phase 4.4/4.5 closed-loop implementation) and does not yet reflect Phase 4.6-4.10 or the post-P5 remediation/follow-ups. Updating it was not in this task's scope; `docs/MASTER_RECORD_CONTENT.md` and the three `FINAL_*` reports at repo root are the current source of truth for everything after that point. |
| `CLAUDE.md` | n/a | does not exist at repo root; nothing to classify. |
| `pyproject.toml`, `.gitattributes`, `.gitignore` | configuration, not documentation | out of scope, untouched |

## Stale-reference fix (found during this pass, and again during the Part C system audit)

Moving the two files above left 4 stale doc-path comments in source code
(non-functional — Python comments/docstrings, not loaded at runtime, so
this did not affect any test or behavior): `src/phase4/prediction_training.py`
(a comment citing the AUC figure's source), `src/phase4/agent_calibration.py`
and `src/phase4/prediction_eval_v2.py` (docstrings citing the report their
design responds to), and `scripts/run_phase4_5b_evidence_at_scale.py` (a
printed message citing the comparison source). All 4 were updated in place
to the new `docs/archive/...` path; no other behavior changed. One further
reference was found in
`experiments/results/phase4_6_to_4_10/20260824T133029Z/reports/PHASE4_7_ABSTENTION_RETRY_REPORT.md` — **left unchanged**, because it is frozen raw
evidence/a canonical report under `experiments/results/`, which this
task's rules forbid modifying; the path it cites still resolves correctly
via git history and the file is still physically present, just moved.

## Net effect

Two files moved (`docs/PHASE4_5_GAP_FIXES_REPORT.md`,
`docs/PHASE4_5B_RECOGNITION_AND_AGENT_EVALUATION_REPORT.md`, both to
`docs/archive/`, content unchanged). Zero files deleted. Zero files under
`experiments/results/` touched. Zero files under the two frozen
post-P5-remediation run directories touched.
