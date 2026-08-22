import hashlib, json
from pathlib import Path
import joblib

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/results/v1_1/calibration_abstention'
EXPS=['3_4_a_calibration','3_4_b_uncertainty','3_4_c_abstention','3_4_d_combined']
REQUIRED=['protocol.json','manifest.json','results.json','summary.json','report.md','finalized.json','.finalized']

def test_phase34_has_four_isolated_experiments():
    assert [p.name for p in sorted(BASE.iterdir()) if p.is_dir()]==EXPS

def test_each_experiment_has_required_contract_and_decision():
    for name in EXPS:
        d=BASE/name
        for f in REQUIRED: assert (d/f).exists(), (name,f)
        protocol=json.loads((d/'protocol.json').read_text()); result=json.loads((d/'results.json').read_text()); summary=json.loads((d/'summary.json').read_text())
        assert protocol['experiment_id']
        assert protocol['hypothesis'] and protocol['intervention']
        assert result['decision'] in {'ACCEPT','REJECT','HOLD','INTERESTING FINDING'}
        assert summary['decision']==result['decision']
        assert 'random_stratified' in result and 'temporal_future' in result

def test_phase34_hashes_are_valid_and_complete():
    for name in EXPS:
        d=BASE/name; hashes=json.loads((d/'.finalized').read_text())
        for rel,digest in hashes.items():
            assert hashlib.sha256((d/rel).read_bytes()).hexdigest()==digest, (name,rel)

def test_no_future_test_tuning_claimed():
    for name in EXPS:
        p=json.loads((BASE/name/'manifest.json').read_text())
        assert 'train/validation only' in p['selection_boundary']
        assert 'future temporal test locked' in p['selection_boundary']

def test_serialized_phase34_artifacts_reload():
    paths=list((BASE/'3_4_a_calibration/artifacts').glob('*.joblib'))+list((BASE/'3_4_b_uncertainty/artifacts').glob('*.joblib'))
    assert paths
    for p in paths: assert joblib.load(p) is not None

def test_decisions_respect_operational_coverage_gate():
    c=json.loads((BASE/'3_4_c_abstention/results.json').read_text())
    d=json.loads((BASE/'3_4_d_combined/results.json').read_text())
    assert c['decision']=='REJECT' and d['decision']=='REJECT'
    assert c['temporal_future']['candidate']['coverage']>0.5
    assert d['temporal_future']['combined_selective']['coverage']>0.5
    assert d['temporal_future']['combined_selective']['selective_risk']>0.1
