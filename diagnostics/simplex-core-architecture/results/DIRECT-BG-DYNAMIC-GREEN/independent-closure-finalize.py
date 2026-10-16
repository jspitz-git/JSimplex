"""Final exclusive exact closure-review record; no closure/publication action."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;run=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION/runs/green300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
assert rd(E/'independent-closure-check.json')['accepted'] is True
for record in [run/'result-review.json',E/'postcheck.json']:
 j=rd(record);assert all(sha(n)==h for n,h in j['sha256'].items())
assert not any((E/n).exists() for n in ['review.json','closure.json','publication.json'])
files=sorted([p for p in E.iterdir() if p.is_file()]+[p for p in run.rglob('*') if p.is_file()])
v={'accepted':True,'findings':[],'scope':'dynamic BG GREEN closure','sha256':{str(p):sha(p) for p in files},'notes':'Independent final review including24new checks; no close/publish, continuation edit, Julia or auditor rerun. Correctness only; performance unqualified.'}
with (E/'review.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
assert set(v['sha256'])=={str(p) for p in E.iterdir() if p.is_file() and p.name!='review.json'}|{str(p) for p in run.rglob('*') if p.is_file()}
print(json.dumps({'accepted':True,'bindings':len(files),'sha256':sha(E/'review.json')}))
