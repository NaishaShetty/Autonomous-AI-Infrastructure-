"""Phase 4.5 gap 7 -- bounded continuous-mode loop over a workload stream.

Uses a genuinely infinite generator (itertools.cycle) to prove the bound is
what stops the loop, not the stream running out on its own.
"""
import itertools
import pathlib
import tempfile

import pytest

from src.phase4.controlled_runtime import ControlledRuntime, RuntimeConfig
from src.phase4.observability import PersistentEventStore
from src.phase4.pipeline import AutonomyPipeline


@pytest.fixture()
def pipeline():
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    store = PersistentEventStore(pathlib.Path(tmp.name) / "events.sqlite")
    config = RuntimeConfig(timeout_seconds=0.2, telemetry_interval_seconds=0.01)
    runtime = ControlledRuntime(store, config)
    yield AutonomyPipeline(runtime)
    store.close()
    tmp.cleanup()


def _infinite_stream():
    scenarios = [
        {"workload_type": "success", "parameters": {"mode": "success"}},
        {"workload_type": "fail", "parameters": {"mode": "fail"}},
        {"workload_type": "network", "parameters": {"mode": "network", "duration_seconds": 0.02}},
    ]
    return itertools.cycle(scenarios)


def test_continuous_mode_stops_cleanly_at_max_episodes_on_an_infinite_stream(pipeline):
    report = pipeline.run_continuous(_infinite_stream(), max_episodes=7)
    assert report.episodes_run == 7
    assert report.stopped_reason == "max_episodes"
    assert len(report.episode_log) == 7
    assert sum(report.final_state_counts.values()) == 7


def test_continuous_mode_stops_cleanly_at_max_duration_on_an_infinite_stream(pipeline):
    report = pipeline.run_continuous(_infinite_stream(), max_duration_seconds=0.5)
    assert report.stopped_reason in ("max_duration_seconds", "max_episodes")
    assert report.episodes_run >= 1
    assert report.wall_clock_seconds < 5.0  # actually stopped, did not run forever


def test_continuous_mode_writes_a_lightweight_json_lines_metrics_log(pipeline, tmp_path):
    log_path = tmp_path / "continuous_metrics.jsonl"
    report = pipeline.run_continuous(_infinite_stream(), max_episodes=5, metrics_log_path=log_path)
    assert log_path.is_file()
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == report.episodes_run + 1  # one row per episode + one summary row
    import json
    summary = json.loads(lines[-1])
    assert summary["summary"] is True
    assert summary["episodes_run"] == 5


def test_run_continuous_requires_at_least_one_bound(pipeline):
    with pytest.raises(ValueError):
        pipeline.run_continuous(_infinite_stream())


def test_continuous_mode_stops_at_stream_exhaustion_for_a_finite_stream(pipeline):
    finite = [{"workload_type": "success", "parameters": {"mode": "success"}} for _ in range(3)]
    report = pipeline.run_continuous(finite, max_episodes=100)
    assert report.episodes_run == 3
    assert report.stopped_reason == "stream_exhausted"
