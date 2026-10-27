from pathlib import Path
import json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');S=D/'baseline/src'
def block(file,start,end):
 s=(S/file).read_text();return s[s.index(start):s.index(end,s.index(start))]
a1=block('dual_simplex.jl','function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},\n                                      direction::Vector{T}, pivot::T) where {T<:BigFloat}','# The entering direction')
a0=block('dual_simplex.jl','function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},\n                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}','function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},\n                                      direction::Vector{T}, pivot::T) where {T<:BigFloat}')
a2=block('dual_simplex.jl','function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},','function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},\n                                  rho::Vector{T}, leaving_row::Int) where {T<:BigFloat}')
a3=block('dual_simplex.jl','function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},\n                                  rho::Vector{T}, leaving_row::Int) where {T<:BigFloat}','# A fresh floating LU')
b1=block('simplex_numerics.jl','@inline function _accumulate_quality_term!','function _quality_roundoff')
b2=block('simplex_numerics.jl','function _wide_solve_quality!','"""Evaluate an absolute residual')
b3=block('simplex_numerics.jl','function solve_quality!','function _refine_basis_solution!') if 'function _refine_basis_solution!' in (S/'simplex_numerics.jl').read_text() else None
# End is identified by the next top-level declaration, not by parsing Julia.
s=(S/'simplex_numerics.jl').read_text();i=s.index('function solve_quality!');j=s.index('\nend',i)+5;b3=s[i:j]+'\n\n'
c1=block('primal_simplex.jl','_primal_devex_candidate_weight(coefficient::T','function _primal_steepest_weight!')
c2=block('primal_simplex.jl','function _primal_update_devex!','_primal_relaxed_step')
extra='''# A call-local comparison limit is shared only across ordinary array accesses.
@inline function _bigfloat_quality_term!(r, scale, terms, x, a, row, column,
                                         transposed, limit::Union{Nothing,BigFloat})
    target, source = transposed ? (column,row) : (row,column)
    product = BigFloat(a)*BigFloat(x[source])
    r[target] -= product
    scale[target] += _primal_direction_magnitude(product)
    terms[target] += 2
    if !iszero(a) && !iszero(x[source])
        if limit === nothing
            limit = floatmin(BigFloat)
        end
        return _primal_direction_magnitude(product) < limit, limit
    end
    return false, limit
end

function _quality_components!(r::Vector{BigFloat}, scale::Vector{BigFloat},
                              terms::Vector{Int},
                              B::Union{Matrix{BigFloat},SparseMatrixCSC{BigFloat}},
                              x::Vector{BigFloat}, rhs::Vector{BigFloat}, transposed)
    for i in eachindex(rhs)
        r[i] = BigFloat(rhs[i])
        scale[i] = _primal_direction_magnitude(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    limit::Union{Nothing,BigFloat} = nothing
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B.nzval[p],
                B.rowval[p],column,transposed,limit)
            unsafe_range |= unsafe
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B[row,column],
                row,column,transposed,limit)
            unsafe_range |= unsafe
        end
    end
    return unsafe_range
end

'''
newc='''_primal_devex_candidate_weight(coefficient::BigFloat,leaving_weight::BigFloat) = begin
    product = _primal_direction_magnitude(coefficient) * leaving_weight
    isinf(product) && !signbit(product) ? floatmax(BigFloat) : product
end
'''
oldc=c1[c1.index('_primal_devex_candidate_weight(coefficient::BigFloat'):]
header='''using JSimplex,SparseArrays
using JSimplex: SimplexWorkspace,_pipeline_changed!,_primal_direction_magnitude,
    SolveQualityScratch,NumericalPolicy,SolveQuality,_stored_quality_bits,
    _quality_roundoff,_quality_values,_is_exact,_compensated_solve_quality!,
    _floating_quality!,_primal_store_rational_weight,_primal_devex_leaving_weight,
    _pipeline_unit_rhs!,_checked_basis_solve!,price!,BASIC
'''
ref=a0+a1+a2+a3+b1+b2+b3+c1+c2
cand=a0+a1.replace('abs(','_primal_direction_magnitude(')+a2+a3.replace('abs(','_primal_direction_magnitude(')+b1+extra+b2+b3+c1.replace(oldc,newc)+c2
(D/'reference.jl').write_text('module SavingsReference\n'+header+ref+'end\n')
(D/'candidate.jl').write_text('module SavingsCandidate\n'+header+cand+'end\n')
(D/'changes.json').write_text(json.dumps({'A1':{'file':'dual_simplex.jl','old':a1,'new':a1.replace('abs(','_primal_direction_magnitude(')},'A2':{'file':'dual_simplex.jl','old':a3,'new':a3.replace('abs(','_primal_direction_magnitude(')},'B':{'file':'simplex_numerics.jl','old':'function _quality_roundoff','new':extra+'function _quality_roundoff'},'C':{'file':'primal_simplex.jl','old':oldc,'new':newc}},indent=2)+'\n')
shutil.copyfile(__file__,D/'prepare.py')
print('private exact reference and separate candidate prepared')
