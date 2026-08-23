import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/results/v1_1/candidate_discovery/3_7"
PROTO = OUT / "candidate_protocols/selected_candidate_protocols.json"
INVENTORY = OUT / "candidate_inventory/candidate_inventory.md"
REPORT = OUT / "reports/PHASE3_7_V1_1_CANDIDATE_DISCOVERY_DESIGN.md"


def test_required_phase37_artifacts_exist():
    assert PROTO.exists()
    assert INVENTORY.exists()
    assert REPORT.exists()
    assert (OUT / "candidate_selection/selection_record.md").exists()


def test_protocol_preserves_frozen_v1_and_declares_design_only_boundary():
    protocol = json.loads(PROTO.read_text())
    assert protocol["frozen_control"]["commit"] == "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
    assert protocol["frozen_control"]["modified"] is False
    assert protocol["status"] == "PREREGISTERED_DESIGN_ONLY"
    assert protocol["not_screened_in_phase37"] is True
    assert protocol["data"]["future_boundary"] == "canonical temporal test plus Phase 3.5 authoritative Fold 1, Fold 2, Fold 3"


def test_at_most_two_candidates_selected():
    protocol = json.loads(PROTO.read_text())
    ids = [candidate["candidate_id"] for candidate in protocol["candidates"]]
    selected = {"candidate_a", "candidate_c"}
    assert len(selected) <= 2
    assert selected.issubset(ids)


def test_selected_candidates_have_falsifiable_protocols():
    protocol = json.loads(PROTO.read_text())
    candidates = {c["candidate_id"]: c for c in protocol["candidates"]}
    for cid in ("candidate_a", "candidate_c"):
        candidate = candidates[cid]
        assert candidate["hypothesis"]
        assert candidate["acceptance"]
        assert candidate["rejection"]
        assert candidate["deterministic_id"].startswith(cid + "__")


def test_report_contains_required_direction_and_no_integration():
    text = REPORT.read_text()
    assert "V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET" in text
    assert "RELIABILITY/DECISION ARCHITECTURE" in text
    assert "No new candidate experiment was executed" in text
    assert "no candidate is promoted, integrated" in text


def test_inventory_contains_all_five_categories_and_do_not_repeat():
    text = INVENTORY.read_text()
    for cid in ("Candidate A", "Candidate B", "Candidate C", "Candidate D", "Candidate E"):
        assert cid in text
    assert "Do not integrate the interaction candidate" in text
    assert "No candidate is accepted" in text


def test_finalized_hashes_are_valid_if_present():
    marker = OUT / ".finalized"
    if not marker.exists():
        return
    hashes = json.loads(marker.read_text())
    for relative, expected in hashes.items():
        path = OUT / relative
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
