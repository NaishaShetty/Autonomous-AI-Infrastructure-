import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/results/v1_1/failure_forensics/3_9"


def test_phase39_required_artifacts_exist():
    assert (OUT / "protocol/phase39_protocol.json").exists()
    assert (OUT / "failure_taxonomy/taxonomy.json").exists()
    assert (OUT / "information_gap/availability_matrix.json").exists()
    assert (OUT / "information_gap/information_gap_matrix.csv").exists()
    assert (OUT / "error_signatures/univariate/univariate_signatures.csv").exists()
    assert (OUT / "error_signatures/cross_fold/cross_fold_signatures.csv").exists()
    assert (OUT / "opportunity_map/opportunity_matrix.csv").exists()
    assert (OUT / "PHASE3_9_SYNTHESIS.md").exists()
    assert (OUT / ".finalized").exists()


def test_protocol_preserves_frozen_v1_and_registered_populations():
    protocol = json.loads((OUT / "protocol/phase39_protocol.json").read_text())
    assert protocol["frozen_v1_commit"] == "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
    assert protocol["evaluation_populations"] == ["random_stratified", "canonical_temporal", "fold_1", "fold_2", "fold_3"]
    assert protocol["no_model_search"] is True
    assert protocol["no_candidate_implementation"] is True
    assert len(protocol["feature_contract"]) == 14


def test_case_level_forensics_reproduces_required_labels():
    import pandas as pd
    cases = pd.read_csv(OUT / "tables/case_level_forensics.csv")
    assert {"correct", "predicted_label", "risk_score", "uncertainty", "primary_failure_category", "secondary_tags"}.issubset(cases.columns)
    assert set(cases.population.unique()) == {"random_stratified", "canonical_temporal", "fold_1", "fold_2", "fold_3"}
    assert set(cases.primary_failure_category.unique()).issubset({"correct", "high_confidence_error", "low_confidence_error"})
    assert ((cases.predicted_label == (cases.risk_score >= 0.5).astype(int))).all()
    assert ((cases.correct == (cases.predicted_label == cases.label))).all()


def test_taxonomy_is_small_explicit_and_noncausal():
    taxonomy = json.loads((OUT / "failure_taxonomy/taxonomy.json").read_text())
    assert taxonomy["case_count"] > 0
    assert taxonomy["category_policy"]
    assert "causal feature mechanism" in taxonomy["unsupported_categories"]
    assert len(taxonomy["primary_categories"]) == 2
    for row in taxonomy["primary_categories"]:
        assert row["cases"] >= 0
        assert row["cross_fold_stability"] in {"ROBUST", "REGIME-SPECIFIC"}


def test_information_gap_has_required_classifications():
    rows = json.loads((OUT / "information_gap/availability_matrix.json").read_text())
    assert {row["classification"] for row in rows}.issubset(set("ABCDEF"))
    assert any(row["classification"] == "D" for row in rows)
    assert any(row["classification"] == "F" for row in rows)
    assert all("leakage_risk" in row for row in rows)


def test_cross_fold_signatures_cover_all_features_and_future_populations():
    import pandas as pd
    cross = pd.read_csv(OUT / "error_signatures/cross_fold/cross_fold_signatures.csv")
    assert set(cross.feature) == set(json.loads((OUT / "protocol/phase39_protocol.json").read_text())["feature_contract"])
    assert {"canonical_temporal_smd", "fold_1_smd", "fold_2_smd", "fold_3_smd", "signature_stability"}.issubset(cross.columns)
    assert set(cross.signature_stability).issubset({"ROBUST", "UNSTABLE", "UNRESOLVED"})


def test_opportunity_map_does_not_force_candidate_integration():
    text = (OUT / "PHASE3_9_SYNTHESIS.md").read_text()
    assert "V1 FAILURE MECHANISM REMAINS UNRESOLVED" in text
    assert "no V1.1 integration is authorized" in text
    assert "Do not begin V1.1 integration" in text


def test_finalized_sha256_manifest_matches_all_files():
    hashes = json.loads((OUT / ".finalized").read_text())
    for rel, expected in hashes.items():
        path = OUT / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
