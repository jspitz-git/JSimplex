"""Exact diagnostic publication only; no Julia or runtime admission."""
from pathlib import Path
import sys,subprocess
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
names=c.rd(D/'publication-names.json')['paths'];selfname=str((D/'publication.json').relative_to(c.R));existing=[n for n in names if n!=selfname]
c.require(c.rd(D/'closure.json')['all_passed'] is True and c.bindings(c.rd(D/'closure.json')),'Closure drift')
c.require(not c.git('diff','--cached','--name-only'),'Nonempty index')
c.require(set(existing)=={str(p.relative_to(c.R)) for p in D.rglob('*') if p.is_file()},'Exact package')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Staged membership')
subprocess.run(['git','diff','--cached','--check'],cwd=c.R,check=True)
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(D/'publication.json',dict(all_passed=True,launch_admitted=False,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(c.R/n) for n in existing},self_binding='Final staged/committed self blob verified separately'))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Final membership')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final staged blob '+n)
print('Exact RED2 publication PASS',len(names),'names/blobs')
