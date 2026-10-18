"""One-shot exact diagnostic staging after accepted offline closure; no push."""
from control import *
import subprocess
names=rd(D/'publication-names.json')['names'];pub=str((D/'publication.json').relative_to(R));others=[n for n in names if n!=pub]
cl=rd(D/'closure.json');require(cl['all_passed'] and all(cl['checks'].values()) and bindings(cl),'Closure drift')
require(not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'),'Existing tracked/staged edits')
require({str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}==set(others),'Exact unstaged membership')
subprocess.run(['git','add','--',*others],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(others),'Exact preliminary staging')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:git('rev-parse',':'+n) for n in others}
require(all(blobs[n]==git('hash-object',n) for n in others),'Index/worktree blobs')
save(D/'publication.json',dict(all_passed=True,names=names,staged_blobs=blobs,sha256={n:sha(R/n) for n in others},scope='Exact offline diagnostic publication; publication self blob verified separately before commit, no Julia/master change'))
subprocess.run(['git','add','--',pub],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Exact complete staging')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
require(all(git('rev-parse',':'+n)==git('hash-object',n) for n in names),'All exact staged blobs')
print(json.dumps(dict(all_passed=True,files=len(names),publication_blob=git('rev-parse',':'+pub),staged_blobs={n:git('rev-parse',':'+n) for n in names})))
