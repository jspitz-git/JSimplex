mutable struct PropagationTrace{T<:Real}
    reference::Union{Nothing,LinearProblem{T}}
    row_origin::Vector{Int}
    column_origin::Vector{Int}
    pending::BitVector
end

PropagationTrace{T}() where {T<:Real} =
    PropagationTrace{T}(nothing, Int[], Int[], BitVector())

function _mark_incident_rows!(dirty::BitVector, A::SparseMatrixCSC,
                              column::Int, first_row::Int=1)
    for position in A.colptr[column]:(A.colptr[column + 1] - 1)
        row = A.rowval[position]
        row >= first_row && !iszero(A.nzval[position]) && (dirty[row] = true)
    end
    return dirty
end

function _changed_propagation_rows(reference::LinearProblem,
                                   current::LinearProblem,
                                   row_origin::Vector{Int},
                                   column_origin::Vector{Int},
                                   pending::BitVector)
    old_A, new_A = reference.A, current.A
    old_m, old_n = size(old_A)
    new_m, new_n = size(new_A)
    length(row_origin) == new_m && length(column_origin) == new_n &&
        length(pending) == new_m && issorted(row_origin) || return trues(new_m)

    old_to_new_row = zeros(Int, old_m)
    for (new_row, old_row) in enumerate(row_origin)
        1 <= old_row <= old_m && old_to_new_row[old_row] == 0 || return trues(new_m)
        old_to_new_row[old_row] = new_row
    end
    kept_columns = falses(old_n)
    for old_column in column_origin
        1 <= old_column <= old_n && !kept_columns[old_column] || return trues(new_m)
        kept_columns[old_column] = true
    end

    dirty = copy(pending)
    for (new_row, old_row) in enumerate(row_origin)
        if current.row_lower[new_row] != reference.row_lower[old_row] ||
           current.row_upper[new_row] != reference.row_upper[old_row]
            dirty[new_row] = true
        end
    end
    for (new_column, old_column) in enumerate(column_origin)
        if current.column_lower[new_column] != reference.column_lower[old_column] ||
           current.column_upper[new_column] != reference.column_upper[old_column]
            _mark_incident_rows!(dirty, new_A, new_column)
        end
    end

    # Every old nonzero in a removed column changes its retained row.
    for old_column in 1:old_n
        kept_columns[old_column] && continue
        for position in old_A.colptr[old_column]:(old_A.colptr[old_column + 1] - 1)
            new_row = old_to_new_row[old_A.rowval[position]]
            new_row != 0 && !iszero(old_A.nzval[position]) && (dirty[new_row] = true)
        end
    end

    # Both sparse columns are sorted by row. Retained row maps preserve order.
    for (new_column, old_column) in enumerate(column_origin)
        old_position = old_A.colptr[old_column]
        old_end = old_A.colptr[old_column + 1]
        new_position = new_A.colptr[new_column]
        new_end = new_A.colptr[new_column + 1]
        while true
            while old_position < old_end &&
                  (old_to_new_row[old_A.rowval[old_position]] == 0 ||
                   iszero(old_A.nzval[old_position]))
                old_position += 1
            end
            while new_position < new_end && iszero(new_A.nzval[new_position])
                new_position += 1
            end
            old_row = old_position < old_end ?
                      old_to_new_row[old_A.rowval[old_position]] : typemax(Int)
            new_row = new_position < new_end ? new_A.rowval[new_position] : typemax(Int)
            old_row == typemax(Int) && new_row == typemax(Int) && break
            if old_row == new_row
                old_A.nzval[old_position] == new_A.nzval[new_position] ||
                    (dirty[new_row] = true)
                old_position += 1
                new_position += 1
            elseif old_row < new_row
                dirty[old_row] = true
                old_position += 1
            else
                dirty[new_row] = true
                new_position += 1
            end
        end
    end
    return dirty
end

_reduction_map(step::PresolveMap) = step
_reduction_map(step::AbstractPostsolveStep) =
    hasproperty(step, :map) && getproperty(step, :map) isa PresolveMap ?
    getproperty(step, :map) : nothing

function _advance_propagation_trace!(trace::PropagationTrace, next::PresolveResult)
    isnothing(trace.reference) && return trace
    map = _reduction_map(only(next.postsolve_stack))
    if isnothing(map)
        trace.reference = nothing
        return trace
    end
    trace.row_origin = trace.row_origin[map.rows]
    trace.column_origin = trace.column_origin[map.columns]
    trace.pending = trace.pending[map.rows]
    return trace
end

function _reset_propagation_trace!(trace::PropagationTrace,
                                   next::PresolveResult,
                                   changed_columns::BitVector)
    problem = next.problem
    pending = falses(size(problem.A, 1))
    if !isempty(next.postsolve_stack)
        map = _reduction_map(only(next.postsolve_stack))
        if isnothing(map)
            trace.reference = nothing
            return trace
        end
        for (column, old_column) in enumerate(map.columns)
            changed_columns[old_column] &&
                _mark_incident_rows!(pending, problem.A, column)
        end
    end
    trace.reference = problem
    trace.row_origin = collect(1:size(problem.A, 1))
    trace.column_origin = collect(1:size(problem.A, 2))
    trace.pending = pending
    return trace
end
