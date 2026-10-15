"""Exact fixed publication after PASS closure. No commit/push in this script."""
from common import *
cl=rd(Q/'closure.json');require(cl['all_passed'] is True and bindings(cl),'Closure')
names=rd(Q/'publication-names.json')['names'];own=str((Q/'publication.json').relative_to(R));other=[n for n in names if n!=own]
require(not git('diff','--cached','--name-only'),'Index not empty')
subprocess.run(['git','add','--',*other],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(other),'Exact staged names')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:git('rev-parse',':'+n) for n in other}
require(all(git('hash-object','--',n)==b for n,b in blobs.items()),'Stage/blob drift')
save(Q/'publication.json',dict(all_passed=True,staged_names=names,other_blobs=blobs,sha256={n:sha(R/n) for n in other},scope='Exact complete fixed names and other blobs BEFORE failfast commit/push; publication own blob verified after staging'))
subprocess.run(['git','add','--',own],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Final staged names')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(dict(names=len(names),bound_other_blobs=len(blobs),all_passed=True))
