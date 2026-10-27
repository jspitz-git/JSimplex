module LocalCandidateAB
using JSimplex,SparseArrays
using JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,
    _is_exact,_compensated_solve_quality!,_primal_direction_magnitude,
    _with_recovery_precision,_finite_workspace,_recomputed_basis_reliable,
    _primal_price_prediction_reliable,recompute!,_PriceAuditMatrix
function _componentwise_backward_error(residual::AbstractVector{T}, scale) where {T<:AbstractFloat}
    axes(residual) == axes(scale) || throw(DimensionMismatch("Residual and scale dimensions differ"))
    error = zero(T)
    for i in eachindex(residual,scale)
        r, s = abs(residual[i]), scale[i]
        isfinite(r) && isfinite(s) && s >= zero(s) || return T(Inf)
        ratio = iszero(s) ? (iszero(r) ? zero(T) : T(Inf)) : r/s
        error = max(error,ratio)
    end
    return error
end

_quality_values(B::AbstractMatrix) = B
_quality_values(B::SparseMatrixCSC) = nonzeros(B)

@inline function _accumulate_quality_term!(r::AbstractVector{W}, scale, terms,
                                          x, a, row, column, transposed) where {W}
    target, source = transposed ? (column,row) : (row,column)
    product = W(a)*W(x[source])
    r[target] -= product
    scale[target] += abs(product)
    terms[target] += 2
    return W <: AbstractFloat && !iszero(a) && !iszero(x[source]) &&
           abs(product) < floatmin(W)
end

function _quality_components!(r::AbstractVector{W}, scale, terms, B, x, rhs, transposed) where {W}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B.nzval[p],B.rowval[p],column,transposed)
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B[row,column],row,column,transposed)
        end
    end
    return unsafe_range
end

# A call-local comparison limit is shared only across ordinary array accesses.
@inline function _bigfloat_quality_term!(r, scale, terms, x, a, row, column,
                                         transposed, limit::Union{Nothing,BigFloat})
    target, source = transposed ? (column,row) : (row,column)
    product = BigFloat(a)*BigFloat(x[source])
    r[target] -= product
    magnitude = _primal_direction_magnitude(product)
    scale[target] += magnitude
    terms[target] += 2
    if !iszero(a) && !iszero(x[source])
        if limit === nothing
            limit = floatmin(BigFloat)
        end
        return magnitude < limit, limit
    end
    return false, limit
end

function _quality_components!(r::Vector{BigFloat}, scale::Vector{BigFloat},
                              terms::Vector{Int},
                              B::Union{Matrix{BigFloat},SparseMatrixCSC{BigFloat}},
                              x::Vector{BigFloat}, rhs::Vector{BigFloat}, transposed)
    for i in eachindex(rhs)
        r[i] = BigFloat(rhs[i])
        scale[i] = _primal_direction_magnitude(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    limit::Union{Nothing,BigFloat} = nothing
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B.nzval[p],
                B.rowval[p],column,transposed,limit)
            unsafe_range |= unsafe
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B[row,column],
                row,column,transposed,limit)
            unsafe_range |= unsafe
        end
    end
    return unsafe_range
end

function _quality_roundoff(::Type{W}, terms) where {W<:AbstractFloat}
    k = maximum(terms; init=0)
    product = W(k)*eps(W)
    return isfinite(product) && product < one(W) ? product/(one(W)-product) : W(Inf)
end

function _floating_quality!(scratch::SolveQualityScratch{T}, r, scale, terms, policy) where {T}
    ratio = _componentwise_backward_error(r,scale)
    absolute = maximum(abs,r; init=zero(eltype(r)))
    for i in eachindex(r)
        scratch.residual[i] = convert(T,r[i])
    end
    absolute_T, ratio_T = convert(T,absolute), convert(T,ratio)
    iszero(absolute_T) && absolute > 0 && (absolute_T = nextfloat(zero(T)))
    finite = isfinite(absolute_T) && isfinite(ratio_T) && all(isfinite,scratch.residual)
    roundoff = _quality_roundoff(eltype(r),terms)
    reliable = finite && isfinite(roundoff) && roundoff < 1 &&
        (ratio + roundoff)/(1-roundoff) <= policy.solve_tolerance
    return SolveQuality{T}(absolute_T,ratio_T,finite,reliable)
end

_stored_quality_bits(::Type{T}, B, x, rhs, policy) where {T<:AbstractFloat} = precision(T)
function _stored_quality_bits(::Type{BigFloat}, B, x, rhs, policy)
    return max(precision(BigFloat), precision(policy.solve_tolerance),
        maximum(precision,_quality_values(B);init=2), maximum(precision,x;init=2),
        maximum(precision,rhs;init=2))
end

function _wide_solve_quality!(scratch::SolveQualityScratch{T}, B, x, rhs, policy, transposed) where {T}
    input_bits = _stored_quality_bits(T,B,x,rhs,policy)
    term_count = max(size(B,1),size(B,2),1)
    # Additional bits keep residual-evaluation uncertainty below the policy's
    # solve tolerance; this does not change the basis working precision.
    bits = max(128, 2*input_bits + ndigits(term_count; base=2) + 16)
    return setprecision(BigFloat,bits) do
        r, scale = zeros(BigFloat,length(rhs)), zeros(BigFloat,length(rhs))
        unsafe_range = _quality_components!(r,scale,scratch.terms,B,x,rhs,transposed)
        quality = _floating_quality!(scratch,r,scale,scratch.terms,policy)
        unsafe_range ? SolveQuality{T}(quality.absolute_error,quality.relative_error,false,false) : quality
    end
end

"""Evaluate an absolute residual and a componentwise backward error.

Scratch is owned separately from live tableau vectors. Float32 and Float64 use
native compensated accumulation before a local BigFloat evaluation is needed
for unsafe range or an inconclusive rounding-error enclosure. Stored
BigFloat precision is respected. Small backward error is not a forward-error
or pivot-safety certificate. Exact rationals require an exactly zero residual.
"""
function solve_quality!(scratch::SolveQualityScratch{T}, B::AbstractMatrix{T},
                        x::AbstractVector{T}, rhs::AbstractVector{T},
                        policy::NumericalPolicy{T}; transposed::Bool=false) where {T}
    rows, columns = transposed ? reverse(size(B)) : size(B)
    length(rhs) == rows && length(x) == columns && length(scratch.residual) == rows ||
        throw(DimensionMismatch("Incompatible basis residual dimensions"))
    any(array -> Base.mightalias(array,rhs) || Base.mightalias(array,x) ||
        Base.mightalias(array,_quality_values(B)),
        (scratch.residual,scratch.work_residual,scratch.work_scale,
         scratch.compensation,scratch.error_sum)) &&
        throw(ArgumentError("Quality scratch must not alias basis, solution, or RHS"))
    if _is_exact(T) === Val(true)
        _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
        copyto!(scratch.residual,scratch.work_residual)
        absolute = maximum(abs,scratch.residual;init=zero(T))
        return SolveQuality{T}(absolute,nothing,true,iszero(absolute))
    end
    if !all(isfinite,_quality_values(B)) || !all(isfinite,x) || !all(isfinite,rhs)
        fill!(scratch.residual,T(Inf))
        return SolveQuality{T}(T(Inf),T(Inf),false,false)
    end
    T === BigFloat && return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    unsafe_range = _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
    roundoff = _quality_roundoff(eltype(scratch.work_residual),scratch.terms)
    if unsafe_range || !all(isfinite,scratch.work_residual) || !all(isfinite,scratch.work_scale) ||
       roundoff > policy.solve_tolerance/4
        if !unsafe_range
            native = _compensated_solve_quality!(scratch,B,x,rhs,policy,transposed)
            isnothing(native) || return native
        end
        return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    end
    return _floating_quality!(scratch,scratch.work_residual,scratch.work_scale,scratch.terms,policy)
end


function _componentwise_backward_error(residual::Vector{BigFloat}, scale::Vector{BigFloat})
    T = BigFloat
    axes(residual) == axes(scale) || throw(DimensionMismatch("Residual and scale dimensions differ"))
    error = zero(T)
    for i in eachindex(residual,scale)
        r, s = _primal_direction_magnitude(residual[i]), scale[i]
        isfinite(r) && isfinite(s) && s >= Clong(0) || return T(Inf)
        ratio = iszero(s) ? (iszero(r) ? zero(T) : T(Inf)) : r/s
        error = max(error,ratio)
    end
    return error
end

function _quality_roundoff(::Type{BigFloat}, terms)
    W = BigFloat
    k = maximum(terms; init=0)
    product = W(k)*eps(W)
    return isfinite(product) && product < Clong(1) ? product/(Clong(1)-product) : W(Inf)
end

function _floating_quality!(scratch::SolveQualityScratch{T}, r::Vector{BigFloat},
                            scale::Vector{BigFloat}, terms::Vector{Int}, policy) where {T}
    ratio = _componentwise_backward_error(r,scale)
    absolute = maximum(_primal_direction_magnitude,r; init=zero(eltype(r)))
    for i in eachindex(r)
        scratch.residual[i] = convert(T,r[i])
    end
    absolute_T, ratio_T = convert(T,absolute), convert(T,ratio)
    iszero(absolute_T) && absolute > 0 && (absolute_T = nextfloat(zero(T)))
    finite = isfinite(absolute_T) && isfinite(ratio_T) && all(isfinite,scratch.residual)
    roundoff = _quality_roundoff(eltype(r),terms)
    reliable = finite && isfinite(roundoff) && roundoff < 1 &&
        (ratio + roundoff)/(1-roundoff) <= policy.solve_tolerance
    return SolveQuality{T}(absolute_T,ratio_T,finite,reliable)
end

_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)
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


end
