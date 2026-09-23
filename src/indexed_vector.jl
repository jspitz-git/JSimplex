"""Owned dense values with a generation-stamped, possibly uncompressed support.

Only exact zeros are omitted. Cancellation may leave a zero index until
`compact_support!`; reinsertion before compaction does not duplicate it.
`dense_values` borrows the values for reading. Use mutation helpers to keep
support coherent; concurrent computations need separate indexed vectors.
"""
mutable struct IndexedVector{T<:Real}
    values::Vector{T}
    indices::Vector{Int}
    membership::Vector{UInt}
    generation::UInt
end

function IndexedVector{T}(n::Integer) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("Unsupported indexed value type $T"))
    n >= 0 || throw(ArgumentError("Negative indexed-vector dimension"))
    return IndexedVector(zeros(T,n),Int[],zeros(UInt,n),UInt(1))
end

dense_values(v::IndexedVector) = v.values
Base.copy(v::IndexedVector) =
    IndexedVector(copy(v.values),copy(v.indices),copy(v.membership),v.generation)

function clear!(v::IndexedVector{T}) where T
    for i in v.indices
        v.values[i] = zero(T)
    end
    empty!(v.indices)
    if v.generation == typemax(UInt)
        fill!(v.membership,UInt(0))
        v.generation = UInt(1)
    else
        v.generation += UInt(1)
    end
    return v
end

function compact_support!(v::IndexedVector)
    kept = 0
    for i in v.indices
        if iszero(v.values[i])
            v.membership[i] = UInt(0)
        else
            kept += 1
            v.indices[kept] = i
        end
    end
    resize!(v.indices,kept)
    return v
end

function set_entry!(v::IndexedVector{T},i::Integer,value) where T
    checkbounds(v.values,i)
    stored = convert(T,value)
    isfinite(stored) || throw(ArgumentError("Indexed entries must be finite"))
    # Publish membership only after conversion succeeds. Normalize zero signs.
    if !iszero(stored) && v.membership[i] != v.generation
        push!(v.indices,Int(i))
        v.membership[i] = v.generation
    end
    v.values[i] = iszero(stored) ? zero(T) : stored
    return v
end

_indexed_sum(a,b) = a+b
_indexed_sum(a::BigFloat,b::BigFloat) =
    setprecision(()->a+b,BigFloat,max(precision(BigFloat),precision(a),precision(b)))

function add_entry!(v::IndexedVector{T},i::Integer,value) where T
    checkbounds(v.values,i)
    converted = convert(T,value)
    isfinite(converted) || throw(ArgumentError("Indexed contributions must be finite"))
    result = _indexed_sum(v.values[i],converted)
    isfinite(result) || throw(OverflowError("Indexed addition overflowed"))
    return set_entry!(v,i,result)
end

"""Replace values and rebuild support; the source must not alias owned storage.

A conversion failure can leave a partial result, whose support remains valid.
"""
function load_indexed!(v::IndexedVector,values::AbstractVector)
    length(v.values) == length(values) || throw(DimensionMismatch("Indexed-vector dimensions"))
    Base.mightalias(v.values,values) && throw(ArgumentError("Indexed input aliases owned storage"))
    clear!(v)
    for i in eachindex(values)
        set_entry!(v,i,values[i])
    end
    return v
end
