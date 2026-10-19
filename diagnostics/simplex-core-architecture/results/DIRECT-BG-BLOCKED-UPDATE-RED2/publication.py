"""Exact failed-RED2 publication preserving one SHA-bound raw EOF blank line."""
from pathlib import Path
import sys,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c
names=c.rd(D/'publication-names.json')['paths'];selfname=str((D/'publication.json').relative_to(R));existing=[n for n in names if n!=selfname];policy=c.rd(D/'publication-policy.json')
c.require(c.rd(D/'closure.json')['all_passed'] is True and c.bindings(c.rd(D/'closure.json')),'Closure drift')
c.require(not c.git('diff','--cached','--name-only'),'Nonempty index')
c.require(set(existing)=={str(p.relative_to(R)) for root in [D,H/'runs/red300',H/'outers/red300'] for p in root.rglob('*') if p.is_file()},'Exact package')
c.require(c.sha(R/policy['raw'])==policy['sha256'],'Raw log drift')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Exact initial stage')
d=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(d.returncode==2 and d.stdout==policy['allowed_warning'],'Only exact bound raw EOF warning allowed')
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(D/'publication.json',dict(all_passed=True,qualification_accepted=False,launch_admitted=False,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(R/n) for n in existing},raw_whitespace_exception=policy,self_binding='Final staged and committed self blob verified separately'))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Exact final stage')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final staged blob '+n)
print('Exact failed RED2 publication PASS',len(names),'names/blobs; raw preserved')
