"""Post-P5 remediation, Step 6 (P5-W1/P5-W2) -- integration coverage for
the repeated-incident memory experiment: memory ON (persisted across
simulated restarts) must change the planner's decision once the existing,
unmodified avoidance rule accumulates enough evidence; memory OFF (fresh
store every episode) must never change it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_p5_step6_memory_repeated_incident import restart_persistence_check, run_condition


def test_memory_on_switches_action_after_two_confirmed_failures_and_self_corrects(tmp_path):
    db_path = tmp_path / "memory_on.sqlite"
    episodes = run_condition("ON", db_path)
    actions = [e["action"] for e in episodes]
    validations = [e["validation_status"] for e in episodes]
    assert actions[0] == "retry" and actions[1] == "retry"
    assert validations[0] == "NOT_RECOVERED" and validations[1] == "NOT_RECOVERED"
    assert actions[2] == "reconfigure"
    assert all(a == "reconfigure" for a in actions[2:]), f"expected the planner to stay switched: {actions}"
    assert all(v == "RECOVERED" for v in validations[2:]), f"expected recovery once switched: {validations}"


def test_memory_off_never_switches_and_never_recovers(tmp_path):
    episodes = run_condition("OFF", None)
    actions = [e["action"] for e in episodes]
    validations = [e["validation_status"] for e in episodes]
    assert all(a == "retry" for a in actions), f"memory OFF must never learn to avoid retry: {actions}"
    assert all(v == "NOT_RECOVERED" for v in validations), f"memory OFF must never recover: {validations}"


def test_restart_persistence_check_passes_all_invariants(tmp_path):
    (tmp_path / "raw").mkdir()
    result = restart_persistence_check(tmp_path)
    assert result["versions_match"] is True
    assert result["retrieved_correctly"] is True
    assert result["cross_scope_query_correctly_returned_nothing"] is True
