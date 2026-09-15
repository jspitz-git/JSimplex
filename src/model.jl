"""
    ObjectiveSense

Objective direction: `MIN_SENSE` minimizes and `MAX_SENSE` maximizes.
"""
@enum ObjectiveSense::UInt8 MIN_SENSE MAX_SENSE

@doc "Minimize the linear objective, including its constant." MIN_SENSE
@doc "Maximize the linear objective, including its constant." MAX_SENSE

"""
    VariableDomain

Variable domain: `CONTINUOUS`, `INTEGER`, `BINARY`, `SEMI_CONTINUOUS`, or
`SEMI_INTEGER`. Semi domains admit zero as well as their active interval
(integer values only for `SEMI_INTEGER`). All domains other than
`CONTINUOUS` require `relax_integrality=true` when passed to [`solve`](@ref).
"""
@enum VariableDomain::UInt8 begin
    CONTINUOUS
    INTEGER
    BINARY
    SEMI_CONTINUOUS
    SEMI_INTEGER
end

@doc "A real-valued variable within its column bounds." CONTINUOUS
@doc "An integer-valued variable within its column bounds." INTEGER
@doc "A variable restricted to zero or one and its column bounds." BINARY
@doc "A variable equal to zero or a real value in its active interval." SEMI_CONTINUOUS
@doc "A variable equal to zero or an integer in its active interval." SEMI_INTEGER

"""
    LinearProblem(A::SparseMatrixCSC, objective; objective_constant=nothing,
                  value_type=nothing, objective_sense=MIN_SENSE,
                  row_lower=nothing, row_upper=nothing,
                  column_lower=nothing, column_upper=nothing,
                  variable_domains=fill(CONTINUOUS, size(A, 2)), name="",
                  row_names=String[], column_names=String[])

Represent a linear objective `dot(objective, x) + objective_constant` with
`row_lower <= A*x <= row_upper` and variable bounds. Data is copied into a
`LinearProblem{T}` with `A::SparseMatrixCSC{T,Int}`, `objective::Vector{T}`, and
`objective_constant::T`. Infer a common concrete `AbstractFloat` or `Rational`
type using Julia promotion of the matrix, objective, explicitly supplied constant,
and finite bound values. Integer-only input uses `Float64`. `value_type=T`
overrides inference and converts finite data with validation. Omitted arguments
and unbounded sentinels do not affect inference; defaults are created in `T`.

Bounds are stored as `Vector{Bound{T}}`. Accept finite real values, convertible
`Bound` values, or `nothing` for an unbounded side. Compatibility sentinels
`-Inf` for lower bounds and `Inf` for upper bounds are normalized to unbounded
tags, even for rational models. NaN and incorrectly signed infinities are invalid.
Use `isfinite(bound)` before [`bound_value`](@ref), which returns `T` for finite
bounds and throws `ArgumentError` for unbounded ones. Code that previously read
numeric bound fields must now use these helpers.
Omitted row bounds and column upper bounds are unbounded; omitted column lower
bounds are `zero(T)`. Construction validates dimensions, finite coefficients,
bounds, and domains, throwing `ArgumentError` on invalid input. Binary bounds
are intersected with `[zero(T), one(T)]`.
Names may be omitted; supplied row/column names must match their dimensions.

Use `Rational{BigInt}` for arbitrary-size exact arithmetic; fixed-width rationals
retain Julia's ordinary solve-time overflow behavior. `BigFloat` precision is
controlled by Julia's ambient context: wrap construction and [`solve`](@ref)
in `setprecision(BigFloat, 256) do ... end`. Internal copies and objective-sense
changes preserve stored BigFloat values and their precision; solving at lower
precision can return `NUMERICAL_ERROR` when certification is inconclusive.

```julia
using JSimplex, SparseArrays
problem = LinearProblem(sparse(Rational{BigInt}[1 1]), Rational{BigInt}[1, 2];
                        row_lower=Rational{BigInt}[1], row_upper=[nothing])
@assert bound_value(problem.row_lower[1]) == 1 // big(1)
@assert !isfinite(problem.row_upper[1])
@assert solve(problem).objective_value == 1 // big(1)
```

The struct is immutable, but its arrays remain mutable; treat them as read-only.
[`solve`](@ref) copies working data and leaves the input model unchanged.
"""
struct LinearProblem{T<:Real}
    A::SparseMatrixCSC{T,Int}
    objective::Vector{T}
    objective_constant::T
    objective_sense::ObjectiveSense
    row_lower::Vector{Bound{T}}
    row_upper::Vector{Bound{T}}
    column_lower::Vector{Bound{T}}
    column_upper::Vector{Bound{T}}
    variable_domains::Vector{VariableDomain}
    name::String
    row_names::Vector{String}
    column_names::Vector{String}

    function LinearProblem{T}(
        A::SparseMatrixCSC{T,Int}, objective::Vector{T},
        objective_constant::T, objective_sense::ObjectiveSense,
        row_lower::Vector{Bound{T}}, row_upper::Vector{Bound{T}},
        column_lower::Vector{Bound{T}}, column_upper::Vector{Bound{T}},
        variable_domains::Vector{VariableDomain}, name::String,
        row_names::Vector{String}, column_names::Vector{String},
    ) where {T<:Real}
        _supported_value_type(T) || throw(ArgumentError("unsupported model value type $T"))
        problem = new{T}(copy(A), copy(objective), objective_constant, objective_sense,
            copy(row_lower), copy(row_upper), copy(column_lower), copy(column_upper),
            copy(variable_domains), name, copy(row_names), copy(column_names))
        error = _validation_error(problem)
        isnothing(error) || throw(ArgumentError(error))
        for index in eachindex(problem.variable_domains)
            if problem.variable_domains[index] == BINARY
                lower, upper = problem.column_lower[index], problem.column_upper[index]
                problem.column_lower[index] = Bound(
                    isfinite(lower) ? max(bound_value(lower), zero(T)) : zero(T))
                problem.column_upper[index] = Bound(
                    isfinite(upper) ? min(bound_value(upper), one(T)) : one(T))
            end
        end
        return problem
    end
end

_promote_input_type(::Type{T}, ::Nothing) where {T} = T
_promote_input_type(::Type{T}, value::Real) where {T} = promote_type(T, typeof(value))

_bound_input_type(::Type{T}, ::Nothing) where {T} = T
_bound_input_type(::Type{T}, bound::Bound) where {T} =
    isfinite(bound) ? promote_type(T, typeof(bound_value(bound))) : T
_bound_input_type(::Type{T}, bound::Real) where {T} =
    isfinite(bound) ? promote_type(T, typeof(bound)) : T
_bound_input_type(::Type, bound) =
    throw(ArgumentError("bounds must contain real values, Bound values, or nothing"))

_bound_vector_type(::Type{T}, ::Nothing) where {T} = T
function _bound_vector_type(::Type{T}, bounds::AbstractVector) where {T}
    result = T
    for bound in bounds
        result = _bound_input_type(result, bound)
    end
    return result
end

function _working_value_type(A, objective, objective_constant, bounds...)
    initial = _promote_input_type(promote_type(eltype(A), eltype(objective)), objective_constant)
    inferred = _working_bounds_type(initial, bounds)
    working = inferred <: Integer ? Float64 : inferred
    _supported_value_type(working) || throw(ArgumentError("unsupported model value type $working"))
    return working
end

_working_bounds_type(::Type{T}, ::Tuple{}) where {T} = T
_working_bounds_type(::Type{T}, bounds::Tuple) where {T} =
    _working_bounds_type(_bound_vector_type(T, first(bounds)), Base.tail(bounds))

function _model_convert(::Type{T}, value, label) where {T}
    converted = try
        T(value)
    catch exception
        exception isa InexactError || exception isa OverflowError || exception isa DomainError || rethrow()
        throw(ArgumentError("$label cannot be converted to $T"))
    end
    isfinite(converted) || throw(ArgumentError("$label must be finite"))
    return converted
end

function _model_bound(::Type{T}, value, side, label) where {T}
    try
        return _normalize_bound(T, value, side, label)
    catch exception
        exception isa InexactError || exception isa OverflowError || exception isa DomainError || rethrow()
        throw(ArgumentError("$label cannot be converted to $T"))
    end
end

# Preserve a caller's constant scalar type across the keyword wrapper.
Base.@constprop :aggressive function LinearProblem(
    A::SparseMatrixCSC,
    objective::AbstractVector{<:Real};
    objective_constant=nothing, value_type::Union{Nothing,Type{V}}=nothing,
    objective_sense::ObjectiveSense=MIN_SENSE,
    row_lower=nothing, row_upper=nothing,
    column_lower=nothing, column_upper=nothing,
    variable_domains::AbstractVector{VariableDomain}=fill(CONTINUOUS, size(A, 2)),
    name::AbstractString="",
    row_names::AbstractVector{<:AbstractString}=String[],
    column_names::AbstractVector{<:AbstractString}=String[],
) where {V}
    T = value_type === nothing ?
        _working_value_type(A, objective, objective_constant,
                            row_lower, row_upper, column_lower, column_upper) : value_type
    T isa Type && _supported_value_type(T) ||
        throw(ArgumentError("unsupported model value type $T"))
    return _typed_problem(T, A, objective, objective_constant, objective_sense,
        row_lower, row_upper, column_lower, column_upper,
        variable_domains, name, row_names, column_names)
end

function _typed_problem(::Type{T}, A, objective, objective_constant, objective_sense,
                        row_lower, row_upper, column_lower, column_upper,
                        variable_domains, name, row_names, column_names) where {T}
    row_count, column_count = size(A)
    matrix = SparseMatrixCSC(row_count, column_count, Int.(A.colptr), Int.(A.rowval),
        [_model_convert(T, value, "constraint matrix coefficient") for value in A.nzval])
    return LinearProblem{T}(
        matrix, [_model_convert(T, value, "objective coefficient") for value in objective],
        objective_constant === nothing ? zero(T) : _model_convert(T, objective_constant, "objective constant"),
        objective_sense,
        row_lower === nothing ? fill(_unbounded_bound(T), row_count) :
            [_model_bound(T, value, :lower, "row lower bound") for value in row_lower],
        row_upper === nothing ? fill(_unbounded_bound(T), row_count) :
            [_model_bound(T, value, :upper, "row upper bound") for value in row_upper],
        column_lower === nothing ? fill(Bound(zero(T)), column_count) :
            [_model_bound(T, value, :lower, "column lower bound") for value in column_lower],
        column_upper === nothing ? fill(_unbounded_bound(T), column_count) :
            [_model_bound(T, value, :upper, "column upper bound") for value in column_upper],
        collect(variable_domains), String(name), String.(row_names), String.(column_names),
    )
end

function LinearProblem(A::SparseMatrixCSC, objective::AbstractVector{<:Real},
                       objective_constant::Real, objective_sense::ObjectiveSense,
                       row_lower::AbstractVector, row_upper::AbstractVector,
                       column_lower::AbstractVector, column_upper::AbstractVector,
                       variable_domains::AbstractVector{VariableDomain}, name::AbstractString,
                       row_names::AbstractVector{<:AbstractString},
                       column_names::AbstractVector{<:AbstractString})
    return LinearProblem(A, objective; objective_constant, objective_sense,
        row_lower, row_upper, column_lower, column_upper,
        variable_domains, name, row_names, column_names)
end

function _validation_error(problem::LinearProblem{T})::Union{Nothing,String} where {T}
    row_count, column_count = size(problem.A)

    length(problem.objective) == column_count ||
        return "objective length must equal the number of columns"
    length(problem.row_lower) == row_count &&
        length(problem.row_upper) == row_count ||
        return "row bound lengths must equal the number of rows"
    length(problem.column_lower) == column_count &&
        length(problem.column_upper) == column_count ||
        return "column bound lengths must equal the number of columns"
    length(problem.variable_domains) == column_count ||
        return "variable domain length must equal the number of columns"
    isempty(problem.row_names) || length(problem.row_names) == row_count ||
        return "row names must be empty or match the number of rows"
    isempty(problem.column_names) || length(problem.column_names) == column_count ||
        return "column names must be empty or match the number of columns"

    all(isfinite, problem.A.nzval) ||
        return "constraint matrix coefficients must be finite"
    all(isfinite, problem.objective) ||
        return "objective coefficients must be finite"
    isfinite(problem.objective_constant) ||
        return "objective constant must be finite"

    for index in eachindex(problem.row_lower)
        lower = problem.row_lower[index]
        upper = problem.row_upper[index]
        if isfinite(lower) && isfinite(upper) && bound_value(lower) > bound_value(upper)
            return "row lower bounds must not exceed upper bounds"
        end
    end
    for index in eachindex(problem.column_lower)
        lower = problem.column_lower[index]
        upper = problem.column_upper[index]
        if isfinite(lower) && isfinite(upper) && bound_value(lower) > bound_value(upper)
            return "column lower bounds must not exceed upper bounds"
        end
    end

    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] == BINARY
            (!isfinite(problem.column_lower[index]) || bound_value(problem.column_lower[index]) <= one(T)) &&
            (!isfinite(problem.column_upper[index]) || bound_value(problem.column_upper[index]) >= zero(T)) ||
                return "binary variable bounds must intersect [0, 1]"
        end
    end
    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] in (SEMI_CONTINUOUS, SEMI_INTEGER) &&
           isfinite(problem.column_upper[index]) && !(bound_value(problem.column_upper[index]) > zero(T))
            return "semi-domain active upper bounds must be positive"
        end
    end

    return nothing
end

"""
    is_continuous(problem::LinearProblem) -> Bool

Return whether every variable has domain `CONTINUOUS`, including an empty model.
Integer, binary, and semi domains return `false` even when their bounds fix them.
"""
is_continuous(problem::LinearProblem) = all(==(CONTINUOUS), problem.variable_domains)
