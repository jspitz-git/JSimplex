from pathlib import Path
import sys,subprocess,json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK1')
sys.path.insert(0,str(P));import control as c
names=c.rd(Q/'publication-names.json')['paths'];cl=c.rd(Q/'closure.json');c.require(cl['all_passed'] and c.bindings(cl),'Closure drift');c.require(not c.git('diff','--cached','--name-only'),'Index not empty')
pub=str((Q/'publication.json').relative_to(R));hashes={n:c.sha(R/n) for n in names if n!=pub}
for n in hashes:
 check=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(R/n)],cwd=R,capture_output=True,text=True)
 c.require(not check.stdout and not check.stderr and check.returncode in (0,1),'Whitespace '+n+':'+check.stdout+check.stderr)
c.save(Q/'publication.json',{'all_passed':True,'exact_paths':names,'sha256':hashes,'scope':'Exact fixed publication after independent review and separate PASS closure'})
subprocess.run(['git','add','--',*names],cwd=R,check=True)
c.require(set(c.git('diff','--cached','--name-only').splitlines())==set(names),'Staged membership')
for n in names:
 b=subprocess.check_output(['git','show',':'+n],cwd=R);c.require(hashlib.sha256(b).hexdigest()==c.sha(R/n),'Staged blob drift '+n)
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps({'all_passed':True,'exact_staged_names_and_blobs':len(names)}))
