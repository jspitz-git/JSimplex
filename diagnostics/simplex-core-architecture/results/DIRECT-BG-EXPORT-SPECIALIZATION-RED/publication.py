"""Exact failed-attempt diagnostic publication, only after separate passing closure."""
from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,m):
 if not v:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
names=rd(D/'publication-names.json')['names'];cl=rd(D/'closure.json');pub=str((D/'publication.json').relative_to(R))
require(cl['all_passed'] and all(cl['checks'].values()),'Closure not passing')
require(all(sha(R/p)==s for p,s in cl['sha256'].items()),'Closure bindings changed')
require(set(names)==set(cl['sha256'])|{str((D/'closure.json').relative_to(R)),pub},'Closure/publication exact set')
require(not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'),'Unexpected tracked/index changes')
require(git('rev-parse','HEAD')=='e780e6158ea5365adf5cde36dceaa8032a34fe9c','HEAD changed')
require(git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205','Master changed')
payload=dict(all_passed=True,names=names,sha256={p:sha(R/p) for p in names if p!=pub},git_blobs={p:git('hash-object',p) for p in names if p!=pub},scope='Exact preserved failed RED attempt and diagnostic review; no qualification acceptance or source/test/env/CI changes')
with (D/'publication.json').open('x') as f:json.dump(payload,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*names],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Staged names differ')
blobs={p:git('rev-parse',':'+p) for p in names}
require(all(blobs[p]==git('hash-object',p) for p in names),'Staged/worktree blobs differ')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
out=dict(all_passed=True,files=len(names),staged_blobs=blobs)
with Path('/tmp/bgxs-red-exact-staged.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,files=len(names),exact_staged_blobs=True)))
