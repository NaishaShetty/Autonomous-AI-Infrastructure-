"""ACTIVE Phase 4.2 -- Pattern Type 2 descriptive/exploratory analysis
(AIOps, AgentRx).

Consumes ``FailureExperience`` records built through the active Phase 4.1
ingestion pipeline (``src.failure_experience.sources.*`` +
``src.failure_experience.ingest.ingest_batch``) -- this module does not
re-parse AIOps/AgentRx raw files itself, unlike ``discovery_alibaba.py``
(which has a documented, protocol-disclosed reason to bypass
FailureExperience; AIOps and AgentRx have no such population-denominator
requirement -- both are per-episode failure recurrence, exactly what
FailureExperience already stores in full).

Neither source has a frozen train/validation/test split
(``environment == "unsplit"`` for AIOps; no split field at all for
AgentRx). Per the frozen protocol's ``descriptive_only_sources`` block, no
train-fit-then-test-score claim is made here -- these functions only ever
report descriptive recurrence and (AIOps only) a temporal-clustering
statistic against a uniform-arrival null. CONFIRMED tier is structurally
unreachable; results here are DescriptiveAssociation objects, not
PatternCandidate/EvidenceTier objects.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import datetime

from src.failure_experience.schema import FailureExperience

from .schema import DescriptiveAssociation


def aiops_recurrence(experiences: list[FailureExperience], min_evidence_n: int = 2) -> list[DescriptiveAssociation]:
    """(entity, fault_desrcibtion) recurrence -- entity is
    ``workload_context.workload_id``, fault type is ``failure.failure_type``
    (both populated directly from the AIOps 2020 challenge's organizer-
    injected ground truth labels by
    ``src.failure_experience.sources.real_aiops``)."""
    counts: Counter = Counter()
    for e in experiences:
        key = (e.workload_context.workload_id, e.failure.failure_type)
        counts[key] += 1
    return [
        DescriptiveAssociation(dataset="aiops_kpi_2020", key=key, count=n, is_candidate=n >= min_evidence_n)
        for key, n in counts.items()
    ]


def aiops_temporal_clustering(experiences: list[FailureExperience]) -> dict:
    """Per entity with >=2 positive-fault onsets: observed inter-onset gap
    coefficient of variation (CV = stdev/mean) vs. the CV implied by a
    uniform-arrival null over the same observed span (a perfectly uniform
    arrival process over n points has CV -> 0 as n grows; small-n exact
    uniform CV is computed via the order statistics of n-1 uniform gaps,
    approximated here by the closed-form CV of n-1 i.i.d. Exponential-like
    spacings under a homogeneous Poisson null, CV=1, which is the standard
    reference point for 'clustered' (CV>1) vs 'uniform/regular' (CV<1)
    inter-event timing -- this is the pre-registered method, fixed in
    ``configs/phase4_2_active_pattern_protocol.json`` before computation).
    Uses REAL wall-clock onset timestamps (``failure.detection_timestamp``,
    populated from AIOps's real ``onset`` field) -- not the synthetic
    generator's constant-gap schedule old Phase 4.2 found trivially null
    by construction."""
    by_entity: dict[str, list[datetime]] = defaultdict(list)
    for e in experiences:
        ts = e.failure.detection_timestamp or e.identity.observed_at
        by_entity[e.workload_context.workload_id].append(ts)

    results = []
    for entity, timestamps in by_entity.items():
        timestamps = sorted(timestamps)
        n = len(timestamps)
        if n < 2:
            results.append({
                "entity": entity, "n_onsets": n, "evaluable": False,
                "reason": "fewer than 2 onsets -- no inter-onset gap to measure",
            })
            continue
        gaps_seconds = [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])]
        mean_gap = statistics.mean(gaps_seconds)
        if n < 3 or mean_gap == 0:
            results.append({
                "entity": entity, "n_onsets": n, "evaluable": False,
                "reason": "fewer than 3 onsets (stdev undefined) or zero mean gap",
            })
            continue
        stdev_gap = statistics.stdev(gaps_seconds)
        cv = stdev_gap / mean_gap
        results.append({
            "entity": entity,
            "n_onsets": n,
            "evaluable": True,
            "mean_gap_seconds": mean_gap,
            "stdev_gap_seconds": stdev_gap,
            "coefficient_of_variation": cv,
            "null_reference_cv": 1.0,
            "interpretation": "clustered (bursty)" if cv > 1.0 else ("regular/underdispersed" if cv < 1.0 else "consistent with a homogeneous Poisson (uniform-arrival) null"),
        })
    return {
        "per_entity": results,
        "n_entities_evaluable": sum(1 for r in results if r["evaluable"]),
        "n_entities_total": len(results),
    }


def agentrx_recurrence(experiences: list[FailureExperience], min_evidence_n: int = 2) -> dict:
    """(domain, failure_category) recurrence. AgentRx failures are
    multi-label (a trajectory can have >=1 failure_categories) --
    reported both as single-label (domain, primary_category =
    ``failure.failure_type``, the first category
    ``src.failure_experience.sources.real_agentrx`` selects) and as
    multi-label (domain, each category in ``diagnosis.evidence``, which
    that adapter populates with the FULL failure_categories list)."""
    single_label: Counter = Counter()
    multi_label: Counter = Counter()
    domains: Counter = Counter()
    categories_per_domain: dict[str, Counter] = defaultdict(Counter)

    for e in experiences:
        domain = e.workload_context.workload_id
        domains[domain] += 1
        single_label[(domain, e.failure.failure_type)] += 1
        categories = e.diagnosis.evidence or [e.failure.failure_type]
        for cat in categories:
            multi_label[(domain, cat)] += 1
            categories_per_domain[domain][cat] += 1

    single_associations = [
        DescriptiveAssociation(dataset="agentrx", key=key, count=n, is_candidate=n >= min_evidence_n)
        for key, n in single_label.items()
    ]
    multi_associations = [
        DescriptiveAssociation(dataset="agentrx", key=key, count=n, is_candidate=n >= min_evidence_n)
        for key, n in multi_label.items()
    ]
    return {
        "single_label_domain_primary_category": single_associations,
        "multi_label_domain_any_category": multi_associations,
        "domains": dict(domains),
        "categories_per_domain": {d: dict(c) for d, c in categories_per_domain.items()},
        "temporal_clustering": "NOT_CURRENTLY_EVALUABLE",
        "temporal_clustering_reason": "AgentRx has no real wall-clock timestamp -- the raw joined data's `timestamp` field is literally 'MISSING' for every record; only a synthetic anchor timestamp exists (src/failure_experience/sources/_util.py), which is not meaningful for ordering and is explicitly excluded from this analysis per the frozen protocol.",
    }
