"""Exact one-shot OFFLINE publication gate; no commit/push or numerical work."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
NAMES = ['diagnostics/simplex-core-architecture/DIRECT-LU-TEST-REPAIR.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/STATUS.md.before-repair', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/closure.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/closure.py', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/continuation.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/continue.py', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/correctness.jl', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/driver.jl', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/frozen-inputs.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/host.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/host.py', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/prepare.py', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/publication.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/publication.py', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/replacements.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/review.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/review.md', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/roadmap.md.before-repair', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/source-check.json', 'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/source-check.py', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((D/'closure.json').read_text())
if not c['all_passed'] or not all(sha(R/n)==h for n,h in c['sha256'].items()):raise SystemExit('Closure not valid')
if git('diff','--cached','--name-only'):raise SystemExit('Index not empty')
selfname=str((D/'publication.json').relative_to(R));other=[n for n in NAMES if n!=selfname]
actual=sorted(str(p.relative_to(R)) for p in D.iterdir() if p.is_file())
if actual!=sorted(n for n in other if n.startswith(str(D.relative_to(R))+'/')):raise SystemExit('Unexpected repair file set')
if any(not (R/n).is_file() for n in other):raise SystemExit('Missing file')
subprocess.run(['git','add','--',*other],cwd=R,check=True)
if sorted(git('diff','--cached','--name-only').splitlines())!=sorted(other):raise SystemExit('Initial exact index mismatch')
blobs={n:git('rev-parse',':'+n) for n in other}
if any(git('hash-object',n)!=h for n,h in blobs.items()):raise SystemExit('Staged bytes mismatch')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
with (D/'publication.json').open('x') as f:json.dump(dict(all_passed=True,scope='Offline test repair accepted; no Julia, launch or numerical correctness acceptance',exact_names=NAMES,staged_blobs_excluding_self=blobs,sha256={n:sha(R/n) for n in other},self_binding='Exact staged and committed set; self blob verified after commit'),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',selfname],cwd=R,check=True)
if sorted(git('diff','--cached','--name-only').splitlines())!=NAMES:raise SystemExit('Final exact staged set mismatch')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps(dict(all_passed=True,exact_staged_files=len(NAMES),bound_other_blobs=len(blobs))))
