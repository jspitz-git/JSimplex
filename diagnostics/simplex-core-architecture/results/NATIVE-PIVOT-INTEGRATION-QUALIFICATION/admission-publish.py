"""Publish one admission after independent passed checks; no numerical execution."""
from pathlib import Path
import hashlib,json,os
R=Path.cwd();B=R/'diagnostics/simplex-core-architecture/results';E=B/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';K=B/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION';run=E/'runs/integration';sp=run/'sealed.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(p.read_text())
checks=rd(K/'admission-checks.json');assert checks['all_passed'] is True and all(checks['checks'].values())
s=rd(sp);assert len(s['files'])==len(s['inventory'])==1643 and set(s['files'])==set(s['inventory'])
assert all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in s['inventory'].items())
env=rd(E/'environment.json');assert {k:os.environ.get(k) for k in env}==env
assert {p.name for p in run.iterdir()}=={'sealed.json','config.json','host.json'}
bindings={n:v['sha256'] for n,v in s['inventory'].items()};bindings[str(sp)]=sha(sp);assert len(bindings)==1644
record=dict(accepted=True,findings=[],scope='exact-stage admission',phase='integration',pins_sha256=sha(sp),sha256=bindings,evidence_sha256={str(K/n):sha(K/n) for n in ['admission-check.py','admission-checks.json','admission-review.md','admission-publish.py']},runtime='UNEXECUTED',limits='One attempt, 60 seconds inclusive / 52 seconds inner, unchanged sealed command and gates; failure preserves evidence and stops')
with (run/'admission.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
written=rd(run/'admission.json');assert written==record
print(json.dumps(dict(accepted=True,scope=record['scope'],phase=record['phase'],bindings=len(bindings),evidence=len(record['evidence_sha256']),pins_sha256=record['pins_sha256'])))
