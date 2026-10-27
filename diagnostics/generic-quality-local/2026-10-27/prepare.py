from pathlib import Path
import json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');S=D/'baseline/src'
s=(S/'simplex_numerics.jl').read_text();start=s.index('function _componentwise_backward_error(');i=s.index('function solve_quality!');end=s.index('\nend',i)+5;quality=s[start:end]+'\n\n'
p=(S/'primal_updates.jl').read_text();i=p.index('function _audit_primal_values!');j=p.index('\nend',i)+5;audit=p[i:j]+'\n\n'
a0=s[s.index('@inline function _bigfloat_quality_term!'):s.index('function _quality_components!(r::Vector{BigFloat}')]
a1=a0.replace('    scale[target] += _primal_direction_magnitude(product)','    magnitude = _primal_direction_magnitude(product)\n    scale[target] += magnitude').replace('return _primal_direction_magnitude(product) < limit, limit','return magnitude < limit, limit')
b0=s[s.index('function _componentwise_backward_error('):s.index('_quality_values(B::AbstractMatrix)')]
b1=b0.replace('function _componentwise_backward_error(residual::AbstractVector{T}, scale) where {T<:AbstractFloat}','function _componentwise_backward_error(residual::Vector{BigFloat}, scale::Vector{BigFloat})\n    T = BigFloat').replace('r, s = abs(residual[i]), scale[i]','r, s = _primal_direction_magnitude(residual[i]), scale[i]').replace('s >= zero(s)','s >= Clong(0)')
r0=s[s.index('function _quality_roundoff('):s.index('function _floating_quality!')]
r1=r0.replace('function _quality_roundoff(::Type{W}, terms) where {W<:AbstractFloat}','function _quality_roundoff(::Type{BigFloat}, terms)\n    W = BigFloat').replace('product < one(W)','product < Clong(1)').replace('(one(W)-product)','(Clong(1)-product)')
f0=s[s.index('function _floating_quality!'):s.index('_stored_quality_bits(::Type{T}')]
f1=f0.replace('function _floating_quality!(scratch::SolveQualityScratch{T}, r, scale, terms, policy) where {T}','function _floating_quality!(scratch::SolveQualityScratch{T}, r::Vector{BigFloat},\n                            scale::Vector{BigFloat}, terms::Vector{Int}, policy) where {T}').replace('maximum(abs,r;','maximum(_primal_direction_magnitude,r;')
c1=audit.replace('function _audit_primal_values!(ws::SimplexWorkspace{T})::Symbol where T','function _audit_primal_values!(ws::SimplexWorkspace{BigFloat})::Symbol\n    T = BigFloat').replace('        for i in eachindex(predicted)','        unit = tolerance\n        unit_ready = false\n        for i in eachindex(predicted)',1).replace('                scale = max(one(T), abs(old), abs(current))','                if !unit_ready\n                    unit = one(T)\n                    unit_ready = true\n                end\n                scale = max(unit, _primal_direction_magnitude(old), _primal_direction_magnitude(current))').replace('abs(old / scale - current / scale)','_primal_direction_magnitude(old / scale - current / scale)')
header='''using JSimplex,SparseArrays
using JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,
    _is_exact,_compensated_solve_quality!,_primal_direction_magnitude,
    _with_recovery_precision,_finite_workspace,_recomputed_basis_reliable,
    _primal_price_prediction_reliable,recompute!
'''
versions={'Reference':quality+audit,'CandidateA':quality.replace(a0,a1)+audit,'CandidateB':quality+b1+r1+f1+audit,'CandidateAB':quality.replace(a0,a1)+b1+r1+f1+audit,'CandidateC':quality+audit+c1}
for name,body in versions.items():(D/(name+'.jl')).write_text('module Local'+name+'\n'+header+body+'end\n')
changes={'A':dict(file='simplex_numerics.jl',old=a0,new=a1),'B':dict(file='simplex_numerics.jl',old='function _stored_quality_bits(::Type{BigFloat}',new='function _stored_quality_bits(::Type{BigFloat}')}
# Append BF methods before stored-bits declaration while retaining generic methods byteexact.
marker='_stored_quality_bits(::Type{T}, B, x, rhs, policy) where {T<:AbstractFloat} = precision(T)'
changes['B']=dict(file='simplex_numerics.jl',old=marker,new=b1+r1+f1+marker)
changes['C']=dict(file='primal_updates.jl',old='# Validate all predicted prices before publishing any of them.',new=c1+'# Validate all predicted prices before publishing any of them.')
(D/'changes.json').write_text(json.dumps(changes,indent=2)+'\n');shutil.copyfile(__file__,D/'prepare.py');print('Five independent exact namespaces plus A/B/AB/C substitutions prepared')
