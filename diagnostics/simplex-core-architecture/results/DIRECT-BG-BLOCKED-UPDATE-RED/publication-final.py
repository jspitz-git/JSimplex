"""Separate publication exception for one exact verbatim log EOF warning; no old script rerun."""
from pathlib import Path
import sys,subprocess,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');sys.path.insert(0,str(H));import control as c
raw=D/'outer-console.log';rawname=str(raw.relative_to(R));warning=rawname+':19: new blank line at EOF.\n'
cl=c.rd(D/'closure.json');rv=c.rd(D/'result-review.json');old=c.rd(D/'publication-names.json')['paths'];missing=str((D/'publication.json').relative_to(R))
c.require(cl['all_passed'] is True and c.bindings(cl),'Original closure drift')
c.require(rv['accepted'] is True and rv['qualification_accepted'] is False and rv['findings']==[] and c.bindings(rv),'Result review drift')
c.require(not (D/'publication.json').exists(),'Initial publication unexpectedly completed')
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(old)-{missing},'Initial exact staged set')
c.require(c.sha(raw)==cl['sha256'][rawname],'Verbatim raw log drift')
d=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(d.returncode==2 and d.stdout==warning,'Not the one recorded raw EOF exception')
c.save(D/'publication-exception.json',dict(all_passed=True,original_publication_completed=False,original_diff_returncode=d.returncode,original_diff_stdout=d.stdout,raw_preserved=True,sha256={str(D/'closure.json'):c.sha(D/'closure.json'),str(D/'publication-names.json'):c.sha(D/'publication-names.json'),str(raw):c.sha(raw),str(D/'publication.py'):c.sha(D/'publication.py')},scope='Initial publisher stopped before receipt/commit/push. Permit only this exact unchanged raw log terminal blank line; all authored files must be clean.'))
roots=[D,H/'runs/red300',H/'outers/red300'];actual={str(p.relative_to(R)) for root in roots for p in root.rglob('*') if p.is_file()}
names=sorted(actual|{str((D/n).relative_to(R)) for n in ['publication-names-final.json','closure-final.json','publication-final.json']})
c.save(D/'publication-names-final.json',dict(paths=names,supersedes_uncompleted_package='publication-names.json',excluded_uncreated=missing))
actual.add(str((D/'publication-names-final.json').relative_to(R)))
c.require(c.git('rev-parse','HEAD')=='6900c4473a39411b074109fb6362fd8753ca10d0' and c.git('rev-parse','master')==c.MASTER,'Ref drift')
c.require(not c.git('diff','--name-only'),'Unexpected unstaged tracked mutation')
c.save(D/'closure-final.json',dict(all_passed=True,qualification_accepted=False,original_closure_preserved=True,independent_result_review_current=True,raw_whitespace_exception='publication-exception.json',sha256={n:c.sha(R/n) for n in sorted(actual)},scope='Final exact diagnostic package closure; original PASS closure and failed publication are preserved.'))
print('Final diagnostic closure PASS',len(actual),'bindings')
selfname=str((D/'publication-final.json').relative_to(R));existing=[n for n in names if n!=selfname]
c.require(set(existing)=={str(p.relative_to(R)) for root in roots for p in root.rglob('*') if p.is_file()},'Final package membership')
c.git('add','--',*existing)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(existing),'Final initial staging names')
d=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
c.require(d.returncode==2 and d.stdout==warning,'Unexpected final whitespace diagnostics')
for n in existing:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob '+n)
c.save(D/'publication-final.json',dict(all_passed=True,qualification_accepted=False,staged_names=names,git_blobs={n:c.git('rev-parse',':'+n) for n in existing},sha256={n:c.sha(R/n) for n in existing},raw_whitespace_exception=warning,self_binding='Exact final staged/committed blob verification; no recursive selfhash'))
c.git('add','--',selfname)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Complete final staging')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Final staged blob '+n)
print('Exact final staged names/blobs PASS',len(names))
