"""Final read/hash/text verification then exclusive result envelope; no later run writes."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;R=E.parents[3];D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION';run=D/'runs/red300';target=run/'result-review.json'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks=rd(E/'result-check.json');assert checks['all_passed'] and checks['checks']==5918
files={str(p) for p in run.rglob('*') if p.is_file()};assert len(files)==17 and files==set(checks['sha256']) and not target.exists()
assert all(sha(n)==h for n,h in checks['sha256'].items())
for name in ['sealed.json','launch-pins.json']:
 j=rd(run/name);paths=set(j['files'])
 for t in j['trees']:
  root=Path(t);assert root.is_dir() and not root.is_symlink()
  for p in root.rglob('*'):
   assert not p.is_symlink()
   if p.is_file():paths.add(str(p))
 assert paths==set(j['inventory'])
 assert all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in j['inventory'].items())
old='Inclusive supervisor/launcher duration was 5.034496337 seconds; the guard recorded 4.483036629 seconds including its launch.'
new='Inclusive launcher duration was 5.034496337 seconds; the supervisor recorded 5.034476037 seconds and the guard recorded 4.483036629 seconds including its launch.'
before=(E/'REPORT.before-review.md').read_text();report=(E/'REPORT.md').read_text();assert before.count(old)==1 and before.replace(old,new)==report
clar=rd(E/'report-clarification.json');inv=rd(run/'invocation.json');assert clar['only_change'] is True and clar['launcher_seconds']==inv['elapsed_seconds'] and clar['supervisor_seconds']==inv['supervisor']['elapsed_seconds']
evidence=[E/n for n in ['allowance.json','preflight.json','postcheck.py','postcheck.json','posthost.json','REPORT.md','REPORT.before-review.md','report-clarification.json','result-check.py','result-check.json','result-review.md','result-publish.py']]
review=dict(accepted=True,findings=[],scope='split BG RED result',phase='red300',sha256={n:sha(n) for n in sorted(files)},evidence_sha256={str(p):sha(p) for p in evidence})
assert set(review['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p!=target}
with target.open('x') as f:json.dump(review,f,indent=2);f.write('\n')
# Read-only final validation. No additional writes under run.
saved=rd(target);assert saved==review and set(saved['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p!=target}
assert all(sha(n)==h for key in ['sha256','evidence_sha256'] for n,h in saved[key].items())
print(json.dumps(dict(accepted=True,findings=[],scope=review['scope'],phase=review['phase'],run_bindings=len(files),evidence_bindings=len(evidence),result_review_sha256=sha(target))))
