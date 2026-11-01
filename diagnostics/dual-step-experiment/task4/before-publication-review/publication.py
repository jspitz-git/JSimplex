from pathlib import Path
import json,subprocess,hashlib
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task4'
def git(*a):return subprocess.check_output(['git','-C',str(W),*a])
def require(v,m):
 if not v:raise ValueError(m)
require(not git('diff','--cached','--name-only').strip(),'index not empty')
require(json.loads((D/'closure.json').read_text())['accepted'] is True,'PASS closure')
required={str(p.relative_to(W)) for p in D.rglob('*') if p.is_file()}
required|={'diagnostics/dual-step-experiment/README.md','experimental/dual_engine/ExperimentalDualEngine.jl','experimental/dual_engine/invariants.jl','experimental/dual_engine/kernels.jl','experimental/dual_engine/proposal.jl','experimental/dual_engine/ratio.jl','experimental/dual_engine/state.jl','experimental/dual_engine/types.jl','experimental/dual_engine/commit.jl','experimental/dual_engine/recovery.jl','experimental/dual_engine/test/commit_fixtures.jl','experimental/dual_engine/test/commit_tests.jl','experimental/dual_engine/test/recovery_tests.jl','experimental/dual_engine/test/task4_runtests.jl'}
selfname=str((D/'publication.json').relative_to(W));require(selfname not in required,'publication already exists')
record=dict(scope='exact local Task4 commit only; no push/master change',names=sorted(required|{selfname}),blobs_excluding_self={n:git('hash-object','--',n).decode().strip() for n in sorted(required)},closure_sha256=hashlib.sha256((D/'closure.json').read_bytes()).hexdigest())
with (D/'publication.json').open('x') as f:json.dump(record,f,indent=2)
git('add','--',*record['names'])
actual=git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0');require(actual==record['names'],'exact stage names')
blobs={n:git('rev-parse',':'+n).decode().strip() for n in actual};require(all(blobs[n]==h for n,h in record['blobs_excluding_self'].items()),'exact staged blobs')
subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True)
with Path('/tmp/task4-exact-staged.json').open('x') as f:json.dump(dict(names=actual,blobs=blobs),f,indent=2)
print(json.dumps(dict(accepted=True,exact_staged_names_and_blobs=len(actual),publication_blob=blobs[selfname])))
