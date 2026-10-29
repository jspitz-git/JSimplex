from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def require(v,m):
 if not v:raise ValueError(m)
 checks.append(m)
def text(p):return (W/p).read_text()
def section(s,start,end):return s[s.index(start):s.index(end,s.index(start)+len(start))]
s=text('src/simplex_recovery.jl');fresh=section(s,'function _recovery_trial','function _rebuild_recovery_weights!');weights=section(s,'function _rebuild_recovery_weights!','function _basis_primal_rhs')
require(fresh.index('_basis_factorization(B,ws.options)')<fresh.index('recompute!(trial')<fresh.index('_rebuild_recovery_weights!(trial'),'recovery path constructs then recomputes then rebuilds')
pr=text('src/simplex_precision.jl');transfer=section(pr,'function _transfer_precision','function ',) if False else pr[pr.index('function _transfer_precision'):]
require(transfer.index('_basis_factorization(B,options)')<transfer.index('recompute!(fresh')<transfer.index('_rebuild_recovery_weights!(fresh'),'precision transfer path fresh factor before rebuild')
calls=[]
for p in (W/'src').glob('*.jl'):
 for line in p.read_text().splitlines():
  if '_rebuild_recovery_weights!(' in line and not line.startswith('function '):calls.append(str(p.relative_to(W)))
require(sorted(calls)==['src/simplex_precision.jl','src/simplex_recovery.jl'],'exact two production caller files')
require('_weight_pricing(trial,:dual) == :steepest_edge || return true' in weights,'weight reconstruction conditional dual steepest_edge')
needles=['for row in 1:m','stop() && return false','fill!(rhs,zero(T))','rhs[row] = one(T)','transpose_solve!(direction,trial.factorization,rhs)','refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true)','weight = dot(direction,direction)','isfinite(weight) && weight > zero(T)','max(_typed_ratio(T,1,10^4),weight)']
positions=[weights.index(q)for q in needles];require(positions==sorted(positions),'unit solve quality norm safeguards and original floor ordered')
f=text('src/factorization.jl');pfi=section(f,'function transpose_solve!(destination::Vector{T}, factor::PFIFactorization','function transpose_solve(factor::PFIFactorization')
require(pfi.index('for eta in Iterators.reverse(factor.updates)')<pfi.index('_backend_transpose_solve!'),'PFI history before actual backend RHS')
t=text('src/triangular_factorization.jl');finish=section(t,'function _finish_triangular_transpose!','function _unit_transpose_rhs')
require(finish.index('_apply_dense_transposed_row_updates!')<finish.index('_backend_transpose_solve!'),'ordinary triangular row history before backend')
for name,upd in [('ForrestTomlin','ForrestTomlinUpdate'),('SuhlSuhl','SuhlSuhlUpdate'),('BartelsGolub','BartelsGolubUpdate')]:
 start='function '+name+'Factorization(B::AbstractMatrix{T}, ::Val{R}, policy::_NativePivotPolicy)';q=section(t,start,'\nend')
 require('_identity_upper(T, n)' in q and upd+'{T}[]' in q,'fresh '+name+' identity upper and empty history')
q=text('src/simplex.jl');bm=section(q,'function _basis_matrix!','\n# A zero primal step');validate=section(q,'function _validate_basis','function basis_matrix')
require('_validate_basis(workspace)' in bm and '_assemble_basis_matrix(workspace, storage)' in bm and 'copyto!(values' in bm,'quality basis assembly is real validation and value copy')
require('fill!(is_basic, false)' in validate and 'for index in eachindex(basis.states)' in validate,'basis validation scans working variable states')
quality=section(s,'function _refine_basis_solve!','function _maybe_refine_basis_solve!')
require('solve_quality!(quality_scratch,B,destination,saved_rhs,policy;transposed)' in quality and 'quality_scratch.residual' in quality,'quality and optional corrections remain full current B checks')
wrapper=(W/'diagnostics/klu-ftran/2026-10-29/vendor/KLU/src/KLU.jl').read_text();require('$sort(klu._symbolic, klu._numeric, Ref(klu.common))' in wrapper,'combined wrapper extraction includes native sorting')
sort=(D/'upstream/klu_sort.c').read_text();require(len(re.findall(r'= KLU_malloc \(',sort))==4 and sort.index('W  = KLU_malloc')<sort.index('for (block = 0'),'matching upstream sort has four allocation requests outside block loop')
extract=(D/'upstream/klu_extract.c').read_text();require('KLU_malloc' not in extract and 'KLU_calloc' not in extract and 'KLU_realloc' not in extract,'matching upstream extraction contains no explicit allocation call')
for n in ['source-bindings.json','source-bindings-addendum.json']:
 for path,h in json.loads((D/n).read_text())['files'].items():
  with Path(path).open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest()
  require(d==h,'source binding '+path)
for p in json.loads((D/'upstream-provenance.json').read_text()):require(hashlib.sha256((D/p['path']).read_bytes()).hexdigest()==p['sha256'],'upstream source bytes '+p['path'])
(D/'source-checks.json').write_text(json.dumps(dict(accepted=True,checks=checks,scope='literal source contracts and readtime hashes; no runtime inference/allocation attribution'),indent=2)+'\n');print(json.dumps({'accepted':True,'source_checks':len(checks)}))
