"""Deterministic mapping from raw diagnosis_hypothesis / workload_type
strings (as actually observed in the frozen Phase 4.4/4.5 evidence) to the
canonical FailureClass enum defined in PHASE5_1_SCHEMA.json.

This mapping is itself a DERIVED_LABEL transformation (leakage policy rule
6): it is computed once, deterministically, from the raw
diagnosis_hypothesis/workload_type strings already present at generation
time -- never back-filled from a later diagnosis or memory record.
"""
from __future__ import annotations

# diagnosis_hypothesis (as emitted by src/phase4/diagnosis.py) -> FailureClass
DIAGNOSIS_TO_FAILURE_CLASS = {
    "NETWORK_CONNECTIVITY_FAILURE": "NETWORK_FAILURE",
    "PROCESS_EXIT_FAILURE": "GENERIC_FAIL",
    "RUNTIME_TIMEOUT": "PROCESS_TIMEOUT_CPU",
    "OUT_OF_MEMORY": "PROCESS_OOM",
    "RESOURCE_CONTENTION": "RESOURCE_UNAVAILABLE",
    "GPU_UNAVAILABLE": "GPU_DEVICE_UNAVAILABLE",
    "DATA_CORRUPTION": "DATA_INTEGRITY_FAILURE",
    "INTERMITTENT_FAILURE": "INTERMITTENT_TRANSIENT_FAILURE",
    None: "NONE",
}

# workload_type / workload_id-derived scenario mode -> FailureClass, used
# only as a fallback when diagnosis_hypothesis is None but the workload was
# not a pure success workload (i.e. the episode's own scenario intent is
# still the best available evidence of the intended failure family).
WORKLOAD_TYPE_TO_FAILURE_CLASS = {
    "success": "NONE",
    "network": "NETWORK_FAILURE",
    "fail": "GENERIC_FAIL",
    "oom": "PROCESS_OOM",
    "timeout": "PROCESS_TIMEOUT_CPU",
    "resource_unavailable": "RESOURCE_UNAVAILABLE",
    "gpu": "GPU_DEVICE_UNAVAILABLE",
    "corruption": "DATA_INTEGRITY_FAILURE",
    "flaky": "INTERMITTENT_TRANSIENT_FAILURE",
}


def infer_failure_class(diagnosis_hypothesis, workload_type_or_id: str) -> tuple[str, bool]:
    """Returns (failure_class, was_unmapped_fallback_to_generic).

    Tries diagnosis_hypothesis first (it is the more specific, real-time
    signal); falls back to a substring match against workload_type/
    workload_id; falls back to GENERIC_FAIL (flagged) if genuinely unknown.
    """
    if diagnosis_hypothesis in DIAGNOSIS_TO_FAILURE_CLASS:
        return DIAGNOSIS_TO_FAILURE_CLASS[diagnosis_hypothesis], False

    wl = (workload_type_or_id or "").lower()
    for key, fc in WORKLOAD_TYPE_TO_FAILURE_CLASS.items():
        if key in wl:
            return fc, False

    return "GENERIC_FAIL", True
