from pathlib import Path
import json,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27')
def fn(file,start):
 s=(D/'baseline/src'/file).read_text();a=s.index(start);b=s.index('\nend',a)+len('\nend\n');return s[a:b]
def need(x,m):
 if not x:raise RuntimeError(m)
virtual=fn('primal_updates.jl','function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix{T},')
price=fn('primal_updates.jl','function _primal_price_prediction_reliable(')
compensated=fn('primal_updates.jl','function _compensated_quality_components!(')
qsource=(D/'baseline/src/simplex_numerics.jl').read_text();quality=qsource[qsource.index('function _componentwise_backward_error('):qsource.index('\nend',qsource.index('function solve_quality!('))+len('\nend\n')]
enter_generic=fn('primal_simplex.jl','function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}\n')
enter=fn('primal_simplex.jl','function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T<:Union{BigFloat,Rational{BigInt}}}')
eligible=fn('simplex_pricing.jl','function _pool_primal_eligible(')
select=fn('simplex_pricing.jl','function select_pricing_candidate!(')
select_ws=fn('simplex_pricing.jl','function _select_workspace_pool!(')
summary_generic=fn('simplex.jl','function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}\n')
summary=fn('simplex.jl','function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T<:Union{BigFloat,Rational{BigInt}}}')
agree=fn('simplex_pivot.jl','function _pivot_agrees(')
validate=fn('simplex_pivot.jl','function validate_pivot!(')
A='''function _quality_components!(r::Vector{BigFloat},scale::Vector{BigFloat},
                               terms::Vector{Int},B::_PriceAuditMatrix{BigFloat},
                               x::Vector{BigFloat},rhs::Vector{BigFloat},transposed)
    for i in eachindex(rhs)
        r[i] = BigFloat(rhs[i])
        scale[i] = _primal_direction_magnitude(r[i])
        terms[i] = 1
    end
    A = B.matrix
    m,n = size(A)
    unsafe = false
    limit = nothing
    for j in axes(A,2), p in nzrange(A,j)
        term_unsafe,limit = _bigfloat_quality_term!(r,scale,terms,x,A.nzval[p],j,A.rowval[p],transposed,limit)
        unsafe |= term_unsafe
    end
    if m > 0
        negative_unit = -one(BigFloat)
        for i in 1:m
            term_unsafe,limit = _bigfloat_quality_term!(r,scale,terms,x,negative_unit,n+i,i,transposed,limit)
            unsafe |= term_unsafe
        end
    end
    if n+m > 0
        positive_unit = one(BigFloat)
        for i in 1:n+m
            term_unsafe,limit = _bigfloat_quality_term!(r,scale,terms,x,positive_unit,i,m+i,transposed,limit)
            unsafe |= term_unsafe
        end
    end
    return unsafe
end

'''
Benter=enter.replace('abs(reduced_cost) > tolerance','_primal_direction_magnitude(reduced_cost) > tolerance');need(Benter!=enter,'enter substitution')
Beligible=eligible.replace('abs(value) > tolerance','_primal_direction_magnitude(value) > tolerance');need(Beligible!=eligible,'pool substitution')
Bsummary=summary.replace('magnitude = abs(reduced_cost)','magnitude = _primal_direction_magnitude(reduced_cost)');need(Bsummary!=summary,'summary substitution')
Cagree=agree.replace('function _pivot_agrees(row_pivot, column_pivot, error_bound)::Bool','function _pivot_agrees(row_pivot::BigFloat, column_pivot::BigFloat, error_bound::BigFloat)::Bool').replace('zero(error_bound)','Clong(0)').replace('abs(row_pivot)','_primal_direction_magnitude(row_pivot)').replace('abs(column_pivot)','_primal_direction_magnitude(column_pivot)').replace('abs(row_pivot-column_pivot)','_primal_direction_magnitude(row_pivot-column_pivot)')
Cvalidate=validate.replace('function validate_pivot!(ws::SimplexWorkspace{T}, proposal::PivotCandidate{T},\n                         policy::NumericalPolicy{T})::Symbol where {T}', 'function validate_pivot!(ws::SimplexWorkspace{BigFloat}, proposal::PivotCandidate{BigFloat},\n                         policy::NumericalPolicy{BigFloat})::Symbol\n    T = BigFloat')
for old,new in [('abs(row_quality.residual[i]*proposal.column[i])','_primal_direction_magnitude(row_quality.residual[i]*proposal.column[i])'),('abs(column_quality.residual[i]*proposal.rho[i])','_primal_direction_magnitude(column_quality.residual[i]*proposal.rho[i])'),('abs(proposal.rho[i]*rhs[i])','_primal_direction_magnitude(proposal.rho[i]*rhs[i])'),('gamma < one(T)','gamma < Clong(1)')]:need(Cvalidate.count(old)==1,'one C site '+old);Cvalidate=Cvalidate.replace(old,new)
old='''    roundoff = gamma/(one(T)-gamma) *
        (dot_scale+abs(row_pivot)+abs(column_pivot))'''
new='''    roundoff_factor = gamma/(Clong(1)-gamma)
    row_magnitude = _primal_direction_magnitude(row_pivot)
    partial_scale = dot_scale+row_magnitude
    column_magnitude = _primal_direction_magnitude(column_pivot)
    roundoff = roundoff_factor*(partial_scale+column_magnitude)'''
need(Cvalidate.count(old)==1,'roundoff order');Cvalidate=Cvalidate.replace(old,new).replace('min(abs(row_pivot),abs(column_pivot))','min(row_magnitude,column_magnitude)')
changes=[dict(variant='A',file='primal_updates.jl',old='function _primal_price_prediction_reliable(',new=A+'function _primal_price_prediction_reliable('),dict(variant='B',file='primal_simplex.jl',old=enter,new=Benter),dict(variant='B',file='simplex_pricing.jl',old=eligible,new=Beligible),dict(variant='B',file='simplex.jl',old=summary,new=Bsummary),dict(variant='C',file='simplex_pivot.jl',old='struct _StageObserver{W}',new=Cagree+'\nstruct _StageObserver{W}'),dict(variant='C',file='simplex_pivot.jl',old=validate,new=validate+'\n'+Cvalidate)]
for v in changes:need((D/'baseline/src'/v['file']).read_text().count(v['old'])==1,'unique source replacement')
(D/'changes.json').write_text(json.dumps(changes,indent=2)+'\n')
imports='''using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,
    PivotCandidate,CandidatePool,VariableState,AT_LOWER,AT_UPPER,FREE_NONBASIC,BASIC,
    _is_exact,_compensated_solve_quality!,_primal_direction_magnitude,_PriceAuditMatrix,
    _prepare_auto_pricing!,_partial_pricing_enabled,_effective_pricing,
    _primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,
    _primal_weighted_score,_record_full_pricing!,_is_fixed,_pricing_pool!,
    _record_pricing_work!,_select_pool!,_pool_primal_score,_select_dual_pool!,
    _pivot_quality_buffers,_pivot_column!,_basis_matrix!,_sync_recovery_rejections!
'''
for arm in ['Reference','A','B','C']:
 parts=[quality,'_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)\n',compensated,virtual,A if arm=='A' else '',price,enter_generic,Benter if arm=='B' else enter,Beligible if arm=='B' else eligible,select,select_ws,summary_generic,Bsummary if arm=='B' else summary,agree,Cagree if arm=='C' else '',validate,Cvalidate if arm=='C' else '']
 (D/(arm+'.jl')).write_text('module VFP'+arm+'\n'+imports+'\n'+'\n'.join(parts)+'\nend\n')
(D/'source-clones.json').write_text(json.dumps(dict(accepted=True,baseline_only=True,clones={str(D/(a+'.jl')):hashlib.sha256((D/(a+'.jl')).read_bytes()).hexdigest() for a in ['Reference','A','B','C']},original_regions=dict(quality=quality,virtual=virtual,price=price,enter=enter,eligible=eligible,summary=summary,agree=agree,validate=validate)),indent=2)+'\n')
shutil.copyfile(__file__,D/'prepare.py');print('Four isolated source namespaces prepared, six reversible replacements, actual production untouched/noJulia')
