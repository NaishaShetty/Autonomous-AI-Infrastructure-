from datetime import datetime, timezone

from src.failure_experience.ingest import ingest_batch
from src.failure_experience.retrieval import RetrievalQuery, retrieve
from src.failure_experience.sources import real_agentrx, real_aiops, real_alibaba
from src.failure_experience.storage import FailureExperienceRepository, get_session, reset_db
from src.failure_patterns import discovery_alibaba as da
from src.failure_patterns import discovery_descriptive as dd
from src.failure_patterns.schema import EvidenceTier

INGESTION_TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_protocol_loads_and_is_frozen():
    protocol = da.load_protocol()
    assert protocol["_frozen"] is True
    assert protocol["hypothesis"]["id"] == "H2-Alibaba"
    assert protocol["acceptance_criteria"]["minimum_evaluable_n"] == 50


def test_alibaba_population_matches_failure_experience_context_keys():
    """Cross-check: FailureExperience-ingested Alibaba failures' (task_name
    via affected_component, gpu_type via observations.system_state) pairs
    must all be valid contexts in the population this module reads
    directly from the same underlying CSV -- proving the two
    representations describe the same data even though FailureExperience
    itself cannot supply the full population denominator."""
    normalized, _ = real_alibaba.load_normalized(sample_size=50)
    result = ingest_batch(normalized, INGESTION_TS)
    assert result.experiences, "expected at least one ingested Alibaba FailureExperience"

    population = da.load_population(split_name="temporal")
    valid_keys = {(r["task_name"], r["gpu_type"]) for r in population}

    for exp in result.experiences:
        task_name = exp.failure.affected_component
        gpu_type = exp.observations.system_state.get("gpu_type") or ""
        assert (task_name, gpu_type) in valid_keys


def test_alibaba_discovery_end_to_end_on_real_data():
    protocol = da.load_protocol()
    rows = da.load_population(split_name="temporal")
    train_rows = [r for r in rows if r["split"] == "train"]
    val_rows = [r for r in rows if r["split"] == "val"]
    test_rows = [r for r in rows if r["split"] == "test"]

    discovered = da.discover(train_rows, protocol)
    assert len(discovered) > 0
    confirmed = da.confirm(discovered, val_rows, protocol)
    assert set(confirmed) == set(discovered)

    candidates = da.to_candidates(confirmed, "test_run", da.dataset_content_hash(), "temporal")
    assert any(c.tier == EvidenceTier.CONFIRMED for c in candidates), (
        "expected at least one CONFIRMED candidate on the real temporal split "
        "(regression guard against a silently degenerate tier assignment)"
    )

    test_outcomes = da.evaluate_test(candidates, test_rows, protocol)
    assert len(test_outcomes) == len(candidates)


def test_aiops_descriptive_pipeline_end_to_end():
    normalized = real_aiops.load_normalized()
    result = ingest_batch(normalized, INGESTION_TS)
    assert result.experiences

    associations = dd.aiops_recurrence(result.experiences, min_evidence_n=2)
    assert any(a.is_candidate for a in associations)

    temporal = dd.aiops_temporal_clustering(result.experiences)
    assert temporal["n_entities_total"] > 0


def test_agentrx_descriptive_pipeline_end_to_end():
    normalized = real_agentrx.load_normalized()
    result = ingest_batch(normalized, INGESTION_TS)
    assert result.experiences

    r = dd.agentrx_recurrence(result.experiences, min_evidence_n=2)
    assert r["temporal_clustering"] == "NOT_CURRENTLY_EVALUABLE"
    assert len(r["domains"]) >= 1


def test_failure_experience_retrieval_still_works_after_phase4_2_import():
    """Regression guard: importing src.failure_patterns must not break the
    active Phase 4.1 retrieval path it depends on."""
    reset_db("sqlite:///:memory:")
    normalized = real_aiops.load_normalized()[:5]
    result = ingest_batch(normalized, INGESTION_TS)
    with get_session() as session:
        repo = FailureExperienceRepository(session)
        repo.save_many(result.experiences)
    with get_session() as session:
        repo = FailureExperienceRepository(session)
        results = retrieve(repo, RetrievalQuery(source_dataset="aiops_kpi_2020"))
    assert len(results) == len(result.experiences)


def test_new_package_does_not_import_old_patterns_package():
    import ast
    import pathlib

    pkg_dir = pathlib.Path(__file__).resolve().parents[2] / "src" / "failure_patterns"
    for py_file in pkg_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("src.patterns"), f"{py_file} imports old src.patterns"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("src.patterns"), f"{py_file} imports old src.patterns"
