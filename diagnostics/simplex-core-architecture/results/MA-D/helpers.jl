# Private scalar scratch exists only during a single upper substitution.
function _markowitz_upper_solve!(work, upper, diagonal, sparse_pivots)
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / diagonal[pivot]
    end
    return work
end

_markowitz_ma_rounding_matches() =
    Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]

_markowitz_ma_scratch(::Type{T}) where {T} =
    (zero(T), MutableArithmetics.buffer_for(MutableArithmetics.sub_mul, T, T, T))

function _markowitz_ma_row_eligible(seed, row, work, diagonal, pivot)
    length(row.indices) >= 2 && length(row.indices) == length(row.values) || return false
    isfinite(seed) || return false
    checkbounds(Bool, diagonal, pivot) && isassigned(diagonal, pivot) || return false
    isfinite(diagonal[pivot]) || return false
    for i in eachindex(row.indices)
        isassigned(row.values, i) || return false
        source = row.indices[i]
        checkbounds(Bool, work, source) && isassigned(work, source) || return false
        isfinite(row.values[i]) && isfinite(work[source]) || return false
    end
    return true
end

function _markowitz_ma_upper_solve!(work::Vector{T}, upper::Vector{PackedFactorVector{T}},
                                    diagonal::Vector{T}, sparse_pivots::Int) where {T}
    scratch = nothing
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = upper[pivot]
        if _markowitz_ma_row_eligible(value, row, work, diagonal, pivot)
            if isnothing(scratch)
                scratch = _markowitz_ma_scratch(T)
            end
            acc, buffer = scratch
            # First subtraction reads the unrounded, borrowed seed directly.
            MutableArithmetics.buffered_operate_to!(buffer, acc,
                MutableArithmetics.sub_mul, value, row.values[1], work[row.indices[1]])
            for index in 2:length(row.indices)
                MutableArithmetics.buffered_operate!(buffer,
                    MutableArithmetics.sub_mul, acc, row.values[index], work[row.indices[index]])
            end
            value = acc
        else
            for index in eachindex(row.indices)
                value -= row.values[index] * work[row.indices[index]]
            end
        end
        # Ordinary division allocates the independently owned published scalar.
        work[pivot] = value / diagonal[pivot]
    end
    return work
end

function _markowitz_upper_solve!(work::Vector{BigFloat}, upper::Vector{PackedFactorVector{BigFloat}},
                                 diagonal::Vector{BigFloat}, sparse_pivots::Int)
    if !_markowitz_ma_rounding_matches()
        return invoke(_markowitz_upper_solve!, Tuple{Any,Any,Any,Any},
                      work, upper, diagonal, sparse_pivots)
    end
    return _markowitz_ma_upper_solve!(work, upper, diagonal, sparse_pivots)
end

function _markowitz_upper_solve!(work::Vector{Rational{BigInt}},
                                 upper::Vector{PackedFactorVector{Rational{BigInt}}},
                                 diagonal::Vector{Rational{BigInt}}, sparse_pivots::Int)
    return _markowitz_ma_upper_solve!(work, upper, diagonal, sparse_pivots)
end

