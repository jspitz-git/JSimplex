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
