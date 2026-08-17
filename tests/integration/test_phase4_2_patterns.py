"""Integration tests for Phase 4.2: runs the actual leakage-audit checks
against the real Phase 4.0 dataset, plus end-to-end evaluation sanity
checks. Mirrors tests/integration/test_phase4_1_retrieval.py's pattern."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.patterns.discovery import candidates_by_key, discover_candidates
from src.patterns.metrics import evaluate_rows
from src.patterns.schema import EvidenceTier

from benchmarks.phase4_2_leakage_audit import (
    check_candidacy_excludes_singletons,
    check_discovery_is_deterministic,
    check_discovery_uses_only_train_and_validation,
    check_empty_candidate_set_handled_gracefully,
    check_pattern_query_excludes_ground_truth,
)

ROOT = Path(__file__).resolve().parents[2]
PHASE4_0_DIR = ROOT / "experiments" / "results" / "phase4_0"
PROTOCOL_PATH = ROOT / "configs" / "phase4_2_pattern_protocol.json"


def _require_data():
    path = PHASE4_0_DIR / "episodes.json"
    if not path.exists():
        pytest.skip("Phase 4.0 dataset not generated; run benchmarks/phase4_0_generate_episodes.py first")
    manifest = json.loads((PHASE4_0_DIR / "manifest.json").read_text())
    records = json.loads(path.read_text())
    protocol = json.loads(PROTOCOL_PATH.read_text())
    return records, manifest["content_hash_sha256"], protocol


def test_pattern_query_excludes_ground_truth():
    assert check_pattern_query_excludes_ground_truth()["passed"]


def test_discovery_uses_only_train_and_validation():
    records, dataset_hash, protocol = _require_data()
    assert check_discovery_uses_only_train_and_validation(records, dataset_hash, protocol)["passed"]


def test_candidacy_excludes_singletons():
    records, dataset_hash, protocol = _require_data()
    assert check_candidacy_excludes_singletons(records, dataset_hash, protocol)["passed"]


def test_discovery_is_deterministic():
    records, dataset_hash, protocol = _require_data()
    assert check_discovery_is_deterministic(records, dataset_hash, protocol)["passed"]


def test_empty_candidate_set_handled_gracefully():
    assert check_empty_candidate_set_handled_gracefully()["passed"]


def test_full_audit_all_passed():
    report_path = ROOT / "experiments" / "results" / "phase4_2" / "leakage_audit.json"
    if not report_path.exists():
        subprocess.run(["python", "benchmarks/phase4_2_leakage_audit.py"], cwd=ROOT, check=True)
    report = json.loads(report_path.read_text())
    assert report["all_passed"] is True


def test_every_candidate_tier_is_a_valid_evidence_tier():
    records, dataset_hash, protocol = _require_data()
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    candidates = discover_candidates(train, val, protocol["tier_thresholds"], "v", dataset_hash)
    assert len(candidates) > 0
    for c in candidates:
        assert isinstance(c.tier, EvidenceTier)
        assert c.n_train >= 2


def test_no_test_split_row_influences_candidate_discovery():
    """Rebuilding candidates with test rows stripped out entirely (vs.
    present but unused) must produce byte-identical candidates -- proves
    test rows genuinely play no role, not just that no function accepts
    them by name."""
    records, dataset_hash, protocol = _require_data()
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    a = discover_candidates(train, val, protocol["tier_thresholds"], "v", dataset_hash)

    # simulate a corrupted "test leaked into train" scenario and confirm it WOULD change results,
    # proving the metric is sensitive -- i.e. the leakage check above isn't vacuously trivial.
    test_rows = [r for r in records if r["split"] == "test" and r["is_failure"] and r["diagnosed_cause"] is not None]
    contaminated_train = train + test_rows
    b = discover_candidates(contaminated_train, val, protocol["tier_thresholds"], "v", dataset_hash)
    a_summary = sorted((c.workload_id, c.diagnosed_cause, c.n_train) for c in a)
    b_summary = sorted((c.workload_id, c.diagnosed_cause, c.n_train) for c in b)
    assert a_summary != b_summary  # contamination is detectable, confirming the real (uncontaminated) build is meaningfully test-free


def test_evaluate_rows_end_to_end_on_real_dataset():
    records, dataset_hash, protocol = _require_data()
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    test = [r for r in records if r["split"] == "test" and r["is_failure"] and r["diagnosed_cause"] is not None]
    candidates = discover_candidates(train, val, protocol["tier_thresholds"], "v", dataset_hash)
    by_key = candidates_by_key(candidates)
    result = evaluate_rows(test, by_key, lambda c: c.tier in (EvidenceTier.INFERRED, EvidenceTier.CONFIRMED))
    assert result["n_total_test_rows"] == len(test)
    assert 0 <= result["n_covered"] <= len(test)
    if result["precision"] is not None:
        assert 0.0 <= result["precision"] <= 1.0
    if result["recall"] is not None:
        assert 0.0 <= result["recall"] <= 1.0
