# Separate untimed source-inverse probe; never used by timed factories.
bits(v)=collect(reinterpret(UInt64,v))
history(f)=[[(s.row,s.last,s.swapped,reinterpret(UInt64,s.multiplier)) for s in u.steps] for u in f.updates]
function packed_state(f)
    f = f isa J.BGSpecializedExportFactor || f isa J.BGSpecializedProbeExportFactor ? f.inner : f
    ptr=Int[1];rows=Int[];values=UInt64[]
    for col in f.upper
        append!(rows,collect(col.indices));append!(values,bits(col.values));push!(ptr,length(rows)+1)
    end
    return (n=length(f.upper),colptr=ptr,rowval=rows,bits=values,history=history(f),order=copy(f.column_order),positions=copy(f.positions),mode=J._direct_mode(f))
end
function cache_record(f;limit=nothing)
    w=f.workspace
    isnothing(w) && return Dict{String,Any}("present"=>false,"dimension"=>0,"charge"=>0,"limit"=>0,"seen_bytes"=>0,"orientation_bytes"=>0,"graph_bytes"=>0)
    n=length(f.inner.upper);l=nnz(f.inner.base.lower);u=sum((length(c.values) for c in f.inner.upper);init=0)
    b=J._bgxs_budget(n,l,u);allowed=isnothing(limit) ? b.limit : limit
    require(w.dimension==n && w.charged_bytes<=allowed,"Cache dimension/charge")
    !isnothing(w.seen) && require(length(w.seen)==n,"Seen dimension")
    !isnothing(w.orientation) && require(all(length(v)==n for v in w.orientation),"Orientation dimensions")
    charge=512+(isnothing(w.seen) ? 0 : 8*cld(n,64))+(isnothing(w.orientation) ? 0 : 32*n)
    require(charge==w.charged_bytes,"Exact cache charge")
    return Dict{String,Any}("present"=>true,"dimension"=>n,"charge"=>charge,"limit"=>allowed,
        "seen_bytes"=>isnothing(w.seen) ? 0 : 8*cld(n,64),"orientation_bytes"=>isnothing(w.orientation) ? 0 : 32*n,
        "graph_bytes"=>Base.summarysize(w))
end
function checkpoint(r,c,p,k,refactored,limits)
    require(isequal(packed_state(r),packed_state(c)) && isequal(packed_state(r),packed_state(p)),"Probe paired state")
    return Dict("step"=>k,"refactored"=>refactored,"equal"=>true,
        "graphs"=>[Base.summarysize(x) for x in (r,c,p)],"cache"=>cache_record(c;limit=limits[1]),"probe_cache"=>cache_record(p;limit=limits[2]),
        "counts"=>copy(J._bgxsp_counts),"coexistence_graph_peak"=>J._bgxsp_coexist_peak[])
end
function probe(backend,f,source)
    J._bgxsp_reset!()
    r=factory(Val(:reference),J.BartelsGolubFactorization,f.matrices[1],backend)
    c=factory(Val(:candidate),J.BartelsGolubFactorization,f.matrices[1],backend)
    p=J._bgxsp_factor(f.matrices[1],backend,policy(backend))
    limits=(cache_record(c)["limit"],cache_record(p)["limit"]);states=[checkpoint(r,c,p,0,false,limits)];outputs=[[zeros(f.n) for _ in 1:24] for _ in 1:3]
    for k in 1:8
        s=f.steps[k]
        for (factor,dest) in zip((r,c,p),outputs)
            J.forward_solve!(dest[3k-2],factor,s.a)
            J.forward_solve!(dest[3k-1],factor,s.dse)
            J.replace_column!(factor,dest[3k-2],s.j)
            J.transpose_solve!(dest[3k],factor,s.unit)
        end
        require(all(bits(outputs[1][i])==bits(outputs[2][i])==bits(outputs[3][i]) for i in 3k-2:3k),"Probe outputs")
        push!(states,checkpoint(r,c,p,k,false,limits))
        if k in (4,8)
            for factor in (r,c,p);J.refactorize!(factor,f.matrices[k+1]);end
            limits=(cache_record(c)["limit"],cache_record(p)["limit"]);push!(states,checkpoint(r,c,p,k,true,limits))
        end
    end
    require(unchanged(f,source),"Probe inputs")
    return Dict("states"=>states,"outputs"=>[[token.(v) for v in side] for side in outputs],"inputs_unchanged"=>true,
        "constructions"=>3,"refactors"=>6,"updates"=>24,"ftran"=>48,"btran"=>24,"copies"=>0,
        "counts"=>copy(J._bgxsp_counts),"coexistence_graph_peak"=>J._bgxsp_coexist_peak[],
        "cache_charge_sum"=>sum(s["cache"]["charge"] for s in states),"cache_charge_peak"=>maximum(s["cache"]["charge"] for s in states))
end

struct ZeroOrientation end
LinearAlgebra.ldiv!(out::Vector{Float64},::ZeroOrientation,rhs::Vector{Float64})=(fill!(out,0.0);out)
mutable struct ControlOwner
    workspace::Union{Nothing,J.BGSpecializedExportWorkspace}
end
function bounded_controls(fixtures)
    snapshot_inputs()=[[(copy(M.colptr),copy(M.rowval),bits(M.nzval)) for M in f.matrices] for f in fixtures]
    original_inputs=snapshot_inputs()
    # Synthetic early exit, no backend/factor construction. Exactly two scratch requests.
    n=4;I4=spdiagm(0=>ones(n));owner=ControlOwner(nothing);requests=Tuple{Any,Int}[]
    allocator=(T,k)->begin push!(requests,(T,k));J._bgxs_allocate(T,k) end
    result=J._bgxs_scale_mode(ZeroOrientation(),I4,I4,collect(1:n),collect(1:n),fill(2.0,n),owner,n,n,n;allocate=allocator)
    require(isnothing(result) && isnothing(owner.workspace) && requests==[(Float64,n),(Float64,n)],"Cold nonretained early exit")
    imports=Dict[]
    for label in (:normalize_false,:reject_first,:reject_last)
        values=[1.0,0.0,1.0,0.0,0.0,1.0]
        if label!==:normalize_false
            slot=label===:reject_first ? 2 : 5;row=slot==2 ? 1 : 2
            values[row==1 ? 1 : 3]=floatmin(Float64);values[slot]=floatmax(Float64)
        end
        U=SparseMatrixCSC(3,3,[1,2,4,7],[1,1,2,1,2,3],values);before=(copy(U.colptr),copy(U.rowval),bits(U.nzval));normalize=label!==:normalize_false
        ref=copy(U);rd=normalize ? J._direct_normalize_upper!(ref) : nothing;rp=J._direct_packed_upper(ref,J.BartelsGolubFactorization)
        cp,cd=J._bgxs_import_upper(U,normalize);J._bgxsp_reset!();pp,pd=J._bgxsp_import_upper(U,normalize)
        tupleof(v)=[(collect(x.indices),bits(x.values)) for x in v]
        require(isequal(tupleof(rp),tupleof(cp)) && isequal(tupleof(rp),tupleof(pp)) && isnothing(rd) && isnothing(cd) && isnothing(pd),"Importer controls")
        require((U.colptr,U.rowval,bits(U.nzval))==before,"Control input mutation")
        push!(imports,Dict("name"=>string(label),"correct"=>true,"u"=>nnz(U),"counts"=>copy(J._bgxsp_counts)))
    end
    transitions=Dict[]
    large=only(f for f in fixtures if f.name=="dense96");small=only(f for f in fixtures if f.name=="dense32")
    for backend in (Val(:native),Val(:markowitz))
        r=factory(Val(:reference),J.BartelsGolubFactorization,large.matrices[1],backend);c=factory(Val(:candidate),J.BartelsGolubFactorization,large.matrices[1],backend)
        sr=J.copy_basis_factorization(r);sc=J.copy_basis_factorization(c)
        require(isnothing(sc.workspace) && sr!==r && sc.inner!==c.inner,"Cold copy empty cache")
        saved=packed_state(sc);states=Dict[]
        for (label,B) in (("same_shape",large.matrices[1]),("large_to_small",small.matrices[1]))
            J.refactorize!(r,B);J.refactorize!(c,B)
            require(isequal(packed_state(r),packed_state(c)) && isequal(packed_state(sc),saved),"Transition state/copy preservation")
            push!(states,Dict("name"=>label,"cache"=>cache_record(c),"graphs"=>[Base.summarysize(r),Base.summarysize(c)],"coexistence_graph"=>Base.summarysize((r,c,sr,sc))))
        end
        J.refactorize!(sr,large.matrices[1]);J.refactorize!(sc,large.matrices[1]);require(isequal(packed_state(sr),packed_state(sc)),"Copy independent refactor")
        push!(transitions,Dict("backend"=>backend===Val(:native) ? "native" : "markowitz","states"=>states,"copy_cache"=>cache_record(sc),"constructions"=>2,"copies"=>2,"refactors"=>6,"explicit_solves"=>0))
    end
    require(isequal(original_inputs,snapshot_inputs()),"Control matrices changed")
    return Dict("complete"=>true,"inputs_unchanged"=>true,"orientation_synthetic_calls"=>1,"orientation_requests"=>2,"orientation_payload"=>16*n,
        "imports"=>imports,"transitions"=>transitions,"constructions"=>4,"copies"=>4,"refactors"=>12,"explicit_solves"=>0)
end
