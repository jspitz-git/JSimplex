abstract type AbstractPostsolveStep end

struct PresolveResult
    problem::LinearProblem
    postsolve_stack::Vector{AbstractPostsolveStep}
    original_column_count::Int
end

struct Scaling
    row_factors::Vector{Float64}
    column_factors::Vector{Float64}
end

identity_presolve(problem::LinearProblem) =
    PresolveResult(problem, AbstractPostsolveStep[], size(problem.A, 2))

identity_scaling(problem::LinearProblem) =
    Scaling(ones(size(problem.A, 1)), ones(size(problem.A, 2)))

unscale_primal(scaling::Scaling, x::AbstractVector{<:Real}) =
    Float64.(x) ./ scaling.column_factors

unscale_dual(scaling::Scaling, y::AbstractVector{<:Real}) =
    Float64.(y) ./ scaling.row_factors

function postsolve_primal(result::PresolveResult, x::AbstractVector{<:Real})
    restored = Float64.(x)
    for step in Iterators.reverse(result.postsolve_stack)
        restored = postsolve_primal(step, restored)
    end
    return restored[1:result.original_column_count]
end

function relax_integrality(problem::LinearProblem)
    column_lower = copy(problem.column_lower)
    column_upper = copy(problem.column_upper)

    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] in (SEMI_CONTINUOUS, SEMI_INTEGER)
            column_lower[index] = min(0.0, column_lower[index])
            column_upper[index] = max(0.0, column_upper[index])
        end
    end

    return LinearProblem(
        problem.A,
        problem.objective,
        problem.objective_constant,
        problem.objective_sense,
        problem.row_lower,
        problem.row_upper,
        column_lower,
        column_upper,
        fill(CONTINUOUS, length(problem.variable_domains)),
        problem.name,
        problem.row_names,
        problem.column_names,
    )
end
