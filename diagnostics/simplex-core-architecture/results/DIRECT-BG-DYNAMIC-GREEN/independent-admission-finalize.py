"""New independent final read/hash check and exclusive admission publication; no Julia."""
import hashlib,json
from pathlib import Path
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';run=D/'runs/green300'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
s=rd(run/'sealed.json')
assert sha(run/'sealed.json')==rd(E/'independent-admission-check.json')['sealed_sha256']
assert all(str(Path(n).resolve())==v['resolved'] and sha(n)==v['sha256'] for n,v in s['inventory'].items())
for name in ['world-age-sources.json','world-age-runtime.json','world-age-conditions.json']:
 assert all(sha(n)==h for n,h in rd(E/name)['sha256'].items()),name
assert rd(E/'world-age-conditions.json')['all_passed'] is True
assert not (run/'reservation.json').exists() and not (run/'output').exists()
evidence={str(p):sha(p) for p in sorted(E.iterdir()) if p.is_file()}
# Bind nested source/header/tool records directly as well as their manifests.
for name in ['world-age-sources.json','world-age-runtime.json','world-age-conditions.json']:
 for n,h in rd(E/name)['sha256'].items():
  assert n not in evidence or evidence[n]==h
  evidence[n]=h
v={'accepted':True,'findings':[],'scope':'dynamic BG exact-stage admission','phase':'green300','pins_sha256':sha(run/'sealed.json'),'sha256':{n:sha(n) for n in s['files']+[str(run/'sealed.json')]},'evidence_sha256':evidence,'notes':'Independent source/runtime assessment accepts one unchanged pinned bounded correctness attempt with world-age warnings retained. Numerical result, future compatibility and performance remain unqualified.'}
with (run/'admission.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({'accepted':True,'sealed_files':len(s['files']),'review_bindings':len(v['sha256']),'evidence_bindings':len(evidence),'admission_sha256':sha(run/'admission.json')}))
