"""Publish exact diagnostic package, preserving only verified unified-diff blank context."""
from pathlib import Path
import sys,subprocess,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');sys.path.insert(0,str(H));import control as c
names=c.rd(D/'publication-names.json')['paths'];selfname=str((D/'publication.json').relative_to(R));existing=[n for n in names if n!=selfname]
c.require(c.rd(D/'closure.json')['all_passed'] is True and c.bindings(c.rd(D/'closure.json')),'Closure drift')
c.require(not c.git('diff','--cached','--name-only'),'Index not empty')
c.require(set(existing)=={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()},'Exact package')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Exact initial stage')
d=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
lines=d.stdout.splitlines();allowed=[];i=0
while i<len(lines):
 match=re.fullmatch(r'(.+):(\d+): trailing whitespace\.',lines[i]);c.require(match is not None,'Unexpected whitespace diagnostic '+lines[i])
 n,line=match.group(1),int(match.group(2));p=R/n
 c.require(p.parent==D/'diffs/src' and p.suffix=='.diff' and p.read_text().splitlines()[line-1]==' ','Only exact verbatim blank diff context is allowed')
 c.require(i+1<len(lines) and lines[i+1]=='+ ','Unexpected diff diagnostic context')
 allowed.append(dict(path=n,line=line,sha256=c.sha(p),reason='Unchanged blank source context in verbatim unified diff'));i+=2
c.require(d.returncode==(2 if allowed else 0),'Unexpected diff returncode')
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(D/'publication.json',dict(all_passed=True,launch_admitted=False,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(R/n) for n in existing},verbatim_diff_whitespace=allowed,self_binding='Final staged/committed self blob verified separately; no recursive hash'))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Exact final names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final staged blob '+n)
print('Exact staged names/blobs PASS',len(names),'verbatim context exceptions',len(allowed))
