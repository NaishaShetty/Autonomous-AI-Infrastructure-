# Step 5 Protocol — P1-W1 Sentiment Uncertainty Mechanism Comparison

Pre-registered BEFORE running any candidate mechanism on the test split.
Target weakness: sentiment error-detection AUROC (≈0.659) was
substantially weaker than arithmetic (≈0.953) and extractive QA (≈0.934)
in the pre-remediation register. This step determines whether the gap is
explained by an inappropriate uncertainty estimator (fixable locally) or
is a more intrinsic model/task limitation, per P1-W1's explicit
instruction: evaluate candidates first, defined before seeing results, and
report honestly either way.

## Candidates (fixed before running; original method is the baseline)

1. **Baseline (original P1 method):** raw softmax probability of the
   predicted class (`ClassificationResult.confidence`). Preserved
   unchanged as the reference point — never modified to chase a better
   number.
2. **Margin:** `top1_prob - top2_prob` (`ClassificationResult.margin`),
   rescaled to `[0,1]` by `min(1.0, margin / MARGIN_SCALE)` with
   `MARGIN_SCALE = 1.0` fixed before running (margin is already bounded in
   `[0,1]` for a 2-class problem, so this rescaling is the identity here —
   stated explicitly rather than silently assumed). Predictive-margin
   uncertainty is a standard classification confidence signal distinct
   from raw softmax probability.
3. **Entropy-based confidence:** `1 - ClassificationResult.entropy`
   (entropy already normalized to `[0,1]` by construction in
   `classification_task.py`). Higher entropy (more uniform distribution
   over classes) → lower confidence.
4. **Temperature-scaled confidence:** a single scalar temperature `T`,
   fit by minimizing NLL on the **calibration split only**, applied to the
   model's raw logits before softmax
   (`softmax(logits / T)`), then the predicted-class probability under the
   rescaled distribution is used as confidence. This is the one candidate
   requiring fitting, so it is the one candidate with a strict split
   requirement (see below).

**Explicitly considered and NOT included, with reason stated rather than
silently omitted:** MC-Dropout / stochastic inference and a small local
ensemble (distinct model checkpoints). Reason: this project's classifier
is a single pinned DistilBERT checkpoint (`real_model_runtime.py`,
deterministic `torch.manual_seed`-controlled inference); MC-Dropout would
require re-enabling dropout at inference time and would change the
model's own documented deterministic-inference contract, and no second
independently-trained checkpoint is available locally without training one
from scratch — a materially larger undertaking than this remediation step
scopes for. Flagged as a legitimate, unexplored follow-up, not silently
dropped.

## Data source and split

- `data/real_model_tasks/sentiment_eval.json` (660 examples,
  `phase4.6-sentiment-templated-v2`), the same corpus the pre-remediation
  0.659 number was measured on — no new data source introduced, so this
  step is a direct, comparable re-evaluation.
- **Strict split, fixed by a stable hash of `example_id` before any
  candidate was run:** ~40% calibration (used ONLY to fit the temperature
  scalar for candidate 4; never touched by candidates 1–3, which require
  no fitting), ~60% test (used to compute every candidate's AUROC/AUPRC/
  Brier/ECE — including candidate 4's, using the temperature fit on the
  calibration split only, never re-fit on test).

## Model

The existing, unmodified, pinned real DistilBERT sentiment classifier
(`real_model_runtime.py::load_classification_model`) — no retraining, no
architecture change. Every candidate is a different deterministic
post-hoc transform of the SAME model's SAME logits per example (all 4
candidates computed from one forward pass per example, never 4 separate
inference runs), so any difference between candidates is purely the
uncertainty-scoring function, never sampling noise or model drift.

## Metrics

Error-detection AUROC, AUPRC, Brier score, ECE, accuracy — via the
existing `src/phase4/uncertainty_eval.py::compute_uncertainty_metrics`
harness, unmodified.

## Stopping rule

Every candidate is evaluated exactly once on the fixed test split. The
winning candidate, if any, is whichever shows the highest test-split AUROC
— decided by this single measurement, not by iterating. If no candidate
materially improves over the baseline (defined as: AUROC improvement over
baseline exceeding 0.03, an arbitrary-but-fixed-before-seeing-results
margin chosen to be clearly larger than expected sampling noise on a
~400-example test split), the honest conclusion is that the weak sentiment
result is not explained by uncertainty-estimator choice, and is left as an
open, accepted limitation rather than iterated on further with additional
candidates invented after seeing this result.
