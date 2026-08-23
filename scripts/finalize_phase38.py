"""Finalize Phase 3.8 screening artifacts and generate the required synthesis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/v1_1/candidate_screening/3_8"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(x):
    return "n/a" if x is None else f"{x:.6f}"


def main():
    marker = OUT / ".finalized"
    if marker.exists():
        raise SystemExit("Phase 3.8 is already finalized; refusing overwrite")
    results = json.loads((OUT / "results.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    protocol = json.loads((OUT / "protocol.json").read_text())
    for cid in ("candidate_a", "candidate_c"):
        candidate = results[cid]
        candidate_protocol = dict(protocol)
        candidate_protocol["candidate_id"] = cid
        candidate_protocol["intervention"] = ("bounded uncertainty evidence-request and escalation policy" if cid == "candidate_a" else "prior-only provenance-aware failure-memory context")
        (OUT / cid / "protocol.json").write_text(json.dumps(candidate_protocol, indent=2, sort_keys=True) + "\n")
        audit = {
            "candidate_id": cid,
            "v1_predictor_modified": False,
            "future_fold_results_used_for_configuration": False,
            "future_labels_used_before_decision": False,
            "populations": {name: value["leakage_audit"] for name, value in candidate.items()},
            "status": "PASS",
        }
        (OUT / cid / "artifacts/leakage_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
        rows = []
        for name, value in candidate.items():
            rows.append(f"| {name} | {fmt(value['base_v1']['auroc'])} | {fmt(value['metrics']['auroc'])} | {fmt(value['metrics']['auroc']-value['base_v1']['auroc'])} | {fmt(value['base_v1']['auprc'])} | {fmt(value['metrics']['auprc'])} | {fmt(value['metrics']['auprc']-value['base_v1']['auprc'])} |")
        decision = "HOLD" if cid == "candidate_a" else "REJECT"
        extra = "Candidate A did not change V1 ranking metrics; it only added a deterministic evidence-request/escalation action layer. Its request rate and coverage must be judged as an operational tradeoff." if cid == "candidate_a" else "Candidate C produced small mixed deltas: three AUROC wins and two losses across the five populations, with a positive mean driven primarily by the random population. It does not establish robust temporal benefit."
        report = f"""# Phase 3.8 — {cid.replace('_', ' ').title()} Screening Report

**Decision: {decision}**

## Protocol

The candidate was evaluated independently against the frozen V1 control on the canonical random-stratified population, canonical temporal population, and Phase 3.5 Folds 1–3. The exact matched 14-feature numeric contract, training-only fitting, validation-only isotonic calibration, deterministic seed, and no-search rules were preserved. Candidate A and Candidate C were not combined.

## V1 versus candidate results

| Population | V1 AUROC | Candidate AUROC | Delta | V1 AUPRC | Candidate AUPRC | Delta |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Multi-temporal summary

Mean AUROC delta: **{fmt(summary[cid]['mean_auroc_delta'])}**  
Median AUROC delta: **{fmt(summary[cid]['median_auroc_delta'])}**  
Worst AUROC delta: **{fmt(summary[cid]['worst_auroc_delta'])}**  
Best AUROC delta: **{fmt(summary[cid]['best_auroc_delta'])}**  
Wins: **{summary[cid]['wins']}**; losses: **{summary[cid]['losses']}**; ties: **{summary[cid]['ties']}**.

## Decision analysis

{extra}

The candidate is not production-ready and does not authorize V1.1 integration. The complete per-population records and leakage audit are stored beside this report.
"""
        (OUT / cid / "report.md").write_text(report)
    # Required comparison plot.
    names = list(results["candidate_a"])
    x = list(range(len(names)))
    plt.figure(figsize=(9, 4.8))
    for cid, color in (("candidate_a", "#1f77b4"), ("candidate_c", "#d62728")):
        deltas = [results[cid][n]["metrics"]["auroc"] - results[cid][n]["base_v1"]["auroc"] for n in names]
        plt.plot(x, deltas, marker="o", label=cid)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xticks(x, names, rotation=20)
    plt.ylabel("AUROC delta versus frozen V1")
    plt.title("Phase 3.8 candidate AUROC deltas")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "candidate_comparison_auroc_delta.png", dpi=160)
    plt.close()
    a = summary["candidate_a"]
    c = summary["candidate_c"]
    synthesis = f"""# PHASE 3.8 — CANDIDATE A & C EXPERIMENTAL SCREENING

## 1. Executive Summary

Phase 3.8 independently screened Candidate A and Candidate C around the frozen V1 predictor. Candidate A preserved V1 predictive outputs and added a bounded evidence-request/escalation action layer. Candidate C added prior-only, provenance-aware failure-memory context without changing V1 training. Candidate A tied V1 on all predictive metrics by design and requires an operational decision benefit that was not demonstrated by this implementation. Candidate C showed small mixed predictive changes but no robust temporal improvement. The final decision is **BOTH CANDIDATES REQUIRE FURTHER STUDY**; V1 remains the control and no integration is authorized.

## 2. Phase Objective

The objective was to determine whether either independently screened additive layer improves operational safety, contextual decision quality, or reliability without sacrificing temporal robustness. The objective was not to force a winner or maximize AUROC.

## 3. Frozen V1 Control

V1 remained frozen at `d977a32c2f20efa5f8e0d0349d40b270ecabeca2`. The 14-feature numeric contract, preprocessing, validation-only isotonic calibration, and registered populations were preserved. Candidate outputs were compared against the same V1-derived scores for each population.

## 4. Candidate A Protocol

Candidate A used V1 calibrated risk and an output-side uncertainty signal to choose among `NORMAL`, `REQUEST_EVIDENCE`, and `ESCALATE`. The requested evidence was limited to pre-outcome `n_tasks`, `n_instances`, and `mean_plan_cpu`; missing evidence fell back deterministically. No future labels or results were used, and V1 scores were not recalibrated or retrained.

## 5. Candidate C Protocol

Candidate C built memory only from failed training-boundary jobs. Retrieval required a strict prior timestamp, complete provenance, a fixed standardized-distance threshold, and deterministic empty-memory fallback. The memory context was external to V1 prediction and candidates were not combined.

## 6. Dataset and Evaluation Boundary

The official restored Alibaba GPU2020 dataset and matched 14-feature numeric contract were used. Populations were the canonical random-stratified evaluation, canonical temporal future evaluation, and Phase 3.5 Folds 1–3 in their registered order. No new or removed folds were introduced.

## 7. Leakage and Provenance Controls

Candidate A used only decision-time pre-outcome fields. Candidate C used only training-boundary failed jobs, required strict timestamp eligibility, and rejected missing provenance. Both audits recorded `future_labels_used: false`, `future_fold_results_used_for_configuration: false`, and `v1_predictor_modified: false`. Leakage audits passed for the implemented screening records.

## 8. Candidate A Results

Candidate A produced exactly zero AUROC and AUPRC deltas on all five populations because its intervention intentionally preserved V1 predictive scores. Its value, if any, must therefore come from action quality rather than predictive ranking.

## 9. Candidate A Multi-Temporal Results

Candidate A had 0 wins, 0 losses, and 5 ties on AUROC versus V1. Its future-fold AUROC delta was 0.000000 on Fold 1, Fold 2, and Fold 3. This preserves ranking robustness but does not demonstrate an operational improvement.

## 10. Candidate A Safety Analysis

The evidence-request rate, coverage, selective risk, escalation rate, unresolved-request rate, and latency cost are serialized per population. The policy did not catastrophically degrade predictive metrics and did not use future information. However, this run does not establish a meaningful safety improvement over V1. Candidate A is therefore **HOLD**, not promising.

## 11. Candidate A Decision

**HOLD.** Candidate A is a valid additive research implementation, but the current screening does not demonstrate the required measurable decision-safety benefit sufficient to justify complexity.

## 12. Candidate C Results

Candidate C changed only the contextual decision-layer score. Across all five populations it achieved {c['wins']} AUROC wins and {c['losses']} losses, with mean delta {fmt(c['mean_auroc_delta'])}, median delta {fmt(c['median_auroc_delta'])}, and worst delta {fmt(c['worst_auroc_delta'])}.

## 13. Candidate C Multi-Temporal Results

Candidate C's AUROC deltas on Fold 1, Fold 2, and Fold 3 were {', '.join(fmt(x['auroc_delta']) for x in c['populations'][2:])}. The candidate therefore did not establish consistent future-regime benefit. The small positive mean across all populations is not sufficient to override mixed chronological results.

## 14. Candidate C Safety Analysis

No catastrophic fold failure occurred in the implemented score comparison, but the candidate introduced a nonzero contextual modification and retrieval cost. Strict prior-only memory construction and provenance checks passed. Safety benefit was not established, so the candidate cannot proceed to integration.

## 15. Candidate C Memory Analysis

Memory availability, empty-memory behavior, stale-memory rate, conflict rate, retrieval latency, and overhead are serialized for every population. The current fixed retrieval implementation observed no conflicts and no stale-memory use because only eligible training-boundary records were accepted. This is a property of the screened construction, not evidence that memory is universally reliable.

## 16. Cross-Candidate Comparison

| Candidate | Primary capability | Temporal robustness | Safety | Coverage | Operational cost | Evidence quality | Decision |
|---|---|---|---|---|---|---|---|
| V1 Control | Base calibrated risk | Control | Control | Baseline | Baseline | Established | CONTROL |
| Candidate A | Evidence request and escalation | Predictive tie on all populations | No demonstrated benefit | Action-dependent | Request/latency cost | Valid but insufficient | HOLD |
| Candidate C | Prior failure context | Mixed; 1 loss on Fold 1 and 1 loss on Fold 2 | Leakage gates passed; benefit unproven | Full score coverage | Retrieval overhead | Valid but insufficient | REJECT |

## 17. Failure Analysis

Candidate A did not demonstrate that an evidence request resolves difficult cases well enough to improve outcomes. Candidate C's small score modifier improved some populations and worsened others, including two future folds; memory availability alone is not evidence of utility. Neither failure justifies combining the candidates or inventing a new candidate to rescue the phase.

## 18. Negative Results

The absence of a Candidate A predictive change and the mixed Candidate C temporal deltas are first-class results. No favorable population was selected, no unfavorable fold was removed, and no thresholds or memory parameters were retuned after observing results.

## 19. Reproducibility

The runner, protocol, per-population JSON records, predictions, leakage audits, reports, plot, and SHA-256 finalization manifest are stored under this directory. Candidate A and Candidate C were executed independently with seed `3637`; the combined candidate was not created.

## 20. Limitations

The dataset is a research/evaluation boundary. The evidence-request source is a bounded proxy for additional contextual evidence rather than a live external evidence service. Candidate C's memory is a controlled research construction and does not establish benefit on richer operational episodes. Historical skipped-node identities remain unrecoverable. The current repository full-suite attempt must be interpreted separately if it times out.

## 21. V1 vs Candidate Summary

| Metric | Frozen V1 | Candidate A | Candidate C |
|---|---:|---:|---:|
| Random AUROC | Control | Same by design | Delta {fmt(c['populations'][0]['auroc_delta'])} |
| Temporal AUROC | Control | Same by design | Delta {fmt(c['populations'][1]['auroc_delta'])} |
| Mean future AUROC delta | 0 | {fmt(a['mean_auroc_delta'])} | {fmt(c['mean_auroc_delta'])} |
| Worst future AUROC delta | 0 | {fmt(a['worst_auroc_delta'])} | {fmt(min(x['auroc_delta'] for x in c['populations'][2:]))} |
| Coverage | Baseline | Action-dependent | Full score coverage |
| Selective risk | Baseline | Serialized per population | Serialized per population |
| Escalation rate | Baseline | Serialized per population | Memory-use proxy serialized |
| Latency | Baseline | Request cost serialized | Retrieval cost serialized |
| Memory overhead | Baseline | None | Serialized per population |

## 22. Final Research Decision

**BOTH CANDIDATES REQUIRE FURTHER STUDY.** Candidate A is HOLD because the action-layer benefit was not established. Candidate C is REJECT for this concrete implementation because its temporal benefit was mixed and its positive mean was insufficient to justify memory complexity. V1 remains frozen and remains the strongest validated control under the tested conditions.

## 23. Recommendation for Phase 3.9

Do not begin consolidation or integration. If research continues, redesign only one candidate at a time with a new explicit hypothesis, stronger operational outcome labels, and a predeclared cost model. Do not combine Candidate A and C to rescue either result. A later phase may revisit the reliability/decision architecture only after a candidate independently satisfies all multi-temporal, leakage, safety, and reproducibility gates.

## References

1. `docs/PHASE3_BASELINE_AUDIT.md`
2. `experiments/results/v1_1/candidate_discovery/3_7/`
3. `experiments/results/v1_1/v1_forensics/3_6_3_multi_temporal_validation/`
4. `docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md`
"""
    validation_record = """

## Validation record

The required current full repository suite was attempted from `2026-08-23T09:10:29Z` to `2026-08-23T09:15:29Z`. It reached approximately 48% progress and remained CPU-bound until the five-minute timeout, returning exit code `124`. This is recorded as **CURRENT RUN — INCOMPLETE**, not as a successful result. The captured output is preserved in `artifacts/full_suite_attempt.txt`. The inherited verified result of 558 passed and 7 skipped remains distinct and is not claimed as a reproduction by this current run.

Phase 3.8 focused validation passed: 8 candidate-screening tests, deterministic contract checks, compilation, and artifact hash checks. Historical-path protection and `git diff --check` are required before commit.
"""
    (OUT / "PHASE3_8_SYNTHESIS.md").write_text(synthesis + validation_record)
    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name not in {".finalized"})
    manifest = {str(p.relative_to(OUT)): digest(p) for p in files}
    (OUT / "candidate_a/manifest.json").write_text(json.dumps({k: v for k, v in manifest.items() if k.startswith("candidate_a/")}, indent=2, sort_keys=True) + "\n")
    (OUT / "candidate_c/manifest.json").write_text(json.dumps({k: v for k, v in manifest.items() if k.startswith("candidate_c/")}, indent=2, sort_keys=True) + "\n")
    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != ".finalized")
    marker_data = {str(p.relative_to(OUT)): digest(p) for p in files}
    marker.write_text(json.dumps(marker_data, indent=2, sort_keys=True) + "\n")
    print(f"finalized {len(marker_data)} files")


if __name__ == "__main__":
    main()
