# Reuse R * B0^-1 * a from an unmodified dense FTRAN. Reconstructing that
# vector as U * Q^-1 * direction would traverse the whole growing upper factor
# and introduce another rounding step. Corrected or external directions retain
# the reconstruction path. Arbitrary-precision and exact types are unchanged.
_begin_prepared_spike!(factor, destination) = nothing
_save_prepared_spike!(::Nothing, destination) = nothing
_finish_prepared_spike!(::Nothing, destination) = nothing
_copy_prepared_spike!(factor, direction) = false
_invalidate_prepared_destination!(factor, destination) = nothing

Base.@noinline function _begin_prepared_spike!(factor::AbstractTriangularBasisFactorization{T},
                                 destination::Vector{T}) where {T<:Union{Float32,Float64}}
    Base.mightalias(destination, factor.spike) && return nothing
    sparse = factor.sparse
    if !isnothing(sparse) && (Base.mightalias(destination, sparse.dense) ||
            Base.mightalias(destination, sparse.dense_result) ||
            Base.mightalias(destination, sparse.work.values) ||
            Base.mightalias(destination, sparse.scratch.values))
        return nothing
    end
    cache = factor.row_cache.prepared
    if isnothing(cache)
        entries = ntuple(_ -> PreparedTriangularSpike{T}(nothing, T[], T[]), 2)
        cache = TriangularSpikeCache{T}(entries, 1)
        factor.row_cache.prepared = cache
    end
    # Invalidate previous output from this same buffer before a solve can
    # overwrite it or fail partway through. Other RHS buffers remain usable.
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination, destination)
            entry.destination = nothing
        end
        # Both slots share the current basis dimension; establish their buffers
        # together so the next ordinary solve can immediately reuse either one.
        resize!(entry.direction, length(destination))
        resize!(entry.spike, length(destination))
    end
    entry = cache.entries[cache.next]
    cache.next = 3 - cache.next
    entry.destination = nothing
    return entry
end

function _save_prepared_spike!(entry::PreparedTriangularSpike, destination)
    copyto!(resize!(entry.spike, length(destination)), destination)
    return nothing
end

Base.@noinline function _finish_prepared_spike!(entry::PreparedTriangularSpike, destination)
    # Do not change the propagation of exceptional input through reconstruction.
    all(isfinite, destination) && all(isfinite, entry.spike) || return nothing
    copyto!(resize!(entry.direction, length(destination)), destination)
    entry.destination = destination
    return nothing
end

# The pending entry is unpublished, so a failed finite check may overwrite its
# private numeric buffer. Publish only after checking both input vectors.
Base.@noinline function _finish_prepared_spike!(entry::PreparedTriangularSpike{T},
                                               destination::Vector{T}) where {T<:Union{Float32,Float64}}
    if !isnothing(entry.destination) || length(entry.spike) != length(destination) ||
            Base.mightalias(entry.direction, destination) ||
            Base.mightalias(entry.direction, entry.spike)
        return invoke(_finish_prepared_spike!, Tuple{PreparedTriangularSpike,Any}, entry, destination)
    end
    direction = resize!(entry.direction, length(destination))
    finite = true
    @inbounds @simd for index in eachindex(destination, entry.spike, direction)
        value = destination[index]
        finite &= isfinite(value) & isfinite(entry.spike[index])
        direction[index] = value
    end
    finite && (entry.destination = destination)
    return nothing
end

Base.@noinline function _copy_prepared_spike!(factor::AbstractTriangularBasisFactorization{T},
                                direction::Vector{T}) where {T<:Union{Float32,Float64}}
    cache = factor.row_cache.prepared
    isnothing(cache) && return false
    for entry in cache.entries
        # Identity prevents another equal-valued RHS buffer from selecting an
        # unrelated solve. Exact value comparison detects in-place corrections,
        # including changes to signed zeros.
        if entry.destination === direction && isequal(entry.direction, direction)
            copyto!(factor.spike, entry.spike)
            return true
        end
    end
    return false
end

function _invalidate_prepared_spikes!(factor::AbstractTriangularBasisFactorization)
    cache = factor.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        entry.destination = nothing
    end
    return nothing
end

# A different solve operation can produce the same rounded values. Invalidate
# provenance before BTRAN or an indexed solve overwrites the output buffer.
function _invalidate_prepared_destination!(factor::AbstractTriangularBasisFactorization,
                                            destination)
    cache = factor.row_cache.prepared
    isnothing(cache) && return nothing
    for entry in cache.entries
        if !isnothing(entry.destination) && Base.mightalias(entry.destination, destination)
            entry.destination = nothing
        end
    end
    return nothing
end

_save_prepared_spike!(::Nothing, source, order) = nothing
function _save_prepared_spike!(entry::PreparedTriangularSpike, source, order)
    resize!(entry.spike, length(source))
    for row in eachindex(source)
        entry.spike[row] = source[order.order[row]]
    end
    return nothing
end
