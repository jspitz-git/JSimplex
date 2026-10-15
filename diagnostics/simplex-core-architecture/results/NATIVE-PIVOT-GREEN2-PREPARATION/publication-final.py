"""Separate publication after exact diff-context supplement review; never rerun original."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
 if not x:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
c=rd(D/'closure-supplement.json');require(c['all_passed'] is True and all(sha(R/n)==v for n,v in c['sha256'].items()),'Supplement closure')
review=rd(D/'publication-review.json');require(review['accepted'] is True and review['findings']==[] and review['scope']=='exact diff-context publication' and all(sha(Path(n))==v for n,v in review['sha256'].items()),'Publication review')
names=rd(D/'publication-names-final.json')['names'];own=str((D/'publication-final.json').relative_to(R));other=[n for n in names if n!=own]
old=rd(D/'publication-names.json')['names'];absent=str((D/'publication.json').relative_to(R))
require(not (D/'publication.json').exists(),'Original failed publication must stay absent')
require(set(git('diff','--cached','--name-only').splitlines())==set(old)-{absent},'Exact original partial stage')
subprocess.run(['git','add','--',*other],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(other),'Exact final stage')
p=str((D/'changes.diff').relative_to(R));lines=(D/'changes.diff').read_text().splitlines();nums=[96,114,133,149,174]
require(all(lines[n-1]==' ' for n in nums),'Exact context markers')
z=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
expected=''.join(f'{p}:{n}: trailing whitespace.\n+ \n' for n in nums)
require(z.returncode==2 and z.stdout==expected and z.stderr=='','Only five exact diagnostics allowed')
subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)'+p],cwd=R,check=True)
blobs={n:git('rev-parse',':'+n) for n in other};require(all(git('hash-object','--',n)==v for n,v in blobs.items()),'Exact blobs')
with (D/'publication-final.json').open('x') as f:json.dump(dict(all_passed=True,staged_names=names,other_blobs=blobs,sha256={n:sha(R/n) for n in other},preserved_whitespace=dict(path=p,lines=nums,reason='Unified diff empty context markers; all authored content passes')),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',own],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Complete stage')
subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)'+p],cwd=R,check=True)
print(dict(names=len(names),blobs=len(blobs),all_passed=True))
