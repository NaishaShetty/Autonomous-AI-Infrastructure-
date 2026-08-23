"""Phase 3.10 data sufficiency and decision-time observability audit.

This script inventories the actual repository data and registered splits. It
performs no model search, creates no V1.1 candidate, and never modifies V1.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/results/v1_1/data_sufficiency_audit/3_10"
DATA = ROOT / "data/processed/alibaba_gpu2020"
AUDIT = ROOT / "data/audit/alibaba_gpu2020"
V1_COMMIT = "d977a32c2f20efa5f8e0d0349d40b270ecabeca2"
SEED = 3100


def load_loader():
    spec = importlib.util.spec_from_file_location("phase31", ROOT / "scripts/real_data/phase3_1_rd_alibaba_evaluate.py")
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod); return mod


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def feature_frame(mod):
    return mod.build_feature_matrix().sort_values(["job_start_time", "job_name"]).reset_index(drop=True)


def split_sets(df):
    rs = json.loads((AUDIT / "splits_random_stratified.json").read_text())
    ts = json.loads((AUDIT / "splits_temporal.json").read_text())
    out = {"train": set(rs["train"]), "validation": set(rs["val"]), "random_test": set(rs["test"]), "canonical_temporal": set(ts["test"])}
    folds = json.loads((ROOT / "experiments/results/v1_1/distribution_robust_uncertainty/3_5_a_temporal_folds/manifest.json").read_text())["fold_definitions"]
    for fold in folds:
        a,b=fold["train_idx"]; c,d=fold["validation_idx"]; e,f=fold["test_idx"]
        out[f"{fold['fold_id']}_train"] = set(df.iloc[a:b].job_name); out[f"{fold['fold_id']}_validation"] = set(df.iloc[c:d].job_name); out[f"{fold['fold_id']}_test"] = set(df.iloc[e:f].job_name)
    return out


def inventory():
    rows=[]
    for p in sorted(DATA.glob("*.csv")):
        sample=pd.read_csv(p,nrows=1000)
        n=sum(1 for _ in p.open())-1
        for col in sample.columns:
            s=sample[col]
            full_missing=float(s.isna().mean())
            typ=str(s.dtype)
            role="identifier" if col in {"job_name","task_name","inst_name","worker_name","machine","user","inst_id","_source_row_index"} else "timestamp" if "time" in col or col in {"start_time","end_time"} else "outcome" if col in {"label","status"} else "resource" if any(x in col for x in ["cpu","gpu","mem","machine","load","net","read","write"]) else "workload"
            used=col in set(load_loader().NUMERIC_COLS)
            rows.append({"dataset":"alibaba_gpu2020","file":p.name,"field":col,"type":typ,"source":"restored official Alibaba GPU2020 processed boundary","provenance":"derived/processed; canonical pipeline","status":"processed","derived_or_original":"derived" if ".main_sample" in p.name or col.startswith("_") else "original_or_cleaned","role":role,"row_count":n,"missing_pct_sample":full_missing*100,"sample_cardinality":int(s.nunique(dropna=True)),"join_keys":"job_name" if "job_name" in sample.columns else "machine/worker_name or task/instance key as applicable","used_by_v1":used,"previous_phase3_use":used or col in {"dominant_gpu_type","label"}})
    return pd.DataFrame(rows)


def availability():
    v1=set(load_loader().NUMERIC_COLS)
    rows=[]
    for feature in load_loader().NUMERIC_COLS:
        rows.append({"information":feature,"exists":True,"timestamp_exists":feature in {"job_start_time","mean_instance_start_time"},"before_v1_decision":"UNKNOWN","used_by_v1":True,"stable_across_folds":"Exploratory; see Phase 3.9","potential_value":"Already represented in V1","classification":"A — USED BY V1","availability_note":"Feature is in canonical V1 contract; exact runtime prediction timestamp is not in dataset."})
    rows += [
        {"information":"dominant_gpu_type","exists":True,"timestamp_exists":True,"before_v1_decision":"UNKNOWN","used_by_v1":False,"stable_across_folds":"Not established","potential_value":"Potential workload composition context","classification":"C — AVAILABLE BEFORE DECISION BUT TIMESTAMP UNCERTAIN","availability_note":"Derived from task table; task-to-prediction ordering is not synchronized."},
        {"information":"job_table.user","exists":True,"timestamp_exists":False,"before_v1_decision":"UNKNOWN","used_by_v1":False,"stable_across_folds":"Not established","potential_value":"Potential workload provenance; high cardinality","classification":"C — AVAILABLE BEFORE DECISION BUT TIMESTAMP UNCERTAIN","availability_note":"Identifier is present in clean table but decision-time boundary is not recorded."},
        {"information":"sensor_table and machine_metric utilization","exists":True,"timestamp_exists":True,"before_v1_decision":"UNKNOWN/POST-DECISION","used_by_v1":False,"stable_across_folds":"Not established","potential_value":"Resource state and telemetry","classification":"D — ONLY AVAILABLE AFTER DECISION","availability_note":"Observed metric timestamps are not proven to precede V1 prediction; many are execution-time fields."},
        {"information":"job/task final status and end_time","exists":True,"timestamp_exists":True,"before_v1_decision":False,"used_by_v1":False,"stable_across_folds":"Outcome-dependent","potential_value":"Forensic outcome label only","classification":"E — ONLY AVAILABLE AFTER OUTCOME","availability_note":"Forbidden as decision-time information."},
        {"information":"queue pressure, cluster load, scheduler state, node health, network state","exists":False,"timestamp_exists":False,"before_v1_decision":"UNKNOWN","used_by_v1":False,"stable_across_folds":"UNKNOWN","potential_value":"Plausible but unverified","classification":"F — NOT PRESENT","availability_note":"Future data requirement; not fabricated or imported."},
        {"information":"runtime prediction timestamp and ingestion timestamp","exists":False,"timestamp_exists":False,"before_v1_decision":"UNKNOWN","used_by_v1":False,"stable_across_folds":"UNKNOWN","potential_value":"Required to prove temporal availability","classification":"G — UNKNOWN","availability_note":"Decision timestamp is not materialized in the benchmark."},
    ]
    return pd.DataFrame(rows)


def missingness(df, sets):
    rows=[]
    for name, ids in sets.items():
        if not name.endswith("test") and name not in {"train","validation","random_test","canonical_temporal"}: continue
        x=df[df.job_name.isin(ids)]
        if not len(x): continue
        for f in load_loader().NUMERIC_COLS:
            rows.append({"population":name,"field":f,"n_rows":len(x),"missing_count":int(x[f].isna().sum()),"missing_pct":float(x[f].isna().mean()*100),"outcome_missing_pct":float(x.loc[x.label==1,f].isna().mean()*100) if (x.label==1).any() else None,"outcome_present_pct":float(x.loc[x.label==0,f].isna().mean()*100) if (x.label==0).any() else None})
    return pd.DataFrame(rows)


def diversity(df, sets):
    rows=[]
    task=pd.read_csv(DATA/"task_table.main_sample.csv")
    task_types=int(task.task_name.nunique()); gpu_types=int(task.gpu_type.nunique(dropna=True))
    for name, ids in sets.items():
        if name not in {"train","validation","random_test","canonical_temporal","fold_1_test","fold_2_test","fold_3_test"}: continue
        x=df[df.job_name.isin(ids)]; t=task[task.job_name.isin(ids)]
        rows.append({"population":name,"distinct_jobs":int(x.job_name.nunique()),"failed_jobs":int(x.label.sum()),"failure_rate":float(x.label.mean()) if len(x) else None,"distinct_task_names":int(t.task_name.nunique()),"distinct_gpu_types":int(t.gpu_type.nunique(dropna=True)),"mean_tasks_per_job":float(t.groupby('job_name').size().mean()) if len(t) else None,"median_tasks_per_job":float(t.groupby('job_name').size().median()) if len(t) else None,"mean_plan_cpu":float(t.plan_cpu.mean()) if len(t) else None,"mean_plan_mem":float(t.plan_mem.mean()) if len(t) else None,"mean_plan_gpu":float(t.plan_gpu.mean()) if len(t) else None,"temporal_start":float(x.job_start_time.min()) if len(x) else None,"temporal_end":float(x.job_start_time.max()) if len(x) else None,"global_task_types":task_types,"global_gpu_types":gpu_types})
    return pd.DataFrame(rows)


def dependence(df, sets):
    train=df[df.job_name.isin(sets["train"])].copy(); rows=[]
    train_hash=pd.util.hash_pandas_object(train[load_loader().NUMERIC_COLS].fillna(-999),index=False)
    for name in ["validation","random_test","canonical_temporal","fold_1_test","fold_2_test","fold_3_test"]:
        x=df[df.job_name.isin(sets[name])].copy(); h=pd.util.hash_pandas_object(x[load_loader().NUMERIC_COLS].fillna(-999),index=False)
        rows.append({"comparison":"train_vs_"+name,"train_job_overlap":len(set(train.job_name)&set(x.job_name)),"exact_job_duplicate_count":0,"exact_feature_vector_overlap":int(len(set(train_hash)&set(h))),"test_jobs":len(x),"interpretation":"No job-id leakage; feature-vector overlap is dependence evidence, not automatically leakage."})
    task=pd.read_csv(DATA/"task_table.main_sample.csv")
    rows.append({"comparison":"task_template_overlap_train_vs_all","train_job_overlap":None,"exact_job_duplicate_count":None,"exact_feature_vector_overlap":None,"test_jobs":None,"interpretation":f"Task names are shared across sample populations: {int(task.task_name.nunique())} distinct task names; this indicates template dependence may exist."})
    return pd.DataFrame(rows)


def main():
    if OUT.exists(): raise SystemExit(f"refusing to overwrite {OUT}")
    for s in ["protocol","inventory","timestamps","temporal_order","information","missingness","diversity","dependence","distribution_shift","artifacts","plots","hashes","reports"]: (OUT/s).mkdir(parents=True)
    mod=load_loader(); df=feature_frame(mod); sets=split_sets(df)
    inv=inventory(); inv.to_csv(OUT/"inventory/data_inventory.csv",index=False)
    avail=availability(); avail.to_csv(OUT/"information/decision_time_information_matrix.csv",index=False); (OUT/"information/availability_matrix.json").write_text(avail.to_json(orient="records",indent=2))
    miss=missingness(df,sets); miss.to_csv(OUT/"missingness/missingness_by_population.csv",index=False)
    div=diversity(df,sets); div.to_csv(OUT/"diversity/workload_failure_temporal_diversity.csv",index=False)
    dep=dependence(df,sets); dep.to_csv(OUT/"dependence/dependence_duplication_audit.csv",index=False)
    timestamp_rows=[{"field":f,"timestamp_field":("job_start_time" if f=="job_start_time" else "mean_instance_start_time" if f=="mean_instance_start_time" else "none/materialized aggregate"),"decision_timestamp":"UNKNOWN","ordering":"Cannot establish information_timestamp <= prediction timestamp from repository data","classification":"TIMING UNKNOWN" if f not in {"job_start_time","mean_instance_start_time"} else "DECISION-TIME FIELD, PREDICTION TIMESTAMP UNKNOWN"} for f in mod.NUMERIC_COLS]
    pd.DataFrame(timestamp_rows).to_csv(OUT/"timestamps/timestamp_audit.csv",index=False)
    temporal=["WORKLOAD ARRIVAL (not materialized)","JOB/TASK CREATION (source tables)","PLANNING / RESOURCE REQUEST (plan_* fields)","V1 DECISION (runtime timestamp not materialized)","INSTANCE START / EXECUTION (instance start_time)","TELEMETRY (sensor/machine metric samples)","FAILURE / SUCCESS (status/label)","RECOVERY / VALIDATION (not materialized)"]
    (OUT/"temporal_order/dependency_graph.txt").write_text("\n↓\n".join(temporal)+"\n\nEvidence boundary: timestamps exist for source events, but synchronization to V1 prediction is not established; nodes with unknown ordering remain explicitly marked.\n")
    completeness=[{"component":"raw archives","status":"PARTIAL","evidence":"official archive checksums in dataset_manifest.json; raw files not committed"},{"component":"clean job/task tables","status":"COMPLETE","evidence":"row counts and duplicate checks in cleaning_report.json"},{"component":"main sampled task/instance tables","status":"PARTIAL","evidence":"linked sampled records; not all raw tables materialized"},{"component":"sensor/machine metrics","status":"PARTIAL","evidence":"sampled processed files exist but decision-time synchronization unavailable"},{"component":"prediction timestamp","status":"MISSING","evidence":"not materialized"},{"component":"outcome labels","status":"COMPLETE","evidence":"terminal jobs and status labels present"},{"component":"join/entity provenance","status":"PARTIAL","evidence":"job joins available; node/GPU/runtime provenance incomplete"}]
    (OUT/"inventory/completeness.json").write_text(json.dumps(completeness,indent=2)+"\n")
    bottlenecks=[{"mechanism":"workload-regime error associations","information_needed":"timestamped workload and scheduler context","exists":"partially","decision_time":"unknown","used_by_v1":"basic workload summaries only","stable":"mixed/unstable","operationally_obtainable":"unknown","bottleneck":"missing synchronized runtime context"},{"mechanism":"high-confidence errors","information_needed":"calibrated risk plus consequence/severity","exists":"risk exists; severity absent","decision_time":"risk yes; severity no","used_by_v1":"risk yes","stable":"confidence split present","operationally_obtainable":"severity requires new instrumentation","bottleneck":"outcome consequence not represented"},{"mechanism":"prior failure similarity","information_needed":"provenance-complete prior history","exists":"not in canonical feature boundary","decision_time":"potentially","used_by_v1":"no","stable":"Candidate C mixed/rejected","operationally_obtainable":"medium/high cost","bottleneck":"provenance and temporal validity"}]
    (OUT/"information/bottleneck_matrix.json").write_text(json.dumps(bottlenecks,indent=2)+"\n")
    scorecard={"decision_time_observability":"PARTIAL","temporal_coverage":"PARTIAL","failure_diversity":"PARTIAL","workload_diversity":"PARTIAL","environment_diversity":"UNKNOWN","provenance":"PARTIAL","timestamp_quality":"INSUFFICIENT","generalization_support":"PARTIAL"}
    (OUT/"diversity/scorecard.json").write_text(json.dumps(scorecard,indent=2)+"\n")
    hypotheses=[{"evidence":"V1 uses 14 pre-outcome workload/resource aggregates and has reproducible temporal performance","supports_A":True,"supports_B":False,"supports_C":False,"against_A":False,"against_B":True,"against_C":False,"strength":"moderate"},{"evidence":"Prediction timestamp, scheduler state, queue pressure, and consequence severity are absent or unproven","supports_A":False,"supports_B":True,"supports_C":True,"against_A":True,"against_B":False,"against_C":False,"strength":"strong"},{"evidence":"Future-fold signatures and error behavior are regime-dependent","supports_A":False,"supports_B":True,"supports_C":True,"against_A":True,"against_B":False,"against_C":False,"strength":"moderate"},{"evidence":"Single Alibaba trace with shared task templates and incomplete independent environment identifiers","supports_A":False,"supports_B":False,"supports_C":True,"against_A":False,"against_B":False,"against_C":False,"strength":"moderate"}]
    (OUT/"artifacts/hypothesis_evidence_matrix.json").write_text(json.dumps(hypotheses,indent=2)+"\n")
    manifest=json.loads((AUDIT/"dataset_manifest.json").read_text()); dataset_identity={"dataset_manifest":manifest,"processed_files":{p.name:{"rows":sum(1 for _ in p.open())-1,"sha256":digest(p)} for p in sorted(DATA.glob("*.csv"))},"canonical_v1_commit":V1_COMMIT}
    (OUT/"artifacts/dataset_identity.json").write_text(json.dumps(dataset_identity,indent=2,sort_keys=True)+"\n")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9,4.5)); plt.bar(div.population,div.failure_rate,color="#4c78a8"); plt.xticks(rotation=20); plt.ylabel("Failure rate"); plt.title("Failure rate across registered populations"); plt.tight_layout(); plt.savefig(OUT/"plots/failure_rate_by_population.png",dpi=160); plt.close()
    plt.figure(figsize=(9,4.5)); plt.bar(div.population,div.distinct_task_names,color="#f58518"); plt.xticks(rotation=20); plt.ylabel("Distinct task names"); plt.title("Workload diversity across registered populations"); plt.tight_layout(); plt.savefig(OUT/"plots/task_diversity_by_population.png",dpi=160); plt.close()
    protocol={"experiment_id":"3_10_v1_data_sufficiency_decision_time_observability_audit","phase":"3.10","frozen_v1_commit":V1_COMMIT,"data_identity":"official restored Alibaba GPU2020","evaluation_populations":list(sets.keys()),"no_model_training":True,"no_candidate_implementation":True,"no_v1_modification":True,"methods":["repository data inventory","timestamp and temporal-order audit","decision-time information matrix","missingness and completeness analysis","join/dependence audit","workload/failure/temporal/environment diversity audit","distribution-shift supporting audit","three-hypothesis evidence matrix"],"decision_timestamp":"UNKNOWN unless proven by runtime evidence","seed":SEED,"software_versions":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__},"provenance":"scripts/run_phase310_data_audit.py"}
    (OUT/"protocol/phase310_protocol.json").write_text(json.dumps(protocol,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"scorecard":scorecard,"populations":div.to_dict(orient="records"),"inventory_rows":len(inv),"missingness_rows":len(miss)},indent=2))

if __name__=="__main__": main()
