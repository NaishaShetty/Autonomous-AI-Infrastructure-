# Phase 5.6 — Release Decision

## Decision: READY_FOR_PUBLICATION

Every technical, security, and licensing gate in this phase now passes
(see `FINAL_PUBLICATION_AUDIT.md` for the full checklist). **Update
(2026-08-27, post-audit addendum):** the project owner has explicitly
decided the license — MIT for the benchmark/software code, CC BY 4.0 for
the dataset — and a dedicated upstream license/provenance audit
(`LICENSE_PROVENANCE_AUDIT.md`, this directory) confirmed no upstream
source (corpus generation, third-party model checkpoints, or any
historical Phase 3/4 real-operational dataset) restricts redistribution
under these terms. `LICENSE` files have been added to both release
packages and the root repository, and `DATASET_CARD.md`, `BENCHMARK_CARD.md`,
both packages' `README.md`, and both `CITATION.cff` files have been
updated accordingly. The previously-open license item is resolved; no
other blocking item exists.

## Recommended Hugging Face artifacts

| Artifact | Recommendation | Justification |
|---|---|---|
| A. Dataset repository (`release/dataset/`) | **RECOMMENDED** | 3,106 records, schema-validated, leakage-audited (0 violations), SHA-256 verified, clean-room loadable with zero repo dependencies, negative results and limitations disclosed rather than hidden, CC BY 4.0 licensed. This is a genuine, verifiable research artifact. |
| B. Benchmark/evaluation package (`release/benchmark/`) | **RECOMMENDED** | Self-contained, clean-room reproducible (41/41 unit tests, full benchmark run byte-identical modulo run metadata to the frozen Phase 5.4 reference), determinism verified twice (internal double-run + cross-machine/cross-day), per-task status explicitly disclosed (0 VALIDATED / 6 PARTIALLY_VALIDATED / 3 UNDERPOWERED / 0 NOT_VALIDATED / 7 NOT_EVALUABLE) so no reader can mistake this for "8 capabilities validated," MIT licensed. |
| C. Model repository | **NOT RECOMMENDED** | See reasoning below. |

## Model-release reasoning (verified against the actual evidence, not assumed)

This project's only candidate model-shaped artifacts are the trained
`RiskPredictor` and `PredictionScopeRouter` objects behind the 4
`PRED-*` failure-prediction tasks. Checked directly against this
project's own frozen findings:

- All 4 `PRED-*` tasks (`PRED-RESOURCE-UNAVAILABLE`, `PRED-OOM`,
  `PRED-CPU`, `PRED-FLAKY`) are **NOT_EVALUABLE** at record level in the
  Phase 5.2 canonical dataset (insufficient per-episode evidence to score
  them at all).
- Their only supporting evidence is Phase 4's **aggregate-level**
  reference numbers, and even those are mixed: `resource_unavailable` is
  the sole `STRONG_EVIDENCE` result; `PROCESS_OOM` has AUROC 0.780 but an
  always-fires false-alarm-rate of 1.0 (flagged
  `RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID` — a ranking signal, not a
  usable operating point); `cpu` and `flaky` are `NOT_VALIDATED`.
- No calibration/decision/recovery model in this project has been
  independently validated end-to-end: recovery is 0/35, diagnosis is
  class-matching only (causal ground truth unavailable, false-causal-
  attribution-rate 1.0), and the abstention tasks are
  `SIMULATED_POLICY_EVALUATION` (no realized ABSTAIN/RETRY episodes
  exist to evaluate against).
- There is therefore no single trained model artifact in this project
  that would responsibly stand alone as a Hugging Face model repository:
  publishing one risks a reader treating an aggregate-only,
  operationally-invalid, or explicitly-NOT_EVALUABLE predictor as a
  usable trained model, which the evidence does not support.

**Conclusion: NO MODEL RELEASE RECOMMENDED.** This reasoning was checked
against the actual per-task capability matrix and aggregate-reference
findings this phase (not assumed from the task framing) and holds.

## Checklist rollup

See `FINAL_PUBLICATION_AUDIT.md` for the full 23-item table. Summary:
security PASS (1 finding, fixed), publication boundary PASS, dataset
integrity PASS, benchmark integrity PASS, leakage PASS, determinism
PASS, clean-room reproduction PASS, cross-environment portability PASS,
documentation accurate, citation present, dataset/benchmark cards
complete, SHA-256 manifests complete. Full repository test suite: see
final section below (filled in after the blocking `pytest tests/ -q` run
this phase completed).

## Full repository test suite result (this phase, final)

`python -m pytest tests/ -q` was run fresh, to completion, blocking
(22m33s). **Actual result: 20 failed, 868 passed** (`FULL_TEST_SUITE_OUTPUT.txt`).
This is not the 880/8 figure the task brief assumed as the "known
state" — that baseline had gone stale since Phase 5.5. The real,
independently-diagnosed breakdown:

- **8 failures** — exactly the previously-known set in
  `tests/runtime/test_counterfactual_generalization.py` (identical test
  names verified against Phase 5.5's own test output), caused by the
  already-documented hardcoded non-hermetic temp-file path in frozen
  `src/runtime/`. Unchanged, not touched (frozen boundary).
- **12 new failures** — `tests/integration/test_phase46_integration.py` (2),
  `tests/unit/test_classification_task.py` (4), `tests/unit/test_qa_task.py` (2),
  `tests/unit/test_real_model_runtime.py` (4) — all traced to the same
  root cause: this machine's `huggingface_hub` Python package is
  corrupted/missing (`ModuleNotFoundError: No module named
  'huggingface_hub'`, confirmed by direct `python -c "import
  huggingface_hub"` and `pip show huggingface_hub` reporting "Package(s)
  not found" alongside an "Ignoring invalid distribution ~uggingface-hub"
  warning). This breaks `transformers`, which these `src/phase4/`
  real-model-runtime tests depend on. It is a local environment defect,
  not a repository or release-package defect.

**Neither failure group touches the release package.** `release/benchmark/`
has zero references to `transformers`/`torch`/`huggingface_hub`/
`real_model_runtime`/`classification_task`/`qa_task`/`src/runtime/experience.py`
(confirmed by grep), its own `requirements.txt` pins only numpy/pandas/
scikit-learn/scipy, its 41 unit tests pass both inside this full run and
inside the isolated clean-room, and the clean-room's full benchmark run
reproduced the frozen Phase 5.4 result byte-for-byte (modulo run
metadata). This test-suite finding changes nothing about the dataset or
benchmark release's technical readiness; it is reported here in full
because the audit's job is to report the real, current state, not the
one assumed at the start of this phase.

## Hugging Face publication status

**No Hugging Face upload, login, repository creation, or any network
call to huggingface.co was made or attempted at any point in this
phase**, regardless of this decision. `huggingface-cli login`,
`huggingface-cli upload`, `HfApi().create_repo(...)`,
`HfApi().upload_file(...)` were never run. No Hugging Face account or
repository was created. This was a hard, non-negotiable constraint for
this phase and was respected throughout — the deliverable is a
publication-ready package plus this decision document, not a publication.

**Even with this READY_FOR_PUBLICATION decision**, actual publishing
still requires: (1) the human user's separate, explicit, real-time
approval, and (2) valid Hugging Face credentials entered by the user
directly (never by an agent), which this task deliberately did not use
even if any were found in the environment (none were deliberately
searched for or used). This document records readiness, not publication.
