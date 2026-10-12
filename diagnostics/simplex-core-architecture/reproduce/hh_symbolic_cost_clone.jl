_s4m_refactor_lu!(F::Float64UMFPACK,B)=
    lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B)))
_s4m_refactor_lu!(F::LinearAlgebra.LU,B)=_hh_native_lu(B)

function _s4m_refactor_backend(F,B,::Val{:native})
    size(B,1)==0 && return nothing
    (isnothing(F) || size(F)!=size(B)) && return _hh_native_lu(B)
    return _s4m_refactor_lu!(F,B)
end
_s4m_refactor_backend(F,B,::Val{:markowitz}) =
    isnothing(F) ? MarkowitzBackend(B) : _refactorize_backend(F,B)

function _s4m_refactorize!(f::HuangfuHallFactorization{T,FType,R},B::AbstractMatrix{T}) where {T,FType,R}
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=f.refactor_workspace
    local base, work, auxiliary, prepared_partial, prepared_direction
    try
        # Extracted L/U own their storage; failed backend construction cannot
        # damage the active factors or copies. Preserve backend choice on retry.
        F=_s4m_refactor_backend(F,B,Val(R))
        # Borrow only disposable solve scratch, never the prepared direction.
        work=length(f.work)==n ? f.work : zeros(T,n)
        auxiliary=length(f.auxiliary)==n ? f.auxiliary : zeros(T,n)
        base=_hh_extract_base(F,work,auxiliary,f.extract_workspace)
        # New dimensions must release obsolete private backing storage. Prepare
        # all references before publication; valid prepared data survives failure.
        prepared_partial=length(f.prepared_partial)==n ? f.prepared_partial : Vector{T}(undef,n)
        prepared_direction=length(f.prepared_direction)==n ? f.prepared_direction : Vector{T}(undef,n)
    catch
        f.refactor_workspace=nothing
        rethrow()
    end
    # Retire only the private suffix, and only after the candidate LU is valid.
    if length(f.work)==n
        for k in (f.shared_update_count+1):length(f.updates)
            t=f.updates[k]
            _hh_retire_pair!(f.u_pool,t.u_indices,t.u_values)
            _hh_retire_pair!(f.v_pool,t.v_indices,t.v_values)
        end
    else
        empty!(f.u_pool.pairs);f.u_pool.entries=0
        empty!(f.v_pool.pairs);f.v_pool.entries=0
    end
    n==0 && (f.extract_workspace=HHExtractWorkspace())
    f.shared_update_count=0
    f.base=base;f.refactor_workspace=F
    f.work=work;f.auxiliary=auxiliary
    f.prepared_partial=prepared_partial;f.prepared_direction=prepared_direction
    if length(f.unit_workspace.values)!=n
        f.unit_workspace=HHUnitWorkspace(n,T)
    end
    empty!(f.updates);f.prepared_valid=false
    f
end
