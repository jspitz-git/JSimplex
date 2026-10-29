function replace_column!(factor::BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _begin_upper_update!(factor, position)
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
                                    trailing, column_index + 1,
                                    _track_upper_value!(factor, old - multiplier * value), slot, column_id)
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
    return _finish_upper_update!(factor)
end
