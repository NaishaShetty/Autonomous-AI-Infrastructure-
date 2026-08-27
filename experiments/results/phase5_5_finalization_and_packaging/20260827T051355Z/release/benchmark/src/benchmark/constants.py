"""Frozen versions, paths, and hashes for the Phase 5.4 implementation.

These values are copied from the frozen Phase 5.2 / 5.3 artifacts. Changing
them would be a specification change, not an implementation convenience.
"""
from __future__ import annotations

from pathlib import Path

IMPLEMENTATION_VERSION = "phase5.4-implementation-v1.0.0"
BENCHMARK_VERSION = "phase5.3-benchmark-v1.0.0"
DATASET_VERSION = "phase5.2-dataset-v1.0.0"
SCHEMA_VERSION = "phase5.1-schema-v1.0.0"
PROTOCOL_VERSION = "phase5.3-protocol-v1.0.0"
METRIC_VERSION = "phase5.3-metrics-v1.0.0"
BASELINE_VERSION = "phase5.3-baselines-v1.0.0"

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DATASET_DIR = (
    REPO_ROOT / "experiments" / "results" / "phase5_dataset_construction" / "20260826T054422Z"
)
CANONICAL_SPEC_DIR = (
    REPO_ROOT / "experiments" / "results" / "phase5_benchmark_specification" / "20260826T055915Z"
)
PHASE51_SCHEMA_PATH = (
    REPO_ROOT
    / "experiments"
    / "results"
    / "phase5_dataset_specification"
    / "20260826T053011Z"
    / "PHASE5_1_SCHEMA.json"
)

# SHA-256 of dataset/all_records.jsonl from the frozen Phase 5.2 manifest.
EXPECTED_ALL_RECORDS_SHA256 = (
    "4f6994447cf28cb7f78948727e177e21cb6688ada85557613723151b66064b83"
)
EXPECTED_TOTAL_RECORDS = 3106
EXPECTED_EPISODES = 3106
EXPECTED_WORKLOADS = 3104
EXPECTED_ENVIRONMENTS = 1
EXPECTED_SPLIT_COUNTS = {
    "train": 2142,
    "calibration_validation": 482,
    "test": 482,
}

BOOTSTRAP_SEED = 20260826
BOOTSTRAP_N_RESAMPLES = 1000
BOOTSTRAP_CONFIDENCE_LEVEL = 0.95
ECE_N_BINS = 10  # equal-width bins on [0, 1], documented in metrics module
USEFUL_LEAD_TIME_SECONDS = 0.010  # 10ms, fixed documented threshold
ALWAYS_FIRES_FAR_THRESHOLD = 0.99
RANDOM_BASELINE_SEED = 20260826
SHUFFLE_CONTROL_SEED = 20260827
FEATURE_PERM_SEED = 20260828
RANDOM_POLICY_SEED = 20260829

# Coverage floor used when fitting ANSWER/ABSTAIN thresholds on
# calibration_validation only. Documented procedure, never tuned on test.
ABSTENTION_MIN_COVERAGE_FOR_FIT = 0.50

FIELD_SEP = "\x1f"

ALLOWED_SPLITS = frozenset({"train", "calibration_validation", "test"})
FITTING_SPLITS = frozenset({"train", "calibration_validation"})
EVALUATION_SPLIT = "test"

CONFIDENCE_FIELD_BY_FAMILY = {
    "arithmetic_self_consistency": "agreement_rate",
    "sentiment_softmax_margin": "softmax_margin",
    "extractive_qa_span_logit": "span_logit_confidence",
}

TASK_FAMILY_BY_UNC_TASK = {
    "UNC-ARITH": "arithmetic_self_consistency",
    "UNC-SENT": "sentiment_softmax_margin",
    "UNC-QA": "extractive_qa_span_logit",
    "ABST-ARITH": "arithmetic_self_consistency",
    "ABST-SENT": "sentiment_softmax_margin",
    "ABST-QA": "extractive_qa_span_logit",
}

# Aggregate PUBLIC_METADATA from Phase 4 / post-P5, never re-derived as
# record-level scores. Values are copied from PHASE5_3_TASK_CATALOG.json
# supporting_evidence text (and MASTER_RECORD_CONTENT.md citations therein).
AGGREGATE_REFERENCE = {
    "PRED-RESOURCE-UNAVAILABLE": {
        "verdict": "STRONG_EVIDENCE",
        "grade": "A",
        "scope": "aggregate Phase 4 pre-flight mechanism; no per-episode join key in Phase 5.2",
        "record_level_status": "NOT_EVALUABLE",
    },
    "PRED-OOM": {
        "verdict": "RANKING_SIGNAL_BUT_OPERATIONALLY_INVALID",
        "auroc_aggregate": 0.780,
        "auroc_aggregate_ci_halfwidth": 0.096,
        "shuffled_auroc_aggregate": 0.625,
        "false_alarm_rate_operating_point": 1.00,
        "specificity_operating_point": 0.179,
        "grade": "C→D, final",
        "scope": "aggregate post_p5_remediation_followups; 10 PROCESS_OOM records cannot reconstruct this",
        "record_level_status": "NOT_EVALUABLE",
    },
    "PRED-CPU": {
        "verdict": "NOT_VALIDATED",
        "grade": "D",
        "pattern": "always_fires",
        "false_alarm_rate": 1.00,
        "scope": "aggregate Phase 4; dataset has n=1 PROCESS_TIMEOUT_CPU",
        "record_level_status": "NOT_EVALUABLE",
    },
    "PRED-FLAKY": {
        "verdict": "NOT_VALIDATED",
        "grade": "D",
        "pattern": "near_chance_and_or_always_fires",
        "scope": "aggregate Phase 4; no dedicated flaky label; GENERIC_FAIL n=13, NETWORK_FAILURE n=11",
        "record_level_status": "NOT_EVALUABLE",
    },
    "GEN-RANKING-CONTRACT": {
        "oom_auroc_development": 0.989,
        "oom_auroc_held_out": 0.983,
        "oom_auroc_robustness": 0.935,
        "scope": "aggregate Phase 4.9/post-P5 environment results; not per-episode canonical records",
        "record_level_status": "NOT_EVALUABLE",
    },
    "GEN-OPERATING-POINT-CONTRACT": {
        "finding": "ranking transfers; the fixed operating point does not",
        "scope": "aggregate Phase 4 OOM environment generalization; not per-episode canonical records",
        "record_level_status": "NOT_EVALUABLE",
    },
    "MEM-EVAL": {
        "finding": "Step 6 repeated-incident: memory ON retry->retry->reconfigure->recovered vs memory OFF retry x6",
        "grade": "A",
        "scope": "aggregate Step 6 experiment; canonical dataset lacks repeated-workload_id structure",
        "record_level_status": "NOT_EVALUABLE",
    },
    "ABL-RETRY-ON-OFF": {
        "finding": "disabling retry removed the whole observed improvement (causally confirmed in frozen evidence)",
        "scope": "aggregate historical ablation; not re-derivable from current per-episode records",
        "record_level_status": "NOT_EVALUABLE",
    },
    "ABL-PREDICTOR-ON-OFF": {
        "finding": "little ON/OFF difference in one sample because retry alone was already highly effective",
        "status": "CONFOUNDED / NOT_IDENTIFIABLE",
        "scope": "no documented 2x2 retry x predictor design in frozen evidence",
        "record_level_status": "NOT_EVALUABLE",
    },
}
