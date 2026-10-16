"""Freeze exact accepted result membership and separate evidence, no project imports."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';P=D/'runs/cost1-300'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(p.read_text())
check=rd(E/'result-review-checks.json');extra=rd(E/'result-review-supplement.json')
assert check['all_passed'] is True and check['count']==14408 and all(x['passed'] for x in check['checks'])
assert extra['all_passed'] is True and len(extra['checks'])==18 and all(extra['checks'].values())
assert check['facts']['exact_residuals']==11520
for n,h in rd(P/'audit.json')['sha256'].items():assert sha(Path(n))==h
for n,h in rd(P/'admission.json')['evidence_sha256'].items():assert sha(Path(n))==h
files=sorted(str(x) for x in P.rglob('*') if x.is_file() and x!=P/'result-review.json')
assert len(files)==577 and str(P/'result-review.md') in files
supp=sorted(x for x in E.iterdir() if x.is_file())
assert {E/n for n in ['REPORT.md','continuation-text.md','close.py','publication.py']}<=set(supp)
a=dict(accepted=True,findings=[],scope='direct adapter matched cost result',phase='cost1-300',sha256={n:sha(Path(n)) for n in files},evidence_sha256={str(n):sha(n) for n in supp})
with (P/'result-review.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
assert rd(P/'result-review.json')==a
assert set(a['sha256'])=={str(x) for x in P.rglob('*') if x.is_file() and x!=P/'result-review.json'}
assert all(sha(Path(n))==h for n,h in a['evidence_sha256'].items())
print(json.dumps(dict(accepted=True,findings=[],result_bindings=len(files),supplementary_bindings=len(supp),checks=14408,supplementary_checks=18,result_review_sha256=sha(P/'result-review.json'))))
