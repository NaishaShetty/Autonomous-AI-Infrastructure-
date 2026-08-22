# V1.1 Experiment Results

This directory is reserved for Phase 3.1 and later experiments. It is intentionally separate from all historical V1.0 evidence under `experiments/results/`.

Each finalized experiment must use the contract in `configs/phase3_evaluation_contract.json` and the immutable writer in `src/phase3_contract.py`. A finalized result contains `protocol.json`, `manifest.json`, `results.json`, `summary.json`, `report.md`, optional `per_seed/` outputs, and a `.finalized` digest marker. Finalized artifacts must not be overwritten. No speculative experiment results are included in Phase 3.0.
