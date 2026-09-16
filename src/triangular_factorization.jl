# These updates maintain B = B₀ R⁻¹ U Q⁻¹. B₀ uses the same LU backend as PFI;
# U starts as the identity and Q records the order of its columns. Each pivot
# appends compact row operations to R, so solves need no temporary allocation.
abstract type AbstractTriangularBasisFactorization{T<:Real} end

_basis_factorization(B, ::Val{:forrest_tomlin}) = ForrestTomlinFactorization(B)
_basis_factorization(B, ::Val{:bartels_golub}) = BartelsGolubFactorization(B)
_basis_factorization(B, ::Val{:suhl_suhl}) = SuhlSuhlFactorization(B)

struct PackedUpperColumn{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
end

function _identity_upper(::Type{T}, n::Int) where {T<:Real}
    return [PackedUpperColumn{T}(Int[index], T[one(T)]) for index in 1:n]
end

function _packed_column(values::Vector{T}) where {T<:Real}
    indices = Int[]
    entries = T[]
    for row in eachindex(values)
        iszero(values[row]) && continue
        push!(indices, row)
        push!(entries, values[row])
    end
    return PackedUpperColumn{T}(indices, entries)
end

function _upper_value(column::PackedUpperColumn{T}, row::Int) where {T}
    position = searchsortedfirst(column.indices, row)
    return position <= length(column.indices) && column.indices[position] == row ?
           column.values[position] : zero(T)
end

function _set_upper_value!(column::PackedUpperColumn{T}, row::Int, value::T) where {T}
    position = searchsortedfirst(column.indices, row)
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
                               upper::Vector{PackedUpperColumn{T}}) where {T}
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

function _set_upper_value!(upper::Vector{PackedUpperColumn{T}},
                           columns_by_row::Vector{Vector{Int}},
                           column_index::Int, row::Int, value::T) where {T}
    column = upper[column_index]
    position = searchsortedfirst(column.indices, row)
    was_stored = position <= length(column.indices) && column.indices[position] == row
    is_stored = !iszero(value)
    was_stored == is_stored && return _set_upper_value!(column, row, value)
    _set_upper_value!(column, row, value)
    row_columns = columns_by_row[row]
    row_position = searchsortedfirst(row_columns, column_index)
    if is_stored
        insert!(row_columns, row_position, column_index)
    else
        deleteat!(row_columns, row_position)
    end
    return nothing
end

function _swap_upper_rows!(upper::Vector{PackedUpperColumn{T}},
                           columns_by_row::Vector{Vector{Int}},
                           affected::Vector{Int}, row::Int) where {T}
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

    for column_index in affected
        column = upper[column_index]
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

mutable struct ForrestTomlinFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{ForrestTomlinUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
end

mutable struct SuhlSuhlFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{SuhlSuhlUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
end

mutable struct BartelsGolubFactorization{T<:Real,F} <: AbstractTriangularBasisFactorization{T}
    base::F
    upper::Vector{PackedUpperColumn{T}}
    column_order::Vector{Int}
    positions::Vector{Int}
    updates::Vector{BartelsGolubUpdate{T}}
    work::Vector{T}
    spike::Vector{T}
    row_columns::Vector{Vector{Int}}
    affected::Vector{Int}
end

function ForrestTomlinFactorization(B::AbstractMatrix{T}) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B)
    n = _backend_dimension(base)
    return ForrestTomlinFactorization{T,typeof(base)}(
        base, _identity_upper(T, n), collect(1:n), collect(1:n),
        ForrestTomlinUpdate{T}[], zeros(T, n), zeros(T, n),
    )
end

function SuhlSuhlFactorization(B::AbstractMatrix{T}) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B)
    n = _backend_dimension(base)
    return SuhlSuhlFactorization{T,typeof(base)}(
        base, _identity_upper(T, n), collect(1:n), collect(1:n),
        SuhlSuhlUpdate{T}[], zeros(T, n), zeros(T, n),
    )
end

function BartelsGolubFactorization(B::AbstractMatrix{T}) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B)
    n = _backend_dimension(base)
    return BartelsGolubFactorization{T,typeof(base)}(
        base, _identity_upper(T, n), collect(1:n), collect(1:n),
        BartelsGolubUpdate{T}[], zeros(T, n), zeros(T, n),
        [Int[] for _ in 1:n], Int[],
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

function _upper_backsolve!(vector::Vector{T}, upper::Vector{PackedUpperColumn{T}}) where {T}
    for column_index in length(upper):-1:1
        column = upper[column_index]
        value = vector[column_index] / _upper_value(column, column_index)
        vector[column_index] = value
        for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            vector[row] -= column.values[index] * value
        end
    end
    return vector
end

function _upper_transpose_solve!(vector::Vector{T}, upper::Vector{PackedUpperColumn{T}}) where {T}
    for column_index in eachindex(upper)
        column = upper[column_index]
        value = vector[column_index]
        for index in eachindex(column.indices)
            row = column.indices[index]
            row == column_index && continue
            value -= column.values[index] * vector[row]
        end
        vector[column_index] = value / _upper_value(column, column_index)
    end
    return vector
end

function forward_solve!(destination::Vector{T},
                        factor::AbstractTriangularBasisFactorization{T},
                        rhs::StridedVector{T}) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    n = _check_triangular_dimensions(factor, destination, rhs)
    source = destination === rhs ? copyto!(factor.work, rhs) : rhs
    _backend_forward_solve!(destination, factor.base, source)
    for update in factor.updates
        _apply_row_update!(destination, update)
    end
    _upper_backsolve!(destination, factor.upper)
    for column in 1:n
        factor.work[factor.column_order[column]] = destination[column]
    end
    copyto!(destination, factor.work)
    return destination
end

function forward_solve!(destination::Vector{T},
                        factor::AbstractTriangularBasisFactorization{T},
                        rhs::AbstractVector) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    _check_triangular_dimensions(factor, destination, rhs)
    copyto!(factor.work, rhs)
    return forward_solve!(destination, factor, factor.work)
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
    source = rhs === factor.work ? copyto!(factor.spike, rhs) : rhs
    for column in 1:n
        factor.work[column] = convert(T, source[factor.column_order[column]])
    end
    _upper_transpose_solve!(factor.work, factor.upper)
    for update in Iterators.reverse(factor.updates)
        _apply_transposed_row_update!(factor.work, update)
    end
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
    fill!(factor.spike, zero(T))
    for column_index in 1:n
        column = factor.upper[column_index]
        value = convert(T, tableau_column[factor.column_order[column_index]])
        for index in eachindex(column.indices)
            factor.spike[column.indices[index]] += column.values[index] * value
        end
    end
    return position
end

function _rotate_columns!(factor::AbstractTriangularBasisFactorization,
                          position::Int, last::Int=length(factor.column_order))
    for column in position:(last - 1)
        factor.upper[column] = factor.upper[column + 1]
    end
    factor.upper[last] = _packed_column(factor.spike)
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

function replace_column!(factor::SuhlSuhlFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    n = length(factor.upper)
    last = n
    while iszero(factor.spike[last])
        last -= 1
    end
    _rotate_columns!(factor, position, last)

    # Move the leaving row only as far as the spike reaches. Columns beyond
    # that point stay in place, but their entry in the moved row may change.
    for column in factor.upper
        old = _upper_value(column, position)
        iszero(old) || _set_upper_value!(column, position, zero(T))
        start = searchsortedfirst(column.indices, position + 1)
        for index in start:length(column.indices)
            column.indices[index] > last && break
            column.indices[index] -= 1
        end
        iszero(old) || _set_upper_value!(column, last, old)
    end

    indices = Int[]
    multipliers = T[]
    for column_index in position:(last - 1)
        column = factor.upper[column_index]
        multiplier = -(_upper_value(column, last) /
                       _upper_value(column, column_index))
        _set_upper_value!(column, last, zero(T))
        iszero(multiplier) && continue
        push!(indices, column_index)
        push!(multipliers, multiplier)
        for trailing in (column_index + 1):n
            trailing_column = factor.upper[trailing]
            value = _upper_value(trailing_column, column_index)
            iszero(value) && continue
            _set_upper_value!(trailing_column, last,
                              _upper_value(trailing_column, last) + multiplier * value)
        end
    end
    push!(factor.updates, SuhlSuhlUpdate{T}(position, last, indices, multipliers))
    return factor
end

function replace_column!(factor::ForrestTomlinFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _rotate_columns!(factor, position)
    n = length(factor.upper)
    # Rotate the leaving row to the bottom. This leaves one row spike.
    for column in factor.upper
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
        if has_pivot
            push!(column.indices, n)
            push!(column.values, old)
        end
    end
    indices = Int[]
    multipliers = T[]
    for column_index in position:(n - 1)
        column = factor.upper[column_index]
        multiplier = -(_upper_value(column, n) / _upper_value(column, column_index))
        _set_upper_value!(column, n, zero(T))
        iszero(multiplier) && continue
        push!(indices, column_index)
        push!(multipliers, multiplier)
        for trailing in (column_index + 1):n
            trailing_column = factor.upper[trailing]
            value = _upper_value(trailing_column, column_index)
            iszero(value) && continue
            _set_upper_value!(trailing_column, n,
                              _upper_value(trailing_column, n) + multiplier * value)
        end
    end
    push!(factor.updates, ForrestTomlinUpdate{T}(position, indices, multipliers))
    return factor
end

function replace_column!(factor::BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _rotate_columns!(factor, position)
    n = length(factor.upper)
    columns_by_row = _rebuild_row_columns!(factor.row_columns, factor.upper)
    steps = BartelsGolubStep{T}[]
    run_start = 0
    run_last = 0
    for column_index in position:(n - 1)
        column = factor.upper[column_index]
        swapped = _pivot_magnitude(_upper_value(column, column_index + 1)) >
                  _pivot_magnitude(_upper_value(column, column_index))
        if swapped
            _swap_upper_rows!(factor.upper, columns_by_row, factor.affected,
                              column_index)
        end
        pivot = _upper_value(column, column_index)
        iszero(pivot) && throw(LinearAlgebra.ZeroPivotException(column_index))
        multiplier = _upper_value(column, column_index + 1) / pivot
        _set_upper_value!(factor.upper, columns_by_row,
                          column_index, column_index + 1, zero(T))
        if !iszero(multiplier)
            for trailing in columns_by_row[column_index]
                trailing <= column_index && continue
                trailing_column = factor.upper[trailing]
                value = _upper_value(trailing_column, column_index)
                _set_upper_value!(factor.upper, columns_by_row,
                                  trailing, column_index + 1,
                                  _upper_value(trailing_column, column_index + 1) -
                                  multiplier * value)
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

_reset_row_scratch!(::ForrestTomlinFactorization, ::Int) = nothing
_reset_row_scratch!(::SuhlSuhlFactorization, ::Int) = nothing

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
    return nothing
end

function refactorize!(factor::AbstractTriangularBasisFactorization{T},
                      B::AbstractMatrix{T}) where {T}
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    n = _backend_dimension(new_base)
    factor.upper = _identity_upper(T, n)
    resize!(factor.column_order, n)
    resize!(factor.positions, n)
    for index in 1:n
        factor.column_order[index] = index
        factor.positions[index] = index
    end
    resize!(factor.work, n)
    resize!(factor.spike, n)
    _reset_row_scratch!(factor, n)
    empty!(factor.updates)
    return factor
end

function copy_basis_factorization(factor::ForrestTomlinFactorization{T,F}) where {T,F}
    return ForrestTomlinFactorization{T,F}(
        factor.base, [PackedUpperColumn(copy(column.indices), copy(column.values))
                      for column in factor.upper],
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike),
    )
end

function copy_basis_factorization(factor::SuhlSuhlFactorization{T,F}) where {T,F}
    return SuhlSuhlFactorization{T,F}(
        factor.base, [PackedUpperColumn(copy(column.indices), copy(column.values))
                      for column in factor.upper],
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike),
    )
end

function copy_basis_factorization(factor::BartelsGolubFactorization{T,F}) where {T,F}
    return BartelsGolubFactorization{T,F}(
        factor.base, [PackedUpperColumn(copy(column.indices), copy(column.values))
                      for column in factor.upper],
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike),
        [Int[] for _ in eachindex(factor.row_columns)], Int[],
    )
end
