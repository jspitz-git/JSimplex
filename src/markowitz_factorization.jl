# Sparse Markowitz elimination followed by a dense trailing Schur complement.
# The column threshold limits the size of multipliers in the sparse L factor.
struct PackedFactorVector{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
end

# A mutable wrapper keeps the optional workspace field from reboxing its arrays
# on each hand-off between output slots. Only private construction uses it.
mutable struct MarkowitzWorkspace{T,D<:AbstractDict{Int,T}}
    rows::Vector{D}
    columns::Vector{D}
    active_rows::BitVector
    active_columns::BitVector
    singleton_rows::Vector{Int}
    singleton_columns::Vector{Int}
    doubleton_columns::BitSet
    affected_rows::Vector{Int}
    row_positions::Vector{Int}
    column_positions::Vector{Int}
    column_maxima::Vector{T}
    column_maxima_valid::BitVector
end

MarkowitzWorkspace(::Type{T},::Type{D}) where {T,D<:AbstractDict{Int,T}} =
    MarkowitzWorkspace{T,D}(D[],D[],BitVector(),BitVector(),Int[],Int[],BitSet(),Int[],Int[],Int[],T[],BitVector())

function _reset_markowitz_workspace!(workspace::MarkowitzWorkspace{T,D}, n::Int) where {T,D}
    # Keep excess dictionary objects when dimensions shrink, but drop old values.
    while length(workspace.rows) < n
        push!(workspace.rows,D())
        push!(workspace.columns,D())
    end
    foreach(empty!,workspace.rows)
    foreach(empty!,workspace.columns)
    fill!(resize!(workspace.active_rows,n),true)
    fill!(resize!(workspace.active_columns,n),true)
    empty!(workspace.singleton_rows)
    empty!(workspace.singleton_columns)
    empty!(workspace.doubleton_columns)
    empty!(workspace.affected_rows)
    resize!(workspace.row_positions,n)
    resize!(workspace.column_positions,n)
    if length(workspace.column_maxima) < n
        resize!(workspace.column_maxima,n)
        resize!(workspace.column_maxima_valid,n)
    end
    fill!(workspace.column_maxima_valid,false)
    return workspace
end

mutable struct MarkowitzBackend{T<:Real,F,D<:AbstractDict{Int,T}}
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
    workspace::Union{Nothing,MarkowitzWorkspace{T,D}}
    spare::Union{Nothing,MarkowitzBackend{T,F,D}}
    shared::Bool
    lower_pool::Vector{PackedFactorVector{T}}
    upper_pool::Vector{PackedFactorVector{T}}
end

_backend_dimension(backend::MarkowitzBackend) = backend.dimension
_backend_storage_count(backend::MarkowitzBackend) =
    sum(v -> length(v.values),backend.lower;init=0)+
    sum(v -> length(v.values),backend.upper;init=0)+
    length(backend.diagonal)+length(backend.core.factors)
_factorize_basis(B::AbstractMatrix, ::Val{:markowitz}) = MarkowitzBackend(B)

function _markowitz_backend(::Type{T}, n::Int, row_order::Vector{Int},
                            column_order::Vector{Int},
                            lower::Vector{PackedFactorVector{T}},
                            upper::Vector{PackedFactorVector{T}},
                            diagonal::Vector{T}, core_matrix::Matrix{T}, workspace,
                            ::Type{D}, candidate, lower_pool, upper_pool) where {T<:Real,D<:AbstractDict{Int,T}}
    # The matrix belongs to an inactive private slot, or is newly allocated.
    core = !isnothing(candidate) && core_matrix === candidate.core.factors ?
        lu!(candidate.core,core_matrix) : lu!(core_matrix)
    if isnothing(candidate)
        return MarkowitzBackend{T,typeof(core),D}(
            n, length(diagonal), row_order, column_order, lower, upper, diagonal,
            core, zeros(T, n), zeros(T, size(core_matrix, 1)), workspace,
            nothing, false, lower_pool, upper_pool,
        )
    end
    candidate.dimension = n
    candidate.sparse_pivots = length(diagonal)
    candidate.core = core
    resize!(candidate.work,n)
    resize!(candidate.core_work,size(core_matrix,1))
    candidate.workspace = workspace
    return candidate
end

function _markowitz_set_entry!(rows::Vector{D},
                               columns::Vector{D},
                               singleton_rows::Vector{Int},
                               singleton_columns::Vector{Int},
                               doubleton_columns::BitSet,
                               row::Int, column::Int, value::T,
                               nonzeros::Int) where {T<:Real,D<:AbstractDict{Int,T}}
    row_data = rows[row]
    column_data = columns[column]
    old_row_count = length(row_data)
    old_column_count = length(column_data)
    if iszero(value)
        if haskey(row_data, column)
            delete!(row_data, column)
            delete!(column_data, row)
            nonzeros -= 1
        end
    else
        row_data[column] = value
        column_data[row] = value
        nonzeros += length(row_data) - old_row_count
    end
    old_row_count != 1 && length(row_data) == 1 && push!(singleton_rows, row)
    new_column_count = length(column_data)
    old_column_count != 1 && new_column_count == 1 &&
        push!(singleton_columns, column)
    if old_column_count != new_column_count
        if new_column_count == 2
            push!(doubleton_columns, column)
        elseif old_column_count == 2
            delete!(doubleton_columns, column)
        end
    end
    return nonzeros
end

_markowitz_magnitude(value::Real) = _pivot_magnitude(value)

function _markowitz_magnitude(value::BigFloat)
    # Positive values are only read by callers. Negation at stored precision is
    # exact, including when ambient precision is lower than the input's.
    signbit(value) || return value
    result = BigFloat(precision=precision(value))
    ccall((:mpfr_neg, Base.MPFR.libmpfr), Cint,
          (Ref{BigFloat}, Ref{BigFloat}, Base.MPFR.MPFRRoundingMode),
          result, value, Base.MPFR.MPFRRoundNearest)
    return result
end

function _markowitz_column_maximum(column::AbstractDict{Int,T}) where {T<:Real}
    maximum_value = zero(T)
    for value in values(column)
        magnitude = _markowitz_magnitude(value)
        magnitude > maximum_value && (maximum_value = magnitude)
    end
    return maximum_value
end

# Cache only the raw maximum: singleton and general candidates use different
# threshold helpers, and BigFloat maxima must retain their stored precision.
_markowitz_cached_maximum(column, ::Nothing, ::Int, ::Bool=true) = _markowitz_column_maximum(column)
@inline function _markowitz_cached_maximum(column, cache::Tuple{Vector{T},BitVector},
                                           index::Int, store::Bool=true) where {T}
    maxima, valid = cache
    valid[index] && return maxima[index]
    maximum = _markowitz_column_maximum(column)
    if store
        maxima[index] = maximum
        valid[index] = true
    end
    return maximum
end

_markowitz_threshold_pass(magnitude::T, column_maximum::T) where {T<:Real} =
    magnitude >= column_maximum / T(10)

_markowitz_threshold_pass(magnitude::Rational{BigInt}, column_maximum::Rational{BigInt}) =
    magnitude >= column_maximum / 10

# A column is unchanged throughout each candidate scan. Compute its exact
# rational threshold once; other types retain their original comparison.
_markowitz_column_threshold(maximum::Real) = maximum
_markowitz_column_threshold(maximum::Rational{BigInt}) = maximum / 10
_markowitz_candidate_pass(magnitude::Real, maximum::Real) =
    _markowitz_threshold_pass(magnitude,maximum)
_markowitz_candidate_pass(magnitude::Rational{BigInt}, threshold::Rational{BigInt}) =
    magnitude >= threshold

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

function _markowitz_pivot(rows::Vector{D}, columns::Vector{D},
                          active_rows::BitVector, active_columns::BitVector,
                          singleton_rows::Vector{Int},
                          singleton_columns::Vector{Int},
                          doubleton_columns::BitSet, cache=nothing) where {T<:Real,D<:AbstractDict{Int,T}}
    while !isempty(singleton_columns)
        column = pop!(singleton_columns)
        active_columns[column] && length(columns[column]) == 1 || continue
        return first(keys(columns[column])), column
    end
    # Columns are immutable during this search, but elimination changes them
    # between searches. Singleton-column exits need neither maxima nor a reset.
    isnothing(cache) || fill!(cache[2],false)
    index = length(singleton_rows)
    while index > 0
        row = singleton_rows[index]
        if active_rows[row] && length(rows[row]) == 1
            column = first(keys(rows[row]))
            value = rows[row][column]
            _markowitz_threshold_pass(_markowitz_magnitude(value),
                                      _markowitz_cached_maximum(columns[column],cache,column)) &&
                return row, column
            # Keep a rejected singleton: a later update may reduce the
            # column maximum and make it an admissible zero-fill pivot.
        else
            singleton_rows[index] = singleton_rows[end]
            pop!(singleton_rows)
        end
        index -= 1
    end

    # After the singleton search, score one is the best possible Markowitz
    # merit. Only columns and rows of length two can achieve it. Search all
    # such candidates to retain the original magnitude tie break.
    doubleton_row = 0
    doubleton_column = 0
    doubleton_magnitude = zero(T)
    for column in doubleton_columns
        active_columns[column] || continue
        column_data = columns[column]
        length(column_data) == 2 || continue
        column_maximum = _markowitz_column_threshold(_markowitz_cached_maximum(column_data,cache,column))
        for (row, value) in column_data
            length(rows[row]) == 2 || continue
            magnitude = _markowitz_magnitude(value)
            _markowitz_candidate_pass(magnitude, column_maximum) || continue
            if magnitude > doubleton_magnitude
                doubleton_row = row
                doubleton_column = column
                doubleton_magnitude = magnitude
            end
        end
    end
    doubleton_row != 0 && return doubleton_row, doubleton_column

    best_row = 0
    best_column = 0
    best_score = typemax(Int)
    best_magnitude = zero(T)
    for column in eachindex(active_columns)
        active_columns[column] || continue
        column_data = columns[column]
        column_maximum = _markowitz_column_threshold(_markowitz_cached_maximum(column_data,cache,column,false))
        # This is the final visit to the column: no need to store a new maximum.
        column_count = length(column_data)
        for (row, value) in column_data
            magnitude = _markowitz_magnitude(value)
            _markowitz_candidate_pass(magnitude, column_maximum) || continue
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

MarkowitzBackend(B::AbstractMatrix{T}) where {T<:Real} =
    MarkowitzBackend(B,OrderedCollections.OrderedDict{Int,T})

MarkowitzBackend(B::AbstractMatrix{T},::Type{D}) where {T<:Real,D<:AbstractDict{Int,T}} =
    _construct_markowitz(B,nothing,D)

function _markowitz_core_matrix(::Type{T}, n::Int, candidate) where {T}
    if !isnothing(candidate) && size(candidate.core.factors) == (n,n)
        return candidate.core.factors
    end
    return Matrix{T}(undef,n,n)
end

function _recycle_markowitz_vectors!(vectors, pool)
    for i in reverse(eachindex(vectors))
        vector = vectors[i]
        empty!(vector.indices)
        empty!(vector.values)
        push!(pool,vector)
    end
    empty!(vectors)
    return vectors
end

_take_markowitz_vector!(pool::Vector{PackedFactorVector{T}}) where {T} =
    isempty(pool) ? PackedFactorVector{T}(Int[],T[]) : pop!(pool)

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
            (workspace.column_maxima,workspace.column_maxima_valid),
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

function _refactorize_backend(backend::MarkowitzBackend{T,F,D}, B::AbstractMatrix{T}) where {T,F,D}
    # Keep a nonempty spare through repeated empty resets.
    size(B) == (0,0) && iszero(backend.dimension) && return backend
    # Only the inactive, private output may be overwritten. A failed construction
    # can damage that slot, but leaves the active factor and all copies intact.
    candidate = try
        _construct_markowitz(B,backend.workspace,D,backend.spare)
    catch
        backend.spare = nothing
        rethrow()
    end
    backend.spare = nothing
    candidate.spare = backend.shared ? nothing : backend
    return candidate
end

function refactorize!(factor::PFIFactorization{T,F}, B::AbstractMatrix{T}) where {T<:Real,F<:MarkowitzBackend}
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    resize!(factor.work, _backend_dimension(new_base))
    _recycle_pfi_updates!(factor)
    factor.sparse = nothing
    return factor
end

function _copy_backend(backend::MarkowitzBackend{T,F,D}) where {T,F,D}
    backend.shared = true
    return MarkowitzBackend{T,F,D}(
        backend.dimension, backend.sparse_pivots,
        backend.row_order, backend.column_order, backend.lower, backend.upper,
        backend.diagonal, backend.core,
        similar(backend.work), similar(backend.core_work), nothing,
        nothing, true, PackedFactorVector{T}[], PackedFactorVector{T}[],
    )
end
