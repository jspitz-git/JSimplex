"""One-shot final publication with exact frozen whitespace diagnostics only."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-N'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def require(ok,msg):
 if not ok:raise ValueError(msg)
names=read(D/'publication-names-final.json');selfname=str((D/'publication-final.json').relative_to(R));other=[n for n in names if n!=selfname];closure=read(D/'closure-final.json');supp=read(D/'publication-whitespace-supplement.json')
staged=[s for s in git('diff','--cached','--name-only','-z').decode().split('\0') if s];blobs={n:git('rev-parse',':'+n).decode().strip() for n in other}
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
checks={
 'supplemental_closure_PASS':closure['all_passed'] is True and all(closure['checks'].values()),
 'supplemental_closure_bindings':all(sha(p)==h for p,h in closure['sha256'].items()),
 'exact_complete_stage_before_self':set(staged)==set(other) and len(staged)==len(other),
 'all_staged_bytes_exact':all(git('show',':'+n)==(R/n).read_bytes() for n in other),
 'only_exact_two_frozen_whitespace_lines':r.returncode==2 and r.stdout==supp['expected_diagnostics'] and not r.stderr,
}
v=dict(all_passed=all(checks.values()),checks=checks,exact_names=names,sha256={n:sha(R/n) for n in other},staged_blobs=blobs,scope='Initial publication remains FALSE. Only exact pinned single-space line15 in prepare-2.py and prepare-3.py permitted. Self record staged/verified separately before failfast commit.')
with(D/'publication-final.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(v['all_passed'],'publication failed; no commit/push')
