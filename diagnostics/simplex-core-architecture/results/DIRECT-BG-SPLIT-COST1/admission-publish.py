"""Publish only the independently accepted exact first-run admission, once."""
from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION'
E=D.parent/'DIRECT-BG-SPLIT-COST1';run=D/'runs/cost1-300'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
s=rd(run/'sealed.json');v=rd(E/'admission-check-v2.json')
assert v['accepted'] is True and v['check_count']==454 and all(v['checks'].values())
assert set(p.name for p in run.iterdir())=={'sealed.json','config.json','host.json'}
paths={Path(n) for n in s['files']}
for t in s['trees']:
 root=Path(t);assert root.is_dir() and not root.is_symlink()
 for p in root.rglob('*'):
  assert not p.is_symlink() or (p.exists() and not p.is_dir())
  if p.is_file():paths.add(p)
assert {str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in paths}==s['inventory']
files=s['files']+[str(run/'sealed.json')]
evidence=['allowance.json','preflight.json','admission-check.py','admission-check.json','admission-check-v2.py','admission-check-v2.json','admission-host-v2.json','admission-review.md','admission-publish.py']
a={'accepted':True,'findings':[],'scope':'split BG matched cost admission','phase':'cost1-300','pins_sha256':sha(run/'sealed.json'),'sha256':{p:sha(p) for p in files},'evidence_sha256':{str(E/n):sha(E/n) for n in evidence},'review_checks':454,'scope_limit':'Exactly one first cost1-300 attempt; no retry, second process, tuning or public/production integration.'}
assert set(a['sha256'])==set(s['files'])|{str(run/'sealed.json')}
with (run/'admission.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
print('ACCEPTED cost1-300;',len(a['sha256']),'exact input bindings;',len(a['evidence_sha256']),'evidence bindings; no execution')
