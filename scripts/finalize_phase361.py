import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'experiments/results/v1_1/v1_forensics/3_6_1_baseline_reconciliation'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in {'manifest.json','finalized.json','.finalized'})
m=json.loads((D/'protocol.json').read_text()); m['result_hashes']={str(p.relative_to(D)):sha(p) for p in files}; (D/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in {'finalized.json','.finalized'}); h={str(p.relative_to(D)):sha(p) for p in files}; (D/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (D/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n')
print('finalized',len(files))
