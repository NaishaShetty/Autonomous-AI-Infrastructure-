"""Phase 4.9 -- independent controlled environments.

The instruction was explicit: "different run_id values are NOT independent
environments." This module defines three genuinely distinct
``ControlledRuntime`` configurations -- differing in real resource limits,
real runtime configuration (timing/telemetry resolution), and real
dependency-contention conditions, not merely a different label -- each
with its own ``environment_id`` and its own scenario-generation function
(so the actual DISTRIBUTION of workload parameters real subprocesses run
against differs by environment, not just the identity string attached to
otherwise-identical runs).

  - ``baseline_cpu``: the same configuration every prior phase (4.4-4.8)
    used -- ``timeout_seconds=0.15``, ``telemetry_interval_seconds=0.01``,
    the original ``scenario_for_seed`` resource/timing parameters. This is
    the DEVELOPMENT environment: the only one any model/threshold/policy
    is ever fit or calibrated against.

  - ``memory_constrained``: a real resource-limit change (the 'oom' mode's
    configured RLIMIT_AS-style budget is much tighter --
    ``limit_mb=8`` instead of 32, with ``alloc_mb`` scaled down to match
    so the family stays genuinely bimodal) PLUS a real runtime-
    configuration change (``telemetry_interval_seconds=0.002``, 5x finer
    sampling resolution -- a genuine telemetry-CAPABILITY difference, not
    just a relabeling). HELD-OUT evaluation environment: no model/
    threshold is ever fit on it.

  - ``dependency_network_constrained``: a real runtime-configuration
    change (``timeout_seconds=0.08``, roughly half the baseline deadline,
    genuinely shifting the cpu/timeout family's failure boundary) PLUS a
    real dependency-contention change (the 'resource_unavailable' family's
    port-occupation probability is raised from the baseline's implicit
    ~50% to 80%, modeling a real dependency that is usually, not
    occasionally, contended). ROBUSTNESS evaluation environment: also
    never fit on.

Every environment records the full required metadata (identity, resource
limits, runtime configuration, dependency configuration, telemetry
capabilities, failure mechanisms, environment version) via
``EnvironmentProfile.as_dict()`` rather than only a name.
"""
from __future__ import annotations

import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .controlled_runtime import ControlledRuntime, RuntimeConfig
from .monitoring import MonitoringBaseline
from .observability import PersistentEventStore
from .prediction import extract_features, rolling_checkpoints
from .prediction_training import CorpusRow, _dt

ENVIRONMENTS_VERSION = "phase4.9-independent-environments-v1"


def _scenario_baseline(seed: int) -> tuple[str, dict]:
    rng = random.Random(seed)
    family = rng.choice([
        "success", "timeout", "nonzero_exit", "network",
        "oom_fail", "oom_ok", "corruption", "gpu",
        "resource_fail", "resource_ok", "flaky_fail_then_ok", "flaky_ok",
    ])
    if family == "success":
        return "success", {"mode": "success"}
    if family == "timeout":
        # See prediction_training.py::scenario_for_seed's identical fix for
        # the full explanation: the old 0.05/0.08s "fast" choices left too
        # little margin against real subprocess-startup overhead
        # (measured ~65-75ms on this platform alone), causing systematic
        # false TIMEOUTs. Lowered to 0.01/0.02s; 0.30/0.45s unchanged.
        #
        # NOTE for DEPENDENCY_NETWORK_CONSTRAINED specifically
        # (timeout_seconds=0.08s): even 0.01-0.02s configured duration
        # plus ~65-75ms of real subprocess overhead can still occasionally
        # approach or exceed an 0.08s deadline on a loaded system -- that
        # environment's tighter deadline is a genuine, disclosed margin
        # limitation on this platform, not fully resolved by this fix. See
        # EnvironmentProfile.description for that environment.
        duration = rng.choice([0.01, 0.02, 0.30, 0.45])
        return "timeout_via_cpu", {"mode": "cpu", "duration_seconds": duration}
    if family == "nonzero_exit":
        return "fail", {"mode": "fail"}
    if family == "network":
        return "network", {"mode": "network", "duration_seconds": 0.05}
    if family == "oom_fail":
        return "oom", {"mode": "oom", "alloc_mb": rng.choice([120, 200, 300]), "limit_mb": 32}
    if family == "oom_ok":
        return "oom", {"mode": "oom", "alloc_mb": 8, "limit_mb": 256}
    if family == "corruption":
        return "corruption", {"mode": "corruption"}
    if family == "gpu":
        return "gpu", {"mode": "gpu"}
    if family == "resource_fail":
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 40000 + (seed % 2000), "_occupy": True}
    if family == "resource_ok":
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 40000 + (seed % 2000), "_occupy": False}
    if family == "flaky_fail_then_ok":
        return "flaky", {"mode": "flaky", "fail_count": rng.choice([1, 2])}
    return "flaky", {"mode": "flaky", "fail_count": 0}


def _scenario_memory_constrained(seed: int) -> tuple[str, dict]:
    """Same family structure as baseline; a real, tighter OOM resource
    budget (limit_mb=8 vs 32) with alloc_mb scaled down so both the
    failing and non-failing OOM variants remain reachable under the
    smaller budget."""
    rng = random.Random(seed)
    family = rng.choice([
        "success", "timeout", "nonzero_exit", "network",
        "oom_fail", "oom_ok", "corruption", "gpu",
        "resource_fail", "resource_ok", "flaky_fail_then_ok", "flaky_ok",
    ])
    if family == "oom_fail":
        return "oom", {"mode": "oom", "alloc_mb": rng.choice([16, 24, 32]), "limit_mb": 8}
    if family == "oom_ok":
        return "oom", {"mode": "oom", "alloc_mb": 2, "limit_mb": 64}
    return _scenario_baseline(seed)


def _scenario_dependency_constrained(seed: int) -> tuple[str, dict]:
    """Same family structure as baseline; the contended-port family is
    genuinely MORE often contended (0.8 occupy probability vs baseline's
    implicit ~0.5), modeling a real, usually-unavailable dependency
    rather than an occasionally-unavailable one."""
    rng = random.Random(seed)
    family = rng.choice([
        "success", "timeout", "nonzero_exit", "network",
        "oom_fail", "oom_ok", "corruption", "gpu",
        "resource_contended", "corruption2", "flaky_fail_then_ok", "flaky_ok",
    ])
    if family == "resource_contended":
        occupy = rng.random() < 0.8
        return "resource_unavailable", {"mode": "resource_unavailable", "port": 41000 + (seed % 2000), "_occupy": occupy}
    if family == "corruption2":
        return "corruption", {"mode": "corruption"}
    return _scenario_baseline(seed)


@dataclass(frozen=True)
class EnvironmentProfile:
    environment_id: str
    role: str  # "development" | "held_out" | "robustness"
    description: str
    resource_limits: dict
    runtime_config_kwargs: dict
    dependency_conditions: str
    telemetry_capabilities: str
    failure_mechanisms: str
    scenario_fn: Callable[[int], tuple[str, dict]] = field(repr=False)
    environment_version: str = ENVIRONMENTS_VERSION

    def as_dict(self) -> dict:
        return {
            "environment_id": self.environment_id, "role": self.role, "description": self.description,
            "resource_limits": self.resource_limits, "runtime_config_kwargs": self.runtime_config_kwargs,
            "dependency_conditions": self.dependency_conditions, "telemetry_capabilities": self.telemetry_capabilities,
            "failure_mechanisms": self.failure_mechanisms, "environment_version": self.environment_version,
        }


BASELINE_CPU = EnvironmentProfile(
    environment_id="phase4.9-env-baseline-cpu",
    role="development",
    description="Same configuration used by every prior phase (4.4-4.8): the reference environment every model/threshold/policy is fit and calibrated against.",
    resource_limits={"oom_limit_mb_fail_variant": 32, "oom_limit_mb_ok_variant": 256},
    runtime_config_kwargs={"timeout_seconds": 0.15, "telemetry_interval_seconds": 0.01},
    dependency_conditions="resource_unavailable family: ~50% of episodes have the contended port pre-occupied",
    telemetry_capabilities="10ms telemetry poll interval",
    failure_mechanisms="unchanged from controlled_runtime.py's original 12 scenario families",
    scenario_fn=_scenario_baseline,
)

MEMORY_CONSTRAINED = EnvironmentProfile(
    environment_id="phase4.9-env-memory-constrained",
    role="held_out",
    description="Real, tighter memory budget for the OOM family (limit_mb=8 vs 32) plus 5x finer telemetry sampling resolution -- never used to fit or calibrate anything.",
    resource_limits={"oom_limit_mb_fail_variant": 8, "oom_limit_mb_ok_variant": 64},
    runtime_config_kwargs={"timeout_seconds": 0.15, "telemetry_interval_seconds": 0.002},
    dependency_conditions="resource_unavailable family: ~50% pre-occupied (unchanged from baseline)",
    telemetry_capabilities="2ms telemetry poll interval (5x finer than baseline)",
    failure_mechanisms="oom mode's real memory budget is 4x tighter than baseline; all other families unchanged",
    scenario_fn=_scenario_memory_constrained,
)

DEPENDENCY_NETWORK_CONSTRAINED = EnvironmentProfile(
    environment_id="phase4.9-env-dependency-network-constrained",
    role="robustness",
    description="Real, tighter execution deadline (timeout_seconds=0.08 vs 0.15) plus a genuinely more-often-contended dependency (resource_unavailable family occupied 80% of the time vs baseline's ~50%) -- never used to fit or calibrate anything.",
    resource_limits={"oom_limit_mb_fail_variant": 32, "oom_limit_mb_ok_variant": 256},
    runtime_config_kwargs={"timeout_seconds": 0.08, "telemetry_interval_seconds": 0.01},
    dependency_conditions="resource_unavailable family: 80% pre-occupied (usually contended, not occasionally)",
    telemetry_capabilities="10ms telemetry poll interval (unchanged from baseline)",
    failure_mechanisms="cpu/timeout family's failure boundary is roughly halved; resource contention is the common case rather than the exception",
    scenario_fn=_scenario_dependency_constrained,
)

ALL_ENVIRONMENTS = (BASELINE_CPU, MEMORY_CONSTRAINED, DEPENDENCY_NETWORK_CONSTRAINED)


def generate_corpus_rows_for_environment(env: EnvironmentProfile, seeds, split: str) -> list[CorpusRow]:
    """Mirrors ``prediction_training.generate_corpus_rows``'s generation
    and temporal-cut discipline exactly, but sources both the scenario
    parameters and the ``RuntimeConfig`` from ``env`` instead of the
    single fixed baseline -- this is what makes the corpus genuinely
    reflect a different environment rather than just a different label."""
    baseline = MonitoringBaseline()
    rows: list[CorpusRow] = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = PersistentEventStore(Path(tmp) / "events.sqlite")
        config = RuntimeConfig(environment_id=env.environment_id, **env.runtime_config_kwargs)
        runtime = ControlledRuntime(store, config)
        for seed in seeds:
            workload_type, params = env.scenario_fn(seed)
            params = dict(params)
            occupy = params.pop("_occupy", None)
            if occupy:
                runtime.occupy_external_resource(int(params["port"]))
            workload_id = f"{env.environment_id}-{split}-seed-{seed}"
            mode = str(params.get("mode") or workload_type)
            result = runtime.run(workload_type, params, workload_id=workload_id)
            failure_events = [e for e in result.events if e.get("event_type") == "failure_detected"]
            label = 1 if failure_events else 0
            failure_class = str(failure_events[0]["payload"].get("failure_kind")) if failure_events else None
            failure_ts = _dt(str(failure_events[0]["timestamp"])) if failure_events else None
            for idx, (checkpoint_time, prefix) in enumerate(rolling_checkpoints(result.events, result.collection_start)):
                if failure_ts is not None and _dt(checkpoint_time) >= failure_ts:
                    continue
                features = extract_features(prefix, baseline, config.timeout_seconds, result.collection_start, checkpoint_time)
                ttf = (failure_ts - _dt(checkpoint_time)).total_seconds() if failure_ts is not None else None
                rows.append(CorpusRow(
                    seed=seed, split=split, run_id=result.run_id, workload_id=workload_id,
                    failure_class=failure_class, label=label, checkpoint_index=idx,
                    checkpoint_time=checkpoint_time, time_to_failure_seconds=ttf,
                    features=features.as_vector(), mode=mode,
                ))
        store.close()
    return rows
