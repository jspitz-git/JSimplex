"""One-shot exact staged publication gate, executed after PASS closure and staging."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-L'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a])
def require(ok,msg):
 if not ok:raise ValueError(msg)
names=read(D/'publication-names.json');selfname=str((D/'publication.json').relative_to(R));other=[n for n in names if n!=selfname]
closure=read(D/'closure.json'); staged=git('diff','--cached','--name-only','-z').decode().split('\0');staged=[s for s in staged if s]
blobs={n:git('rev-parse',':'+n).decode().strip() for n in other}
checks={
'closure_pass':closure['all_passed'] is True and all(closure['checks'].values()),
'closure_bindings':all(sha(p)==v for p,v in closure['sha256'].items()),
'exact_stage_before_self':set(staged)==set(other) and len(staged)==len(other),
'staged_bytes_exact':all(git('show',':'+n)==(R/n).read_bytes() for n in other),
'staged_diff_clean':subprocess.run(['git','diff','--cached','--check'],capture_output=True).returncode==0,
}
record=dict(all_passed=all(checks.values()),checks=checks,exact_names=names,sha256={n:sha(R/n) for n in other},staged_blobs=blobs,scope='Exact complete staged list except this self-record, which is staged and verified before failfast commit.')
with (D/'publication.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(record['all_passed'],'publication failed; no commit/push')
