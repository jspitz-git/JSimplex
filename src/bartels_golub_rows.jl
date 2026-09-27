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
