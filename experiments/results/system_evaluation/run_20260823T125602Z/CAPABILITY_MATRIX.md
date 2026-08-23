# Capability Matrix

| Capability | Exists | Actually works | Tested | Quantitatively evaluated | Evidence | Limitation |
|---|---|---|---|---|---|---|
| Workload lifecycle and event persistence | Yes | Yes | Yes | Yes, N=3 | Fresh controlled subprocess runs + SQLite restart replay | One project-owned local environment |
| Resource telemetry | Partial | Partial | Yes | Partial | RSS/CPU samples where /proc is available | GPU, scheduler, queue unavailable; Windows may yield null process telemetry |
| Failure detection | Yes | Yes | Yes | Yes, N=3 / failures N=2 | Actual exit-7 and killed timeout | Rule-based classes only; engineering validation |
| Anomaly detection | Partial | Not established | Yes | No | RSS rule implementation | No legitimate anomalous-success workload demonstrated |
| Failure prediction / early warning | Partial | Not established in runtime | Partial | Historical artifact only | Runtime defaults to unconfigured assessor | No current injected artifact or predictive-horizon evaluation |
| Diagnosis | Yes | Yes for two controlled failure classes | Yes | Yes, N=2 | Fresh deterministic diagnosis records | Failure-class explanation only; causal ground truth unavailable |
| Uncertainty / abstention | Yes | Partial | Yes | Not evaluated in process runtime | Default runtime abstains when unconfigured | No paired live workload evaluation |
| Failure memory | Yes | Yes in controlled simulator | Yes | Historical simulator evidence | Existing versioned simulator studies | Not evaluated against current subprocess failures |
| Recovery execution | Simulated | Yes in simulator | Yes | Not evaluated here | SimulatedRecoveryExecutor | No real infrastructure mutation or recovery claim |
| Independent recovery validation | Simulated | Yes in simulator | Yes | Not evaluated here | SignalRecoveryValidator | Not independent external environment |
| Learning from incidents | Yes | Controlled simulator only | Yes | Historical simulator evidence | Runtime learning manager | No production continual-learning evidence |
| Reproducibility | Partial | Yes for this run | Yes | Yes | New protocol, raw log, hashes | No Docker or CI workflow |
| Engineering quality gates | Partial | Test suite dependent | Yes | Full suite recorded | pytest result in this run | No CI/CD configuration discovered |
