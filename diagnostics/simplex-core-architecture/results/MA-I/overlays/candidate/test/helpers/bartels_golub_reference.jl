# Scalar BG replacement from baseline 1ffdbc2, retained as an independent
# history/rounding oracle for the batched permutation implementation.
function bg_reference_replace_column!(factor::JSimplex.BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=JSimplex._is_exact(T) === Val(true) ? zero(T) :
                                              JSimplex._positive_tolerance(T, 1 // 10^12)) where {T}
    position = JSimplex._prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    JSimplex._invalidate_sparse_upper!(factor)
    JSimplex._rotate_columns!(factor, position)
    n = length(factor.upper)
    columns_by_row = JSimplex._rebuild_row_columns!(factor.row_columns, factor.upper)
    steps = JSimplex._take_bartels_golub_steps!(factor)
    run_start = 0
    run_last = 0
    for column_index in position:(n - 1)
        column = factor.upper[column_index]
        swapped = JSimplex._pivot_magnitude(JSimplex._upper_value(column, column_index + 1)) >
                  JSimplex._pivot_magnitude(JSimplex._upper_value(column, column_index))
        if swapped
            JSimplex._swap_upper_rows!(factor.upper, columns_by_row, factor.affected,
                              column_index)
        end
        pivot = JSimplex._upper_value(column, column_index)
        iszero(pivot) && throw(LinearAlgebra.ZeroPivotException(column_index))
        slot, old = JSimplex._upper_entry(column, column_index + 1)
        multiplier = old / pivot
        JSimplex._set_upper_value_at!(factor.upper, columns_by_row,
                            column_index, column_index + 1, zero(T), slot)
        if !iszero(multiplier)
            for trailing in columns_by_row[column_index]
                trailing <= column_index && continue
                trailing_column = factor.upper[trailing]
                value = JSimplex._upper_value(trailing_column, column_index)
                slot, old = JSimplex._upper_entry(trailing_column, column_index + 1)
                JSimplex._set_upper_value_at!(factor.upper, columns_by_row,
                                    trailing, column_index + 1, old - multiplier * value, slot)
            end
        end
        if swapped && iszero(multiplier)
            run_start == 0 && (run_start = column_index)
            run_last = column_index
            continue
        end
        if run_start != 0
            push!(steps, JSimplex.BartelsGolubStep{T}(run_start, run_last, true, zero(T)))
            run_start = 0
        end
        (swapped || !iszero(multiplier)) &&
            push!(steps, JSimplex.BartelsGolubStep{T}(
                column_index, column_index, swapped, multiplier,
            ))
    end
    run_start == 0 ||
        push!(steps, JSimplex.BartelsGolubStep{T}(run_start, run_last, true, zero(T)))
    push!(factor.updates, JSimplex.BartelsGolubUpdate{T}(steps))
    return factor
end

