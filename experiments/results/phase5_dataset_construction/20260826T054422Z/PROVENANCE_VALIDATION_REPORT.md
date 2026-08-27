# Phase 5.2 Provenance Validation Report

Total records: 3106
Total provenance problems: 0

## Label type distribution (across all labels[] entries)
- DERIVED_LABEL: 46
- OBJECTIVE_GROUND_TRUTH: 3060
- OBSERVED_OUTCOME_VALIDATED: 35

**Result: PASS**

## What was checked
- every record's provenance object has source/source_version/extraction_method/timestamp_quality/evidence_class
- every record's provenance.checksum matches a real, recorded sha256 of an actual frozen source file (dataset_metadata.json)
- every labels[] entry with is_ground_truth_eligible=true has label_type in {OBJECTIVE_GROUND_TRUTH, OBSERVED_OUTCOME_VALIDATED} only
- diagnosis/prediction/decision/validation sub-objects carry their schema-mandated, non-substitutable label_type
