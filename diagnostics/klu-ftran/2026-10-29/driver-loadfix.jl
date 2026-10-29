using Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML, Libdl
include(joinpath(@__DIR__,"vendor/KLU/src/KLU.jl"))
include(joinpath(@__DIR__,"export.jl"))
include(joinpath(@__DIR__,"candidate-loadfix.jl"))
const D=@__DIR__
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
function enclosure(B,x,b,tol,tr=false)
    setprecision(BigFloat,256) do
        xx=BigFloat.(x);bb=BigFloat.(b)
        bounds=map((RoundDown,RoundUp)) do mode
            setrounding(BigFloat,mode) do
                r=-bb
                for j in 1:size(B,2),k in nzrange(B,j)
                    i=B.rowval[k];target,source=tr ? (j,i) : (i,j)
                    r[target]+=BigFloat(B.nzval[k])*xx[source]
                end
                r
            end
        end
        high=maximum(i->max(abs(bounds[1][i]),abs(bounds[2][i])),eachindex(bb))
        low=setrounding(BigFloat,RoundDown) do
            sums=zeros(BigFloat,size(B,1))
            for j in 1:size(B,2),k in nzrange(B,j)
                sums[tr ? j : B.rowval[k]]+=abs(BigFloat(B.nzval[k]))
            end
            BigFloat(tol)*max(BigFloat(1),maximum(sums)*maximum(abs,xx),maximum(abs,bb))
        end
        (passed=high<=low,residual_upper=Float64(high,RoundUp),allowed_lower=Float64(low,RoundDown))
    end
end
function stat(t)
    Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
partshash(c::NativeOnly)="native-only"
partshash(c::GraphContext)=digestarrays(values(c.parts)...)
function memory(c)
    payload=c isa GraphContext ? sum(sizeof,values(c.parts))+sum(sizeof,(c.rowpos,c.block,c.weights,c.work,c.marks,c.heap,c.rhs)) : sizeof(c.rhs)
    Dict("owned_export_and_scratch_payload_bytes"=>payload,"wrapper_julia_graph_bytes"=>Base.summarysize(c),"native_reported_bytes"=>Int(c.native.common.memusage),"graph_eligible"=>c isa GraphContext,"blocks"=>c.native.nblocks)
end
function residual(B,x,rhs,bnorm)
    all(isfinite,x) || return Inf
    norm(B*x-rhs,Inf)/max(1.,bnorm*norm(x,Inf),norm(rhs,Inf))
end
function batch!(dest,c,A,queries,mode,repeats)
    paths=zeros(Int,7);blocks=0;weight=0;checksum=0.
    for r in 1:repeats,(i,e) in enumerate(queries)
        column_ftran!(dest,c,A,e,mode)
        paths[c.last_path]+=1;blocks+=c.last_blocks;weight+=c.last_weight
        checksum+=dest[1+mod(i+r-2,length(dest))]
    end
    (paths=paths,blocks=blocks,weight=weight,checksum=checksum)
end
function microtests()
    B=spdiagm(0=>ones(50),1=>fill(.125,49));A=sparse([50,1],[1,2],[1.,1.],50,2)
    c=prepare(B;minimum_dimension=0);r=prepare(B);x=zeros(50);y=zeros(50);z=zeros(50)
    @test c isa GraphContext
    column_ftran!(x,c,A,2,Val(:local));@test c.last_path==1 && c.last_blocks==1
    column_ftran!(y,c,A,2,Val(:full));@test x==y
    column_ftran!(x,c,A,1,Val(:local));@test c.last_path==4 && 0<c.last_blocks<50
    column_ftran!(y,r,A,1,Val(:local));@test x==y
    c.epoch=typemax(UInt32);column_ftran!(x,c,A,2,Val(:local));@test c.epoch==1 && x[1]==1.
    snap=partshash(c);source=matrixhash(A)
    @test_throws ArgumentError column_ftran!(c.work,c,A,1,Val(:local))
    @test_throws ArgumentError column_ftran!(c.rhs,c,A,1,Val(:local))
    vals=ones(100);aliasA=SparseMatrixCSC(50,1,[1,51],collect(1:50),vals[1:50])
    GC.@preserve aliasA begin
        v=unsafe_wrap(Vector{Float64},pointer(aliasA.nzval)+8,49;own=false)
        # A destination of correct length with overlapping storage, independently owned backing.
        owner=ones(101);src=unsafe_wrap(Vector{Float64},pointer(owner),50;own=false)
        dst=unsafe_wrap(Vector{Float64},pointer(owner)+8,50;own=false)
        aliasB=SparseMatrixCSC(50,1,[1,51],collect(1:50),src)
        GC.@preserve owner src dst aliasB begin
            @test_throws ArgumentError column_ftran!(dst,c,aliasB,1,Val(:local))
            @test all(==(1.),owner)
        end
    end
    @test snap==partshash(c) && source==matrixhash(A)
    @test_throws SingularException replace_native!(c,spzeros(50,50))
    @test c.valid && snap==partshash(c)
    replace_native!(c,2B);column_ftran!(x,c,A,2,Val(:local));@test c.last_path==6 && x[1]==.5
    c2=prepare(B;minimum_dimension=0);@test !overlaps(c.work,c2.work) && !overlaps(c.rhs,c2.rhs)
    column_ftran!(x,c2,A,2,Val(:local));@test c2.last_path==1 && x[1]==1.
    for value in (-0.,Inf,NaN)
        aa=sparse([1],[1],[value],50,1);column_ftran!(x,c2,aa,1,Val(:local));@test c2.last_path==5
        column_ftran!(y,r,aa,1,Val(:local));@test all(isequal.(x,y))
    end
    tiny=spdiagm(0=>fill(1e-308,50));tc=prepare(tiny;minimum_dimension=0)
    aa=sparse([1],[1],[1e308],50,1);column_ftran!(x,tc,aa,1,Val(:local));@test tc.last_path==5
    aa.nzval[1]=1e-308;column_ftran!(x,tc,aa,1,Val(:local));@test tc.last_path==1 && x[1]==1.
    dense_ftran!(x,c2,ones(50));@test c2.last_path==3 && residual(B,x,ones(50),opnorm(B,Inf))<1e-12
    denseA=sparse(reshape(ones(50),50,1))
    column_ftran!(x,c2,denseA,1,Val(:local));@test c2.last_path==3
    column_ftran!(y,r,denseA,1,Val(:local));@test x==y
    @test_throws ArgumentError dense_ftran!(c2.work,c2,ones(50))
    column_ftran!(x,c2,A,2,Val(:local));bad=copy(x);bad[1]+=1
    @test residual(B,bad,c2.rhs,opnorm(B,Inf))>1e-5
    @test_throws DimensionMismatch column_ftran!(zeros(3),c2,A,1,Val(:local))
    @test_throws BoundsError column_ftran!(x,c2,A,0,Val(:local))
end
function qualifycase(B,A,queries,id,result;minimum_dimension=4096)
    GC.gc();tr=@timed prepare(B;minimum_dimension=typemax(Int));ref=tr.value
    tc=@timed prepare(B;minimum_dimension);c=tc.value
    n=size(B,1);tol=min(1e-10,128*n*eps(Float64));bnorm=opnorm(B,Inf)
    ah=matrixhash(A);bh=matrixhash(B);ph=partshash(c)
    xr=zeros(n);xf=zeros(n);xl=zeros(n);routes=zeros(Int,7);zero_sign_differences=0
    maxres=0.;maxdiff=0.;enclosures=Any[]
    for cycle in 1:2,(i,e) in enumerate(queries)
        column_ftran!(xr,ref,A,e,Val(:local));column_ftran!(xf,c,A,e,Val(:full));column_ftran!(xl,c,A,e,Val(:local))
        routes[c.last_path]+=1
        for v in (xr,xf,xl)
            q=residual(B,v,ref.rhs,bnorm);@test q<=tol;maxres=max(maxres,q)
        end
        delta=norm(xr-xl,Inf)/max(1.,norm(xr,Inf));@test delta<=1e-6;maxdiff=max(maxdiff,delta)
        if c.last_path==1
            @test all((iszero(a)&&iszero(b))||isequal(a,b) for (a,b) in zip(xf,xl))
            zero_sign_differences+=count(i->iszero(xf[i])&&iszero(xl[i])&&signbit(xf[i])!=signbit(xl[i]),1:n)
        end
        if cycle==1 && i==1
            for (arm,v) in zip(("native","full","local"),(xr,xf,xl))
                q=enclosure(B,v,ref.rhs,tol);@test q.passed
                push!(enclosures,Dict("arm"=>arm,"residual_upper"=>q.residual_upper,"allowed_lower"=>q.allowed_lower))
            end
            GC.gc()
        end
    end
    @test matrixhash(A)==ah && matrixhash(B)==bh && partshash(c)==ph
    record=Dict("id"=>id,"n"=>n,"matrix_hash"=>bh,"queries"=>length(queries),"tolerance"=>tol,"max_scaled_residual"=>maxres,"max_native_relative_difference"=>maxdiff,"qualification_routes"=>routes,"zero_sign_differences"=>zero_sign_differences,"enclosures"=>enclosures,"reference_memory"=>memory(ref),"candidate_memory"=>memory(c),"reference_setup"=>stat(tr),"candidate_setup"=>stat(tc),"samples"=>Any[])
    # Setup samples above deliberately include compilation; a second warm preparation is recorded separately.
    for (arm,minimum) in (("native",typemax(Int)),("candidate",minimum_dimension))
        t=@timed prepare(B;minimum_dimension=minimum)
        push!(result["preparation"],merge(stat(t),Dict("case"=>id,"arm"=>arm,"stage"=>"warm-factor-and-private-context")))
    end
    for round in 1:7
        for offset in 0:2
            arm=mod(round-1+offset,3)+1
            context=arm==1 ? ref : c;dest=arm==1 ? xr : arm==2 ? xf : xl;mode=arm==2 ? Val(:full) : Val(:local)
            t=@timed batch!(dest,context,A,queries,mode,8)
            if round>2
                @test t.compile_time==0 && t.recompile_time==0
                @test isfinite(t.value.checksum)
                push!(record["samples"],merge(stat(t),Dict("arm"=>("native","full","local")[arm],"round"=>round-2,"calls"=>8length(queries),"paths"=>t.value.paths,"processed_blocks"=>t.value.blocks,"processed_weight"=>t.value.weight,"checksum"=>t.value.checksum)))
            end
        end
        round==2 && GC.gc()
    end
    @test matrixhash(A)==ah && matrixhash(B)==bh && partshash(c)==ph
    push!(result["cases"],record)
    println(id," completed; graph eligible=",c isa GraphContext," routes=",routes);flush(stdout)
end
function main(out)
    @assert sizeof(Int)==8 && Threads.nthreads()==1 && BLAS.get_num_threads()==1
    result=Dict{String,Any}("cases"=>Any[],"preparation"=>Any[],"completed"=>false,"schedule"=>"2 warm +5 measured rounds;8 fixed-window repeats;3 rotating arms; actual anchors0/80/160")
    @testset "Fixed-base graph-local FTRAN" begin
        microtests()
        for entry in TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
            entry["structural_only"]&&continue
            @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
            t=@timed deserialize(entry["path"]);d=t.value
            push!(result["preparation"],merge(stat(t),Dict("case"=>entry["id"],"stage"=>"deserialize")))
            A=d.A;basis=copy(d.basis);ah=matrixhash(A);initial=copy(basis)
            @test d.input_sha256==entry["input_sha256"] && length(d.steps)>=161
            for anchor in (0,80,160)
                if anchor>0
                    for state in anchor-79:anchor;row,enter=d.steps[state];basis[row]=enter;end
                end
                t=@timed assemble(A,basis);B=t.value
                push!(result["preparation"],merge(stat(t),Dict("case"=>entry["id"]*"-B"*string(anchor),"stage"=>"assemble-basis")))
                queries=Int[d.steps[state+1][2] for state in anchor:min(anchor+79,160)]
                qualifycase(B,A,queries,entry["id"]*"-B"*string(anchor),result)
                open(out,"w") do io;TOML.print(io,result);end
                GC.gc()
            end
            @test matrixhash(A)==ah && d.basis==initial
            d=nothing;GC.gc()
        end
        n=256;coupled=spdiagm(0=>fill(4.,n),1=>fill(.25,n-1))
        qualifycase(coupled,sparse([1,128,256],[1,2,3],ones(3),n,3),[1,2,3],"coupled256-forced",result;minimum_dimension=0)
        dense=sparse([i==j ? 4. : .01/(1+abs(i-j)) for i in 1:n,j in 1:n])
        qualifycase(dense,sparse(reshape([(-1.)^i/16 for i in 1:n],n,1)),[1],"dense256-native-only",result)
        sparseB=spdiagm(0=>fill(4.,n),1=>fill(.125,n-1),-1=>fill(.125,n-1))
        qualifycase(sparseB,sparse([1,128],[1,2],[1.,1.],n,2),[1,2],"irreducible256-native-only",result)
        @test length(result["cases"])==12 && sum(c["queries"] for c in result["cases"])==489
        result["loaded_libraries"]=[realpath(p) for p in Libdl.dllist() if any(s->occursin(s,basename(p)),("libklu.","libbtf.","libamd.","libcolamd.","libsuitesparseconfig."))]
        expected=TOML.parsefile(joinpath(D,"library-pins.toml"))["libraries"]
        @test all(p->haskey(expected,p)&&bytes2hex(open(sha256,p))==expected[p],result["loaded_libraries"])
        result["completed"]=true
        open(out,"w") do io;TOML.print(io,result);end
    end
end
main(abspath(ARGS[1]))
