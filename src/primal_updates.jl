"""Apply a bound flip using an already validated, unoriented tableau column.

`signed_change` is the actual change of the entering variable. The basis,
factorization, costs, prices, and completed-step count are unchanged. Predict
every value before writing so an overflow cannot publish a partial flip.
"""
function apply_primal_flip!(ws::SimplexWorkspace{T}, entering::Int,
                            signed_change::T, column::AbstractVector{T})::Nothing where T
    return _with_recovery_precision(ws, ws) do
        _apply_primal_flip!(ws, entering, signed_change, column)
    end
end

function _apply_primal_flip!(ws::SimplexWorkspace{T}, entering::Int,
                             signed_change::T, column::AbstractVector{T})::Nothing where T
    length(column) == length(ws.basis.basic_indices) ||
        throw(DimensionMismatch("primal flip column dimensions"))
    Base.mightalias(column, ws.primal) &&
        throw(ArgumentError("primal flip direction aliases live values"))
    state = ws.basis.states[entering]
    state in (AT_LOWER, AT_UPPER) ||
        throw(ArgumentError("a bound flip requires a bounded nonbasic variable"))
    iszero(signed_change) && return nothing
    isfinite(signed_change) || throw(_UnreliableBasisSolve())
    target = state == AT_LOWER ? ws.upper[entering] : ws.lower[entering]
    isfinite(target) || throw(ArgumentError("a bound flip requires a finite opposite bound"))
    value = bound_value(target)
    signed_change == value - ws.primal[entering] ||
        throw(ArgumentError("a bound flip must reach the opposite bound"))
    isfinite(ws.primal[entering] + signed_change) || throw(_UnreliableBasisSolve())
    for (row, index) in enumerate(ws.basis.basic_indices)
        isfinite(ws.primal[index] - signed_change * column[row]) ||
            throw(_UnreliableBasisSolve())
    end
    for (row, index) in enumerate(ws.basis.basic_indices)
        ws.primal[index] -= signed_change * column[row]
    end
    ws.primal[entering] = value
    ws.basis.states[entering] = state == AT_LOWER ? AT_UPPER : AT_LOWER
    return nothing
end

"""Recompute values independently and report whether the prediction stayed accurate.

A failed audit retains the recomputed values. Transactional callers discard
the candidate and retry from a freshly recomputed basis before publishing it.
"""
function audit_primal_values!(ws::SimplexWorkspace{T})::Bool where T
    return _with_recovery_precision(ws, ws) do
        predicted = copy(ws.primal)
        recompute!(ws)
        _finite_workspace(ws) && _recomputed_basis_reliable(ws) || return false
        tolerance = ws.progress.numerical_policy.solve_tolerance
        for i in eachindex(predicted)
            old, current = predicted[i], ws.primal[i]
            isfinite(old) || return false
            if T <: Rational
                old == current || return false
            else
                scale = max(one(T), abs(old), abs(current))
                abs(old / scale - current / scale) <= tolerance || return false
            end
        end
        return true
    end
end
