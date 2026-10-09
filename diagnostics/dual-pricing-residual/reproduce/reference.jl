# Frozen arithmetic from d1978a1; a lightweight fixture replaces workspace dispatch.
function reference_ratio(workspace,
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = @inbounds -rho[index - column_count]
            residual += term
            scale += abs(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + one(T)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, abs(residual) / tolerance)
    end
    return worst_ratio
end
