# Phase 4 / Phase 5 Reality Check and Execution Plan

**Date:** 2026-08-23
**Scope:** Honest audit of the current repository state, followed by a concrete plan to carry Phase 4 (operational intelligence) and Phase 5 (closed-loop self-healing) to completion.
**Method:** Read every Phase 4-era doc, `git log` across all 50 commits, and the actual source in `src/phase4/`, `src/runtime/`, `src/recovery/`, `src/decision/`, `src/failure_memory/`, `src/failure_experience/`. No claim below is asserted without a file or commit as evidence.

---

## 1. Executive summary — the thing nobody has said out loud yet

The framing "Phase 4 and 5 are about turning the foundations into a genuinely autonomous closed loop rather than stopping at monitoring and diagnosis" undersells the situation in one direction and oversells it in another.

It **undersells** it because a complete, tested, independently-validated closed loop — detection, reliability assessment, memory retrieval, diagnosis, recovery planning, a safety gate, simulated execution, independent validation, and a learning update back into memory — **already exists in this repository** and was evaluated on 56 real-data replay cases with zero unsafe executions (`docs/V1_FINAL_EVALUATION.md`, `docs/V1_RELEASE_AUDIT.md`). That is essentially a working prototype of everything Phase 5 asks for.

It **oversells** it because that closed loop is built on the Alibaba-trace/dataset-replay foundation the project's own history says can't legitimately serve as a synchronized decision-time source. When that foundation was abandoned in favor of the controlled subprocess runtime (today's `src/phase4/`), **the closed loop was not carried over.** The new pipeline was rebuilt from `AutonomyState.RECEIVED` up to `DIAGNOSING` and then stopped. Prediction, decision/abstention, planning, the safety gate, execution, validation, and the learning loop are all defined as `Protocol` interfaces in `src/phase4/architecture.py` — and none of them has a concrete implementation on the new foundation.

So the real starting position for Phase 4/5 is not "build these things." It is: **decide whether to port the already-built, already-validated V1 recovery/safety/execution/validation machinery onto the new controlled-runtime contracts, or rebuild it a third time** — and then close the specific, narrow gaps that are genuinely new (prediction, abstention wired into the live pipeline, and the historical-memory contract, none of which V1 solved either). Getting this decision right the first time matters, because the project has now paid the cost of "build a full generation, discover the foundation was wrong, freeze and restart" at least twice.

---

## 2. What actually exists — three architecture generations, not one

| Generation | Where | Foundation | How far it got | Status |
|---|---|---|---|---|
| **Gen 1 — original Phase 4** | `src/experience/`, `src/patterns/`, `docs/PHASE4_1_FAILURE_MEMORY.md`, `docs/PHASE4_2_FAILURE_PATTERNS.md` | Synthetic regime-drift data (`src/data/synthetic.py`) | Failure memory (PASS WITH ISSUES) and pattern learning (INCONCLUSIVE) | Frozen, superseded, not deleted |
| **Gen 2 — "V1" closed-loop runtime** | `src/runtime/*`, `src/failure_experience/*`, `src/recovery/*` (incl. `policy_v2`, `environment_v2`), `src/failure_memory/*`, `src/decision/policy.py` | Alibaba GPU2020 trace replayed through a serialized reliability artifact | **Full loop**: detect → assess → retrieve memory → diagnose → plan recovery → safety-gate → execute (simulated) → validate → persist experience → learn → update memory. Evaluated across 8 jobs / 7 conditions / 56 cases, 0 unsafe executions (`V1_FINAL_EVALUATION.md`). | Frozen ("V1 core architecture frozen... no production-readiness claim") because the trace can't act as a live decision-time source |
| **Gen 3 — current active "Phase 4"** | `src/phase4/*` | Project-owned controlled runtime, real subprocess execution, SQLite event store | Observability (`observability.py`) → monitoring/anomaly+failure detection (`monitoring.py`) → diagnosis (`diagnosis.py`). Contracts for prediction, decision/abstention, planning, safety, execution, validation exist as empty `Protocol`s in `architecture.py`. | **Active, incomplete.** Stops at diagnosis. |

Confirmed by direct dependency check: `src/phase4/` imports only `src.data_foundation.foundation` and its own submodules. It does **not** import `src.runtime`, `src.recovery`, `src.failure_memory`, `src.failure_experience`, or `src.decision` anywhere. The Gen 2 machinery is real, tested, and completely disconnected from the pipeline the project is currently building forward.

This is not a minor bookkeeping detail — it is the single most consequential fact for how Phase 4/5 should be planned, and it isn't stated plainly anywhere in the docs. `docs/PHASE4_PLAN.md` §11-12 gesture at "the rest of the originally-planned sequence remains open," and `RUNTIME_RELIABILITY_OBSERVABILITY_ARCHITECTURE_AUDIT.md` (dated the day before the Gen 3 restart) is a good self-audit of Gen 2 — but nothing in the repo says "Gen 2's recovery/safety/execution/validation code is a candidate for reuse on Gen 3" versus "abandon it and rebuild." Nobody has made that call.

---

## 3. Concrete problems, with evidence

**3.1 — Diagnosis is real but very shallow, and self-admittedly so.** `src/phase4/diagnosis.py`'s `DiagnosisEngine` handles exactly two failure classes (`PROCESS_TIMEOUT`, `PROCESS_NONZERO_EXIT`); everything else raises or returns `UNKNOWN`. Hypothesis scores are hardcoded literals (`0.4`, `0.2`, `0.1`), not fitted or calibrated against outcomes. `memory_used=False` is a hardcoded field — the docstring for `_eligible_current_incident` says plainly: "Diagnosis does not currently support a historical-memory input, so evidence from another run is never eligible merely because it is earlier in time." That is the right safety posture (no leakage), but it also means the "diagnosis and causal understanding" milestone claimed as in-progress in the project narrative is, concretely, a two-branch lookup table with static weights.

**3.2 — Anomaly detection is one fixed threshold.** `AnomalyDetector.detect()` in `monitoring.py` checks exactly one condition: `process_rss_bytes > 512MB`. There is no latency, throughput, error-rate, or drift signal despite the `RUNTIME_RELIABILITY_OBSERVABILITY_ARCHITECTURE_AUDIT.md`'s own telemetry-contract proposal listing all of those as required. `DetectionEvaluator.evaluate()` literally hardcodes `'unsupported_classes': ['GPU_FAILURE','SCHEDULER_FAILURE','NETWORK_FAILURE']` — a permanent, explicit admission that entire failure categories are out of scope, not a temporary gap.

**3.3 — The abstention engine — a named foundation of this whole project — is not wired into the live pipeline.** A repo-wide search for `abstention`/`Abstain` in `src/` returns hits only in `src/decision/policy.py`, `src/recovery/policy*.py`, `src/runtime/controller.py`, and evaluation modules — all Gen 1/Gen 2 code. `src/phase4/` has zero occurrences. `architecture.py`'s state machine does define an `ABSTAINED` state and allows `DECIDING → ABSTAINED`, so the seam is designed correctly, but `DecisionPolicyPort` has no implementation. The system that is supposed to "recognize uncertainty and abstain when it is unsafe to act" currently cannot abstain, because there is no decision stage at all between diagnosis and (nonexistent) planning.

**3.4 — Historical failure memory is exactly the unsolved problem the project itself flagged, and it is unsolved in a specific, checkable way.** Two working memory implementations exist (`src/failure_memory/memory.py`, `src/failure_experience/*`), both with real lifecycle bugs already found and partially fixed (`docs/FAILURE_MEMORY_LIFECYCLE_RECONCILIATION.md` — `rebuild()` vs `fit()` inconsistently promoting `_memory_version`). Neither is connected to Gen 3. There is no "historical-memory contract" document anywhere in `docs/` — the closest thing is the data-isolation section of the old `PHASE4_PLAN.md` §3, which was written for Gen 1's synthetic episodic data and never revisited for the controlled-runtime foundation.

**3.5 — The controlled runtime is real but tiny.** `controlled_runtime.py` is 84 lines. It launches genuine subprocesses and records genuine telemetry (this part of the pivot was the right call, and it shows — `_command`, `_emit`, real `subprocess` calls, not mocks). But scenario diversity is minimal: the failure taxonomy is `NONZERO_EXIT` / `TIMEOUT` only, telemetry is RSS and CPU ticks only, and everything runs in one environment. The project's own honest self-description ("validated primarily in one controlled environment with limited CPU/RSS telemetry") is accurate and should stay in every future report, not get quietly dropped as Phase 4 continues.

**3.6 — Development pace is a red flag worth naming, not just noting.** `git log` shows Phase 3.1 through the Phase 4.3 contamination fix — roughly 16 major "phases," each with its own protocol, implementation, and audit doc — landing across three calendar days (Aug 21–23), with the majority in a single day (Aug 23). Real audits, real leakage checks, and a real contamination bug were found and fixed in that window, which is good evidence the process isn't purely cosmetic. But a pace like this is also exactly the regime where a plausible-sounding audit report gets written faster than the corresponding validation actually happened. The concrete ask: from here on, every phase-completion doc should be checked against its actual test run output (pasted or logged, not just asserted), and reviewed by rerunning the claimed command, not by re-reading the prose.

**3.7 — The "649 passed, 0 failed, 0 skipped" full-suite claim could not be independently re-verified in this session.** The sandbox this audit ran in doesn't have `pytest` on the path reachable from the device shell and the project's `.venv` is a Windows venv (`Scripts/`, not `bin/`) that a Linux shell can't activate. This is disclosed rather than glossed over: the diagnosis contamination fix and the general shape of the pipeline were verified by reading the actual source and tests, not by re-running them. Re-running `pytest -q` on your machine and pasting the tail of the output is the single highest-value five-minute check before trusting any further claim in this document or in the next phase's report.

---

## 4. What this means for planning

Two decisions have to be made before any Phase 4/5 code gets written, because they change the shape of everything downstream.

**Decision A — reuse or rebuild the recovery/safety/execution/validation layer?** Recommendation: **adapt, don't rebuild.** `src/recovery/policy.py`, `feasibility.py`, `taxonomy.py`, `validation.py`, and `src/runtime/components.py` (`RuleBasedRecoveryPlanner`, `SimulatedRecoveryExecutor`, `SignalRecoveryValidator`, `RuntimeLearningManager`) already implement every `Protocol` in `architecture.py`'s back half in spirit, already have a safety gate that rejected 100% of unsafe proposals across 56 real-data cases, and already have tests. The work is writing thin adapters from the Gen 3 `FailureEvent`/`StructuredDiagnosis` contracts to what those components expect — not re-deriving planning, safety, and validation logic from zero a third time. This should be a short, explicit spike (days, not weeks) that produces a written verdict — "these N components port with an adapter, these M don't and here's why" — before Phase 5 implementation starts.

**Decision B — what does "historical memory without contamination" actually mean for Gen 3?** This has to be a written, frozen contract *before* any memory read path is added to `diagnosis.py`, the same discipline the project already used for Phase 3's protocols. At minimum it must fix, in writing: what scope a memory record can be retrieved within (run/workload/environment, matching what the contamination fix just enforced for current-run evidence — memory must not be looser than that); what "relevant" means and how it's scored (Gen 2 already has a `MemoryMatch` implementation with a relevance flag — reusable, per Decision A); how memory versions are promoted so a diagnosis is reproducible against a specific memory snapshot; and how the frozen-test-once rule from `PHASE4_PLAN.md` §3 applies to any evaluation of "does memory help."

---

## 5. Phase 4 completion plan — operational intelligence layer

Ordered by dependency, each item states what exists, what's missing, and the concrete deliverable.

**4.A — Expand detection and diagnosis coverage.** Exists: 2 failure classes, 1 anomaly rule. Missing: at minimum resource-pressure (sustained CPU), and a second, genuinely different anomaly signal so "anomaly detection" isn't one threshold. Deliverable: extend `FailureDetector`/`AnomalyDetector` with 2-3 additional signal types, each with its own test scenario in `controlled_runtime.py`, and remove or narrow the hardcoded `unsupported_classes` list by actually supporting one of the three currently-excluded categories (network failure is the most tractable — kill connectivity to a subprocess dependency).

**4.B — Implement `PredictionPort`.** Exists: nothing concrete; the interface is defined. This is a real, currently-absent capability — not a rewiring job. Deliverable: a `PredictionPort` implementation over the controlled-runtime telemetry stream that predicts failure risk *before* a `failure_detected` event, evaluated against a held-out set of runs with a real precision/recall/lead-time metric (not just "it produces a number"). This is where "predicting problems before they become catastrophic" stops being aspirational.

**4.C — Implement `DecisionPolicyPort` with abstention.** Exists: `src/decision/policy.py` (Gen 2, disconnected) has a working confidence/abstention policy already evaluated in Phase 3. Missing: it's not wired to `PredictionPort` output or exposed through `AutonomyState.DECIDING`. Deliverable: adapt `DecisionPolicy` onto the Gen 3 `Prediction` contract, with explicit calibration thresholds (not tuned against whatever the eventual test split is — freeze thresholds before touching held-out data, per the project's own stated discipline).

**4.D — Write and freeze the historical-memory contract**, per Decision B above, then implement it as a real read path in `DiagnosisEngine` (a new `evidence_kind=HISTORICAL` branch alongside the existing `CURRENT`/`DERIVED` ones already modeled in `EvidenceKind`). Deliverable: `docs/PHASE4_MEMORY_CONTRACT.md` (frozen before implementation) + a diagnosis-with-memory vs. diagnosis-without-memory ablation on held-out runs, reporting whether memory measurably changes diagnosis confidence/accuracy — the same honest "measured, don't assume" standard the project applied to recovery-planner memory in Gen 2's `MASTER_IMPLEMENTATION_REPORT.md`.

**4.E — Multi-environment validation.** Exists: one controlled environment. Deliverable: run the full observability→diagnosis pipeline in at least a second distinct environment (different machine profile, container vs. host process, or a second OS if available) and report whether detection/diagnosis behavior holds — this directly answers the project's own stated limitation ("lacks independent environments").

Phase 4 is done when: prediction, decision/abstention, and memory-aware diagnosis are concrete implementations (not `Protocol` stubs) wired into one pipeline run end-to-end from `RECEIVED` to `DIAGNOSING`/`ABSTAINED`, evaluated in ≥2 environments, with every claim traceable to a logged test run.

---

## 6. Phase 5 plan — closed-loop self-healing

This phase is where Decision A pays off. Rather than "design a recovery planner," the task is "port the validated Gen 2 planner/safety-gate/executor/validator onto Gen 3's diagnosis output, and add the one genuinely new piece: recovery outcomes feeding back into the Phase 4 memory contract."

**5.A — Adapter layer.** Write `PlannerPort`, `SafetyGatePort`, `ExecutorPort`, `ValidatorPort` implementations in `src/phase4/recovery.py` that internally call the existing `RuleBasedRecoveryPlanner`/safety checks/`SimulatedRecoveryExecutor`/`SignalRecoveryValidator` (or their `src/recovery/policy.py` equivalents), translating Gen 3's `StructuredDiagnosis` into whatever input shape those components expect. Keep the executor simulated — the project has never claimed a real executor and shouldn't start now without a separate, explicit safety review.

**5.B — Safety gate hardening.** Gen 2's gate already achieved 0/56 unsafe executions, which is real evidence, but it was evaluated against Gen 2's action taxonomy on trace-replay data. Deliverable: re-run the same style of adversarial/conflicting-evidence test matrix (`C3 conflicting memory`, `C5 safety conflict` from `V1_FINAL_EVALUATION.md`) against the Gen 3 controlled runtime's actual action set (retry/rollback/reconfigure/retrain/redeploy, whichever are feasible against a subprocess workload) before allowing any executed action.

**5.C — Independent recovery validation.** Exists in Gen 2 (`SignalRecoveryValidator`, independent of the executor). Deliverable: confirm the ported validator checks workload health *independently* of "the executor reported success" — i.e., an actual post-recovery telemetry probe against the controlled runtime, not a trust-the-executor rubber stamp. This is the single most important claim in the entire project's mission statement ("verify the result... rather than assuming that an attempted action means success"), so it deserves its own explicit test: inject an executor that lies about success and confirm the validator still catches it.

**5.D — Learning feedback loop.** New work, not a port: recovery outcome → `FailureExperience` → the Phase 4.D memory contract → next diagnosis. Deliverable: repeat Gen 2's control-vs-learned experiment (`docs/LEARNING_INFLUENCE_REPORT.md` is a good template) on the Gen 3 foundation — same honesty standard: report what changed (retrieval, confidence, action selection) and be explicit about what wasn't established (real-world generalization).

**5.E — End-to-end evaluation against baselines.** No-recovery baseline, fixed-rule recovery (no memory), and memory-informed recovery, run across the same scenario set from 4.A/4.E, reporting recovery success rate, unsafe-proposal rate, and abstention rate for each — mirroring the B0-B5 baseline matrix Gen 2 already used, so the comparison is apples-to-apples with the project's own prior standard.

Phase 5 is done when: a controlled-runtime failure can be observed, diagnosed, planned against, safety-gated, (simulated-)executed, independently validated, and the outcome measurably changes a later diagnosis — end to end, in the live Gen 3 pipeline, with zero unsafe executions across the adversarial test matrix and a written claim-boundary doc in the same style as `V1_RELEASE_AUDIT.md`.

---

## 7. Immediate next actions (this week)

1. Re-run `pytest -q` for real and paste the tail of the result into the next doc — close the one claim in this audit that couldn't be independently verified.
2. Spend one session on Decision A (port-vs-rebuild spike for the recovery/safety/execution/validation layer) and write the verdict down.
3. Draft `docs/PHASE4_MEMORY_CONTRACT.md` (Decision B) and get it frozen before writing a single line of memory-read code in `diagnosis.py`.
4. Start 4.B (`PredictionPort`) — it's the one Phase 4 gap with no existing code anywhere in the repo to lean on, so it has the longest lead time.

---

## 8. What I did not do

I did not modify any code or docs in the repository, and I did not run the test suite (environment constraint, disclosed in §3.7). This document is an audit and a plan, not an implementation — the next step should be picking which of §5-7 to execute first.
