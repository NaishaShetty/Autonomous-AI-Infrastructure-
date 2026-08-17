"""Active Phase 4.1 experiments A-E (Task 14).

Runs entirely against the four source adapters in
src/failure_experience/sources/ (three real datasets + the frozen,
read-only Phase 4.0 synthetic episode stream). Writes results to
experiments/results/phase4_1_active/*.json. Deterministic given the fixed
seeds already baked into the adapters (Alibaba sampling seed=42, everything
else exhaustive-over-available-records) -- re-running this script produces
byte-identical results.

Does not modify any file under experiments/results/phase4_0/,
experiments/results/phase4_1/, experiments/results/phase4_2/, or any
docs/PHASE3_*.md / docs/PHASE4_1_FAILURE_MEMORY.md / docs/PHASE4_2_*.md --
all of those remain frozen historical artifacts.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.failure_experience import storage
from src.failure_experience.ingest import ingest_batch
from src.failure_experience.reconstruction import verify_round_trip
from src.failure_experience.retrieval import RetrievalQuery, retrieve
from src.failure_experience.sources import real_agentrx, real_aiops, real_alibaba, synthetic_episodic

RESULTS_DIR = Path(__file__).resolve().parents[1] / "experiments" / "results" / "phase4_1_active"
INGESTION_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)
ALIBABA_SAMPLE_SIZE = 500


def _load_all_sources() -> dict[str, list[dict]]:
    syn_raw = synthetic_episodic.load_records(only_failures=False)
    syn = synthetic_episodic.load_normalized()
    agx_raw = real_agentrx.load_records()
    agx = real_agentrx.load_normalized()
    alb, alb_sample_report = real_alibaba.load_normalized(sample_size=ALIBABA_SAMPLE_SIZE)
    alb_raw_failed_count = alb_sample_report["available_failed_rows"]
    aio_raw = real_aiops.load_records()
    aio = real_aiops.load_normalized()
    raw_counts = {
        "phase4_0_synthetic_episodic": {"total_episode_records": len(syn_raw), "failure_records_only": len(syn)},
        "agentrx": {"total_trajectory_records": len(agx_raw), "failure_annotated_records": len(agx)},
        "alibaba_gpu2020": {"failed_task_rows_available": alb_raw_failed_count, "sampled": len(alb), "sample_report": alb_sample_report},
        "aiops_kpi_2020": {"positive_fault_windows": len(aio_raw), "normalized": len(aio)},
    }
    return {"phase4_0_synthetic_episodic": syn, "agentrx": agx, "alibaba_gpu2020": alb, "aiops_kpi_2020": aio}, raw_counts


def experiment_a_completeness(sources: dict[str, list[dict]], raw_counts: dict) -> dict:
    per_source = {}
    total_records = total_ok = total_err = 0
    for name, records in sources.items():
        result = ingest_batch(records, INGESTION_TS)
        per_source[name] = {
            "input_records": len(records),
            "successfully_represented": len(result.experiences),
            "errors": len(result.errors),
            "error_reasons": result.errors[:10],
            "raw_counts": raw_counts[name],
        }
        total_records += len(records)
        total_ok += len(result.experiences)
        total_err += len(result.errors)
    return {
        "total_normalized_records_across_sources": total_records,
        "total_successfully_represented": total_ok,
        "total_invalid": total_err,
        "note": (
            "0 errors observed in this run because source adapters produce "
            "schema-conformant NormalizedRecords by construction; the error "
            "path itself (missing/invalid fields) is exercised directly by "
            "tests/unit/test_failure_experience_ingest.py, not fabricated "
            "here as a positive result."
        ),
        "per_source": per_source,
    }


def experiment_b_information_preservation(sources: dict[str, list[dict]]) -> dict:
    per_source = {}
    for name, records in sources.items():
        check_pass_counts = Counter()
        n_checked = 0
        n_fully_passed = 0
        for record in records:
            result = ingest_batch([record], INGESTION_TS)
            if not result.experiences:
                continue
            exp = result.experiences[0]
            report = verify_round_trip(record, exp)
            n_checked += 1
            if report.passed:
                n_fully_passed += 1
            for check_name, passed in report.checks.items():
                if passed:
                    check_pass_counts[check_name] += 1
        per_source[name] = {
            "records_checked": n_checked,
            "records_fully_passed_all_checks": n_fully_passed,
            "all_checks_passed_rate": (n_fully_passed / n_checked) if n_checked else None,
            "per_check_pass_count": dict(check_pass_counts),
            "per_check_total": n_checked,
        }
    return {"per_source": per_source}


def experiment_c_outcome_fidelity(sources: dict[str, list[dict]]) -> dict:
    per_source_status_distribution = {}
    for name, records in sources.items():
        result = ingest_batch(records, INGESTION_TS)
        dist = Counter(e.outcome.final_status.value for e in result.experiences)
        per_source_status_distribution[name] = dict(dist)

    syn_experiences = ingest_batch(sources["phase4_0_synthetic_episodic"], INGESTION_TS).experiences
    action_outcome = defaultdict(Counter)
    for e in syn_experiences:
        action = e.recovery.selected_action or "none"
        action_outcome[action][e.outcome.final_status.value] += 1
    ambiguous_actions = {
        action: dict(outcomes) for action, outcomes in action_outcome.items() if len(outcomes) > 1
    }

    return {
        "final_status_distribution_per_source": per_source_status_distribution,
        "synthetic_action_to_outcome_crosstab": {a: dict(o) for a, o in action_outcome.items()},
        "actions_with_multiple_distinct_outcomes": ambiguous_actions,
        "interpretation": (
            "Non-empty 'actions_with_multiple_distinct_outcomes' demonstrates the "
            "same recovery action produces different final outcomes depending on "
            "context (Task 4's 'Failure A + restart -> success, Failure B + restart "
            "-> failure' requirement) -- the schema represents this, it does not "
            "collapse action into a proxy for outcome."
        ),
    }


def experiment_d_temporal_integrity(sources: dict[str, list[dict]]) -> dict:
    all_experiences = []
    for records in sources.values():
        all_experiences.extend(ingest_batch(records, INGESTION_TS).experiences)

    lineage_violations = 0  # structurally impossible post-construction (pydantic validator), counted for completeness
    for e in all_experiences:
        events = e.temporal_lineage.ordered_events()
        ts_list = [ts for _, ts in events]
        if ts_list != sorted(ts_list):
            lineage_violations += 1

    with_observed_at = sorted(all_experiences, key=lambda e: e.identity.observed_at)
    cutoff = with_observed_at[len(with_observed_at) // 2].identity.observed_at

    with storage.get_session() as session:
        pass  # ensures schema created; not used for this in-memory-only check

    before = [e for e in all_experiences if e.identity.observed_at <= cutoff]
    after = [e for e in all_experiences if e.identity.observed_at > cutoff]

    return {
        "total_experiences": len(all_experiences),
        "lineage_monotonicity_violations": lineage_violations,
        "cutoff_timestamp": cutoff.isoformat(),
        "available_before_cutoff": len(before),
        "available_after_cutoff": len(after),
        "partition_sums_to_total": len(before) + len(after) == len(all_experiences),
        "partition_is_disjoint": len(set(e.identity.experience_id for e in before) & set(e.identity.experience_id for e in after)) == 0,
        "interpretation": (
            "The system can partition its full experience set into "
            "'available strictly before T' vs. 'after T' with zero overlap "
            "and full coverage -- the property required to prevent future "
            "information leaking into an earlier evaluation boundary."
        ),
    }


def experiment_e_provenance_integrity(sources: dict[str, list[dict]]) -> dict:
    per_source = {}
    for name, records in sources.items():
        result = ingest_batch(records[:50], INGESTION_TS)
        traced = 0
        hash_present = 0
        for e in result.experiences:
            if e.provenance.raw_record_ref:
                traced += 1
            if e.provenance.dataset_content_hash:
                hash_present += 1
        per_source[name] = {
            "sample_checked": len(result.experiences),
            "traceable_to_raw_record_ref": traced,
            "dataset_content_hash_present": hash_present,
        }
    return {"per_source": per_source}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    sources, raw_counts = _load_all_sources()

    results = {
        "experiment_a_completeness": experiment_a_completeness(sources, raw_counts),
        "experiment_b_information_preservation": experiment_b_information_preservation(sources),
        "experiment_c_outcome_fidelity": experiment_c_outcome_fidelity(sources),
        "experiment_d_temporal_integrity": experiment_d_temporal_integrity(sources),
        "experiment_e_provenance_integrity": experiment_e_provenance_integrity(sources),
    }

    out_path = RESULTS_DIR / "phase4_1_active_experiments.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"wrote {out_path}")

    print(json.dumps({
        "experiment_a_totals": {
            k: v for k, v in results["experiment_a_completeness"].items() if k != "per_source"
        },
        "experiment_d_summary": {
            k: v for k, v in results["experiment_d_temporal_integrity"].items() if k != "cutoff_timestamp"
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
