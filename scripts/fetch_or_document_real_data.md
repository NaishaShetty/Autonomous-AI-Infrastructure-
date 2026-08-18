# Fetching / regenerating the real datasets

This repo's real-data tests and real-data experiment scripts depend on three
external datasets. None of their raw or derived files are committed (see
`/data/` in `.gitignore`) -- they must be downloaded and rebuilt locally.
This document is the exact, scripted path from "nothing" to the derived
files those tests read:

- `data/processed/alibaba_gpu2020/task_table.main_sample.csv`
- `data/audit/aiops_kpi/positive_windows.json` (and the sibling
  `negative_window_natural_population.json`, `negative_windows_sampled.json`,
  `positive_window_validation.json`, `negative_window_validation.json`)
- `data/processed/agentrx/{tau_retail_joined,magentic_joined}.jsonl`

None of these are programmatically fetchable end-to-end by a single script:
Alibaba requires an unauthenticated but manual bulk download, AIOps is a
competition-gated archive with no confirmed stable download URL, and AgentRx
requires an authenticated, gated Hugging Face token. Each is documented
below with what *is* scripted (the cleaning/sampling/extraction pipeline,
all under `scripts/real_data/`) and what remains a manual acquisition step.

Run everything from the repo root with the project's Python environment
(`pip install -r requirements.txt`) active.

## 1. Alibaba GPU 2020 cluster trace

**Source**: [Alibaba Cluster Trace Program v2020 GPU trace](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020),
published alongside Weng et al., *"MLaaS in the Wild: Workload Analysis and
Scheduling in Large-Scale Heterogeneous GPU Clusters"*, NSDI '22. The
official README (already vendored read-only in this repo at
`data/provenance/alibaba_gpu2020/official_README.md`) lists the download
URLs and the publisher's own SHA-256 checksums for each table.

### 1a. Download (manual)

Download these 7 archives from
`https://aliopentrace.oss-cn-beijing.aliyuncs.com/v2020GPUTraces/` (or the
mirror at `https://github.com/qzweng/clusterdata-cluster-trace-gpu-v2020-data`)
into `data/raw/alibaba_gpu2020/`, unmodified:

```
pai_job_table.tar.gz
pai_task_table.tar.gz
pai_instance_table.tar.gz
pai_sensor_table.tar.gz
pai_group_tag_table.tar.gz
pai_machine_spec.tar.gz
pai_machine_metric.tar.gz
```

Verify against the publisher's checksums before proceeding:

```bash
cd data/raw/alibaba_gpu2020
sha256sum -c <(grep -A9 '^\$sha256sum' ../../provenance/alibaba_gpu2020/official_README.md | tail -n +2 | head -n7)
```

(or just diff each file's `sha256sum` output against the table in
`data/provenance/alibaba_gpu2020/official_README.md` by hand).

### 1b. Clean, sample, split (scripted)

Run in this exact order -- each step reads only the outputs of the previous
one and never re-touches `data/raw/`:

```bash
python scripts/real_data/clean_alibaba_job_task.py
python scripts/real_data/alibaba_power_analysis.py
python scripts/real_data/alibaba_stratified_sampling.py
python scripts/real_data/alibaba_extract_linked_records.py
python scripts/real_data/alibaba_build_splits.py
```

Outputs used by the tests/adapters:

- `data/processed/alibaba_gpu2020/task_table.main_sample.csv` (from
  `alibaba_extract_linked_records.py`, tier=`main`)
- `data/audit/alibaba_gpu2020/splits_random_stratified.json` and
  `splits_temporal.json` (from `alibaba_build_splits.py`)

All five scripts are deterministic given the same raw archives (seeded
sampling; see each script's own docstring for its seed and rationale).

## 2. CCF AIOps Challenge 2020 (preliminary round)

**Source**: CCF (China Computer Federation) AIOps Challenge 2020,
preliminary round. This is a competition-gated archive; unlike Alibaba's
trace, there is no independently reverified, stable public download URL for
it in this repo's audit trail (see README.md, "Dataset C -- AIOps KPI"
section: *"the exact original download URL/date were not independently
re-verified this pass"*). What the archive itself confirms about its own
identity/integrity:

- Filename: `AIOps挑战赛2020预赛数据.zip`
- Size: 3,084,639,115 bytes
- SHA-256: `0b50d8a68101af534ee5e3be1730abaef6f04b059f0e9e0904b10fee95162dce`
  (also recorded in `configs/aiops_extraction_protocol_v1.json`)
- Internally it ships its own `sha256sum.txt` (per-day archive checksums)
  and `passwd.txt` (zip password for the 10 password-gated `_lock.zip` daily
  archives -- password decoded and documented, but only used to extract
  files this repo's own scripts need).

To reproduce: obtain this archive from the CCF AIOps Challenge 2020
organizers/competition site under its original terms, verify it against the
SHA-256 above, and place it at
`data/raw/aiops_kpi/AIOps挑战赛2020预赛数据.zip`. Do not substitute a
differently-packaged copy without re-verifying the checksum -- the
extraction pipeline below assumes this exact archive layout.

### 2a. Build windows, extract telemetry, validate (scripted)

```bash
python scripts/real_data/aiops_build_windows.py
python scripts/real_data/aiops_extract_telemetry.py
python scripts/real_data/aiops_validate_positive_windows.py
python scripts/real_data/aiops_validate_negative_windows.py
```

`aiops_build_windows.py` must run first and its output must be frozen
before `aiops_extract_telemetry.py` runs (see that script's docstring --
the window set is derived purely from fault-log timing/entity IDs, before
any telemetry content is read, so the extraction filter cannot be
influenced by what the telemetry looks like).

Outputs used by the tests/adapters:

- `data/audit/aiops_kpi/positive_windows.json` (read directly by
  `src/failure_experience/sources/real_aiops.py`)
- `data/processed/aiops_kpi/{platform,business,trace_windows}/` (full
  per-day extracted telemetry, referenced by the descriptive/discovery
  pipeline)

## 3. AgentRx

**Source**: [huggingface.co/datasets/microsoft/AgentRx](https://huggingface.co/datasets/microsoft/AgentRx)
(gated dataset -- requires accepting the dataset's access terms on
Hugging Face and an authenticated read token).

### 3a. Download (manual, authenticated)

```bash
export HF_TOKEN=<your accepted-access token>
mkdir -p data/raw/agentrx
for f in magentic_dataset.jsonl magentic_one.jsonl tau_retail.jsonl tau_retail_dataset.jsonl; do
  curl -L -H "Authorization: Bearer $HF_TOKEN" \
    "https://huggingface.co/datasets/microsoft/AgentRx/resolve/main/$f" \
    -o "data/raw/agentrx/$f"
done
```

Verify against the checksums recorded in
`data/provenance/agentrx_download_provenance.md` before proceeding.

### 3b. Join into normalized trajectories (scripted)

```bash
python scripts/real_data/agentrx_build_joined_tables.py
```

Output used by the tests/adapters:
`data/processed/agentrx/{tau_retail_joined,magentic_joined}.jsonl`

## 4. Verifying the setup

Once all three datasets are in place, run:

```bash
python -m pytest -q
```

All 425 tests (408 data-independent + 17 real-data-dependent) should pass.
Without any of the three datasets present, `pytest -q` still runs cleanly --
the real-data-dependent tests are skipped individually (per missing
dataset) with a message pointing back to `docs/DATA_SETUP.md`, rather than
erroring. This was verified directly: with `data/` moved aside, the suite
reports `408 passed, 17 skipped` with no tracebacks.

See also `docs/DATA_SETUP.md` for the condensed version of this document
aimed at a first-time contributor, and each adapter module
(`src/failure_experience/sources/real_*.py`) for the exact file paths and
schema each one expects.
