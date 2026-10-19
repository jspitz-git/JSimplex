from pathlib import Path
import sys,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')
sys.path.insert(0,str(P));import control as c
names=c.rd(Q/'publication-names.json')['paths'];selfname=str((Q/'publication.json').relative_to(R));existing=[n for n in names if n!=selfname]
c.require(c.rd(Q/'closure.json')['all_passed'],'Closure must pass')
c.require(not c.git('diff','--cached','--name-only'),'Index empty')
for n,h in c.rd(Q/'closure.json')['sha256'].items():c.require(c.sha(R/n)==h,'Closure drift '+n)
w=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(Q/'REPORT.md')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(w.returncode in (0,1) and not w.stdout,'Report whitespace')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Exact first staging')
d=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(d.returncode==0 and not d.stdout,'Staged whitespace: '+d.stdout)
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(Q/'publication.json',dict(all_passed=True,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(R/n) for n in existing},self_binding='Exact staged working and later committed blob check; no recursive selfhash',scope='Diagnostic Task2 only; master unchanged'))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Exact final staging')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final blob '+n)
print('EXACT '+str(len(names))+' staged names/blobs PASS; ready for failfast commit/push')
