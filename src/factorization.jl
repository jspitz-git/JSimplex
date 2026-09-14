struct PackedEta
    indices::Vector{Int}
    values::Vector{Float64}
    pivot_row::Int
end

mutable struct PFIFactorization
    base::Any
    updates::Vector{PackedEta}
end

function _factorize_basis(B::AbstractMatrix)
    rows, columns = size(B)
    rows == columns || throw(DimensionMismatch("basis matrix must be square"))
    return lu(SparseMatrixCSC{Float64, Int}(B))
end

function PFIFactorization(B::AbstractMatrix)
    return PFIFactorization(_factorize_basis(B), PackedEta[])
end

function _check_rhs_dimension(factor::PFIFactorization, rhs::AbstractVector)
    length(rhs) == size(factor.base, 1) ||
        throw(DimensionMismatch("right-hand side length must match the basis dimension"))
    return nothing
end

function forward_solve(factor::PFIFactorization, rhs::AbstractVector)
    _check_rhs_dimension(factor, rhs)
    x = factor.base \ copy(rhs)
    for eta in factor.updates
        pivot = x[eta.pivot_row]
        x[eta.pivot_row] = zero(eltype(x))
        for index in eachindex(eta.indices)
            x[eta.indices[index]] += pivot * eta.values[index]
        end
    end
    return x
end

function transpose_solve(factor::PFIFactorization, rhs::AbstractVector)
    _check_rhs_dimension(factor, rhs)
    x = Float64.(rhs)
    for eta in Iterators.reverse(factor.updates)
        value = zero(eltype(x))
        for index in eachindex(eta.indices)
            value += eta.values[index] * x[eta.indices[index]]
        end
        x[eta.pivot_row] = value
    end
    return adjoint(factor.base) \ x
end

function replace_column!(
    factor::PFIFactorization,
    tableau_column::AbstractVector,
    pivot_row::Integer;
    zero_tolerance::Real=1.0e-12,
)
    isfinite(zero_tolerance) && zero_tolerance >= zero(zero_tolerance) ||
        throw(ArgumentError("zero_tolerance must be finite and nonnegative"))
    length(tableau_column) == size(factor.base, 1) ||
        throw(DimensionMismatch("tableau column length must match the basis dimension"))

    pivot = Int(pivot_row)
    checkbounds(tableau_column, pivot)
    pivot_value = Float64(tableau_column[pivot])
    abs(pivot_value) > zero_tolerance || throw(LinearAlgebra.ZeroPivotException(pivot))

    indices = Int[pivot]
    values = Float64[inv(pivot_value)]
    for row in 1:length(tableau_column)
        row == pivot && continue
        value = Float64(tableau_column[row])
        iszero(value) && continue
        push!(indices, row)
        push!(values, -value / pivot_value)
    end
    push!(factor.updates, PackedEta(indices, values, pivot))
    return factor
end

function refactorize!(factor::PFIFactorization, B::AbstractMatrix)
    factor.base = _factorize_basis(B)
    empty!(factor.updates)
    return factor
end
