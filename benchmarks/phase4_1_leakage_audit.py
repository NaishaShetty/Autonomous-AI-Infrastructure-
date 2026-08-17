"""Phase 4.1 leakage/integrity audit. Mirrors the project's existing
leakage-audit convention (benchmarks/phase3_6_leakage_audit.py,
benchmarks/phase4_0_leakage_audit.py).

Run: python benchmarks/phase4_1_leakage_audit.py
Writes: experiments/results/phase4_1/leakage_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.synthetic import FEATURE_NAMES  # noqa: E402
from src.experience.schema import DecisionTimeQuery, experience_from_episode_record  # noqa: E402
from src.experience.store import build_store_from_episode_records  # noqa: E402

PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_1"


def _load():
    records = json.loads((PHASE4_0_DIR / "episodes.json").read_text())
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    return records, manifest["content_hash_sha256"]


def check_store_contains_only_train_split(records, dataset_hash) -> dict:
    store = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    violations = [e for e in store.experiences if e.provenance.split != "train"]
    return {"name": "store_contains_only_train_split", "passed": len(violations) == 0, "detail": f"{len(violations)} non-train rows in store"}


def check_store_contains_only_failures(records, dataset_hash) -> dict:
    store = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    violations = [e for e in store.experiences if not e.event.is_failure]
    return {"name": "store_contains_only_is_failure_true_rows", "passed": len(violations) == 0, "detail": f"{len(violations)} non-failure rows in store"}


def check_decision_time_query_type_excludes_ground_truth() -> dict:
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(DecisionTimeQuery)}
    forbidden = {"condition_id", "true_label", "outcome", "is_failure", "recovery_action", "recovery_outcome", "recovery_correct"}
    overlap = field_names & forbidden
    return {"name": "decision_time_query_excludes_ground_truth_and_outcome_fields", "passed": len(overlap) == 0, "detail": f"overlap={sorted(overlap)}"}


def check_store_build_is_deterministic(records, dataset_hash) -> dict:
    a = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    b = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    same = a.content_hash() == b.content_hash()
    return {"name": "store_content_hash_is_deterministic", "passed": same, "detail": f"{a.content_hash()[:12]} vs {b.content_hash()[:12]}"}


def check_no_test_or_validation_row_reachable_from_store(records, dataset_hash) -> dict:
    store = build_store_from_episode_records(records, FEATURE_NAMES, "v", dataset_hash, split="train")
    store_ids = {e.event.event_id for e in store.experiences}
    non_train_ids = set()
    for r in records:
        if r["split"] != "train" and r["is_failure"]:
            exp = experience_from_episode_record(r, "v", dataset_hash)
            non_train_ids.add(exp.event.event_id)
    overlap = store_ids & non_train_ids
    return {"name": "no_validation_or_test_event_id_present_in_store", "passed": len(overlap) == 0, "detail": f"{len(overlap)} overlapping ids"}


def check_retrieval_on_empty_store_returns_empty_not_error() -> dict:
    from src.experience.store import ExperienceStore

    store = ExperienceStore(FEATURE_NAMES)
    q = DecisionTimeQuery(context={f: 0.0 for f in FEATURE_NAMES}, confidence=0.5, workload_id="w", tier="LOW", diagnosed_cause=None, step=0)
    try:
        r_random = store.retrieve_random(q, k=5, seed=1)
        r_recency = store.retrieve_recency(q, k=5)
        r_sim = store.retrieve_similarity(q, k=5)
        ok = r_random == [] and r_recency == [] and r_sim == []
        detail = "ok" if ok else f"{r_random}, {r_recency}, {r_sim}"
    except Exception as e:  # noqa: BLE001
        ok = False
        detail = f"raised {type(e).__name__}: {e}"
    return {"name": "retrieval_on_empty_store_returns_empty_not_error", "passed": ok, "detail": detail}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records, dataset_hash = _load()

    checks = [
        check_store_contains_only_train_split(records, dataset_hash),
        check_store_contains_only_failures(records, dataset_hash),
        check_decision_time_query_type_excludes_ground_truth(),
        check_store_build_is_deterministic(records, dataset_hash),
        check_no_test_or_validation_row_reachable_from_store(records, dataset_hash),
        check_retrieval_on_empty_store_returns_empty_not_error(),
    ]
    all_passed = all(c["passed"] for c in checks)
    output = {"all_passed": all_passed, "checks": checks}
    (RESULTS_DIR / "leakage_audit.json").write_text(json.dumps(output, indent=2))

    print("Phase 4.1 leakage audit\n")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['name']} -- {c['detail']}")
    print(f"\nALL PASSED: {all_passed}")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
