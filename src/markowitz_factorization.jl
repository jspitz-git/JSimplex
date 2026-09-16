# Sparse Markowitz elimination followed by a dense trailing Schur complement.
# The column threshold limits the size of multipliers in the sparse L factor.
struct PackedFactorVector{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
end

struct MarkowitzBackend{T<:Real,F}
    dimension::Int
    sparse_pivots::Int
    row_order::Vector{Int}
    column_order::Vector{Int}
    lower::Vector{PackedFactorVector{T}}
    upper::Vector{PackedFactorVector{T}}
    diagonal::Vector{T}
    core::F
    work::Vector{T}
    core_work::Vector{T}
end

_backend_dimension(backend::MarkowitzBackend) = backend.dimension
_factorize_basis(B::AbstractMatrix, ::Val{:markowitz}) = MarkowitzBackend(B)

function _markowitz_backend(::Type{T}, n::Int, row_order::Vector{Int},
                            column_order::Vector{Int},
                            lower::Vector{PackedFactorVector{T}},
                            upper::Vector{PackedFactorVector{T}},
                            diagonal::Vector{T}, core_matrix::Matrix{T}) where {T<:Real}
    core = lu(core_matrix)
    return MarkowitzBackend{T,typeof(core)}(
        n, length(diagonal), row_order, column_order, lower, upper, diagonal,
        core, zeros(T, n), zeros(T, size(core_matrix, 1)),
    )
end

function _markowitz_set_entry!(rows::Vector{Dict{Int,T}},
                               columns::Vector{Dict{Int,T}},
                               singleton_rows::Vector{Int},
                               singleton_columns::Vector{Int},
                               row::Int, column::Int, value::T,
                               nonzeros::Int) where {T<:Real}
    row_data = rows[row]
    column_data = columns[column]
    old_row_count = length(row_data)
    old_column_count = length(column_data)
    present = haskey(row_data, column)
    if iszero(value)
        if present
            delete!(row_data, column)
            delete!(column_data, row)
            nonzeros -= 1
        end
    else
        row_data[column] = value
        column_data[row] = value
        nonzeros += !present
    end
    old_row_count != 1 && length(row_data) == 1 && push!(singleton_rows, row)
    old_column_count != 1 && length(column_data) == 1 &&
        push!(singleton_columns, column)
    return nonzeros
end

function _markowitz_column_maximum(column::Dict{Int,T}) where {T<:Real}
    maximum_value = zero(T)
    for value in values(column)
        magnitude = _pivot_magnitude(value)
        magnitude > maximum_value && (maximum_value = magnitude)
    end
    return maximum_value
end

_markowitz_threshold_pass(magnitude::T, column_maximum::T) where {T<:Real} =
    magnitude >= column_maximum / T(10)

# Stored BigFloat values may have more bits than the current working precision.
# Give the product four extra bits so multiplying by 10 is exact, without
# changing global MPFR precision or expanding large binary exponents to rationals.
function _markowitz_threshold_pass(magnitude::BigFloat, column_maximum::BigFloat)
    product = BigFloat(precision=max(precision(magnitude),
                                     precision(column_maximum)) + 4)
    ccall((:mpfr_mul_si, Base.MPFR.libmpfr), Cint,
          (Ref{BigFloat}, Ref{BigFloat}, Clong, Base.MPFR.MPFRRoundingMode),
          product, magnitude, Clong(10), Base.MPFR.MPFRRoundNearest)
    return product >= column_maximum
end

function _markowitz_pivot(rows::Vector{Dict{Int,T}}, columns::Vector{Dict{Int,T}},
                          active_rows::BitVector, active_columns::BitVector,
                          singleton_rows::Vector{Int},
                          singleton_columns::Vector{Int}) where {T<:Real}
    while !isempty(singleton_columns)
        column = pop!(singleton_columns)
        active_columns[column] && length(columns[column]) == 1 || continue
        return first(keys(columns[column])), column
    end
    while !isempty(singleton_rows)
        row = pop!(singleton_rows)
        active_rows[row] && length(rows[row]) == 1 || continue
        column = first(keys(rows[row]))
        value = rows[row][column]
        _markowitz_threshold_pass(_pivot_magnitude(value),
                                  _markowitz_column_maximum(columns[column])) &&
            return row, column
    end

    best_row = 0
    best_column = 0
    best_score = typemax(Int)
    best_magnitude = zero(T)
    for column in eachindex(columns)
        active_columns[column] || continue
        column_data = columns[column]
        column_maximum = _markowitz_column_maximum(column_data)
        column_count = length(column_data)
        for (row, value) in column_data
            magnitude = _pivot_magnitude(value)
            _markowitz_threshold_pass(magnitude, column_maximum) || continue
            score = (length(rows[row]) - 1) * (column_count - 1)
            if score < best_score || (score == best_score && magnitude > best_magnitude)
                best_row = row
                best_column = column
                best_score = score
                best_magnitude = magnitude
            end
        end
    end
    return best_row, best_column
end

function MarkowitzBackend(B::AbstractMatrix{T}) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    n, width = size(B)
    n == width || throw(DimensionMismatch("basis matrix must be square"))
    sparse_basis = SparseMatrixCSC{T,Int}(B)
    lower = PackedFactorVector{T}[]
    upper = PackedFactorVector{T}[]
    diagonal = T[]
    if 2 * count(!iszero, sparse_basis.nzval) >= n * n
        return _markowitz_backend(T, n, collect(1:n), collect(1:n),
                                  lower, upper, diagonal, Matrix{T}(B))
    end

    rows = [Dict{Int,T}() for _ in 1:n]
    columns = [Dict{Int,T}() for _ in 1:n]
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
    active_rows = trues(n)
    active_columns = trues(n)
    singleton_rows = Int[row for row in 1:n if length(rows[row]) == 1]
    singleton_columns = Int[column for column in 1:n if length(columns[column]) == 1]
    row_order = Int[]
    column_order = Int[]
    affected_rows = Int[]

    while length(row_order) < n
        remaining = n - length(row_order)
        2 * nonzeros >= remaining * remaining && break
        pivot_row, pivot_column = _markowitz_pivot(
            rows, columns, active_rows, active_columns,
            singleton_rows, singleton_columns,
        )
        pivot_row == 0 && throw(LinearAlgebra.SingularException(length(row_order) + 1))
        pivot = rows[pivot_row][pivot_column]
        push!(row_order, pivot_row)
        push!(column_order, pivot_column)
        push!(diagonal, pivot)

        upper_indices = Int[]
        upper_values = T[]
        for (column, value) in rows[pivot_row]
            column == pivot_column && continue
            push!(upper_indices, column)
            push!(upper_values, value)
        end
        push!(upper, PackedFactorVector{T}(upper_indices, upper_values))

        empty!(affected_rows)
        for row in keys(columns[pivot_column])
            row == pivot_row || push!(affected_rows, row)
        end
        lower_indices = Int[]
        lower_values = T[]
        for row in affected_rows
            multiplier = rows[row][pivot_column] / pivot
            push!(lower_indices, row)
            push!(lower_values, multiplier)
            for index in eachindex(upper_indices)
                column = upper_indices[index]
                value = get(rows[row], column, zero(T)) -
                        multiplier * upper_values[index]
                nonzeros = _markowitz_set_entry!(
                    rows, columns, singleton_rows, singleton_columns,
                    row, column, value, nonzeros,
                )
            end
            nonzeros = _markowitz_set_entry!(
                rows, columns, singleton_rows, singleton_columns,
                row, pivot_column, zero(T), nonzeros,
            )
        end
        push!(lower, PackedFactorVector{T}(lower_indices, lower_values))
        for column in upper_indices
            nonzeros = _markowitz_set_entry!(
                rows, columns, singleton_rows, singleton_columns,
                pivot_row, column, zero(T), nonzeros,
            )
        end
        nonzeros = _markowitz_set_entry!(
            rows, columns, singleton_rows, singleton_columns,
            pivot_row, pivot_column, zero(T), nonzeros,
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
    row_positions = zeros(Int, n)
    column_positions = zeros(Int, n)
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
    core_matrix = zeros(T, core_dimension, core_dimension)
    for local_row in 1:core_dimension
        row = row_order[sparse_pivots + local_row]
        for (column, value) in rows[row]
            core_matrix[local_row, column_positions[column] - sparse_pivots] = value
        end
    end
    return _markowitz_backend(T, n, row_order, column_order,
                              lower, upper, diagonal, core_matrix)
end

function _backend_forward_solve!(destination::Vector{T},
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

function _backend_transpose_solve!(destination::Vector{T},
                                   backend::MarkowitzBackend{T},
                                   rhs::AbstractVector) where {T}
    n = backend.dimension
    sparse_pivots = backend.sparse_pivots
    work = backend.work
    for index in 1:n
        work[index] = rhs[backend.column_order[index]]
    end
    for pivot in 1:sparse_pivots
        value = work[pivot] / backend.diagonal[pivot]
        work[pivot] = value
        row = backend.upper[pivot]
        for index in eachindex(row.indices)
            work[row.indices[index]] -= row.values[index] * value
        end
    end
    for index in eachindex(backend.core_work)
        backend.core_work[index] = work[sparse_pivots + index]
    end
    isempty(backend.core_work) || ldiv!(transpose(backend.core), backend.core_work)
    for index in eachindex(backend.core_work)
        work[sparse_pivots + index] = backend.core_work[index]
    end
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        column = backend.lower[pivot]
        for index in eachindex(column.indices)
            value -= column.values[index] * work[column.indices[index]]
        end
        work[pivot] = value
    end
    for index in 1:n
        destination[backend.row_order[index]] = work[index]
    end
    return destination
end

_refactorize_backend(::MarkowitzBackend{T}, B::AbstractMatrix{T}) where {T} =
    MarkowitzBackend(B)

function refactorize!(factor::PFIFactorization{T,F}, B::AbstractMatrix{T}) where {T<:Real,F<:MarkowitzBackend}
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    resize!(factor.work, _backend_dimension(new_base))
    empty!(factor.updates)
    return factor
end

function _copy_backend(backend::MarkowitzBackend{T,F}) where {T,F}
    return MarkowitzBackend{T,F}(
        backend.dimension, backend.sparse_pivots,
        backend.row_order, backend.column_order, backend.lower, backend.upper,
        backend.diagonal, backend.core,
        similar(backend.work), similar(backend.core_work),
    )
end
