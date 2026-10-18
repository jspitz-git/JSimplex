# Separate untimed source-inverse probe, never used by timed factory.
bits(v)=collect(reinterpret(UInt64,v))
history(f)=[[(s.row,s.last,s.swapped,reinterpret(UInt64,s.multiplier)) for s in u.steps] for u in f.updates]
counts()=Dict(string(k)=>v for (k,v) in J._split_probe_counts)
function packed_state(f)
    ptr=Int[1];rows=Int[];values=UInt64[]
    for col in f.upper
        append!(rows,collect(col.indices));append!(values,bits(col.values));push!(ptr,length(rows)+1)
    end
    return (n=length(f.upper),colptr=ptr,rowval=rows,bits=values)
end
function block_state(U)
    ptr=Int[1];rows=Int[];values=UInt64[]
    for c in U.column_order
        b=Int(U.column_head[Int(c)])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b])
            for k in a:a+Int(U.count[b])-1
                push!(rows,Int(U.row_position[Int(U.row_ids[s][k])]))
                push!(values,reinterpret(UInt64,U.values[s][k]))
            end
            b=Int(U.next[b])
        end
        push!(ptr,length(rows)+1)
    end
    return (n=U.n,colptr=ptr,rowval=rows,bits=values)
end
function array_record(label,a)
    memory=getfield(getfield(a,:ref),:mem)
    return Dict("name"=>label,"length"=>length(a),"element_bytes"=>Base.elsize(typeof(a)),
        "backing_length"=>length(memory),"backing_bytes"=>sizeof(memory),"graph_bytes"=>Base.summarysize(a))
end
function storage(U)
    arrays=Dict[]
    for name in fieldnames(typeof(U))
        a=getfield(U,name);a isa Vector && push!(arrays,array_record(string(name),a))
    end
    for s in 1:U.slabs, name in (:values,:row_ids,:row_backs)
        push!(arrays,array_record("$(name)[$s]",getfield(U,name)[s]))
    end
    for r in 1:U.n;push!(arrays,array_record("rows[$r]",U.rows[r]));end
    C=sum((length(U.values[s]) for s in 1:U.slabs);init=0)
    R=sum(length,U.rows;init=0);K=length(U.slab);S=U.slabs;D=length(U.values)
    free=sum((Int(U.capacity[b]) for b in 1:U.used if U.column[b]==0);init=0)
    liveblocks=count(b->U.column[b]!=0,1:U.used)
    payload=16*C+4*R+28*K+32*U.n+656
    return Dict("C"=>C,"R"=>R,"K"=>K,"S"=>S,"D"=>D,"used"=>U.used,
        "live"=>U.live,"live_blocks"=>liveblocks,"free_capacity"=>free,
        "active_slack"=>C-free-U.live,"bin_heads"=>Int.(U.bins),
        "column_heads"=>Int.(U.column_head),"column_tails"=>Int.(U.column_tail),
        "extents"=>[[Int(getfield(U,f)[b]) for f in (:slab,:start,:capacity,:count,:column,:prev,:next)] for b in 1:U.used],
        "gap_reserve"=>sum(Int,U.gap_length;init=0),"core_payload"=>payload,
        "outer_pointer_payload"=>8*U.n+24*D,"struct_bytes"=>sizeof(U),
        "graph_bytes"=>Base.summarysize(U),"arrays"=>arrays)
end
function checkpoint(r,d,p,k,refactored)
    require(J._sbu_check(d.upper) && J._probe_sbu_check(p.upper),"Split invariant")
    same=isequal(packed_state(r),block_state(d.upper)) && isequal(packed_state(r),block_state(p.upper)) &&
        isequal(history(r),history(d)) && isequal(history(r),history(p)) &&
        r.column_order==d.upper.column_order==p.upper.column_order &&
        r.positions==d.upper.column_position==p.upper.column_position &&
        J._direct_mode(r)==J._split_bg_mode(d)==J._probe_split_bg_mode(p)
    require(same,"Probe state mismatch")
    return Dict("step"=>k,"refactored"=>refactored,"equal"=>same,
        "graphs"=>[Base.summarysize(x) for x in (r,d,p)],"storage"=>storage(d.upper),
        "history_length"=>length(d.updates),"counts"=>counts())
end
function probe(backend,f,source)
    for k in keys(J._split_probe_counts);J._split_probe_counts[k]=0;end
    r=J._direct_lu_factor(J.BartelsGolubFactorization,f.matrices[1],backend,policy(backend);normalize=true)
    d=J._split_bg_factor(f.matrices[1],backend,policy(backend))
    p=J._probe_split_bg_factor(f.matrices[1],backend,policy(backend))
    states=[checkpoint(r,d,p,0,false)]
    outputs=[[zeros(f.n) for _ in 1:24] for _ in 1:3]
    for k in 1:8
        s=f.steps[k]
        for (factor,dest) in zip((r,d,p),outputs)
            J.forward_solve!(dest[3k-2],factor,s.a)
            J.forward_solve!(dest[3k-1],factor,s.dse)
            J.replace_column!(factor,dest[3k-2],s.j)
            J.transpose_solve!(dest[3k],factor,s.unit)
        end
        require(all(bits(outputs[1][i])==bits(outputs[2][i])==bits(outputs[3][i]) for i in 3k-2:3k),"Probe bitwise output mismatch")
        push!(states,checkpoint(r,d,p,k,false))
        if k in (4,8)
            for factor in (r,d,p);J.refactorize!(factor,f.matrices[k+1]);end
            push!(states,checkpoint(r,d,p,k,true))
        end
    end
    ok=unchanged(f,source);require(ok,"Probe changed inputs")
    return Dict("states"=>states,"outputs"=>[[token.(v) for v in side] for side in outputs],
        "inputs_unchanged"=>ok,"constructions"=>3,"refactors"=>6,"updates"=>24,
        "ftran"=>48,"btran"=>24,"copies"=>0,"counts"=>counts())
end
# One structural-only source-inverse repeated row-fill probe; no factorization/solve.
function row_growth_probe()
    for k in keys(J._split_probe_counts);J._split_probe_counts[k]=0;end
    U=J._probe_sbu_build(spzeros(64,64),collect(1:64));states=Dict[]
    for c in 1:64
        J._probe_sbu_set!(U,1,c,Float64(c));require(J._probe_sbu_check(U),"Row growth invariant")
        push!(states,Dict("insertions"=>c,"row_capacity"=>length(U.rows[1]),"counts"=>counts()))
    end
    require(U.live==64 && all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,1,c))[1]===Float64(c) for c in 1:64),"Row growth values")
    return Dict("complete"=>true,"n"=>64,"insertions"=>64,"factorizations"=>0,"solves"=>0,"states"=>states,"storage"=>storage(U),"counts"=>counts())
end

# Fixed structural schedules; helper setup allocations are deliberately outside
# counted operation ledgers. Full initial storage is saved before counter reset.
reset_counts!()=(foreach(k->(J._split_probe_counts[k]=0),keys(J._split_probe_counts));nothing)
function structural_state(U,step)
    return Dict("step"=>step,"storage"=>storage(U),"counts"=>counts())
end
function structural_schedules()
    results=Dict[]
    U=J._probe_sbu_test_free([32]);reset_counts!()
    require(J._probe_sbu_check(U),"Repeated4 initial")
    states=[structural_state(U,0)]
    for c in 1:8
        b=J._probe_sbu_reserve_block!(U,4,J._probe_sbu_allocate,typemax(Int32))
        J._probe_sbu_test_claim!(U,b,c)
        require(J._probe_sbu_check(U) && U.live==c && all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,i,i))[1]===Float64(i) for i in 1:c),"Repeated4 values")
        push!(states,structural_state(U,c))
    end
    push!(results,Dict("name"=>"repeated4","n"=>8,"sets"=>0,"reservations"=>8,"claims"=>8,"invariant_checks"=>9,"states"=>states))
    U=J._probe_sbu_test_free(Int[];n=32);reset_counts!()
    require(J._probe_sbu_check(U),"Monotone initial");states=[structural_state(U,0)]
    for r in 1:32
        J._probe_sbu_set!(U,r,1,Float64(r))
        require(J._probe_sbu_check(U) && U.live==r && all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,i,1))[1]===Float64(i) for i in 1:r),"Monotone values")
        push!(states,structural_state(U,r))
    end
    push!(results,Dict("name"=>"monotone32","n"=>32,"sets"=>32,"reservations"=>0,"claims"=>0,"invariant_checks"=>33,"states"=>states))
    U=J._probe_sbu_test_free(fill(3,16);n=40,K=16);reset_counts!()
    require(J._probe_sbu_check(U),"Fragmented initial");states=[structural_state(U,0)]
    b=J._probe_sbu_reserve_block!(U,3,J._probe_sbu_allocate,typemax(Int32));J._probe_sbu_test_claim!(U,b,1)
    require(J._probe_sbu_check(U) && U.live==1,"Fragmented claim");push!(states,structural_state(U,1))
    J._probe_sbu_set!(U,1,1,0.0);require(J._probe_sbu_check(U) && U.live==0,"Fragmented delete");push!(states,structural_state(U,2))
    for cycle in 1:3
        for r in 1:40
            J._probe_sbu_set!(U,r,1,Float64(r))
            require(J._probe_sbu_check(U) && U.live==r,"Fragmented fill invariant")
        end
        require(all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,r,1))[1]===Float64(r) for r in 1:40),"Fragmented fill values")
        push!(states,structural_state(U,2+80*(cycle-1)+40))
        for r in 1:40
            J._probe_sbu_set!(U,r,1,0.0)
            require(J._probe_sbu_check(U) && U.live==40-r,"Fragmented drain invariant")
        end
        push!(states,structural_state(U,2+80*cycle))
    end
    push!(results,Dict("name"=>"fragmented_refill","n"=>40,"sets"=>241,"reservations"=>1,"claims"=>1,"invariant_checks"=>243,"states"=>states))
    return results
end
function growth_probe()
    result=row_growth_probe();result["schedules"]=structural_schedules();return result
end
