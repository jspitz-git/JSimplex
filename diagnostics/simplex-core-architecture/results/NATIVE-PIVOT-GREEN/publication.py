"""One-shot exact complete staging after accepted failed-GREEN diagnostic closure; no commit/push."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
 if not x:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
c=rd(D/'closure.json');require(c['all_passed'] is True and all(sha(R/n)==v for n,v in c['sha256'].items()),'Closure')
names=rd(D/'publication-names.json')['names'];own=str((D/'publication.json').relative_to(R));other=[n for n in names if n!=own]
require(not git('diff','--cached','--name-only'),'Index')
subprocess.run(['git','add','--',*other],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(other),'Exact stage')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:git('rev-parse',':'+n) for n in other};require(all(git('hash-object','--',n)==v for n,v in blobs.items()),'Blobs')
with (D/'publication.json').open('x') as f:json.dump(dict(all_passed=True,staged_names=names,other_blobs=blobs,sha256={n:sha(R/n) for n in other}),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',own],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Complete stage')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(dict(names=len(names),blobs=len(blobs),all_passed=True))
