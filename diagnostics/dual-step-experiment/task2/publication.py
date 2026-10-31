from pathlib import Path
import json,subprocess,hashlib
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task2'
def git(*args):return subprocess.check_output(['git','-C',str(W),*args])
def require(v,m):
 if not v:raise ValueError(m)
require(not git('diff','--cached','--name-only').strip(),'index not empty')
require(json.loads((D/'closure.json').read_text())['accepted'] is True,'closure')
required={str(p.relative_to(W)) for p in D.rglob('*') if p.is_file()}
required|={'diagnostics/dual-step-experiment/README.md','experimental/dual_engine/ExperimentalDualEngine.jl','experimental/dual_engine/state.jl','experimental/dual_engine/types.jl','experimental/dual_engine/kernels.jl','experimental/dual_engine/test/kernel_fixtures.jl','experimental/dual_engine/test/kernel_tests.jl','experimental/dual_engine/test/task2_runtests.jl'}
selfname=str((D/'publication.json').relative_to(W));require(selfname not in required,'publication record already exists')
record=dict(scope='exact Task2 local commit only; no push/master change',names=sorted(required|{selfname}),blobs_excluding_self={n:git('hash-object','--',n).decode().strip() for n in sorted(required)},closure_sha256=hashlib.sha256((D/'closure.json').read_bytes()).hexdigest())
with (D/'publication.json').open('x') as f:json.dump(record,f,indent=2)
git('add','--',*record['names'])
actual=git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0')
require(actual==record['names'],'stage names mismatch')
blobs={n:git('rev-parse',':'+n).decode().strip() for n in actual}
require(all(blobs[n]==h for n,h in record['blobs_excluding_self'].items()),'stage blob mismatch')
subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True)
with Path('/tmp/task2-exact-staged.json').open('x') as f:json.dump(dict(names=actual,blobs=blobs),f,indent=2)
print(json.dumps(dict(accepted=True,exact_staged_names_and_blobs=len(actual),publication_blob=blobs[selfname])))
