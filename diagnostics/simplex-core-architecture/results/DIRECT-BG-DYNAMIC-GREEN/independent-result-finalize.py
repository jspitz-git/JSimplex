"""New exclusive result-review publication from independently checked saved bytes."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';r=D/'runs/green300'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert rd(E/'independent-result-check.json')['accepted'] is True
assert {p.name for p in (r/'output').iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}
assert all(p.is_file() and not p.is_symlink() for p in (r/'output').iterdir())
for record in [r/'audit.json',r/'admission.json']:
 j=rd(record)
 assert all(sha(n)==h for n,h in j['sha256'].items())
 if 'evidence_sha256' in j:assert all(sha(n)==h for n,h in j['evidence_sha256'].items())
files=[p for p in r.rglob('*') if p.is_file()]
evidence={str(E/n):sha(E/n) for n in ['independent-result-check.py','independent-result-check.json','independent-result-review.md','independent-result-finalize.py']}
v={'accepted':True,'findings':[],'scope':'dynamic BG GREEN result','phase':'green300','sha256':{str(p):sha(p) for p in sorted(files)},'evidence_sha256':evidence,'notes':'Exact8776passing assertions and retained7world-age warnings accepted for pinned correctness only; no performance/future-runtime qualification.'}
with (r/'result-review.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({'accepted':True,'run_files':len(files),'sha256':sha(r/'result-review.json')}))
