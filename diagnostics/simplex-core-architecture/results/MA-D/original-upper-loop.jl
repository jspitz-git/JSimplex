    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = backend.upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / backend.diagonal[pivot]
    end
