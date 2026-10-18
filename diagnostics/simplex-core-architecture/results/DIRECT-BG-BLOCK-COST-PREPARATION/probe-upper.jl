const _block_probe_counts=Dict{Symbol,Int}(:allocation_requests=>0,:requested_payload_bytes=>0,:tuple_writes=>0,:row_handle_repairs=>0,:back_repairs=>0,:gap_moves=>0,:row_growths=>0,:row_copied_bytes=>0,:row_coexist_payload=>0,:grown_copied_bytes=>0,:descriptor_growths=>0,:descriptor_coexist_payload=>0,:slab_appends=>0,:directory_growths=>0,:directory_copied_bytes=>0,:directory_coexist_payload=>0,:merge_stage_reads=>0,:merge_stage_writes=>0,:merges=>0,:merge_tuple_moves=>0,:delete_tuple_moves=>0,:extent_tuple_moves=>0,:splits=>0,:split_stage_reads=>0,:split_stage_writes=>0,:split_final_writes=>0,:insert_tuple_moves=>0,:swap_tuple_moves=>0,:rotation_tuple_moves=>0)
_block_count!(k,n)=(_block_probe_counts[k]+=n;nothing)
_block_max!(k,n)=(_block_probe_counts[k]=max(_block_probe_counts[k],n);nothing)
# Task1 private candidate. UNEXECUTED. No solver methods, global overrides or runtime imports.
mutable struct ProbeBGBlockUpper
    values::Vector{Vector{Float64}}
    row_ids::Vector{Vector{Int32}}
    row_backs::Vector{Vector{Int32}}
    slab::Vector{Int32}
    start::Vector{Int32}
    capacity::Vector{Int32}
    count::Vector{Int32}
    column::Vector{Int32}
    prev::Vector{Int32}
    next::Vector{Int32}
    row_order::Vector{Int32}
    row_position::Vector{Int32}
    column_order::Vector{Int32}
    column_position::Vector{Int32}
    column_head::Vector{Int32}
    column_tail::Vector{Int32}
    rows::Vector{Vector{Int32}}
    gap_first::Vector{Int32}
    gap_length::Vector{Int32}
    bins::Vector{Int32}
    scratch_value::Vector{Float64}
    scratch_row::Vector{Int32}
    scratch_back::Vector{Int32}
    n::Int
    live::Int
    used::Int
    slabs::Int
end

_probe_bgu_allocate(::Type{T},n::Int) where {T}=(_block_count!(:allocation_requests,1);_block_count!(:requested_payload_bytes,n*Base.elsize(Vector{T}));Vector{T}(undef,n))
function _probe_bgu_zeros(::Type{T},n::Int,allocate) where {T}
    a=allocate(T,n)::Vector{T}
    length(a)==n || throw(ArgumentError("allocator length"))
    fill!(a,zero(T)); return a
end
function _probe_bgu_limit(x::Int,limit::Integer)
    0<=x<=limit<=typemax(Int32) || throw(OverflowError("block U index capacity"))
    return x
end
function _probe_bgu_handle(b::Int,k::Int,limit::Integer=typemax(Int32))::Int32
    b>0 && 1<=k<=32 || throw(OverflowError("block U handle coordinate"))
    _probe_bgu_limit(Base.Checked.checked_mul(b,32),limit)
    return Int32((b-1)*32+k)
end
@inline _probe_bgu_decode(h::Int32)=(Int(h-1)÷32+1,Int(h-1)%32+1)
function _probe_bgu_row_capacity(old::Int,required::Int,limit::Integer)
    new=Base.Checked.checked_add(required,min(8,max(1,old÷8)))
    _probe_bgu_limit(Base.Checked.checked_add(new,1),limit)
    return new
end
function _probe_bgu_descriptor_capacity(old::Int,required::Int,limit::Integer)
    required<=old && return old
    new=max(required,Base.Checked.checked_add(old,max(old÷2,8)))
    _probe_bgu_limit(Base.Checked.checked_mul(new,32),limit)
    return new
end
_probe_bgu_buffer(::Type{T},n::Int,allocate,clear::Bool) where {T}=clear ? _probe_bgu_zeros(T,n,allocate) : allocate(T,n)::Vector{T}
function _probe_bgu_new(n::Int,K::Int,D::Int,allocate,clear::Bool=true)
    # Outer directories may contain unassigned spare entries; only1:slabs is live.
    return ProbeBGBlockUpper(allocate(Vector{Float64},D),allocate(Vector{Int32},D),allocate(Vector{Int32},D),
        _probe_bgu_buffer(Int32,K,allocate,clear),_probe_bgu_buffer(Int32,K,allocate,clear),_probe_bgu_buffer(Int32,K,allocate,clear),
        _probe_bgu_buffer(Int32,K,allocate,clear),_probe_bgu_buffer(Int32,K,allocate,clear),_probe_bgu_buffer(Int32,K,allocate,clear),_probe_bgu_buffer(Int32,K,allocate,clear),
        _probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,n,allocate,clear),
        _probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,n,allocate,clear),allocate(Vector{Int32},n),
        _probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,n,allocate,clear),_probe_bgu_buffer(Int32,32,allocate,clear),
        _probe_bgu_buffer(Float64,33,allocate,clear),_probe_bgu_buffer(Int32,33,allocate,clear),_probe_bgu_buffer(Int32,33,allocate,clear),n,0,0,0)
end
@inline function _probe_bgu_tuple(U,h::Int32)
    b,k=_probe_bgu_decode(h);s=Int(U.slab[b]);p=Int(U.start[b])+k-1
    return U.values[s][p],U.row_ids[s][p],U.row_backs[s][p]
end
@inline function _probe_bgu_write!(U,b::Int,k::Int,v::Float64,r::Int32,p::Int32)
    s=Int(U.slab[b]);i=Int(U.start[b])+k-1
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:tuple_writes,1);_block_count!(:row_handle_repairs,1)
    # BLOCK_COST_PROBE_END

    U.values[s][i]=v;U.row_ids[s][i]=r;U.row_backs[s][i]=p
    U.rows[Int(r)][Int(p)]=Int32((b-1)*32+k)
    return nothing
end
@inline function _probe_bgu_back!(U,h::Int32,p::Int)
    b,k=_probe_bgu_decode(h);U.row_backs[Int(U.slab[b])][Int(U.start[b])+k-1]=Int32(p)
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:back_repairs,1)
    # BLOCK_COST_PROBE_END

end
@inline function _probe_bgu_clear!(U,b::Int,k::Int)
    s=Int(U.slab[b]);p=Int(U.start[b])+k-1
    U.values[s][p]=0.0;U.row_ids[s][p]=0;U.row_backs[s][p]=0
end
@inline _probe_bgu_degree(U,r::Int)=length(U.rows[r])-Int(U.gap_length[r])
@inline _probe_bgu_row_offset(U,r::Int,k::Int)=k<Int(U.gap_first[r]) ? k : k+Int(U.gap_length[r])
@inline _probe_bgu_row_handle(U,r::Int,k::Int)=U.rows[r][_probe_bgu_row_offset(U,r,k)]
@inline function _probe_bgu_cid(U,h::Int32)
    b,_=_probe_bgu_decode(h);return Int(U.column[b])
end
function _probe_bgu_coordinates(U,r::Int,c::Int)
    1<=r<=U.n && 1<=c<=U.n || throw(ArgumentError("block U coordinates"))
end
function _probe_bgu_row_search(U,r::Int,c::Int)
    k=1;d=_probe_bgu_degree(U,r)
    while k<=d
        h=_probe_bgu_row_handle(U,r,k);cid=_probe_bgu_cid(U,h)
        cid>=c && return k,(cid==c ? h : Int32(0))
        k+=1
    end
    return k,Int32(0)
end
function _probe_bgu_find(U::ProbeBGBlockUpper,rid::Int,cid::Int)::Int32
    _probe_bgu_coordinates(U,rid,cid);return _probe_bgu_row_search(U,rid,cid)[2]
end
function _probe_bgu_gap!(U,r::Int,target::Int)
    a=U.rows[r];g=Int(U.gap_first[r]);l=Int(U.gap_length[r])
    if l==0;U.gap_first[r]=Int32(target);return nothing;end
    while g>target
        h=a[g-1];a[g+l-1]=h;a[g-1]=0;_probe_bgu_back!(U,h,g+l-1);g-=1
    # BLOCK_COST_PROBE_BEGIN
        _block_count!(:gap_moves,1)
    # BLOCK_COST_PROBE_END

    end
    while g<target
        h=a[g+l];a[g]=h;a[g+l]=0;_probe_bgu_back!(U,h,g);g+=1
    # BLOCK_COST_PROBE_BEGIN
        _block_count!(:gap_moves,1)
    # BLOCK_COST_PROBE_END

    end
    U.gap_first[r]=Int32(g);return nothing
end
function _probe_bgu_reserve_row!(U,r::Int,rank::Int,allocate,limit::Integer)
    Int(U.gap_length[r])>0 && return nothing
    d=_probe_bgu_degree(U,r);C=_probe_bgu_row_capacity(length(U.rows[r]),d+1,limit)
    a=allocate(Int32,C)::Vector{Int32};length(a)==C || throw(ArgumentError("allocator length"));gap=C-d
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:row_growths,1);_block_count!(:row_copied_bytes,4*d)
    _block_max!(:row_coexist_payload,4*(length(U.rows[r])+C))
    # BLOCK_COST_PROBE_END

    for p in rank:rank+gap-1;a[p]=0;end
    for k in 1:d
        p=k<rank ? k : k+gap;a[p]=_probe_bgu_row_handle(U,r,k)
    end
    # Allocation succeeded: publish owned reserve, then repair reciprocal positions.
    U.rows[r]=a;U.gap_first[r]=Int32(rank);U.gap_length[r]=Int32(gap)
    for k in rank:d
        p=k+gap;_probe_bgu_back!(U,a[p],p)
    end
    return nothing
end
function _probe_bgu_grown(old::Vector{T},C::Int,allocate) where {T}
    a=allocate(T,C)::Vector{T};length(a)==C || throw(ArgumentError("allocator length"))
    copyto!(a,1,old,1,length(old))
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:grown_copied_bytes,sizeof(T)*length(old))
    # BLOCK_COST_PROBE_END

    for k in length(old)+1:C;a[k]=zero(T);end
    return a
end
function _probe_bgu_reserve_descriptors!(U,required::Int,allocate,limit::Integer)
    C=_probe_bgu_descriptor_capacity(length(U.slab),required,limit)
    C==length(U.slab) && return nothing
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:descriptor_growths,1);_block_max!(:descriptor_coexist_payload,28*(length(U.slab)+C))
    # BLOCK_COST_PROBE_END

    a=_probe_bgu_grown(U.slab,C,allocate);b=_probe_bgu_grown(U.start,C,allocate);c=_probe_bgu_grown(U.capacity,C,allocate)
    d=_probe_bgu_grown(U.count,C,allocate);e=_probe_bgu_grown(U.column,C,allocate)
    f=_probe_bgu_grown(U.prev,C,allocate);g=_probe_bgu_grown(U.next,C,allocate)
    U.slab=a;U.start=b;U.capacity=c;U.count=d;U.column=e;U.prev=f;U.next=g
    return nothing
end
function _probe_bgu_free!(U,b::Int)
    cap=Int(U.capacity[b]);h=Int(U.bins[cap])
    U.count[b]=0;U.column[b]=0;U.prev[b]=0;U.next[b]=Int32(h)
    h!=0 && (U.prev[h]=Int32(b));U.bins[cap]=Int32(b)
    return nothing
end
function _probe_bgu_take!(U,b::Int)
    cap=Int(U.capacity[b]);p=Int(U.prev[b]);n=Int(U.next[b])
    if p==0;U.bins[cap]=Int32(n);else;U.next[p]=Int32(n);end
    n!=0 && (U.prev[n]=Int32(p));U.prev[b]=0;U.next[b]=0
    return b
end
function _probe_bgu_free_block(U,required::Int)
    for c in required:32
        U.bins[c]!=0 && return Int(U.bins[c])
    end
    return 0
end
function _probe_bgu_append_slab!(U,allocate,limit::Integer)
    used=Base.Checked.checked_add(U.used,8);ns=Base.Checked.checked_add(U.slabs,1)
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:slab_appends,1)
    # BLOCK_COST_PROBE_END

    _probe_bgu_limit(ns,limit);_probe_bgu_limit(256,limit)
    _probe_bgu_reserve_descriptors!(U,used,allocate,limit)
    # Every following allocation remains private until all succeed.
    v=_probe_bgu_zeros(Float64,256,allocate);r=_probe_bgu_zeros(Int32,256,allocate);p=_probe_bgu_zeros(Int32,256,allocate)
    D=length(U.values)
    if ns>D
        D=max(ns,Base.Checked.checked_add(D,max(D÷2,1)));_probe_bgu_limit(D,limit)
        av=allocate(Vector{Float64},D);ar=allocate(Vector{Int32},D);ap=allocate(Vector{Int32},D)
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:directory_growths,1);_block_count!(:directory_copied_bytes,24*U.slabs)
    _block_max!(:directory_coexist_payload,24*(length(U.values)+D))
    # BLOCK_COST_PROBE_END

        for i in 1:U.slabs;av[i]=U.values[i];ar[i]=U.row_ids[i];ap[i]=U.row_backs[i];end
        av[ns]=v;ar[ns]=r;ap[ns]=p;U.values=av;U.row_ids=ar;U.row_backs=ap
    else
        U.values[ns]=v;U.row_ids[ns]=r;U.row_backs[ns]=p
    end
    for i in 1:8
        b=U.used+i;U.slab[b]=Int32(ns);U.start[b]=Int32(32*(i-1)+1);U.capacity[b]=32
        _probe_bgu_free!(U,b)
    end
    U.used=used;U.slabs=ns;return nothing
end
function _probe_bgu_reserve_block!(U,required::Int,allocate,limit::Integer)
    b=_probe_bgu_free_block(U,required)
    if b==0;_probe_bgu_append_slab!(U,allocate,limit);b=Int(U.bins[32]);end
    return b # Still on free list: no reservation is consumed before commit.
end
function _probe_bgu_link_block!(U,b::Int,c::Int,p::Int,n::Int)
    U.column[b]=Int32(c);U.prev[b]=Int32(p);U.next[b]=Int32(n)
    if p==0;U.column_head[c]=Int32(b);else;U.next[p]=Int32(b);end
    if n==0;U.column_tail[c]=Int32(b);else;U.prev[n]=Int32(b);end
end
function _probe_bgu_unlink_block!(U,b::Int)
    c=Int(U.column[b]);p=Int(U.prev[b]);n=Int(U.next[b])
    if p==0;U.column_head[c]=Int32(n);else;U.next[p]=Int32(n);end
    if n==0;U.column_tail[c]=Int32(p);else;U.prev[n]=Int32(p);end
    _probe_bgu_free!(U,b);return nothing
end
function _probe_bgu_stage!(U,b::Int,offset::Int=0)
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:merge_stage_reads,Int(U.count[b]));_block_count!(:merge_stage_writes,Int(U.count[b]))
    # BLOCK_COST_PROBE_END

    for k in 1:Int(U.count[b])
        v,r,p=_probe_bgu_tuple(U,Int32((b-1)*32+k))
        U.scratch_value[offset+k]=v;U.scratch_row[offset+k]=r;U.scratch_back[offset+k]=p
    end
end
function _probe_bgu_from_stage!(U,b::Int,offset::Int,n::Int)
    for k in 1:n
        _probe_bgu_write!(U,b,k,U.scratch_value[offset+k],U.scratch_row[offset+k],U.scratch_back[offset+k])
    end
    for k in n+1:Int(U.capacity[b]);_probe_bgu_clear!(U,b,k);end
    U.count[b]=Int32(n)
end
function _probe_bgu_merge_next!(U,b::Int)
    n=Int(U.next[b]);n==0 && return nothing
    total=Int(U.count[b])+Int(U.count[n]);total>max(U.capacity[b],U.capacity[n]) && return nothing
    left=Int(U.count[b]);_probe_bgu_stage!(U,b);_probe_bgu_stage!(U,n,left)
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:merges,1);_block_count!(:merge_tuple_moves,total)
    # BLOCK_COST_PROBE_END

    before=Int(U.prev[b]);after=Int(U.next[n]);c=Int(U.column[b])
    keep=U.capacity[b]>=U.capacity[n] ? b : n;drop=keep==b ? n : b
    _probe_bgu_link_block!(U,keep,c,before,after);_probe_bgu_from_stage!(U,keep,0,total)
    for k in 1:Int(U.capacity[drop]);_probe_bgu_clear!(U,drop,k);end
    _probe_bgu_free!(U,drop);return nothing
end
function _probe_bgu_delete!(U,r::Int,rank::Int,h::Int32)
    b,k=_probe_bgu_decode(h);cnt=Int(U.count[b]);_probe_bgu_gap!(U,r,rank)
    g=Int(U.gap_first[r]);l=Int(U.gap_length[r]);U.rows[r][g+l]=0;U.gap_length[r]=Int32(l+1)
    for i in k:cnt-1
    # BLOCK_COST_PROBE_BEGIN
        _block_count!(:delete_tuple_moves,1)
    # BLOCK_COST_PROBE_END

        v,rid,p=_probe_bgu_tuple(U,Int32((b-1)*32+i+1));_probe_bgu_write!(U,b,i,v,rid,p)
    end
    _probe_bgu_clear!(U,b,cnt);U.count[b]=Int32(cnt-1);U.live-=1
    if cnt==1;_probe_bgu_unlink_block!(U,b);else;_probe_bgu_merge_next!(U,b);end
    return nothing
end
function _probe_bgu_predecessor(U,r::Int,c::Int)
    target=Int(U.row_position[r]);b=Int(U.column_head[c]);previous=Int32(0)
    while b!=0
        for k in 1:Int(U.count[b])
            h=Int32((b-1)*32+k)
            Int(U.row_position[Int(_probe_bgu_tuple(U,h)[2])])>=target && return previous
            previous=h
        end
        b=Int(U.next[b])
    end
    return previous
end
# Task2 can supply its existing monotone row cursor and known adjacent source predecessor.
function _probe_bgu_insert_at!(U,r::Int,c::Int,value::Float64,rank::Int,pred::Int32,allocate,limit::Integer)
    _probe_bgu_coordinates(U,r,c);d=_probe_bgu_degree(U,r)
    1<=rank<=d+1 || throw(ArgumentError("row cursor"))
    rank>1 && _probe_bgu_cid(U,_probe_bgu_row_handle(U,r,rank-1))>=c && throw(ArgumentError("row predecessor"))
    rank<=d && _probe_bgu_cid(U,_probe_bgu_row_handle(U,r,rank))<=c && throw(ArgumentError("row successor"))
    if pred==0
        b=Int(U.column_head[c]);pos=1
    else
        b,k=_probe_bgu_decode(pred)
        1<=b<=U.used && U.column[b]==c && 1<=k<=U.count[b] || throw(ArgumentError("column predecessor"))
        U.row_position[Int(_probe_bgu_tuple(U,pred)[2])]<U.row_position[r] || throw(ArgumentError("predecessor row order"))
        pos=k+1
    end
    # Check immediate successor without searching the column.
    nb=b;np=pos
    if nb!=0 && np>U.count[nb];nb=Int(U.next[nb]);np=1;end
    nb!=0 && U.row_position[Int(_probe_bgu_tuple(U,Int32((nb-1)*32+np))[2])]<=U.row_position[r] && throw(ArgumentError("successor row order"))
    newlive=Base.Checked.checked_add(U.live,1)
    _probe_bgu_reserve_row!(U,r,rank,allocate,limit)
    count=b==0 ? 0 : Int(U.count[b]);reserve=0
    if b==0 || count==32
        reserve=_probe_bgu_reserve_block!(U,b==0 ? 1 : 32,allocate,limit)
    elseif count==U.capacity[b]
        reserve=_probe_bgu_reserve_block!(U,count+1,allocate,limit)
    end
    # All checked arithmetic/conversions and allocation precede edits below.
    _probe_bgu_gap!(U,r,rank);back=Int(U.gap_first[r])
    if b==0
        b=_probe_bgu_take!(U,reserve);_probe_bgu_link_block!(U,b,c,0,0)
    elseif count<32 && reserve!=0
        donor=_probe_bgu_take!(U,reserve);s=Int(U.slab[donor]);start=Int(U.start[donor])
        for k in 1:count
            v,rid,p=_probe_bgu_tuple(U,Int32((b-1)*32+k));idx=start+k-1
            U.values[s][idx]=v;U.row_ids[s][idx]=rid;U.row_backs[s][idx]=p
    # BLOCK_COST_PROBE_BEGIN
            _block_count!(:extent_tuple_moves,1)
    # BLOCK_COST_PROBE_END

        end
        U.slab[b],U.slab[donor]=U.slab[donor],U.slab[b]
        U.start[b],U.start[donor]=U.start[donor],U.start[b]
        U.capacity[b],U.capacity[donor]=U.capacity[donor],U.capacity[b]
        for k in 1:Int(U.capacity[donor]);_probe_bgu_clear!(U,donor,k);end
        _probe_bgu_free!(U,donor)
    end
    U.gap_first[r]=Int32(back+1);U.gap_length[r]-=Int32(1)
    if count==32
    # BLOCK_COST_PROBE_BEGIN
    _block_count!(:splits,1);_block_count!(:split_stage_reads,32);_block_count!(:split_stage_writes,33);_block_count!(:split_final_writes,33)
    # BLOCK_COST_PROBE_END

        for k in 1:33
            if k==pos
                U.scratch_value[k]=value;U.scratch_row[k]=Int32(r);U.scratch_back[k]=Int32(back)
            else
                old=k<pos ? k : k-1;v,rid,p=_probe_bgu_tuple(U,Int32((b-1)*32+old))
                U.scratch_value[k]=v;U.scratch_row[k]=rid;U.scratch_back[k]=p
            end
        end
        other=_probe_bgu_take!(U,reserve);after=Int(U.next[b]);_probe_bgu_link_block!(U,other,c,b,after)
        _probe_bgu_from_stage!(U,b,0,16);_probe_bgu_from_stage!(U,other,16,17)
    else
        for k in count:-1:pos
    # BLOCK_COST_PROBE_BEGIN
            _block_count!(:insert_tuple_moves,1)
    # BLOCK_COST_PROBE_END

            v,rid,p=_probe_bgu_tuple(U,Int32((b-1)*32+k));_probe_bgu_write!(U,b,k+1,v,rid,p)
        end
        _probe_bgu_write!(U,b,pos,value,Int32(r),Int32(back));U.count[b]=Int32(count+1)
    end
    U.live=newlive;return nothing
end
function _probe_bgu_set_with!(U,r::Int,c::Int,value::Float64,allocate,limit::Integer)::Nothing
    _probe_bgu_coordinates(U,r,c);rank,h=_probe_bgu_row_search(U,r,c)
    if h!=0
        if iszero(value);_probe_bgu_delete!(U,r,rank,h)
        else;b,k=_probe_bgu_decode(h);U.values[Int(U.slab[b])][Int(U.start[b])+k-1]=value;end
    elseif !iszero(value)
        _probe_bgu_insert_at!(U,r,c,value,rank,_probe_bgu_predecessor(U,r,c),allocate,limit)
    end
    return nothing
end
_probe_bgu_set!(U::ProbeBGBlockUpper,rid::Int,cid::Int,value::Float64)::Nothing=
    _probe_bgu_set_with!(U,rid,cid,value,_probe_bgu_allocate,typemax(Int32))
function _probe_bgu_swap_rows!(U::ProbeBGBlockUpper,j::Int)::Nothing
    1<=j<U.n || throw(ArgumentError("adjacent rows"))
    a=Int(U.row_order[j]);b=Int(U.row_order[j+1]);i=1;k=1
    while i<=_probe_bgu_degree(U,a) && k<=_probe_bgu_degree(U,b)
        h=_probe_bgu_row_handle(U,a,i);t=_probe_bgu_row_handle(U,b,k);c=_probe_bgu_cid(U,h);d=_probe_bgu_cid(U,t)
        if c<d;i+=1
        elseif d<c;k+=1
        else
            x=_probe_bgu_tuple(U,h);y=_probe_bgu_tuple(U,t);bh,kh=_probe_bgu_decode(h);bt,kt=_probe_bgu_decode(t)
            _probe_bgu_write!(U,bh,kh,y...);_probe_bgu_write!(U,bt,kt,x...);i+=1;k+=1
    # BLOCK_COST_PROBE_BEGIN
            _block_count!(:swap_tuple_moves,2)
    # BLOCK_COST_PROBE_END

        end
    end
    U.row_order[j]=Int32(b);U.row_order[j+1]=Int32(a);U.row_position[a]=Int32(j+1);U.row_position[b]=Int32(j)
    return nothing
end
function _probe_bgu_rotate_rows!(U::ProbeBGBlockUpper,first::Int,last::Int)::Nothing
    1<=first<=last<=U.n || throw(ArgumentError("row rotation"))
    first==last && return nothing
    r=Int(U.row_order[first])
    for i in 1:_probe_bgu_degree(U,r)
        h=_probe_bgu_row_handle(U,r,i);x=_probe_bgu_tuple(U,h);b,k=_probe_bgu_decode(h)
        while true
            nb=b;nk=k+1
            if nk>U.count[b];nb=Int(U.next[b]);nk=1;end
            nb==0 && break
            y=_probe_bgu_tuple(U,Int32((nb-1)*32+nk));U.row_position[Int(y[2])]>last && break
            _probe_bgu_write!(U,b,k,y...);b=nb;k=nk
    # BLOCK_COST_PROBE_BEGIN
            _block_count!(:rotation_tuple_moves,1)
    # BLOCK_COST_PROBE_END

        end
        _probe_bgu_write!(U,b,k,x...)
    # BLOCK_COST_PROBE_BEGIN
        _block_count!(:rotation_tuple_moves,1)
    # BLOCK_COST_PROBE_END

    end
    for j in first:last-1
        rid=U.row_order[j+1];U.row_order[j]=rid;U.row_position[Int(rid)]=Int32(j)
    end
    U.row_order[last]=Int32(r);U.row_position[r]=Int32(last);return nothing
end
function _probe_bgu_build_with(A::SparseMatrixCSC{Float64,Int},q::Vector{Int},allocate,limit::Integer)::ProbeBGBlockUpper
    n=size(A,1);size(A,2)==n && length(q)==n || throw(ArgumentError("square U and q"))
    _probe_bgu_limit(Base.Checked.checked_add(n,1),limit)
    m=length(A.nzval);_probe_bgu_limit(m,limit)
    length(A.rowval)==m && length(A.colptr)==n+1 || throw(ArgumentError("CSC lengths"))
    A.colptr[1]==1 && A.colptr[end]==m+1 || throw(ArgumentError("CSC endpoints"))
    K=0
    for c in 1:n
        a=A.colptr[c];b=A.colptr[c+1]
        1<=a<=b<=m+1 || throw(ArgumentError("CSC pointer"))
        K=Base.Checked.checked_add(K,cld(b-a,32))
    end
    _probe_bgu_limit(Base.Checked.checked_mul(K,32),limit)
    U=_probe_bgu_new(n,K,m==0 ? 0 : 1,allocate)
    # gap_first temporarily holds row degrees; gap_length temporarily fill cursors.
    for j in 1:n
        c=q[j];1<=c<=n && U.column_position[c]==0 || throw(ArgumentError("q permutation"))
        U.column_order[j]=Int32(c);U.column_position[c]=Int32(j)
        U.row_order[j]=Int32(j);U.row_position[j]=Int32(j)
        previous=0
        for p in A.colptr[j]:A.colptr[j+1]-1
            r=A.rowval[p];previous<r<=n || throw(ArgumentError("CSC rows strictly increasing"))
            U.gap_first[r]+=Int32(1);previous=r
        end
    end
    for r in 1:n
        d=Int(U.gap_first[r]);_probe_bgu_limit(d+1,limit);U.rows[r]=allocate(Int32,d)::Vector{Int32}
    end
    if m>0
        U.values[1]=allocate(Float64,m)::Vector{Float64};U.row_ids[1]=allocate(Int32,m)::Vector{Int32};U.row_backs[1]=allocate(Int32,m)::Vector{Int32}
        U.slabs=1
    end
    used=0
    # Stable-column order builds sorted row incidences without sorting/insertion.
    for cid in 1:n
        j=Int(U.column_position[cid]);a=A.colptr[j];z=A.colptr[j+1]-1;before=0
        while a<=z
            used+=1;b=used;cnt=min(32,z-a+1)
            U.slab[b]=1;U.start[b]=Int32(a);U.capacity[b]=Int32(cnt);U.count[b]=Int32(cnt)
            _probe_bgu_link_block!(U,b,cid,before,0)
            for k in 1:cnt
                p=a+k-1;r=A.rowval[p];back=Int(U.gap_length[r])+1;U.gap_length[r]=Int32(back)
                _probe_bgu_write!(U,b,k,A.nzval[p],Int32(r),Int32(back))
            end
            before=b;a+=cnt
        end
    end
    for r in 1:n;U.gap_first[r]+=Int32(1);U.gap_length[r]=0;end
    U.used=used;U.live=m;return U
end
_probe_bgu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::ProbeBGBlockUpper=
    _probe_bgu_build_with(A,q,_probe_bgu_allocate,typemax(Int32))
_probe_bgu_build(A,q)=throw(ArgumentError("block U requires Float64/Int CSC and Int q"))
function _probe_bgu_copy_with(U::ProbeBGBlockUpper,allocate)::ProbeBGBlockUpper
    V=_probe_bgu_new(U.n,length(U.slab),length(U.values),allocate,false)
    for field in (:slab,:start,:capacity,:count,:column,:prev,:next,:row_order,:row_position,:column_order,:column_position,:column_head,:column_tail,:gap_first,:gap_length,:bins,:scratch_value,:scratch_row,:scratch_back)
        copyto!(getfield(V,field),getfield(U,field))
    end
    for s in 1:U.slabs
        V.values[s]=_probe_bgu_grown(U.values[s],length(U.values[s]),allocate)
        V.row_ids[s]=_probe_bgu_grown(U.row_ids[s],length(U.row_ids[s]),allocate)
        V.row_backs[s]=_probe_bgu_grown(U.row_backs[s],length(U.row_backs[s]),allocate)
    end
    for r in 1:U.n;V.rows[r]=_probe_bgu_grown(U.rows[r],length(U.rows[r]),allocate);end
    V.live=U.live;V.used=U.used;V.slabs=U.slabs;return V
end
_probe_bgu_copy(U::ProbeBGBlockUpper)::ProbeBGBlockUpper=_probe_bgu_copy_with(U,_probe_bgu_allocate)
