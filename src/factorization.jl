const Float64UMFPACK = SparseArrays.UMFPACK.UmfpackLU{Float64,Int}

mutable struct UMFPACKBackend
    factorization::Union{Nothing,Float64UMFPACK}
    dimension::Int
    # A candidate is always private. Only a successful LU becomes active.
    spare::Union{Nothing,Float64UMFPACK}
    shared::Bool
end

UMFPACKBackend(factorization::Union{Nothing,Float64UMFPACK}, dimension::Int) =
    UMFPACKBackend(factorization, dimension, nothing, false)

struct DenseLUBackend{T,F}
    factorization::F
end

mutable struct Float32LUBackend{F}
    factorization::F
    # Concrete slots avoid boxing the immutable LU wrapper. With no spare,
    # this field aliases the active LU and must not be used as a candidate.
    spare::F
    has_spare::Bool
    shared::Bool
end

Float32LUBackend(factorization::F) where {F} =
    Float32LUBackend{F}(factorization, factorization, false, false)

struct PackedEta{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
    pivot_row::Int
end

mutable struct PFIFactorization{T<:Real,F}
    base::F
    updates::Vector{PackedEta{T}}
    # Private mutable solve scratch; concurrent solves need separate factorizations.
    work::Vector{T}
    # Only retired, unshared updates can donate their buffers to a later pivot.
    recycled_updates::Vector{PackedEta{T}}
    shared_update_count::Int
end

# Count active numeric storage; retired buffers and spare factorizations do not
# contribute to solve work. F19 can refine this with sparse reach information.
_backend_storage_count(backend::UMFPACKBackend) =
    isnothing(backend.factorization) ? 0 : nnz(backend.factorization)
_backend_storage_count(backend::Union{DenseLUBackend,Float32LUBackend}) =
    length(backend.factorization.factors)
_factor_storage_count(factor::PFIFactorization) =
    _backend_storage_count(factor.base)+sum(eta -> length(eta.values),factor.updates;init=0)
_factor_growth_reference(factor::PFIFactorization{T}) where T = one(T)
_factor_growth_measure(factor::PFIFactorization{T}) where T =
    maximum(eta -> maximum(abs,eta.values;init=one(T)),factor.updates;init=one(T))

_backend_dimension(backend::UMFPACKBackend) = backend.dimension
_backend_dimension(backend::Union{DenseLUBackend,Float32LUBackend}) =
    size(backend.factorization, 1)

function _factorize_basis(B::AbstractMatrix{Float64})
    # UMFPACK copies its input arrays; reuse an already matching CSC matrix.
    sparse_basis = convert(SparseMatrixCSC{Float64,Int}, B)
    rows, columns = size(sparse_basis)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    return iszero(rows) ? UMFPACKBackend(nothing, 0) : UMFPACKBackend(lu(sparse_basis), rows)
end

function _factorize_dense_basis(B::AbstractMatrix{T}) where {T<:Real}
    rows, columns = size(B)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    # Matrix constructs our private buffer, so LU can overwrite it directly.
    lu_result = lu!(Matrix{T}(B))
    return DenseLUBackend{T,typeof(lu_result)}(lu_result)
end

function _factorize_dense_basis(B::AbstractMatrix{Float32})
    rows, columns = size(B)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    return Float32LUBackend(lu!(Matrix{Float32}(B)))
end

_factorize_basis(B::AbstractMatrix{T}) where {T<:Real} = _factorize_dense_basis(B)
_factorize_basis(B::AbstractMatrix, ::Val{:native}) = _factorize_basis(B)

PFIFactorization(B::AbstractMatrix{T}) where {T<:Real} =
    PFIFactorization(B, Val(:native))

function PFIFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B, Val(R))
    return PFIFactorization{T,typeof(base)}(
        base, PackedEta{T}[], zeros(T, size(B, 1)), PackedEta{T}[], 0,
    )
end

function _check_rhs_dimension(factor::PFIFactorization, rhs::AbstractVector)
    length(rhs) == _backend_dimension(factor.base) ||
        throw(DimensionMismatch("right-hand side length must match the basis dimension"))
    return nothing
end

function _backend_forward_solve!(destination::Vector, backend::UMFPACKBackend,
                                 rhs::StridedVector)
    isnothing(backend.factorization) ? copyto!(destination, rhs) :
        ldiv!(destination, backend.factorization, rhs)
    return destination
end

function _backend_forward_solve!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend},
                                 rhs::AbstractVector)
    ldiv!(destination, backend.factorization, rhs)
    return destination
end

function _backend_transpose_solve!(destination::Vector, backend::UMFPACKBackend,
                                   rhs::StridedVector)
    isnothing(backend.factorization) ? copyto!(destination, rhs) :
        ldiv!(destination, transpose(backend.factorization), rhs)
    return destination
end

function _backend_transpose_solve!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend},
                                   rhs::AbstractVector)
    ldiv!(destination, transpose(backend.factorization), rhs)
    return destination
end

function _check_destination_dimension(factor::PFIFactorization, destination::AbstractVector)
    length(destination) == _backend_dimension(factor.base) ||
        throw(DimensionMismatch("destination length must match the basis dimension"))
    return nothing
end

function forward_solve!(destination::Vector{T}, factor::PFIFactorization{T},
                        rhs::StridedVector{T}) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    _check_rhs_dimension(factor, rhs)
    _check_destination_dimension(factor, destination)
    source = destination === rhs ? copyto!(factor.work, rhs) : rhs
    _backend_forward_solve!(destination, factor.base, source)
    for eta in factor.updates
        pivot = destination[eta.pivot_row]
        destination[eta.pivot_row] = zero(T)
        for index in eachindex(eta.indices)
            destination[eta.indices[index]] += pivot * eta.values[index]
        end
    end
    return destination
end

function forward_solve!(destination::Vector{T}, factor::PFIFactorization{T},
                        rhs::AbstractVector) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    _check_rhs_dimension(factor, rhs)
    copyto!(factor.work, rhs)
    return forward_solve!(destination, factor, factor.work)
end

function forward_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    return forward_solve!(Vector{T}(undef, length(rhs)), factor, rhs)
end

function transpose_solve!(destination::Vector{T}, factor::PFIFactorization{T},
                          rhs::AbstractVector) where {T}
    destination === factor.work && throw(ArgumentError(
        "destination must not alias the factorization work storage",
    ))
    _check_rhs_dimension(factor, rhs)
    _check_destination_dimension(factor, destination)
    copyto!(factor.work, rhs)
    for eta in Iterators.reverse(factor.updates)
        value = zero(T)
        for index in eachindex(eta.indices)
            value += eta.values[index] * factor.work[eta.indices[index]]
        end
        factor.work[eta.pivot_row] = value
    end
    return _backend_transpose_solve!(destination, factor.base, factor.work)
end

function transpose_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    return transpose_solve!(Vector{T}(undef, length(rhs)), factor, rhs)
end

_pivot_magnitude(value::Real) = abs(value)
_pivot_magnitude(value::BigFloat) = setprecision(BigFloat, precision(value)) do
    # Negating a stored negative BigFloat must not round before the cutoff check.
    abs(value)
end

function replace_column!(
    factor::PFIFactorization{T},
    tableau_column::AbstractVector,
    pivot_row::Integer;
    zero_tolerance::Real=_is_exact(T) === Val(true) ? zero(T) :
                         _positive_tolerance(T, 1 // 10^12),
) where {T}
    tolerance = convert(T, zero_tolerance)
    isfinite(tolerance) && tolerance >= zero(T) ||
        throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    length(tableau_column) == _backend_dimension(factor.base) ||
        throw(DimensionMismatch("tableau column length must match the basis dimension"))

    pivot = Int(pivot_row)
    checkbounds(tableau_column, pivot)
    pivot_value = convert(T, tableau_column[pivot])
    _pivot_magnitude(pivot_value) > tolerance || throw(LinearAlgebra.ZeroPivotException(pivot))

    inverse_pivot = inv(pivot_value)
    if !isempty(factor.recycled_updates)
        retired = pop!(factor.recycled_updates)
        entry_count = tableau_column isa AbstractVector{T} ?
            count(!iszero, tableau_column) : 1
        indices = resize!(retired.indices, entry_count)
        values = resize!(retired.values, entry_count)
        resize!(indices, 1)
        resize!(values, 1)
        indices[1] = pivot
        values[1] = inverse_pivot
    elseif tableau_column isa AbstractVector{T}
        # Allocate the final capacity once, without first creating singleton
        # buffers that would immediately need to grow.
        entry_count = count(!iszero, tableau_column)
        indices = Vector{Int}(undef, entry_count)
        values = Vector{T}(undef, entry_count)
        resize!(indices, 1)
        resize!(values, 1)
        indices[1] = pivot
        values[1] = inverse_pivot
    else
        # Converting mixed-type inputs just to count nonzeros can allocate
        # heavily, so retain the single conversion pass.
        indices = Int[pivot]
        values = T[inverse_pivot]
    end
    for row in eachindex(tableau_column)
        row == pivot && continue
        value = convert(T, tableau_column[row])
        iszero(value) && continue
        push!(indices, row)
        push!(values, -(value / pivot_value))
    end
    push!(factor.updates, PackedEta{T}(indices, values, pivot))
    return factor
end

function _same_umfpack_pattern(factor::Float64UMFPACK, B::SparseMatrixCSC{Float64,Int})
    size(factor) == size(B) || return false
    length(factor.colptr) == length(B.colptr) || return false
    length(factor.rowval) == length(B.rowval) || return false
    # UMFPACK owns zero-based indices; normal Julia CSC indices are one-based.
    offset = iszero(first(B.colptr)) ? 0 : 1
    for index in eachindex(B.colptr)
        factor.colptr[index] == B.colptr[index] - offset || return false
    end
    for index in eachindex(B.rowval)
        factor.rowval[index] == B.rowval[index] - offset || return false
    end
    return true
end

function _refactorize_backend(backend::UMFPACKBackend, B::AbstractMatrix{Float64})
    sparse_basis = convert(SparseMatrixCSC{Float64,Int}, B)
    rows, columns = size(sparse_basis)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    if iszero(rows)
        if !backend.shared && !isnothing(backend.factorization)
            backend.spare = backend.factorization
        end
        backend.factorization = nothing
        backend.dimension = 0
        backend.shared = false
        return backend
    end

    candidate = backend.spare
    if isnothing(candidate)
        candidate = lu(sparse_basis)
    else
        reuse_symbolic = _same_umfpack_pattern(candidate, sparse_basis)
        try
            lu!(candidate, sparse_basis; reuse_symbolic)
        catch
            # lu! can change indices and symbolic/numeric state before failing.
            # Drop that candidate; the active LU and all copies are untouched.
            backend.spare = nothing
            rethrow()
        end
    end
    backend.spare = backend.shared ? nothing : backend.factorization
    backend.factorization = candidate
    backend.dimension = rows
    backend.shared = false
    return backend
end

function _recycle_pfi_updates!(factor::PFIFactorization)
    # Copies share an immutable prefix of the active history. Never clear or
    # recycle that prefix, even if the copy has since become unreachable.
    for index in (factor.shared_update_count + 1):length(factor.updates)
        eta = factor.updates[index]
        empty!(eta.indices)
        empty!(eta.values)
        push!(factor.recycled_updates, eta)
    end
    empty!(factor.updates)
    factor.shared_update_count = 0
    return nothing
end

function _refactorize_backend(
    backend::DenseLUBackend{T}, B::AbstractMatrix{T},
) where {T<:Real}
    return _factorize_dense_basis(B)
end

function _refactorize_backend(backend::Float32LUBackend, B::AbstractMatrix{Float32})
    rows, columns = size(B)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    # Repeated empty resets should not evict a nonempty private spare.
    iszero(rows) && iszero(_backend_dimension(backend)) && return backend
    candidate = backend.spare
    if !backend.has_spare || size(candidate) != size(B)
        candidate = lu!(Matrix{Float32}(B))
    else
        try
            # The returned LU carries the new status, reusing factors and pivots.
            candidate = lu!(candidate, B)
        catch
            backend.spare = backend.factorization
            backend.has_spare = false
            rethrow()
        end
    end
    backend.spare = backend.shared ? candidate : backend.factorization
    backend.has_spare = !backend.shared
    backend.factorization = candidate
    backend.shared = false
    return backend
end

function refactorize!(factor::PFIFactorization{Float64,UMFPACKBackend}, B::AbstractMatrix{Float64})
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    resize!(factor.work, _backend_dimension(new_base))
    _recycle_pfi_updates!(factor)
    return factor
end

function refactorize!(factor::PFIFactorization{T,F}, B::AbstractMatrix{T}) where {T<:Real,F<:Union{DenseLUBackend,Float32LUBackend}}
    new_base = _refactorize_backend(factor.base, B)
    factor.base = new_base
    resize!(factor.work, _backend_dimension(new_base))
    _recycle_pfi_updates!(factor)
    return factor
end

_copy_backend(backend::DenseLUBackend) = backend

function _copy_backend(backend::Float32LUBackend)
    backend.shared = true
    return Float32LUBackend(backend.factorization, backend.factorization, false, true)
end

function _copy_backend(backend::UMFPACKBackend)
    backend.shared = true
    # Share only the active LU, never the mutable slot container or its spare.
    return UMFPACKBackend(backend.factorization, backend.dimension, nothing, true)
end

function copy_basis_factorization(factor::PFIFactorization{T,F}) where {T,F}
    factor.shared_update_count = length(factor.updates)
    return PFIFactorization{T,F}(
        _copy_backend(factor.base), copy(factor.updates), similar(factor.work),
        PackedEta{T}[], factor.shared_update_count,
    )
end

_basis_factorization(B, ::Val{:pfi}) = PFIFactorization(B)
_basis_factorization(B, ::Val{:pfi}, refactorization::Val) =
    PFIFactorization(B, refactorization)
_basis_factorization(B, ::SolverOptions{T,M,R}) where {T,M,R} =
    _basis_factorization(B, Val(M), Val(R))
