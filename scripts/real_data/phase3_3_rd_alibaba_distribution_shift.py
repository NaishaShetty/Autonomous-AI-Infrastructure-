"""
Phase 3.3-RD -- Alibaba train/test COVARIATE distribution-shift characterization.

This script does NOT fit, tune, or re-evaluate any model. It reuses the
identical, unmodified feature frame from
scripts/real_data/phase3_1_rd_alibaba_evaluate.py (same allowed pre-outcome
fields, same leakage exclusions) and the already-frozen temporal split
(data/audit/alibaba_gpu2020/splits_temporal.json), and computes simple
descriptive statistics of each FEATURE's distribution in train (Q1-Q3) vs.
test (Q4). No test labels are used to select, transform, or weight any
feature -- the outcome label is reported only as a single already-disclosed
population statistic (train/test failure rate), identical to the number
already published in Phase 3.1-RD/3.2-RD. This is purely a description of
the environment the frozen temporal generalization experiment operates in,
not a new evaluation.
"""
import json
import numpy as np
import pandas as pd

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "phase3_1_rd_alibaba_evaluate", "scripts/real_data/phase3_1_rd_alibaba_evaluate.py"
)
p1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p1)

NUMERIC_COLS = p1.NUMERIC_COLS
CATEGORICAL_COLS = p1.CATEGORICAL_COLS


def describe_numeric(train_s, test_s):
    return {
        "train_mean": float(train_s.mean()), "test_mean": float(test_s.mean()),
        "train_median": float(train_s.median()), "test_median": float(test_s.median()),
        "train_std": float(train_s.std()), "test_std": float(test_s.std()),
        "train_missing_rate": float(train_s.isna().mean()), "test_missing_rate": float(test_s.isna().mean()),
    }


def main():
    df = p1.build_feature_matrix()
    p1.assert_no_excluded_columns(df)

    with open("data/audit/alibaba_gpu2020/splits_temporal.json") as f:
        ts = json.load(f)
    train_df = df[df["job_name"].isin(set(ts["train"]))]
    test_df = df[df["job_name"].isin(set(ts["test"]))]

    numeric_shift = {}
    for col in NUMERIC_COLS:
        numeric_shift[col] = describe_numeric(train_df[col], test_df[col])

    categorical_shift = {}
    for col in CATEGORICAL_COLS:
        train_props = (train_df[col].fillna("UNKNOWN").value_counts(normalize=True)).to_dict()
        test_props = (test_df[col].fillna("UNKNOWN").value_counts(normalize=True)).to_dict()
        categories = sorted(set(train_props) | set(test_props))
        categorical_shift[col] = {
            cat: {"train_proportion": float(train_props.get(cat, 0.0)), "test_proportion": float(test_props.get(cat, 0.0))}
            for cat in categories
        }

    out = {
        "phase": "3.3-RD",
        "protocol_version": "1.0",
        "dataset": "alibaba_gpu2020",
        "analysis": "train(Q1-Q3)_vs_test(Q4)_covariate_distribution_shift_descriptive_only",
        "_note": "Descriptive only -- no model fit, no test-label-driven feature selection or transformation. n_train and n_test match the frozen temporal split exactly.",
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "already_disclosed_label_shift_reference": {
            "train_failed_rate": float(train_df["label"].mean()),
            "test_failed_rate": float(test_df["label"].mean()),
            "source": "identical to Phase 3.1-RD sec 11 / Phase 3.2-RD sec 11 -- not recomputed differently here",
        },
        "numeric_feature_shift": numeric_shift,
        "categorical_feature_shift": categorical_shift,
    }
    out_path = "experiments/results/phase3_real_data/phase3_3/alibaba_distribution_shift.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
