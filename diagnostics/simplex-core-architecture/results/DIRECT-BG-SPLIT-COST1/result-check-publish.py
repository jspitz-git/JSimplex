"""Publish exact independent diagnostic result acceptance; performance rejected."""
from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION';E=D.parent/'DIRECT-BG-SPLIT-COST1';run=D/'runs/cost1-300'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(p.read_text())
v=rd(E/'result-check.json');assert v['accepted'] is True and v['check_count']==74 and all(v['checks'].values()) and v['details']['exact_residuals']==4416 and v['details']['first_process_viable'] is False
assert not (run/'result-review.json').exists()
a=rd(run/'audit.json');assert all(sha(n)==h for n,h in a['sha256'].items())
files=sorted(str(p) for p in run.rglob('*') if p.is_file())
evidence=['result-check.py','result-check.json','result-check-host.json','result-check-publish.py','result-review.md','REPORT.md','report.py','summary.csv','gc-windows.json','postcheck.py','postcheck.json','posthost.json','allowance.json','preflight.json','closure.py','publication.py','admission-check.py','admission-check.json','admission-check-v2.py','admission-check-v2.json','admission-host-v2.json','admission-review.md','admission-publish.py']
r=dict(accepted=True,findings=[],scope='split BG matched cost result',phase='cost1-300',sha256={p:sha(p) for p in files},evidence_sha256={str(E/n):sha(E/n) for n in evidence},review_checks=74,exact_residuals=4416,performance_qualified=False,scope_limit='Diagnostic integrity/correctness acceptance only. Six cells fail; fixed design stopped. No second process, retry, tuning or production promotion.')
with (run/'result-review.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
assert set(r['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p!=run/'result-review.json'}
print('ACCEPTED diagnostic result; performance REJECTED;',len(files),'exact run bindings;',len(evidence),'evidence bindings; all review files frozen')
