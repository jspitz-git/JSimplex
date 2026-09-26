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
    _advance_pricing_basis!(ws)
    return nothing
end

"""Recompute values and prices independently and check their predictions.

An inaccurate prediction retains independently recomputed values and prices.
The internal result distinguishes a verified correction from an unreliable
recomputation; incremental pivots may publish a feasible verified correction.
"""
audit_primal_values!(ws::SimplexWorkspace)::Bool = _audit_primal_values!(ws) == :accurate

function _audit_primal_values!(ws::SimplexWorkspace{T})::Symbol where T
    return _with_recovery_precision(ws, ws) do
        predicted = copy(ws.primal)
        predicted_costs = copy(ws.reduced_costs)
        recompute!(ws)
        _finite_workspace(ws) && _recomputed_basis_reliable(ws) || return :unreliable
        tolerance = ws.progress.numerical_policy.solve_tolerance
        for i in eachindex(predicted)
            old, current = predicted[i], ws.primal[i]
            isfinite(old) || return :corrected
            if T <: Rational
                old == current || return :corrected
            else
                scale = max(one(T), abs(old), abs(current))
                abs(old / scale - current / scale) <= tolerance || return :corrected
            end
        end
        return _primal_price_prediction_reliable(ws,predicted_costs) ? :accurate : :corrected
    end
end

# Validate all predicted prices before publishing any of them.
function _primal_price_multiplier(costs, row, entering, leaving, pivot)
    axes(costs) == axes(row) || throw(DimensionMismatch("primal pricing row dimensions"))
    Base.mightalias(costs, row) && throw(ArgumentError("pricing row aliases reduced costs"))
    entering != leaving || throw(ArgumentError("entering and leaving variables must differ"))
    isfinite(pivot) && !iszero(pivot) || throw(_UnreliableBasisSolve())
    alpha = costs[entering] / pivot
    isfinite(alpha) || throw(_UnreliableBasisSolve())
    for i in eachindex(costs, row)
        isfinite(row[i]) && isfinite(costs[i] - alpha * row[i]) ||
            throw(_UnreliableBasisSolve())
    end
    return alpha
end

"""Update prices with an unoriented row of the old basis tableau."""
function update_reduced_costs!(costs::AbstractVector{T}, row::AbstractVector{T},
                               entering::Int, leaving::Int, pivot::T)::Nothing where T
    alpha = _primal_price_multiplier(costs, row, entering, leaving, pivot)
    return _apply_reduced_costs!(costs,row,entering,leaving,alpha)
end

function _apply_reduced_costs!(costs::AbstractVector{T},row,entering,leaving,alpha)::Nothing where T
    for i in eachindex(costs, row)
        costs[i] -= alpha * row[i]
    end
    costs[entering] = zero(T)
    # The old leaving column is a unit basis column, including when the
    # computed tableau row has small roundoff in its basic entries.
    costs[leaving] = -alpha
    return nothing
end

"""Apply a validated primal pivot, retaining the old row and column until exchange.

The ratio test supplies the leaving state explicitly, including zero steps.
The caller owns pricing-weight updates and the completed-step counter.
"""
function apply_primal_pivot!(ws::SimplexWorkspace{T}, entering::Int, leaving_row::Int,
                             signed_change::T, column::AbstractVector{T},
                             row::AbstractVector{T}; leaving_state::VariableState,
                             stop_requested=nothing)::Nothing where T
    return _with_recovery_precision(ws, ws) do
        length(column) == length(ws.basis.basic_indices) ||
            throw(DimensionMismatch("primal pivot column dimensions"))
        (Base.mightalias(column,ws.primal) || Base.mightalias(row,ws.primal) ||
         Base.mightalias(column,ws.reduced_costs)) &&
            throw(ArgumentError("primal pivot direction aliases live values"))
        ws.basis.states[entering] != BASIC ||
            throw(ArgumentError("entering variable is already basic"))
        leaving_state in (AT_LOWER, AT_UPPER) ||
            throw(ArgumentError("leaving variable requires a bound state"))
        leaving = ws.basis.basic_indices[leaving_row]
        target = leaving_state == AT_LOWER ? ws.lower[leaving] : ws.upper[leaving]
        isfinite(target) || throw(ArgumentError("leaving bound must be finite"))
        pivot = row[entering]
        alpha = _primal_price_multiplier(ws.reduced_costs,row,entering,leaving,pivot)
        isfinite(signed_change) && isfinite(ws.primal[entering]+signed_change) ||
            throw(_UnreliableBasisSolve())
        for (r,index) in enumerate(ws.basis.basic_indices)
            isfinite(ws.primal[index]-signed_change*column[r]) || throw(_UnreliableBasisSolve())
        end
        _replace_pivot_column!(ws,column,leaving_row;zero_tolerance=zero(T),stop_requested)
        for (r,index) in enumerate(ws.basis.basic_indices)
            ws.primal[index] -= signed_change*column[r]
        end
        ws.primal[entering] += signed_change
        ws.primal[leaving] = bound_value(target)
        _apply_reduced_costs!(ws.reduced_costs,row,entering,leaving,alpha)
        ws.basis.basic_indices[leaving_row] = entering
        ws.basis.states[entering] = BASIC
        ws.basis.states[leaving] = leaving_state
        _advance_pricing_basis!(ws)
        ws.scratch.basic_mask[entering] = true
        ws.scratch.basic_mask[leaving] = false
        for index in ws.basis.basic_indices
            ws.reduced_costs[index] = zero(T)
        end
        ws.scratch.last_dual_step = alpha
        return nothing
    end
end

# The implicit system [A'; -I] * dual + reduced_costs = costs retains
# the original arithmetic terms in its residual scale,
# unlike a forward difference divided by a nearly cancelled reduced cost.
struct _PriceAuditMatrix{T} <: AbstractMatrix{T}
    matrix::SparseMatrixCSC{T,Int}
end
function Base.size(B::_PriceAuditMatrix)
    m,n = size(B.matrix)
    return (n+m,n+2m)
end
function Base.getindex(B::_PriceAuditMatrix{T},i::Int,j::Int) where T
    @boundscheck checkbounds(B,i,j)
    m,n = size(B.matrix)
    j > m && return i == j-m ? one(T) : zero(T)
    i <= n && return B.matrix[j,i]
    return i-n == j ? -one(T) : zero(T)
end
_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)

function _compensated_quality_components!(scratch,B::_PriceAuditMatrix{T},x,transposed) where T
    A = B.matrix
    m,n = size(A)
    for j in axes(A,2), p in nzrange(A,j)
        target,source = transposed ? (A.rowval[p],j) : (j,A.rowval[p])
        _compensated_quality_term!(scratch,A.nzval[p],x[source],target)
    end
    for i in 1:m
        target,source = transposed ? (i,n+i) : (n+i,i)
        _compensated_quality_term!(scratch,-one(T),x[source],target)
    end
    for i in 1:n+m
        target,source = transposed ? (m+i,i) : (i,m+i)
        _compensated_quality_term!(scratch,one(T),x[source],target)
    end
    return nothing
end

function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix{T},
                               x,rhs,transposed) where {W,T}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    A = B.matrix
    m,n = size(A)
    unsafe = false
    for j in axes(A,2), p in nzrange(A,j)
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,A.nzval[p],j,A.rowval[p],transposed)
    end
    for i in 1:m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,-one(T),n+i,i,transposed)
    end
    for i in 1:n+m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,one(T),i,m+i,transposed)
    end
    return unsafe
end

function _primal_price_prediction_reliable(ws::SimplexWorkspace{T},predicted) where T
    all(i -> iszero(predicted[i]),ws.basis.basic_indices) || return false
    B = _PriceAuditMatrix(ws.problem.A)
    values = vcat(ws.scratch.rho,predicted)
    scratch = SolveQualityScratch(T,length(ws.costs))
    return solve_quality!(scratch,B,values,ws.costs,ws.progress.numerical_policy).reliable
end
