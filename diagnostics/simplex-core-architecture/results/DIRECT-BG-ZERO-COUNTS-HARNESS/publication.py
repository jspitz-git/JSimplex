"""One-shot exact offline diagnostic publication. No numerical entrypoints."""
from control import *
BASENAMES=['ADMISSION.md', 'REPORT.md', 'audit.py', 'baseline.json', 'candidate-side.jl', 'close-preparation.py', 'closure.json', 'closure.py', 'control.py', 'copied-files.json', 'dict-fix.json', 'driver.jl', 'driver.jl.initial', 'environment.json', 'extend.py', 'guard.py', 'historical-groups.json', 'host-closure.json', 'host-entry.json', 'independent-check.json', 'independent-check.py', 'launch.py', 'loaded-paths.json', 'operations.jl', 'operations.jl.before-dict-fix', 'operations.jl.initial', 'oracle.py', 'oracle.py.initial', 'outer.py', 'outer.py.initial', 'pin-preparation.py', 'post-return.py', 'preparation-pins.json', 'prepare.py', 'progress.md.after-zero-harness', 'progress.md.before-zero-harness', 'publication.json', 'publication.py', 'reference-side.jl', 'required-paths.json', 'review-initial.json', 'review.json', 'review.md', 'runtime-inputs-complete.json', 'seal.py', 'source-check.json', 'source-check.py', 'stages.json', 'supervisor.py', 'tests-extended.json', 'tests-extended.py', 'tests.json', 'tests.py', 'tests.py.initial']
def main():
 names=sorted(str((D/n).relative_to(R)) for n in BASENAMES);target=str((D/'publication.json').relative_to(R));actual=[n for n in names if n!=target]
 require(git('rev-parse','HEAD')==ENTRY and git('rev-parse','master')==MASTER,'Refs drift')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Existing edits/index')
 require({str(p.relative_to(R)) for p in D.iterdir()}==set(actual) and all((R/n).is_file() and not (R/n).is_symlink() for n in actual),'Exact publication files')
 z=rd(D/'closure.json');require(z['all_passed'] is True and bindings(z),'Closure drift')
 preparation()
 subprocess.run(['git','add','--',*actual],cwd=R,check=True)
 require(git('diff','--cached','--name-only').splitlines()==actual,'Exact staged names')
 subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
 save(D/'publication.json',dict(all_passed=True,names=names,sha256={str(R/n):sha(R/n) for n in actual},blobs_except_self={n:git('hash-object','--',n) for n in actual},scope='Exact staged names and blobs before failfast commit/push; self blob verified after save'))
 subprocess.run(['git','add','--',target],cwd=R,check=True)
 require(git('diff','--cached','--name-only').splitlines()==names,'Final exact names')
 for n in names:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Exact staged blob')
 subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
 print(json.dumps(dict(all_passed=True,exact_staged_files=len(names))))
if __name__=='__main__':main()
