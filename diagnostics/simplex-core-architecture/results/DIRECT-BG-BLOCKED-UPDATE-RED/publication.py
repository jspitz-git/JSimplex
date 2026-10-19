"""Stage the exact failed-RED diagnostic package only after independent review and closure."""
from pathlib import Path
import sys,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');sys.path.insert(0,str(H));import control as c
names=c.rd(D/'publication-names.json')['paths'];selfname=str((D/'publication.json').relative_to(R));existing=[n for n in names if n!=selfname]
c.require(c.rd(D/'closure.json')['all_passed'] is True and c.bindings(c.rd(D/'closure.json')),'Closure not PASS/current')
c.require(not c.git('diff','--cached','--name-only'),'Index not empty')
roots=[D,H/'runs/red300',H/'outers/red300'];actual={str(p.relative_to(R)) for root in roots for p in root.rglob('*') if p.is_file()}
c.require(set(existing)==actual,'Exact package names')
c.require(all(any(n.startswith(str(root.relative_to(R))+'/') for root in roots) for n in names),'Scope escaped')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Exact first staging')
diff=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(diff.returncode==0 and not diff.stdout,'Whitespace '+diff.stdout)
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(D/'publication.json',dict(all_passed=True,qualification_accepted=False,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(R/n) for n in existing},self_binding='Exact final staging and postcommit self blob; no recursive hash',scope=__doc__))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Exact final names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final staged blob '+n)
print('Exact staged names/blobs PASS',len(names))
