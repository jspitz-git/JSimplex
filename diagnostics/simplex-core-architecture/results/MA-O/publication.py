"""One-shot exact staged publication after PASS diagnostic closure."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-O'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def require(v,m):
 if not v:raise ValueError(m)
names=read(D/'publication-names.json');selfname=str((D/'publication.json').relative_to(R));other=[n for n in names if n!=selfname];closure=read(D/'closure.json');staged=[n for n in git('diff','--cached','--name-only','-z').decode().split('\0') if n];blobs={n:git('rev-parse',':'+n).decode().strip() for n in other}
checks=dict(closure_PASS=closure['all_passed'] is True and all(closure['checks'].values()),closure_bindings=all(sha(p)==h for p,h in closure['sha256'].items()),exact_complete_stage=set(staged)==set(other) and len(staged)==len(other),staged_bytes_exact=all(git('show',':'+n)==(R/n).read_bytes() for n in other),staged_diff_clean=subprocess.run(['git','diff','--cached','--check'],capture_output=True).returncode==0)
v=dict(all_passed=all(checks.values()),checks=checks,exact_names=names,sha256={n:sha(R/n) for n in other},staged_blobs=blobs,scope='Exact publication of diagnostic rejection; self record staged and verified separately before failfast commit/push.')
with(D/'publication.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(v['all_passed'],'publication failed; no commit/push')
