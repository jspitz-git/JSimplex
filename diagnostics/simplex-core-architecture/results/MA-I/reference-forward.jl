function reference_forward!(destination::Vector{T},
                                 backend::MarkowitzBackend{T},
                                 rhs::AbstractVector) where {T}
    n = backend.dimension
    sparse_pivots = backend.sparse_pivots
    work = backend.work
    for index in 1:n
        work[index] = rhs[backend.row_order[index]]
    end
    for pivot in 1:sparse_pivots
        value = work[pivot]
        column = backend.lower[pivot]
        for index in eachindex(column.indices)
            work[column.indices[index]] -= column.values[index] * value
        end
    end
    for index in eachindex(backend.core_work)
        backend.core_work[index] = work[sparse_pivots + index]
    end
    isempty(backend.core_work) || ldiv!(backend.core, backend.core_work)
    for index in eachindex(backend.core_work)
        work[sparse_pivots + index] = backend.core_work[index]
    end
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = backend.upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / backend.diagonal[pivot]
    end
    for index in 1:n
        destination[backend.column_order[index]] = work[index]
    end
    return destination
end

