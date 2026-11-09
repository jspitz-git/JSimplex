# Guarded compensated original-column intervals for ambiguous BASIC stationarity.
# Included after primal_row_certification.jl, which supplies the pair/bound helpers.
_native_basic_certificate_mode(::Type{T}) where T = false
_native_basic_certificate_mode(::Type{T}, mode, ftz::Bool) where T = false

@inline function _native_basic_certificate_mode(::Type{T}, mode, ftz::Bool) where {T<:Union{Float32,Float64}}
    return mode === RoundNearest && !ftz
end

@inline function _native_basic_certificate_mode(::Type{T}) where {T<:Union{Float32,Float64}}
    return _native_basic_certificate_mode(T,rounding(T),get_zero_subnormals())
end

# Private kernel: the caller must have verified nearest rounding and gradual
# underflow locally, with no intervening callback. The certificate supplies that caller.
# There is no retained mode proof, cache, model/factor owner or mutable scratch.
function _native_basic_column_interval(problem::LinearProblem{T}, dual::Vector{T},
                                        column::Int) where {T<:Union{Float32,Float64}}
    A=problem.A
    length(dual)==size(A,1) || throw(DimensionMismatch("dual length differs from original row count"))
    checkbounds(Base.OneTo(size(A,2)),column)
    checkbounds(problem.objective,column)
    cost=problem.objective[column]
    isfinite(cost) || return nothing
    high=tail_lower=tail_upper=zero(T)
    for position in A.colptr[column]:(A.colptr[column+1]-1)
        coefficient=A.nzval[position]
        value=dual[A.rowval[position]]
        # Finite input checks precede the product helper's zero/unit shortcuts.
        isfinite(coefficient) && isfinite(value) || return nothing
        product=_native_row_product_pair(coefficient,value)
        isnothing(product) && return nothing
        product_value,product_error=product
        isfinite(product_error) || return nothing # Sum pair already checks product_value.
        pair=_native_row_sum_pair(high,product_value)
        isnothing(pair) && return nothing
        high,sum_error=pair
        # Invariant: the exact original dot is in high+[tail_lower,tail_upper].
        tail_lower,_=_primal_sum_bounds(tail_lower,product_error)
        _,tail_upper=_primal_sum_bounds(tail_upper,product_error)
        tail_lower,_=_primal_sum_bounds(tail_lower,sum_error)
        _,tail_upper=_primal_sum_bounds(tail_upper,sum_error)
    end
    isfinite(tail_lower) && isfinite(tail_upper) && tail_lower<=tail_upper || return nothing
    # Subtract cost BEFORE collapsing high+tail to a large-scale dot interval.
    difference=_native_row_difference(high,tail_lower,tail_upper,cost)
    isnothing(difference) && return nothing
    difference_lower,difference_upper=difference
    isfinite(difference_lower) && isfinite(difference_upper) &&
        difference_lower<=difference_upper || return nothing
    # Difference is dot-cost; the certificate needs cost-dot.
    return -difference_upper,-difference_lower
end

@inline function _native_basic_intersection(coarse::Tuple{T,T},
                                            refined::Tuple{T,T}) where {T<:Union{Float32,Float64}}
    coarse_lower,coarse_upper=coarse
    refined_lower,refined_upper=refined
    isfinite(coarse_lower) && isfinite(coarse_upper) &&
        isfinite(refined_lower) && isfinite(refined_upper) || return nothing
    coarse_lower<=coarse_upper && refined_lower<=refined_upper || return nothing
    lower=max(coarse_lower,refined_lower)
    upper=min(coarse_upper,refined_upper)
    return lower<=upper ? (lower,upper) : nothing
end
