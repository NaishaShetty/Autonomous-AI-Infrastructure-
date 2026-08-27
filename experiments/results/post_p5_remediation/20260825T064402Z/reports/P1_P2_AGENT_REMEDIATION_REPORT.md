# P1/P2 Agent Uncertainty & Decision Remediation Report — Step 5

Executed exactly per
`protocol/P1_STEP5_SENTIMENT_UNCERTAINTY_PROTOCOL.md`, pre-registered
before any candidate was run on the test split. Raw results:
`raw/p1_step5_sentiment_uncertainty_results.json`. Script:
`scripts/run_p1_step5_sentiment_uncertainty.py`.

## P1-W1: sentiment uncertainty — root cause identified, not fixable by estimator choice

| Candidate | Test AUROC | Brier | ECE |
|---|---|---|---|
| Baseline (raw softmax confidence) | 0.6286 | 0.0882 | 0.0890 |
| Margin (top1 − top2) | 0.6286 | 0.0858 | 0.0870 |
| Entropy-based confidence | 0.6286 | 0.0783 | 0.0774 |
| Temperature-scaled confidence (T=2.93, fit on calibration split only) | 0.6286 | **0.0749** | **0.0235** |

**Finding, with the mathematical reason stated plainly:** all four
candidates produce **identical AUROC** (to 4 decimal places — the tiny
residual differences are floating-point noise from `argmax` ties, not a
real distinction). This is not a coincidence or a bug in the harness: for
a **binary** classifier, raw softmax confidence, margin, entropy-based
confidence, and any monotonic temperature rescaling of the same logits are
all **rank-equivalent** — each is a strictly monotonic function of the
same underlying "how far the top-class logit sits above the other one"
signal. AUROC (and AUPRC) are purely rank-based metrics, so no post-hoc
recalibration of a single binary softmax output can change them, by
construction. **This is a clean, mathematically-grounded negative result,
not an unexplained one, and it directly answers the P1-W1 question:
sentiment's weak AUROC is NOT explained by "inappropriate uncertainty
estimator" — no reformulation of this model's own confidence signal can
improve ranking, so the gap versus arithmetic (0.953) and QA (0.934) most
likely reflects either (a) an intrinsic property of this specific
DistilBERT sentiment checkpoint's error structure on this corpus, or (b)
a genuinely harder discrimination problem for this task family — not a
locally fixable calibration/estimator defect.**

**What temperature scaling DID fix, honestly reported alongside the
non-improvement:** ECE dropped from 0.089 to 0.023 (a 74% reduction) and
Brier from 0.088 to 0.075 — the model's raw confidence values were
genuinely overconfident (fitted `T = 2.93`, meaning the model's logits
needed to be softened substantially to match its real accuracy), and
temperature scaling is a real, legitimate fix for that specific problem.
**Calibration and discrimination are different properties** — this result
improves the former while leaving the latter, which the model genuinely
lacks for this task, unchanged. Per the master remediation register's
integrity rules, this is reported as a genuine, partial, honest outcome:
FIXED for calibration, NOT FIXED (and not fixable by this class of method)
for discrimination.

**Per protocol's stopping rule:** no candidate showed a >0.03 AUROC
improvement over baseline (all showed exactly 0.0). No further candidates
were invented or tried after seeing this result. MC-Dropout / a small
local ensemble were pre-registered as considered-but-excluded (would
require changing the model's deterministic-inference contract, or
training a second checkpoint — out of scope for this remediation phase);
if sentiment discrimination is revisited in a future phase, those are the
next legitimate candidates to try, not a mechanically different
recalibration of the same single-checkpoint softmax output.

## P1-W2: real-model coverage — unchanged, no action needed

Arithmetic self-consistency, sentiment (DistilBERT), and extractive QA
(DistilBERT-SQuAD) remain the three real, local, no-paid-API models. No
model was added or removed in this remediation phase. Per the master
register's explicit instruction not to expand the model set merely to
cherry-pick a favorable result, and since this step's finding for
sentiment is a genuine, well-explained negative result rather than a gap
an additional model would close, no expansion was made.

## P1-W3: mechanism-aware uncertainty interface — verified working, no change needed

`src/phase4/uncertainty_eval.py`'s `UncertaintyRecord.mechanism` field and
`compute_uncertainty_metrics_by_task_family` already preserve per-family
mechanism labels while sharing one common metrics interface (AUROC/AUPRC/
Brier/ECE/risk-coverage) — confirmed by direct use in this step (four
different `mechanism` labels flowed through the same harness without
collapsing them into one formula). No change was needed; this was already
correctly designed.

## P2-W2: RETRY availability per task family — verified correct, no fabrication found

Confirmed by reading `src/phase4/agent_calibration.py`: `RETRY` is defined
**only** for the arithmetic self-consistency agent, where it has a
concrete, legitimate meaning (resample with more independent samples,
`RETRY_SAMPLE_INCREASE_FACTOR = 2`, capped at `MAX_RETRY_N_SAMPLES = 40`).
No code path in this repository defines or fabricates a RETRY mechanism
for the sentiment or QA classifiers — both are single deterministic
forward passes with no natural resampling axis, and no `agent_calibration`
-equivalent module exists for them. This already matches the master
register's explicit instruction ("only define RETRY where retry has a
legitimate meaning... explicitly mark RETRY unavailable rather than
inventing a mechanism") by construction — verified this step, not newly
implemented.

## P2-W1, P2-W3: not addressed in this step

Expanding the calibrated policy's held-out sample size (P2-W1) and a
dedicated retry-economics sensitivity sweep (P2-W3, varying
`COST_RETRY_PER_EXTRA_SAMPLE`/`BENEFIT_CORRECT`/`COST_WRONG_ANSWER` before
seeing results) were not performed in this step — they concern the
arithmetic agent's already-functioning calibrated decision policy
(`agent_calibration.py`), not the sentiment discrimination gap this step
was scoped to investigate first per the master register's stated
priority. Logged as **NOT YET STARTED**, not silently skipped, and are
natural candidates for a follow-up remediation pass.
