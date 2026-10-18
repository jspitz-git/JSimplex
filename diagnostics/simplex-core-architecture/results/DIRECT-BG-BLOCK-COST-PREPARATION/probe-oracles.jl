# Test-only oracles. UNEXECUTED; never included in a timed manager.
function _bgu_check(U::BGBlockUpper)::Bool
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
    livehandles=Set{Int32}();live=0
    for cid in 1:n
        b=Int(U.column_head[cid]);previous=0;lastrow=0
        while b!=0
            @assert 1<=b<=U.used && !seen[b];seen[b]=true
            @assert U.column[b]==cid && U.prev[b]==previous && 1<=U.count[b]<=U.capacity[b]
            for k in 1:Int(U.count[b])
                h=_bgu_handle(b,k);v,r,p=_bgu_tuple(U,h)
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
            v,rid,back=_bgu_tuple(U,h);@assert rid==r && back==p
            c=_bgu_cid(U,h);@assert c>lastcol;lastcol=c;push!(rowhandles,h)
        end
    end
    @assert rowhandles==livehandles
    for b in U.used+1:K
        @assert all(getfield(U,f)[b]==0 for f in (:slab,:start,:capacity,:count,:column,:prev,:next))
    end
    return true
end
# Test-only oracles. UNEXECUTED; never included in a timed manager.
function _probe_bgu_check(U::ProbeBGBlockUpper)::Bool
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
    livehandles=Set{Int32}();live=0
    for cid in 1:n
        b=Int(U.column_head[cid]);previous=0;lastrow=0
        while b!=0
            @assert 1<=b<=U.used && !seen[b];seen[b]=true
            @assert U.column[b]==cid && U.prev[b]==previous && 1<=U.count[b]<=U.capacity[b]
            for k in 1:Int(U.count[b])
                h=_probe_bgu_handle(b,k);v,r,p=_probe_bgu_tuple(U,h)
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
            v,rid,back=_probe_bgu_tuple(U,h);@assert rid==r && back==p
            c=_probe_bgu_cid(U,h);@assert c>lastcol;lastcol=c;push!(rowhandles,h)
        end
    end
    @assert rowhandles==livehandles
    for b in U.used+1:K
        @assert all(getfield(U,f)[b]==0 for f in (:slab,:start,:capacity,:count,:column,:prev,:next))
    end
    return true
end
