function _column_move_preserves_rows(problem::LinearProblem, column::Int,
                                     toward_lower::Bool)
    A = problem.A
    for position in A.colptr[column]:(A.colptr[column + 1] - 1)
        coefficient = A.nzval[position]
        iszero(coefficient) && continue
        row = A.rowval[position]
        # Moving a positive coefficient downward threatens only the row lower
        # bound; reversing either direction reverses the blocking side.
        blocking_side = (coefficient > 0) == toward_lower ?
                        problem.row_lower[row] : problem.row_upper[row]
        isfinite(blocking_side) && return false
    end
    return true
end

function reduce_dual_fixings(problem::LinearProblem{T}) where {T}
    columns = size(problem.A, 2)
    selections = nothing
    for column in 1:columns
        cost = problem.objective[column]
        lower_improves = iszero(cost) ||
            ((cost > 0) == (problem.objective_sense == MIN_SENSE))
        upper_improves = iszero(cost) || !lower_improves
        lower = problem.column_lower[column]
        upper = problem.column_upper[column]
        selection = if lower_improves && isfinite(lower) &&
           _column_move_preserves_rows(problem, column, true)
            (bound_value(lower), AT_LOWER)
        elseif upper_improves && isfinite(upper) &&
               _column_move_preserves_rows(problem, column, false)
            (bound_value(upper), AT_UPPER)
        else
            continue
        end
        # Passes with no eligible column need no selection storage.
        if isnothing(selections)
            selections = Vector{Union{Nothing,Tuple{T,VariableState}}}(nothing, columns)
        end
        selections[column] = selection
    end
    isnothing(selections) && return identity_presolve(problem)
    return _presolve_basic(problem; selections)
end
