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

_scale_shift(value::T, exponent::Int) where {T<:AbstractFloat} = ldexp(value, exponent)

function _scale_shift(value::BigFloat, exponent::Int)
    return setprecision(BigFloat, max(precision(value), precision(BigFloat))) do
        ldexp(value, exponent)
    end
end

_scale_magnitude(value::T) where {T<:AbstractFloat} = abs(value)

function _scale_magnitude(value::BigFloat)
    return setprecision(BigFloat, max(precision(value), precision(BigFloat))) do
        abs(value)
    end
end

_scale_exponent(value::AbstractFloat) = last(frexp(value)) - 1

function _scale_exponent(value::BigFloat)
    return setprecision(BigFloat, max(precision(value), precision(BigFloat))) do
        last(frexp(value)) - 1
    end
end

function _safe_scale_shift(value::T, exponent::Int) where {T<:AbstractFloat}
    shifted = _scale_shift(value, exponent)
    return isfinite(shifted) && (iszero(value) || !iszero(shifted))
end

_safe_scale_bound(bound::Bound{T}, exponent::Int) where {T<:AbstractFloat} =
    !isfinite(bound) || _safe_scale_shift(bound_value(bound), exponent)

_scale_bound(bound::Bound{T}, exponent::Int) where {T<:AbstractFloat} =
    isfinite(bound) ? Bound(_scale_shift(bound_value(bound), exponent)) : bound

function scale_problem(problem::LinearProblem{T}) where {T<:AbstractFloat}
    A = problem.A
    row_count, column_count = size(A)
    row_maxima = zeros(T, row_count)
    for position in eachindex(A.nzval)
        row = A.rowval[position]
        row_maxima[row] = max(row_maxima[row], _scale_magnitude(A.nzval[position]))
    end

    row_exponents = zeros(Int, row_count)
    row_valid = trues(row_count)
    for row in 1:row_count
        iszero(row_maxima[row]) && continue
        exponent = _scale_exponent(row_maxima[row])
        row_exponents[row] = exponent
        row_valid[row] = _safe_scale_bound(problem.row_lower[row], -exponent) &&
                         _safe_scale_bound(problem.row_upper[row], -exponent)
    end
    for position in eachindex(A.nzval)
        row = A.rowval[position]
        row_valid[row] &= _safe_scale_shift(A.nzval[position], -row_exponents[row])
    end

    row_factors = ones(T, row_count)
    row_lower, row_upper = copy(problem.row_lower), copy(problem.row_upper)
    scaled_A = copy(A)
    for row in 1:row_count
        row_valid[row] || continue
        exponent = row_exponents[row]
        row_factors[row] = _scale_shift(one(T), exponent)
        row_lower[row] = _scale_bound(row_lower[row], -exponent)
        row_upper[row] = _scale_bound(row_upper[row], -exponent)
    end
    for position in eachindex(scaled_A.nzval)
        row = scaled_A.rowval[position]
        row_valid[row] || continue
        scaled_A.nzval[position] = _scale_shift(scaled_A.nzval[position], -row_exponents[row])
    end

    column_maxima = zeros(T, column_count)
    for column in 1:column_count
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            column_maxima[column] = max(column_maxima[column],
                                        _scale_magnitude(scaled_A.nzval[position]))
        end
    end
    column_factors = ones(T, column_count)
    scaled_objective = copy(problem.objective)
    column_lower, column_upper = copy(problem.column_lower), copy(problem.column_upper)
    for column in 1:column_count
        problem.variable_domains[column] == CONTINUOUS || continue
        iszero(column_maxima[column]) && continue
        exponent = _scale_exponent(column_maxima[column])
        _safe_scale_bound(column_lower[column], exponent) || continue
        _safe_scale_bound(column_upper[column], exponent) || continue
        _safe_scale_shift(scaled_objective[column], -exponent) || continue
        all(position -> _safe_scale_shift(scaled_A.nzval[position], -exponent),
            A.colptr[column]:(A.colptr[column + 1] - 1)) || continue

        column_factors[column] = _scale_shift(one(T), exponent)
        column_lower[column] = _scale_bound(column_lower[column], exponent)
        column_upper[column] = _scale_bound(column_upper[column], exponent)
        scaled_objective[column] = _scale_shift(scaled_objective[column], -exponent)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            scaled_A.nzval[position] = _scale_shift(scaled_A.nzval[position], -exponent)
        end
    end

    scaled_problem = LinearProblem{T}(
        scaled_A, scaled_objective, problem.objective_constant, problem.objective_sense,
        row_lower, row_upper, column_lower, column_upper,
        problem.variable_domains, problem.name, problem.row_names, problem.column_names,
    )
    return scaled_problem, Scaling(row_factors, column_factors)
end

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
