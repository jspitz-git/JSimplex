# UNEXECUTED. Separate untimed correctness/instrumentation path, no global overwrite.
bits(v)=collect(reinterpret(UInt64,v))
history(f)=[[(s.row,s.last,s.swapped,reinterpret(UInt64,s.multiplier)) for s in u.steps] for u in f.updates]
function packed_state(f)
    ptr=Int[1];rows=Int[];values=UInt64[]
    for col in f.upper
        append!(rows,collect(col.indices));append!(values,bits(col.values));push!(ptr,length(rows)+1)
    end
    return (n=length(f.upper),colptr=ptr,rowval=rows,bits=values)
end
function checkpoint(r,d,p,k,refactored)
    same=isequal(packed_state(r),_bg_selected_state(d.upper)) && isequal(packed_state(r),_bg_selected_state(p.upper)) &&
        isequal(history(r),history(d)) && isequal(history(r),history(p)) &&
        r.column_order==d.upper.column_order==p.upper.column_order &&
        r.positions==d.upper.column_position==p.upper.column_position &&
        J._direct_mode(r)==J._dynamic_bg_mode(d)==J._probe_dynamic_bg_mode(p)
    require(same,"Probe state mismatch")
    capacity=d.upper.capacity
    return Dict("step"=>k,"refactored"=>refactored,"equal"=>same,
        "graphs"=>[Base.summarysize(x) for x in (r,d,p)],
        "capacity"=>capacity,"live"=>d.upper.live_count,
        "arena_graph_bytes"=>Base.summarysize(d.upper),
        "array_graph_bytes"=>[Base.summarysize(getfield(d.upper,i)) for i in 1:15],
        "requested_payload_bytes"=>56*capacity+64*d.upper.n,
        "copy_arena_payload_bound"=>2*(56*capacity+64*d.upper.n),
        "history_length"=>length(d.updates),"counts"=>copy(J._bg_probe_counts))
end
function probe(backend,f,source)
    fill!(J._bg_probe_counts,0)
    r=J._direct_lu_factor(J.BartelsGolubFactorization,f.matrices[1],backend,policy(backend);normalize=true)
    d=J._dynamic_bg_factor(f.matrices[1],backend,policy(backend))
    p=J._probe_dynamic_bg_factor(f.matrices[1],backend,policy(backend))
    states=[checkpoint(r,d,p,0,false)]
    #72 detached outputs/cell, no persistent old factor owners.
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
    ok=unchanged(f,source)
    require(ok,"Probe changed inputs")
    return Dict("states"=>states,"outputs"=>[[token.(v) for v in side] for side in outputs],
        "inputs_unchanged"=>ok,"constructions"=>3,"refactors"=>6,"updates"=>24,
        "ftran"=>48,"btran"=>24,"copies"=>0,"counts"=>copy(J._bg_probe_counts))
end
