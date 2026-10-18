"""Exact new GREEN2 evidence staging after PASS closure; no numerical execution."""
from pathlib import Path
import sys,json,subprocess
E=Path(__file__).resolve().parent;D=E;sys.path.insert(0,str(D));import control as c
R=c.R;run=D/'runs/green2-300';F=R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl';names=c.rd(E/'publication-names.json')['names'];pub=str((E/'publication.json').relative_to(R));others=[n for n in names if n!=pub]
cl=c.rd(E/'closure.json');c.require(cl['all_passed'] and all(cl['checks'].values()) and c.bindings(cl),'Closure drift')
c.require(not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'Existing staged/tracked edits')
c.require({str(p.relative_to(R)) for root in (E,) for p in root.rglob('*') if p.is_file()}|{str(F.relative_to(R))}==set(others),'Exact new membership')
subprocess.run(['git','add','--',*others],cwd=R,check=True)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(others),'Exact preliminary staging')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:c.git('rev-parse',':'+n) for n in others};c.require(all(blobs[n]==c.git('hash-object',n) for n in others),'Index blobs')
c.save(E/'publication.json',dict(all_passed=True,names=names,staged_blobs=blobs,sha256={n:c.sha(R/n) for n in others},scope='Exact GREEN2 harness/results; self publication blob checked separately before commit; no performance/master changes'))
subprocess.run(['git','add','--',pub],cwd=R,check=True)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Exact complete staging')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
c.require(all(c.git('rev-parse',':'+n)==c.git('hash-object',n) for n in names),'All exact blobs')
print(json.dumps(dict(all_passed=True,files=len(names),publication_blob=c.git('rev-parse',':'+pub),staged_blobs={n:c.git('rev-parse',':'+n) for n in names})))
