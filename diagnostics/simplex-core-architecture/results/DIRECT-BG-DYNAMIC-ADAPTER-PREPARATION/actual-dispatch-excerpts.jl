# triangular_indices.jl:90-143
function _stable_upper_backsolve_physical!(work, upper, columns, order)
    for column_index in Iterators.reverse(columns)
        column = upper[column_index]
        diagonal = order.order[column_index]
        value = work[diagonal] / _upper_diagonal(column, column_index)
        work[diagonal] = value
        ids = column.indices.ids
        # Canonical packed columns have unique, ordered rows. With the
        # diagonal last, exclude it once instead of testing every coefficient.
        if !isempty(ids) && ids[end] == diagonal
            @inbounds for slot in 1:(length(ids) - 1)
                row = ids[slot]
                work[row] -= column.values[slot] * value
            end
        else
            @inbounds for slot in eachindex(ids)
                row = ids[slot]
                row == diagonal && continue
                work[row] -= column.values[slot] * value
            end
        end
    end
    return work
end

function _stable_upper_transpose_solve!(work::Vector{T}, upper,
                                        columns, order::UpperRowOrder) where {T}
    for column_index in columns
        column = upper[column_index]
        diagonal = order.order[column_index]
        value = work[diagonal]
        ids = column.indices.ids
        # Canonical packed columns have unique, ordered rows. With the
        # diagonal last, exclude it once instead of testing every coefficient.
        if !isempty(ids) && ids[end] == diagonal
            @inbounds for slot in 1:(length(ids) - 1)
                row = ids[slot]
                value -= column.values[slot] * work[row]
            end
        else
            @inbounds for slot in eachindex(ids)
                row = ids[slot]
                row == diagonal && continue
                value -= column.values[slot] * work[row]
            end
        end
        work[diagonal] = value / _upper_diagonal(column, column_index)
    end
    return work
end

# triangular_factorization.jl:172-183
function _upper_value(column::PackedUpperColumn{T}, row::Int) where {T}
    return last(_upper_entry(column, row))
end

# The position may be reused until this column's packed arrays are mutated.
function _upper_entry(column::PackedUpperColumn{T}, row::Int) where {T}
    position = searchsortedfirst(column.indices, row)
    value = position <= length(column.indices) && column.indices[position] == row ?
           column.values[position] : zero(T)
    return position, value
end


# triangular_factorization.jl:387-409
function _begin_upper_update!(factor, position)
    safe = factor.row_cache.upper_prefix_safe
    _invalidate_sparse_upper!(factor, position)
    factor.row_cache.upper_prefix_candidate = safe
    return nothing
end
function _finish_upper_update!(factor)
    factor.row_cache.upper_prefix_safe = factor.row_cache.upper_prefix_candidate
    return factor
end
@inline function _track_upper_value!(factor, value::T) where {T}
    if T <: Union{Float32,Float64} && !isfinite(value)
        factor.row_cache.upper_prefix_candidate = false
    end
    return value
end
function _copy_triangular_row_cache(factor)
    cache = TriangularRowCache(eltype(factor.work), length(factor.work))
    cache.upper_prefix_safe = factor.row_cache.upper_prefix_safe
    return cache
end

mutable struct ForrestTomlinFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}

# triangular_factorization.jl:147-170
function _packed_column!(column::PackedUpperColumn{T}, values::Vector{T}, cache=nothing) where {T}
    entry_count = count(!iszero, values)
    # Keep the same spare slot as the allocating packer for subsequent row rotation.
    capacity = entry_count + !iszero(entry_count)
    resize!(column.indices, capacity)
    resize!(column.values, capacity)
    resize!(column.indices, entry_count)
    resize!(column.values, entry_count)
    finite_entries = true
    next_entry = 1
    for row in eachindex(values)
        iszero(values[row]) && continue
        column.indices[next_entry] = row
        column.values[next_entry] = values[row]
        if T <: Union{Float32,Float64} && cache !== nothing
            finite_entries &= isfinite(values[row])
        end
        next_entry += 1
    end
    if T <: Union{Float32,Float64} && cache !== nothing
        cache.upper_prefix_candidate &= finite_entries
    end
    return column
end

