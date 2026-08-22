import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'experiments/results/v1_1/v1_forensics'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for d in sorted(p for p in BASE.iterdir() if p.is_dir()):
 files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'manifest.json','finalized.json','.finalized'})
 m=json.loads((d/'manifest.json').read_text()); m['artifact_hashes']={str(p.relative_to(d)):sha(p) for p in files}; (d/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 files=sorted(p for p in d.rglob('*') if p.is_file() and p.name not in {'finalized.json','.finalized'}); h={str(p.relative_to(d)):sha(p) for p in files}; (d/'finalized.json').write_text(json.dumps({'immutable':True,'files':h},indent=2,sort_keys=True)+'\n'); (d/'.finalized').write_text(json.dumps(h,sort_keys=True)+'\n')
print('finalized',len([p for p in BASE.iterdir() if p.is_dir()]))
