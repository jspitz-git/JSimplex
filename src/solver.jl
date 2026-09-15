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

function _minimization_problem(problem::LinearProblem{T}) where {T}
    problem.objective_sense == MIN_SENSE && return problem
    return LinearProblem(
        problem.A, -problem.objective, -problem.objective_constant, MIN_SENSE,
        problem.row_lower, problem.row_upper, problem.column_lower,
        problem.column_upper, problem.variable_domains, problem.name,
        problem.row_names, problem.column_names,
    )
end

"""
    solve(problem::LinearProblem; relax_integrality=false, options=nothing)

Solve an LP using dual simplex. Discrete domains require explicit LP relaxation;
the input model remains unchanged. Only optimal results contain a primal vector
and objective value, expressed in the original structural variables and sense.

Without relaxation, any non-continuous domain returns `MIP_NOT_SUPPORTED`.
With relaxation, integer/binary domains retain their bounds and semi domains
use the convex hull of zero and their active interval. Only `algorithm=:dual`
is supported. Inspect `solution.status`, `solution.message`, and
`solution.statistics` for termination details; non-optimal results have
`nothing` for both `primal` and `objective_value`.

The monotonic time limit starts at entry; an expired deadline takes precedence
over algorithm selection and validation. Iteration limits count completed pivots.
"""
function solve(problem::LinearProblem{T}; relax_integrality::Bool=false,
               options=nothing)::Solution{T} where {T<:Real}
    typed_options = options === nothing ? SolverOptions(T) : SolverOptions(T, options)
    context = SolveContext(time_ns(), typed_options.time_limit)
    @logmsg typed_options.log_level "Starting solve" name=problem.name algorithm=typed_options.algorithm
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT, "time limit reached")
    typed_options.algorithm == :dual ||
        return _finish_solve(T, context, typed_options, ALGORITHM_NOT_SUPPORTED,
                             "only the dual simplex algorithm is supported")
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
    run = _solve_continuous_dual(working_problem, typed_options;
                               stop_requested=() -> time_limit_reached(context))
    if run.status != OPTIMAL
        return _finish_solve(T, context, typed_options, run.status, run.message;
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end

    primal = postsolve_primal(presolved, unscale_primal(scaling, run.primal))
    objective = dot(problem.objective, primal) + problem.objective_constant
    tolerance = typed_options.primal_tolerance
    if !isfinite(objective) ||
       !_within_primal_bounds(primal, continuous_problem.column_lower,
                              continuous_problem.column_upper, tolerance) ||
       !_within_primal_bounds(continuous_problem.A * primal,
                              continuous_problem.row_lower, continuous_problem.row_upper, tolerance)
        return _finish_solve(T, context, typed_options, NUMERICAL_ERROR,
                             "restored primal failed original-model feasibility checks";
                             iterations=run.iterations, refactorizations=run.refactorizations)
    end
    return _finish_solve(T, context, typed_options, OPTIMAL, run.message;
                         primal, objective_value=objective,
                         iterations=run.iterations, refactorizations=run.refactorizations)
end
