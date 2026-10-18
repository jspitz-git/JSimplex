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
# Test-only oracles. UNEXECUTED; never included in a timed manager.
function _probe_sbu_check(U::ProbeBGSplitUpper)::Bool
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
                h=_probe_sbu_handle(b,k);v,r,p=_probe_sbu_tuple(U,h)
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
            v,rid,back=_probe_sbu_tuple(U,h);@assert rid==r && back==p
            c=_probe_sbu_cid(U,h);@assert c>lastcol;lastcol=c;push!(rowhandles,h)
        end
    end
    @assert rowhandles==livehandles
    for b in U.used+1:K
        @assert all(getfield(U,f)[b]==0 for f in (:slab,:start,:capacity,:count,:column,:prev,:next))
    end
    return true
end
function _probe_sbu_test_free(caps::Vector{Int}; n::Int=8,K::Int=max(length(caps),16))
    U=_probe_sbu_new(n,K,isempty(caps) ? 0 : 1,_probe_sbu_allocate)
    for i in 1:n
        U.row_order[i]=U.row_position[i]=U.column_order[i]=U.column_position[i]=Int32(i)
        U.rows[i]=Int32[];U.gap_first[i]=1
    end
    if !isempty(caps)
        C=sum(caps);U.values[1]=zeros(C);U.row_ids[1]=zeros(Int32,C);U.row_backs[1]=zeros(Int32,C);U.slabs=1
        start=1
        for (b,cap) in enumerate(caps)
            U.slab[b]=1;U.start[b]=Int32(start);U.capacity[b]=Int32(cap);_probe_sbu_free!(U,b);start+=cap
        end
    end
    U.used=length(caps);return U
end
function _probe_sbu_test_claim!(U,b,c)
    # Finish one synchronous reserve; only this test helper manually publishes a singleton.
    _probe_sbu_reserve_row!(U,c,1,_probe_sbu_allocate,typemax(Int32))
    _probe_sbu_take!(U,b);_probe_sbu_link_block!(U,b,c,0,0)
    U.gap_first[c]=2;U.gap_length[c]-=Int32(1)
    _probe_sbu_write!(U,b,1,Float64(c),Int32(c),Int32(1));U.count[b]=1;U.live+=1
end
