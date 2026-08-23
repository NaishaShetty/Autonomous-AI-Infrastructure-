import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'experiments/results/v1_1/v1_forensics/3_6_2_matched_complexity'
def test_contract_files_exist():
 for n in ['protocol.json','manifest.json','results.json','summary.json','report.md','finalized.json','.finalized']:assert(D/n).exists()
def test_exact_numeric_feature_contract():
 p=json.loads((D/'protocol.json').read_text());assert len(p['feature_contract'])==14;assert p['categorical_features_used']==[];assert 'dominant_gpu_type' not in p['feature_contract']
def test_ladder_is_predeclared_and_ordered():
 p=json.loads((D/'protocol.json').read_text());ids=[x['id'] for x in p['ladder']];assert ids==['0_prevalence','1_v1_logistic','2_controlled_linear_C01','3_limited_interactions','4_constrained_random_forest','5_phase31_gradient_boosting'];assert p['ladder'][-1]['kind']=='gb'
def test_v1_control_reproduces_canonical():
 x=json.loads((D/'results.json').read_text())['ladder']['1_v1_logistic'];assert abs(x['random']['auroc']-.7201347191)<1e-8;assert abs(x['temporal']['auroc']-.8302048638)<1e-8
def test_gradient_boosting_reproduces_phase31():
 x=json.loads((D/'results.json').read_text())['ladder']['5_phase31_gradient_boosting'];assert abs(x['random']['auroc']-.7472031587)<1e-8;assert abs(x['temporal']['auroc']-.3335682021)<1e-8
def test_complexity_evidence_is_bounded():
 x=json.loads((D/'results.json').read_text())['ladder'];assert x['4_constrained_random_forest']['temporal']['auroc']<x['1_v1_logistic']['temporal']['auroc'];assert x['5_phase31_gradient_boosting']['temporal']['auroc']<x['1_v1_logistic']['temporal']['auroc'];assert x['3_limited_interactions']['temporal']['auroc']>x['1_v1_logistic']['temporal']['auroc']
def test_hashes_are_immutable():
 h=json.loads((D/'.finalized').read_text());
 for rel,d in h.items():assert hashlib.sha256((D/rel).read_bytes()).hexdigest()==d
def test_historical_evidence_protected():
 assert (ROOT/'experiments/results/v1_1/v1_forensics/3_6_1_baseline_reconciliation/results.json').exists();assert (ROOT/'experiments/results/v1_1/v1_forensics/3_6_d_complexity_ladder/results.json').exists()
