# Uncertainty + Abstention Architecture

Three **distinct, never-merged** uncertainty mechanisms feed one shared
abstention-aware decision policy. Each mechanism has its own metric
family, its own sample-size gate, and its own status — they are not
pooled into one "uncertainty score."

```mermaid
flowchart LR
    subgraph MECH["Uncertainty mechanisms (independent, never merged)"]
        A["Arithmetic self-consistency<br/>(src/phase4/uncertainty_eval.py)<br/>AUROC 0.955 (n=310, UNDERPOWERED: min 500)"]
        B["Sentiment softmax-margin<br/>(src/phase4/classification_task.py)<br/>AUROC 0.439 -- near-chance (n=113, UNDERPOWERED: min 300)"]
        C["QA span-logit margin<br/>(src/phase4/qa_task.py)<br/>AUROC 0.938 (n=49, UNDERPOWERED: min 300)"]
    end

    A --> CAL["Per-family calibration<br/>(temperature scaling)<br/>sentiment ECE 0.089 -> 0.023 (ECE fixed, AUROC NOT fixed)"]
    B --> CAL
    C --> CAL

    CAL --> POL["AbstentionAwareDecisionPolicy<br/>(src/phase4/decision.py, reuses<br/>src.decision.policy.DecisionPolicy)"]:::partial
    POL --> OUT{"ANSWER / ABSTAIN"}
    OUT -->|ABSTAIN| ESC["Escalate / defer to diagnosis"]
    OUT -->|ANSWER| CONT["Continue to diagnosis/recovery"]

    classDef partial stroke-dasharray: 5 5,stroke:#b45309,color:inherit;
```

## Why they are never merged

- Each family has a genuinely different discrimination ceiling: sentiment
  is near-chance (0.439) even after calibration fixed its ECE, because
  temperature scaling corrects *calibration* (probabilities matching
  observed frequencies), not *discrimination* (AUROC). Averaging it with
  arithmetic's 0.955 would hide a real negative finding.
- All three are `UNDERPOWERED`, not `VALIDATED` or `NOT_VALIDATED` — the
  frozen minimum-sample gates (500 / 300 / 300) were not met in the
  Phase 5.2 test split (310 / 113 / 49). The point estimates are real
  measurements, not claims of statistical significance.
- The benchmark's `ABST-ARITH` / `ABST-SENT` / `ABST-QA` tasks are
  `PARTIALLY_VALIDATED` and explicitly flagged
  `SIMULATED_POLICY_EVALUATION`: no realized ABSTAIN/RETRY-decision
  episode exists in the ingested raw sources, so selective-risk numbers
  describe a simulated policy applied post hoc to labeled records, not an
  agent's actual historical abstention behavior.
