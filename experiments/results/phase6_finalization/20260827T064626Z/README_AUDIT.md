# Phase 6.3 — README Audit

## Method

Every number in the rewritten `README.md` was traced to one of two
sources before being written: `docs/MASTER_RECORD_CONTENT.md` (sections 3,
5, 13–18, 22 specifically) or
`experiments/results/phase5_6_external_release/20260827T055356Z/BENCHMARK_CARD.md`
/ `DATASET_CARD.md`. No number in the README was invented or restated from
memory without checking the source file first.

## Cross-checked claims (source -> README)

| README claim | Source | Match |
|---|---|---|
| AI-Abstention-Engine ~9,700 lines, Introspective Failure Memory Model ~1,560 lines | MASTER_RECORD_CONTENT.md §3 | Exact |
| `global_reliability_score: 189.61`, selective risk 0.1667 vs 0.2083, correlation 0.031 vs 0.200 | MASTER_RECORD_CONTENT.md §3 | Exact |
| Arithmetic AUROC 0.955 (n=310), QA AUROC 0.938 (n=49), sentiment AUROC 0.439 (n=113) | BENCHMARK_CARD.md capability matrix | Exact |
| Sentiment ECE 0.089 -> 0.023 | MASTER_RECORD_CONTENT.md §14 | Exact |
| Selective risk 0.0 / 0.3125 / 0.03125 | BENCHMARK_CARD.md | Exact |
| Memory ON retry->retry->reconfigure->recovered; OFF retry x6 | MASTER_RECORD_CONTENT.md §16 | Exact |
| `resource_unavailable` STRONG_EVIDENCE; oom AUROC 0.780/0.625; cpu 0.616/0.389 FAR 1.00 | MASTER_RECORD_CONTENT.md §13 | Exact |
| OOM generalization 0.989/0.983/0.935 | MASTER_RECORD_CONTENT.md §22 (Step 4) | Exact |
| Diagnosis 35/35 accuracy, false-causal-attribution-rate 1.0 | BENCHMARK_CARD.md (DIAG-EVAL) | Exact |
| Recovery 0/35; safety 0/6 and 0/16 incorrectly authorized | MASTER_RECORD_CONTENT.md §17-18, BENCHMARK_CARD.md | Exact |
| RECONFIGURE 100% vs RETRY 0% on RESOURCE_UNAVAILABLE, n=40 each, Wilson CIs | MASTER_RECORD_CONTENT.md §19 | Exact |
| 3,106 records (3,060 + 46), splits 2,142/482/482, 1 environment | DATASET_CARD.md | Exact |
| 16 tasks / 8 tracks / 33 metrics / 10 baselines / 5 ablations, 0/6/3/0/7 status counts | BENCHMARK_CARD.md | Exact |
| Both Hugging Face URLs | Verified live via WebFetch during this phase (both pages returned real, matching content) | Confirmed reachable |
| MIT (code) / CC BY 4.0 (dataset) | RELEASE_DECISION.md, LICENSE files in both release packages | Exact |
| requirements.txt tech stack list | `requirements.txt` (root), read directly | Exact |
| Benchmark release package deps (numpy/pandas/scikit-learn/scipy only) | `release/benchmark/requirements.txt`, read directly | Exact |

## Defect found and fixed during this audit

The first draft of the README's "Quick start" and "CLI / API demo"
sections instructed readers to run `python -m src.benchmark.runner` as the
benchmark entry point. Direct inspection of `src/benchmark/runner.py`
showed **no `__main__` guard exists in that module** — running it as
`python -m src.benchmark.runner` executes successfully but does nothing
(confirmed: exit code 0, zero output, zero files written). The real entry
point, confirmed by reading `scripts/run_phase5_4_benchmark.py` and the
release package's own `scripts/` directory, is
`python scripts/run_phase5_4_benchmark.py`. **This was corrected in the
final README** before publication of this audit. This is exactly the kind
of claim-vs-code mismatch this audit step exists to catch.

## What was deliberately not re-verified line-by-line

- The full historical phase-history table (README "Research provenance
  summary") is a condensed restatement of `MASTER_RECORD_CONTENT.md` §5's
  own table, which is itself already the audited canonical source; it was
  not independently re-derived from raw experiment JSON in this phase.
- Docker/CI/CLI claims are covered by their own dedicated reports
  (`DOCKER_REPRODUCIBILITY_REPORT.md`, `CI_CD_VALIDATION_REPORT.md`,
  `API_CLI_VALIDATION_REPORT.md`) rather than duplicated here.

## Outcome

README.md passes this audit with one defect found and fixed (the
benchmark entry-point command). No other unsupported or incorrect claim
was found during this cross-check.
