import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
exp = root / 'experiments/results/v1_1/reliability_model/gradient_boosting_same_features_v1'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
summary = exp / 'summary.json'
manifest_path = exp / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest['summary_sha256'] = sha(summary)
manifest['report_sha256'] = sha(exp / 'report.md')
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
files = [exp / n for n in ('protocol.json','manifest.json','results.json','summary.json','report.md')]
hashes = {p.name: sha(p) for p in files}
(exp / 'finalized.json').write_text(json.dumps({'immutable': True, 'files': hashes}, indent=2, sort_keys=True) + '\n')
(exp / '.finalized').write_text(json.dumps(hashes, sort_keys=True) + '\n')
print(json.dumps(hashes, indent=2, sort_keys=True))
