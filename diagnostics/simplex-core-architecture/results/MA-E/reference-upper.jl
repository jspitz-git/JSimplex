function reference_upper!(work, upper, diagonal, sparse_pivots)
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / diagonal[pivot]
    end
    return work
end
