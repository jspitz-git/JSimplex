"""One-shot publication manifest after exact staging; never commits or pushes."""
from pathlib import Path
import json,subprocess,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3]
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
c=json.loads((D/'closure.json').read_text());need(c['all_passed'] is True,'closure')
bound=dict(c['sha256']);bound[str((D/'closure.json').relative_to(R))]=sha((D/'closure.json').read_bytes())
actual=git('diff','--cached','--name-only','--diff-filter=A').decode().splitlines()
need(sorted(actual)==sorted(bound),'Exact staged names')
need(git('diff','--cached','--name-only').decode().splitlines()==sorted(bound),'No other staged changes')
for n,h in bound.items():need(sha(git('show',':'+n))==h==sha((R/n).read_bytes()),'Exact staged bytes '+n)
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
need(git('rev-parse','HEAD').decode().strip()=='60396400ca4a73c813bcec05cb3a602b743f82b9','entry')
need(git('rev-parse','master').decode().strip()=='26e2291745999f485a74f643298ca997d65c7205','master')
name=str((D/'publication.json').relative_to(R))
with (D/'publication.json').open('x') as f:json.dump(dict(all_passed=True,sha256=bound,exact_names=sorted([*bound,name]),scope='Before commit: exact staged names/blobs. This publication self-blob must be verified separately before failfast commit/push.'),f,indent=2);f.write('\n')
print('Publication PASS, final exact names',len(bound)+1)
