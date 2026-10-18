# Task1 private candidate. UNEXECUTED. No solver methods, global overrides or runtime imports.
mutable struct BGSplitUpper
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

_sbu_allocate(::Type{T},n::Int) where {T}=Vector{T}(undef,n)
function _sbu_zeros(::Type{T},n::Int,allocate) where {T}
    a=allocate(T,n)::Vector{T}
    length(a)==n || throw(ArgumentError("allocator length"))
    fill!(a,zero(T)); return a
end
function _sbu_limit(x::Int,limit::Integer)
    0<=x<=limit<=typemax(Int32) || throw(OverflowError("block U index capacity"))
    return x
end
function _sbu_handle(b::Int,k::Int,limit::Integer=typemax(Int32))::Int32
    b>0 && 1<=k<=32 || throw(OverflowError("block U handle coordinate"))
    _sbu_limit(Base.Checked.checked_mul(b,32),limit)
    return Int32((b-1)*32+k)
end
@inline _sbu_decode(h::Int32)=(Int(h-1)÷32+1,Int(h-1)%32+1)
function _sbu_row_capacity(old::Int,required::Int,limit::Integer)
    new=Base.Checked.checked_add(required,min(8,max(1,old÷8)))
    _sbu_limit(Base.Checked.checked_add(new,1),limit)
    return new
end
function _sbu_descriptor_capacity(old::Int,required::Int,limit::Integer)
    required<=old && return old
    new=max(required,Base.Checked.checked_add(old,max(old÷2,8)))
    _sbu_limit(Base.Checked.checked_mul(new,32),limit)
    return new
end
_sbu_buffer(::Type{T},n::Int,allocate,clear::Bool) where {T}=clear ? _sbu_zeros(T,n,allocate) : allocate(T,n)::Vector{T}
function _sbu_new(n::Int,K::Int,D::Int,allocate,clear::Bool=true)
    # Outer directories may contain unassigned spare entries; only1:slabs is live.
    return BGSplitUpper(allocate(Vector{Float64},D),allocate(Vector{Int32},D),allocate(Vector{Int32},D),
        _sbu_buffer(Int32,K,allocate,clear),_sbu_buffer(Int32,K,allocate,clear),_sbu_buffer(Int32,K,allocate,clear),
        _sbu_buffer(Int32,K,allocate,clear),_sbu_buffer(Int32,K,allocate,clear),_sbu_buffer(Int32,K,allocate,clear),_sbu_buffer(Int32,K,allocate,clear),
        _sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,n,allocate,clear),
        _sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,n,allocate,clear),allocate(Vector{Int32},n),
        _sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,n,allocate,clear),_sbu_buffer(Int32,32,allocate,clear),
        _sbu_buffer(Float64,33,allocate,clear),_sbu_buffer(Int32,33,allocate,clear),_sbu_buffer(Int32,33,allocate,clear),n,0,0,0)
end
@inline function _sbu_tuple(U,h::Int32)
    b,k=_sbu_decode(h);s=Int(U.slab[b]);p=Int(U.start[b])+k-1
    return U.values[s][p],U.row_ids[s][p],U.row_backs[s][p]
end
@inline function _sbu_write!(U,b::Int,k::Int,v::Float64,r::Int32,p::Int32)
    s=Int(U.slab[b]);i=Int(U.start[b])+k-1
    U.values[s][i]=v;U.row_ids[s][i]=r;U.row_backs[s][i]=p
    U.rows[Int(r)][Int(p)]=Int32((b-1)*32+k)
    return nothing
end
@inline function _sbu_back!(U,h::Int32,p::Int)
    b,k=_sbu_decode(h);U.row_backs[Int(U.slab[b])][Int(U.start[b])+k-1]=Int32(p)
end
@inline function _sbu_clear!(U,b::Int,k::Int)
    s=Int(U.slab[b]);p=Int(U.start[b])+k-1
    U.values[s][p]=0.0;U.row_ids[s][p]=0;U.row_backs[s][p]=0
end
@inline _sbu_degree(U,r::Int)=length(U.rows[r])-Int(U.gap_length[r])
@inline _sbu_row_offset(U,r::Int,k::Int)=k<Int(U.gap_first[r]) ? k : k+Int(U.gap_length[r])
@inline _sbu_row_handle(U,r::Int,k::Int)=U.rows[r][_sbu_row_offset(U,r,k)]
@inline function _sbu_cid(U,h::Int32)
    b,_=_sbu_decode(h);return Int(U.column[b])
end
function _sbu_coordinates(U,r::Int,c::Int)
    1<=r<=U.n && 1<=c<=U.n || throw(ArgumentError("block U coordinates"))
end
function _sbu_row_search(U,r::Int,c::Int)
    k=1;d=_sbu_degree(U,r)
    while k<=d
        h=_sbu_row_handle(U,r,k);cid=_sbu_cid(U,h)
        cid>=c && return k,(cid==c ? h : Int32(0))
        k+=1
    end
    return k,Int32(0)
end
function _sbu_find(U::BGSplitUpper,rid::Int,cid::Int)::Int32
    _sbu_coordinates(U,rid,cid);return _sbu_row_search(U,rid,cid)[2]
end
function _sbu_gap!(U,r::Int,target::Int)
    a=U.rows[r];g=Int(U.gap_first[r]);l=Int(U.gap_length[r])
    if l==0;U.gap_first[r]=Int32(target);return nothing;end
    while g>target
        h=a[g-1];a[g+l-1]=h;a[g-1]=0;_sbu_back!(U,h,g+l-1);g-=1
    end
    while g<target
        h=a[g+l];a[g]=h;a[g+l]=0;_sbu_back!(U,h,g);g+=1
    end
    U.gap_first[r]=Int32(g);return nothing
end
function _sbu_reserve_row!(U,r::Int,rank::Int,allocate,limit::Integer)
    Int(U.gap_length[r])>0 && return nothing
    d=_sbu_degree(U,r);C=_sbu_row_capacity(length(U.rows[r]),d+1,limit)
    a=allocate(Int32,C)::Vector{Int32};length(a)==C || throw(ArgumentError("allocator length"));gap=C-d
    for p in rank:rank+gap-1;a[p]=0;end
    for k in 1:d
        p=k<rank ? k : k+gap;a[p]=_sbu_row_handle(U,r,k)
    end
    # Allocation succeeded: publish owned reserve, then repair reciprocal positions.
    U.rows[r]=a;U.gap_first[r]=Int32(rank);U.gap_length[r]=Int32(gap)
    for k in rank:d
        p=k+gap;_sbu_back!(U,a[p],p)
    end
    return nothing
end
function _sbu_grown(old::Vector{T},C::Int,allocate) where {T}
    a=allocate(T,C)::Vector{T};length(a)==C || throw(ArgumentError("allocator length"))
    copyto!(a,1,old,1,length(old))
    for k in length(old)+1:C;a[k]=zero(T);end
    return a
end
function _sbu_reserve_descriptors!(U,required::Int,allocate,limit::Integer)
    C=_sbu_descriptor_capacity(length(U.slab),required,limit)
    C==length(U.slab) && return nothing
    a=_sbu_grown(U.slab,C,allocate);b=_sbu_grown(U.start,C,allocate);c=_sbu_grown(U.capacity,C,allocate)
    d=_sbu_grown(U.count,C,allocate);e=_sbu_grown(U.column,C,allocate)
    f=_sbu_grown(U.prev,C,allocate);g=_sbu_grown(U.next,C,allocate)
    U.slab=a;U.start=b;U.capacity=c;U.count=d;U.column=e;U.prev=f;U.next=g
    return nothing
end
function _sbu_free!(U,b::Int)
    cap=Int(U.capacity[b]);h=Int(U.bins[cap])
    U.count[b]=0;U.column[b]=0;U.prev[b]=0;U.next[b]=Int32(h)
    h!=0 && (U.prev[h]=Int32(b));U.bins[cap]=Int32(b)
    return nothing
end
function _sbu_take!(U,b::Int)
    cap=Int(U.capacity[b]);p=Int(U.prev[b]);n=Int(U.next[b])
    if p==0;U.bins[cap]=Int32(n);else;U.next[p]=Int32(n);end
    n!=0 && (U.prev[n]=Int32(p));U.prev[b]=0;U.next[b]=0
    return b
end
function _sbu_free_block(U,required::Int)
    for c in required:32
        U.bins[c]!=0 && return Int(U.bins[c])
    end
    return 0
end
function _sbu_append_slab!(U,allocate,limit::Integer)
    used=Base.Checked.checked_add(U.used,8);ns=Base.Checked.checked_add(U.slabs,1)
    _sbu_limit(ns,limit);_sbu_limit(256,limit)
    _sbu_reserve_descriptors!(U,used,allocate,limit)
    # Every following allocation remains private until all succeed.
    v=_sbu_zeros(Float64,256,allocate);r=_sbu_zeros(Int32,256,allocate);p=_sbu_zeros(Int32,256,allocate)
    D=length(U.values)
    if ns>D
        D=max(ns,Base.Checked.checked_add(D,max(D÷2,1)));_sbu_limit(D,limit)
        av=allocate(Vector{Float64},D);ar=allocate(Vector{Int32},D);ap=allocate(Vector{Int32},D)
        for i in 1:U.slabs;av[i]=U.values[i];ar[i]=U.row_ids[i];ap[i]=U.row_backs[i];end
        av[ns]=v;ar[ns]=r;ap[ns]=p;U.values=av;U.row_ids=ar;U.row_backs=ap
    else
        U.values[ns]=v;U.row_ids[ns]=r;U.row_backs[ns]=p
    end
    for i in 1:8
        b=U.used+i;U.slab[b]=Int32(ns);U.start[b]=Int32(32*(i-1)+1);U.capacity[b]=32
        _sbu_free!(U,b)
    end
    U.used=used;U.slabs=ns;return nothing
end
function _sbu_target(required::Int)::Int
    1<=required<=32 || throw(ArgumentError("split U required capacity"))
    target=1
    while target<required;target*=2;end
    return target
end
function _sbu_reserve_block!(U::BGSplitUpper,required::Int,allocate,limit::Integer)::Int
    target=_sbu_target(required)
    b=_sbu_free_block(U,target)
    if b==0;_sbu_append_slab!(U,allocate,limit);b=Int(U.bins[32]);end
    # Local validation only; all fallible work precedes unlinking the free donor.
    1<=b<=U.used || throw(ArgumentError("split U free descriptor"))
    _sbu_handle(b,32,limit)
    cap=Int(U.capacity[b]);s=Int(U.slab[b]);start=Int(U.start[b])
    U.count[b]==0 && U.column[b]==0 && target<=cap<=32 || throw(ArgumentError("split U free extent"))
    1<=s<=U.slabs || throw(ArgumentError("split U slab"))
    last=Base.Checked.checked_add(start,cap-1);_sbu_limit(last,limit)
    1<=start<=last<=length(U.values[s]) && length(U.values[s])==length(U.row_ids[s])==length(U.row_backs[s]) || throw(ArgumentError("split U extent bounds"))
    cap==target && return b
    suffix=Base.Checked.checked_add(U.used,1);_sbu_handle(suffix,32,limit)
    nextstart=Base.Checked.checked_add(start,target);_sbu_limit(nextstart,limit)
    remainder=cap-target
    Base.Checked.checked_add(nextstart,remainder-1)==last || throw(ArgumentError("split U partition"))
    _sbu_reserve_descriptors!(U,suffix,allocate,limit)
    # Completed descriptor growth is allowed on later failure, but no active extent changes.
    _sbu_take!(U,b)
    U.capacity[b]=Int32(target)
    U.slab[suffix]=Int32(s);U.start[suffix]=Int32(nextstart);U.capacity[suffix]=Int32(remainder)
    U.count[suffix]=0;U.column[suffix]=0;U.prev[suffix]=0;U.next[suffix]=0
    U.used=suffix
    _sbu_free!(U,b);_sbu_free!(U,suffix)
    return b # Still free; caller consumes exactly one reservation at its commit point.
end
function _sbu_link_block!(U,b::Int,c::Int,p::Int,n::Int)
    U.column[b]=Int32(c);U.prev[b]=Int32(p);U.next[b]=Int32(n)
    if p==0;U.column_head[c]=Int32(b);else;U.next[p]=Int32(b);end
    if n==0;U.column_tail[c]=Int32(b);else;U.prev[n]=Int32(b);end
end
function _sbu_unlink_block!(U,b::Int)
    c=Int(U.column[b]);p=Int(U.prev[b]);n=Int(U.next[b])
    if p==0;U.column_head[c]=Int32(n);else;U.next[p]=Int32(n);end
    if n==0;U.column_tail[c]=Int32(p);else;U.prev[n]=Int32(p);end
    _sbu_free!(U,b);return nothing
end
function _sbu_stage!(U,b::Int,offset::Int=0)
    for k in 1:Int(U.count[b])
        v,r,p=_sbu_tuple(U,Int32((b-1)*32+k))
        U.scratch_value[offset+k]=v;U.scratch_row[offset+k]=r;U.scratch_back[offset+k]=p
    end
end
function _sbu_from_stage!(U,b::Int,offset::Int,n::Int)
    for k in 1:n
        _sbu_write!(U,b,k,U.scratch_value[offset+k],U.scratch_row[offset+k],U.scratch_back[offset+k])
    end
    for k in n+1:Int(U.capacity[b]);_sbu_clear!(U,b,k);end
    U.count[b]=Int32(n)
end
function _sbu_merge_next!(U,b::Int)
    n=Int(U.next[b]);n==0 && return nothing
    total=Int(U.count[b])+Int(U.count[n]);total>max(U.capacity[b],U.capacity[n]) && return nothing
    left=Int(U.count[b]);_sbu_stage!(U,b);_sbu_stage!(U,n,left)
    before=Int(U.prev[b]);after=Int(U.next[n]);c=Int(U.column[b])
    keep=U.capacity[b]>=U.capacity[n] ? b : n;drop=keep==b ? n : b
    _sbu_link_block!(U,keep,c,before,after);_sbu_from_stage!(U,keep,0,total)
    for k in 1:Int(U.capacity[drop]);_sbu_clear!(U,drop,k);end
    _sbu_free!(U,drop);return nothing
end
function _sbu_delete!(U,r::Int,rank::Int,h::Int32)
    b,k=_sbu_decode(h);cnt=Int(U.count[b]);_sbu_gap!(U,r,rank)
    g=Int(U.gap_first[r]);l=Int(U.gap_length[r]);U.rows[r][g+l]=0;U.gap_length[r]=Int32(l+1)
    for i in k:cnt-1
        v,rid,p=_sbu_tuple(U,Int32((b-1)*32+i+1));_sbu_write!(U,b,i,v,rid,p)
    end
    _sbu_clear!(U,b,cnt);U.count[b]=Int32(cnt-1);U.live-=1
    if cnt==1;_sbu_unlink_block!(U,b);else;_sbu_merge_next!(U,b);end
    return nothing
end
function _sbu_predecessor(U,r::Int,c::Int)
    target=Int(U.row_position[r]);b=Int(U.column_head[c]);previous=Int32(0)
    while b!=0
        for k in 1:Int(U.count[b])
            h=Int32((b-1)*32+k)
            Int(U.row_position[Int(_sbu_tuple(U,h)[2])])>=target && return previous
            previous=h
        end
        b=Int(U.next[b])
    end
    return previous
end
# Task2 can supply its existing monotone row cursor and known adjacent source predecessor.
function _sbu_insert_at!(U,r::Int,c::Int,value::Float64,rank::Int,pred::Int32,allocate,limit::Integer)
    _sbu_coordinates(U,r,c);d=_sbu_degree(U,r)
    1<=rank<=d+1 || throw(ArgumentError("row cursor"))
    rank>1 && _sbu_cid(U,_sbu_row_handle(U,r,rank-1))>=c && throw(ArgumentError("row predecessor"))
    rank<=d && _sbu_cid(U,_sbu_row_handle(U,r,rank))<=c && throw(ArgumentError("row successor"))
    if pred==0
        b=Int(U.column_head[c]);pos=1
    else
        b,k=_sbu_decode(pred)
        1<=b<=U.used && U.column[b]==c && 1<=k<=U.count[b] || throw(ArgumentError("column predecessor"))
        U.row_position[Int(_sbu_tuple(U,pred)[2])]<U.row_position[r] || throw(ArgumentError("predecessor row order"))
        pos=k+1
    end
    # Check immediate successor without searching the column.
    nb=b;np=pos
    if nb!=0 && np>U.count[nb];nb=Int(U.next[nb]);np=1;end
    nb!=0 && U.row_position[Int(_sbu_tuple(U,Int32((nb-1)*32+np))[2])]<=U.row_position[r] && throw(ArgumentError("successor row order"))
    newlive=Base.Checked.checked_add(U.live,1)
    _sbu_reserve_row!(U,r,rank,allocate,limit)
    count=b==0 ? 0 : Int(U.count[b]);reserve=0
    if b==0 || count==32
        reserve=_sbu_reserve_block!(U,b==0 ? 1 : 32,allocate,limit)
    elseif count==U.capacity[b]
        reserve=_sbu_reserve_block!(U,count+1,allocate,limit)
    end
    # All checked arithmetic/conversions and allocation precede edits below.
    _sbu_gap!(U,r,rank);back=Int(U.gap_first[r])
    if b==0
        b=_sbu_take!(U,reserve);_sbu_link_block!(U,b,c,0,0)
    elseif count<32 && reserve!=0
        donor=_sbu_take!(U,reserve);s=Int(U.slab[donor]);start=Int(U.start[donor])
        for k in 1:count
            v,rid,p=_sbu_tuple(U,Int32((b-1)*32+k));idx=start+k-1
            U.values[s][idx]=v;U.row_ids[s][idx]=rid;U.row_backs[s][idx]=p
        end
        U.slab[b],U.slab[donor]=U.slab[donor],U.slab[b]
        U.start[b],U.start[donor]=U.start[donor],U.start[b]
        U.capacity[b],U.capacity[donor]=U.capacity[donor],U.capacity[b]
        for k in 1:Int(U.capacity[donor]);_sbu_clear!(U,donor,k);end
        _sbu_free!(U,donor)
    end
    U.gap_first[r]=Int32(back+1);U.gap_length[r]-=Int32(1)
    if count==32
        for k in 1:33
            if k==pos
                U.scratch_value[k]=value;U.scratch_row[k]=Int32(r);U.scratch_back[k]=Int32(back)
            else
                old=k<pos ? k : k-1;v,rid,p=_sbu_tuple(U,Int32((b-1)*32+old))
                U.scratch_value[k]=v;U.scratch_row[k]=rid;U.scratch_back[k]=p
            end
        end
        other=_sbu_take!(U,reserve);after=Int(U.next[b]);_sbu_link_block!(U,other,c,b,after)
        _sbu_from_stage!(U,b,0,16);_sbu_from_stage!(U,other,16,17)
    else
        for k in count:-1:pos
            v,rid,p=_sbu_tuple(U,Int32((b-1)*32+k));_sbu_write!(U,b,k+1,v,rid,p)
        end
        _sbu_write!(U,b,pos,value,Int32(r),Int32(back));U.count[b]=Int32(count+1)
    end
    U.live=newlive;return nothing
end
function _sbu_set_with!(U,r::Int,c::Int,value::Float64,allocate,limit::Integer)::Nothing
    _sbu_coordinates(U,r,c);rank,h=_sbu_row_search(U,r,c)
    if h!=0
        if iszero(value);_sbu_delete!(U,r,rank,h)
        else;b,k=_sbu_decode(h);U.values[Int(U.slab[b])][Int(U.start[b])+k-1]=value;end
    elseif !iszero(value)
        _sbu_insert_at!(U,r,c,value,rank,_sbu_predecessor(U,r,c),allocate,limit)
    end
    return nothing
end
_sbu_set!(U::BGSplitUpper,rid::Int,cid::Int,value::Float64)::Nothing=
    _sbu_set_with!(U,rid,cid,value,_sbu_allocate,typemax(Int32))
function _sbu_swap_rows!(U::BGSplitUpper,j::Int)::Nothing
    1<=j<U.n || throw(ArgumentError("adjacent rows"))
    a=Int(U.row_order[j]);b=Int(U.row_order[j+1]);i=1;k=1
    while i<=_sbu_degree(U,a) && k<=_sbu_degree(U,b)
        h=_sbu_row_handle(U,a,i);t=_sbu_row_handle(U,b,k);c=_sbu_cid(U,h);d=_sbu_cid(U,t)
        if c<d;i+=1
        elseif d<c;k+=1
        else
            x=_sbu_tuple(U,h);y=_sbu_tuple(U,t);bh,kh=_sbu_decode(h);bt,kt=_sbu_decode(t)
            _sbu_write!(U,bh,kh,y...);_sbu_write!(U,bt,kt,x...);i+=1;k+=1
        end
    end
    U.row_order[j]=Int32(b);U.row_order[j+1]=Int32(a);U.row_position[a]=Int32(j+1);U.row_position[b]=Int32(j)
    return nothing
end
function _sbu_rotate_rows!(U::BGSplitUpper,first::Int,last::Int)::Nothing
    1<=first<=last<=U.n || throw(ArgumentError("row rotation"))
    first==last && return nothing
    r=Int(U.row_order[first])
    for i in 1:_sbu_degree(U,r)
        h=_sbu_row_handle(U,r,i);x=_sbu_tuple(U,h);b,k=_sbu_decode(h)
        while true
            nb=b;nk=k+1
            if nk>U.count[b];nb=Int(U.next[b]);nk=1;end
            nb==0 && break
            y=_sbu_tuple(U,Int32((nb-1)*32+nk));U.row_position[Int(y[2])]>last && break
            _sbu_write!(U,b,k,y...);b=nb;k=nk
        end
        _sbu_write!(U,b,k,x...)
    end
    for j in first:last-1
        rid=U.row_order[j+1];U.row_order[j]=rid;U.row_position[Int(rid)]=Int32(j)
    end
    U.row_order[last]=Int32(r);U.row_position[r]=Int32(last);return nothing
end
function _sbu_build_with(A::SparseMatrixCSC{Float64,Int},q::Vector{Int},allocate,limit::Integer)::BGSplitUpper
    n=size(A,1);size(A,2)==n && length(q)==n || throw(ArgumentError("square U and q"))
    _sbu_limit(Base.Checked.checked_add(n,1),limit)
    m=length(A.nzval);_sbu_limit(m,limit)
    length(A.rowval)==m && length(A.colptr)==n+1 || throw(ArgumentError("CSC lengths"))
    A.colptr[1]==1 && A.colptr[end]==m+1 || throw(ArgumentError("CSC endpoints"))
    K=0
    for c in 1:n
        a=A.colptr[c];b=A.colptr[c+1]
        1<=a<=b<=m+1 || throw(ArgumentError("CSC pointer"))
        K=Base.Checked.checked_add(K,cld(b-a,32))
    end
    _sbu_limit(Base.Checked.checked_mul(K,32),limit)
    U=_sbu_new(n,K,m==0 ? 0 : 1,allocate)
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
        d=Int(U.gap_first[r]);_sbu_limit(d+1,limit);U.rows[r]=allocate(Int32,d)::Vector{Int32}
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
            _sbu_link_block!(U,b,cid,before,0)
            for k in 1:cnt
                p=a+k-1;r=A.rowval[p];back=Int(U.gap_length[r])+1;U.gap_length[r]=Int32(back)
                _sbu_write!(U,b,k,A.nzval[p],Int32(r),Int32(back))
            end
            before=b;a+=cnt
        end
    end
    for r in 1:n;U.gap_first[r]+=Int32(1);U.gap_length[r]=0;end
    U.used=used;U.live=m;return U
end
_sbu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGSplitUpper=
    _sbu_build_with(A,q,_sbu_allocate,typemax(Int32))
_sbu_build(A,q)=throw(ArgumentError("block U requires Float64/Int CSC and Int q"))
function _sbu_copy_with(U::BGSplitUpper,allocate)::BGSplitUpper
    V=_sbu_new(U.n,length(U.slab),length(U.values),allocate,false)
    for field in (:slab,:start,:capacity,:count,:column,:prev,:next,:row_order,:row_position,:column_order,:column_position,:column_head,:column_tail,:gap_first,:gap_length,:bins,:scratch_value,:scratch_row,:scratch_back)
        copyto!(getfield(V,field),getfield(U,field))
    end
    for s in 1:U.slabs
        V.values[s]=_sbu_grown(U.values[s],length(U.values[s]),allocate)
        V.row_ids[s]=_sbu_grown(U.row_ids[s],length(U.row_ids[s]),allocate)
        V.row_backs[s]=_sbu_grown(U.row_backs[s],length(U.row_backs[s]),allocate)
    end
    for r in 1:U.n;V.rows[r]=_sbu_grown(U.rows[r],length(U.rows[r]),allocate);end
    V.live=U.live;V.used=U.used;V.slabs=U.slabs;return V
end
_sbu_copy(U::BGSplitUpper)::BGSplitUpper=_sbu_copy_with(U,_sbu_allocate)
