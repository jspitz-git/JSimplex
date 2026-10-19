"""Seal the independent diagnostic review only; no qualification acceptance."""
from pathlib import Path
import hashlib,json
Q=Path(__file__).resolve().parent;D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');RUN=D/'runs/red300'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
check=read(Q/'result-check.json');assert check['all_passed'] is True and all(check['checks'].values())
files={str(p):sha(p) for p in sorted(RUN.rglob('*')) if p.is_file() and p.name!='result-review.json'}
assert files==check['run_sha256'] and len(files)==67
assert all(sha(p)==h for p,h in check['evidence_sha256'].items())
evidence=['result-review.md','result-check.py','result-check.json','result-review-seal.py','RESULT.md','outer-closure.json','post-summary.json','admission-review.md','admission-check.py','admission-check.json','admission-check2.py','admission-check2.json','post-return.py']
record=dict(accepted=False,qualification_accepted=False,diagnostic_review_accepted=True,findings=[],scope='BG specialization RED failed-attempt diagnostic review',phase='red300',sha256=files,evidence_sha256={str(Q/n):sha(Q/n) for n in evidence},checks_passed=len(check['checks']),limitations=check['evidence']['limitations'])
with (RUN/'result-review.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
assert set(record['sha256'])=={str(p) for p in RUN.rglob('*') if p.is_file() and p.name!='result-review.json'}
assert all(sha(p)==h for p,h in record['sha256'].items()) and all(sha(p)==h for p,h in record['evidence_sha256'].items())
print(json.dumps(dict(diagnostic_review_accepted=True,qualification_accepted=False,accepted=False,checks=len(check['checks']),run_files=len(files),evidence_files=len(evidence))))
