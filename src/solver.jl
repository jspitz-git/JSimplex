struct SolveContext
    start_ns::UInt64
    time_limit_seconds::Float64
end

elapsed_seconds(context::SolveContext) = (time_ns() - context.start_ns) / 1.0e9
time_limit_reached(context::SolveContext) =
    elapsed_seconds(context) >= context.time_limit_seconds

function _report_problem_statistics(stage::AbstractString, problem::LinearProblem,
                                    options::SolverOptions)
    options.verbose || return nothing
    rows, columns = size(problem.A)
    nonzeros = count(value -> !iszero(value), problem.A.nzval)
    return _report_problem_statistics(stage, rows, columns, nonzeros, options)
end

function _report_problem_statistics(stage::AbstractString, rows::Int, columns::Int,
                                    nonzeros::Int, options::SolverOptions)
    options.verbose || return nothing
    @info string(stage, ": rows=", rows, " columns=", columns, " nnz=", nonzeros)
    return nothing
end

function _finish_solve(::Type{T}, context::SolveContext, options::SolverOptions{T},
                       status::TerminationStatus, message::String;
                       primal=nothing, objective_value=nothing,
                       iterations::Int=0, refactorizations::Int=0) where {T<:Real}
    statistics = SolveStatistics(; iterations, refactorizations,
                                 elapsed_seconds=elapsed_seconds(context))
    @logmsg options.log_level "Solve terminated" status iterations refactorizations elapsed_seconds=statistics.elapsed_seconds
    return Solution{T}(status, objective_value, primal, statistics, message)
end

_negate_model_value(value::Real) = -value
_negate_model_value(value::BigFloat) = setprecision(BigFloat, precision(value)) do
    -value
end

function _minimization_problem(problem::LinearProblem{T}) where {T}
    problem.objective_sense == MIN_SENSE && return problem
    # Negation and the public BigFloat conversion constructor both use ambient
    # precision. A sense change must preserve each stored coefficient exactly.
    return LinearProblem{T}(
        problem.A, _negate_model_value.(problem.objective),
        _negate_model_value(problem.objective_constant), MIN_SENSE,
        problem.row_lower, problem.row_upper, problem.column_lower,
        problem.column_upper, problem.variable_domains, problem.name,
        problem.row_names, problem.column_names,
    )
end

_restored_objective(problem::LinearProblem{T}, primal::Vector{T}) where {T} =
    dot(problem.objective, primal) + problem.objective_constant

function cleanup_original(problem::LinearProblem{T}, restored_basis::Basis,
                          options::SolverOptions{T}, context::SolveContext,
                          prior_iterations::Int, prior_refactorizations::Int) where {T}
    stop_requested = _guard_stop_callback(() -> time_limit_reached(context))
    workspace = nothing
    try
        progress = SimplexProgressContext(problem; start_ns=context.start_ns)
        workspace = initialize_workspace(_minimization_problem(problem), options; progress)
        workspace.iterations = prior_iterations
        workspace.refactorizations = prior_refactorizations
        stop_requested() && return _internal_solution(workspace, TIME_LIMIT, "time limit reached")
        workspace.basis = Basis(restored_basis.basic_indices, restored_basis.states)
        recompute!(workspace; refactorize=true, caller_guard=stop_requested)
        return _solve_continuous_dual!(workspace, stop_requested)
    catch exception
        exception === stop_requested.exception && rethrow()
        _is_numerical_exception(exception) || rethrow()
        return DualRunResult{T}(NUMERICAL_ERROR, nothing, nothing,
                                isnothing(workspace) ? prior_iterations : workspace.iterations,
                                isnothing(workspace) ? prior_refactorizations : workspace.refactorizations,
                                sprint(showerror, exception))
    end
end

function _remaining_options(options::SolverOptions{T}; iterations::Int) where {T}
    return SolverOptions(T;
        primal_tolerance=options.primal_tolerance, dual_tolerance=options.dual_tolerance,
        zero_tolerance=options.zero_tolerance,
        iteration_limit=max(0, options.iteration_limit - iterations),
        time_limit=options.time_limit,
        refactorization_interval=options.refactorization_interval,
        verbose=options.verbose, log_level=options.log_level,
        algorithm=options.algorithm, pricing=options.pricing,
        basis_update=options.basis_update,
        basis_refactorization=options.basis_refactorization, scaling=options.scaling,
        presolve=options.presolve)
end

function _retry_original(problem::LinearProblem{T}, options::SolverOptions{T},
                         context::SolveContext, previous::DualRunResult{T}) where {T}
    time_limit_reached(context) &&
        return DualRunResult{T}(TIME_LIMIT, nothing, nothing, previous.iterations,
                                previous.refactorizations, "time limit reached")
    algorithm = options.algorithm == :dual ? _solve_continuous_dual : _solve_continuous_primal
    retry = algorithm(_minimization_problem(problem),
                      _remaining_options(options; iterations=previous.iterations);
                      stop_requested=() -> time_limit_reached(context),
                      progress=SimplexProgressContext(problem; start_ns=context.start_ns))
    return DualRunResult{T}(retry.status, retry.objective_value, retry.primal,
                            previous.iterations + retry.iterations,
                            previous.refactorizations + retry.refactorizations,
                            retry.message, retry.basis)
end

function _cleanup_or_retry_original(problem::LinearProblem{T}, basis::Basis,
                                    options::SolverOptions{T}, context::SolveContext,
                                    prior_iterations::Int,
                                    prior_refactorizations::Int) where {T}
    run = cleanup_original(problem, basis, options, context,
                           prior_iterations, prior_refactorizations)
    return run.status == NUMERICAL_ERROR ?
           _retry_original(problem, options, context, run) : run
end

function _restored_objective(problem::LinearProblem{BigFloat}, primal::Vector{BigFloat})
    working_precision = precision(BigFloat)
    if precision(problem.objective_constant) <= working_precision &&
       all(value -> precision(value) <= working_precision, problem.objective) &&
       all(value -> precision(value) <= working_precision, primal)
        return dot(problem.objective, primal) + problem.objective_constant
    end

    # A lower precision can lose stored objective bits before cancellation
    # with the constant. Require the entire exact-value enclosure to round to
    # one solve-precision value; otherwise the public objective is inconclusive.
    lower = upper = zero(BigFloat)
    for index in eachindex(primal)
        product_lower, product_upper = _primal_product_bounds(problem.objective[index], primal[index])
        lower, _ = _primal_sum_bounds(lower, product_lower)
        _, upper = _primal_sum_bounds(upper, product_upper)
    end
    lower, _ = _primal_sum_bounds(lower, problem.objective_constant)
    _, upper = _primal_sum_bounds(upper, problem.objective_constant)
    isfinite(lower) && isfinite(upper) || return nothing
    rounded_lower, rounded_upper = BigFloat(lower), BigFloat(upper)
    return rounded_lower == rounded_upper ? rounded_lower : nothing
end

"""
    solve(problem::LinearProblem{T}; relax_integrality=false, options=nothing)::Solution{T}

Solve an LP using dual simplex by default, or primal simplex with
`SolverOptions(algorithm=:primal)`. Discrete domains require explicit LP relaxation;
the input model remains unchanged. Only optimal results contain a primal vector
and objective value, expressed in the original structural variables and sense.
Every status returns `Solution{T}`, with objective data in `Union{Nothing,T}`
and primal data in `Union{Nothing,Vector{T}}`.

Presolve is enabled by default; `SolverOptions(presolve=false)` skips it. When
enabled, it removes fixed and redundant structure and skips a floating reduction
when transformed values cannot be represented safely. After postsolve, an optimal
reduced solution is cleaned up on the original continuous LP from its restored
basis, using the remaining time and iteration budget.

Floating models use reversible row and column scaling by default. Set
`SolverOptions(scaling=:off)` to disable it or `scaling=:on` to request it
explicitly. Rational models use identity scaling; `scaling=:on` is invalid for
them. The objective is not scaled as a whole. Progress objective values and
optimal results use original units; simplex tolerances apply in working units.

Omitted options create `SolverOptions(T)`; explicit options are converted and
validated through `SolverOptions(T, options)`, preserving supplied tolerance
values. Rational defaults, Harris pivot cutoffs, and recession-ray roundoff
allowances are exactly zero. Explicit nonzero rational tolerances are allowed;
passing `SolverOptions()` therefore differs from omitting options on an exact LP.

Float64 bases use sparse UMFPACK; other supported scalar types use generic dense LU
from `LinearAlgebra`. Dense BigFloat and rational solves are intended for small
models. Use `Rational{BigInt}` for arbitrary-size exact arithmetic; fixed-width
rationals retain Julia's ordinary overflow behavior, and those exceptions
propagate. For `BigFloat`, place both model construction and solve inside the
desired `setprecision` context. Internal transformations preserve stored values
and their precision; arithmetic uses the active solve precision. When objective
data or primal values have higher precision, the original objective is returned
only if its exact-value enclosure rounds to one value at the solve precision.
An inconclusive objective evaluation returns `NUMERICAL_ERROR`.

Without relaxation, any non-continuous domain returns `MIP_NOT_SUPPORTED`.
With relaxation, integer/binary domains retain their bounds and semi domains
use the convex hull of zero and their active interval. Supported algorithms are
`:dual` and `:primal`. Inspect `solution.status`, `solution.message`, and
`solution.statistics` for termination details; non-optimal results have
`nothing` for both `primal` and `objective_value`.

The monotonic time limit starts at entry; an expired deadline takes precedence
over algorithm selection and validation. Iteration limits count completed
simplex steps, including primal bound flips.
Time limits and elapsed seconds remain `Float64`; counters remain `Int`.
Deadline checks do not interrupt an in-progress numerical operation.

```julia
using JSimplex, SparseArrays
setprecision(BigFloat, 256) do
    problem = LinearProblem(sparse(BigFloat[1 1]), BigFloat[1, 2];
                            row_lower=BigFloat[1])
    result = solve(problem)
    @assert result.status == OPTIMAL
    @assert result.primal isa Vector{BigFloat}
end
```
"""
function solve(problem::LinearProblem{T}; relax_integrality::Bool=false,
               options=nothing)::Solution{T} where {T<:Real}
    start_ns = time_ns()
    typed_options = options === nothing ? SolverOptions(T) : SolverOptions(T, options)
    context = SolveContext(start_ns, typed_options.time_limit)
    @logmsg typed_options.log_level "Starting solve" name=problem.name algorithm=typed_options.algorithm
    _report_problem_statistics("Loaded problem", problem, typed_options)
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT, "time limit reached")
    typed_options.algorithm in (:dual, :primal) ||
        return _finish_solve(T, context, typed_options, ALGORITHM_NOT_SUPPORTED,
                             "only the dual and primal simplex algorithms are supported")
    error = _validation_error(problem)
    isnothing(error) || return _finish_solve(T, context, typed_options, INVALID_MODEL, error)
    if !relax_integrality && !is_continuous(problem)
        return _finish_solve(T, context, typed_options, MIP_NOT_SUPPORTED,
                             "discrete domains require relax_integrality=true")
    end

    # Even a continuous input gets its own arrays before future transforms can
    # mutate the working model. Keep this original-space LP for certification.
    continuous_problem = JSimplex.relax_integrality(problem)
    presolved = typed_options.presolve ? presolve_problem(continuous_problem) :
                identity_presolve(continuous_problem)
    if typed_options.presolve
        if presolved isa PresolveFailure
            _report_problem_statistics("After presolve", presolved.rows, presolved.columns,
                                       presolved.nonzeros, typed_options)
        else
            _report_problem_statistics("After presolve", presolved.problem, typed_options)
        end
    end
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT, "time limit reached")
    presolved isa PresolveFailure &&
        return _finish_solve(T, context, typed_options, presolved.status, presolved.message)
    scaled_problem, scaling =
        typed_options.scaling === :off || T <: Rational ?
            (presolved.problem, identity_scaling(presolved.problem)) :
            scale_problem(presolved.problem)
    working_problem = _minimization_problem(scaled_problem)
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT, "time limit reached")

    # The core converts expected internal numerical failures and preserves
    # callback exception provenance. Do not add a broader catch at this layer.
    progress = SimplexProgressContext(presolved.problem; start_ns=context.start_ns, scaling)
    algorithm = typed_options.algorithm == :dual ? _solve_continuous_dual : _solve_continuous_primal
    run = algorithm(
        working_problem,
        typed_options;
        stop_requested=() -> time_limit_reached(context),
        progress,
    )
    reduced = !isempty(presolved.postsolve_stack)
    retried_original = false
    if reduced && run.status in (INFEASIBLE, UNBOUNDED, NUMERICAL_ERROR)
        run = _retry_original(continuous_problem, typed_options, context, run)
        retried_original = true
    end
    if run.status != OPTIMAL
        return _finish_solve(T, context, typed_options, run.status, run.message;
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end

    primal = retried_original ? run.primal :
             postsolve_primal(presolved, unscale_primal(scaling, run.primal))
    if reduced && !retried_original
        if isnothing(run.basis)
            run = _retry_original(continuous_problem, typed_options, context, run)
        else
            basis = restore_basis(presolved, run.basis)
            run = _cleanup_or_retry_original(continuous_problem, basis,
                typed_options, context, run.iterations, run.refactorizations)
        end
        if run.status != OPTIMAL
            return _finish_solve(T, context, typed_options, run.status, run.message;
                                 iterations=run.iterations, refactorizations=run.refactorizations)
        end
        primal = run.primal
    end
    objective = _restored_objective(problem, primal)
    if isnothing(objective)
        return _finish_solve(T, context, typed_options, NUMERICAL_ERROR,
                             "original-objective evaluation is inconclusive at the current precision";
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end
    tolerance = typed_options.primal_tolerance
    if !isfinite(objective) ||
       !_original_primal_feasible(continuous_problem, primal, tolerance)
        return _finish_solve(T, context, typed_options, NUMERICAL_ERROR,
                             "restored primal failed original-model feasibility checks";
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end
    return _finish_solve(T, context, typed_options, OPTIMAL, run.message;
                         primal, objective_value=objective,
                         iterations=run.iterations, refactorizations=run.refactorizations)
end
