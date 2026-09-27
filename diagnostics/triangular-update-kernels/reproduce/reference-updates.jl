# Diagnostic snapshots of replacement and FTRAN kernels from 17be8a3.
@eval JSimplex begin
function _reference_prepare_spike!(factor::AbstractTriangularBasisFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer,
                         zero_tolerance::Real) where {T}
    tolerance = convert(T, zero_tolerance)
    isfinite(tolerance) && tolerance >= zero(T) ||
        throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    n = _backend_dimension(factor.base)
    length(tableau_column) == n ||
        throw(DimensionMismatch("tableau column length must match the basis dimension"))
    pivot = Int(pivot_row)
    checkbounds(tableau_column, pivot)
    _pivot_magnitude(convert(T, tableau_column[pivot])) > tolerance ||
        throw(LinearAlgebra.ZeroPivotException(pivot))
    position = factor.positions[pivot]
    fill!(factor.spike, zero(T))
    for column_index in 1:n
        column = factor.upper[column_index]
        value = convert(T, tableau_column[factor.column_order[column_index]])
        # Packed rows and paired values are owned by the factor; callers
        # validate vector dimensions before entering this coefficient loop.
        @inbounds for index in eachindex(column.indices)
            factor.spike[column.indices[index]] += column.values[index] * value
        end
    end
    return position
end


end
@eval JSimplex begin
function _reference_forward_solve!(destination::Vector{T},
                        factor::AbstractTriangularBasisFactorization{T},
                        rhs::StridedVector{T}) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    n = _check_triangular_dimensions(factor, destination, rhs)
    source = destination === rhs ? copyto!(factor.work, rhs) : rhs
    _backend_forward_solve!(destination, factor.base, source)
    _apply_dense_row_updates!(destination, factor)
    _upper_backsolve!(destination, factor.upper, _dense_upper_columns(factor))
    for column in 1:n
        factor.work[factor.column_order[column]] = destination[column]
    end
    copyto!(destination, factor.work)
    return destination
end

end
@eval JSimplex begin
function _reference_replace!(factor::SuhlSuhlFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _reference_prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _invalidate_sparse_upper!(factor)
    n = length(factor.upper)
    last = n
    while iszero(factor.spike[last])
        last -= 1
    end
    _rotate_columns!(factor, position, last)

    # Move the leaving row only as far as the spike reaches. Columns beyond
    # that point stay in place, but their entry in the moved row may change.
    stored_entries = 0
    for column in factor.upper
        slot, old = _upper_entry(column, position)
        iszero(old) || _set_upper_value_at!(column, position, zero(T), slot)
        start = searchsortedfirst(column.indices, position + 1)
        for index in start:length(column.indices)
            column.indices[index] > last && break
            column.indices[index] -= 1
        end
        iszero(old) || _set_upper_value!(column, last, old)
        stored_entries += length(column.indices)
    end

    use_row_index = last - position >= 16 && stored_entries ÷ n <= (last - position) ÷ 4
    row_index_ready = false
    indices, multipliers = _take_triangular_update_buffers!(factor)
    for column_index in position:(last - 1)
        column = factor.upper[column_index]
        slot, old = _upper_entry(column, last)
        multiplier = -(old / _upper_value(column, column_index))
        _set_upper_value_at!(column, last, zero(T), slot)
        iszero(multiplier) && continue
        push!(indices, column_index)
        push!(multipliers, multiplier)
        if use_row_index && !row_index_ready
            _triangular_row_columns!(factor, column_index, last - 1)
            row_index_ready = true
        end
        trailing_columns = use_row_index ? factor.row_columns[column_index] : (column_index + 1):n
        for trailing in trailing_columns
            trailing_column = factor.upper[trailing]
            value = _upper_value(trailing_column, column_index)
            iszero(value) && continue
            slot, old = _upper_entry(trailing_column, last)
            _set_upper_value_at!(trailing_column, last, old + multiplier * value, slot)
        end
    end
    push!(factor.updates, SuhlSuhlUpdate{T}(position, last, indices, multipliers))
    return factor
end

end
@eval JSimplex begin
function _reference_replace!(factor::ForrestTomlinFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _reference_prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _invalidate_sparse_upper!(factor)
    _rotate_columns!(factor, position)
    n = length(factor.upper)
    # Rotate the leaving row to the bottom. This leaves one row spike.
    stored_entries = 0
    for column in factor.upper
        start = searchsortedfirst(column.indices, position)
        has_pivot = start <= length(column.indices) && column.indices[start] == position
        old = has_pivot ? column.values[start] : zero(T)
        if has_pivot
            deleteat!(column.indices, start)
            deleteat!(column.values, start)
        end
        for index in start:length(column.indices)
            column.indices[index] -= 1
        end
        if has_pivot
            push!(column.indices, n)
            push!(column.values, old)
        end
        stored_entries += length(column.indices)
    end
    use_row_index = n - position >= 16 && stored_entries ÷ n <= (n - position) ÷ 4
    row_index_ready = false
    indices, multipliers = _take_triangular_update_buffers!(factor)
    for column_index in position:(n - 1)
        column = factor.upper[column_index]
        slot, old = _upper_entry(column, n)
        multiplier = -(old / _upper_value(column, column_index))
        _set_upper_value_at!(column, n, zero(T), slot)
        iszero(multiplier) && continue
        push!(indices, column_index)
        push!(multipliers, multiplier)
        if use_row_index && !row_index_ready
            _triangular_row_columns!(factor, column_index, n - 1)
            row_index_ready = true
        end
        trailing_columns = use_row_index ? factor.row_columns[column_index] : (column_index + 1):n
        for trailing in trailing_columns
            trailing_column = factor.upper[trailing]
            value = _upper_value(trailing_column, column_index)
            iszero(value) && continue
            slot, old = _upper_entry(trailing_column, n)
            _set_upper_value_at!(trailing_column, n, old + multiplier * value, slot)
        end
    end
    push!(factor.updates, ForrestTomlinUpdate{T}(position, indices, multipliers))
    return factor
end

end
@eval JSimplex begin
function _reference_replace!(factor::BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _reference_prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _invalidate_sparse_upper!(factor)
    _ensure_bartels_golub_incidence!(factor)
    _replace_bartels_golub_incidence_column!(factor, position)
    _rotate_columns!(factor, position)
    n = length(factor.upper)
    columns_by_row = factor.row_columns
    # The spike has been packed into the replacement column. Reuse its scratch
    # as incidence marks while batching permutations, without another vector.
    fill!(factor.spike, zero(T))
    steps = _take_bartels_golub_steps!(factor)
    run_start = 0
    run_last = 0
    completed_through = position - 1
    for column_index in position:(n - 1)
        column_index <= completed_through && continue
        last_pure = _last_pure_bartels_golub_swap(factor.upper, column_index)
        if last_pure > column_index
            _rotate_upper_rows!(factor.upper, columns_by_row, factor.affected,
                                factor.spike, column_index, last_pure + 1, factor.positions)
            run_start == 0 && (run_start = column_index)
            run_last = last_pure
            completed_through = last_pure
            continue
        end
        column = factor.upper[column_index]
        swapped = _pivot_magnitude(_upper_value(column, column_index + 1)) >
                  _pivot_magnitude(_upper_value(column, column_index))
        if swapped
            _swap_upper_rows!(factor.upper, columns_by_row, factor.affected,
                              column_index, factor.positions)
        end
        pivot = _upper_value(column, column_index)
        iszero(pivot) && throw(LinearAlgebra.ZeroPivotException(column_index))
        slot, old = _upper_entry(column, column_index + 1)
        multiplier = old / pivot
        _set_upper_value_at!(factor.upper, columns_by_row,
                            column_index, column_index + 1, zero(T), slot,
                            factor.column_order[column_index])
        if !iszero(multiplier)
            for column_id in columns_by_row[column_index]
                trailing = factor.positions[column_id]
                trailing <= column_index && continue
                trailing_column = factor.upper[trailing]
                value = _upper_value(trailing_column, column_index)
                slot, old = _upper_entry(trailing_column, column_index + 1)
                _set_upper_value_at!(factor.upper, columns_by_row,
                                    trailing, column_index + 1, old - multiplier * value, slot, column_id)
            end
        end
        if swapped && iszero(multiplier)
            run_start == 0 && (run_start = column_index)
            run_last = column_index
            continue
        end
        if run_start != 0
            push!(steps, BartelsGolubStep{T}(run_start, run_last, true, zero(T)))
            run_start = 0
        end
        (swapped || !iszero(multiplier)) &&
            push!(steps, BartelsGolubStep{T}(
                column_index, column_index, swapped, multiplier,
            ))
    end
    run_start == 0 ||
        push!(steps, BartelsGolubStep{T}(run_start, run_last, true, zero(T)))
    push!(factor.updates, BartelsGolubUpdate{T}(steps))
    return factor
end

# Only the target row changes during FT/SS elimination. Index the other rows
# once, in ascending column order; the target row is never queried as a pivot.
end
