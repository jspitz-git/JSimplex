"""Publish exact reviewer admission after final independent pure hash/text checks."""
from pathlib import Path
import hashlib,json,tomllib
E=Path(__file__).resolve().parent;R=E.parents[3];D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION';run=D/'runs/red300';sp=run/'sealed.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
s=rd(sp);result=rd(E/'admission-check.json')
assert result['all_passed'] and result['sealed_sha256']==sha(sp)
assert {p.name for p in run.iterdir()}=={'config.json','host.json','sealed.json'}
paths=set(s['files'])
for tree in s['trees']:
 root=Path(tree);assert root.is_dir() and not root.is_symlink()
 for p in root.rglob('*'):
  assert not p.is_symlink()
  if p.is_file():paths.add(str(p))
assert paths==set(s['inventory'])
for n,v in s['inventory'].items():assert sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved']
toml=tomllib.loads((D/'expected-tests.toml').read_text())['red']
assert toml=={'assertions':10,'groups':[{'name':'Missing split BG U contracts (ten expected failures)','pass':0,'fail':10,'error':0,'broken':0}]}
files=list(s['files'])+[str(sp)];assert len(files)==len(set(files))
evidence=[E/n for n in ['allowance.json','preflight.json','postcheck.py','admission-check.py','admission-check.json','admission-review.md','admission-publish.py']]
review=dict(accepted=True,findings=[],scope='split BG exact-stage admission',phase='red300',pins_sha256=sha(sp),sha256={n:sha(n) for n in sorted(files)},evidence_sha256={str(p):sha(p) for p in evidence})
assert set(review['sha256'])==set(s['files'])|{str(sp)}
assert all(review['sha256'][n]==v['sha256'] for n,v in s['inventory'].items())
with (run/'admission.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
saved=rd(run/'admission.json');assert saved==review
assert all(sha(n)==h for key in ['sha256','evidence_sha256'] for n,h in saved[key].items())
print(json.dumps(dict(accepted=True,findings=[],phase=review['phase'],scope=review['scope'],sealed_sha256=sha(sp),review_sha256=sha(run/'admission.json'),exact_file_bindings=len(files),evidence_bindings=len(evidence))))
