"""One-shot exact staging of independently accepted offline candidate/tests."""
from pathlib import Path
import sys,subprocess,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');sys.path.insert(0,str(D));import control as c
R=c.R
basenames=['REPORT.md','author-check.json','author-check.py','closure.json','closure.py','host.json','panel.jl','prepare.py','progress.md.after-zero-counts','progress.md.before-zero-counts','publication.json','publication.py','review.json','review.md','source-check.json','source_contract.py','structural-red.json','zero-counts-tests.jl']
names=sorted(str((E/n).relative_to(R)) for n in basenames);target=str((E/'publication.json').relative_to(R));actual=[n for n in names if n!=target]
c.require(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'Existing edits/index')
c.require(c.git('rev-parse','HEAD')=='370b5529b454acc2e93332245966c6a160bdc0d9' and c.git('rev-parse','master')==c.MASTER,'Refs')
c.require({str(p.relative_to(R)) for p in E.iterdir()}==set(actual) and all((R/n).is_file() and not (R/n).is_symlink() for n in actual),'Exact regular files')
z=c.rd(E/'closure.json');c.require(z['all_passed'] is True and c.bindings(z),'Closure')
subprocess.run(['git','add','--',*actual],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==actual,'Exact staged names')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
c.save(E/'publication.json',dict(all_passed=True,names=names,sha256={str(R/n):c.sha(R/n) for n in actual},blobs_except_self={n:c.git('hash-object','--',n) for n in actual},scope='Exact staging with self blob verified after save and at commit'))
subprocess.run(['git','add','--',target],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==names,'Final exact names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob drift')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps({'all_passed':True,'exact_staged_files':len(names)}))
