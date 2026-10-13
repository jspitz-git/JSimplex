from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd(); D=R/'diagnostics/simplex-core-architecture/results/S2-C'; B=D.parent/'S2-B'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((B/'closure.json').read_text()); assert old['all_passed']
assert all(sha(Path(p))==h for p,h in old['sha256'].items())
for p,n in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-S2-C'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-S2-C')]:put(n,(R/p).read_text())
s=(R/'src/primal_updates.jl').read_text(); put('original-primal-updates.jl',s)
helper='''# Borrow only nonempty, concrete hardware vectors for this synchronous audit.
# Empty parents must be materialized: scratch alias checks ignore empty arrays.
struct _PriceAuditValues{T<:Union{Float32,Float64}} <: AbstractVector{T}
    dual::Vector{T}
    predicted::Vector{T}
    function _PriceAuditValues(dual::Vector{T}, predicted::Vector{T}) where {T<:Union{Float32,Float64}}
        (T === Float32 || T === Float64) ||
            throw(ArgumentError("price audit borrowing requires a concrete hardware type"))
        (isempty(dual) || isempty(predicted)) &&
            throw(ArgumentError("price audit borrowing requires nonempty parents"))
        return new{T}(dual, predicted)
    end
end
Base.size(v::_PriceAuditValues) = (length(v.dual) + length(v.predicted),)
Base.IndexStyle(::Type{<:_PriceAuditValues}) = IndexLinear()
@inline function Base.getindex(v::_PriceAuditValues, i::Int)
    @boundscheck checkbounds(v, i)
    split = length(v.dual)
    return i <= split ? v.dual[i] : v.predicted[i-split]
end
Base.dataids(v::_PriceAuditValues) = (Base.dataids(v.dual)..., Base.dataids(v.predicted)...)

_price_audit_values(dual, predicted) = vcat(dual, predicted)
function _price_audit_values(dual::Vector{Float32}, predicted::Vector{Float32})
    (isempty(dual) || isempty(predicted)) && return vcat(dual, predicted)
    return _PriceAuditValues(dual, predicted)
end
function _price_audit_values(dual::Vector{Float64}, predicted::Vector{Float64})
    (isempty(dual) || isempty(predicted)) && return vcat(dual, predicted)
    return _PriceAuditValues(dual, predicted)
end

'''
anchor='function _primal_price_prediction_reliable(ws::SimplexWorkspace{T},predicted) where T\n'; oldline='    values = vcat(ws.scratch.rho,predicted)\n'; newline='    values = _price_audit_values(ws.scratch.rho,predicted)\n'
assert s.count(anchor)==s.count(oldline)==1
c=s.replace(anchor,helper+anchor).replace(oldline,newline)
assert c.replace(helper,'',1).replace(newline,oldline)==s
put('adapter.jl.txt',helper); put('candidate-primal-updates.jl',c)
t=(R/'test/primal_update_tests.jl').read_text(); start=t.index('function price_audit_workspace('); end=t.index('@testset "Unreliable or infeasible audited pivots still roll back atomically"')
put('integration-original.jl',t[start:end]); put('integration-binding.json',json.dumps({'source':'test/primal_update_tests.jl','source_sha256':sha(R/'test/primal_update_tests.jl'),'start_byte':len(t[:start].encode()),'end_byte':len(t[:end].encode()),'slice_sha256':sha(D/'integration-original.jl'),'scope':'helper plus three unchanged testsets, UNEXECUTED'},indent=2)+'\n')
print('Prepared exact source inverse and integration extraction; NO Julia.')
