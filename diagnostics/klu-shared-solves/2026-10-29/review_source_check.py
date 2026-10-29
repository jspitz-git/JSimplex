from pathlib import Path
import json,hashlib,re,tomllib,subprocess
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-shared-solves/2026-10-29');W=D.parents[2]
files={};checks=[]
def read(p):
 p=Path(p); b=p.read_bytes();files[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
r=read(W/'src/simplex_recovery.jl');p=read(W/'src/simplex_precision.jl');f=read(W/'src/factorization.jl');t=read(W/'src/triangular_factorization.jl');s=read(W/'src/simplex.jl');q=read(W/'src/simplex_numerics.jl')
for name,src,start,construct,recompute,weight in [('recovery',r,'function _recovery_trial','_basis_factorization(B,ws.options)','recompute!(trial','_rebuild_recovery_weights!(trial'),('precision transfer',p,'function _transfer_precision','_basis_factorization(B,options)','recompute!(fresh','_rebuild_recovery_weights!(fresh')]:
 z=src[src.index(start):];ck(z.index(construct)<z.index(recompute)<z.index(weight),name+' fresh construction/recompute/rebuild order')
calls=[(str(x),i+1) for x in (W/'src').glob('*.jl') for i,line in enumerate(x.read_text().splitlines()) if '_rebuild_recovery_weights!(' in line and not line.startswith('function ')]
ck(len(calls)==2 and {Path(x).name for x,i in calls}=={'simplex_recovery.jl','simplex_precision.jl'},'exact two production recovery-weight callsites')
z=r[r.index('function _rebuild_recovery_weights!'):r.index('function _basis_primal_rhs')]
ck('_weight_pricing(trial,:dual) == :steepest_edge || return true' in z,'conditional steepest edge rebuild')
markers=['for row in 1:m','stop() && return false','fill!(rhs,zero(T))','rhs[row] = one(T)','transpose_solve!(direction,trial.factorization,rhs)','refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true)','dot(direction,direction)','isfinite(weight) && weight > zero(T)','max(_typed_ratio(T,1,10^4),weight)']
ck([z.index(m) for m in markers]==sorted(z.index(m) for m in markers),'original per-row unit/stop/refinement/norm/floor safeguards')
z=f[f.index('function transpose_solve!(destination::Vector{T}, factor::PFIFactorization'):];ck(z.index('Iterators.reverse(factor.updates)')<z.index('_backend_transpose_solve!'),'PFI transformed work reaches backend')
z=t[t.index('function _finish_triangular_transpose!'):];ck(z.index('_apply_dense_transposed_row_updates!')<z.index('_backend_transpose_solve!'),'triangular row history before full backend')
ck('base, PackedEta{T}[], zeros(T, size(B, 1)), PackedEta{T}[], 0, nothing' in f,'PFI constructor has empty history')
for name in ['ForrestTomlin','SuhlSuhl','BartelsGolub']:
 z=t[t.index('function '+name+'Factorization(B::AbstractMatrix{T}, ::Val{R}, policy::_NativePivotPolicy)'):];z=z[:z.index('\nend')]
 ck((('_identity_upper(T, n, Val(:stable))' if name=='BartelsGolub' else '_identity_upper(T, n)') in z) and name+'Update{T}[]' in z,'fresh '+name+' identity/history')
ck('B = _basis_matrix!(ws)' in r and 'saved_rhs = copyto!(buffers.rhs,rhs)' in r and 'solve_quality!(quality_scratch,B,destination,saved_rhs,policy;transposed)' in r,'every refinement assembles/validates current B and computes quality')
ck('fill!(is_basic, false)' in s and 'for index in eachindex(basis.states)' in s and 'copyto!(values' in s,'basis validation/state scan and assembly copy present')
ck('_quality_finite_values(_quality_values(B))' in q and '_quality_components!' in q and '_wide_solve_quality!' in q,'quality includes basis scan/residual and wider recovery path')
c=read('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-chain-cost/reproduce/capture.jl')
z=c[c.index('tape=('):c.index('serialize(file,tape)')]
ck(all(x in z for x in ['A=data.A','basis=data.basis','steps=data.steps','source_sha256']) and all(x not in z for x in ['eta','direction','rhs=']),'captured tape schema lacks backend RHS/update coefficient vectors')
w=read(W/'diagnostics/klu-ftran/2026-10-29/vendor/KLU/src/KLU.jl');ck('$sort(klu._symbolic, klu._numeric, Ref(klu.common))' in w,'wrapper combined extract sorts')
so=read(D/'upstream/klu_sort.c');ex=read(D/'upstream/klu_extract.c');ts=read(D/'upstream/klu_tsolve.c')
ck(len(re.findall(r'= KLU_malloc \(',so))==4 and so.rindex('= KLU_malloc (')<so.index('for (block = 0'),'exact four sort workspace allocation requests outside block loop')
ck(all(x not in ex for x in ['KLU_malloc','KLU_calloc','KLU_realloc']),'extract has no explicit allocation request')
ck('X [k] = Bz  [Q [k]]' in ts and 'for (block = 0 ; block < nblocks ; block++)' in ts and 'for (chunk = 0 ; chunk < nrhs ; chunk += 4)' in ts,'upstream transpose Q seed/block order/four-RHS implementation')
for x in json.loads(read(D/'upstream-provenance.json')):ck(hashlib.sha256((D/x['path']).read_bytes()).hexdigest()==x['sha256'],'saved release source hash '+x['path'])
ck(subprocess.check_output(['git','diff','--name-only','08dfda4b25bb1d014fd9d4c8781b1a83f46c8cd8','--','src'],cwd=W,text=True)=='','no production source diff from diagnostic baseline')
old=json.loads((D/'review-bindings.json').read_text())
for name,h in old['files'].items():ck(hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,'review preservation '+name)
for name,h in old['witnesses'].items():
 with Path(name).open('rb') as fd:ck(hashlib.file_digest(fd,'sha256').hexdigest()==h,'review witness preservation '+name)
(D/'review-source-checks.json').open('x').write(json.dumps(dict(accepted=True,checks=checks,readtime_source_sha256=files,scope='Independent literal source/preservation review, no runtime allocation inference or installed library build proof'),indent=2)+'\n')
(D/'review_check.py').open('x').write(Path('/tmp/klu_shared_independent_review.py').read_text())
(D/'review_source_check.py').open('x').write(Path(__file__).read_text())
print(json.dumps(dict(accepted=True,source_and_preservation_checks=len(checks),readtime_source_files=len(files))))
