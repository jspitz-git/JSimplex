"""One-shot OFFLINE preparation, no Julia, imports of historical tools, or stage."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'NATIVE-PIVOT-PREPARATION'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def require(x,m):
 if not x:raise RuntimeError(m)
old=json.loads((P/'overlay-manifest.json').read_text());entries=old['candidate']
require(len(entries)==75,'Original overlay size')
for e in entries:require(sha(e['source'])==e['sha256'],'Frozen input changed '+e['source'])
# Reuse exact accepted production candidate, do not rewrite frozen files.
newtest='test/native_pivot_integration_tests.jl';entries=entries+[dict(destination=newtest,source=str(D/'native_pivot_integration_tests.jl'),sha256=sha(D/'native_pivot_integration_tests.jl'))]
save(D/'overlay-manifest.json',dict(candidate=entries,scope='76 ordinary files. No stage created. Eventual permanent test entry is separate.'))
original=(R/'test/runtests.jl').read_bytes();needle=b'    include("options_tests.jl")\n'
require(original.count(needle)==1,'Test entry anchor')
replacement=needle+b'    include("native_pivot_policy_tests.jl")\n    include("native_pivot_integration_tests.jl")\n'
write(D/'candidate/test/runtests.jl',original.replace(needle,replacement))
save(D/'runtests-inverse.json',dict(path='test/runtests.jl',before=needle.decode(),after=replacement.decode(),original_sha256=sha(R/'test/runtests.jl'),candidate_sha256=sha(D/'candidate/test/runtests.jl'),scope='Eventual permanent inclusion only; full test entry is NOT selected by the future focused driver.'))
# Concrete future observer anchors: source text only, no executable stage yet.
f=(P/'candidate/src/factorization.jl').read_text();edits=[]
def add(before,after,count=1):
 require(f.count(before)==count,'Observer anchor cardinality')
 edits.append(dict(file='src/factorization.jl',before=before,after=after,count=count))
add('function _factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)\n','function _factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)\n    Main.NativePivotIntegrationProbe.enter!(:construct)\n')
add('    return UMFPACKBackend(factor, rows, nothing, false, policy)\n','    return Main.NativePivotIntegrationProbe.completed(:construct, UMFPACKBackend(factor, rows, nothing, false, policy))\n')
add('function _refactorize_backend(backend::UMFPACKBackend, B::AbstractMatrix{Float64})\n','function _refactorize_backend(backend::UMFPACKBackend, B::AbstractMatrix{Float64})\n    Main.NativePivotIntegrationProbe.enter!(:refactor)\n')
# Keep return anchors scoped to this method, two returns including empty branch.
a=f.index('function _refactorize_backend(backend::UMFPACKBackend,');b=f.index('\nfunction _recycle_pfi_updates!',a)
block=f[a:b];require(block.count('return backend')==2,'Refactor returns')
edits.append(dict(file='src/factorization.jl',before=block,after=block.replace('return backend','return Main.NativePivotIntegrationProbe.completed(:refactor, backend)'),count=1,apply_before_other_edits=True))
for direction,spaces in [('forward',33),('transpose',35)]:
 before=f'function _backend_{direction}_solve!(destination::Vector, backend::UMFPACKBackend,\n'+(' '*spaces)+'rhs::StridedVector)\n'
 add(before,before+f'    Main.NativePivotIntegrationProbe.enter!(:{direction})\n')
save(D/'observer-seams.json',dict(edits=edits,application_order=[3,0,1,2,4,5],scope='UNIMPLEMENTED future driver hooks: managed native backend attempts and completed control checks only. No global method overwrite; reverse exact edits before admission.'))
# Source-only structural sensitivity, not Julia RED or behavior proof.
t=(D/'native_pivot_integration_tests.jl').read_text()
checks=dict(overlay75_unchanged=all(e==o for e,o in zip(entries[:75],old['candidate'])),overlay76=len(entries)==76,entry_inverse=(D/'candidate/test/runtests.jl').read_bytes().replace(replacement,needle)==original,public_one_call=t.count('result = solve(problem; options)')==1,recovery_one_call=t.count('trial = J._recovery_trial(')==1,no_restore_call='restore_checkpoint!' not in t,no_extra_basis_calls=all(x not in t for x in ['forward_solve','transpose_solve','refactorize!','_original_primal_feasible']),literal_oracles='[2.0, 2.0]' in t and '-10.0' in t,original_options='refactorization_interval=2, time_limit=5.0, iteration_limit=100' in t,private_controls='trial.factorization.base.factorization.control !== controls' in t,work_survives='old_refactors + 1' in t,refactor_observer_returns=block.count('return backend')==2)
source_names=['src/simplex.jl','src/simplex_recovery.jl','src/simplex_numerics.jl','src/solver.jl','src/triangular_factorization.jl','src/simplex_phase_one.jl','src/simplex_precision.jl','src/lp_refinement_driver.jl','src/dual_simplex.jl','src/primal_simplex.jl','src/simplex_driver.jl','src/precompile.jl','test/basis_recovery_tests.jl','test/runtests.jl']
files=[D/'prepare.py',D/'host.json',D/'native_pivot_integration_tests.jl',D/'overlay-manifest.json',D/'candidate/test/runtests.jl',D/'runtests-inverse.json',D/'observer-seams.json',P/'overlay-manifest.json',P/'inverse.json']+[R/n for n in source_names]+[Path(e['source']) for e in entries]
save(D/'source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in set(files)},scope='Literal source/inverse checks only; Julia parse, runtime, public trajectories and observer implementation UNQUALIFIED.'))
require(all(checks.values()),'Source checks failed; preserve');print(dict(checks=len(checks),bindings=len(set(files)),overlay=len(entries)))
