"""One-shot text-only repair preparation; no Julia/parser/import/numerics."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
C=R/'diagnostics/direct-lu-markowitz/reproduce';A=D.parent/'DIRECT-LU-ADMISSION';P=D.parent/'DIRECT-LU-CORRECTNESS'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
    with p.open('x') as f:f.write(s)
def save(p,x):put(p,json.dumps(x,indent=2)+'\n')
def req(x,s):
    if not x:raise ValueError(s)
req(json.loads((D/'host.json').read_text())['matches']==[],'Host not clean')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
mappings=[]
for source,name in ((status,'STATUS.md.before-repair'),(roadmap,'roadmap.md.before-repair')):
    (D/name).write_bytes(source.read_bytes())
    for record in ('review.json','closure.json','publication.json'):
        data=json.loads((P/record).read_text())
        key=str(source) if record=='review.json' else str(source.relative_to(R))
        req(data['sha256'][key]==sha(source),'Prior continuation mismatch')
        mappings.append(dict(record=str((P/record).relative_to(R)),key=key,preserved_path=str((D/name).relative_to(R)),sha256=sha(source)))
save(D/'continuation.json',dict(mappings=mappings,older_mappings='Unchanged; this mapping applies only to DIRECT-LU-CORRECTNESS current continuation bindings.'))
old='                    lu!(backend.factorization,sparse(2.0*B))'
new='''                    # Preserve explicit stored zeros for symbolic reuse. The fixture
                    # and both exported factors must remain independently owned.
                    refactor_input = copy(B)
                    refactor_input.nzval .*= 2.0
                    @test refactor_input.colptr == B.colptr
                    @test refactor_input.rowval == B.rowval
                    @test all(a !== b for (a,b) in zip(
                        (refactor_input.colptr,refactor_input.rowval,refactor_input.nzval),owners))
                    @test all(isequal(refactor_input.nzval[k],2.0*B.nzval[k]) for k in eachindex(B.nzval))
                    lu!(backend.factorization,refactor_input)
                    @test issuccess(backend.factorization)'''
original=(C/'correctness.jl').read_text();req(original.count(old)==1,'Unique test replacement')
put(D/'correctness.jl',original.replace(old,new))
driver=(A/'driver.jl').read_text()
replacements=[('Base.invokelatest(run_direct_lu_red)','Base.invokelatest(() -> getfield(Main,:run_direct_lu_red)())'),('(\"exports\",:test_exports,100)','(\"exports\",:test_exports,130)'),('Base.invokelatest(getfield(Main,fn))','Base.invokelatest(() -> getfield(Main,fn)())')]
corrected=driver
for before,after in replacements:
    req(corrected.count(before)==1,'Unique driver replacement: '+before);corrected=corrected.replace(before,after)
put(D/'driver.jl',corrected)
save(D/'replacements.json',dict(test=dict(old=old,new=new),driver=[dict(old=a,new=b) for a,b in replacements]))
roots=['diagnostics/direct-lu-markowitz','diagnostics/simplex-core-architecture/results/DIRECT-LU-PREPARATION','diagnostics/simplex-core-architecture/results/DIRECT-LU-ADMISSION','diagnostics/simplex-core-architecture/results/DIRECT-LU-CORRECTNESS','docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md','docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md']
names=subprocess.check_output(['git','ls-files','--',*roots],cwd=R,text=True).splitlines()
save(D/'frozen-inputs.json',dict(sha256={n:sha(R/n) for n in names},scope='Current read-time evidence, not new or retroactive launch pins'))
print(json.dumps(dict(frozen_files=len(names),test_sha256=sha(D/'correctness.jl'),driver_sha256=sha(D/'driver.jl'),continuation_mappings=len(mappings))))
