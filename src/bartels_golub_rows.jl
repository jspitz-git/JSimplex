# A run of pure adjacent swaps is one row rotation. Rotate each packed column
# once, including its values, and rotate the owned incidence lists identically.
function _rotate_upper_rows!(upper, columns_by_row, affected, marks::Vector{T},
                             first::Int, last::Int) where {T}
    first == last && return nothing
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
        column = upper[column_index]
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
