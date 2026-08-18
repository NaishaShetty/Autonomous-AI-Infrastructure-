# Data setup

17 of this repo's 425 tests exercise the real AgentRx / AIOps 2020 /
Alibaba GPU 2020 datasets end-to-end. None of the raw or derived data files
are committed to the repo (`/data/` is gitignored) -- on a clean checkout
those 17 tests are skipped with a message like:

```
SKIPPED [1] tests/conftest.py:41: real dataset 'alibaba_gpu2020' not present
locally (expected data/processed/alibaba_gpu2020/task_table.main_sample.csv),
see docs/DATA_SETUP.md
```

That is expected and not a failure. The remaining 408 tests are fully
data-independent (synthetic data generated in-process, or fixtures under
`tmp_path`) and always run.

## Reproducing the real-data test coverage

Full instructions -- exact download sources, checksums, and the scripted
cleaning/sampling/extraction pipeline for each of the three datasets -- are
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

Once all three are in place, `python -m pytest -q` reports `425 passed`.

## Honest claim to make about test counts

- **408/408** -- data-independent tests pass on any clean checkout, no
  setup required.
- **425/425** -- the full suite, including the 17 real-data tests, only
  passes once all three datasets above are fetched and regenerated
  locally per this document.

Do not state "425/425" without that qualification -- it is only true on a
machine that has done the data setup above. On a machine that hasn't, the
correct statement is "408/408 data-independent tests pass; 17 additional
tests are skipped pending local data setup (see docs/DATA_SETUP.md)".
