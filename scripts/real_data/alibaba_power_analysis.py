"""
Phase 3 real-data replication — power / sample-size analysis for the
Alibaba GPU2020 job-level failure-prediction task, BEFORE any
stratified sampling or evaluation is run.

Primary criterion: AUROC estimation precision, via the Hanley-McNeil
(1982) approximate variance of the Mann-Whitney AUC estimator. This
maps directly onto the metrics the original (synthetic) Phase 3.1
protocol used (AUROC/AUPRC/ECE/AURC), so it is the natural quantity to
power for here.

    SE(AUC)^2 = [ AUC(1-AUC) + (n_pos-1)(Q1-AUC^2) + (n_neg-1)(Q2-AUC^2) ]
                / (n_pos * n_neg)
    Q1 = AUC / (2 - AUC)
    Q2 = 2*AUC^2 / (1 + AUC)

We solve for the total n (at the observed real class balance) needed
so the 95% CI half-width on AUROC is <= a target precision, across a
sensitivity grid of plausible AUROC values — we do NOT pick a single
favorable AUROC assumption, per the brief's explicit sensitivity-
analysis requirement.

Secondary criterion: minimum n to detect a specific AUROC *difference*
between two candidates (e.g. F vs B, mirroring original Phase 3.4),
using the conservative independent-AUC approximation (paired/DeLong
would need a smaller n given positive correlation between paired
classifier scores, but we do not assume a correlation coefficient
without justification, so this is a deliberately conservative
upper-bound n).

This script performs NO sampling and touches no data files — it is a
pure numerical planning step, run and frozen BEFORE Step 8 (stratified
sampling) and long before any Phase 3.1-3.6 evaluation.
"""
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = REPO_ROOT / "data" / "audit" / "alibaba_gpu2020" / "power_analysis.json"

# Observed real class balance among terminal (Terminated+Failed) jobs,
# from the cleaned job_table (see data/audit/alibaba_gpu2020/cleaning_report.json):
# Terminated=732355, Failed=256555 -> Failed rate = 256555/988910
N_TERMINATED = 732355
N_FAILED = 256555
P_FAILED = N_FAILED / (N_TERMINATED + N_FAILED)

ALPHA = 0.05
Z_ALPHA_2 = 1.959963985  # two-sided 95% CI


def auc_se(auc, n_pos, n_neg):
    q1 = auc / (2 - auc)
    q2 = (2 * auc ** 2) / (1 + auc)
    var = (auc * (1 - auc) + (n_pos - 1) * (q1 - auc ** 2) + (n_neg - 1) * (q2 - auc ** 2)) / (n_pos * n_neg)
    return math.sqrt(max(var, 0.0))


def required_n_for_precision(auc, target_half_width, p_pos, z=Z_ALPHA_2):
    """Smallest total n (search) such that z*SE(AUC) <= target_half_width,
    at class balance p_pos (fraction positive/Failed)."""
    n = 100
    while n < 20_000_000:
        n_pos = max(2, round(n * p_pos))
        n_neg = max(2, n - n_pos)
        se = auc_se(auc, n_pos, n_neg)
        if z * se <= target_half_width:
            return n, n_pos, n_neg, se
        n = int(n * 1.05) + 1
    return None


def required_n_for_auc_difference(auc, min_diff, p_pos, power=0.8, alpha=ALPHA):
    """Conservative (independent-samples) n to detect a difference of
    min_diff between two AUROC values via a two-sided z-test comparing
    two independent AUC estimates, each with the Hanley-McNeil SE.
    This over-estimates required n relative to a paired/DeLong test on
    the same test set (positive correlation between paired classifier
    scores reduces variance of the difference) -- deliberately
    conservative, documented as such."""
    z_alpha = 1.959963985  # alpha=0.05 two-sided
    z_power = 0.8416212336  # power=0.80
    n = 100
    while n < 20_000_000:
        n_pos = max(2, round(n * p_pos))
        n_neg = max(2, n - n_pos)
        se_single = auc_se(auc, n_pos, n_neg)
        se_diff = math.sqrt(2) * se_single  # independent-samples upper bound
        required_diff = (z_alpha + z_power) * se_diff
        if required_diff <= min_diff:
            return n, n_pos, n_neg, se_diff, required_diff
        n = int(n * 1.05) + 1
    return None


def main():
    results = {
        "observed_class_balance": {
            "n_terminated": N_TERMINATED,
            "n_failed": N_FAILED,
            "p_failed": P_FAILED,
        },
        "alpha": ALPHA,
        "precision_analysis": [],
        "difference_detection_analysis": [],
    }

    print(f"Observed P(Failed | terminal) = {P_FAILED:.4f}")
    print()
    print("=== Sensitivity: n required for AUROC 95% CI half-width <= target ===")
    for assumed_auc in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        for target_hw in [0.05, 0.03, 0.02]:
            n, n_pos, n_neg, se = required_n_for_precision(assumed_auc, target_hw, P_FAILED)
            print(f"AUROC={assumed_auc:.2f} target_hw={target_hw:.2f} -> n={n:>8} (pos={n_pos}, neg={n_neg}, achieved_hw={Z_ALPHA_2*se:.4f})")
            results["precision_analysis"].append({
                "assumed_auc": assumed_auc, "target_half_width": target_hw,
                "required_n": n, "required_n_pos": n_pos, "required_n_neg": n_neg,
                "achieved_half_width": Z_ALPHA_2 * se,
            })

    print()
    print("=== Sensitivity: n required to detect an AUROC DIFFERENCE (power=0.80, alpha=0.05, conservative independent-samples bound) ===")
    for assumed_auc in [0.55, 0.60, 0.65, 0.70]:
        for min_diff in [0.03, 0.05, 0.08]:
            r = required_n_for_auc_difference(assumed_auc, min_diff, P_FAILED)
            if r is None:
                continue
            n, n_pos, n_neg, se_diff, req = r
            print(f"AUROC~{assumed_auc:.2f} min_detectable_diff={min_diff:.2f} -> n={n:>8} (pos={n_pos}, neg={n_neg})")
            results["difference_detection_analysis"].append({
                "assumed_auc": assumed_auc, "min_detectable_diff": min_diff,
                "required_n": n, "required_n_pos": n_pos, "required_n_neg": n_neg,
            })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWritten to {OUT_PATH}")


if __name__ == "__main__":
    main()
