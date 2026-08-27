"""Post-P5 remediation (P3-W7) -- explicit GPU probe state classification.

Prior to this module, ``controlled_runtime.py``'s ``gpu`` mode collapsed every
probe outcome into a single boolean (``available``): tool-not-found,
tool-found-but-no-device, a probe timeout, and a probe subprocess error were
all silently folded into "unavailable." The project's own P3 GPU AUROC result
was later found unreplicated -- consistent with an unreplicated hardware/
timing race hiding inside that boolean collapse. This module makes every
distinct outcome an explicit, named state instead, and records the provenance
needed to tell them apart after the fact (host identity, probe tool/version,
timeout used, timestamp).

States:
  GPU_AVAILABLE      -- probe tool ran, exited 0, and reported at least one device.
  GPU_UNAVAILABLE    -- probe tool ran cleanly but reported no device (or a
                        non-zero exit), i.e. the probe itself worked and the
                        honest answer is "no GPU."
  GPU_PROBE_TIMEOUT  -- the probe subprocess itself did not return within the
                        configured timeout. This is a probe-infrastructure
                        fact, not evidence about the device.
  GPU_PROBE_ERROR    -- the probe could not be run at all (e.g. the tool
                        exists but raised an unexpected OS-level error).
  UNKNOWN            -- no GPU management tool (``nvidia-smi``/``rocm-smi``)
                        was found on PATH, so no probe could even be
                        attempted. This is deliberately NOT classified as
                        GPU_UNAVAILABLE: absence of a probe tool is not
                        evidence of absence of a device.

``probe_gpu(force_state=...)`` exists only for deterministic *pipeline
plumbing* tests (escalation/circuit-breaker/fallback-routing logic) that need
a GPU_UNAVAILABLE outcome regardless of what hardware the test happens to run
on. It is never used by production code or by any P3/P4 research evaluation
path -- forced records are labeled ``forced: True`` with an explicit
``provenance.source == "test_override"`` so they can never be mistaken for
real hardware evidence downstream.
"""
from __future__ import annotations

import platform
import shutil
import subprocess as sp
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

GPU_AVAILABLE = "GPU_AVAILABLE"
GPU_UNAVAILABLE = "GPU_UNAVAILABLE"
GPU_PROBE_TIMEOUT = "GPU_PROBE_TIMEOUT"
GPU_PROBE_ERROR = "GPU_PROBE_ERROR"
UNKNOWN = "UNKNOWN"

VALID_STATES = (GPU_AVAILABLE, GPU_UNAVAILABLE, GPU_PROBE_TIMEOUT, GPU_PROBE_ERROR, UNKNOWN)

GPU_PROBE_VERSION = "phase4.post-p5-gpu-probe-v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class GPUProbeResult:
    state: str
    tool: str | None
    hardware_identity: str | None
    probe_version: str
    timestamp: str
    timeout_seconds: float
    host_identity: str
    forced: bool
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state, "tool": self.tool, "hardware_identity": self.hardware_identity,
            "probe_version": self.probe_version, "timestamp": self.timestamp,
            "timeout_seconds": self.timeout_seconds, "host_identity": self.host_identity,
            "forced": self.forced, "provenance": dict(self.provenance),
        }


def probe_gpu(timeout_seconds: float = 2.0, force_state: str | None = None) -> GPUProbeResult:
    if force_state is not None:
        if force_state not in VALID_STATES:
            raise ValueError(f"force_state must be one of {VALID_STATES}, got {force_state!r}")
        return GPUProbeResult(
            state=force_state, tool=None, hardware_identity=None, probe_version=GPU_PROBE_VERSION,
            timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
            forced=True, provenance={"source": "test_override", "note": "deterministic override for test determinism; not a claim about real hardware"},
        )

    tool = shutil.which("nvidia-smi") or shutil.which("rocm-smi")
    if not tool:
        return GPUProbeResult(
            state=UNKNOWN, tool=None, hardware_identity=None, probe_version=GPU_PROBE_VERSION,
            timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
            forced=False, provenance={"source": "real_probe", "reason": "no GPU management tool found on PATH"},
        )

    try:
        result = sp.run([tool, "-L"], capture_output=True, timeout=timeout_seconds, text=True)
    except sp.TimeoutExpired:
        return GPUProbeResult(
            state=GPU_PROBE_TIMEOUT, tool=tool, hardware_identity=None, probe_version=GPU_PROBE_VERSION,
            timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
            forced=False, provenance={"source": "real_probe", "reason": f"{tool} did not return within {timeout_seconds}s"},
        )
    except Exception as exc:
        return GPUProbeResult(
            state=GPU_PROBE_ERROR, tool=tool, hardware_identity=None, probe_version=GPU_PROBE_VERSION,
            timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
            forced=False, provenance={"source": "real_probe", "reason": f"{type(exc).__name__}: {exc}"},
        )

    output = (result.stdout or "").strip()
    if result.returncode == 0 and output:
        return GPUProbeResult(
            state=GPU_AVAILABLE, tool=tool, hardware_identity=output, probe_version=GPU_PROBE_VERSION,
            timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
            forced=False, provenance={"source": "real_probe", "returncode": result.returncode},
        )
    return GPUProbeResult(
        state=GPU_UNAVAILABLE, tool=tool, hardware_identity=None, probe_version=GPU_PROBE_VERSION,
        timestamp=_now_iso(), timeout_seconds=timeout_seconds, host_identity=platform.node(),
        forced=False, provenance={"source": "real_probe", "returncode": result.returncode},
    )
