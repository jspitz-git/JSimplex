"""Exact one-shot offline publication staging."""
from pathlib import Path
import sys,subprocess,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');sys.path.insert(0,str(D));import control as c
R=c.R
basenames=['REPORT.md','closure.json','closure.py','host.json','progress.md.after-P011-attribution','progress.md.before-P011-attribution','publication.json','publication.py','review.json','review.md','source-check.json','source_check.py']
names=sorted(str((E/n).relative_to(R)) for n in basenames);target=str((E/'publication.json').relative_to(R));actual=[n for n in names if n!=target]
c.require(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'Existing tracked/index changes')
c.require(c.git('rev-parse','HEAD')=='fb8f47d9a22b8f87a5db468813ec81202a7e8450' and c.git('rev-parse','master')==c.MASTER,'Refs')
c.require({str(p.relative_to(R)) for p in E.iterdir()}==set(actual),'Exact disk membership')
z=c.rd(E/'closure.json');c.require(z['all_passed'] is True and c.bindings(z),'Closure')
subprocess.run(['git','add','--',*actual],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==actual,'Staged names')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
c.save(E/'publication.json',dict(all_passed=True,names=names,sha256={str(R/n):c.sha(R/n) for n in actual},blobs_except_self={n:c.git('hash-object','--',n) for n in actual},scope='Exact staging; publication self blob checked externally after write'))
subprocess.run(['git','add','--',target],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==names,'Final names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps({'all_passed':True,'files':len(names)}))
