"""Source adapters: raw, dataset-specific records -> NormalizedRecord dicts
consumed by src.failure_experience.ingest.ingest_record / ingest_batch.

Each adapter is read-only with respect to its input files (data/, or the
frozen experiments/results/phase4_0/episodes.json deliverable) -- none of
them write to or modify any existing dataset, audit, or results file.
"""
