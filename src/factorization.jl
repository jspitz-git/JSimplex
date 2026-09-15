const Float64UMFPACK = SparseArrays.UMFPACK.UmfpackLU{Float64,Int}

struct UMFPACKBackend
    factorization::Union{Nothing,Float64UMFPACK}
    dimension::Int
end

struct DenseLUBackend{T,F}
    factorization::F
end

struct PackedEta{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
    pivot_row::Int
end

mutable struct PFIFactorization{T<:Real,F}
    base::F
    updates::Vector{PackedEta{T}}
end

_backend_dimension(backend::UMFPACKBackend) = backend.dimension
_backend_dimension(backend::DenseLUBackend) = size(backend.factorization, 1)

function _factorize_basis(B::AbstractMatrix{Float64})
    sparse_basis = SparseMatrixCSC{Float64,Int}(B)
    rows, columns = size(sparse_basis)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    return iszero(rows) ? UMFPACKBackend(nothing, 0) : UMFPACKBackend(lu(sparse_basis), rows)
end

function _factorize_dense_basis(B::AbstractMatrix{T}) where {T<:Real}
    rows, columns = size(B)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    lu_result = lu(Matrix{T}(B))
    return DenseLUBackend{T,typeof(lu_result)}(lu_result)
end

_factorize_basis(B::AbstractMatrix{T}) where {T<:Real} = _factorize_dense_basis(B)

function PFIFactorization(B::AbstractMatrix{T}) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))
    base = _factorize_basis(B)
    return PFIFactorization{T,typeof(base)}(base, PackedEta{T}[])
end

function _check_rhs_dimension(factor::PFIFactorization, rhs::AbstractVector)
    length(rhs) == _backend_dimension(factor.base) ||
        throw(DimensionMismatch("right-hand side length must match the basis dimension"))
    return nothing
end

_backend_forward_solve(backend::UMFPACKBackend, rhs::AbstractVector) =
    isnothing(backend.factorization) ? copy(rhs) : backend.factorization \ rhs
_backend_forward_solve(backend::DenseLUBackend, rhs::AbstractVector) =
    backend.factorization \ rhs

_backend_transpose_solve(backend::UMFPACKBackend, rhs::AbstractVector) =
    isnothing(backend.factorization) ? copy(rhs) : transpose(backend.factorization) \ rhs
_backend_transpose_solve(backend::DenseLUBackend, rhs::AbstractVector) =
    transpose(backend.factorization) \ rhs

function forward_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    _check_rhs_dimension(factor, rhs)
    x = _backend_forward_solve(factor.base, convert.(T, rhs))
    for eta in factor.updates
        pivot = x[eta.pivot_row]
        x[eta.pivot_row] = zero(T)
        for index in eachindex(eta.indices)
            x[eta.indices[index]] += pivot * eta.values[index]
        end
    end
    return x
end

function transpose_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    _check_rhs_dimension(factor, rhs)
    x = convert.(T, rhs)
    for eta in Iterators.reverse(factor.updates)
        value = zero(T)
        for index in eachindex(eta.indices)
            value += eta.values[index] * x[eta.indices[index]]
        end
        x[eta.pivot_row] = value
    end
    return _backend_transpose_solve(factor.base, x)
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

    indices = Int[pivot]
    values = T[inv(pivot_value)]
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

function _refactorize_backend(backend::UMFPACKBackend, B::AbstractMatrix{Float64})
    return _factorize_basis(B)
end

function _refactorize_backend(
    backend::DenseLUBackend{T}, B::AbstractMatrix{T},
) where {T<:Real}
    return _factorize_dense_basis(B)
end

function refactorize!(factor::PFIFactorization{Float64,UMFPACKBackend}, B::AbstractMatrix{Float64})
    factor.base = _refactorize_backend(factor.base, B)
    empty!(factor.updates)
    return factor
end

function refactorize!(factor::PFIFactorization{T,F}, B::AbstractMatrix{T}) where {T<:Real,F<:DenseLUBackend}
    factor.base = _refactorize_backend(factor.base, B)
    empty!(factor.updates)
    return factor
end
