function _evaluate_moi_function(
    evaluation::MOIScalarEvaluation{T},
    primal::Vector{T},
)::T where {T<:Real}
    value = evaluation.constant
    for (column, coefficient) in zip(evaluation.columns, evaluation.coefficients)
        value += coefficient * primal[column]
    end
    return value
end

function _evaluate_moi_function(
    evaluation::MOIScalarEvaluation{BigFloat},
    primal::Vector{BigFloat},
)::BigFloat
    value = evaluation.constant
    for (column, coefficient) in zip(evaluation.columns, evaluation.coefficients)
        primal_value = primal[column]
        value = setprecision(
            BigFloat,
            max(precision(value), precision(coefficient), precision(primal_value)),
        ) do
            value + coefficient * primal_value
        end
    end
    return value
end

function _moi_bigfloat_precision(problem::LinearProblem{BigFloat})
    result = precision(problem.objective_constant)
    for value in problem.A.nzval
        result = max(result, precision(value))
    end
    for value in problem.objective
        result = max(result, precision(value))
    end
    for bounds in (problem.row_lower, problem.row_upper,
                   problem.column_lower, problem.column_upper)
        for bound in bounds
            isfinite(bound) || continue
            result = max(result, precision(bound_value(bound)))
        end
    end
    return result
end

function _solve_moi_problem(
    optimizer::Optimizer{T},
    problem::LinearProblem{T},
) where {T}
    return solve(
        problem;
        relax_integrality=optimizer.relax_integrality,
        options=_solver_options(optimizer),
    )
end

function _solve_moi_problem(
    optimizer::Optimizer{BigFloat},
    problem::LinearProblem{BigFloat},
)
    return setprecision(BigFloat, _moi_bigfloat_precision(problem)) do
        solve(
            problem;
            relax_integrality=optimizer.relax_integrality,
            options=_solver_options(optimizer),
        )
    end
end

function MOI.optimize!(optimizer::Optimizer{T}, source::MOI.ModelLike) where {T}
    _clear_result!(optimizer)
    translation = _translate_moi_model(optimizer, source)
    if translation.error !== nothing
        optimizer.solution = Solution{T}(
            INVALID_MODEL,
            nothing,
            nothing,
            SolveStatistics(),
            translation.error,
        )
    else
        problem = something(translation.problem)
        optimizer.solution = _solve_moi_problem(optimizer, problem)
    end
    solution = optimizer.solution::Solution{T}
    if solution.status == OPTIMAL
        primal = something(solution.primal)
        append!(
            optimizer.constraint_primals,
            (_evaluate_moi_function(evaluation, primal)
             for evaluation in translation.evaluations),
        )
    end
    return translation.index_map, false
end

function _moi_termination_status(status::TerminationStatus)
    if status == OPTIMAL
        return MOI.OPTIMAL
    elseif status == INFEASIBLE
        return MOI.INFEASIBLE
    elseif status == UNBOUNDED
        return MOI.DUAL_INFEASIBLE
    elseif status == ITERATION_LIMIT
        return MOI.ITERATION_LIMIT
    elseif status == TIME_LIMIT
        return MOI.TIME_LIMIT
    elseif status == NUMERICAL_ERROR
        return MOI.NUMERICAL_ERROR
    elseif status == INVALID_MODEL
        return MOI.INVALID_MODEL
    elseif status == MIP_NOT_SUPPORTED
        return MOI.OTHER_ERROR
    end
    @assert status == ALGORITHM_NOT_SUPPORTED
    return MOI.INVALID_OPTION
end

MOI.get(optimizer::Optimizer, ::MOI.TerminationStatus) =
    isnothing(optimizer.solution) ? MOI.OPTIMIZE_NOT_CALLED :
    _moi_termination_status(optimizer.solution.status)

function MOI.get(optimizer::Optimizer, ::MOI.RawStatusString)
    isnothing(optimizer.solution) && return "optimize not called"
    optimizer.solution.status == MIP_NOT_SUPPORTED &&
        return "integer variables require a MIP solver; set relax_integrality=true to solve the LP relaxation"
    return optimizer.solution.message
end

MOI.get(optimizer::Optimizer, ::MOI.ResultCount) =
    !isnothing(optimizer.solution) && optimizer.solution.status == OPTIMAL ? 1 : 0

function MOI.get(optimizer::Optimizer, attr::MOI.PrimalStatus)
    return attr.result_index == 1 && MOI.get(optimizer, MOI.ResultCount()) == 1 ?
           MOI.FEASIBLE_POINT : MOI.NO_SOLUTION
end

MOI.get(::Optimizer, ::MOI.DualStatus) = MOI.NO_SOLUTION

function MOI.get(optimizer::Optimizer, attr::MOI.ObjectiveValue)
    MOI.check_result_index_bounds(optimizer, attr)
    return something((optimizer.solution::Solution).objective_value)
end

function MOI.get(
    optimizer::Optimizer,
    attr::MOI.VariablePrimal,
    variable::MOI.VariableIndex,
)
    MOI.check_result_index_bounds(optimizer, attr)
    return something((optimizer.solution::Solution).primal)[variable.value]
end

function MOI.get(
    optimizer::Optimizer,
    attr::MOI.ConstraintPrimal,
    constraint::MOI.ConstraintIndex,
)
    MOI.check_result_index_bounds(optimizer, attr)
    return optimizer.constraint_primals[constraint.value]
end

MOI.get(optimizer::Optimizer, ::MOI.SolveTimeSec) =
    isnothing(optimizer.solution) ? 0.0 : optimizer.solution.statistics.elapsed_seconds
MOI.get(optimizer::Optimizer, ::MOI.SimplexIterations) =
    isnothing(optimizer.solution) ? 0 : optimizer.solution.statistics.iterations
