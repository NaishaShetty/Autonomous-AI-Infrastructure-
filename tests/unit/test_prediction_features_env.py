"""Post-P5 remediation, Step 4 -- unit coverage for the environment-aware
RSS normalization feature (P4-W2)."""
from src.phase4.monitoring import MonitoringBaseline
from src.phase4.prediction_features_env import _configured_limit_mb, extract_features_env_aware


def _workload_received(mode, extra_params=None):
    params = {"mode": mode}
    params.update(extra_params or {})
    return {"event_type": "workload_received", "payload": {"workload_parameters": params}}


def _telemetry(rss_bytes):
    return {"event_type": "telemetry_observed", "payload": {"process_rss_bytes": rss_bytes}}


def test_configured_limit_mb_reads_oom_budget_from_workload_received():
    prefix = [_workload_received("oom", {"limit_mb": 8, "alloc_mb": 6})]
    assert _configured_limit_mb(prefix) == 8.0


def test_configured_limit_mb_is_none_for_non_oom_modes():
    prefix = [_workload_received("cpu", {"duration_seconds": 0.3})]
    assert _configured_limit_mb(prefix) is None


def test_configured_limit_mb_is_none_when_absent():
    assert _configured_limit_mb([]) is None


def test_env_normalized_rss_uses_the_runs_own_budget_not_the_fixed_baseline():
    baseline = MonitoringBaseline()  # fixed 512MB envelope, unrelated to any oom limit_mb
    rss_bytes = 4 * 1024 * 1024  # 4MB peak RSS
    prefix_tight_budget = [_workload_received("oom", {"limit_mb": 8}), _telemetry(rss_bytes)]
    features = extract_features_env_aware(prefix_tight_budget, baseline, 0.15, "2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z")
    # 4MB against an 8MB budget -> 0.5, NOT 4MB/512MB ~= 0.0078 (the fixed-baseline value).
    assert abs(features.rss_ratio_env_normalized - 0.5) < 1e-6
    assert features.base.rss_ratio < 0.01  # the original, environment-blind feature stays tiny for the same reading


def test_env_normalized_rss_falls_back_honestly_when_no_budget_is_known():
    baseline = MonitoringBaseline()
    rss_bytes = 4 * 1024 * 1024
    prefix_no_oom = [_workload_received("cpu", {"duration_seconds": 0.3}), _telemetry(rss_bytes)]
    features = extract_features_env_aware(prefix_no_oom, baseline, 0.15, "2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z")
    # No limit_mb known for this mode -- must fall back to the base rss_ratio, never fabricate a budget.
    assert features.rss_ratio_env_normalized == features.base.rss_ratio
