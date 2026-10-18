# UNEXECUTED Task2 candidate. Appended to the frozen ordinary JSimplex stage.
# No production type or method is replaced. Float64 packed DIRECT BG only.
mutable struct BGExportFactor{I}
    inner::I
    workspace::Union{Nothing,BGExportWorkspace}
    busy::Bool
end
# Setup has no live inner yet. This single-field cold owner is not retained.
mutable struct _BGXBuildOwner
    workspace::Union{Nothing,BGExportWorkspace}
end
function _bgx_input(B::AbstractMatrix{Float64},::Val{R},policy::_NativePivotPolicy) where R
    ((R===:native && policy===_NATIVE_PIVOT_ONE) ||
     (R===:markowitz && policy===_NATIVE_PIVOT_DEFAULT)) ||
        throw(ArgumentError("BG export workspace requires native threshold_one or Markowitz default"))
    B isa SparseMatrixCSC && !(B isa SparseMatrixCSC{Float64,Int}) &&
        throw(ArgumentError("BG export workspace requires Int CSC indices"))
    nothing
end
function _bgx_build(B::AbstractMatrix{Float64},backend::Val{R},policy::_NativePivotPolicy,
                    normalize::Bool,owner;factorize=_factorize_basis,export_parts=_bgx_export,
                    import_upper=_bgx_import_upper,allocate=_bgx_allocate,
                    make_inner=_init_direct_manager) where R
    _bgx_input(B,backend,policy)
    ordinary=factorize(B,backend,policy)
    parts=export_parts(ordinary,owner;allocate)
    F=typeof(ordinary)
    if isnothing(parts)
        _bgx_drop!(owner)
        n=_backend_dimension(ordinary)
        base=DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,
                                    normalize,policy,ordinary,Float64[])
        upper=_identity_upper(Float64,n,Val(:stable))
        return make_inner(BartelsGolubFactorization,base,upper,collect(1:n))
    end
    upper,D=import_upper(parts.upper,normalize;allocate)
    base=DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,
                                D,normalize,policy,nothing,zeros(length(parts.rows)))
    return make_inner(BartelsGolubFactorization,base,upper,parts.columns)
end
function _bgx_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy;
                     normalize::Bool=true)
    owner=_BGXBuildOwner(nothing)
    try
        inner=_bgx_build(B,backend,policy,normalize,owner)
        return BGExportFactor(inner,owner.workspace,false)
    catch
        _bgx_drop!(owner)
        rethrow()
    end
end
function _bgx_check_inner(active,candidate)
    typeof(candidate)===typeof(active) || throw(ArgumentError("BG export refactorization type changed"))
    nothing
end
function _bgx_refactor_with!(f::BGExportFactor,B::AbstractMatrix{Float64};
        factorize=_factorize_basis,export_parts=_bgx_export,import_upper=_bgx_import_upper,
        allocate=_bgx_allocate,make_inner=_init_direct_manager,check_inner=nothing)
    f.busy && throw(ArgumentError("BG export workspace is busy"))
    f.busy=true
    try
        base=f.inner.base
        candidate=_bgx_build(B,Val(_direct_requested_backend(base)),base.pivot_policy,
            base.normalize_requested,f;factorize,export_parts,import_upper,allocate,make_inner)
        isnothing(check_inner) || check_inner(f.inner,candidate)
        # One mandatory guard, also after any diagnostic hook.
        _bgx_check_inner(f.inner,candidate)
        f.inner=candidate
        return f
    catch
        _bgx_drop!(f)
        rethrow()
    finally
        f.busy=false
    end
end
function _bgx_copy(f::BGExportFactor)
    f.busy && throw(ArgumentError("BG export workspace is busy"))
    # Original inner copy marks its source's shared update prefix, as before.
    BGExportFactor(copy_basis_factorization(f.inner),nothing,false)
end

# Exact dense diagnostic surface. No indexed/kernel_mode or other scalar adapter.
forward_solve!(out::Vector{Float64},f::BGExportFactor,rhs::Vector{Float64})=
    forward_solve!(out,f.inner,rhs)
transpose_solve!(out::Vector{Float64},f::BGExportFactor,
                 rhs::Union{Vector{Float64},_UnitTransposeRHS{Float64}})=
    transpose_solve!(out,f.inner,rhs)
_ordinary_forward_solve!(out::Vector{Float64},f::BGExportFactor,rhs::Vector{Float64})=
    _ordinary_forward_solve!(out,f.inner,rhs)
forward_solve(f::BGExportFactor,rhs::Vector{Float64})=forward_solve(f.inner,rhs)
transpose_solve(f::BGExportFactor,rhs::Vector{Float64})=transpose_solve(f.inner,rhs)
_unit_transpose_rhs(f::BGExportFactor,rhs::Vector{Float64},row::Int)=_unit_transpose_rhs(f.inner,rhs,row)
_copy_prepared_spike!(f::BGExportFactor,direction::Vector{Float64})=_copy_prepared_spike!(f.inner,direction)
function replace_column!(f::BGExportFactor,direction::Vector{Float64},row::Integer;
                         zero_tolerance::Real=_positive_tolerance(Float64,1//10^12))
    replace_column!(f.inner,direction,row;zero_tolerance)
    f
end
refactorize!(f::BGExportFactor,B::AbstractMatrix{Float64})=_bgx_refactor_with!(f,B)
copy_basis_factorization(f::BGExportFactor)=_bgx_copy(f)
_direct_mode(f::BGExportFactor)=_direct_mode(f.inner)
_backend_dimension(f::BGExportFactor)=_backend_dimension(f.inner.base)
_factor_storage_count(f::BGExportFactor)=_factor_storage_count(f.inner)
_factor_growth_measure(f::BGExportFactor)=_factor_growth_measure(f.inner)
_factor_growth_reference(f::BGExportFactor)=_factor_growth_reference(f.inner)
_finite_updated_factor(f::BGExportFactor)=_finite_updated_factor(f.inner)
