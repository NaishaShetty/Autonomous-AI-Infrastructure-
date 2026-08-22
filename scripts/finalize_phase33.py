import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/results/v1_1/temporal_robustness'
EXPERIMENTS = [
    BASE / '3_3_a_temporal_validation/phase33_a_temporal_validation_model_selection',
    BASE / '3_3_b_contextual_features',
    BASE / '3_3_c_constrained_nonlinear',
    BASE / '3_3_d_drift_aware',
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for path in EXPERIMENTS:
    manifest = json.loads((path / 'manifest.json').read_text())
    manifest['report_sha256'] = sha(path / 'report.md')
    manifest['summary_sha256'] = sha(path / 'summary.json')
    (path / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    names = ['protocol.json', 'results.json', 'summary.json', 'manifest.json', 'report.md']
    hashes = {name: sha(path / name) for name in names}
    (path / 'finalized.json').write_text(json.dumps({'immutable': True, 'files': hashes}, indent=2, sort_keys=True) + '\n')
    (path / '.finalized').write_text(json.dumps(hashes, sort_keys=True) + '\n')
print('finalized', len(EXPERIMENTS), 'experiments')
