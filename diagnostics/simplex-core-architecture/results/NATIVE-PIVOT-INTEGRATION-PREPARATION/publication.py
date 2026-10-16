"""One-shot exact stage/publication verification after offline PASS closure."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,m):
 if not x:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
z=rd(D/'closure.json');require(z['all_passed'] is True,'Closure not PASS')
require(all(sha(R/n)==h for n,h in z['sha256'].items()),'Closure bindings')
require(not git('diff','--cached','--name-only'),'Index not empty')
names=rd(D/'publication-names.json')['names'];myname=str((D/'publication.json').relative_to(R));others=[n for n in names if n!=myname]
require(set(others)==set(z['sha256'])|{str((D/'closure.json').relative_to(R))},'Exact closure coverage')
subprocess.run(['git','add','--',*others],cwd=R,check=True)
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(others),'Unexpected staged names')
blobs={n:git('rev-parse',':'+n) for n in others}
for n in others:
 require(subprocess.check_output(['git','show',':'+n],cwd=R)==(R/n).read_bytes(),'Staged mismatch '+n)
with (D/'publication.json').open('x') as f:json.dump(dict(all_passed=True,staged_names=names,other_blobs=blobs,sha256={n:sha(R/n) for n in others}),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',myname],cwd=R,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Final staged membership')
for n in names:require(subprocess.check_output(['git','show',':'+n],cwd=R)==(R/n).read_bytes(),'Final staged bytes')
print(dict(all_passed=True,names=len(names),other_blobs=len(blobs)))
