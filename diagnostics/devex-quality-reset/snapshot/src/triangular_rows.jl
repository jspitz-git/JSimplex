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
        row = update.indices[index]
        if _row_update_swapped(update, row)
            cache.permuted = true
            order[row], order[last] = order[last], order[row]
        end
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
    # Reverse every elimination, including dependent operations separated by
    # row swaps. Permutations are already incorporated in physical coordinates.
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
    cache.upper_dirty_from = n + 1
    cache.upper_prefix_safe = eltype(factor.work) <: Union{Float32,Float64}
    cache.upper_prefix_candidate = false
    _invalidate_prepared_spikes!(factor)
    return nothing
end

function _invalidate_dense_upper!(factor::ComposedRowFactorization, first_column::Int=1)
    cache = factor.row_cache
    # Rotations and eliminations cannot affect the triangular prefix before the
    # leaving column. Multiple pending mutations retain the earliest boundary.
    cache.upper_dirty_from = cache.upper_dirty ? min(cache.upper_dirty_from, first_column) : first_column
    cache.upper_dirty = true
    cache.upper_prefix_safe = false
    _invalidate_prepared_spikes!(factor)
    return nothing
end

function _dense_upper_columns(factor::Union{ForrestTomlinFactorization{T},
        SuhlSuhlFactorization{T},BartelsGolubFactorization{T}}) where {T<:Union{Float32,Float64}}
    cache = factor.row_cache
    if cache.upper_dirty
        first_column = cache.upper_dirty_from
        resize!(cache.active_upper, searchsortedfirst(cache.active_upper, first_column) - 1)
        for index in first_column:length(factor.upper)
            column = factor.upper[index]
            # Explicit off-diagonal zeros still participate in arithmetic.
            identity = length(column.indices) == 1 && column.indices[1] == index &&
                column.values[1] == one(T)
            identity || push!(cache.active_upper, index)
            # New values were checked at their stores. Validate the diagonal in
            # the existing dirty-column pass, before a solve reads eligibility.
            if !identity && cache.upper_prefix_safe &&
                    (isempty(column.indices) || column.indices[end] != index ||
                     iszero(column.values[end]))
                cache.upper_prefix_safe = false
            end
        end
        cache.upper_dirty = false
        cache.upper_dirty_from = length(factor.upper) + 1
    end
    return cache.active_upper
end

# Hand off vectors between solve stages without materializing intermediate
# logical permutations. The two coordinate maps need not agree on copied BG.
function _finish_triangular_forward!(destination, factor::ComposedRowFactorization, prepared, n)
    cache = _sync_triangular_rows!(factor)
    operation = _row_operation(factor)
    for (target, source, multiplier) in cache.operations
        _compiled_row_operation!(destination, target, source, multiplier, operation)
    end
    order = _upper_order(factor.upper)
    if isnothing(order)
        for row in 1:n
            factor.work[row] = destination[cache.order[row]]
        end
        _save_prepared_spike!(prepared, factor.work)
        _upper_backsolve!(factor.work, factor.upper, _dense_upper_columns(factor))
        for column in 1:n
            destination[factor.column_order[column]] = factor.work[column]
        end
    else
        for row in 1:n
            factor.work[order.order[row]] = destination[cache.order[row]]
        end
        _save_prepared_spike!(prepared, factor.work, order)
        _stable_upper_backsolve_physical!(factor.work, factor.upper,
                                         _dense_upper_columns(factor), order)
        for column in 1:n
            destination[factor.column_order[column]] = factor.work[order.order[column]]
        end
    end
    return destination
end

function _finish_triangular_transpose!(destination, factor::ComposedRowFactorization, order)
    cache = _sync_triangular_rows!(factor)
    if isnothing(order) && !cache.permuted
        source = factor.work
    else
        for row in eachindex(cache.order)
            factor.spike[cache.order[row]] = factor.work[isnothing(order) ? row : order.order[row]]
        end
        source = factor.spike
    end
    operation = _row_operation(factor)
    for (target, origin, multiplier) in Iterators.reverse(cache.operations)
        _compiled_row_operation!(source, origin, target, multiplier, operation)
    end
    # Public callers may use spike as output; backend input must remain separate.
    destination === source && (source = copyto!(factor.work, source))
    return _backend_transpose_solve!(destination, factor.base, source)
end

# Unit RHS preparation initializes the strict triangular prefix to +0. With
# finite coefficients and nonzero diagonals, only its divisions can affect the
# signed zeros; the suffix retains the original scalar subtraction order.
function _transpose_upper_for_rhs!(factor::Union{ForrestTomlinFactorization{T},
        SuhlSuhlFactorization{T},BartelsGolubFactorization{T}},
        rhs::_UnitTransposeRHS{T}, columns, ::Nothing) where {T<:Union{Float32,Float64}}
    if factor.row_cache.upper_prefix_safe
        split = searchsortedfirst(columns, factor.positions[rhs.row])
        if split > 1
            for slot in 1:(split - 1)
                j = columns[slot]
                factor.work[j] /= _upper_diagonal(factor.upper[j], j)
            end
            return _upper_transpose_solve!(factor.work, factor.upper, @view(columns[split:end]))
        end
    end
    return _upper_transpose_solve!(factor.work, factor.upper, columns)
end
function _transpose_upper_for_rhs!(factor::BartelsGolubFactorization{T},
        rhs::_UnitTransposeRHS{T}, columns, order::UpperRowOrder) where {T<:Union{Float32,Float64}}
    if factor.row_cache.upper_prefix_safe
        split = searchsortedfirst(columns, factor.positions[rhs.row])
        if split > 1
            for slot in 1:(split - 1)
                j = columns[slot]
                physical = order.order[j]
                factor.work[physical] /= _upper_diagonal(factor.upper[j], j)
            end
            return _stable_upper_transpose_solve!(factor.work, factor.upper,
                                                  @view(columns[split:end]), order)
        end
    end
    return _stable_upper_transpose_solve!(factor.work, factor.upper, columns, order)
end
