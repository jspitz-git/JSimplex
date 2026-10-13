function _construct_markowitz(B::AbstractMatrix{T}, workspace,
                              ::Type{D}, candidate=nothing) where {T<:Real,D<:AbstractDict{Int,T}}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    n, width = size(B)
    n == width || throw(DimensionMismatch("basis matrix must be square"))
    lower_pool = isnothing(candidate) ? PackedFactorVector{T}[] : candidate.lower_pool
    upper_pool = isnothing(candidate) ? PackedFactorVector{T}[] : candidate.upper_pool
    lower = isnothing(candidate) ? PackedFactorVector{T}[] :
        _recycle_markowitz_vectors!(candidate.lower,lower_pool)
    upper = isnothing(candidate) ? PackedFactorVector{T}[] :
        _recycle_markowitz_vectors!(candidate.upper,upper_pool)
    diagonal = isnothing(candidate) ? T[] : empty!(candidate.diagonal)
    row_order = isnothing(candidate) ? Int[] : empty!(candidate.row_order)
    column_order = isnothing(candidate) ? Int[] : empty!(candidate.column_order)
    if B isa StridedMatrix{T} && 2 * count(!iszero, B) >= n * n
        append!(row_order,1:n)
        append!(column_order,1:n)
        core_matrix = _markowitz_core_matrix(T,n,candidate)
        copyto!(core_matrix,B)
        return _markowitz_backend(T, n, row_order, column_order,
                                  lower, upper, diagonal, core_matrix, workspace, D,
                                  candidate, lower_pool, upper_pool)
    end
    # Elimination owns its dictionaries and dense core; the CSC is read-only.
    sparse_basis = convert(SparseMatrixCSC{T,Int}, B)
    if 2 * count(!iszero, sparse_basis.nzval) >= n * n
        append!(row_order,1:n)
        append!(column_order,1:n)
        core_matrix = _markowitz_core_matrix(T,n,candidate)
        copyto!(core_matrix,B)
        return _markowitz_backend(T, n, row_order, column_order,
                                  lower, upper, diagonal, core_matrix, workspace, D,
                                  candidate, lower_pool, upper_pool)
    end

    workspace = isnothing(workspace) ? MarkowitzWorkspace(T,D) : workspace
    _reset_markowitz_workspace!(workspace,n)
    entry_zero = zero(T)
    rows = workspace.rows
    columns = workspace.columns
    for column in 1:n
        for pointer in nzrange(sparse_basis, column)
            row = sparse_basis.rowval[pointer]
            value = sparse_basis.nzval[pointer]
            iszero(value) && continue
            rows[row][column] = value
            columns[column][row] = value
        end
    end
    nonzeros = sum(length, rows)
    active_rows = workspace.active_rows
    active_columns = workspace.active_columns
    singleton_rows = workspace.singleton_rows
    singleton_columns = workspace.singleton_columns
    doubleton_columns = workspace.doubleton_columns
    for row in 1:n
        length(rows[row]) == 1 && push!(singleton_rows,row)
    end
    for column in 1:n
        length(columns[column]) == 1 && push!(singleton_columns,column)
        length(columns[column]) == 2 && push!(doubleton_columns,column)
    end
    affected_rows = workspace.affected_rows

    while length(row_order) < n
        remaining = n - length(row_order)
        2 * nonzeros >= remaining * remaining && break
        pivot_row, pivot_column = _markowitz_pivot(
            rows, columns, active_rows, active_columns,
            singleton_rows, singleton_columns, doubleton_columns,
            (workspace.column_maxima,workspace.column_maxima_valid), true,
        )
        pivot_row == 0 && throw(LinearAlgebra.SingularException(length(row_order) + 1))
        pivot = rows[pivot_row][pivot_column]
        push!(row_order, pivot_row)
        push!(column_order, pivot_column)
        push!(diagonal, pivot)

        upper_vector = _take_markowitz_vector!(upper_pool)
        upper_indices = upper_vector.indices
        upper_values = upper_vector.values
        for (column, value) in rows[pivot_row]
            column == pivot_column && continue
            push!(upper_indices, column)
            push!(upper_values, value)
        end
        push!(upper, upper_vector)

        # Elimination and pivot-row removal touch only these columns. Other
        # cached maxima remain valid, regardless of changed row counts.
        workspace.column_maxima_valid[pivot_column] = false
        for column in upper_indices
            workspace.column_maxima_valid[column] = false
        end

        empty!(affected_rows)
        for row in keys(columns[pivot_column])
            row == pivot_row || push!(affected_rows, row)
        end
        lower_vector = _take_markowitz_vector!(lower_pool)
        lower_indices = lower_vector.indices
        lower_values = lower_vector.values
        for row in affected_rows
            multiplier = rows[row][pivot_column] / pivot
            push!(lower_indices, row)
            push!(lower_values, multiplier)
            for index in eachindex(upper_indices)
                column = upper_indices[index]
                value = get(rows[row], column, entry_zero) -
                        multiplier * upper_values[index]
                nonzeros = _markowitz_set_entry!(
                    rows, columns, singleton_rows, singleton_columns, doubleton_columns,
                    row, column, value, nonzeros,
                )
            end
            nonzeros = _markowitz_set_entry!(
                rows, columns, singleton_rows, singleton_columns, doubleton_columns,
                row, pivot_column, entry_zero, nonzeros,
            )
        end
        push!(lower, lower_vector)
        for column in upper_indices
            nonzeros = _markowitz_set_entry!(
                rows, columns, singleton_rows, singleton_columns, doubleton_columns,
                pivot_row, column, entry_zero, nonzeros,
            )
        end
        nonzeros = _markowitz_set_entry!(
            rows, columns, singleton_rows, singleton_columns, doubleton_columns,
            pivot_row, pivot_column, entry_zero, nonzeros,
        )
        active_rows[pivot_row] = false
        active_columns[pivot_column] = false
    end

    for row in 1:n
        active_rows[row] && push!(row_order, row)
    end
    for column in 1:n
        active_columns[column] && push!(column_order, column)
    end
    row_positions = workspace.row_positions
    column_positions = workspace.column_positions
    for position in 1:n
        row_positions[row_order[position]] = position
        column_positions[column_order[position]] = position
    end
    for vector in lower
        for index in eachindex(vector.indices)
            vector.indices[index] = row_positions[vector.indices[index]]
        end
    end
    for vector in upper
        for index in eachindex(vector.indices)
            vector.indices[index] = column_positions[vector.indices[index]]
        end
    end

    sparse_pivots = length(diagonal)
    core_dimension = n - sparse_pivots
    core_matrix = _markowitz_core_matrix(T,core_dimension,candidate)
    fill!(core_matrix,zero(T))
    for local_row in 1:core_dimension
        row = row_order[sparse_pivots + local_row]
        for (column, value) in rows[row]
            core_matrix[local_row, column_positions[column] - sparse_pivots] = value
        end
    end
    return _markowitz_backend(T, n, row_order, column_order,
                              lower, upper, diagonal, core_matrix, workspace, D,
                              candidate, lower_pool, upper_pool)
end
