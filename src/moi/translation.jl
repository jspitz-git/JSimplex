struct MOIScalarEvaluation{T<:Real}
    columns::Vector{Int}
    coefficients::Vector{T}
    constant::T
end

struct MOIColumnData{T<:Real}
    index_map::MOI.Utilities.IndexMap
    lower::Vector{Bound{T}}
    upper::Vector{Bound{T}}
    domains::Vector{VariableDomain}
    names::Vector{String}
    evaluations::Vector{MOIScalarEvaluation{T}}
    error::Union{Nothing,String}
end

_moi_set_bounds(set::MOI.GreaterThan{T}) where {T} =
    (Bound(set.lower), _unbounded_bound(T))
_moi_set_bounds(set::MOI.LessThan{T}) where {T} =
    (_unbounded_bound(T), Bound(set.upper))
_moi_set_bounds(set::MOI.EqualTo{T}) where {T} =
    (Bound(set.value), Bound(set.value))
_moi_set_bounds(set::MOI.Interval{T}) where {T} =
    (Bound(set.lower), Bound(set.upper))

function _intersect_moi_lower(left::Bound{T}, right::Bound{T}) where {T}
    !isfinite(left) && return right
    !isfinite(right) && return left
    return Bound(max(bound_value(left), bound_value(right)))
end

function _intersect_moi_upper(left::Bound{T}, right::Bound{T}) where {T}
    !isfinite(left) && return right
    !isfinite(right) && return left
    return Bound(min(bound_value(left), bound_value(right)))
end

function _intersect_moi_bounds!(
    lower::Vector{Bound{T}},
    upper::Vector{Bound{T}},
    column::Int,
    constraint_lower::Bound{T},
    constraint_upper::Bound{T},
    error::Union{Nothing,String},
) where {T}
    lower[column] = _intersect_moi_lower(lower[column], constraint_lower)
    upper[column] = _intersect_moi_upper(upper[column], constraint_upper)
    if isnothing(error) && isfinite(lower[column]) && isfinite(upper[column]) &&
       bound_value(lower[column]) > bound_value(upper[column])
        return "column lower bound exceeds column upper bound for variable $column"
    end
    return error
end

function _apply_moi_variable_constraint!(
    lower::Vector{Bound{T}},
    upper::Vector{Bound{T}},
    domains::Vector{VariableDomain},
    column::Int,
    set::_MOINumericSet{T},
    error::Union{Nothing,String},
) where {T}
    constraint_lower, constraint_upper = _moi_set_bounds(set)
    return _intersect_moi_bounds!(
        lower,
        upper,
        column,
        constraint_lower,
        constraint_upper,
        error,
    )
end

function _apply_moi_variable_constraint!(
    lower::Vector{Bound{T}},
    upper::Vector{Bound{T}},
    domains::Vector{VariableDomain},
    column::Int,
    ::MOI.ZeroOne,
    error::Union{Nothing,String},
) where {T}
    domains[column] = BINARY
    return _intersect_moi_bounds!(
        lower,
        upper,
        column,
        Bound(zero(T)),
        Bound(one(T)),
        error,
    )
end

function _apply_moi_variable_constraint!(
    lower::Vector{Bound{T}},
    upper::Vector{Bound{T}},
    domains::Vector{VariableDomain},
    column::Int,
    ::MOI.Integer,
    error::Union{Nothing,String},
) where {T}
    domains[column] == CONTINUOUS && (domains[column] = INTEGER)
    return error
end

_moi_variable_set_types(::Type{T}) where {T} = (
    MOI.GreaterThan{T},
    MOI.LessThan{T},
    MOI.EqualTo{T},
    MOI.Interval{T},
    MOI.Integer,
    MOI.ZeroOne,
)

function _collect_moi_columns(optimizer::Optimizer{T}, source)::MOIColumnData{T} where {T}
    source_variables = MOI.get(source, MOI.ListOfVariableIndices())
    index_map = MOI.Utilities.IndexMap()
    lower = fill(_unbounded_bound(T), length(source_variables))
    upper = fill(_unbounded_bound(T), length(source_variables))
    domains = fill(CONTINUOUS, length(source_variables))
    names = String[]
    evaluations = MOIScalarEvaluation{T}[]
    error = nothing

    for (column, source_variable) in enumerate(source_variables)
        index_map[source_variable] = MOI.VariableIndex(column)
        push!(names, MOI.get(source, MOI.VariableName(), source_variable))
    end

    for set_type in _moi_variable_set_types(T)
        source_indices = MOI.get(
            source,
            MOI.ListOfConstraintIndices{MOI.VariableIndex,set_type}(),
        )
        for source_index in source_indices
            source_variable = MOI.get(source, MOI.ConstraintFunction(), source_index)
            column = index_map[source_variable].value
            index_map[source_index] = MOI.ConstraintIndex{MOI.VariableIndex,set_type}(
                length(evaluations) + 1,
            )
            push!(evaluations, MOIScalarEvaluation(Int[column], T[one(T)], zero(T)))
            set = MOI.get(source, MOI.ConstraintSet(), source_index)
            error = _apply_moi_variable_constraint!(
                lower,
                upper,
                domains,
                column,
                set,
                error,
            )
        end
    end

    return MOIColumnData(index_map, lower, upper, domains, names, evaluations, error)
end
