"""Post-P5 remediation, Step 4 -- unit coverage for the dual-feature
(Model A / Model B) environment corpus generator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_p4_step4_environment_generalization import generate_dual_corpus_for_environment, _rows_with_features
from src.phase4.environments import BASELINE_CPU, MEMORY_CONSTRAINED


def test_dual_corpus_rows_carry_both_feature_representations():
    rows = generate_dual_corpus_for_environment(BASELINE_CPU, list(range(0, 25)), "unit-dual")
    assert rows, "expected rows from a 25-seed corpus"
    assert all(len(r.features_a) == 4 for r in rows)
    assert all(len(r.features_b) == 5 for r in rows)
    # features_a/features_b must come from the SAME real run (first 4 dims agree; only the 5th differs at most)
    assert all(r.features_a == r.features_b[:4] for r in rows)


def test_oom_rows_get_a_different_env_normalized_rss_under_a_tighter_budget():
    baseline_rows = [r for r in generate_dual_corpus_for_environment(BASELINE_CPU, list(range(0, 60)), "unit-dual-a") if r.mode == "oom"]
    constrained_rows = [r for r in generate_dual_corpus_for_environment(MEMORY_CONSTRAINED, list(range(0, 60)), "unit-dual-b") if r.mode == "oom"]
    assert baseline_rows and constrained_rows, "expected oom-mode rows in both environments for a 60-seed corpus"
    # The env-normalized feature (index 4) must differ from the fixed-baseline feature (index 0)
    # for at least some rows where real telemetry was observed (peak RSS > 0).
    differs = any(abs(r.features_b[4] - r.features_b[0]) > 1e-9 for r in baseline_rows + constrained_rows if r.features_b[0] > 0 or r.features_b[4] > 0)
    assert differs, "expected at least one oom row where env-normalized RSS differs from fixed-baseline RSS"


def test_rows_with_features_selects_the_requested_variant():
    rows = generate_dual_corpus_for_environment(BASELINE_CPU, list(range(0, 15)), "unit-dual-select")
    a_rows = _rows_with_features(rows, "A")
    b_rows = _rows_with_features(rows, "B")
    assert all(len(r.features) == 4 for r in a_rows)
    assert all(len(r.features) == 5 for r in b_rows)
