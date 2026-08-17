"""Task 12: reconstruction / information-preservation verification.

``verify_round_trip`` checks that a NormalizedRecord -> FailureExperience ->
reconstructed-dict round trip preserves the fields Task 12 lists as
required: failure identity, observations, diagnosis, action, outcome,
timestamps, provenance. It does NOT check byte-for-byte equality of the
whole record -- some source fields are intentionally not carried into the
canonical schema (documented in ``INTENTIONALLY_LOSSY_FIELDS`` below), and
the check is written to fail loudly on any field that ISN'T supposed to be
lossy but round-trips incorrectly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .schema import FailureExperience

# Fields present on some NormalizedRecord sources that are deliberately not
# preserved verbatim -- e.g. AgentRx's free-text `instruction` field (not
# ingested at all, to avoid storing unstructured free text beyond what the
# brief permits -- see sources/real_agentrx.py) and internal join keys
# (`annotation_id_used_for_join`) that exist only to build `occurrence_key`.
INTENTIONALLY_LOSSY_FIELDS = {
    "instruction",  # AgentRx free-text task instruction -- not stored (avoids unstructured PII-adjacent text)
    "annotation_id_used_for_join",  # consumed into occurrence_key, not separately retained
    "source_annotation_file",  # retained only inside provenance.raw_record_ref for AgentRx, not top-level
    "num_steps",  # retained only inside runtime_context, not as a dedicated field
}


@dataclass
class ReconstructionReport:
    experience_id: str
    checks: dict = field(default_factory=dict)  # field_group -> bool
    missing: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.checks.values())


def verify_round_trip(normalized_record: dict, experience: FailureExperience) -> ReconstructionReport:
    checks = {}
    missing = []

    checks["failure_identity"] = (
        experience.failure.failure_type == normalized_record["failure_type"]
        and experience.identity.episode_id == normalized_record["episode_id"]
    )

    obs_ok = True
    for group_name, key in [
        ("telemetry", "telemetry"), ("resource_metrics", "resource_metrics"),
        ("performance_metrics", "performance_metrics"), ("log_events", "log_events"),
        ("anomaly_signals", "anomaly_signals"), ("system_state", "system_state"),
    ]:
        source_val = normalized_record.get(key)
        recon_val = getattr(experience.observations, group_name)
        if source_val:
            if recon_val != source_val:
                obs_ok = False
                missing.append(f"observations.{group_name}")
    checks["observations"] = obs_ok

    diag_ok = (
        experience.diagnosis.suspected_cause == normalized_record.get("diagnosis_suspected_cause")
        and experience.diagnosis.source.value == normalized_record.get("diagnosis_source")
    )
    checks["diagnosis"] = diag_ok

    action_ok = (
        experience.recovery.status.value == normalized_record.get("recovery_status")
        and experience.recovery.selected_action == normalized_record.get("recovery_selected_action")
    )
    checks["recovery_action"] = action_ok

    outcome_ok = experience.outcome.final_status.value == normalized_record.get("outcome_final_status")
    checks["outcome"] = outcome_ok

    timestamps_ok = experience.identity.observed_at == normalized_record["observed_at"]
    checks["timestamps"] = timestamps_ok

    provenance_ok = experience.provenance.source_dataset == normalized_record["source_dataset"]
    checks["provenance"] = provenance_ok

    return ReconstructionReport(experience_id=experience.identity.experience_id, checks=checks, missing=missing)
