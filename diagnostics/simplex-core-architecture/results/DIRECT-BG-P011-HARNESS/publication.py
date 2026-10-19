"""One-shot exact offline staging. Does not commit, push or execute Julia."""
from pathlib import Path
import subprocess,json
import control as c
D=c.D;R=c.R
names=c.rd(D/'publication-names.json')['names'];target=str((D/'publication.json').relative_to(R))
c.require(len(names)==len(set(names)) and names==sorted(names),'Names duplicate/order')
c.require(c.git('diff','--cached','--name-only')=='','Nonempty preexisting index')
c.require(c.git('diff','--name-only')=='','Tracked changes')
c.require(c.git('rev-parse','HEAD')==c.ENTRY and c.git('rev-parse','master')==c.MASTER,'Reference drift')
z=c.rd(D/'closure.json');c.require(z['all_passed'] is True and all(z['checks'].values()) and c.bindings(z),'Closure failed/drift')
actual={str(p.relative_to(R)) for p in D.iterdir() if p.is_file()}
c.require(actual==set(names)-{target} and not any(p.is_dir() or p.is_symlink() for p in D.iterdir()),'Exact disk membership')
subprocess.run(['git','add','--',*[n for n in names if n!=target]],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==[n for n in names if n!=target],'Pre-output staged names')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:c.git('hash-object','--',n) for n in names if n!=target}
sha={str(R/n):c.sha(R/n) for n in names if n!=target}
c.save(D/'publication.json',dict(all_passed=True,checks=dict(closure=True,exact_disk_membership=True,exact_preoutput_staging=True,whitespace=True,refs=True),names=names,blobs_except_self=blobs,sha256=sha,scope='Exact complete staging; self blob checked after save and again after commit, outside self-referential record'))
subprocess.run(['git','add','--',target],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==names,'Final staged names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob mismatch '+n)
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps(dict(all_passed=True,exact_staged_files=len(names),listed_hashes=len(sha),publication_blob=c.git('rev-parse',':'+target))))
