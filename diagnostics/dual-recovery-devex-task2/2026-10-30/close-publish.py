from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task2/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def req(v,m):
 if not v:raise RuntimeError(m)
for a,b in [('/tmp/devex-task2-review.md','REVIEW-FINAL.md'),('/tmp/devex-task2-review.json','review-final.json')]:
 with (D/b).open('xb') as f:f.write(Path(a).read_bytes())
r=json.loads((D/'review-final.json').read_text());c=json.loads((D/'source-check.json').read_text())
checks={'review_accepted':r['accepted'] and all(r['checks'].values()),'review_bindings':all(sha(Path(n))==h for n,h in r['bindings'].items()),'review_report':sha(D/'REVIEW-FINAL.md')==r['review_report_sha256'],'source_inverse':c['accepted'] and all(c['checks'].values()),'source_bindings':all(sha(Path(n))==h for n,h in c['bindings'].items()),'head':git('rev-parse','HEAD')=='5c01262acb36bae18c8bc578dab6e93e2748129c','master':git('rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','tracked_unchanged':not git('diff','--name-only','HEAD'),'empty_index':not git('diff','--cached','--name-only')}
req(all(checks.values()),str(checks))
with (D/'close-publish.py').open('xb') as f:f.write(Path(__file__).read_bytes())
with (D/'closure.json').open('x') as f:f.write(json.dumps(dict(accepted=True,scope='Task2 source preparation only; Julia UNEXECUTED',numerical_admission=False,checks=checks,bindings={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n')
paths=sorted(str(p.relative_to(W)) for p in D.iterdir() if p.is_file())
for p in paths:
 x=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(W/p)],capture_output=True,text=True);req(not x.stdout and not x.stderr and x.returncode in (0,1),'whitespace '+p)
names=sorted(paths+[str((D/'publication.json').relative_to(W))]);blobs={p:git('hash-object',str(W/p)) for p in paths}
with (D/'publication.json').open('x') as f:f.write(json.dumps(dict(accepted=True,expected_names=names,blobs_excluding_publication=blobs,closure_sha256=sha(D/'closure.json')),indent=2)+'\n')
subprocess.run(['git','-C',str(W),'add','--',*names],check=True)
req(git('diff','--cached','--name-only').splitlines()==names,'names');seal={p:git('rev-parse',':'+p) for p in names};req(all(h==git('hash-object',str(W/p)) for p,h in seal.items()),'blobs')
Path('/tmp/dual-recovery-devex-task2-20261030/exact-staged.json').write_text(json.dumps(dict(names=names,blobs=seal),indent=2)+'\n')
print(json.dumps(dict(closure_checks=len(checks),exact_staged_files=len(names),exact_staged_blobs=len(seal))))
