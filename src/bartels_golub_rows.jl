# A run of pure adjacent swaps is one row rotation. Rotate each packed column
# once, including its values, and rotate the owned incidence lists identically.
function _rotate_upper_rows!(upper, columns_by_row, affected, marks::Vector{T},
                             first::Int, last::Int, positions=eachindex(upper)) where {T}
    first == last && return nothing
    # Stable identities let unaffected rows follow the permutation implicitly.
    if _stable_rotate_upper_rows!(upper, first, last,
                                  (positions[id] for id in columns_by_row[first]))
        old = columns_by_row[first]
        for row in first:(last - 1)
            columns_by_row[row] = columns_by_row[row + 1]
        end
        columns_by_row[last] = old
        empty!(affected)
        return nothing
    end
    # marks is zero on entry and exit. Visit each affected column only once;
    # scanning every column for many short rotations would be quadratic.
    empty!(affected)
    for row in first:last
        for column_index in columns_by_row[row]
            if iszero(marks[column_index])
                marks[column_index] = one(T)
                push!(affected, column_index)
            end
        end
    end
    for column_index in affected
        marks[column_index] = zero(T)
        column = upper[positions[column_index]]
        indices, values = column.indices, column.values
        start = searchsortedfirst(indices, first)
        finish = searchsortedlast(indices, last)
        start > finish && continue
        if indices[start] == first
            old = values[start]
            for position in start:(finish - 1)
                indices[position] = indices[position + 1] - 1
                values[position] = values[position + 1]
            end
            indices[finish] = last
            values[finish] = old
        else
            for position in start:finish
                indices[position] -= 1
            end
        end
    end
    old = columns_by_row[first]
    for row in first:(last - 1)
        columns_by_row[row] = columns_by_row[row + 1]
    end
    columns_by_row[last] = old
    return nothing
end

function _last_pure_bartels_golub_swap(upper, first::Int)
    for column_index in first:(length(upper) - 1)
        column = upper[column_index]
        # Previous pure swaps carry the initial top row down through the run.
        # Require exact zero; underflow and all nonzero eliminations continue
        # through the original scalar path with its original pivot decisions.
        iszero(_upper_value(column, first)) || return column_index - 1
        lower = _upper_value(column, column_index + 1)
        _pivot_magnitude(lower) > zero(lower) || return column_index - 1
    end
    return length(upper) - 1
end


# Column identities are basis positions, not current positions in U. Q already
# maps between them, so rotating columns need not rebuild every incidence list.
function _ensure_bartels_golub_incidence!(factor::BartelsGolubFactorization)
    factor.row_columns_ready && return nothing
    rows = factor.row_columns
    foreach(empty!, rows)
    for column_id in eachindex(factor.positions)
        column = factor.positions[column_id]
        for row in factor.upper[column].indices
            push!(rows[row], column_id)
        end
    end
    factor.row_columns_ready = true
    return nothing
end

function _replace_bartels_golub_incidence_column!(factor::BartelsGolubFactorization,
                                                  position::Int)
    old_indices = factor.upper[position].indices
    column_id = factor.column_order[position]
    old_position = 1
    for row in eachindex(factor.spike)
        was_stored = old_position <= length(old_indices) && old_indices[old_position] == row
        is_stored = !iszero(factor.spike[row])
        if was_stored != is_stored
            columns = factor.row_columns[row]
            slot = searchsortedfirst(columns, column_id)
            if is_stored
                _insert_bartels_golub_incidence!(columns, slot, column_id)
            else
                _delete_bartels_golub_incidence!(columns, slot)
            end
        end
        was_stored && (old_position += 1)
    end
    return nothing
end

# Preserve the vector's starting offset and reusable capacity. Base.deleteat!
# can advance it for a leading entry, forcing later insertions to allocate.
function _delete_bartels_golub_incidence!(columns::Vector{Int}, slot::Int)
    copyto!(columns, slot, columns, slot + 1, length(columns) - slot)
    resize!(columns, length(columns) - 1)
    return columns
end

function _insert_bartels_golub_incidence!(columns::Vector{Int}, slot::Int, column::Int)
    resize!(columns, length(columns) + 1)
    copyto!(columns, slot + 1, columns, slot, length(columns) - slot)
    columns[slot] = column
    return columns
end
