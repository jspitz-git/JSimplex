# These updates maintain B = B₀ R⁻¹ U Q⁻¹. B₀ uses the same LU backend as PFI;
# U starts as the identity and Q records the order of its columns. Each pivot
# appends compact row operations to R, so solves need no temporary allocation.
abstract type AbstractTriangularBasisFactorization{T<:Real} end

_basis_factorization(B, ::Val{:forrest_tomlin}) = ForrestTomlinFactorization(B)
_basis_factorization(B, ::Val{:bartels_golub}) = BartelsGolubFactorization(B)
_basis_factorization(B, ::Val{:suhl_suhl}) = SuhlSuhlFactorization(B)
_basis_factorization(B, ::Val{:forrest_tomlin}, refactorization::Val) =
    ForrestTomlinFactorization(B, refactorization)
_basis_factorization(B, ::Val{:bartels_golub}, refactorization::Val) =
    BartelsGolubFactorization(B, refactorization)
_basis_factorization(B, ::Val{:suhl_suhl}, refactorization::Val) =
    SuhlSuhlFactorization(B, refactorization)

include("triangular_indices.jl")

struct PackedUpperColumn{T<:Real,I<:AbstractVector{Int}}
    indices::I
    values::Vector{T}
end

PackedUpperColumn{T}(indices::I, values::Vector{T}) where {T<:Real,I<:AbstractVector{Int}} =
    PackedUpperColumn{T,I}(indices, values)

# Plain columns retain their original storage. All stable columns in one BG
# factor share an owned map; copied factors rebase into an independent map.
_upper_order(::Vector{PackedUpperColumn{T,Vector{Int}}}) where {T} = nothing
_upper_order(upper::Vector{PackedUpperColumn{T,UpperRowIndices}}) where {T} =
    isempty(upper) ? nothing : upper[1].indices.order

function _identity_upper(::Type{T}, n::Int, ::Val{:stable}) where {T<:Real}
    order = UpperRowOrder(n)
    return [PackedUpperColumn{T}(UpperRowIndices(Int[index], order), T[one(T)])
            for index in 1:n]
end

function _copy_upper(upper::Vector{PackedUpperColumn{T,Vector{Int}}}) where {T}
    return [PackedUpperColumn(copy(c.indices), copy(c.values)) for c in upper]
end

function _copy_upper(upper::Vector{PackedUpperColumn{T,UpperRowIndices}}) where {T}
    order = UpperRowOrder(length(upper))
    return [PackedUpperColumn{T}(UpperRowIndices(copy(c.indices), order), copy(c.values))
            for c in upper]
end

function _identity_upper(::Type{T}, n::Int) where {T<:Real}
    return [PackedUpperColumn{T}(Int[index], T[one(T)]) for index in 1:n]
end

function _reset_identity_upper!(upper::Vector{PackedUpperColumn{T,Vector{Int}}}, n::Int) where {T}
    old_length = length(upper)
    resize!(upper, n)
    for index in 1:n
        if index <= old_length
            # Columns own their arrays, including in copied factorizations.
            # Retain their capacity for subsequent updates after the reset.
            column = upper[index]
            resize!(column.indices, 1)
            resize!(column.values, 1)
            column.indices[1] = index
            column.values[1] = one(T)
        else
            upper[index] = PackedUpperColumn{T}(Int[index], T[one(T)])
        end
    end
    return upper
end

function _reset_identity_upper!(upper::Vector{PackedUpperColumn{T,UpperRowIndices}}, n::Int) where {T}
    old_length = length(upper)
    order = old_length > 0 ? upper[1].indices.order : nothing
    if isnothing(order)
        order = UpperRowOrder(n)
    else
        resize!(order.order, n)
        resize!(order.positions, n)
        for row in 1:n
            order.order[row] = order.positions[row] = row
        end
    end
    resize!(upper, n)
    for index in 1:n
        if index <= old_length
            # Columns own their arrays, including in copied factorizations.
            # Retain their capacity for subsequent updates after the reset.
            column = upper[index]
            if column.indices.order !== order
                column = PackedUpperColumn{T}(UpperRowIndices(column.indices.ids, order), column.values)
                upper[index] = column
            end
            resize!(column.indices, 1)
            resize!(column.values, 1)
            column.indices[1] = index
            column.values[1] = one(T)
        else
            upper[index] = PackedUpperColumn{T}(UpperRowIndices(Int[index], order), T[one(T)])
        end
    end
    return upper
end

function _packed_column(values::Vector{T}) where {T<:Real}
    entry_count = count(!iszero, values)
    # Row rotation removes an early entry and appends it at the end. Leave
    # one spare slot so advancing a vector's start does not force growth.
    capacity = entry_count + !iszero(entry_count)
    indices = Vector{Int}(undef, capacity)
    entries = Vector{T}(undef, capacity)
    resize!(indices, entry_count)
    resize!(entries, entry_count)
    next_entry = 1
    for row in eachindex(values)
        iszero(values[row]) && continue
        indices[next_entry] = row
        entries[next_entry] = values[row]
        next_entry += 1
    end
    return PackedUpperColumn{T}(indices, entries)
end

# `values` must be separate from the packed arrays (the factor's spike scratch).
function _packed_column!(column::PackedUpperColumn{T}, values::Vector{T}) where {T}
    entry_count = count(!iszero, values)
    # Keep the same spare slot as the allocating packer for subsequent row rotation.
    capacity = entry_count + !iszero(entry_count)
    resize!(column.indices, capacity)
    resize!(column.values, capacity)
    resize!(column.indices, entry_count)
    resize!(column.values, entry_count)
    next_entry = 1
    for row in eachindex(values)
        iszero(values[row]) && continue
        column.indices[next_entry] = row
        column.values[next_entry] = values[row]
        next_entry += 1
    end
    return column
end

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

function _set_upper_value!(column::PackedUpperColumn{T}, row::Int, value::T) where {T}
    position = searchsortedfirst(column.indices, row)
    return _set_upper_value_at!(column, row, value, position)
end

function _set_upper_value_at!(column::PackedUpperColumn{T}, row::Int, value::T,
                              position::Int) where {T}
    if position <= length(column.indices) && column.indices[position] == row
        if iszero(value)
            deleteat!(column.indices, position)
            deleteat!(column.values, position)
        else
            column.values[position] = value
        end
    elseif !iszero(value)
        insert!(column.indices, position, row)
        insert!(column.values, position, value)
    end
    return nothing
end

function _rebuild_row_columns!(columns_by_row::Vector{Vector{Int}},
                               upper::Vector{<:PackedUpperColumn{T}}) where {T}
    for columns in columns_by_row
        empty!(columns)
    end
    for column_index in eachindex(upper)
        for row in upper[column_index].indices
            push!(columns_by_row[row], column_index)
        end
    end
    return columns_by_row
end

function _set_upper_value!(upper::Vector{<:PackedUpperColumn{T}},
                           columns_by_row::Vector{Vector{Int}},
                           column_index::Int, row::Int, value::T) where {T}
    column = upper[column_index]
    position = searchsortedfirst(column.indices, row)
    return _set_upper_value_at!(upper, columns_by_row, column_index, row, value, position)
end

function _set_upper_value_at!(upper::Vector{<:PackedUpperColumn{T}},
                              columns_by_row::Vector{Vector{Int}},
                              column_index::Int, row::Int, value::T, position::Int,
                              column_id::Int=column_index) where {T}
    column = upper[column_index]
    was_stored = position <= length(column.indices) && column.indices[position] == row
    is_stored = !iszero(value)
    was_stored == is_stored && return _set_upper_value_at!(column, row, value, position)
    _set_upper_value_at!(column, row, value, position)
    row_columns = columns_by_row[row]
    row_position = searchsortedfirst(row_columns, column_id)
    if is_stored
        _insert_bartels_golub_incidence!(row_columns, row_position, column_id)
    else
        _delete_bartels_golub_incidence!(row_columns, row_position)
    end
    return nothing
end

function _swap_upper_rows!(upper::Vector{<:PackedUpperColumn{T}},
                           columns_by_row::Vector{Vector{Int}},
                           affected::Vector{Int}, row::Int,
                           positions=eachindex(upper)) where {T}
    top_columns = columns_by_row[row]
    bottom_columns = columns_by_row[row + 1]
    empty!(affected)
    top_index = 1
    bottom_index = 1
    while top_index <= length(top_columns) || bottom_index <= length(bottom_columns)
        if bottom_index > length(bottom_columns) ||
           (top_index <= length(top_columns) &&
            top_columns[top_index] < bottom_columns[bottom_index])
            push!(affected, top_columns[top_index])
            top_index += 1
        elseif top_index > length(top_columns) ||
               bottom_columns[bottom_index] < top_columns[top_index]
            push!(affected, bottom_columns[bottom_index])
            bottom_index += 1
        else
            push!(affected, top_columns[top_index])
            top_index += 1
            bottom_index += 1
        end
    end

    order = _upper_order(upper)
    if !isnothing(order)
        for column_index in affected
            column = upper[positions[column_index]]
            slot = searchsortedfirst(column.indices, row)
            if slot < length(column.indices) && column.indices[slot] == row &&
               column.indices[slot + 1] == row + 1
                ids, values = column.indices.ids, column.values
                ids[slot], ids[slot + 1] = ids[slot + 1], ids[slot]
                values[slot], values[slot + 1] = values[slot + 1], values[slot]
            end
        end
        _rotate_upper_order!(order, row, row + 1)
    else
        for column_index in affected
            column = upper[positions[column_index]]
            position = searchsortedfirst(column.indices, row)
            if position <= length(column.indices) && column.indices[position] == row
                if position < length(column.indices) && column.indices[position + 1] == row + 1
                    column.values[position], column.values[position + 1] =
                        column.values[position + 1], column.values[position]
                else
                    column.indices[position] = row + 1
                end
            else
                column.indices[position] = row
            end
        end
    end
    columns_by_row[row], columns_by_row[row + 1] = bottom_columns, top_columns
    return nothing
end

struct ForrestTomlinUpdate{T<:Real}
    pivot::Int
    indices::Vector{Int}
    multipliers::Vector{T}
end

struct SuhlSuhlUpdate{T<:Real}
    pivot::Int
    last::Int
    indices::Vector{Int}
    multipliers::Vector{T}
end

struct BartelsGolubStep{T<:Real}
    row::Int
    last::Int
    swapped::Bool
    multiplier::T
end

struct BartelsGolubUpdate{T<:Real}
    steps::Vector{BartelsGolubStep{T}}
end

_update_storage_count(update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate}) = length(update.multipliers)
_update_storage_count(update::BartelsGolubUpdate) = length(update.steps)
_factor_storage_count(factor::AbstractTriangularBasisFactorization) =
    _backend_storage_count(factor.base)+sum(c -> length(c.values),factor.upper;init=0)+
    sum(_update_storage_count,factor.updates;init=0)+_sparse_coefficient_count(factor.sparse)
_factor_growth_measure(factor::AbstractTriangularBasisFactorization{T}) where T =
    maximum(c -> maximum(abs,c.values;init=zero(T)),factor.upper;init=zero(T))
_factor_growth_reference(factor::AbstractTriangularBasisFactorization) = _factor_growth_measure(factor)

# A forward solve can supply the entering spike before solving with U. Keep
# two results because steepest-edge pricing performs another FTRAN before the
# basis replacement. Entries are private, and identify the exact output buffer.
mutable struct PreparedTriangularSpike{T<:Real}
    destination::Union{Nothing,Vector{T}}
    direction::Vector{T}
    spike::Vector{T}
end
mutable struct TriangularSpikeCache{T<:Real}
    entries::NTuple{2,PreparedTriangularSpike{T}}
    next::Int
end

# Dense-solve cache only: the original history remains authoritative for sparse
# solves. Each operation is (physical target, physical source, multiplier).
# The upper-column cache is independently invalidated before upper mutation.
mutable struct TriangularRowCache{T<:Real}
    order::Vector{Int}
    operations::Vector{Tuple{Int,Int,T}}
    update_count::Int
    permuted::Bool
    active_upper::Vector{Int}
    upper_dirty::Bool
    prepared::Union{Nothing,TriangularSpikeCache{T}}
end
TriangularRowCache(::Type{T}, n::Int) where {T<:Real} =
    TriangularRowCache{T}(collect(1:n), Tuple{Int,Int,T}[], 0, false, Int[], true, nothing)

mutable struct ForrestTomlinFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T,Vector{Int}}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{ForrestTomlinUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
    row_columns::Vector{Vector{Int}}
    # Private retired history; copied active prefixes must never be recycled.
    recycled_updates::Vector{ForrestTomlinUpdate{T}}
    shared_update_count::Int
    sparse::Union{Nothing,SparseBasisWorkspace{T}}
    row_cache::TriangularRowCache{T}
end

mutable struct SuhlSuhlFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T,Vector{Int}}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{SuhlSuhlUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
    row_columns::Vector{Vector{Int}}
    # Private retired history; copied active prefixes must never be recycled.
    recycled_updates::Vector{SuhlSuhlUpdate{T}}
    shared_update_count::Int
    sparse::Union{Nothing,SparseBasisWorkspace{T}}
    row_cache::TriangularRowCache{T}
end

mutable struct BartelsGolubFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T,UpperRowIndices}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{BartelsGolubUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
    row_columns::Vector{Vector{Int}}
    affected::Vector{Int}
    # Private retired history; copied active prefixes must never be recycled.
    recycled_updates::Vector{BartelsGolubUpdate{T}}
    shared_update_count::Int
    sparse::Union{Nothing,SparseBasisWorkspace{T}}
    row_cache::TriangularRowCache{T}
    row_columns_ready::Bool
end

ForrestTomlinFactorization(B::AbstractMatrix{T}) where {T<:Real} =
    ForrestTomlinFactorization(B, Val(:native))

function ForrestTomlinFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B, Val(R))
    n = _backend_dimension(base)
    return ForrestTomlinFactorization{T,typeof(base)}(
        base, _identity_upper(T, n), collect(1:n), collect(1:n),
        ForrestTomlinUpdate{T}[], zeros(T, n), zeros(T, n), Vector{Int}[],
        ForrestTomlinUpdate{T}[], 0, nothing, TriangularRowCache(T, n),
    )
end

SuhlSuhlFactorization(B::AbstractMatrix{T}) where {T<:Real} =
    SuhlSuhlFactorization(B, Val(:native))

function SuhlSuhlFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B, Val(R))
    n = _backend_dimension(base)
    return SuhlSuhlFactorization{T,typeof(base)}(
        base, _identity_upper(T, n), collect(1:n), collect(1:n),
        SuhlSuhlUpdate{T}[], zeros(T, n), zeros(T, n), Vector{Int}[],
        SuhlSuhlUpdate{T}[], 0, nothing, TriangularRowCache(T, n),
    )
end

BartelsGolubFactorization(B::AbstractMatrix{T}) where {T<:Real} =
    BartelsGolubFactorization(B, Val(:native))

function BartelsGolubFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B, Val(R))
    n = _backend_dimension(base)
    return BartelsGolubFactorization{T,typeof(base)}(
        base, _identity_upper(T, n, Val(:stable)), collect(1:n), collect(1:n),
        BartelsGolubUpdate{T}[], zeros(T, n), zeros(T, n),
        [Int[] for _ in 1:n], Int[],
        BartelsGolubUpdate{T}[], 0, nothing, TriangularRowCache(T, n), false,
    )
end

function _check_triangular_dimensions(factor::AbstractTriangularBasisFactorization,
                                       destination::AbstractVector, rhs::AbstractVector)
    n = _backend_dimension(factor.base)
    length(rhs) == n || throw(DimensionMismatch("right-hand side length must match the basis dimension"))
    length(destination) == n || throw(DimensionMismatch("destination length must match the basis dimension"))
    return n
end

function _apply_row_update!(vector::Vector, update::ForrestTomlinUpdate)
    pivot = update.pivot
    last = length(vector)
    old = vector[pivot]
    for row in pivot:(last - 1)
        vector[row] = vector[row + 1]
    end
    vector[last] = old
    for i in eachindex(update.indices)
        vector[last] += update.multipliers[i] * vector[update.indices[i]]
    end
    return vector
end

function _apply_transposed_row_update!(vector::Vector, update::ForrestTomlinUpdate)
    pivot = update.pivot
    last = length(vector)
    bottom = vector[last]
    for i in eachindex(update.indices)
        vector[update.indices[i]] += update.multipliers[i] * bottom
    end
    for row in last:-1:(pivot + 1)
        vector[row] = vector[row - 1]
    end
    vector[pivot] = bottom
    return vector
end

function _apply_row_update!(vector::Vector, update::SuhlSuhlUpdate)
    pivot = update.pivot
    last = update.last
    old = vector[pivot]
    for row in pivot:(last - 1)
        vector[row] = vector[row + 1]
    end
    vector[last] = old
    for i in eachindex(update.indices)
        vector[last] += update.multipliers[i] * vector[update.indices[i]]
    end
    return vector
end

function _apply_transposed_row_update!(vector::Vector, update::SuhlSuhlUpdate)
    pivot = update.pivot
    last = update.last
    bottom = vector[last]
    for i in eachindex(update.indices)
        vector[update.indices[i]] += update.multipliers[i] * bottom
    end
    for row in last:-1:(pivot + 1)
        vector[row] = vector[row - 1]
    end
    vector[pivot] = bottom
    return vector
end

function _apply_row_update!(vector::Vector, update::BartelsGolubUpdate)
    for step in update.steps
        row = step.row
        if step.last > row
            # Adjacent pure swaps form one rotation.
            old = vector[row]
            for index in row:step.last
                vector[index] = vector[index + 1]
            end
            vector[step.last + 1] = old
        elseif step.swapped
            vector[row], vector[row + 1] = vector[row + 1], vector[row]
        end
        iszero(step.multiplier) ||
            (vector[row + 1] -= step.multiplier * vector[row])
    end
    return vector
end

function _apply_transposed_row_update!(vector::Vector, update::BartelsGolubUpdate)
    for step in Iterators.reverse(update.steps)
        row = step.row
        iszero(step.multiplier) ||
            (vector[row] -= step.multiplier * vector[row + 1])
        if step.last > row
            old = vector[step.last + 1]
            for index in (step.last + 1):-1:(row + 1)
                vector[index] = vector[index - 1]
            end
            vector[row] = old
        elseif step.swapped
            vector[row], vector[row + 1] = vector[row + 1], vector[row]
        end
    end
    return vector
end

function _upper_backsolve!(vector::Vector{T}, upper::Vector{<:PackedUpperColumn{T}},
                           columns=eachindex(upper)) where {T}
    for column_index in Iterators.reverse(columns)
        column = upper[column_index]
        value = vector[column_index] / _upper_value(column, column_index)
        vector[column_index] = value
        # Packed rows and paired values are owned by the factor; callers
        # validate vector dimensions before entering this coefficient loop.
        @inbounds for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            vector[row] -= column.values[index] * value
        end
    end
    return vector
end

function _upper_transpose_solve!(vector::Vector{T}, upper::Vector{<:PackedUpperColumn{T}},
                                 columns=eachindex(upper)) where {T}
    for column_index in columns
        column = upper[column_index]
        value = vector[column_index]
        # Packed rows and paired values are owned by the factor; callers
        # validate vector dimensions before entering this coefficient loop.
        @inbounds for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            value -= column.values[index] * vector[row]
        end
        vector[column_index] = value / _upper_value(column, column_index)
    end
    return vector
end

function _apply_dense_row_updates!(vector, factor::AbstractTriangularBasisFactorization)
    for update in factor.updates
        _apply_row_update!(vector, update)
    end
    return vector
end

function _apply_dense_transposed_row_updates!(vector, factor::AbstractTriangularBasisFactorization)
    for update in Iterators.reverse(factor.updates)
        _apply_transposed_row_update!(vector, update)
    end
    return vector
end

_reset_dense_row_cache!(::AbstractTriangularBasisFactorization, ::Int) = nothing
_dense_upper_columns(factor::AbstractTriangularBasisFactorization) = eachindex(factor.upper)
_invalidate_dense_upper!(factor) = nothing

# Public FTRAN retains prepared-update reuse. Internal auxiliary solves can skip
# its copies without changing the arithmetic or weakening output provenance.
forward_solve!(destination::Vector{T}, factor::AbstractTriangularBasisFactorization{T},
               rhs::AbstractVector) where {T} =
    _triangular_forward_solve!(destination, factor, rhs, true)

_ordinary_forward_solve!(destination, factor, rhs) = forward_solve!(destination, factor, rhs)
_ordinary_forward_solve!(destination::Vector{T}, factor::AbstractTriangularBasisFactorization{T},
                         rhs::AbstractVector) where {T} =
    _triangular_forward_solve!(destination, factor, rhs, false)

function _triangular_forward_solve!(destination::Vector{T},
                        factor::AbstractTriangularBasisFactorization{T},
                        rhs::StridedVector{T}, prepare_update::Bool) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    n = _check_triangular_dimensions(factor, destination, rhs)
    source = destination === rhs ? copyto!(factor.work, rhs) : rhs
    _invalidate_prepared_destination!(factor, destination)
    # Preserve the original two-slot eviction schedule even when auxiliary
    # solves omit payload copies: longer retention changes update rounding.
    entry = _begin_prepared_spike!(factor, destination)
    prepared = prepare_update ? entry : nothing
    _backend_forward_solve!(destination, factor.base, source)
    _apply_dense_row_updates!(destination, factor)
    _save_prepared_spike!(prepared, destination)
    order = _upper_order(factor.upper)
    if isnothing(order)
        _upper_backsolve!(destination, factor.upper, _dense_upper_columns(factor))
        for column in 1:n
            factor.work[factor.column_order[column]] = destination[column]
        end
        copyto!(destination, factor.work)
    else
        _stable_upper_backsolve!(factor.work, destination, factor.upper,
                                 _dense_upper_columns(factor), order)
        for column in 1:n
            destination[factor.column_order[column]] = factor.work[order.order[column]]
        end
    end
    _finish_prepared_spike!(prepared, destination)
    return destination
end

function _triangular_forward_solve!(destination::Vector{T},
                        factor::AbstractTriangularBasisFactorization{T},
                        rhs::AbstractVector, prepare_update::Bool) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    _check_triangular_dimensions(factor, destination, rhs)
    copyto!(factor.work, rhs)
    return _triangular_forward_solve!(destination, factor, factor.work, prepare_update)
end

function forward_solve(factor::AbstractTriangularBasisFactorization{T}, rhs::AbstractVector) where {T}
    return forward_solve!(Vector{T}(undef, length(rhs)), factor, rhs)
end

function transpose_solve!(destination::Vector{T},
                          factor::AbstractTriangularBasisFactorization{T},
                          rhs::AbstractVector) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    n = _check_triangular_dimensions(factor, destination, rhs)
    _invalidate_prepared_destination!(factor, destination)
    source = rhs === factor.work ? copyto!(factor.spike, rhs) : rhs
    order = _upper_order(factor.upper)
    if isnothing(order)
        for column in 1:n
            factor.work[column] = convert(T, source[factor.column_order[column]])
        end
        _upper_transpose_solve!(factor.work, factor.upper, _dense_upper_columns(factor))
    else
        for column in 1:n
            factor.work[order.order[column]] = convert(T, source[factor.column_order[column]])
        end
        _stable_upper_transpose_solve!(factor.work, factor.upper,
                                      _dense_upper_columns(factor), order)
        for row in 1:n
            destination[row] = factor.work[order.order[row]]
        end
        copyto!(factor.work, destination)
    end
    _apply_dense_transposed_row_updates!(factor.work, factor)
    return _backend_transpose_solve!(destination, factor.base, factor.work)
end

function transpose_solve(factor::AbstractTriangularBasisFactorization{T}, rhs::AbstractVector) where {T}
    return transpose_solve!(Vector{T}(undef, length(rhs)), factor, rhs)
end

function _prepare_spike!(factor::AbstractTriangularBasisFactorization{T},
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
    _copy_prepared_spike!(factor, tableau_column) && return position
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

function _rotate_columns!(factor::AbstractTriangularBasisFactorization,
                          position::Int, last::Int=length(factor.column_order))
    # The leaving column owns its buffers; the completed spike is separate scratch.
    replacement = _packed_column!(factor.upper[position], factor.spike)
    for column in position:(last - 1)
        factor.upper[column] = factor.upper[column + 1]
    end
    factor.upper[last] = replacement
    removed = factor.column_order[position]
    for column in position:(last - 1)
        index = factor.column_order[column + 1]
        factor.column_order[column] = index
        factor.positions[index] = column
    end
    factor.column_order[last] = removed
    factor.positions[removed] = last
    return nothing
end

function _take_triangular_update_buffers!(
    factor::Union{ForrestTomlinFactorization{T},SuhlSuhlFactorization{T}},
) where {T}
    isempty(factor.recycled_updates) && return Int[], T[]
    update = pop!(factor.recycled_updates)
    return update.indices, update.multipliers
end

function _take_bartels_golub_steps!(factor::BartelsGolubFactorization{T}) where {T}
    isempty(factor.recycled_updates) && return BartelsGolubStep{T}[]
    return pop!(factor.recycled_updates).steps
end

function _clear_triangular_update!(update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate})
    empty!(update.indices)
    empty!(update.multipliers)
    return nothing
end

function _clear_triangular_update!(update::BartelsGolubUpdate)
    empty!(update.steps)
    return nothing
end

function _recycle_triangular_updates!(factor::AbstractTriangularBasisFactorization)
    # Shared arrays stay untouched even if the copies have become unreachable.
    for index in (factor.shared_update_count + 1):length(factor.updates)
        update = factor.updates[index]
        _clear_triangular_update!(update)
        push!(factor.recycled_updates, update)
    end
    empty!(factor.updates)
    factor.shared_update_count = 0
    return nothing
end

# Only the moved row changes during FT/SS elimination. Keep it in dense scratch
# instead of repeatedly searching, inserting and deleting its packed entries.
# Row rotation has populated factor.spike and removed the eliminated entries.
# The pivot rows remain unchanged, so their incidence can be indexed once.
function _eliminate_triangular_row_spike!(
    factor::Union{ForrestTomlinFactorization{T},SuhlSuhlFactorization{T}},
    position::Int, last::Int, stored_entries::Int,
) where {T}
    n = length(factor.upper)
    position == last && return _take_triangular_update_buffers!(factor)
    spike, touched = factor.spike, factor.work
    empty_value, marker = zero(T), one(T)
    for column_index in last:n
        touched[column_index] = empty_value
    end
    use_row_index = last - position >= 16 && stored_entries ÷ n <= (last - position) ÷ 4
    row_index_ready = false
    indices, multipliers = _take_triangular_update_buffers!(factor)
    for column_index in position:(last - 1)
        column = factor.upper[column_index]
        multiplier = -(spike[column_index] / _upper_value(column, column_index))
        iszero(multiplier) && continue
        push!(indices, column_index)
        push!(multipliers, multiplier)
        if use_row_index && !row_index_ready
            _triangular_row_columns!(factor, column_index, last - 1)
            row_index_ready = true
        end
        trailing_columns = use_row_index ? factor.row_columns[column_index] : (column_index + 1):n
        for trailing in trailing_columns
            value = _upper_value(factor.upper[trailing], column_index)
            iszero(value) && continue
            updated = spike[trailing] + multiplier * value
            # Packed updates remove exact zeros; subsequent lookups return +0.
            spike[trailing] = iszero(updated) ? empty_value : updated
            trailing >= last && (touched[trailing] = marker)
        end
    end
    for column_index in last:n
        # Preserve untouched stored zeros as well as ordinary coefficients.
        iszero(touched[column_index]) && continue
        _set_upper_value!(factor.upper[column_index], last, spike[column_index])
    end
    return indices, multipliers
end

function replace_column!(factor::SuhlSuhlFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _invalidate_sparse_upper!(factor)
    n = length(factor.upper)
    last = n
    while iszero(factor.spike[last])
        last -= 1
    end
    _rotate_columns!(factor, position, last)

    # The replacement is already triangular: there is no row rotation and no
    # elimination. Avoid visiting every other column just to restore its entry.
    if position == last
        indices, multipliers = _take_triangular_update_buffers!(factor)
        push!(factor.updates, SuhlSuhlUpdate{T}(position, last, indices, multipliers))
        return factor
    end

    # Move the leaving row only as far as the spike reaches. Columns beyond
    # that point stay in place, but their entry in the moved row may change.
    stored_entries = 0
    for (column_index, column) in enumerate(factor.upper)
        # The unchanged prefix is triangular and cannot contain the moved row.
        if column_index < position
            stored_entries += length(column.indices)
            continue
        end
        slot, old = _upper_entry(column, position)
        iszero(old) || _set_upper_value_at!(column, position, zero(T), slot)
        start = searchsortedfirst(column.indices, position + 1)
        for index in start:length(column.indices)
            column.indices[index] > last && break
            column.indices[index] -= 1
        end
        factor.spike[column_index] = iszero(old) ? zero(T) : old
        column_index >= last && !iszero(old) && _set_upper_value!(column, last, old)
        stored_entries += length(column.indices)
    end

    indices, multipliers = _eliminate_triangular_row_spike!(factor, position, last, stored_entries)
    push!(factor.updates, SuhlSuhlUpdate{T}(position, last, indices, multipliers))
    return factor
end

function replace_column!(factor::ForrestTomlinFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _invalidate_sparse_upper!(factor)
    _rotate_columns!(factor, position)
    n = length(factor.upper)
    # Rotate the leaving row to the bottom. This leaves one row spike.
    stored_entries = 0
    first_spike = n
    for (column_index, column) in enumerate(factor.upper)
        # The unchanged prefix is triangular and cannot contain the moved row.
        if column_index < position
            stored_entries += length(column.indices)
            continue
        end
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
        # A pure row permutation needs no dense scratch writes. Start storing
        # at the first nonzero that actually needs elimination; all earlier
        # multipliers are zero and the helper never reads that prefix.
        if first_spike == n
            if !iszero(old)
                first_spike = column_index
            elseif column_index < n
                diagonal = _upper_value(column, column_index)
                # Keep the previous zero/zero and zero/NaN behavior for an
                # invalid upper factor rather than hiding a numerical failure.
                if iszero(diagonal) || !isfinite(diagonal)
                    first_spike = column_index
                end
            end
        end
        if column_index >= first_spike
            factor.spike[column_index] = old
        end
        if has_pivot && column_index >= n
            push!(column.indices, n)
            push!(column.values, old)
        end
        stored_entries += length(column.indices)
    end
    indices, multipliers = _eliminate_triangular_row_spike!(factor, first_spike, n, stored_entries)
    push!(factor.updates, ForrestTomlinUpdate{T}(position, indices, multipliers))
    return factor
end

function replace_column!(factor::BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
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
function _triangular_row_columns!(factor::Union{ForrestTomlinFactorization,SuhlSuhlFactorization},
                                  first_row::Int, last_row::Int)
    rows = factor.row_columns
    while length(rows) < length(factor.upper)
        push!(rows, Int[])
    end
    foreach(empty!, rows)
    for column_index in (first_row + 1):length(factor.upper)
        column = factor.upper[column_index]
        start = searchsortedfirst(column.indices, first_row)
        for index in start:length(column.indices)
            row = column.indices[index]
            row > last_row && break
            row < column_index && push!(rows[row], column_index)
        end
    end
    return rows
end

function _reset_row_scratch!(factor::Union{ForrestTomlinFactorization,SuhlSuhlFactorization}, ::Int)
    foreach(empty!, factor.row_columns)
    return nothing
end

function _reset_row_scratch!(factor::BartelsGolubFactorization, n::Int)
    old_length = length(factor.row_columns)
    resize!(factor.row_columns, n)
    for row in 1:n
        if row <= old_length
            empty!(factor.row_columns[row])
        else
            factor.row_columns[row] = Int[]
        end
    end
    empty!(factor.affected)
    factor.row_columns_ready = false
    return nothing
end

function refactorize!(factor::AbstractTriangularBasisFactorization{T},
                      B::AbstractMatrix{T}) where {T}
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    n = _backend_dimension(new_base)
    _reset_identity_upper!(factor.upper, n)
    resize!(factor.column_order, n)
    resize!(factor.positions, n)
    for index in 1:n
        factor.column_order[index] = index
        factor.positions[index] = index
    end
    resize!(factor.work, n)
    resize!(factor.spike, n)
    _reset_row_scratch!(factor, n)
    _recycle_triangular_updates!(factor)
    _reset_dense_row_cache!(factor, n)
    factor.sparse = nothing
    return factor
end

function copy_basis_factorization(factor::ForrestTomlinFactorization{T,F}) where {T,F}
    factor.shared_update_count = length(factor.updates)
    return ForrestTomlinFactorization{T,F}(
        _copy_backend(factor.base), _copy_upper(factor.upper),
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike), Vector{Int}[],
        ForrestTomlinUpdate{T}[], factor.shared_update_count, _copy_sparse_basis_cache(factor.sparse),
        TriangularRowCache(T, length(factor.work)),
    )
end

function copy_basis_factorization(factor::SuhlSuhlFactorization{T,F}) where {T,F}
    factor.shared_update_count = length(factor.updates)
    return SuhlSuhlFactorization{T,F}(
        _copy_backend(factor.base), _copy_upper(factor.upper),
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike), Vector{Int}[],
        SuhlSuhlUpdate{T}[], factor.shared_update_count, _copy_sparse_basis_cache(factor.sparse),
        TriangularRowCache(T, length(factor.work)),
    )
end

function copy_basis_factorization(factor::BartelsGolubFactorization{T,F}) where {T,F}
    factor.shared_update_count = length(factor.updates)
    return BartelsGolubFactorization{T,F}(
        _copy_backend(factor.base), _copy_upper(factor.upper),
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike),
        [Int[] for _ in eachindex(factor.row_columns)], Int[],
        BartelsGolubUpdate{T}[], factor.shared_update_count, _copy_sparse_basis_cache(factor.sparse),
        TriangularRowCache(T, length(factor.work)), false,
    )
end
