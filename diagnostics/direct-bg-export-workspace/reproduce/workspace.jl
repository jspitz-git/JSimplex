# UNEXECUTED separate candidate. Loaded only after the frozen direct-BG stage.
mutable struct BGExportWorkspace
    seen::Union{Nothing,BitVector}
    orientation::Union{Nothing,NTuple{4,Vector{Float64}}}
    dimension::Int
    charged_bytes::Int
end
_bgx_allocate(::Type{T},n::Int) where T = Vector{T}(undef,n)
_bgx_allocate(::Type{Bool},n::Int) = falses(n)
_bgx_drop!(owner) = (owner.workspace=nothing; nothing)
function _bgx_budget(n::Int,l::Int,u::Int)
    n>=0 && l>=0 && u>=0 || throw(ArgumentError("Negative export size"))
    add=Base.Checked.checked_add;mul=Base.Checked.checked_mul
    payload=add(mul(16,add(l,u)),mul(8,add(n,1)))
    # Avoid n+63 overflow: quotient plus remainder accounts for bit chunks.
    seen_bytes=mul(8,add(div(n,64),Int(rem(n,64)!=0)))
    orientation_bytes=mul(32,n)
    limit=min(1048576,fld(payload,16))
    seen_charge=add(512,seen_bytes)
    full_charge=add(seen_charge,orientation_bytes)
    keep_seen=n>0 && seen_charge<=limit
    return (;limit,seen_bytes,orientation_bytes,keep_seen,
             keep_orientation=keep_seen && full_charge<=limit)
end
function _bgx_charge(w::BGExportWorkspace)
    512+(isnothing(w.seen) ? 0 : 8*cld(w.dimension,64))+
        (isnothing(w.orientation) ? 0 : 32*w.dimension)
end
# Private cache invariants originate here. No arbitrary caller-owned buffers.
function _bgx_prepare!(owner,n::Int,b)
    w=owner.workspace
    if !b.keep_seen || (!isnothing(w) && w.dimension!=n)
        _bgx_drop!(owner);return nothing
    end
    if !isnothing(w) && !b.keep_orientation
        w.orientation=nothing
        if isnothing(w.seen)
            _bgx_drop!(owner);return nothing
        end
        w.charged_bytes=_bgx_charge(w)
    end
    return owner.workspace
end
function _bgx_scratch!(owner,role::Symbol,n::Int,l::Int,u::Int;allocate=_bgx_allocate)
    role===:seen || throw(ArgumentError("Unsupported export scratch role"))
    try
        b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)
        !isnothing(w) && !isnothing(w.seen) && return w.seen
        seen=allocate(Bool,n)::BitVector
        if b.keep_seen
            if isnothing(w)
                w=BGExportWorkspace(seen,nothing,n,512+b.seen_bytes)
                owner.workspace=w
            else
                w.seen=seen;w.charged_bytes=_bgx_charge(w)
            end
        end
        return seen
    catch
        _bgx_drop!(owner);rethrow()
    end
end
