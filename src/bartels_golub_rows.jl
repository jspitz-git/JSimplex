# Replay eliminations in stable physical coordinates. Permutations change only
# the map while extending the cache, not every RHS traversing the same history.
function _sync_bartels_golub_rows!(factor::BartelsGolubFactorization)
    cache = factor.row_cache
    order = cache.order
    for index in (cache.update_count + 1):length(factor.updates)
        for step in factor.updates[index].steps
            row = step.row
            if step.last > row
                old = order[row]
                for position in row:step.last
                    order[position] = order[position + 1]
                end
                order[step.last + 1] = old
            elseif step.swapped
                order[row], order[row + 1] = order[row + 1], order[row]
            end
            iszero(step.multiplier) || push!(cache.operations,
                (order[row + 1], order[row], step.multiplier))
        end
        cache.update_count = index
    end
    return cache
end

function _apply_dense_row_updates!(vector, factor::BartelsGolubFactorization)
    isempty(factor.updates) && return vector
    cache = _sync_bartels_golub_rows!(factor)
    for (target, source, multiplier) in cache.operations
        vector[target] -= multiplier * vector[source]
    end
    # The forward solve rejects factor.work as its destination.
    for row in eachindex(cache.order)
        factor.work[row] = vector[cache.order[row]]
    end
    copyto!(vector, factor.work)
    return vector
end

function _apply_dense_transposed_row_updates!(vector, factor::BartelsGolubFactorization)
    isempty(factor.updates) && return vector
    cache = _sync_bartels_golub_rows!(factor)
    # The incoming transpose RHS has already been gathered into factor.work;
    # factor.spike is free even when it originally held the caller's RHS.
    for row in eachindex(cache.order)
        factor.spike[cache.order[row]] = vector[row]
    end
    copyto!(vector, factor.spike)
    for (target, source, multiplier) in Iterators.reverse(cache.operations)
        vector[source] -= multiplier * vector[target]
    end
    return vector
end

function _reset_dense_row_cache!(factor::BartelsGolubFactorization, n::Int)
    cache = factor.row_cache
    resize!(cache.order, n)
    for row in 1:n
        cache.order[row] = row
    end
    empty!(cache.operations)
    cache.update_count = 0
    return nothing
end

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
