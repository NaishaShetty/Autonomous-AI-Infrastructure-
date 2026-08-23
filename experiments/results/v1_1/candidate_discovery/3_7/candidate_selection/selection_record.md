# Phase 3.7 Candidate Selection Record

## Decision

**Selected for future screening:** Candidate A — Structured uncertainty and evidence-request policy; Candidate C — Provenance-aware failure-memory context.

**Not selected for immediate screening:** Candidate B — Distribution-context monitor; Candidate D — Constrained model disagreement; Candidate E — Explicit structured decision policy.

**Phase outcome:** **V1.1 DIRECTION IDENTIFIED — NO CANDIDATE YET.**

## Selection basis

The selection was made before any Phase 3.7 future-fold result existed. It uses accumulated evidence, scientific plausibility, novelty relative to prior phases, implementation feasibility, measurable capability, safety, and ability to validate on the canonical temporal test plus all three authoritative Phase 3.5 folds.

| Criterion | Candidate A | Candidate C | Candidate B | Candidate D | Candidate E |
|---|---:|---:|---:|---:|---:|
| Addresses a capability V1 lacks | High | High | Medium | Medium | High |
| Supported by prior evidence | High | Medium-high | Medium | Low-medium | Medium |
| Novel versus rejected work | High | High | Medium | Medium | Medium |
| Safety and leakage testability | High | High | Medium | Medium | Medium |
| Multi-temporal feasibility | High | High | High | High | High |
| Priority | **1** | **2** | 3 | 4 | 5 |

## Reasons for non-selection

Candidate B is retained as a reserve because its predecessor demonstrated operational coverage problems; a new drift-context design is plausible, but it should follow a stricter specification of what drift changes and how escalation cost is bounded. Candidate D is reserve because there is not yet enough independent evidence that constrained disagreement adds information beyond V1. Candidate E is reserve because it is a broad wrapper whose value depends on validated uncertainty, context, or memory signals; screening it first would risk arbitrary policy design.

## Guardrails

Selection does not permit implementation into V1. It does not permit tuning on future folds, feature fishing, unrestricted algorithm search, candidate cherry-picking, or relabeling prior results as Phase 3.7 candidate results. Candidate A and Candidate C remain research copies until independently screened and reviewed in a later phase.
