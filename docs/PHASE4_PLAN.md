# Phase 4 Plan — Self-Learning & Validation

**Status: APPROVED (reviewed and authorized).** Phase 4.0 is **COMPLETE**
— see [`docs/PHASE4_0_EPISODIC_DATA.md`](PHASE4_0_EPISODIC_DATA.md).
Phase 4.1 is **COMPLETE — 🟡 PASS WITH ISSUES** (H1 partially supported)
— see [`docs/PHASE4_1_FAILURE_MEMORY.md`](PHASE4_1_FAILURE_MEMORY.md).
Phase 4.2 is **COMPLETE — 🟡 INCONCLUSIVE** (H2 inconclusive, evidence
volume insufficient) — see
[`docs/PHASE4_2_FAILURE_PATTERNS.md`](PHASE4_2_FAILURE_PATTERNS.md).
Phase 4.3 has not started; per the authorization, subphases proceed one
at a time in frozen sequence, each implemented/tested/documented before
the next begins.

This document is the pre-registered plan required before any Phase 4 code
is written, per the project's research-integrity rule (see
[`docs/PHASE3_FREEZE.md`](PHASE3_FREEZE.md), which this plan does not
modify). It fixes subphase sequence, dependencies, hypotheses, data
protocol, metrics, and completion criteria *before* any Phase 4 result is
computed — the same discipline Phase 3.1's frozen protocol established
for Phase 3.

## 0. Where Phase 3 left off (the starting position, not re-litigated)

Frozen findings this plan must not silently overwrite (full detail in
[`PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md`](PHASE3_6_DIAGNOSIS_ABSTENTION_RECOVERY.md),
[`PHASE3_FREEZE.md`](PHASE3_FREEZE.md)):

- **B (calibrated confidence) is the strongest, cheapest signal at every
  axis tested.** F (Supervised Failure Risk) and B+F provide no measurable
  incremental value over B alone (Phase 3.4, 3.6 §4).
- **Diagnosis (condition attribution)** is a deterministic, zero-fitting
  rule — perfect on `feature_dropout`, weak on mild `feature_noise`
  (recall 42.5%).
- **Recovery**: retry succeeds ~55% of the time it fires (45% of
  "recoveries" are still wrong); reconfigure recovers **0/N** because its
  fallback signal (B) shares the same corruption as the primary signal.
- **Autonomous decision authority is NOT justified** by any Phase 3
  result. This conclusion stands until Phase 4 produces new,
  independently evaluated evidence.
- Reusable, frozen-in-place components (Phase 4 must not edit these
  in-place — see §5 isolation rules): `src/schema/events.py`
  (`ReliabilityEvent` already carries `workload_id`, `context`,
  `confidence`, `failure_risk`, `decision`, `outcome`, `failure_cluster`,
  `metadata`, `timestamp` — most of the Phase 4.1 field list already
  exists), `src/storage/` (SQLAlchemy persistence + repository),
  `src/failure_memory/` (existing embedding + clustering, currently used
  only for the F signal), `src/decision/policy.py` (the one authoritative
  decision policy), `src/evaluation/{diagnosis,recovery,decision_policy}.py`
  (deterministic Phase 3.6 rule/policy implementations).

## 1. Critical data gap (why Phase 4.0 exists)

Phase 3's benchmark (`src/data/synthetic.py`) generates **i.i.d.
classification samples** under a regime-drift/attack condition — there is
no notion of a *recurring workload* experiencing *repeated incidents over
time*, no recovery-attempt trace, and no "the system saw this failure
mode last week and is now facing it again." Phases 4.2 (pattern
learning), 4.3 (recovery strategy learning), 4.6 (continual learning),
and 4.7 (generalization) all require **episodic, temporally-ordered
incident data with repeatable workload/condition identity** — this does
not exist yet and must be built first.

**Phase 4.0 — Incident/Episode Data Generation** (prerequisite, not in
the original numbered list but required before 4.1 can be evaluated
meaningfully):

- Extend (not modify in place — new module `src/data/episodic.py`)
  `synthetic.py`'s regime/attack machinery to emit **episodes**: a
  sequence of `(workload_id, timestamp, context, true_label, model
  prediction, confidence, decision, outcome, recovery_action,
  recovery_outcome)` tuples, grouped into incidents, across many
  synthetic "workloads" (parameterized regime/attack combinations) that
  **recur** across simulated time with configurable recurrence rate,
  drift, and novel (held-out) conditions.
- Deterministic, seeded, documented generator — same reproducibility bar
  as `synthetic.py` (fixed seeds, closed-form ground truth for what
  "recurring" vs. "novel" means, so generalization in 4.7 can be checked
  against a known answer instead of an assumption).
- Deliverable: `src/data/episodic.py`, `docs/PHASE4_0_EPISODIC_DATA.md`
  (generator spec + leakage-relevant properties: what info is available
  at decision time vs. only after outcome is known).

## 2. Subphase sequence and dependencies

```
4.0 Episodic data generator
 └─▶ 4.1 Failure memory & experience schema/store
      └─▶ 4.2 Pattern learning  ──────────────┐
      └─▶ 4.3 Recovery strategy learning ─────┤
                                               ├─▶ 4.4 Safe learning & abstention integration
                                               │        (gates 4.2 + 4.3 outputs)
4.5 Learning protocol & data isolation ◀───────┘  (defined alongside 4.0, enforced from 4.1 onward)
      └─▶ 4.6 Continual learning experiments
      └─▶ 4.7 Generalization evaluation
              └─▶ 4.8 Learning validation & safety gates
                       └─▶ Phase 4 verification report
```

4.5 is not "step 5 chronologically" — its protocol (train/validation/
frozen-test split, freeze points) must be **written and frozen before
4.1's store is first populated with anything used for evaluation**, the
same way `configs/phase3_1_protocol.json` predated Phase 3.1's first
result. It is listed as 4.5 to match the requested numbering, but
enforced from 4.0 onward.

## 3. Data isolation protocol (write this before touching 4.1)

- **Learning/training split**: episodes from "known" workload/condition
  combinations, regime-2-equivalent role (matches Phase 3's regime-2 =
  "fit-only" convention) — failure memory is populated and pattern/
  recovery-strategy learning fits only here.
- **Validation split**: held-out episodes from known combinations, used
  for threshold/confidence-gate tuning (4.4) and early stopping in
  continual-learning experiments (4.6). May be touched repeatedly during
  development.
- **Frozen test split**: sealed before 4.6 begins, touched **exactly
  once** per pre-registered experiment, covering both (a) unseen episodes
  of known combinations and (b) entirely novel workload/condition
  combinations never in train or validation (required for 4.7).
- Freeze artifact: `configs/phase4_learning_protocol.json` (row-hash
  manifest of the frozen test split, same leakage-audit pattern as
  `phase3_1_leakage_audit.py` — a `phase4_leakage_audit.py` checks zero
  row-hash overlap between splits, and that no learned parameter's
  fitting code path ever touches the frozen split).
- **Learned-state versioning**: every fitted memory/pattern/policy
  artifact gets a content-hashed version id + manifest (training data
  version, code version, seed, timestamp) written alongside it — this is
  what 4.5's "how learned state is versioned" and the Research Integrity
  §5/§6 requirements need concretely.
- Rule, stated explicitly and enforced by the audit script: **once the
  frozen test split is evaluated for a given learned-state version, that
  version is retired** — no re-fitting and re-testing the same
  architecture against the same frozen split to chase a better number.

## 4. Subphase plans

Each subphase follows the Implementation Rule in the brief (inspect →
identify reuse → define hypothesis → define evaluation → smallest
research-valid version → test → evaluate → document). Below fixes the
hypothesis, baseline, and metrics for each — the "smallest valid version"
decision is made at implementation time per subphase, but must be
justified against the frozen protocol here, not decided ad hoc.

### 4.1 — Failure Memory & Experience Learning

- **Hypothesis (H1)**: a structured, indexed experience store built on
  `ReliabilityEvent` + episode outcome data can retrieve relevant past
  incidents for a new failure with better-than-chance similarity
  ranking, without becoming an unstructured log.
- **Reuse**: extend `src/storage/` (repository pattern) and
  `src/failure_memory/embedding.py` rather than building new persistence
  from scratch. New: `src/experience/` module for the
  store/retrieve/decay API, kept separate from `src/failure_memory/`
  (frozen) rather than editing it in place.
- **What is stored**: only fields listed in the brief that are
  reconstructable from schema/episode data — explicitly *not* raw
  input payloads beyond the existing `context: dict[str,float]`
  vector (no free-text, no PII — same constraint `SCHEMA.md` already
  enforces via `metadata`).
- **Staleness/decay**: recency-weighted retrieval score, decay function
  fixed before 4.6 experiments run (not tuned against frozen test data).
- **Metrics**: retrieval precision@k / recall@k against known
  ground-truth "same underlying condition" labels from the episodic
  generator (§4.0's known ground truth is what makes this measurable
  instead of assumed).
- **Baseline**: no-memory (uniform-random retrieval) and
  recency-only (most-recent-k, no similarity) retrieval.

### 4.2 — Failure Pattern Learning

- **Hypothesis (H2)**: recurring failure patterns (condition recurrence,
  temporal clustering, symptom→cause→outcome relationships) are
  detectable above chance in the episode stream, and the system can
  correctly separate observed evidence from inferred pattern from
  confirmed relationship from uncertain hypothesis (four explicit
  confidence tiers, not a single score).
- **Reuse**: `src/failure_memory/embedding.py` clustering as a candidate
  pattern-detection primitive (already shown modest signal in Phase
  3.2/3.2C); diagnosis taxonomy from `src/evaluation/diagnosis.py`
  (frozen, reused read-only) as one input feature, not retrained.
- **Metrics**: precision/recall of detected recurring patterns against
  §4.0's known ground-truth recurrence structure; calibration of the
  four-tier confidence labeling (does "confirmed" actually mean higher
  precision than "hypothesis," measured, not asserted).
- **Baseline**: no pattern learning (each incident treated
  independently) vs. naive frequency-count pattern flagging (no
  confidence tiering) vs. the proposed tiered approach.

### 4.3 — Recovery Strategy Learning

- **Hypothesis (H3)**: using historical recovery outcomes to select
  among {retry, rollback, restart, reconfigure, abstain, retrain,
  redeploy} produces a lower expected-cost / lower-unsafe-rate policy
  than Phase 3.6's fixed diagnosis→action rule, when experience
  relevance is evaluated (similarity, context compatibility, recency,
  evidence quantity, provenance) rather than applied blindly.
- **Explicit non-goal**: "past success implies future success" is
  disallowed by construction — every candidate strategy selection must
  attach a relevance/reliability score computed from the dimensions
  listed in the brief, and a strategy with low relevance score must be
  down-weighted or excluded, not used at full trust.
- **Reuse**: `src/evaluation/recovery.py` (frozen) as the Phase 3.6
  baseline policy, evaluated unmodified for comparison; new
  `src/experience/recovery_selector.py` as the learned alternative.
- **Metrics**: recovery success rate, unsafe-action rate (recovered but
  still wrong — Phase 3.6 §17's key finding), expected cost under the
  same frozen cost model as `configs/phase3_6_decision_recovery_protocol.json`
  (reused unmodified for comparability, not re-derived).
- **Baseline**: Phase 3.6's frozen diagnosis-gated recovery policy
  (retry/reconfigure/rollback, as-is) — this is the primary baseline for
  the whole of Phase 4.3, not a strawman.

### 4.4 — Safe Learning & Abstention

- **Hypothesis (H4)**: gating learned recovery/pattern knowledge by an
  evidence/confidence threshold reduces the unsafe-action rate relative
  to using learned knowledge unconditionally, at an acceptable utility
  cost (mirrors the cost-ratio sensitivity method from Phase 3.6 §7/§13).
- **Integration point**: extends `src/decision/policy.py`'s tiering
  logic (frozen — extend via a new decision layer that *consumes* its
  output, does not edit it in place) to add a fourth outcome: "abstain
  from applying learned knowledge, fall back to Phase 3.6's static
  policy" — i.e., a meta-abstention over the *learning* itself, distinct
  from abstention over the *answer*.
- **Metrics**: false-confidence rate (learned knowledge applied with high
  stated confidence but wrong), unsafe-autonomous-action rate with vs.
  without the gate, abstention-quality (does gating catch the cases where
  learned knowledge would have been wrong, at what precision/recall).
- **Baseline**: (a) no gate — always apply learned knowledge; (b) always
  abstain from learned knowledge (equivalent to pure Phase 3.6 policy);
  (c) the proposed evidence-gated policy. (b) is expected to be safest
  but least autonomous — the report must state where the proposed policy
  actually lands between (a) and (b), not assume it strictly dominates.

### 4.5 — Learning Protocol & Data Isolation

Protocol document + `phase4_leakage_audit.py`, written per §3 above,
frozen before 4.6. Deliverable is the audit passing with zero violations
on whatever is built in 4.1–4.4, re-run (not re-derived) before 4.6/4.7.

### 4.6 — Continual Learning Experiments

- **Hypothesis (H5)**: `Initial system → observe failures → learn →
  re-evaluate` produces a measurable, statistically distinguishable
  (bootstrap CI, same method as Phase 3.1 `bootstrap.py`, reused)
  improvement over a frozen-knowledge control on the metrics in §"Phase
  4.6" of the brief (detection, diagnosis, recovery success/selection,
  abstention, reliability, false recovery, overhead, latency,
  memory/compute cost).
- **Design**: multiple seeds (reuse Phase 3's seed convention `[1,2,3,4,5,42]`,
  primary seed 42) × multiple checkpoints along the episode stream
  (e.g., after 0/N, 1/N, ..., N/N training incidents) evaluated each time
  against the **same frozen validation split**, with the **frozen test
  split touched only once at the final checkpoint** per §3.
- **Controls needed to distinguish real learning from confounds** (the
  brief's explicit requirement): (a) frozen-knowledge control (same
  architecture, learning disabled after checkpoint 0) to separate
  learning from simple additional-observation noise; (b) shuffled-label
  control (experience store populated with mismatched
  incident↔outcome pairs) to detect memorization/overfitting rather than
  generalizable learning; (c) distribution-shift control (checkpoints
  compared only within the same underlying regime, to rule out the
  "improvement" being a change in test-stream difficulty rather than
  learning).
- **Baseline**: Phase 3.6's frozen policy (zero learning) is the headline
  comparison, per the brief's "compare against the relevant Phase 3
  baseline."

### 4.7 — Generalization of Learned Knowledge

- **Hypothesis (H6)**: knowledge learned from training-split incidents
  transfers with reduced-but-nonzero effectiveness to (a) unseen
  instances of known conditions, (b) entirely novel workload identities,
  (c) altered operating conditions, (d) novel symptom combinations —
  using §4.0's known ground-truth novelty labeling to measure this
  directly rather than assuming transfer.
- **Metrics**: same as 4.6, stratified by novelty category, each
  compared against the frozen-knowledge control from 4.6 at matched
  novelty category (a fair comparison needs the control to see the same
  novel cases, not just the learner).
- Explicit finding target: does performance degrade gracefully with
  novelty distance, or cliff sharply at any tested boundary — report
  whichever is observed.

### 4.8 — Learning Validation & Safety Gates

- **Hypothesis (H7)**: a predefined, reproducible validation procedure
  can correctly sort learned artifacts (a pattern, a recovery
  association, a policy update) into `validated / uncertain / invalid /
  unsafe`, and this sorting measurably improves downstream safety (lower
  unsafe-action rate) versus admitting all learned artifacts
  unconditionally.
- **Reuse**: this is 4.4's gate generalized from "gate a decision" to
  "gate a piece of learned state before it is ever eligible to influence
  a decision" — implemented as a promotion pipeline in front of the 4.1
  store, not a duplicate mechanism.
- **Metrics**: validation-outcome distribution, and (per the brief)
  auditability — every validation decision must log its inputs,
  thresholds, and outcome in a reproducible, queryable form (reuse
  `src/storage/repository.py` patterns).
- **Baseline**: unconditional admission of all learned artifacts (no
  gate) — same comparison structure as 4.4.

## 5. Metrics reference (definitions fixed before any Phase 4 result)

| Metric | Definition | Source data | Reused from Phase 3? |
|---|---|---|---|
| AUROC/AUPRC/ECE/AURC | Same as `src/evaluation/metrics.py` | frozen/held-out splits | Yes, unmodified |
| Bootstrap CI | Same as `src/evaluation/bootstrap.py` | per-seed results | Yes, unmodified |
| Retrieval precision@k/recall@k | New (4.1) | episodic ground-truth condition identity | No — new |
| Pattern precision/recall by tier | New (4.2) | episodic ground-truth recurrence | No — new |
| Recovery success/unsafe-action/expected cost | Same formulas as Phase 3.6 §7/§13/§17 | episodic recovery outcomes | Reused definitions, new data |
| False-confidence rate | New (4.4) | learned-knowledge applications vs. ground truth | No — new |
| Generalization gap | performance(novel) − performance(known), same metric | 4.7 stratified splits | No — new |
| Operational overhead | wall-clock + memory delta, learning vs. frozen-knowledge control | 4.6 runs | No — new |

Each new metric gets its own short spec (definition, rationale,
calculation method, data source, limitations) in the corresponding
subphase doc, per Research Integrity Requirement 2 — not merely listed
here.

## 6. Ablations (planned, not exhaustive — extend if a result motivates one)

- 4.2: pattern learning with vs. without the four-tier confidence
  labeling (does tiering matter, or would a single score do as well).
- 4.3: recovery selection with vs. without each relevance dimension
  (similarity / recency / evidence quantity) removed one at a time.
- 4.4: gate threshold sensitivity sweep (mirrors Phase 3.6's cost-ratio
  sensitivity sweep methodology).
- 4.6: with vs. without each control (b)/(c) from §4.6 above, to isolate
  which confound each control actually rules out.

## 7. Completion criteria checklist (mirrors the brief verbatim, tracked here)

- [ ] All planned subphases (4.0–4.8) implemented, or explicitly marked
      not-implemented with justification.
- [ ] Failure memory functional and provenance-aware.
- [ ] Learned knowledge influences decisions only through the 4.4/4.8
      controlled gate mechanism.
- [ ] Safety/abstention integrated (4.4).
- [ ] Learning/evaluation data isolation enforced and audited (4.5).
- [ ] Continual learning experimentally evaluated with controls (4.6).
- [ ] Generalization evaluated (4.7).
- [ ] Baselines (Phase 3.6 frozen policy) and ablations conducted.
- [ ] Results reproducible (seeds, versions, configs recorded).
- [ ] Negative/inconclusive findings documented, not omitted.
- [ ] No frozen-test contamination or metric manipulation (audited).
- [ ] All code/experiments/configs/docs committed.
- [ ] Formal Phase 4 verification report produced with an honest status:
      PASS / PASS WITH ISSUES / INCONCLUSIVE / FAIL.

## 8. Deliverables → subphase map

| # | Deliverable | Produced by |
|---|---|---|
| 1 | Failure memory architecture | 4.1 |
| 2 | Structured failure/experience representation | 4.1 |
| 3 | Experience retrieval mechanism | 4.1 |
| 4 | Failure pattern learning mechanism | 4.2 |
| 5 | Recovery strategy learning mechanism | 4.3 |
| 6 | Safety/abstention integration | 4.4 |
| 7 | Learning validation mechanism | 4.8 |
| 8 | Strict train/validation/test isolation | 4.0/4.5 |
| 9 | Continual learning evaluation framework | 4.6 |
| 10 | Generalization evaluation | 4.7 |
| 11 | Baseline comparison | 4.6/4.7 (vs. Phase 3.6 frozen) |
| 12 | Quantitative evaluation results | all |
| 13 | Ablation studies | 4.2/4.3/4.4/4.6 |
| 14 | Failure-case analysis | all, esp. 4.6/4.7 |
| 15 | Learning-state/provenance tracking | 4.1/4.5 |
| 16 | Reproducible experiment configs | all (`configs/phase4_*.json`) |
| 17 | Phase 4 documentation | `docs/PHASE4_*.md` per subphase |
| 18 | Phase 4 verification report | final, after 4.8 |

## 9. What this plan deliberately does not decide yet

Per the Implementation Rule, the *specific* model/algorithm choice for
each subphase (e.g., what similarity metric 4.1 retrieval uses, what
form the 4.3 relevance score takes) is decided at implementation time,
starting from the smallest research-valid version, and documented in
that subphase's own report — not pre-committed here. What *is* fixed
here is unbuildable-around-later: the sequence, the hypotheses, the
baselines, the isolation protocol, and the completion/status criteria.

## 10. Review decisions (recorded, not open anymore)

Reviewed and authorized. Decisions, verbatim in substance:

1. **Phase 4.0 — APPROVED.** Accepted as an explicit, in-scope
   prerequisite. Built per §1's spec: `src/data/episodic.py`, existing
   Phase 3 synthetic generator left unmodified, deterministic/seeded,
   decision-time vs. outcome-time fields kept distinct, known ground
   truth for recurrence/novelty, documented and tested before any
   subphase depends on it. **Status: COMPLETE** — see
   `docs/PHASE4_0_EPISODIC_DATA.md`.
2. **Frozen Phase 3 boundary — APPROVED, with clarification.** Phase 4
   extends via new modules (`src/data/episodic.py`, and `src/experience/`
   once Phase 4.1 begins) that *consume* frozen Phase 3 components
   read-only, rather than editing them in place. Concretely for Phase
   4.4's later gate: `Phase 3 decision/policy → Phase 4 learning layer →
   safety/abstention gate → final action`, not a rewrite of
   `src/decision/policy.py`. This boundary was followed exactly in Phase
   4.0 (verified structurally by the leakage audit's
   `no_regime_0_1_2_row_ever_emitted` check, not just by code review).
3. **Primary research question — APPROVED**, unchanged from §"Required
   Evaluation Philosophy" of the brief, framing the final verification
   report (deliverable 18). The report's status categories remain
   yes/partially/no/inconclusive — not structured to prove "yes."
4. **Research-integrity clarification on inconclusive results —
   APPROVED and binding for the rest of Phase 4.** An earlier
   subphase's INCONCLUSIVE (or any other) finding is never retroactively
   changed. A later subphase may add independently-justified new
   evidence; if that resolves the earlier uncertainty, the progression is
   documented explicitly (`Earlier experiment → INCONCLUSIVE`, `New
   experiment → additional evidence`, `Combined evidence → <verdict>`),
   never silently overwritten. Same discipline `docs/PHASE3_FREEZE.md`
   already established for Phase 3.

**Authorization scope**: proceed to Phase 4.0 only, which is now done.
Do not begin Phase 4.1 without a further go-ahead per the frozen
sequence in §2.

## 11. Amendment — real-data expansion, revised Phase 3, and the active Phase 4.1 reboot

*(Added after §0–§10 above; nothing above this section was edited or
retroactively changed.)*

After Phase 4.0/4.1/4.2 (§0–§10, all synthetic-data-only) were completed and
frozen, the project substantially expanded its evaluation data with three
real datasets (AgentRx, AIOps 2020, Alibaba GPU 2020 cluster trace — see
`data/`) and re-ran Phase 3 against them
(`docs/PHASE3_REAL_DATA_*.md`, decision in
`docs/PHASE3_REAL_DATA_3_6_DECISION.md`). Phase 4 was then deliberately
paused before continuing, to reassess Phase 4's design against the new data
and the revised Phase 3 findings — the real-data pipeline currently
produces detection only (no diagnosis/recovery/validation on real data, a
documented gap, see that decision doc's H6/H7).

**The old Phase 4.1 (§4.1 above, `docs/PHASE4_1_FAILURE_MEMORY.md`) and old
Phase 4.2 (§4.2 above, `docs/PHASE4_2_FAILURE_PATTERNS.md`) are NOT
retroactively changed by this amendment** — both remain frozen, exactly as
recorded, per this document's own §10 item 4 research-integrity rule.

A new, independent, additive package (`src/failure_experience/`) implements
the **current active Phase 4.1** against the post-expansion repository
state — see [`docs/PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md`](PHASE4_1_ACTIVE_FAILURE_EXPERIENCE.md)
for the full audit, design, implementation, experiments, and status. It
does not import, edit, or extend-in-place `src/experience/` (old 4.1) or
`src/patterns/` (old 4.2). Phase 4.2 onward (pattern learning, recovery
policy learning, etc.) has not been redone or restarted — this amendment
covers Phase 4.1 only; the rest of the originally-planned sequence (§2, §4)
remains open and unauthorized pending a further go-ahead, same as before.
