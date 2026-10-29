using Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML, Libdl
include(joinpath(@__DIR__,"vendor/KLU/src/KLU.jl"))
include(joinpath(@__DIR__,"graph.jl"))
const D=@__DIR__
const COUNTS=Dict("factorizations"=>0,"combined_extracts"=>0,"basis_solves"=>0,"identity_probes"=>0)
const WITNESS_BYTES=Ref(0)
function digestarrays(a...)
    io=IOBuffer();for v in a;write(io,Int(length(v)));write(io,v);end;bytes2hex(sha256(take!(io)))
end
matrixhash(B)=digestarrays(B.colptr,B.rowval,B.nzval)
function assemble(A,basis)
    n,m=size(A);ptr=Int[1];rows=Int[];vals=Float64[]
    for e in basis
        if e<=m
            for k in nzrange(A,e);push!(rows,A.rowval[k]);push!(vals,A.nzval[k]);end
        else
            1<=e-m<=n || error("artificial basis column");push!(rows,e-m);push!(vals,-1.)
        end
        push!(ptr,length(rows)+1)
    end
    SparseMatrixCSC(n,n,ptr,rows,vals)
end
function inputcolumn(A,e)
    n,m=size(A)
    e<=m ? (copy(A.rowval[nzrange(A,e)]),copy(A.nzval[nzrange(A,e)])) : ([e-m],[-1.])
end
function factor(B)
    f=KLU.KLUFactorization(B);f.common.tol=1.;f.common.btf=1;f.common.ordering=0;f.common.scale=1;f.common.maxwork=10.
    KLU.klu_factor!(f);COUNTS["factorizations"]+=1;f
end
function export_once(f)
    n=f.n;b=f.nblocks
    Lp=Vector{Int}(undef,n+1);Li=Vector{Int}(undef,f.lnz);Lx=Vector{Float64}(undef,f.lnz)
    Up=similar(Lp);Ui=Vector{Int}(undef,f.unz);Ux=Vector{Float64}(undef,f.unz)
    Fp=similar(Lp);Fi=Vector{Int}(undef,f.nzoff);Fx=Vector{Float64}(undef,f.nzoff)
    P=Vector{Int}(undef,n);Q=similar(P);R=Vector{Int}(undef,b+1);Rs=Vector{Float64}(undef,n)
    if isempty(Fi)
        fill!(Fp,0);KLU._extract!(f;Lp,Li,Lx,Up,Ui,Ux,P,Q,R,Rs)
    else
        KLU._extract!(f;Lp,Li,Lx,Up,Ui,Ux,Fp,Fi,Fx,P,Q,R,Rs)
    end
    COUNTS["combined_extracts"]+=1
    for v in (Lp,Li,Up,Ui,Fp,Fi,P,Q,R);v .+= 1;end
    (Lp=Lp,Li=Li,Lx=Lx,Up=Up,Ui=Ui,Ux=Ux,Fp=Fp,Fi=Fi,Fx=Fx,P=P,Q=Q,R=R,Rs=Rs)
end
function csc_action(ptr,rows,vals,v,n)
    out=zeros(n)
    for j in 1:n,k in ptr[j]:(ptr[j+1]-1);out[rows[k]]+=vals[k]*v[j];end
    out
end
function deltas(B,row,er,ev)
    old=Dict(B.rowval[k]=>B.nzval[k] for k in nzrange(B,row));new=Dict(er[i]=>ev[i] for i in eachindex(er))
    rows=sort!(collect(union(keys(old),keys(new))))
    rows,[get(old,r,0.) for r in rows],[get(new,r,0.) for r in rows]
end
function witness(io,state,n,dims,lu,g,rb,cb,enter_rows,row,dr,ov,nv)
    nb=length(dims);nf=length(g.target)
    # 8 Int64 header fields followed by explicitly sized little-endian primitive arrays.
    header=Int64[state,n,nb,nf,length(enter_rows),row,length(dr),0]
    arrays=(dims,lu,g.ptr,g.target,rb,cb,enter_rows,dr)
    bytes=64+4*sum(length,arrays)+length(g.nonzero)+8*(length(ov)+length(nv))
    WITNESS_BYTES[]+bytes<=512*1024^2 || error("witness512MiB cap")
    write(io,header)
    for v in (dims,lu,g.ptr,g.target);write(io,Int32.(v));end
    write(io,g.nonzero)
    for v in (rb,cb,enter_rows,dr);write(io,Int32.(v));end
    write(io,ov);write(io,nv);WITNESS_BYTES[]+=bytes
end
function profile(A,basis,row,enter,id,state,io,anchors)
    B=assemble(A,basis);n=size(B,1);before=matrixhash(B);er,ev=inputcolumn(A,enter)
    @test all(isfinite,B.nzval) && all(isfinite,ev)
    f=factor(B);x=export_once(f);nb=length(x.R)-1
    @test x.R[1]==1 && x.R[end]==n+1 && all(>(0),diff(x.R))
    @test sort(x.P)==collect(1:n) && sort(x.Q)==collect(1:n)
    @test all(isfinite,x.Lx) && all(isfinite,x.Ux) && all(isfinite,x.Fx) && all(v->isfinite(v)&&v>0,x.Rs)
    @test length(x.Li)+length(x.Ui)+length(x.Fi)<=5_000_000
    block=zeros(Int,n);rb=zeros(Int,n);cb=zeros(Int,n);dims=diff(x.R);lu=zeros(Int,nb)
    for b in 1:nb,k in x.R[b]:(x.R[b+1]-1)
        block[k]=b;rb[x.P[k]]=b;cb[x.Q[k]]=b
        lu[b]+=x.Lp[k+1]-x.Lp[k]+x.Up[k+1]-x.Up[k]
    end
    @test all(block[x.Li[k]]==block[j] for j in 1:n for k in x.Lp[j]:(x.Lp[j+1]-1))
    @test all(block[x.Ui[k]]==block[j] for j in 1:n for k in x.Up[j]:(x.Up[j+1]-1))
    @test all(x.Ui[x.Up[j+1]-1]==j && !iszero(x.Ux[x.Up[j+1]-1]) for j in 1:n)
    @test all(block[x.Fi[k]]<block[j] for j in 1:n for k in x.Fp[j]:(x.Fp[j+1]-1))
    # A combined extraction preserves the same permuted/scaled matrix identity.
    point=[(-1.)^i*(1+mod(i,13))/16 for i in 1:n];z=point[x.Q]
    uy=csc_action(x.Up,x.Ui,x.Ux,z,n);left=csc_action(x.Lp,x.Li,x.Lx,uy,n)+csc_action(x.Fp,x.Fi,x.Fx,z,n)
    right=(B*point)[x.P]./x.Rs;ident=norm(left-right,Inf)/max(1.,norm(right,Inf));COUNTS["identity_probes"]+=1
    @test ident<=min(1e-10,128*n*eps(Float64))
    g=BlockCSR([x.Fp[k] for k in x.R],block[x.Fi],UInt8[!iszero(v) for v in x.Fx]);rg=reverse_graph(g)
    support=[er[k] for k in eachindex(er) if !iszero(ev[k])]
    @test all(i->1<=i<=n,support)
    sf=unique(rb[support]);sb=[cb[row]]
    F=measure_reach(g,rg,dims,lu,sf,false);T=measure_reach(g,rg,dims,lu,sb,true)
    dr,ov,nv=deltas(B,row,er,ev);change=classify_change(rb,cb[row],dr,ov,nv);change["leaving_block_dimension"]=dims[cb[row]]
    @test matrixhash(B)==before
    if state in (0,80,160)
        a=anchors[id*"-B"*string(state)]
        @test a["matrix_hash"]==before && a["L_nnz"]+a["U_nnz"]==sum(lu) && a["F_nnz"]==length(x.Fi)
        @test a["blocks"]==nb && a["max_block"]==maximum(dims)
    end
    witness(io,state,n,dims,lu,g,rb,cb,support,row,dr,ov,nv)
    # Canonical column-group tokens permit comparisons across changing block numbering.
    token=zeros(Int,n)
    for b in 1:nb
        cols=@view x.Q[x.R[b]:(x.R[b+1]-1)];root=minimum(cols)
        for c in cols;token[c]=root;end
    end
    record=Dict("history"=>id,"state"=>state,"n"=>n,"B_nnz"=>nnz(B),"matrix_hash"=>before,
        "blocks"=>nb,"largest_block"=>maximum(dims),"LU_stored"=>sum(lu),"LU_visits"=>sum(lu)-n,"F_stored"=>length(g.target),
        "full_coefficient_visits"=>sum(lu)-n+length(g.target),"identity_error"=>ident,
        "entering_nonzeros"=>length(support),"FTRAN"=>F,"BTRAN"=>T,"change"=>change,
        "dense_rhs_active_fraction"=>1.,"CSR_graph_payload_bytes"=>8*(length(g.ptr)+length(g.target)+length(rg.ptr)+length(rg.target))+length(g.nonzero)+length(rg.nonzero),
        "block_weight_map_payload_bytes"=>8*(length(rb)+length(cb)+length(dims)+length(lu)),
        "factor_native_bytes"=>Int(f.common.memusage))
    record,token
end
function main(out,root)
    @assert sizeof(Int)==8 && ENDIAN_BOM==0x04030201 && Threads.nthreads()==1 && BLAS.get_num_threads()==1
    version=zeros(Cint,3);ccall((:klu_version,KLU.libklu),Cint,(Ptr{Cint},),version);@assert version==[2,3,5]
    ispath(root) && error("fresh witnesses required");mkpath(root)
    prior=TOML.parsefile(joinpath(D,"prior-results.toml"));anchors=Dict{String,Any}()
    for q in prior["qualification"]
        if startswith(q["arm"],"KLU")
            c=only(filter(v->v["id"]==q["case"],prior["cases"]));a=copy(q["metadata"]);a["matrix_hash"]=c["matrix_sha256"];a["F_nnz"]=a["coupling_nnz"];anchors[q["case"]]=a
        end
    end
    result=Dict{String,Any}("scope"=>"structural reach on freshly factored captured bases; not update admission or timing benchmark","profiles"=>Any[],"witnesses"=>Any[],"counts"=>COUNTS)
    @testset "KLU block reach on captured exchanges" begin
        graph_tests()
        for entry in TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
            entry["structural_only"] && continue
            @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
            d=deserialize(entry["path"]);A=d.A;n,m=size(A);basis=copy(d.basis)
            @test length(basis)==n && length(unique(basis))==n && length(d.steps)>=161 && d.input_sha256==entry["input_sha256"]
            inputhash=digestarrays(A.colptr,A.rowval,A.nzval,basis);flags=falses(m+n);flags[basis].=true
            path=joinpath(root,entry["id"]*".bin");lasttoken=nothing
            ispath(path) && error("witness path already exists")
            open(path,"w") do io
                write(io,codeunits("KREACH01"));WITNESS_BYTES[]+=8
                for state in 0:160
                    if state>0
                        row,enter=d.steps[state];@test !flags[enter]
                        flags[basis[row]]=false;flags[enter]=true;basis[row]=enter
                    end
                    row,enter=d.steps[state+1];@test !flags[enter]
                    rec,token=profile(A,basis,row,enter,entry["id"],state,io,anchors)
                    rec["partition_token_changed_column_slots"]=lasttoken===nothing ? 0 : count(i->lasttoken[i]!=token[i],eachindex(token))
                    lasttoken=token;push!(result["profiles"],rec)
                    state%8==0 && GC.gc()
                    if state%40==0;println(entry["id"]," state ",state," of160");flush(stdout);end
                end
            end
            push!(result["witnesses"],Dict("path"=>path,"sha256"=>bytes2hex(open(sha256,path)),"bytes"=>filesize(path)))
            @test digestarrays(A.colptr,A.rowval,A.nzval,d.basis)==inputhash
            open(out,"w") do io;TOML.print(io,result);end
        end
        @test COUNTS==Dict("factorizations"=>483,"combined_extracts"=>483,"basis_solves"=>0,"identity_probes"=>483)
        @test length(result["profiles"])==483
        result["witness_bytes"]=WITNESS_BYTES[];result["completed"]=true
        result["loaded_libraries"]=[realpath(p) for p in Libdl.dllist() if any(s->occursin(s,basename(p)),("libklu.","libbtf.","libumfpack.","libamd.","libcolamd.","libsuitesparseconfig."))]
        expected=TOML.parsefile(joinpath(D,"library-pins.toml"))["libraries"]
        @test all(p->haskey(expected,p)&&bytes2hex(open(sha256,p))==expected[p],result["loaded_libraries"])
        open(out,"w") do io;TOML.print(io,result);end
    end
end
main(abspath(ARGS[1]),abspath(ARGS[2]))
