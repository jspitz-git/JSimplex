struct SolveContext
    start_ns::UInt64
    time_limit_seconds::Float64
end

elapsed_seconds(context::SolveContext) = (time_ns() - context.start_ns) / 1.0e9
time_limit_reached(context::SolveContext) =
    elapsed_seconds(context) >= context.time_limit_seconds

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
    presolved = identity_presolve(continuous_problem)
    scaling = identity_scaling(presolved.problem)
    working_problem = _minimization_problem(presolved.problem)
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT, "time limit reached")

    # The core converts expected internal numerical failures and preserves
    # callback exception provenance. Do not add a broader catch at this layer.
    progress = SimplexProgressContext(problem; start_ns=context.start_ns)
    algorithm = typed_options.algorithm == :dual ? _solve_continuous_dual : _solve_continuous_primal
    run = algorithm(
        working_problem,
        typed_options;
        stop_requested=() -> time_limit_reached(context),
        progress,
    )
    if run.status != OPTIMAL
        return _finish_solve(T, context, typed_options, run.status, run.message;
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end

    primal = postsolve_primal(presolved, unscale_primal(scaling, run.primal))
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
