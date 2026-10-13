"""Exclusive exact complete staged publication, after separate PASS closure."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True)
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
c=json.loads((H/'closure.json').read_text());assert c['all_passed'] is True and all(v is True for v in c['checks'].values()) and all(sha(k)==v for k,v in c['sha256'].items());assert not git('diff','--cached','--name-only').strip()
paths=[H,D/'STATUS.md',D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-preparation.md'];expected={str(p.relative_to(R)) for x in paths for p in (x.rglob('*') if x.is_dir() else [x]) if p.is_file()}
subprocess.run(['git','add','--',*[str(p.relative_to(R)) for p in paths]],check=True)
subprocess.run(['git','diff','--cached','--check'],check=True)
names=set(git('diff','--cached','--name-only').splitlines());assert names==expected and all(subprocess.check_output(['git','show',':'+n])==(R/n).read_bytes() for n in names)
checks=dict(closure_PASS=True,closure_bindings=True,complete_names=True,exact_blobs=True,authored_diff_clean=True,no_source_test_env_CI=True)
assert all(n.startswith('diagnostics/simplex-core-architecture/') or n.startswith('docs/superpowers/plans/') for n in names)
dump(H/'publication-check.json',dict(checks=checks,all_passed=True));subprocess.run(['git','add','--',str((H/'publication-check.json').relative_to(R))],check=True)
names=set(git('diff','--cached','--name-only').splitlines());blobs={n:hashlib.sha256(subprocess.check_output(['git','show',':'+n])).hexdigest() for n in sorted(names)};assert all(sha(R/n)==v for n,v in blobs.items())
p=H/'staged-files.json';dump(p,dict(sha256=blobs,scope='All staged names except self; own blob separately verified.'));subprocess.run(['git','add','--',str(p.relative_to(R))],check=True)
a=set(git('diff','--cached','--name-only').splitlines());assert a==names|{str(p.relative_to(R))} and all(subprocess.check_output(['git','show',':'+n])==(R/n).read_bytes() for n in a)
print(json.dumps(dict(checks=checks,complete_staged=len(a))))
