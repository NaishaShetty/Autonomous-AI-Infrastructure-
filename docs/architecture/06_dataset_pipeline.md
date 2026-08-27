# Dataset Construction / Provenance Pipeline

```mermaid
flowchart LR
    subgraph P4["Phase 4 (frozen) -- raw evidence"]
        E1["Agent-task evaluation runs<br/>(arithmetic self-consistency,<br/>sentiment, extractive QA)"]
        E2["Controlled-runtime failure/recovery episodes<br/>(retry/restart against subprocess runtime)"]
        E3["Prediction / diagnosis / recovery /<br/>generalization aggregate results"]
    end

    E1 --> SPEC["Phase 5.1 -- Schema + policy specification<br/>(docs/PHASE5_1_SCHEMA.json,<br/>SPLIT_POLICY, LEAKAGE_POLICY,<br/>PROVENANCE_CONTRACT, PUBLICATION_BOUNDARY)"]
    E2 --> SPEC
    E3 -.aggregate-reference only, not record-level.-> SPEC

    SPEC --> CONSTRUCT["Phase 5.2 -- Dataset construction<br/>(src/phase5/build_dataset.py,<br/>sources.py, failure_mapping.py, record_id.py)"]
    CONSTRUCT --> RECORDS[("3,106 canonical records:<br/>3,060 agent_task + 46 controlled_runtime<br/>1 environment, split by workload_id")]
    RECORDS --> SPLITS["train=2,142 / calibration=482 / test=482<br/>0 workload_id crosses a split boundary"]
    RECORDS --> PROV["Provenance: identity.source_artifact_version<br/>traces every record to a named Phase 4 source"]
    SPLITS --> RELEASE["Phase 5.6 -- Public release package<br/>(release/dataset/, CC BY 4.0)"]
    PROV --> RELEASE
    RELEASE --> HF["Hugging Face:<br/>huggingface.co/datasets/naishashetty/<br/>autonomous-ai-infrastructure-dataset"]

    classDef danger stroke-dasharray: 5 5,stroke:#b91c1c,color:inherit;
    E3:::danger
```

Aggregate-only Phase 4 evidence (dashed, red) is deliberately **not**
converted into fabricated per-record values anywhere in this pipeline —
this is enforced by the Phase 5.1 provenance contract and verified by the
Phase 5.6 release audits (`LICENSE_PROVENANCE_AUDIT.md`,
`DATASET_RELEASE_AUDIT.md`).
