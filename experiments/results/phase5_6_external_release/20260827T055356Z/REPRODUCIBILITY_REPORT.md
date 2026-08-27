# Phase 5.6 — Reproducibility Metadata

## Versions and environment (this audit run)

| Field | Value |
|---|---|
| Repository git commit (this phase) | `8086e7185d0917e8431749db0f0c47ba18088eb5` |
| Dataset version | `phase5.2-dataset-v1.0.0` |
| Schema version | `phase5.1-schema-v1.0.0` |
| Benchmark version | `phase5.3-benchmark-v1.0.0` |
| Benchmark implementation version | `phase5.4-implementation-v1.0.0` |
| Metric version | `phase5.3-metrics-v1.0.0` |
| Python version | 3.11.3 (tags/v3.11.3:f3909b8, Apr 4 2023) |
| numpy | 2.4.6 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.0 |
| scipy | 1.17.1 |
| OS (coarsened, no hostname) | Windows-10-AMD64 |
| Bootstrap seed | 20260826 |
| Benchmark config hash | `d8d349a545a1910bfada66de5628cf3ebb52c50f9a15465dd34840ab8de5e08b` |
| Dataset `all_records.jsonl` SHA-256 | `4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83` |
| Benchmark release package SHA-256 manifest | this directory's `SHA256_MANIFEST.json` (generated last, after all content is finalized) |

## No Python `hash()` usage

`src/benchmark/ids.py` module docstring: *"Deterministic SHA-256
identifiers. Never uses Python's salted hash()."* Verified by direct
grep of every `.py` file in `release/benchmark/src/benchmark/`
(`grep -rn "\bhash(" *.py`) — the only 3 matches are docstring/comment
prose asserting the absence, not an actual call; `sha256_canonical_json`
in `ids.py` and `reproducibility.py` use `hashlib.sha256` throughout.
`collect_reproducibility_metadata()` in `reproducibility.py` sets an
explicit `"no_python_hash_used": True` field in every run's metadata.

## No filesystem-order dependence

Established originally in Phase 5.2 (dataset construction, canonical
record ordering fixed by `record_id`) and Phase 5.4 (benchmark
implementation). This phase's own spot-check: `grep -rn "os.listdir\|glob.glob\|iterdir"` across
`src/benchmark/*.py` returns 0 matches — the implementation never
iterates a directory and relies on OS-returned order; all record
ordering is driven by the explicit, sorted `all_records.jsonl` line
order and dict/JSON key access, not directory listings.
`collect_reproducibility_metadata()` sets an explicit
`"no_filesystem_order_dependence": True` field. Independently confirmed
behaviorally: the clean-room run's internal double-execution
determinism check (`determinism_check`) reported all 4 sub-checks
`true`, and the clean-room run's full result was field-identical
(modulo expected run metadata) to the original Phase 5.4 run performed
on a different machine/day — see `CLEAN_ROOM_REPRODUCTION_REPORT.md`.

## Host-identity exclusion, verified in code

`src/benchmark/reproducibility.py::platform_string()` explicitly builds
`f"{platform.system()}-{platform.release()}-{platform.machine()}"` and
its comment states this is "coarsened per PHASE5_1_PUBLICATION_BOUNDARY.md
host-identity exclusion... never `platform.node()` (hostname)." Confirmed
by reading the function: `platform.node()` is never called anywhere in
`src/benchmark/`.

## Reproduction instructions (already shipped, verified working)

`release/benchmark/REPRODUCIBILITY_GUIDE.md` and `release/dataset/README.md`
both ship copy-pasteable instructions (pip install, SHA-256 verification
snippet, `python scripts/run_phase5_4_benchmark.py`). These exact
instructions were followed verbatim in `CLEAN_ROOM_REPRODUCTION_REPORT.md`
and succeeded.

## Conclusion

All required reproducibility metadata is present and independently
verified this phase, on top of (not merely repeating) Phase 5.2/5.4's
original determinism work. No hash()-order or filesystem-order
dependence found; host identity is explicitly excluded from all
metadata by code, not merely by policy.
