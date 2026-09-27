# Replay eliminations in stable physical coordinates. Permutations change only
# the map while extending the cache, not every RHS traversing the same history.
const ComposedRowFactorization = Union{BartelsGolubFactorization,
    ForrestTomlinFactorization,SuhlSuhlFactorization}

function _rotate_row_order!(order, first, last)
    old = order[first]
    for row in first:(last - 1)
        order[row] = order[row + 1]
    end
    order[last] = old
    return nothing
end

function _append_compiled_rows!(cache, update::BartelsGolubUpdate)
    order = cache.order
    for step in update.steps
        row = step.row
        if step.last > row
            cache.permuted = true
            _rotate_row_order!(order, row, step.last + 1)
        elseif step.swapped
            cache.permuted = true
            order[row], order[row + 1] = order[row + 1], order[row]
        end
        iszero(step.multiplier) || push!(cache.operations,
            (order[row + 1], order[row], step.multiplier))
    end
    return nothing
end

_row_update_last(cache, ::ForrestTomlinUpdate) = length(cache.order)
_row_update_last(cache, update::SuhlSuhlUpdate) = update.last
function _append_compiled_rows!(cache, update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate})
    last = _row_update_last(cache, update)
    order = cache.order
    cache.permuted |= update.pivot < last
    _rotate_row_order!(order, update.pivot, last)
    for index in eachindex(update.indices)
        push!(cache.operations,
            (order[last], order[update.indices[index]], update.multipliers[index]))
    end
    return nothing
end

function _sync_triangular_rows!(factor::ComposedRowFactorization)
    cache = factor.row_cache
    for index in (cache.update_count + 1):length(factor.updates)
        _append_compiled_rows!(cache, factor.updates[index])
        cache.update_count = index
    end
    return cache
end

_row_operation(::BartelsGolubFactorization) = Val(:subtract)
_row_operation(::Union{ForrestTomlinFactorization,SuhlSuhlFactorization}) = Val(:add)
@inline _compiled_row_operation!(vector, target, source, multiplier, ::Val{:subtract}) =
    (vector[target] -= multiplier * vector[source])
@inline _compiled_row_operation!(vector, target, source, multiplier, ::Val{:add}) =
    (vector[target] += multiplier * vector[source])

function _apply_dense_row_updates!(vector, factor::ComposedRowFactorization)
    isempty(factor.updates) && return vector
    cache = _sync_triangular_rows!(factor)
    operation = _row_operation(factor)
    for (target, source, multiplier) in cache.operations
        _compiled_row_operation!(vector, target, source, multiplier, operation)
    end
    # The forward solve rejects factor.work as its destination.
    if cache.permuted
        for row in eachindex(cache.order)
            factor.work[row] = vector[cache.order[row]]
        end
        copyto!(vector, factor.work)
    end
    return vector
end

function _apply_dense_transposed_row_updates!(vector, factor::ComposedRowFactorization)
    isempty(factor.updates) && return vector
    cache = _sync_triangular_rows!(factor)
    if cache.permuted
        for row in eachindex(cache.order)
            factor.spike[cache.order[row]] = vector[row]
        end
        copyto!(vector, factor.spike)
    end
    operation = _row_operation(factor)
    # FT/SS operations within one update have distinct targets and a common,
    # unchanged source. Their transpose operations are independent; reversing
    # them preserves each target's arithmetic as well as update order.
    for (target, source, multiplier) in Iterators.reverse(cache.operations)
        _compiled_row_operation!(vector, source, target, multiplier, operation)
    end
    return vector
end

function _reset_dense_row_cache!(factor::ComposedRowFactorization, n::Int)
    cache = factor.row_cache
    resize!(cache.order, n)
    for row in 1:n
        cache.order[row] = row
    end
    empty!(cache.operations)
    cache.update_count = 0
    cache.permuted = false
    empty!(cache.active_upper)
    cache.upper_dirty = false
    _invalidate_prepared_spikes!(factor)
    return nothing
end

function _invalidate_dense_upper!(factor::ComposedRowFactorization)
    factor.row_cache.upper_dirty = true
    _invalidate_prepared_spikes!(factor)
    return nothing
end

function _dense_upper_columns(factor::Union{ForrestTomlinFactorization{T},
        SuhlSuhlFactorization{T},BartelsGolubFactorization{T}}) where {T<:Union{Float32,Float64}}
    cache = factor.row_cache
    if cache.upper_dirty
        empty!(cache.active_upper)
        for index in eachindex(factor.upper)
            column = factor.upper[index]
            # Explicit off-diagonal zeros still participate in arithmetic.
            identity = length(column.indices) == 1 && column.indices[1] == index &&
                column.values[1] == one(T)
            identity || push!(cache.active_upper, index)
        end
        cache.upper_dirty = false
    end
    return cache.active_upper
end
