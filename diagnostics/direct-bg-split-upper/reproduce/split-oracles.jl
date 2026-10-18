# Test-only oracles. UNEXECUTED; never included in a timed manager.
function _sbu_check(U::BGSplitUpper)::Bool
    n=U.n;K=length(U.slab);D=length(U.values)
    @assert 0<=U.used<=K && 0<=U.slabs<=D
    @assert length(U.row_ids)==D==length(U.row_backs)
    for field in (:start,:capacity,:count,:column,:prev,:next);@assert length(getfield(U,field))==K;end
    for field in (:row_order,:row_position,:column_order,:column_position,:column_head,:column_tail,:rows,:gap_first,:gap_length)
        @assert length(getfield(U,field))==n
    end
    @assert length(U.bins)==32
    @assert length(U.scratch_value)==length(U.scratch_row)==length(U.scratch_back)==33
    @assert sort(Int.(U.row_order))==collect(1:n) && sort(Int.(U.column_order))==collect(1:n)
    @assert all(U.row_position[Int(U.row_order[j])]==j && U.column_position[Int(U.column_order[j])]==j for j in 1:n)
    seen=falses(U.used);owners=[zeros(Int,length(U.values[s])) for s in 1:U.slabs]
    for s in 1:U.slabs;@assert length(U.values[s])==length(U.row_ids[s])==length(U.row_backs[s]);end
    for b in 1:U.used
        s=Int(U.slab[b]);a=Int(U.start[b]);cap=Int(U.capacity[b])
        @assert 1<=s<=U.slabs && 1<=cap<=32 && 1<=a<=a+cap-1<=length(owners[s])
        for p in a:a+cap-1;@assert owners[s][p]==0;owners[s][p]=b;end
    end
    @assert all(all(!iszero,a) for a in owners)
    @assert sum(Int(U.capacity[b]) for b in 1:U.used; init=0)==sum(length(U.values[s]) for s in 1:U.slabs; init=0)
    @assert U.used<=sum(length(U.values[s]) for s in 1:U.slabs; init=0)
    for b in 1:U.used, k in Int(U.count[b])+1:Int(U.capacity[b])
        s=Int(U.slab[b]);p=Int(U.start[b])+k-1
        @assert isequal(U.values[s][p],0.0) && U.row_ids[s][p]==0 && U.row_backs[s][p]==0
    end

    livehandles=Set{Int32}();live=0
    for cid in 1:n
        b=Int(U.column_head[cid]);previous=0;lastrow=0
        while b!=0
            @assert 1<=b<=U.used && !seen[b];seen[b]=true
            @assert U.column[b]==cid && U.prev[b]==previous && 1<=U.count[b]<=U.capacity[b]
            for k in 1:Int(U.count[b])
                h=_sbu_handle(b,k);v,r,p=_sbu_tuple(U,h)
                @assert 1<=r<=n && 1<=p<=length(U.rows[Int(r)])
                @assert lastrow<U.row_position[Int(r)];lastrow=Int(U.row_position[Int(r)])
                @assert U.rows[Int(r)][Int(p)]==h && !(h in livehandles)
                push!(livehandles,h);live+=1
            end
            previous=b;b=Int(U.next[b])
        end
        @assert U.column_tail[cid]==previous
    end
    for cap in 1:32
        b=Int(U.bins[cap]);previous=0
        while b!=0
            @assert 1<=b<=U.used && !seen[b];seen[b]=true
            @assert U.count[b]==0 && U.column[b]==0 && U.capacity[b]==cap && U.prev[b]==previous
            previous=b;b=Int(U.next[b])
        end
    end
    @assert all(seen) && live==U.live
    rowhandles=Set{Int32}()
    for r in 1:n
        a=U.rows[r];g=Int(U.gap_first[r]);l=Int(U.gap_length[r]);lastcol=0
        @assert 0<=l<=length(a) && 1<=g<=length(a)-l+1
        for p in eachindex(a)
            if g<=p<g+l;@assert a[p]==0;continue;end
            h=a[p];@assert h in livehandles && !(h in rowhandles)
            v,rid,back=_sbu_tuple(U,h);@assert rid==r && back==p
            c=_sbu_cid(U,h);@assert c>lastcol;lastcol=c;push!(rowhandles,h)
        end
    end
    @assert rowhandles==livehandles
    for b in U.used+1:K
        @assert all(getfield(U,f)[b]==0 for f in (:slab,:start,:capacity,:count,:column,:prev,:next))
    end
    return true
end
function _sbu_materialize(U::BGSplitUpper)
    A=zeros(Float64,U.n,U.n)
    for j in 1:U.n
        c=Int(U.column_order[j]);b=Int(U.column_head[c])
        while b!=0
            for k in 1:Int(U.count[b])
                v,r,p=_sbu_tuple(U,_sbu_handle(b,k));A[Int(U.row_position[Int(r)]),j]=v
            end
            b=Int(U.next[b])
        end
    end
    return A
end
function _sbu_test_column(n,rows)
    return sparse(rows,fill(1,length(rows)),Float64.(rows),n,n)
end
function _sbu_test_arrays(U)
    arrays=Any[]
    for name in fieldnames(BGSplitUpper)
        value=getfield(U,name);value isa AbstractVector && push!(arrays,value)
    end
    for s in 1:U.slabs;append!(arrays,(U.values[s],U.row_ids[s],U.row_backs[s]));end
    append!(arrays,U.rows);return arrays
end
function _sbu_test_disjoint(U,V)
    return all(a!==b for a in _sbu_test_arrays(U),b in _sbu_test_arrays(V))
end
_sbu_test_capacity(U)=(sum(length,U.values[1:U.slabs]),sum(length,U.rows),length(U.slab),length(U.values))
struct SBUInjectedAllocationFailure <: Exception end
function _sbu_test_allocation_failures(factory,operation)
    count=Ref(0)
    countalloc(T,n)=(count[]+=1;Vector{T}(undef,n))
    sample=factory();operation(sample,countalloc);@test _sbu_check(sample)
    @test count[]>0
    for stop in 1:count[]
        U=factory();expected=_sbu_materialize(U);row=copy(U.row_order);col=copy(U.column_order);live=U.live
        calls=Ref(0)
        allocate(T,n)=(calls[]+=1;calls[]==stop && throw(SBUInjectedAllocationFailure());Vector{T}(undef,n))
        @test_throws SBUInjectedAllocationFailure operation(U,allocate)
        @test _sbu_check(U)
        @test isequal(_sbu_materialize(U),expected) && U.row_order==row && U.column_order==col && U.live==live
    end
end
function _sbu_test_build_failures(A,q)
    before=copy(A);qs=copy(q);count=Ref(0)
    allocate(T,n)=(count[]+=1;Vector{T}(undef,n))
    U=_sbu_build_with(A,q,allocate,typemax(Int32));@test _sbu_check(U)
    for stop in 1:count[]
        calls=Ref(0)
        fail(T,n)=(calls[]+=1;calls[]==stop && throw(SBUInjectedAllocationFailure());Vector{T}(undef,n))
        @test_throws SBUInjectedAllocationFailure _sbu_build_with(A,q,fail,typemax(Int32))
        @test isequal(A,before) && q==qs
    end
end

function _sbu_test_right_merge_fixture()
    A=sparse(vcat(collect(1:16),collect(17:48)),vcat(fill(1,16),fill(2,32)),Float64.(1:48),64,64)
    q=vcat([3,1,2],collect(4:64));U=_sbu_build(A,q)
    left=Int(U.column_head[3]);right=Int(U.column_head[1])
    # No numerical work: join disjoint row memberships; each row has one incidence.
    U.next[left]=Int32(right);U.prev[right]=Int32(left);U.column[right]=3
    U.column_tail[3]=Int32(right);U.column_head[1]=0;U.column_tail[1]=0
    return U,left,right
end

# Test-only free extent fixture, no LP/solver/factorization.
function _sbu_test_free(caps::Vector{Int}; n::Int=8,K::Int=max(length(caps),16))
    U=_sbu_new(n,K,isempty(caps) ? 0 : 1,_sbu_allocate)
    for i in 1:n
        U.row_order[i]=U.row_position[i]=U.column_order[i]=U.column_position[i]=Int32(i)
        U.rows[i]=Int32[];U.gap_first[i]=1
    end
    if !isempty(caps)
        C=sum(caps);U.values[1]=zeros(C);U.row_ids[1]=zeros(Int32,C);U.row_backs[1]=zeros(Int32,C);U.slabs=1
        start=1
        for (b,cap) in enumerate(caps)
            U.slab[b]=1;U.start[b]=Int32(start);U.capacity[b]=Int32(cap);_sbu_free!(U,b);start+=cap
        end
    end
    U.used=length(caps);return U
end
function _sbu_test_claim!(U,b,c)
    # Finish one synchronous reserve; only this test helper manually publishes a singleton.
    _sbu_reserve_row!(U,c,1,_sbu_allocate,typemax(Int32))
    _sbu_take!(U,b);_sbu_link_block!(U,b,c,0,0)
    U.gap_first[c]=2;U.gap_length[c]-=Int32(1)
    _sbu_write!(U,b,1,Float64(c),Int32(c),Int32(1));U.count[b]=1;U.live+=1
end
function _sbu_test_handles(U)
    return [[_sbu_row_handle(U,r,k) for k in 1:_sbu_degree(U,r)] for r in 1:U.n]
end
# Test-only counters inferred from before/after reserve geometry; never timed code.
function _sbu_test_set_counted!(U,r,c,v,totals)
    oldK=length(U.slab);oldR=length(U.rows[r]);oldD=length(U.values);oldS=U.slabs
    old=[(U.slab[b],U.start[b],U.capacity[b],U.count[b],U.column[b]) for b in 1:U.used]
    # Observe completed reserve publications at EVERY allocation boundary and after return:
    # append followed by split can grow metadata twice in one insertion.
    function observe()
        K=length(U.slab);R=length(U.rows[r]);D=length(U.values);S=U.slabs
        if K!=oldK;totals[:descriptor_copied]+=28oldK;oldK=K;end
        if R!=oldR;totals[:row_copied]+=4oldR;oldR=R;end
        if D!=oldD;totals[:directory_copied]+=24oldS;oldD=D;end
        totals[:slabs]+=S-oldS;oldS=S
    end
    function allocate(T,n)
        observe();totals[:requests]+=1
        totals[:payload]+=(isbitstype(T) ? sizeof(T) : sizeof(Ptr{Cvoid}))*n
        return Vector{T}(undef,n)
    end
    _sbu_set_with!(U,r,c,v,allocate,typemax(Int32));observe()
    for b in eachindex(old)
        s,a,cap,count,col=old[b]
        if col!=0 && U.column[b]==col && (U.slab[b]!=s || U.start[b]!=a)
            totals[:relocated]+=Int(count);totals[:cleared]+=Int(cap)
        end
    end
    return nothing
end
_sbu_test_totals()=Dict(k=>0 for k in (:requests,:payload,:slabs,:descriptor_copied,:row_copied,:directory_copied,:relocated,:cleared))
