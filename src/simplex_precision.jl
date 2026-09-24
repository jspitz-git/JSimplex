_working_value_bits(::Real) = 0
_working_value_bits(value::AbstractFloat) = precision(value)
_working_value_bits(bound::Bound) = isfinite(bound) ? _working_value_bits(bound_value(bound)) : 0
_working_value_bits(values::AbstractArray) = maximum(_working_value_bits,values;init=0)
_working_value_bits(values::SparseMatrixCSC) = _working_value_bits(values.nzval)
_working_value_bits(::Nothing) = 0

function _working_value_bits(bounds::BoundPerturbationState)
    return max(_working_value_bits(bounds.original_lower),_working_value_bits(bounds.original_upper),
        _working_value_bits(bounds.active_lower),_working_value_bits(bounds.active_upper))
end

function _working_value_bits(journal::PerturbationJournal)
    return max(_working_value_bits(journal.original_costs),_working_value_bits(journal.active_costs),
        _working_value_bits(journal.bounds))
end

_precision_scalar_type(::Type{T}) where T = T
_precision_scalar_type(::Type{Bound{T}}) where T = T

function _check_precision_types(::Type{T},::Type{S},bits) where {T,S}
    _supported_value_type(T) && _supported_value_type(S) ||
        throw(ArgumentError("Unsupported working precision transfer"))
    if T <: Rational || S <: Rational
        T <: Rational && S <: Rational ||
            throw(ArgumentError("Working precision transfer must not convert exact arithmetic to floating point or back"))
        bits >= 0 || throw(ArgumentError("Negative exact working precision"))
    else
        bits >= 2 || throw(ArgumentError("Working precision must be at least two bits"))
        S === BigFloat || (T !== BigFloat && precision(S) >= precision(T)) ||
            throw(ArgumentError("Working precision transfer must not narrow stored floating values"))
    end
    return nothing
end

_with_transfer_precision(f,::Type{T},bits) where T = f()
_with_transfer_precision(f,::Type{BigFloat},bits) = setprecision(f,BigFloat,bits)
_copy_precision_scalar(::Type{S},value::Real) where S = S(value)
_copy_precision_scalar(::Type{BigFloat},value::Real) = BigFloat(value;precision=precision(BigFloat))
function _copy_precision_scalar(::Type{BigFloat},value::BigFloat)
    copied = BigFloat(value;precision=precision(BigFloat))
    # Julia returns the same BigFloat when its precision already matches.
    return copied === value ? deepcopy(value) : copied
end
_copy_precision_scalar(::Type{S},bound::Bound) where S =
    isfinite(bound) ? Bound(_copy_precision_scalar(S,bound_value(bound))) : Bound{S}(nothing)

_copy_working_values(::Type{S},values::AbstractArray) where S =
    map(value->_copy_precision_scalar(S,value),values)
function _copy_working_values(::Type{S},values::SparseMatrixCSC) where S
    return SparseMatrixCSC(size(values,1),size(values,2),copy(values.colptr),
        copy(values.rowval),_copy_working_values(S,values.nzval))
end

"""Copy stored numeric values into independently owned working storage.

Increasing floating precision preserves the stored binary model, not hypothetical
decimal input. BigFloat copies retain at least the highest stored input precision,
even in a lower ambient context. Exact arithmetic never crosses into floating point.
"""
function copy_working_values(::Type{S},values::AbstractArray;bits::Int) where S
    T = _precision_scalar_type(eltype(values))
    _check_precision_types(T,S,bits)
    actual_bits = max(bits,_working_value_bits(values))
    return _with_transfer_precision(S,actual_bits) do
        _copy_working_values(S,values)
    end
end

function _transfer_bits(ws,policy,bits)
    p,progress,o = ws.problem,ws.progress,ws.options
    return max(bits,_working_value_bits(p.A),_working_value_bits(p.objective),
        _working_value_bits(p.objective_constant),_working_value_bits(p.column_lower),
        _working_value_bits(p.column_upper),_working_value_bits(p.row_lower),
        _working_value_bits(p.row_upper),_working_value_bits(ws.costs),
        _working_value_bits(ws.lower),_working_value_bits(ws.upper),
        _working_value_bits(progress.objective),_working_value_bits(progress.objective_constant),
        _working_value_bits(progress.scaling.row_factors),_working_value_bits(progress.scaling.column_factors),
        _working_value_bits(o.primal_tolerance),_working_value_bits(o.dual_tolerance),
        _working_value_bits(o.zero_tolerance),_working_value_bits(policy.solve_tolerance),
        _working_value_bits(policy.pivot_error_tolerance),_working_value_bits(ws.scratch.perturbations))
end

function _copy_precision_policy(::Type{S},policy::NumericalPolicy) where S
    return NumericalPolicy{S}(_copy_precision_scalar(S,policy.solve_tolerance),
        _copy_precision_scalar(S,policy.pivot_error_tolerance),
        ntuple(i->getfield(policy,i+2),Val(fieldcount(typeof(policy))-2))...)
end

function _copy_precision_options(::Type{S},o::SolverOptions{T,M,R}) where {S,T,M,R}
    return SolverOptions{S,M,R}(_copy_precision_scalar(S,o.primal_tolerance),
        _copy_precision_scalar(S,o.dual_tolerance),_copy_precision_scalar(S,o.zero_tolerance),
        o.iteration_limit,o.time_limit,o.refactorization_interval,o.verbose,o.log_level,
        o.algorithm,o.pricing,o.basis_update,o.basis_refactorization,o.scaling,o.presolve,o.simplex_strategy)
end

function _copy_precision_problem(::Type{S},p) where S
    return LinearProblem{S}(_copy_working_values(S,p.A),_copy_working_values(S,p.objective),
        _copy_precision_scalar(S,p.objective_constant),p.objective_sense,
        _copy_working_values(S,p.row_lower),_copy_working_values(S,p.row_upper),
        _copy_working_values(S,p.column_lower),_copy_working_values(S,p.column_upper),
        copy(p.variable_domains),p.name,copy(p.row_names),copy(p.column_names))
end

function _copy_precision_progress(::Type{S},p,policy,budget) where S
    scaling = Scaling(_copy_working_values(S,p.scaling.row_factors),
        _copy_working_values(S,p.scaling.column_factors))
    return SimplexProgressContext{S,typeof(p.diagnostics)}(budget.start_ns,
        _copy_working_values(S,p.objective),_copy_precision_scalar(S,p.objective_constant),
        scaling,p.iteration_offset,p.refactorization_offset,p.diagnostics,policy)
end

function _check_transfer_journal(ws,journal)
    isnothing(journal) && return nothing
    _check_perturbation_owner(ws,journal)
    journal.active && journal.active_costs != ws.costs &&
        throw(ArgumentError("Active perturbation costs disagree with the working model"))
    bounds = journal.bounds
    if !isnothing(bounds) && bounds.active
        bounds.active_lower == ws.lower && bounds.active_upper == ws.upper ||
            throw(ArgumentError("Active perturbation bounds disagree with the working model"))
    end
    return nothing
end

_copy_precision_bounds(::Type,::Nothing) = nothing
function _copy_precision_bounds(::Type{S},b::BoundPerturbationState) where S
    return BoundPerturbationState{S}(_copy_working_values(S,b.original_lower),
        _copy_working_values(S,b.original_upper),_copy_working_values(S,b.active_lower),
        _copy_working_values(S,b.active_upper),b.active,b.level,nothing,0,b.cooldown_until)
end

_copy_precision_journal!(fresh,::Nothing) = nothing
function _copy_precision_journal!(fresh::SimplexWorkspace{S},j::PerturbationJournal) where S
    # Histories refer to the old model/factor. Retain bounded attempts and cooldowns,
    # but require fresh observations before any further perturbation.
    copied = PerturbationJournal{S}(objectid(fresh),_copy_working_values(S,j.original_costs),
        _copy_working_values(S,j.active_costs),j.original_perturbed,j.active,j.level,
        nothing,0,j.cooldown_until,_copy_precision_bounds(S,j.bounds))
    if copied.active
        fresh.costs = copied.active_costs
    end
    if !isnothing(copied.bounds) && copied.bounds.active
        fresh.lower = copied.bounds.active_lower
        fresh.upper = copied.bounds.active_upper
    end
    fresh.scratch.perturbations = copied
    return nothing
end

function _transfer_basis_matrix(problem::LinearProblem{S},basis,lower,upper,stop) where S
    m,n = size(problem.A)
    length(basis.basic_indices) == m && length(basis.states) == m+n ||
        throw(ArgumentError("Transferred basis dimensions do not match the working model"))
    mask = falses(m+n)
    for j in basis.basic_indices
        1 <= j <= m+n && !mask[j] || throw(ArgumentError("Invalid or duplicate transferred basis index"))
        mask[j] = true
    end
    for j in eachindex(basis.states)
        state = basis.states[j]
        (state == BASIC) == mask[j] || throw(ArgumentError("Transferred basis states disagree with its indices"))
        state == BASIC && continue
        valid = state == AT_LOWER ? isfinite(lower[j]) : state == AT_UPPER ? isfinite(upper[j]) :
            state == FREE_NONBASIC && !isfinite(lower[j]) && !isfinite(upper[j])
        valid || throw(ArgumentError("Transferred nonbasic state refers to invalid bounds"))
    end
    # Assemble only selected sparse columns; never materialize [A, -I] or an
    # unrelated slack factor before constructing the actual transferred basis.
    pointers,rows,values = Int[1],Int[],S[]
    for j in basis.basic_indices
        stop() && return nothing
        if j <= n
            for k in nzrange(problem.A,j)
                push!(rows,problem.A.rowval[k]);push!(values,problem.A.nzval[k])
            end
        else
            push!(rows,j-n);push!(values,-one(S))
        end
        push!(pointers,length(values)+1)
    end
    return SparseMatrixCSC(m,m,pointers,rows,values)
end

function _transfer_precision(ws,::Type{S},budget,policy,stop) where S
    problem = _copy_precision_problem(S,ws.problem)
    stop() && return nothing
    options = _copy_precision_options(S,ws.options)
    converted_policy = _copy_precision_policy(S,policy)
    progress = _copy_precision_progress(S,ws.progress,converted_policy,budget)
    costs,lower,upper = _copy_working_values(S,ws.costs),_copy_working_values(S,ws.lower),_copy_working_values(S,ws.upper)
    basis = Basis(ws.basis.basic_indices,ws.basis.states)
    B = _transfer_basis_matrix(problem,basis,lower,upper,stop)
    (isnothing(B) || stop()) && return nothing
    factor = try
        _diagnostic_kernel(progress.diagnostics,:refactorization) do
            _basis_factorization(B,options)
        end
    finally
        # Attempted factors consume work even when construction throws.
        ws.refactorizations += 1
        _sync_run_budget!(budget,ws)
    end
    stop() && return nothing
    m,n = size(problem.A)
    fresh = SimplexWorkspace(problem,options,progress,costs,lower,upper,basis,
        zeros(S,m+n),zeros(S,m+n),ones(S,m+n),falses(m+n),factor,SimplexScratch(S,m,m+n),
        (getfield(ws,key) for key in _PIVOT_STATE_SCALARS)...)
    fresh.scratch.basis_matrix = B
    fresh.dual_nonzero_steps_since_refactorization = 0
    _copy_precision_journal!(fresh,ws.scratch.perturbations)
    _configure_refactorization!(fresh)
    recompute!(fresh;caller_guard=stop)
    stop() && return nothing
    _finite_workspace(fresh) && _recomputed_basis_reliable(fresh) || throw(_UnreliableBasisSolve())
    reset_devex!(fresh)
    _rebuild_recovery_weights!(fresh,stop) || throw(_UnreliableBasisSolve())
    stop() && return nothing
    _simplex_event!(fresh,:refactor_other)
    stop() && return nothing
    return fresh
end

"""Rebuild a verified, independently owned workspace at a nondecreasing precision.

The original workspace retains its numerical state and all consumed work. The
shared budget/clock and original progress/scaling context survive the transfer.
Return `nothing` on cancellation; invalid bases and numerical construction failures
throw without discarding attempted factorization counts. This operation does not
claim optimality or change the public solution's scalar type.
"""
function transfer_precision(ws::SimplexWorkspace{T},::Type{S},bits::Int,
                            budget::SimplexRunBudget,policy::NumericalPolicy{T};
                            stop=()->false) where {T,S}
    _check_precision_types(T,S,bits)
    guard = _guard_stop_callback(()->_budget_expired(budget) || stop())
    ws.iterations = max(ws.iterations,budget.iterations-ws.progress.iteration_offset)
    ws.refactorizations = max(ws.refactorizations,budget.refactorizations-ws.progress.refactorization_offset)
    try
        guard() && return nothing
        _check_transfer_journal(ws,ws.scratch.perturbations)
        actual_bits = _transfer_bits(ws,policy,bits)
        guard() && return nothing
        return _with_transfer_precision(S,actual_bits) do
            _transfer_precision(ws,S,budget,policy,guard)
        end
    catch exception
        exception === guard.exception && rethrow()
        _crash_numerical_exception(exception) && guard() && return nothing
        rethrow()
    finally
        _sync_run_budget!(budget,ws)
    end
end
