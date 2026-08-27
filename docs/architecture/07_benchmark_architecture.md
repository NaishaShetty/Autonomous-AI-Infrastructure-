# Benchmark Architecture

```mermaid
flowchart TD
    DS[("Phase 5.2 canonical dataset<br/>3,106 records")] --> RUNNER["src/benchmark/runner.py<br/>(python -m src.benchmark.runner)"]
    RUNNER --> TRACKS

    subgraph TRACKS["8 tracks -> 16 tasks"]
        T1["uncertainty<br/>UNC-ARITH, UNC-SENT, UNC-QA"]
        T2["abstention<br/>ABST-ARITH, ABST-SENT, ABST-QA"]
        T3["failure_prediction<br/>PRED-RESOURCE-UNAVAILABLE, PRED-OOM,<br/>PRED-CPU, PRED-FLAKY"]
        T4["diagnosis<br/>DIAG-EVAL"]
        T5["recovery<br/>REC-EVAL"]
        T6["memory<br/>MEM-EVAL"]
        T7["generalization<br/>GEN-RANKING-CONTRACT,<br/>GEN-OPERATING-POINT-CONTRACT"]
        T8["end_to_end<br/>E2E-EVAL"]
    end

    TRACKS --> METRICS["33 metrics<br/>(AUROC/AUPRC/Brier/ECE/risk-coverage/Wilson CI,<br/>src/benchmark/metrics.py)"]
    TRACKS --> BASE["10 baselines<br/>(BASE-ALWAYS-ABSTAIN/ANSWER, BASE-GENERIC-POLICY,<br/>BASE-CALIBRATED-MECHANISM-AWARE, CTRL-RANDOM-POLICY,<br/>BASE-RANDOM, + 4 more)"]
    TRACKS --> ABL["5 ablations<br/>(2 computable, 3 AGGREGATE_REFERENCE_EVIDENCE only)"]
    TRACKS --> LEAK["12 leakage rules L1-L12<br/>(3 mechanically enforced every run)"]

    METRICS --> MATRIX["Capability matrix (never a single score)<br/>0 VALIDATED / 6 PARTIALLY_VALIDATED /<br/>3 UNDERPOWERED / 0 NOT_VALIDATED / 7 NOT_EVALUABLE"]
    BASE --> MATRIX
    ABL --> MATRIX
    LEAK --> MATRIX

    MATRIX --> RELEASE["Phase 5.6 release package<br/>(release/benchmark/, MIT license)"]
    RELEASE --> HF["Hugging Face:<br/>huggingface.co/datasets/naishashetty/<br/>autonomous-ai-infrastructure-benchmark"]
```

The benchmark deliberately has **no aggregate "overall score"** — the
capability matrix (see `BENCHMARK_CARD.md` and `README.md`) is the
intended unit of reporting, read left to right, status column and all.
