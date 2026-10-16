const _bg_probe_counts=zeros(Int,6) # ONLY separate untimed probe dispatch
# Diagnostic Task1 candidate, UNEXECUTED. No factor/solver methods or test helpers.
# Internal slot IDs must not escape the current primitive/update.
mutable struct ProbeBGSlotUpper
    value::Vector{Float64}
    row_id::Vector{Int}
    column_id::Vector{Int}
    row_prev::Vector{Int}
    row_next::Vector{Int}
    column_prev::Vector{Int}
    column_next::Vector{Int}
    row_order::Vector{Int}
    row_position::Vector{Int}
    column_order::Vector{Int}
    column_position::Vector{Int}
    row_head::Vector{Int}
    row_tail::Vector{Int}
    column_head::Vector{Int}
    column_tail::Vector{Int}
    n::Int
    capacity::Int
    live_count::Int
    free_head::Int
end

@inline function _probe_bg_ids(U::ProbeBGSlotUpper, rid::Int, cid::Int)
    1 <= rid <= U.n && 1 <= cid <= U.n || throw(ArgumentError("slot coordinates"))
    return nothing
end

@inline function _probe_bg_live(U::ProbeBGSlotUpper, s::Int)
    1 <= s <= U.capacity && U.row_id[s] != 0 || throw(ArgumentError("inactive slot"))
    return nothing
end

function _probe_bg_capacity(C::Int, required::Int)::Int
    C >= 0 && required >= 0 || throw(ArgumentError("negative capacity"))
    required <= C && return C
    grown = Base.Checked.checked_add(C, max(C ÷ 2, 16))
    result = max(required, grown)
    Base.Checked.checked_mul(result, sizeof(Int)) # reject impossible buffer bytes
    return result
end

_probe_bg_allocate(::Type{T}, n::Int) where {T} = Vector{T}(undef,n)

function _probe_bg_grown_buffer(old::Vector{T}, C::Int, allocate)::Vector{T} where {T}
    fresh = allocate(T,C)::Vector{T}
    length(fresh) == C || throw(ArgumentError("allocator length"))
    copyto!(fresh,1,old,1,length(old))
    for i in length(old)+1:C
        fresh[i]=zero(T)
    end
    return fresh
end

# Private call-local allocator seam for failure tests, never retained in U.
# The allocator contract is a fresh independent Vector of the requested type/size.
function _probe_bg_reserve_with!(U::ProbeBGSlotUpper, required::Int, allocate)::Nothing
    C = _probe_bg_capacity(U.capacity,required)
    _bg_probe_counts[1]+=1 # reserve attempts
    C == U.capacity && return nothing
    _bg_probe_counts[2]+=1 # growth attempts
    _bg_probe_counts[3]+=7*U.capacity # copied scalar entries
    _bg_probe_counts[4]=max(_bg_probe_counts[4],56*(U.capacity+C)) # old+new arena payload
    value = _probe_bg_grown_buffer(U.value,C,allocate)
    row_id = _probe_bg_grown_buffer(U.row_id,C,allocate)
    column_id = _probe_bg_grown_buffer(U.column_id,C,allocate)
    row_prev = _probe_bg_grown_buffer(U.row_prev,C,allocate)
    row_next = _probe_bg_grown_buffer(U.row_next,C,allocate)
    column_prev = _probe_bg_grown_buffer(U.column_prev,C,allocate)
    column_next = _probe_bg_grown_buffer(U.column_next,C,allocate)
    first_new = U.capacity + 1
    for s in first_new:C-1
        column_next[s] = s+1
    end
    column_next[C] = U.free_head
    # No allocation or throwing conversion after this publication point.
    U.value=value; U.row_id=row_id; U.column_id=column_id
    U.row_prev=row_prev; U.row_next=row_next
    U.column_prev=column_prev; U.column_next=column_next
    U.capacity=C; U.free_head=first_new
    return nothing
end

_probe_bg_reserve!(U::ProbeBGSlotUpper, required::Int)::Nothing =
    _probe_bg_reserve_with!(U,required,_probe_bg_allocate)

function _probe_bg_slots(A::SparseMatrixCSC{Float64,Int}, q::Vector{Int})::ProbeBGSlotUpper
    n = size(A,1)
    size(A,2) == n && length(q) == n || throw(ArgumentError("square U and matching q required"))
    positions = zeros(Int,n)
    for j in 1:n
        cid=q[j]
        1 <= cid <= n || throw(ArgumentError("q range"))
        positions[cid] == 0 || throw(ArgumentError("q duplicate"))
        positions[cid]=j
    end
    m = length(A.nzval)
    length(A.rowval) == m && length(A.colptr) == n+1 || throw(ArgumentError("CSC lengths"))
    A.colptr[1] == 1 && A.colptr[end] == Base.Checked.checked_add(m,1) ||
        throw(ArgumentError("CSC endpoints"))
    for j in 1:n
        lo, hi = A.colptr[j], A.colptr[j+1]
        1 <= lo <= hi <= m+1 || throw(ArgumentError("CSC pointers"))
        prev=0
        for k in lo:hi-1
            r=A.rowval[k]
            prev < r <= n || throw(ArgumentError("CSC rows must be unique and ordered"))
            prev=r
        end
    end
    C = n == 0 ? 0 : max(m,16)
    Base.Checked.checked_mul(C,sizeof(Int))
    U=ProbeBGSlotUpper(zeros(Float64,C),zeros(Int,C),zeros(Int,C),zeros(Int,C),
                  zeros(Int,C),zeros(Int,C),zeros(Int,C),collect(1:n),collect(1:n),
                  copy(q),positions,zeros(Int,n),zeros(Int,n),zeros(Int,n),zeros(Int,n),
                  n,C,0,C==0 ? 0 : 1)
    for s in 1:C-1
        U.column_next[s]=s+1
    end
    # q-aware import: original basis IDs, NOT logical CSC column order.
    for cid in 1:n
        j=positions[cid]
        for k in A.colptr[j]:A.colptr[j+1]-1
            rid=A.rowval[k]
            _probe_bg_link!(U,rid,cid,A.nzval[k],U.row_tail[rid],0,U.column_tail[cid],0)
        end
    end
    return U
end

function _probe_bg_lookup(U::ProbeBGSlotUpper, rid::Int, cid::Int)::Int
    _probe_bg_ids(U,rid,cid)
    s=U.row_head[rid]
    while s != 0 && U.column_id[s] < cid
        s=U.row_next[s]
    end
    return s != 0 && U.column_id[s] == cid ? s : 0
end

# Supplied gaps are checked in O(1), without a redundant row/column scan.
function _probe_bg_row_gap(U::ProbeBGSlotUpper,rid::Int,cid::Int,p::Int,t::Int)::Nothing
    if p == 0
        U.row_head[rid] == t || throw(ArgumentError("row head gap"))
    else
        _probe_bg_live(U,p)
        U.row_id[p] == rid && U.column_id[p] < cid && U.row_next[p] == t ||
            throw(ArgumentError("row predecessor gap"))
    end
    if t == 0
        U.row_tail[rid] == p || throw(ArgumentError("row tail gap"))
    else
        _probe_bg_live(U,t)
        U.row_id[t] == rid && cid < U.column_id[t] && U.row_prev[t] == p ||
            throw(ArgumentError("row successor gap"))
    end
    return nothing
end

function _probe_bg_column_gap(U::ProbeBGSlotUpper,rid::Int,cid::Int,p::Int,t::Int)::Nothing
    pos=U.row_position[rid]
    if p == 0
        U.column_head[cid] == t || throw(ArgumentError("column head gap"))
    else
        _probe_bg_live(U,p)
        U.column_id[p] == cid && U.row_position[U.row_id[p]] < pos && U.column_next[p] == t ||
            throw(ArgumentError("column predecessor gap"))
    end
    if t == 0
        U.column_tail[cid] == p || throw(ArgumentError("column tail gap"))
    else
        _probe_bg_live(U,t)
        U.column_id[t] == cid && pos < U.row_position[U.row_id[t]] && U.column_prev[t] == p ||
            throw(ArgumentError("column successor gap"))
    end
    return nothing
end

function _probe_bg_link!(U::ProbeBGSlotUpper,rid::Int,cid::Int,value::Float64,
                   rp::Int,rn::Int,cp::Int,cn::Int)::Int
    _bg_probe_counts[5]+=1 # link attempts
    _probe_bg_ids(U,rid,cid)
    _probe_bg_row_gap(U,rid,cid,rp,rn); _probe_bg_column_gap(U,rid,cid,cp,cn)
    count=Base.Checked.checked_add(U.live_count,1)
    _probe_bg_reserve!(U,count)
    s=U.free_head
    U.free_head=U.column_next[s]
    U.value[s]=value; U.row_id[s]=rid; U.column_id[s]=cid
    U.row_prev[s]=rp; U.row_next[s]=rn; U.column_prev[s]=cp; U.column_next[s]=cn
    if rp==0; U.row_head[rid]=s; else; U.row_next[rp]=s; end
    if rn==0; U.row_tail[rid]=s; else; U.row_prev[rn]=s; end
    if cp==0; U.column_head[cid]=s; else; U.column_next[cp]=s; end
    if cn==0; U.column_tail[cid]=s; else; U.column_prev[cn]=s; end
    U.live_count=count
    return s
end

function _probe_bg_unlink!(U::ProbeBGSlotUpper,s::Int)::Nothing
    _bg_probe_counts[6]+=1 # unlink attempts
    _probe_bg_live(U,s)
    rid,cid=U.row_id[s],U.column_id[s]
    rp,rn,cp,cn=U.row_prev[s],U.row_next[s],U.column_prev[s],U.column_next[s]
    if rp==0; U.row_head[rid]=rn; else; U.row_next[rp]=rn; end
    if rn==0; U.row_tail[rid]=rp; else; U.row_prev[rn]=rp; end
    if cp==0; U.column_head[cid]=cn; else; U.column_next[cp]=cn; end
    if cn==0; U.column_tail[cid]=cp; else; U.column_prev[cn]=cp; end
    U.value[s]=0.0; U.row_id[s]=0; U.column_id[s]=0
    U.row_prev[s]=0; U.row_next[s]=0; U.column_prev[s]=0
    U.column_next[s]=U.free_head; U.free_head=s; U.live_count-=1
    return nothing
end

function _probe_bg_set_at!(U::ProbeBGSlotUpper,s::Int,value::Float64)::Nothing
    _probe_bg_live(U,s)
    if iszero(value)
        _probe_bg_unlink!(U,s)
    else
        U.value[s]=value
    end
    return nothing
end

function _probe_bg_swap_rows!(U::ProbeBGSlotUpper,j::Int)::Nothing
    1 <= j < U.n || throw(ArgumentError("adjacent row range"))
    ra,rb=U.row_order[j],U.row_order[j+1]
    a,b=U.row_head[ra],U.row_head[rb]
    while a != 0 && b != 0
        ca,cb=U.column_id[a],U.column_id[b]
        if ca < cb
            a=U.row_next[a]
        elseif cb < ca
            b=U.row_next[b]
        else
            # In a valid arena adjacent logical rows are adjacent column nodes.
            p,t=U.column_prev[a],U.column_next[b]
            if p==0; U.column_head[ca]=b; else; U.column_next[p]=b; end
            if t==0; U.column_tail[ca]=a; else; U.column_prev[t]=a; end
            U.column_prev[b]=p; U.column_next[b]=a
            U.column_prev[a]=b; U.column_next[a]=t
            a,b=U.row_next[a],U.row_next[b]
        end
    end
    U.row_order[j]=rb; U.row_order[j+1]=ra
    U.row_position[ra]=j+1; U.row_position[rb]=j
    return nothing
end

function _probe_bg_rotate_rows!(U::ProbeBGSlotUpper,first::Int,last::Int)::Nothing
    1 <= first <= last <= U.n || throw(ArgumentError("rotation range"))
    first == last && return nothing
    rid=U.row_order[first]; s=U.row_head[rid]
    while s != 0
        p=s; t=U.column_next[s]
        while t != 0 && U.row_position[U.row_id[t]] <= last
            p=t; t=U.column_next[t]
        end
        if p != s
            cid=U.column_id[s]; before=U.column_prev[s]; after=U.column_next[s]
            if before==0; U.column_head[cid]=after; else; U.column_next[before]=after; end
            U.column_prev[after]=before # p!=s proves after!=0
            U.column_next[p]=s; U.column_prev[s]=p; U.column_next[s]=t
            if t==0; U.column_tail[cid]=s; else; U.column_prev[t]=s; end
        end
        s=U.row_next[s]
    end
    for j in first:last-1
        moved=U.row_order[j+1]
        U.row_order[j]=moved; U.row_position[moved]=j
    end
    U.row_order[last]=rid; U.row_position[rid]=last
    return nothing
end
