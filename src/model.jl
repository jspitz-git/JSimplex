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
    LinearProblem(A::SparseMatrixCSC, objective; objective_constant=0.0,
                  objective_sense=MIN_SENSE, row_lower=fill(-Inf, size(A, 1)),
                  row_upper=fill(Inf, size(A, 1)), column_lower=zeros(size(A, 2)),
                  column_upper=fill(Inf, size(A, 2)),
                  variable_domains=fill(CONTINUOUS, size(A, 2)), name="",
                  row_names=String[], column_names=String[])

Represent a linear objective `dot(objective, x) + objective_constant` with
`row_lower <= A*x <= row_upper` and variable bounds. Data is copied and
converted to sparse `Float64` coefficients and `Float64` vectors. Construction
validates dimensions, finite coefficients, bounds, and domains, throwing
`ArgumentError` on invalid input. Binary bounds are intersected with `[0, 1]`.
Names may be omitted; supplied row/column names must match their dimensions.

The struct is immutable, but its arrays remain mutable; treat them as read-only.
[`solve`](@ref) copies working data and leaves the input model unchanged.
"""
struct LinearProblem
    A::SparseMatrixCSC{Float64,Int}
    objective::Vector{Float64}
    objective_constant::Float64
    objective_sense::ObjectiveSense
    row_lower::Vector{Float64}
    row_upper::Vector{Float64}
    column_lower::Vector{Float64}
    column_upper::Vector{Float64}
    variable_domains::Vector{VariableDomain}
    name::String
    row_names::Vector{String}
    column_names::Vector{String}

    function LinearProblem(
        A::SparseMatrixCSC{Float64,Int},
        objective::Vector{Float64},
        objective_constant::Float64,
        objective_sense::ObjectiveSense,
        row_lower::Vector{Float64},
        row_upper::Vector{Float64},
        column_lower::Vector{Float64},
        column_upper::Vector{Float64},
        variable_domains::Vector{VariableDomain},
        name::String,
        row_names::Vector{String},
        column_names::Vector{String},
    )
        copied_column_lower = copy(column_lower)
        copied_column_upper = copy(column_upper)
        copied_domains = copy(variable_domains)

        if length(copied_domains) == length(copied_column_lower) ==
           length(copied_column_upper)
            for index in eachindex(copied_domains)
                if copied_domains[index] == BINARY
                    lower = copied_column_lower[index]
                    upper = copied_column_upper[index]
                    if lower <= upper && lower <= 1.0 && upper >= 0.0
                        copied_column_lower[index] = max(lower, 0.0)
                        copied_column_upper[index] = min(upper, 1.0)
                    end
                end
            end
        end

        problem = new(
            copy(A), copy(objective), objective_constant, objective_sense,
            copy(row_lower), copy(row_upper), copied_column_lower,
            copied_column_upper, copied_domains, name, copy(row_names),
            copy(column_names),
        )
        error = _validation_error(problem)
        isnothing(error) || throw(ArgumentError(error))
        return problem
    end
end

function LinearProblem(
    A::SparseMatrixCSC,
    objective::AbstractVector{<:Real};
    objective_constant::Real=0.0,
    objective_sense::ObjectiveSense=MIN_SENSE,
    row_lower::AbstractVector{<:Real}=fill(-Inf, size(A, 1)),
    row_upper::AbstractVector{<:Real}=fill(Inf, size(A, 1)),
    column_lower::AbstractVector{<:Real}=zeros(size(A, 2)),
    column_upper::AbstractVector{<:Real}=fill(Inf, size(A, 2)),
    variable_domains::AbstractVector{VariableDomain}=fill(CONTINUOUS, size(A, 2)),
    name::AbstractString="",
    row_names::AbstractVector{<:AbstractString}=String[],
    column_names::AbstractVector{<:AbstractString}=String[],
)
    return LinearProblem(
        SparseMatrixCSC{Float64,Int}(A), Float64.(objective),
        Float64(objective_constant), objective_sense, Float64.(row_lower),
        Float64.(row_upper), Float64.(column_lower), Float64.(column_upper),
        collect(variable_domains), String(name), String.(row_names),
        String.(column_names),
    )
end

function _validation_error(problem::LinearProblem)::Union{Nothing,String}
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
        isnan(lower) && return "row lower bounds must not be NaN"
        isnan(upper) && return "row upper bounds must not be NaN"
        lower == Inf && return "row lower bounds must not be +Inf"
        upper == -Inf && return "row upper bounds must not be -Inf"
        lower <= upper || return "row lower bounds must not exceed upper bounds"
    end
    for index in eachindex(problem.column_lower)
        lower = problem.column_lower[index]
        upper = problem.column_upper[index]
        isnan(lower) && return "column lower bounds must not be NaN"
        isnan(upper) && return "column upper bounds must not be NaN"
        lower == Inf && return "column lower bounds must not be +Inf"
        upper == -Inf && return "column upper bounds must not be -Inf"
        lower <= upper || return "column lower bounds must not exceed upper bounds"
    end

    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] == BINARY
            problem.column_lower[index] <= 1.0 && problem.column_upper[index] >= 0.0 ||
                return "binary variable bounds must intersect [0, 1]"
        end
    end
    for index in eachindex(problem.variable_domains)
        if problem.variable_domains[index] in (SEMI_CONTINUOUS, SEMI_INTEGER) &&
           problem.column_upper[index] != Inf && !(problem.column_upper[index] > 0.0)
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
