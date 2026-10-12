_s4i_refactor_lu!(F::Float64UMFPACK,B)=
    lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B)))
_s4i_refactor_lu!(F::LinearAlgebra.LU,B)=_hh_native_lu(B)

function _s4i_refactor_backend(F,B,::Val{:native})
    size(B,1)==0 && return nothing
    (isnothing(F) || size(F)!=size(B)) && return _hh_native_lu(B)
    return _s4i_refactor_lu!(F,B)
end
_s4i_refactor_backend(F,B,::Val{:markowitz}) =
    isnothing(F) ? MarkowitzBackend(B) : _refactorize_backend(F,B)

function _s4i_refactorize!(f::HuangfuHallFactorization{T,FType,R},B::AbstractMatrix{T}) where {T,FType,R}
    size(B,1)==size(B,2) || throw(DimensionMismatch("Basis must be square"))
    n=size(B,1);F=f.refactor_workspace
    local base, work, auxiliary, prepared_partial, prepared_direction
    try
        # Extracted L/U own their storage; failed backend construction cannot
        # damage the active factors or copies. Preserve backend choice on retry.
        F=_s4i_refactor_backend(F,B,Val(R))
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
function _s4i_recompute!(workspace::SimplexWorkspace{T}; refactorize::Bool=false,
                    caller_guard=nothing, diagnostic_reason::Symbol=:refactor_other) where {T}
    _validate_basis(workspace)
    _invalidate_pricing_pool!(workspace)
    if refactorize
        try
            @logmsg workspace.options.log_level "Refactorizing basis" iterations=workspace.iterations refactorizations=workspace.refactorizations + 1
        catch exception
            # A logger is caller code, even when it throws a numerical exception.
            # Share provenance with every enclosing numerical handler.
            isnothing(caller_guard) || (caller_guard.exception = exception)
            rethrow()
        end
        B = _basis_matrix!(workspace)
        _before_basis_refactor!(workspace,diagnostic_reason)
        _measure_basis_factorization!(workspace) do
            _timed_simplex(workspace, :refactorization) do
                _s4i_refactorize!(workspace.factorization, B)
            end
        end
        _after_basis_refactor!(workspace)
        workspace.refactorizations += 1
        _simplex_event!(workspace, diagnostic_reason)
        workspace.dual_nonzero_steps_since_refactorization = 0
        pricing = _weight_pricing(workspace,:dual)
        if pricing == :devex
            reset_devex!(workspace)
        end
        # Refactorization preserves the basis and its steepest-edge weights.
        # Auto still checks the selected weight against the fresh factor.
    end

    A = workspace.problem.A
    row_count, column_count = size(A)
    basis = workspace.basis
    is_basic = workspace.scratch.basic_mask
    rhs = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,rhs)
    fill!(rhs, zero(T))

    for index in eachindex(basis.states)
        is_basic[index] && continue
        value = _nonbasic_value(workspace, index)
        workspace.primal[index] = value
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                rhs[A.rowval[position]] -= A.nzval[position] * value
            end
        else
            rhs[index - column_count] += value
        end
    end

    basic_primal = _checked_basis_solve!(workspace.scratch.row_solution,
                                         workspace,rhs,caller_guard)
    _pipeline_changed!(workspace,rhs)
    for (row, index) in enumerate(basis.basic_indices)
        workspace.primal[index] = basic_primal[row]
        rhs[row] = workspace.costs[index]
    end

    dual = _checked_basis_solve!(workspace.scratch.rho,workspace,rhs,caller_guard;transposed=true)
    _recompute_reduced_costs!(workspace.reduced_costs, workspace, dual)
    if workspace.progress.numerical_policy.recovery && !workspace.scratch.recovery_active &&
       !_is_staged_workspace(workspace) && isempty(workspace.factorization.updates)
        _remember_verified_basis!(workspace,_basis_solve_stop(workspace,caller_guard))
    end
    refactorize && _report_simplex_progress(workspace, caller_guard)
    return workspace
end

