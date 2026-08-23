"""Phase 3.9 V1 decision-failure and information-gap forensics.

This is an isolated analysis around frozen V1. It does not train an error
classifier or alter the V1 predictor. All categories and signatures are
computed deterministically from the registered evaluation populations.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/v1_1/failure_forensics/3_9"
SEED = 3900
p = importlib.util.spec_from_file_location("phase31", ROOT / "scripts/real_data/phase3_1_rd_alibaba_evaluate.py")
m = importlib.util.module_from_spec(p)
assert p and p.loader
p.loader.exec_module(m)
FEATURES = m.NUMERIC_COLS


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ece(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    value = 0.0
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10 if i < 9 else 1.0000001
        mask = (pred >= lo) & (pred < hi)
        if mask.any(): value += mask.sum() * abs(float(pred[mask].mean()) - float(y[mask].mean()))
    return float(value / len(y))


def metrics(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    return {"auroc": float(roc_auc_score(y, pred)), "auprc": float(average_precision_score(y, pred)), "ece": ece(y, pred), "count": int(len(y)), "prevalence": float(y.mean())}


def v1_pipeline():
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))])


def populations(df):
    rs = json.loads((ROOT / "data/audit/alibaba_gpu2020/splits_random_stratified.json").read_text())
    ts = json.loads((ROOT / "data/audit/alibaba_gpu2020/splits_temporal.json").read_text())
    out = [("random_stratified", set(rs["train"]), set(rs["val"]), set(rs["test"])), ("canonical_temporal", set(ts["train"]), set(ts["val"]), set(ts["test"]))]
    folds = json.loads((ROOT / "experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json").read_text())["fold_definitions"]
    for fold in folds:
        a, b = fold["train_idx"]; c, d = fold["validation_idx"]; e, f = fold["test_idx"]
        out.append((fold["fold_id"], set(df.iloc[a:b].job_name), set(df.iloc[c:d].job_name), set(df.iloc[e:f].job_name)))
    return out


def classify(test, pred, population):
    y = test.label.to_numpy(dtype=int)
    predicted = (pred >= 0.5).astype(int)
    correct = predicted == y
    uncertainty = 1 - np.abs(2 * pred - 1)
    high = uncertainty <= 0.50
    primary = np.where(correct, "correct", np.where(high, "high_confidence_error", "low_confidence_error"))
    secondary = []
    for i in range(len(test)):
        tags = ["false_positive" if predicted[i] == 1 and y[i] == 0 else "false_negative" if predicted[i] == 0 and y[i] == 1 else "correct"]
        if high[i]: tags.append("high_confidence")
        else: tags.append("low_confidence")
        if population != "random_stratified": tags.append("temporal_regime")
        if test.iloc[i][FEATURES].isna().any(): tags.append("feature_missingness")
        secondary.append(";".join(tags))
    out = test[["job_name", "label", *FEATURES]].copy()
    out.insert(1, "population", population)
    out["predicted_label"] = predicted
    out["risk_score"] = pred
    out["calibrated_risk"] = pred
    out["uncertainty"] = uncertainty
    out["correct"] = correct
    out["primary_failure_category"] = primary
    out["secondary_tags"] = secondary
    out["decision_time_availability"] = "DECISION-TIME"
    return out, metrics(y, pred)


def univariate(cases):
    rows = []
    for population, cases_df in cases.items():
        error = ~cases_df.correct.astype(bool)
        for feature in FEATURES:
            a = cases_df.loc[error, feature].dropna().to_numpy(dtype=float)
            b = cases_df.loc[~error, feature].dropna().to_numpy(dtype=float)
            allv = cases_df[feature].dropna().to_numpy(dtype=float)
            if len(a) and len(b):
                pooled = np.sqrt((np.var(a) + np.var(b)) / 2) or 1.0
                smd = float((np.mean(a) - np.mean(b)) / pooled)
                ks = float(ks_2samp(a, b).statistic)
                try: ua = float(roc_auc_score(error.loc[cases_df[feature].notna()], cases_df.loc[cases_df[feature].notna(), feature]))
                except ValueError: ua = None
            else: smd = ks = ua = None
            rows.append({"population": population, "feature": feature, "n_error": int(error.sum()), "n_correct": int((~error).sum()), "error_missing_rate": float(cases_df.loc[error, feature].isna().mean()), "correct_missing_rate": float(cases_df.loc[~error, feature].isna().mean()), "standardized_mean_difference": smd, "ks_statistic": ks, "univariate_error_auroc": ua, "feature_min": float(allv.min()) if len(allv) else None, "feature_max": float(allv.max()) if len(allv) else None})
    return pd.DataFrame(rows)


def main():
    if OUT.exists(): raise SystemExit(f"refusing to overwrite {OUT}")
    for sub in ("protocol", "failure_taxonomy/failure_cases", "failure_taxonomy/reports", "information_gap/reports", "error_signatures/univariate", "error_signatures/multivariate", "error_signatures/cross_fold", "error_signatures/reports", "opportunity_map/reports", "plots", "tables", "artifacts", "hashes"):
        (OUT / sub).mkdir(parents=True)
    df = m.build_feature_matrix().sort_values(["job_start_time", "job_name"]).reset_index(drop=True)
    cases, pop_metrics = {}, {}
    for name, train_ids, val_ids, test_ids in populations(df):
        train, val, test = (df[df.job_name.isin(ids)].copy() for ids in (train_ids, val_ids, test_ids))
        model = v1_pipeline(); model.fit(train[FEATURES], train.label)
        raw_val, raw_test = model.predict_proba(val[FEATURES])[:, 1], model.predict_proba(test[FEATURES])[:, 1]
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(raw_val, val.label)
        pred = calibrator.predict(raw_test)
        case_df, met = classify(test, pred, name)
        cases[name] = case_df
        pop_metrics[name] = {"metrics": met, "n_train": len(train), "n_validation": len(val), "n_test": len(test), "train_start": float(train.job_start_time.min()), "train_end": float(train.job_start_time.max()), "test_start": float(test.job_start_time.min()), "test_end": float(test.job_start_time.max())}
        case_df.to_csv(OUT / "failure_taxonomy/failure_cases" / f"{name}.csv", index=False, float_format="%.17g")
    all_cases = pd.concat(cases.values(), ignore_index=True)
    all_cases.to_csv(OUT / "tables/case_level_forensics.csv", index=False, float_format="%.17g")
    tax_rows = []
    for category in ("high_confidence_error", "low_confidence_error"):
        mask = all_cases.primary_failure_category == category
        counts = all_cases[mask].groupby("population").size().to_dict()
        tax_rows.append({"failure_category": category, "cases": int(mask.sum()), "percent_of_failures": float(mask.sum() / max(1, (all_cases.primary_failure_category.isin(["high_confidence_error", "low_confidence_error"])).sum()) * 100), "percent_of_all_cases": float(mask.mean() * 100), "population_distribution": counts, "temporal_presence": any(k != "random_stratified" and v > 0 for k, v in counts.items()), "cross_fold_stability": "ROBUST" if all(counts.get(f"fold_{i}", 0) > 0 for i in (1,2,3)) else "REGIME-SPECIFIC", "decision_time_information": "A — observable and already used by V1", "confidence": "HIGH", "limitations": "Primary categories are mutually exclusive; secondary tags are multi-label."})
    taxonomy = {"failure_definition": "Canonical V1 threshold prediction is incorrect; threshold=0.5.", "primary_categories": tax_rows, "category_policy": "correct, high-confidence error, and low-confidence error; secondary tags are multi-label and descriptive.", "unsupported_categories": ["failure severity", "causal feature mechanism", "memory-relevant error without a validated memory label"], "case_count": int(len(all_cases))}
    (OUT / "failure_taxonomy/taxonomy.json").write_text(json.dumps(taxonomy, indent=2, sort_keys=True) + "\n")
    uni = univariate(cases); uni.to_csv(OUT / "error_signatures/univariate/univariate_signatures.csv", index=False, float_format="%.17g")
    future = uni[uni.population.isin(["canonical_temporal", "fold_1", "fold_2", "fold_3"])].copy()
    cross = []
    for feature in FEATURES:
        vals = future[future.feature == feature].set_index("population")["standardized_mean_difference"]
        vals = vals.reindex(["canonical_temporal", "fold_1", "fold_2", "fold_3"])
        av = vals.dropna().to_numpy()
        direction = "ROBUST" if len(av) == 4 and np.all(np.sign(av) == np.sign(av[0])) and np.mean(np.abs(av) >= 0.2) >= 0.5 else "UNSTABLE" if len(av) == 4 else "UNRESOLVED"
        cross.append({"feature": feature, "canonical_temporal_smd": vals.get("canonical_temporal"), "fold_1_smd": vals.get("fold_1"), "fold_2_smd": vals.get("fold_2"), "fold_3_smd": vals.get("fold_3"), "mean_abs_smd": float(np.mean(np.abs(av))) if len(av) else None, "signature_stability": direction})
    cross_df = pd.DataFrame(cross); cross_df.to_csv(OUT / "error_signatures/cross_fold/cross_fold_signatures.csv", index=False, float_format="%.17g")
    availability = [
        {"failure_category": "high/low-confidence error", "information_needed": "V1 risk and calibrated score", "availability": "DECISION-TIME", "already_used_by_v1": True, "potentially_useful": "Yes, policy interpretation", "acquisition_cost": "None", "leakage_risk": "Low", "classification": "A"},
        {"failure_category": "temporal-regime error", "information_needed": "job start time and workload/resource summary", "availability": "DECISION-TIME", "already_used_by_v1": True, "potentially_useful": "Possibly; signatures are exploratory", "acquisition_cost": "None in current contract", "leakage_risk": "Low", "classification": "A"},
        {"failure_category": "missingness-associated error", "information_needed": "feature presence at decision time", "availability": "DECISION-TIME", "already_used_by_v1": "Yes, through imputation", "potentially_useful": "Possibly", "acquisition_cost": "Low", "leakage_risk": "Low", "classification": "A"},
        {"failure_category": "prior failure similarity", "information_needed": "temporally eligible failure memory", "availability": "Potentially available", "already_used_by_v1": False, "potentially_useful": "Unproven; Candidate C rejected", "acquisition_cost": "Medium/high", "leakage_risk": "High unless prior-only", "classification": "C"},
        {"failure_category": "future telemetry or final outcome", "information_needed": "post-decision resource state/outcome", "availability": "POST-OUTCOME", "already_used_by_v1": False, "potentially_useful": "Forensic explanation only", "acquisition_cost": "Not applicable", "leakage_risk": "Prohibited", "classification": "D"},
        {"failure_category": "unmaterialized queue/machine context", "information_needed": "runtime context not in processed contract", "availability": "UNKNOWN", "already_used_by_v1": False, "potentially_useful": "Unknown", "acquisition_cost": "Unknown", "leakage_risk": "Unknown", "classification": "F"},
    ]
    (OUT / "information_gap/availability_matrix.json").write_text(json.dumps(availability, indent=2, sort_keys=True) + "\n")
    pd.DataFrame(availability).to_csv(OUT / "information_gap/information_gap_matrix.csv", index=False)
    opportunities = [
        ["uncertainty-associated errors", "High; reproduced in prior phases", "Risk/uncertainty available", "V1 uses risk but not a validated action policy", "Uncertainty interpretation", "Bounded evidence request or escalation", "Coverage/latency and policy overfit", "1"],
        ["decision-time workload regime signatures", "Medium; exploratory cross-fold analysis", "14 numeric features available", "V1 consumes them predictively", "Contextual scrutiny", "Separate diagnostic context, not blind abstention", "Regime instability", "2"],
        ["prior failure similarity", "Medium; architecture exists but Candidate C rejected", "Potentially prior-only", "V1 memory path is not a validated predictor context", "Provenance-aware memory", "New strict retrieval study", "Leakage/staleness/overhead", "3"],
        ["post-outcome errors", "High that information exists only after outcome", "Not decision-time", "Not available to prediction", "None safely at original decision", "Instrumentation for later diagnosis only", "Cannot solve original error", "4"],
    ]
    opp_df = pd.DataFrame(opportunities, columns=["failure_mechanism", "evidence_strength", "decision_time_information", "current_v1_capability", "missing_capability", "potential_intervention", "risk", "priority"]); opp_df.to_csv(OUT / "opportunity_map/opportunity_matrix.csv", index=False)
    (OUT / "tables/population_metrics.json").write_text(json.dumps(pop_metrics, indent=2, sort_keys=True) + "\n")
    (OUT / "protocol/phase39_protocol.json").write_text(json.dumps({"experiment_id":"3_9_v1_failure_information_gap_forensics","phase":"3.9","frozen_v1_commit":"d977a32c2f20efa5f8e0d0349d40b270ecabeca2","data_identity":"official restored Alibaba GPU2020","feature_contract":FEATURES,"evaluation_populations":["random_stratified","canonical_temporal","fold_1","fold_2","fold_3"],"failure_definition":"incorrect threshold prediction at 0.5","uncertainty_definition":"1 - abs(2*risk - 1)","high_confidence_rule":"uncertainty <= 0.50","analysis_methods":["case-level deterministic classification","univariate SMD/KS/AUROC","cross-fold signature comparison","availability matrix","opportunity map"],"post_outcome_policy":"post-outcome fields are forensic only, never decision-time inputs","seed":SEED,"software_versions":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__},"no_model_search":True,"no_candidate_implementation":True}, indent=2, sort_keys=True) + "\n")
    # deterministic plot
    import matplotlib.pyplot as plt
    names=list(pop_metrics); errs=[float((~cases[n].correct).mean()) for n in names]
    plt.figure(figsize=(9,4.5)); plt.bar(names,errs,color="#4c78a8"); plt.xticks(rotation=20); plt.ylabel("V1 error rate"); plt.title("V1 forensic error rate by evaluation population"); plt.tight_layout(); plt.savefig(OUT/"plots/error_rate_by_population.png",dpi=160); plt.close()
    print(json.dumps({"populations":pop_metrics,"taxonomy":taxonomy,"cross_fold":cross,"opportunities":opportunities}, indent=2, default=str))

if __name__ == "__main__": main()
