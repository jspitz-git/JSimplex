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

struct MOITranslation{T<:Real}
    problem::Union{Nothing,LinearProblem{T}}
    index_map::MOI.Utilities.IndexMap
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

function _check_moi_constraint_support(optimizer::Optimizer, source)
    for (function_type, set_type) in MOI.get(source, MOI.ListOfConstraintTypesPresent())
        MOI.supports_constraint(optimizer, function_type, set_type) && continue
        throw(MOI.UnsupportedConstraint{function_type,set_type}())
    end
    return
end

function _moi_affine_evaluation(
    index_map::MOI.Utilities.IndexMap,
    function_::MOI.ScalarAffineFunction{T},
) where {T}
    columns = Int[]
    coefficients = T[]
    for term in function_.terms
        push!(columns, index_map[term.variable].value)
        push!(coefficients, term.coefficient)
    end
    return MOIScalarEvaluation(columns, coefficients, function_.constant)
end

function _moi_shift_bound(bound::Bound{T}, constant::T) where {T}
    isfinite(bound) || return bound
    return Bound(bound_value(bound) - constant)
end

function _moi_objective(
    optimizer::Optimizer{T},
    source,
    index_map::MOI.Utilities.IndexMap,
    column_count::Int,
) where {T}
    sense = MOI.get(source, MOI.ObjectiveSense())
    sense == MOI.FEASIBILITY_SENSE && return zeros(T, column_count), zero(T), MIN_SENSE

    function_type = MOI.get(source, MOI.ObjectiveFunctionType())
    attribute = MOI.ObjectiveFunction{function_type}()
    MOI.supports(optimizer, attribute) || throw(MOI.UnsupportedAttribute(attribute))
    function_ = MOI.get(source, attribute)
    objective = zeros(T, column_count)

    if function_type == MOI.VariableIndex
        objective[index_map[function_].value] = one(T)
        constant = zero(T)
    elseif function_type == MOI.ScalarAffineFunction{T}
        for term in function_.terms
            objective[index_map[term.variable].value] += term.coefficient
        end
        constant = function_.constant
    else
        throw(MOI.UnsupportedAttribute(attribute))
    end

    objective_sense = sense == MOI.MIN_SENSE ? MIN_SENSE : MAX_SENSE
    return objective, constant, objective_sense
end

function _translate_moi_model(optimizer::Optimizer{T}, source)::MOITranslation{T} where {T}
    _check_moi_constraint_support(optimizer, source)
    columns = _collect_moi_columns(optimizer, source)
    evaluations = columns.evaluations
    !isnothing(columns.error) &&
        return MOITranslation{T}(nothing, columns.index_map, evaluations, columns.error)

    row_indices = Int[]
    column_indices = Int[]
    coefficients = T[]
    row_lower = Bound{T}[]
    row_upper = Bound{T}[]
    row_names = String[]
    function_type = MOI.ScalarAffineFunction{T}

    for set_type in (MOI.GreaterThan{T}, MOI.LessThan{T}, MOI.EqualTo{T}, MOI.Interval{T})
        source_indices = MOI.get(
            source,
            MOI.ListOfConstraintIndices{MOI.ScalarAffineFunction{T},set_type}(),
        )
        for source_index in source_indices
            function_ = MOI.get(source, MOI.ConstraintFunction(), source_index)
            set = MOI.get(source, MOI.ConstraintSet(), source_index)
            row = length(row_lower) + 1
            evaluation = _moi_affine_evaluation(columns.index_map, function_)
            columns.index_map[source_index] = MOI.ConstraintIndex{function_type,set_type}(
                length(evaluations) + 1,
            )
            push!(evaluations, evaluation)

            row_coefficients = Dict{Int,T}()
            for (column, coefficient) in zip(evaluation.columns, evaluation.coefficients)
                row_coefficients[column] = get(row_coefficients, column, zero(T)) + coefficient
            end
            for (column, coefficient) in row_coefficients
                push!(row_indices, row)
                push!(column_indices, column)
                push!(coefficients, coefficient)
            end

            lower, upper = _moi_set_bounds(set)
            push!(row_lower, _moi_shift_bound(lower, evaluation.constant))
            push!(row_upper, _moi_shift_bound(upper, evaluation.constant))
            push!(row_names, MOI.get(source, MOI.ConstraintName(), source_index))
        end
    end

    objective, objective_constant, objective_sense = _moi_objective(
        optimizer,
        source,
        columns.index_map,
        length(columns.lower),
    )
    A = sparse(row_indices, column_indices, coefficients, length(row_lower), length(columns.lower))
    problem = try
        LinearProblem(
            A,
            objective;
            value_type=T,
            objective_constant,
            objective_sense,
            row_lower,
            row_upper,
            column_lower=columns.lower,
            column_upper=columns.upper,
            variable_domains=columns.domains,
            name=MOI.get(source, MOI.Name()),
            row_names,
            column_names=columns.names,
        )
    catch exception
        exception isa ArgumentError || rethrow()
        return MOITranslation{T}(
            nothing,
            columns.index_map,
            evaluations,
            sprint(showerror, exception),
        )
    end
    return MOITranslation{T}(problem, columns.index_map, evaluations, nothing)
end
