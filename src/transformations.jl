abstract type AbstractPostsolveStep end

struct PresolveResult{T<:Real,S<:Tuple}
    problem::LinearProblem{T}
    postsolve_stack::S
    original_column_count::Int
end

struct Scaling{T<:Real}
    row_factors::Vector{T}
    column_factors::Vector{T}
end

identity_presolve(problem::LinearProblem{T}) where {T} =
    PresolveResult(problem, (), size(problem.A, 2))

identity_scaling(problem::LinearProblem{T}) where {T} =
    Scaling(ones(T, size(problem.A, 1)), ones(T, size(problem.A, 2)))

_unscale_value(value::Real, factor::T) where {T} =
    isone(factor) ? convert(T, value) : convert(T, value) / factor

unscale_primal(scaling::Scaling{T}, x::AbstractVector{<:Real}) where {T} =
    _unscale_value.(x, scaling.column_factors)

unscale_dual(scaling::Scaling{T}, y::AbstractVector{<:Real}) where {T} =
    _unscale_value.(y, scaling.row_factors)

function postsolve_primal(result::PresolveResult{T}, x::AbstractVector{<:Real}) where {T}
    restored = _postsolve_primal(result.postsolve_stack, convert.(T, x))
    return restored[1:result.original_column_count]
end

_postsolve_primal(::Tuple{}, x) = x
_postsolve_primal(steps::Tuple, x) =
    postsolve_primal(first(steps), _postsolve_primal(Base.tail(steps), x))

function relax_integrality(problem::LinearProblem{T}) where {T}
    column_lower = copy(problem.column_lower)
    column_upper = copy(problem.column_upper)

    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] == BINARY
            column_lower[index] = Bound(isfinite(column_lower[index]) ?
                max(zero(T), bound_value(column_lower[index])) : zero(T))
            column_upper[index] = Bound(isfinite(column_upper[index]) ?
                min(one(T), bound_value(column_upper[index])) : one(T))
        elseif problem.variable_domains[index] in (SEMI_CONTINUOUS, SEMI_INTEGER)
            isfinite(column_lower[index]) &&
                (column_lower[index] = Bound(min(zero(T), bound_value(column_lower[index]))))
            isfinite(column_upper[index]) &&
                (column_upper[index] = Bound(max(zero(T), bound_value(column_upper[index]))))
        end
    end

    return LinearProblem{T}(
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
