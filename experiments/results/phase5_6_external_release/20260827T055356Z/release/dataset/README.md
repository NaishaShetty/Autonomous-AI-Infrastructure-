---
license: cc-by-4.0
language:
  - en
task_categories:
  - text-classification
  - question-answering
tags:
  - autonomous-systems
  - uncertainty-estimation
  - failure-prediction
  - reliability
  - research
pretty_name: Autonomous AI Infrastructure — Phase 5.2 Canonical Dataset
size_categories:
  - 1K<n<10K
configs:
  - config_name: default
    data_files:
      - split: full
        path: data/all_records.jsonl
---

# Phase 5.2 Canonical Dataset — Release Package

3,106 records (3,060 agent-task + 46 controlled-runtime episodes)
supporting the paired Phase 5.3/5.4 benchmark. See `DATASET_CARD.md` for
the full description, limitations, and publication boundary.

## Contents

```
data/
  all_records.jsonl        the dataset itself, one JSON record per line
  dataset_statistics.json  breakdowns by track/split/failure-class/etc.
  split_audit.json         split-integrity audit (overlap counts, etc.)
  dataset_metadata.json    version/schema metadata
docs/
  PHASE5_1_SCHEMA.json            record schema
  PHASE5_1_SPLIT_POLICY.md        split axes and grouping rules
  PHASE5_1_LEAKAGE_POLICY.md      leakage rules this dataset was built to satisfy
  PHASE5_1_PROVENANCE_CONTRACT.md provenance requirements
  PHASE5_1_PUBLICATION_BOUNDARY.md what was/was not included and why
DATASET_README.md          original construction-time README (Phase 5.2)
```

## Verifying integrity

```
python -c "
import hashlib
h = hashlib.sha256(open('data/all_records.jsonl','rb').read()).hexdigest()
print(h)
assert h == '4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83'
print('OK: matches published SHA-256')
"
```

## Loading

Each line of `data/all_records.jsonl` is one JSON record conforming to
`docs/PHASE5_1_SCHEMA.json`. No special loader is required; the paired
benchmark package's `src/benchmark/dataset_loader.py` is a reference
implementation if you want split-aware, schema-validated loading.

## License

**CC BY 4.0** (Creative Commons Attribution 4.0 International). See
`LICENSE` in this directory, `CITATION.cff`, and `DATASET_CARD.md`'s
License section for the upstream-provenance audit backing this decision
(`LICENSE_PROVENANCE_AUDIT.md` in the Phase 5.6 release directory).

## Citation

See `CITATION.cff`.
