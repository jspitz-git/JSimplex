"""One-time OFFLINE source candidate; exact reversed edit ledger, no Julia."""
from common import *
import difflib
files=['options.jl','factorization.jl','triangular_factorization.jl','simplex_phase_one.jl','simplex_precision.jl','solver.jl','lp_refinement_driver.jl']
original={n:(R/'src'/n).read_text() for n in files};texts=dict(original);edits=[]
def edit(n,a,b):
 require(texts[n].count(a)==1,'Ambiguous source edit '+n+' '+a[:70])
 texts[n]=texts[n].replace(a,b);edits.append(dict(file='src/'+n,before=a,after=b))
# Options: appended field and exact legacy arity, no type parameter changes.
edit('options.jl','presolve=true, simplex_strategy=:legacy, partial_pricing=false)','presolve=true, simplex_strategy=:legacy, partial_pricing=false,\n                  native_pivot_policy=:default)')
edit('options.jl','domains. It defaults to `false` in both strategies.','''domains. It defaults to `false` in both strategies.
`native_pivot_policy=:threshold_one` selects pivot tolerance 1 and no iterative
refinement for managed native Float64 basis factors (PFI/FT/SS/BG). Default
`:default` retains existing controls. Intent survives precision conversion;
other precisions keep their existing arithmetic. Markowitz and Huangfu–Hall
reject the nondefault policy. Auxiliary raw LU safeguards retain their controls.
AUTO strategy and symmetric pivot tolerance remain unchanged; threshold one is
not a universal full-partial-pivot guarantee when AUTO selects SYMMETRIC.''')
edit('options.jl','    partial_pricing::Bool\nend','    partial_pricing::Bool\n    native_pivot_policy::Symbol\nend')
fields=['primal_tolerance','dual_tolerance','zero_tolerance','iteration_limit','time_limit','refactorization_interval','verbose','log_level','algorithm','pricing','basis_update','basis_refactorization','scaling','presolve','simplex_strategy','partial_pricing']
args=', '.join(fields)
edit('options.jl','SolverOptions(; kwargs...) = SolverOptions(Float64; kwargs...)',f'''# Preserve the original positional constructor's default policy.
SolverOptions{{T,M,R}}({args}) where {{T,M,R}} =
    SolverOptions{{T,M,R}}({args}, :default)

SolverOptions(; kwargs...) = SolverOptions(Float64; kwargs...)''')
edit('options.jl','    presolve::Bool=true, simplex_strategy::Symbol=:legacy, partial_pricing::Bool=false,','    presolve::Bool=true, simplex_strategy::Symbol=:legacy, partial_pricing::Bool=false,\n    native_pivot_policy::Symbol=:default,')
edit('options.jl','                 algorithm, pricing, scaling, presolve, simplex_strategy, partial_pricing)','                 algorithm, pricing, scaling, presolve, simplex_strategy, partial_pricing, native_pivot_policy)')
edit('options.jl','                            pricing, scaling, presolve, simplex_strategy, partial_pricing) where {T,M,R}','                            pricing, scaling, presolve, simplex_strategy, partial_pricing,\n                            native_pivot_policy::Symbol=:default) where {T,M,R}')
edit('options.jl','    M === :huangfu_hall && _validate_huangfu_hall(T, Val(R))','''    native_pivot_policy in (:default, :threshold_one) ||
        throw(ArgumentError("native_pivot_policy must be :default or :threshold_one"))
    native_pivot_policy === :threshold_one &&
        !(R === :native && M in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)) &&
        throw(ArgumentError("threshold_one requires native PFI/FT/SS/BG basis factors"))
    M === :huangfu_hall && _validate_huangfu_hall(T, Val(R))''')
edit('options.jl','                              algorithm, pricing, M, R, scaling, presolve, simplex_strategy, partial_pricing)','                              algorithm, pricing, M, R, scaling, presolve, simplex_strategy, partial_pricing, native_pivot_policy)')
edit('options.jl','                       options.pricing, options.scaling, options.presolve, options.simplex_strategy, options.partial_pricing)','                       options.pricing, options.scaling, options.presolve, options.simplex_strategy, options.partial_pricing, options.native_pivot_policy)')
# Native lifetime selection is separate from solve arithmetic.
edit('factorization.jl','mutable struct UMFPACKBackend','''@enum _NativePivotPolicy::UInt8 _NATIVE_PIVOT_DEFAULT _NATIVE_PIVOT_ONE

function _native_pivot_policy(value::Symbol)::_NativePivotPolicy
    value === :default && return _NATIVE_PIVOT_DEFAULT
    value === :threshold_one && return _NATIVE_PIVOT_ONE
    throw(ArgumentError("native_pivot_policy must be :default or :threshold_one"))
end

function _native_lu(B::SparseMatrixCSC{Float64,Int}, policy::_NativePivotPolicy)::Float64UMFPACK
    policy === _NATIVE_PIVOT_DEFAULT && return lu(B)
    control = SparseArrays.UMFPACK.get_umfpack_control(Float64, Int)
    control[SparseArrays.LibSuiteSparse.UMFPACK_PIVOT_TOLERANCE + 1] = 1.0
    control[SparseArrays.LibSuiteSparse.UMFPACK_IRSTEP + 1] = 0.0
    return lu(B; control)
end

mutable struct UMFPACKBackend''')
edit('factorization.jl','    spare::Union{Nothing,Float64UMFPACK}\n    shared::Bool\nend','    spare::Union{Nothing,Float64UMFPACK}\n    shared::Bool\n    const pivot_policy::_NativePivotPolicy\nend')
edit('factorization.jl','    UMFPACKBackend(factorization, dimension, nothing, false)','''    UMFPACKBackend(factorization, dimension, nothing, false, _NATIVE_PIVOT_DEFAULT)

# Legacy raw-factor wrappers do not certify caller-supplied control values.
UMFPACKBackend(factorization::Union{Nothing,Float64UMFPACK}, dimension::Int,
               spare::Union{Nothing,Float64UMFPACK}, shared::Bool) =
    UMFPACKBackend(factorization, dimension, spare, shared, _NATIVE_PIVOT_DEFAULT)''')
edit('factorization.jl','function _factorize_basis(B::AbstractMatrix{Float64})','''_factorize_basis(B::AbstractMatrix{Float64}) =
    _factorize_basis(B, Val(:native), _NATIVE_PIVOT_DEFAULT)

function _factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)''')
edit('factorization.jl','    return iszero(rows) ? UMFPACKBackend(nothing, 0) : UMFPACKBackend(lu(sparse_basis), rows)','''    factor = iszero(rows) ? nothing : _native_lu(sparse_basis, policy)
    return UMFPACKBackend(factor, rows, nothing, false, policy)''')
edit('factorization.jl','_factorize_basis(B::AbstractMatrix, ::Val{:native}) = _factorize_basis(B)','''_factorize_basis(B::AbstractMatrix, ::Val{:native}) = _factorize_basis(B)
_factorize_basis(B::AbstractMatrix, ::Val{:native}, ::_NativePivotPolicy) =
    _factorize_basis(B)
function _factorize_basis(B::AbstractMatrix, ::Val{:markowitz}, policy::_NativePivotPolicy)
    policy === _NATIVE_PIVOT_DEFAULT ||
        throw(ArgumentError("Markowitz does not support a native pivot policy"))
    return _factorize_basis(B, Val(:markowitz))
end''')
edit('factorization.jl','function PFIFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}','''PFIFactorization(B::AbstractMatrix{T}, backend::Val) where {T<:Real} =
    PFIFactorization(B, backend, _NATIVE_PIVOT_DEFAULT)

function PFIFactorization(B::AbstractMatrix{T}, ::Val{R}, policy::_NativePivotPolicy) where {T<:Real,R}''')
edit('factorization.jl','    base = _factorize_basis(B, Val(R))','    base = _factorize_basis(B, Val(R), policy)')
edit('factorization.jl','        candidate = lu(sparse_basis)','        candidate = _native_lu(sparse_basis, backend.pivot_policy)')
edit('factorization.jl','    return UMFPACKBackend(backend.factorization, backend.dimension, nothing, true)','    return UMFPACKBackend(backend.factorization, backend.dimension, nothing, true, backend.pivot_policy)')
edit('factorization.jl','_basis_factorization(B, ::SolverOptions{T,M,R}) where {T,M,R} =\n    _basis_factorization(B, Val(M), Val(R))','''_basis_factorization(B, ::Val{:pfi}, backend::Val, policy::_NativePivotPolicy) =
    PFIFactorization(B, backend, policy)
function _basis_factorization(B, mode::Val, backend::Val, policy::_NativePivotPolicy)
    policy === _NATIVE_PIVOT_DEFAULT ||
        throw(ArgumentError("native pivot policy requires PFI/FT/SS/BG"))
    return _basis_factorization(B, mode, backend)
end
_basis_factorization(B, options::SolverOptions{T,M,R}) where {T,M,R} =
    _basis_factorization(B, Val(M), Val(R), _native_pivot_policy(options.native_pivot_policy))''')
for manager,mode in [('ForrestTomlinFactorization','forrest_tomlin'),('SuhlSuhlFactorization','suhl_suhl'),('BartelsGolubFactorization','bartels_golub')]:
 a=f'function {manager}(B::AbstractMatrix{{T}}, ::Val{{R}}) where {{T<:Real,R}}\n    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))\n    base = _factorize_basis(B, Val(R))'
 b=f'''{manager}(B::AbstractMatrix{{T}}, backend::Val) where {{T<:Real}} =
    {manager}(B, backend, _NATIVE_PIVOT_DEFAULT)
_basis_factorization(B, ::Val{{:{mode}}}, backend::Val, policy::_NativePivotPolicy) =
    {manager}(B, backend, policy)

function {manager}(B::AbstractMatrix{{T}}, ::Val{{R}}, policy::_NativePivotPolicy) where {{T<:Real,R}}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B, Val(R), policy)'''
 edit('triangular_factorization.jl',a,b)
for n in ['simplex_phase_one.jl','simplex_precision.jl','lp_refinement_driver.jl']:
 edit(n,'o.simplex_strategy,o.partial_pricing)','o.simplex_strategy,o.partial_pricing,o.native_pivot_policy)')
edit('solver.jl','algorithm, options.pricing, options.scaling, options.presolve, options.simplex_strategy, options.partial_pricing)','algorithm, options.pricing, options.scaling, options.presolve, options.simplex_strategy, options.partial_pricing, options.native_pivot_policy)')
for n in files:
 s=texts[n]
 for e in reversed([e for e in edits if e['file']=='src/'+n]):
  require(s.count(e['after'])==1,'Ambiguous inverse '+n);s=s.replace(e['after'],e['before'])
 require(s==original[n],'Inverse mismatch '+n)
 target=Q/'candidate/src'/n;target.parent.mkdir(exist_ok=True,parents=True)
 with target.open('x') as f:f.write(texts[n])
with (Q/'candidate.patch').open('x') as f:
 for n in files:f.writelines(difflib.unified_diff(original[n].splitlines(True),texts[n].splitlines(True),fromfile='a/src/'+n,tofile='b/src/'+n))
save(Q/'inverse.json',dict(edits=edits,original={str(R/'src'/n):sha(R/'src'/n) for n in files},candidate={str(Q/'candidate/src'/n):sha(Q/'candidate/src'/n) for n in files},scope='Exact string edits reversed to entire original files; not Julia syntax/dispatch/runtime proof'))
save(Q/'prepare.json',dict(all_passed=True,files=len(files),edits=len(edits),tests_written_first=True,sha256={str(f):sha(f) for f in [Path(__file__),Q/'inverse.json',Q/'candidate.patch',Q/'candidate/test/native_pivot_policy_tests.jl',Q/'candidate/test/native_pivot_policy_entry.jl',Q/'red-contract.jl']},scope='OFFLINE only; no Julia'))
print(dict(all_passed=True,files=len(files),edits=len(edits)))
