# SOURCE construction direct-factor.jl:116-148
function _init_direct_manager(::Type{BartelsGolubFactorization},base,upper,q)
    n=_backend_dimension(base)
    return BartelsGolubFactorization{Float64,typeof(base)}(base,upper,q,invperm(q),
        BartelsGolubUpdate{Float64}[],zeros(n),zeros(n),[Int[] for _ in 1:n],Int[],
        BartelsGolubUpdate{Float64}[],0,nothing,TriangularRowCache(Float64,n),false)
end

function _direct_lu_factor_with_exporter(Factor,B::AbstractMatrix{Float64},backend::Val{R},
                                         policy::_NativePivotPolicy,exporter;normalize::Bool=true,
                                         factorize=_factorize_basis) where {R}
    Factor in (ForrestTomlinFactorization,SuhlSuhlFactorization,BartelsGolubFactorization) ||
        throw(ArgumentError("Unsupported direct LU manager"))
    R in (:native,:markowitz) || throw(ArgumentError("Unsupported direct LU backend"))
    R === :markowitz && policy !== _NATIVE_PIVOT_DEFAULT &&
        throw(ArgumentError("Markowitz does not support a native pivot policy"))
    ordinary=factorize(B,backend,policy) # Exactly one factorization; test seam is not retained.
    parts=exporter(ordinary)
    F=typeof(ordinary)
    if isnothing(parts)
        n=_backend_dimension(ordinary)
        base=DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,
                                    normalize,policy,ordinary,Float64[])
        upper=Factor===BartelsGolubFactorization ? _identity_upper(Float64,n,Val(:stable)) : _identity_upper(Float64,n)
        return _init_direct_manager(Factor,base,upper,collect(1:n))
    end
    D=normalize ? _direct_normalize_upper!(parts.upper) : nothing
    base=DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,
                                D,normalize,policy,nothing,zeros(length(parts.rows)))
    upper=_direct_packed_upper(parts.upper,Factor)
    # q is owned by the export and transferred; temporary CSC U and ordinary
    # backend/workspace are not retained by the constructed manager.
    return _init_direct_manager(Factor,base,upper,parts.columns)
end

# SOURCE metadata triangular_factorization.jl:343-350
_update_storage_count(update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate}) = length(update.multipliers)
_update_storage_count(update::BartelsGolubUpdate) = length(update.steps)
_factor_storage_count(factor::AbstractTriangularBasisFactorization) =
    _backend_storage_count(factor.base)+sum(c -> length(c.values),factor.upper;init=0)+
    sum(_update_storage_count,factor.updates;init=0)+_sparse_coefficient_count(factor.sparse)
_factor_growth_measure(factor::AbstractTriangularBasisFactorization{T}) where T =
    maximum(c -> maximum(abs,c.values;init=zero(T)),factor.upper;init=zero(T))
_factor_growth_reference(factor::AbstractTriangularBasisFactorization) = _factor_growth_measure(factor)

# SOURCE dimensions triangular_factorization.jl:517-524
function _check_triangular_dimensions(factor::AbstractTriangularBasisFactorization,
                                       destination::AbstractVector, rhs::AbstractVector)
    n = _backend_dimension(factor.base)
    length(rhs) == n || throw(DimensionMismatch("right-hand side length must match the basis dimension"))
    length(destination) == n || throw(DimensionMismatch("destination length must match the basis dimension"))
    return n
end


# SOURCE prepared triangular_spikes.jl:1-123
# Reuse R * B0^-1 * a from an unmodified dense FTRAN. Reconstructing that
# vector as U * Q^-1 * direction would traverse the whole growing upper factor
# and introduce another rounding step. Corrected or external directions retain
# the reconstruction path. Arbitrary-precision and exact types are unchanged.
_begin_prepared_spike!(factor, destination) = nothing
_save_prepared_spike!(::Nothing, destination) = nothing
_finish_prepared_spike!(::Nothing, destination) = nothing
_copy_prepared_spike!(factor, direction) = false
_invalidate_prepared_destination!(factor, destination) = nothing

Base.@noinline function _begin_prepared_spike!(factor::AbstractTriangularBasisFactorization{T},
                                 destination::Vector{T}) where {T<:Union{Float32,Float64}}
    Base.mightalias(destination, factor.spike) && return nothing
    sparse = factor.sparse
    if !isnothing(sparse) && (Base.mightalias(destination, sparse.dense) ||
            Base.mightalias(destination, sparse.dense_result) ||
            Base.mightalias(destination, sparse.work.values) ||
            Base.mightalias(destination, sparse.scratch.values))
        return nothing
    end
    cache = factor.row_cache.prepared
    if isnothing(cache)
        entries = ntuple(_ -> PreparedTriangularSpike{T}(nothing, T[], T[]), 2)
        cache = TriangularSpikeCache{T}(entries, 1)
        factor.row_cache.prepared = cache
    end
    # Invalidate previous output from this same buffer before a solve can
    # overwrite it or fail partway through. Other RHS buffers remain usable.
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination, destination)
            entry.destination = nothing
        end
        # Both slots share the current basis dimension; establish their buffers
        # together so the next ordinary solve can immediately reuse either one.
        resize!(entry.direction, length(destination))
        resize!(entry.spike, length(destination))
    end
    entry = cache.entries[cache.next]
    cache.next = 3 - cache.next
    entry.destination = nothing
    return entry
end

function _save_prepared_spike!(entry::PreparedTriangularSpike, destination)
    copyto!(resize!(entry.spike, length(destination)), destination)
    return nothing
end

Base.@noinline function _finish_prepared_spike!(entry::PreparedTriangularSpike, destination)
    # Do not change the propagation of exceptional input through reconstruction.
    all(isfinite, destination) && all(isfinite, entry.spike) || return nothing
    copyto!(resize!(entry.direction, length(destination)), destination)
    entry.destination = destination
    return nothing
end

# The pending entry is unpublished, so a failed finite check may overwrite its
# private numeric buffer. Publish only after checking both input vectors.
Base.@noinline function _finish_prepared_spike!(entry::PreparedTriangularSpike{T},
                                               destination::Vector{T}) where {T<:Union{Float32,Float64}}
    if !isnothing(entry.destination) || length(entry.spike) != length(destination) ||
            Base.mightalias(entry.direction, destination) ||
            Base.mightalias(entry.direction, entry.spike)
        return invoke(_finish_prepared_spike!, Tuple{PreparedTriangularSpike,Any}, entry, destination)
    end
    direction = resize!(entry.direction, length(destination))
    finite = true
    @inbounds @simd for index in eachindex(destination, entry.spike, direction)
        value = destination[index]
        finite &= isfinite(value) & isfinite(entry.spike[index])
        direction[index] = value
    end
    finite && (entry.destination = destination)
    return nothing
end

Base.@noinline function _copy_prepared_spike!(factor::AbstractTriangularBasisFactorization{T},
                                direction::Vector{T}) where {T<:Union{Float32,Float64}}
    cache = factor.row_cache.prepared
    isnothing(cache) && return false
    for entry in cache.entries
        # Identity prevents another equal-valued RHS buffer from selecting an
        # unrelated solve. Exact value comparison detects in-place corrections,
        # including changes to signed zeros.
        if entry.destination === direction && isequal(entry.direction, direction)
            copyto!(factor.spike, entry.spike)
            return true
        end
    end
    return false
end

function _invalidate_prepared_spikes!(factor::AbstractTriangularBasisFactorization)
    cache = factor.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        entry.destination = nothing
    end
    return nothing
end

# A different solve operation can produce the same rounded values. Invalidate
# provenance before BTRAN or an indexed solve overwrites the output buffer.
function _invalidate_prepared_destination!(factor::AbstractTriangularBasisFactorization,
                                            destination)
    cache = factor.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination, destination)
            entry.destination = nothing
        end
    end
    return nothing
end

_save_prepared_spike!(::Nothing, source, order) = nothing
function _save_prepared_spike!(entry::PreparedTriangularSpike, source, order)
    resize!(entry.spike, length(source))
    for row in eachindex(source)
        entry.spike[row] = source[order.order[row]]
    end
    return nothing
end

# SOURCE rows triangular_rows.jl:14-68

function _append_compiled_rows!(cache, update::BartelsGolubUpdate)
    order = cache.order
    for step in update.steps
        row = step.row
        if step.last > row
            cache.permuted = true
            _rotate_row_order!(order, row, step.last + 1)
        elseif step.swapped
            cache.permuted = true
            order[row], order[row + 1] = order[row + 1], order[row]
        end
        iszero(step.multiplier) || push!(cache.operations,
            (order[row + 1], order[row], step.multiplier))
    end
    return nothing
end

_row_update_last(cache, ::ForrestTomlinUpdate) = length(cache.order)
_row_update_last(cache, update::SuhlSuhlUpdate) = update.last
function _append_compiled_rows!(cache, update::Union{ForrestTomlinUpdate,SuhlSuhlUpdate})
    last = _row_update_last(cache, update)
    order = cache.order
    cache.permuted |= update.pivot < last
    _rotate_row_order!(order, update.pivot, last)
    for index in eachindex(update.indices)
        row = update.indices[index]
        if _row_update_swapped(update, row)
            cache.permuted = true
            order[row], order[last] = order[last], order[row]
        end
        push!(cache.operations,
            (order[last], order[update.indices[index]], update.multipliers[index]))
    end
    return nothing
end

function _sync_triangular_rows!(factor::ComposedRowFactorization)
    cache = factor.row_cache
    for index in (cache.update_count + 1):length(factor.updates)
        _append_compiled_rows!(cache, factor.updates[index])
        cache.update_count = index
    end
    return cache
end

_row_operation(::BartelsGolubFactorization) = Val(:subtract)
_row_operation(::Union{ForrestTomlinFactorization,SuhlSuhlFactorization}) = Val(:add)
@inline _compiled_row_operation!(vector, target, source, multiplier, ::Val{:subtract}) =
    (vector[target] -= multiplier * vector[source])
@inline _compiled_row_operation!(vector, target, source, multiplier, ::Val{:add}) =
    (vector[target] += multiplier * vector[source])

function _apply_dense_row_updates!(vector, factor::ComposedRowFactorization)
    isempty(factor.updates) && return vector

# SOURCE eligibility triangular_rows.jl:120-155
function _invalidate_dense_upper!(factor::ComposedRowFactorization, first_column::Int=1)
    cache = factor.row_cache
    # Rotations and eliminations cannot affect the triangular prefix before the
    # leaving column. Multiple pending mutations retain the earliest boundary.
    cache.upper_dirty_from = cache.upper_dirty ? min(cache.upper_dirty_from, first_column) : first_column
    cache.upper_dirty = true
    cache.upper_prefix_safe = false
    _invalidate_prepared_spikes!(factor)
    return nothing
end

function _dense_upper_columns(factor::Union{ForrestTomlinFactorization{T},
        SuhlSuhlFactorization{T},BartelsGolubFactorization{T}}) where {T<:Union{Float32,Float64}}
    cache = factor.row_cache
    if cache.upper_dirty
        first_column = cache.upper_dirty_from
        resize!(cache.active_upper, searchsortedfirst(cache.active_upper, first_column) - 1)
        for index in first_column:length(factor.upper)
            column = factor.upper[index]
            # Explicit off-diagonal zeros still participate in arithmetic.
            identity = length(column.indices) == 1 && column.indices[1] == index &&
                column.values[1] == one(T)
            identity || push!(cache.active_upper, index)
            # New values were checked at their stores. Validate the diagonal in
            # the existing dirty-column pass, before a solve reads eligibility.
            if !identity && cache.upper_prefix_safe &&
                    (isempty(column.indices) || column.indices[end] != index ||
                     iszero(column.values[end]))
                cache.upper_prefix_safe = false
            end
        end
        cache.upper_dirty = false
        cache.upper_dirty_from = length(factor.upper) + 1
    end
    return cache.active_upper
end

# SOURCE ftran triangular_rows.jl:159-187
function _finish_triangular_forward!(destination, factor::ComposedRowFactorization, prepared, n)
    cache = _sync_triangular_rows!(factor)
    operation = _row_operation(factor)
    for (target, source, multiplier) in cache.operations
        _compiled_row_operation!(destination, target, source, multiplier, operation)
    end
    order = _upper_order(factor.upper)
    if isnothing(order)
        for row in 1:n
            factor.work[row] = destination[cache.order[row]]
        end
        _save_prepared_spike!(prepared, factor.work)
        _upper_backsolve!(factor.work, factor.upper, _dense_upper_columns(factor))
        for column in 1:n
            destination[factor.column_order[column]] = factor.work[column]
        end
    else
        for row in 1:n
            factor.work[order.order[row]] = destination[cache.order[row]]
        end
        _save_prepared_spike!(prepared, factor.work, order)
        _stable_upper_backsolve_physical!(factor.work, factor.upper,
                                         _dense_upper_columns(factor), order)
        for column in 1:n
            destination[factor.column_order[column]] = factor.work[order.order[column]]
        end
    end
    return destination
end

# SOURCE ftran-entry triangular_factorization.jl:756-773
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
    _finish_triangular_forward!(destination, factor, prepared, n)
    _finish_prepared_spike!(prepared, destination)
    return destination
end

# SOURCE upper-ftran triangular_factorization.jl:655-679
function _upper_backsolve!(vector::Vector{T}, upper::Vector{<:PackedUpperColumn{T}},
                           columns=eachindex(upper)) where {T}
    for column_index in Iterators.reverse(columns)
        column = upper[column_index]
        value = vector[column_index] / _upper_diagonal(column, column_index)
        vector[column_index] = value
        # Packed rows and paired values are owned by the factor; callers
        # validate vector dimensions before entering this coefficient loop.
        # Canonical packed columns have unique, ordered rows. With the
        # diagonal last, exclude it once instead of testing every coefficient.
        if !isempty(column.indices) && column.indices[end] == column_index
            @inbounds for index in 1:(length(column.indices) - 1)
                row = column.indices[index]
                vector[row] -= column.values[index] * value
            end
        else
            @inbounds for index in eachindex(column.indices)
                row = column.indices[index]
                row == column_index && continue
                vector[row] -= column.values[index] * value
            end
        end
    end
    return vector
end

# SOURCE upper-btran triangular_factorization.jl:681-705
function _upper_transpose_solve!(vector::Vector{T}, upper::Vector{<:PackedUpperColumn{T}},
                                 columns=eachindex(upper)) where {T}
    for column_index in columns
        column = upper[column_index]
        value = vector[column_index]
        # Packed rows and paired values are owned by the factor; callers
        # validate vector dimensions before entering this coefficient loop.
        # Canonical packed columns have unique, ordered rows. With the
        # diagonal last, exclude it once instead of testing every coefficient.
        if !isempty(column.indices) && column.indices[end] == column_index
            @inbounds for index in 1:(length(column.indices) - 1)
                row = column.indices[index]
                value -= column.values[index] * vector[row]
            end
        else
            @inbounds for index in eachindex(column.indices)
                row = column.indices[index]
                row == column_index && continue
                value -= column.values[index] * vector[row]
            end
        end
        vector[column_index] = value / _upper_diagonal(column, column_index)
    end
    return vector
end

# SOURCE btran-entry triangular_factorization.jl:801-860
function _unit_transpose_rhs(factor::AbstractTriangularBasisFactorization{T},
                             rhs::Vector{T}, row::Int) where {T<:Union{Float32,Float64}}
    checkbounds(rhs, row)
    return _UnitTransposeRHS(rhs, row)
end

function _prepare_transpose_rhs!(factor::AbstractTriangularBasisFactorization{T},
                                 rhs, ::Nothing) where {T}
    for column in eachindex(factor.work)
        factor.work[column] = convert(T, rhs[factor.column_order[column]])
    end
end
function _prepare_transpose_rhs!(factor::AbstractTriangularBasisFactorization{T},
                                 rhs, order) where {T}
    for column in eachindex(factor.work)
        factor.work[order.order[column]] = convert(T, rhs[factor.column_order[column]])
    end
end
function _prepare_transpose_rhs!(factor::AbstractTriangularBasisFactorization{T},
                                 rhs::_UnitTransposeRHS{T}, ::Nothing) where {T<:Real}
    fill!(factor.work, zero(T))
    factor.work[factor.positions[rhs.row]] = one(T)
end
function _prepare_transpose_rhs!(factor::AbstractTriangularBasisFactorization{T},
                                 rhs::_UnitTransposeRHS{T}, order) where {T<:Real}
    fill!(factor.work, zero(T))
    factor.work[order.order[factor.positions[rhs.row]]] = one(T)
end

_transpose_upper_for_rhs!(factor, rhs, columns, ::Nothing) =
    _upper_transpose_solve!(factor.work, factor.upper, columns)
_transpose_upper_for_rhs!(factor, rhs, columns, order) =
    _stable_upper_transpose_solve!(factor.work, factor.upper, columns, order)

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
        _prepare_transpose_rhs!(factor, source, nothing)
        _transpose_upper_for_rhs!(factor, source, _dense_upper_columns(factor), nothing)
        return _finish_triangular_transpose!(destination, factor, nothing)
    else
        _prepare_transpose_rhs!(factor, source, order)
        _transpose_upper_for_rhs!(factor, source, _dense_upper_columns(factor), order)
        # Keep the concrete row-order type across the call boundary; merging
        # it with `nothing` boxes the immutable wrapper on each BG BTRAN.
        return _finish_triangular_transpose!(destination, factor, order)
    end
end

function transpose_solve(factor::AbstractTriangularBasisFactorization{T}, rhs::AbstractVector) where {T}
    return transpose_solve!(Vector{T}(undef, length(rhs)), factor, rhs)
end

# SOURCE btran-history triangular_rows.jl:189-206
function _finish_triangular_transpose!(destination, factor::ComposedRowFactorization, order)
    cache = _sync_triangular_rows!(factor)
    if isnothing(order) && !cache.permuted
        source = factor.work
    else
        for row in eachindex(cache.order)
            factor.spike[cache.order[row]] = factor.work[isnothing(order) ? row : order.order[row]]
        end
        source = factor.spike
    end
    operation = _row_operation(factor)
    for (target, origin, multiplier) in Iterators.reverse(cache.operations)
        _compiled_row_operation!(source, origin, target, multiplier, operation)
    end
    # Public callers may use spike as output; backend input must remain separate.
    destination === source && (source = copyto!(factor.work, source))
    return _backend_transpose_solve!(destination, factor.base, source)
end

# SOURCE btran-prefix triangular_rows.jl:226-241
function _transpose_upper_for_rhs!(factor::BartelsGolubFactorization{T},
        rhs::_UnitTransposeRHS{T}, columns, order::UpperRowOrder) where {T<:Union{Float32,Float64}}
    if factor.row_cache.upper_prefix_safe
        split = searchsortedfirst(columns, factor.positions[rhs.row])
        if split > 1
            for slot in 1:(split - 1)
                j = columns[slot]
                physical = order.order[j]
                factor.work[physical] /= _upper_diagonal(factor.upper[j], j)
            end
            return _stable_upper_transpose_solve!(factor.work, factor.upper,
                                                  @view(columns[split:end]), order)
        end
    end
    return _stable_upper_transpose_solve!(factor.work, factor.upper, columns, order)
end

# SOURCE spike triangular_factorization.jl:862-908
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
    replacement = _packed_column!(factor.upper[position], factor.spike, factor.row_cache)
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


# SOURCE pure-swaps bartels_golub_rows.jl:57-68
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

# SOURCE update triangular_factorization.jl:1112-1187
function replace_column!(factor::BartelsGolubFactorization{T},
                         tableau_column::AbstractVector, pivot_row::Integer;
                         zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                                              _positive_tolerance(T, 1 // 10^12)) where {T}
    position = _prepare_spike!(factor, tableau_column, pivot_row, zero_tolerance)
    _begin_upper_update!(factor, position)
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
                                    trailing, column_index + 1,
                                    _track_upper_value!(factor, old - multiplier * value), slot, column_id)
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
    return _finish_upper_update!(factor)
end

# Only the target row changes during FT/SS elimination. Index the other rows

# SOURCE copy triangular_factorization.jl:1285-1295
function copy_basis_factorization(factor::BartelsGolubFactorization{T,F}) where {T,F}
    factor.shared_update_count = length(factor.updates)
    return BartelsGolubFactorization{T,F}(
        _copy_backend(factor.base), _copy_upper(factor.upper),
        copy(factor.column_order), copy(factor.positions),
        copy(factor.updates), similar(factor.work), similar(factor.spike),
        [Int[] for _ in eachindex(factor.row_columns)], Int[],
        BartelsGolubUpdate{T}[], factor.shared_update_count, _copy_sparse_basis_cache(factor.sparse),
        _copy_triangular_row_cache(factor), false,
    )
end

# SOURCE refactor direct-factor.jl:164-176
_direct_mode(f::DirectLUFactor)=!isnothing(f.base.fallback) ? :fallback :
    isnothing(f.base.diagonal) ? :direct : :normalized
function _direct_refactorize_with_exporter!(f::DirectLUFactor,B::AbstractMatrix{Float64},exporter)
    Factor=getfield(@__MODULE__,nameof(typeof(f)))
    candidate=_direct_lu_factor_with_exporter(Factor,B,Val(_direct_requested_backend(f.base)),
                                            f.base.pivot_policy,exporter;normalize=f.base.normalize_requested)
    typeof(candidate)===typeof(f) || throw(ArgumentError("Direct refactorization type changed"))
    # All potentially throwing construction has finished; concrete fields match.
    for name in fieldnames(typeof(f));setfield!(f,name,getfield(candidate,name));end
    return f
end
refactorize!(f::DirectLUFactor,B::AbstractMatrix{Float64})=
    _direct_refactorize_with_exporter!(f,B,_export_basis_lu)

