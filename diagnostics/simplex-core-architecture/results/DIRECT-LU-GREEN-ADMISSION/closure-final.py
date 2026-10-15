"""Separate publication amendment closure; old closure is read, never rerun."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
old=rd(D/'closure.json');review=rd(D/'publication-review.json');w=rd(D/'whitespace-check.json')
checks=dict(original15_closure_pass=old['all_passed'] is True and len(old['checks'])==15 and all(old['checks'].values()),original39_bindings_unchanged=len(old['sha256'])==39 and all(sha(path(n))==h for n,h in old['sha256'].items()),independent_exception_review=review['accepted'] is True and review['findings']==[],exception_review_bindings=all(sha(path(n))==h for n,h in review['sha256'].items()),four_exact_exception_gates=w['all_passed'] is True and len(w['checks'])==4 and all(w['checks'].values()),exception_source_bindings=all(sha(path(n))==h for n,h in w['sha256'].items()),original_failure_preserved=rd(D/'publication-failure.json')['execution_exit']==1 and not (D/'publication.json').exists(),refs_unchanged=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='ac2a94f40e8c815f48683adce67820e5ec6b8d62' and subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='6f68e24e8ddac42b948da8fcc2d636c010751194')
paths=[p for p in D.rglob('*') if p.is_file() and p.name not in ('closure-final.json','publication-final.json')]+[R/'diagnostics/simplex-core-architecture/DIRECT-LU-GREEN-ADMISSION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result=dict(all_passed=all(checks.values()),checks=checks,scope='Exact publication exception only; old failure preserved, no Julia',sha256={str(p.relative_to(R)):sha(p) for p in sorted(paths)})
with (D/'closure-final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256']))))
if not result['all_passed']:raise SystemExit('Publication amendment closure refused')
