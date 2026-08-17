"""Phase 4.2 leakage/integrity audit."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.patterns.discovery import discover_candidates  # noqa: E402
from src.patterns.metrics import evaluate_rows  # noqa: E402
from src.patterns.schema import PatternQuery  # noqa: E402

PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"
PROTOCOL_PATH = ROOT / "configs" / "phase4_2_pattern_protocol.json"
RESULTS_DIR = ROOT / "experiments" / "results" / "phase4_2"


def _load():
    records = json.loads((PHASE4_0_DIR / "episodes.json").read_text())
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    protocol = json.loads(PROTOCOL_PATH.read_text())
    return records, manifest["content_hash_sha256"], protocol


def check_pattern_query_excludes_ground_truth() -> dict:
    field_names = {f.name for f in dataclasses.fields(PatternQuery)}
    forbidden = {"condition_id", "true_label", "outcome", "is_failure", "recovery_action", "recovery_outcome", "recovery_correct"}
    overlap = field_names & forbidden
    return {"name": "pattern_query_excludes_ground_truth_and_outcome_fields", "passed": len(overlap) == 0, "detail": f"overlap={sorted(overlap)}"}


def check_discovery_uses_only_train_and_validation(records, dataset_hash, protocol) -> dict:
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    thresholds = protocol["tier_thresholds"]
    candidates = discover_candidates(train, val, thresholds, "v", dataset_hash)
    test_row_keys = {(r["workload_id"], r["diagnosed_cause"]) for r in records if r["split"] == "test" and r["diagnosed_cause"] is not None}
    train_or_val_keys = {(r["workload_id"], r["diagnosed_cause"]) for r in (train + val) if r["diagnosed_cause"] is not None}
    only_from_test = test_row_keys - train_or_val_keys
    candidate_keys = {(c.workload_id, c.diagnosed_cause) for c in candidates}
    violation = candidate_keys & only_from_test
    return {"name": "no_candidate_derived_only_from_test_split", "passed": len(violation) == 0, "detail": f"violating keys={sorted(violation)}"}


def check_candidacy_excludes_singletons(records, dataset_hash, protocol) -> dict:
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    thresholds = protocol["tier_thresholds"]
    candidates = discover_candidates(train, val, thresholds, "v", dataset_hash)
    singleton_violations = [c for c in candidates if c.n_train < 2]
    return {"name": "candidacy_rule_excludes_n_train_below_2", "passed": len(singleton_violations) == 0, "detail": f"{len(singleton_violations)} violations"}


def check_discovery_is_deterministic(records, dataset_hash, protocol) -> dict:
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    thresholds = protocol["tier_thresholds"]
    a = discover_candidates(train, val, thresholds, "v", dataset_hash)
    b = discover_candidates(train, val, thresholds, "v", dataset_hash)
    same = [(c.workload_id, c.diagnosed_cause, c.tier) for c in a] == [(c.workload_id, c.diagnosed_cause, c.tier) for c in b]
    return {"name": "discovery_is_deterministic", "passed": same, "detail": f"{len(a)} candidates, stable={same}"}


def check_empty_candidate_set_handled_gracefully() -> dict:
    try:
        result = evaluate_rows([], {}, lambda c: True)
        ok = result["n_covered"] == 0 and result["precision"] is None and result["recall"] is None
        detail = "ok" if ok else str(result)
    except Exception as e:  # noqa: BLE001
        ok = False
        detail = f"raised {type(e).__name__}: {e}"
    return {"name": "empty_candidate_or_row_set_handled_gracefully", "passed": ok, "detail": detail}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records, dataset_hash, protocol = _load()

    checks = [
        check_pattern_query_excludes_ground_truth(),
        check_discovery_uses_only_train_and_validation(records, dataset_hash, protocol),
        check_candidacy_excludes_singletons(records, dataset_hash, protocol),
        check_discovery_is_deterministic(records, dataset_hash, protocol),
        check_empty_candidate_set_handled_gracefully(),
    ]
    all_passed = all(c["passed"] for c in checks)
    output = {"all_passed": all_passed, "checks": checks}
    (RESULTS_DIR / "leakage_audit.json").write_text(json.dumps(output, indent=2))

    print("Phase 4.2 leakage audit\n")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['name']} -- {c['detail']}")
    print(f"\nALL PASSED: {all_passed}")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
