# Phase 6.5 — CI/CD Validation Report

## What was created

- `.github/workflows/ci.yml` — fast path, runs on every push/PR to `main`:
  install deps, run `tests/unit/test_phase54_benchmark.py` explicitly (the
  benchmark's own unit tests), run the rest of `tests/unit` excluding the
  three real-model/torch-dependent test files, run the full benchmark via
  `scripts/run_phase5_4_benchmark.py` (which itself performs schema
  validation, leakage scanning, and a determinism check as part of its own
  execution), assert `determinism_check` is true on every axis, then a
  separate `build-check` job that validates the Python package build and
  runs a Docker build check (`docker/build-push-action`, `push: false`).
- `.github/workflows/full-suite.yml` — manual/weekly-scheduled path, runs
  the entire `tests/` suite (including the slower real-model tests) and
  uploads the full pytest output as an artifact, with an explicit note
  about the known `tests/runtime/test_counterfactual_generalization.py`
  failure category so it does not look like a silent CI regression.

## Validation performed

**YAML syntax**: both files parsed successfully with Python's `yaml`
module (`yaml.safe_load`), confirmed via direct execution in this
session:

```
.github/workflows/ci.yml OK jobs= ['unit-and-benchmark-tests', 'build-check']
.github/workflows/full-suite.yml OK jobs= ['full-suite']
```

**What was NOT verified**: GitHub Actions itself was not triggered from
this environment — no push to `origin` was made (per the hard boundary
in this phase's instructions), so the workflows have never actually run
on GitHub's infrastructure. The job steps were written against commands
that were independently verified to work on this machine during this
phase (`pytest tests/unit/test_phase54_benchmark.py -v` → 41 passed;
`python scripts/run_phase5_4_benchmark.py` → completed, determinism
confirmed), but `actions/checkout`, `actions/setup-python`, and the
`docker/*` actions' exact behavior on GitHub's hosted runners is not
something this environment can execute or observe.

## Separation rationale

The fast (`ci.yml`) and full (`full-suite.yml`) workflows are kept
separate specifically because the full suite includes torch/transformers-
dependent tests (`test_real_model_runtime.py`, `test_classification_task.py`,
`test_qa_task.py`) that are slower and, in this local environment, were
affected by an environment-specific `huggingface_hub` issue in the past
(see `FINAL_SYSTEM_AUDIT.md` for whether that is still an issue) — a fast
CI signal should not block on that dependency surface.

## Honest conclusion

CI/CD YAML is syntactically valid and each of its command steps is built
from commands independently confirmed to work locally in this phase. No
GitHub Actions run was triggered or observed from this environment, and
this report does not claim one was.
