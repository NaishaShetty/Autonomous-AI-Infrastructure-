# Data setup

## Current, freshly-verified test counts (see below for how these are checked)

As of this doc's last update, the suite has **449 tests total**. None of
the raw or derived real-dataset files are committed to the repo (`/data/`
is gitignored):

- **Without any local real-data setup:** `435 passed, 14 skipped`.
- **With the three marker files below present:** `449 passed, 0 skipped`.

These numbers were produced by two actual fresh runs of
`python -m pytest -q`, not carried forward from an earlier report. If you
run the suite and get a different total, see "Why this number has drifted
before" below before assuming something is broken.

## What determines skip vs. run — exact mechanism

`tests/conftest.py` defines three session-scoped fixtures
(`require_alibaba_data`, `require_aiops_data`, `require_agentrx_data`).
Each checks for exactly one **marker file** — not the full raw or
processed dataset — and skips with a named, itemized message if that one
file is missing:

| Fixture | Marker file checked | Size |
|---|---|---|
| `require_alibaba_data` | `data/processed/alibaba_gpu2020/task_table.main_sample.csv` | ~1.2 MB |
| `require_aiops_data` | `data/audit/aiops_kpi/positive_windows.json` | ~36 KB |
| `require_agentrx_data` | `data/processed/agentrx/tau_retail_joined.jsonl` | ~35 KB |

Important, easy-to-miss detail: **the code paths gated by these fixtures
only read the files above (`real_alibaba.py` reads exactly
`task_table.main_sample.csv`; `real_agentrx.py` reads exactly
`tau_retail_joined.jsonl` and `magentic_joined.jsonl`, ~77 KB) — they do
NOT need the multi-gigabyte raw Alibaba/AIOps archives or the `.clean.csv`
intermediate files** to pass. Placing just those three small files (well
under 2 MB combined) at the paths above is sufficient to turn all 14
real-data-gated tests from skipped to passing; you do not need to run the
full `scripts/real_data/` pipeline just to get a green local suite. Run
that full pipeline (see below) if you actually need the regenerated,
provenance-tracked dataset for research work, not just to make tests pass.

## Reproducing the full real-data test coverage

Full instructions — exact download sources, checksums, and the scripted
cleaning/sampling/extraction pipeline for each of the three datasets — are
in [`scripts/fetch_or_document_real_data.md`](../scripts/fetch_or_document_real_data.md).

Short version:

1. Alibaba GPU 2020: download 7 archives from the [official Alibaba trace
   release](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020)
   into `data/raw/alibaba_gpu2020/`, then run the 5 scripts in
   `scripts/real_data/alibaba_*.py` / `clean_alibaba_job_task.py` in the
   order listed in `scripts/fetch_or_document_real_data.md`.
2. AIOps 2020: obtain `AIOps挑战赛2020预赛数据.zip` (CCF AIOps Challenge
   2020, preliminary round; SHA-256
   `0b50d8a68101af534ee5e3be1730abaef6f04b059f0e9e0904b10fee95162dce`) into
   `data/raw/aiops_kpi/`, then run the 4 scripts in
   `scripts/real_data/aiops_*.py`.
3. AgentRx: accept access terms on
   [huggingface.co/datasets/microsoft/AgentRx](https://huggingface.co/datasets/microsoft/AgentRx),
   download the 4 raw files with an authenticated token into
   `data/raw/agentrx/`, then run
   `scripts/real_data/agentrx_build_joined_tables.py`.

Once all three are in place, `python -m pytest -q` reports `449 passed`.

## Honest claim to make about test counts

- **435/449** — data-independent tests pass on any clean checkout, no
  setup required; 14 skip with an itemized message pointing here.
- **449/449** — the full suite, including the 14 real-data tests, only
  passes once at least the three marker files above are present (full
  pipeline optional for a green suite; required for actual research use
  of the regenerated data).

Do not state "449/449" without that qualification — it is only true on a
machine that has the marker files (at minimum) in place. On a machine that
doesn't, the correct statement is "435/449 tests pass; 14 additional tests
are skipped pending local data setup (see this document)".

## Why this number has drifted before

This doc and the top-level README have both previously understated the
real-data-gated test count (425 total/17 gated, then 441 total/5 gated, in
successive earlier versions of this doc and README) because the count was
written once and not re-verified as later phases (4.1's `failure_experience`
pipeline, 4.2's active pattern integration) added more tests gated by the
same three fixtures without updating this doc. If you find the numbers
here don't match a fresh `pytest --collect-only -q`, trust the fresh run,
not this document, and please update this section rather than assuming
either number was fabricated — see the git history of this file for the
actual sequence of test-count drift.
