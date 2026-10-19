# Untimed source-inverse instrumentation; no timed factory uses these methods.
const _bgxsp_counts=Dict{String,Int}(k=>0 for k in ("allocation_requests","requested_payload","factorizations","extractions","orientation_solves","orientation_products","triangle_checks","permutation_checks","normalized_stores","raw_stores","fallback_stores","index_stores","refactor_entries"))
const _bgxsp_coexist_peak=Ref(0)
_bgxsp_count!(k,n=1)=(_bgxsp_counts[string(k)]+=n;nothing)
function _bgxsp_reset!()
    for k in keys(_bgxsp_counts);_bgxsp_counts[k]=0;end
    _bgxsp_coexist_peak[]=0;nothing
end
function _bgxsp_capture_build(inner,backend,parts,owner)
    _bgxsp_coexist_peak[]=max(_bgxsp_coexist_peak[],Base.summarysize((inner,backend,parts,owner)))
    inner
end
# UNEXECUTED separate candidate. Loaded only after the frozen direct-BG stage.
mutable struct BGSpecializedProbeExportWorkspace
    seen::Union{Nothing,BitVector}
    orientation::Union{Nothing,NTuple{4,Vector{Float64}}}
    dimension::Int
    charged_bytes::Int
end
_bgxsp_allocate(::Type{T},n::Int) where T = (_bgxsp_count!(:allocation_requests);_bgxsp_count!(:requested_payload,n*sizeof(T));Vector{T}(undef,n))
_bgxsp_allocate(::Type{Bool},n::Int) = (_bgxsp_count!(:allocation_requests);_bgxsp_count!(:requested_payload,8*cld(n,64));falses(n))
_bgxsp_drop!(owner) = (owner.workspace=nothing; nothing)
function _bgxsp_budget(n::Int,l::Int,u::Int)
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
function _bgxsp_charge(w::BGSpecializedProbeExportWorkspace)
    512+(isnothing(w.seen) ? 0 : 8*cld(w.dimension,64))+
        (isnothing(w.orientation) ? 0 : 32*w.dimension)
end
# Private cache invariants originate here. No arbitrary caller-owned buffers.
function _bgxsp_prepare!(owner,n::Int,b)
    w=owner.workspace
    if !b.keep_seen || (!isnothing(w) && w.dimension!=n)
        _bgxsp_drop!(owner);return nothing
    end
    if !isnothing(w) && !b.keep_orientation
        w.orientation=nothing
        if isnothing(w.seen)
            _bgxsp_drop!(owner);return nothing
        end
        w.charged_bytes=_bgxsp_charge(w)
    end
    return owner.workspace
end
@inline function _bgxsp_scratch!(owner,role::Symbol,n::Int,l::Int,u::Int;allocate=_bgxsp_allocate)
    _bgxsp_scratch_core!(owner,role,n,l,u,allocate)
end

function _bgxsp_scratch_core!(owner::O,role::Symbol,n::Int,l::Int,u::Int,allocate::A) where {O,A}
    role===:seen || throw(ArgumentError("Unsupported export scratch role"))
    try
        b=_bgxsp_budget(n,l,u);w=_bgxsp_prepare!(owner,n,b)
        !isnothing(w) && !isnothing(w.seen) && return w.seen
        seen=allocate(Bool,n)::BitVector
        if b.keep_seen
            if isnothing(w)
                w=BGSpecializedProbeExportWorkspace(seen,nothing,n,512+b.seen_bytes)
                owner.workspace=w
            else
                w.seen=seen;w.charged_bytes=_bgxsp_charge(w)
            end
        end
        return seen
    catch
        _bgxsp_drop!(owner);rethrow()
    end
end
