import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'experiments/results/v1_1/v1_forensics/3_6_1_baseline_reconciliation'
def test_reconciliation_contract_files_exist():
 for n in ['protocol.json','manifest.json','results.json','summary.json','report.md','reconciliation_matrix.json','finalized.json','.finalized']: assert (D/n).exists()
def test_canonical_and_copy_reproductions_match_declared_values():
 x=json.loads((D/'results.json').read_text()); c=x['canonical_v1']; r=x['phase36_research_copy']
 assert abs(c['random']['auroc']-.7201347191)<1e-8 and abs(c['temporal']['auroc']-.8302048638)<1e-8
 assert abs(r['random']['auroc']-.7347731374)<1e-8 and abs(r['temporal']['auroc']-.7930934239)<1e-8
def test_gradient_boosting_reproductions_match_both_historical_protocols():
 x=json.loads((D/'results.json').read_text())['gradient_boosting']; a=x['phase31_canonical_reproduction']; b=x['phase36_copy_reproduction']
 assert abs(a['random']['auroc']-.7472031587)<1e-8 and abs(a['temporal']['auroc']-.3335682021)<1e-8
 assert abs(b['random']['auroc']-.8070064106)<1e-8 and abs(b['temporal']['auroc']-.2294050932)<1e-8
def test_matrix_records_feature_and_calibration_differences():
 m=json.loads((D/'reconciliation_matrix.json').read_text()); assert m['Features'][2] in (False,'False'); assert m['Calibration'][2] in (False,'False'); assert m['AUROC implementation'][2] in (True,'True')
def test_identity_hashes_are_valid():
 h=json.loads((D/'.finalized').read_text())
 for rel,digest in h.items(): assert hashlib.sha256((D/rel).read_bytes()).hexdigest()==digest

def test_primary_classification_and_impacts_are_bounded():
 x=json.loads((D/'results.json').read_text()); assert x['primary_classification']=='EXPECTED PROTOCOL DIFFERENCE'; assert 'VALID BUT DIFFERENT PROTOCOL' in x['phase36_d_validity']; assert 'research-copy-specific' in x['phase36_c_validity']
def test_historical_paths_are_not_replaced():
 assert (ROOT/'experiments/results/v1_1/v1_forensics/3_6_d_complexity_ladder/results.json').exists(); assert (ROOT/'experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1/results.json').exists()
