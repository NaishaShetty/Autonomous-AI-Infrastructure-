# Public Release Architecture

```mermaid
flowchart TD
    subgraph REPO["GitHub -- source of truth"]
        SRC["src/, tests/, docs/<br/>(this repository)"]
        EXP["experiments/results/<br/>(all phase evidence, frozen)"]
        REL["Phase 5.5/5.6 release packaging<br/>(release/dataset/, release/benchmark/)"]
    end

    SRC --> REL
    EXP --> REL

    REL -->|CC BY 4.0, self-contained,<br/>clean-room loadable, 0 repo deps| HFDATA["Hugging Face dataset repo<br/>huggingface.co/datasets/naishashetty/<br/>autonomous-ai-infrastructure-dataset"]
    REL -->|MIT, clean-room reproducible,<br/>41/41 unit tests, deterministic| HFBENCH["Hugging Face benchmark repo<br/>huggingface.co/datasets/naishashetty/<br/>autonomous-ai-infrastructure-benchmark"]
    REL -.NOT RECOMMENDED -- no single trained model<br/>artifact would responsibly stand alone.-> HFMODEL["Hugging Face model repo<br/>(NOT PUBLISHED)"]

    HFDATA -.->|referenced from| SRC
    HFBENCH -.->|referenced from| SRC

    classDef danger stroke-dasharray: 5 5,stroke:#b91c1c,color:inherit;
    HFMODEL:::danger
```

- GitHub remains the canonical source repository: all code, tests, and the
  full evidence trail under `experiments/results/`.
- Hugging Face hosts two release packages, both derived from and
  cross-linked back to this repository, never the reverse — the packages
  are self-contained (no dependency back on this repo to load or run).
- No model repository was published. The Phase 5.6 `RELEASE_DECISION.md`
  documents why: no single trained model artifact in this project (the
  `RiskPredictor` / `PredictionScopeRouter` behind the 4 `PRED-*` tasks) is
  independently validated at record level, so publishing one risks a
  reader treating an aggregate-only or explicitly `NOT_EVALUABLE`
  predictor as a usable trained model.
- This Phase 6 finalization work does **not** push anything to GitHub's
  `origin` remote and does **not** touch either Hugging Face repository —
  see `FINAL_RELEASE_CHECKLIST.md` for the explicit local-only commit/tag
  boundary.
