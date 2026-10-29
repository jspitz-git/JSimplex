using Test, LinearAlgebra, SparseArrays, Serialization, SHA, Statistics, TOML, Libdl
include(joinpath(@__DIR__,"vendor/KLU/src/KLU.jl"))
const D=@__DIR__
const U=SparseArrays.UMFPACK
const LS=SparseArrays.LibSuiteSparse
const ARMS=(Val(:umf),Val(:klu))
label(::Val{:umf})="UMFPACK-one"
label(::Val{:klu})="KLU-BTF-AMD-one"
const COUNTS=Dict("builds"=>0,"forward"=>0,"transpose"=>0)

function makefactor(::Val{:umf},B)
    c=U.get_umfpack_control(Float64,Int)
    c[LS.UMFPACK_PIVOT_TOLERANCE+1]=1.
    c[LS.UMFPACK_IRSTEP+1]=0.
    lu(B;control=c)
end
function makefactor(::Val{:klu},B)
    f=KLU.KLUFactorization(B) # copies CSC indices AND values; unlike convenience klu(B)
    f.common.tol=1.;f.common.btf=1;f.common.ordering=0;f.common.scale=1;f.common.maxwork=10.
    KLU.klu_factor!(f)
end
forward!(::Val{:umf},x,f,b)=ldiv!(x,f,b)
backward!(::Val{:umf},x,f,b)=ldiv!(x,transpose(f),b)
function forward!(::Val{:klu},x,f,b)
    copyto!(x,b);KLU.solve!(f,x)
end
function backward!(::Val{:klu},x,f,b)
    copyto!(x,b);KLU.solve!(transpose(f),x)
end
function hasharrays(arrays...)
    io=IOBuffer()
    for a in arrays;write(io,Int(length(a)));write(io,a);end
    bytes2hex(sha256(take!(io)))
end
matrixhash(B)=hasharrays(B.colptr,B.rowval,B.nzval)
function stat(t)
    Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
         "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function rss()
    r=Dict{String,Int}()
    for line in eachline("/proc/self/status")
        a=split(line)
        a[1] in ("VmRSS:","VmHWM:","VmPeak:","VmSwap:") && (r[chop(a[1])]=parse(Int,a[2])*1024)
    end
    r
end
function doforward(arm,f,x,y,b,c,repeats)
    for _ in 1:repeats;forward!(arm,x,f,b);forward!(arm,y,f,c);end
    nothing
end
function dobackward(arm,f,x,b,repeats)
    for _ in 1:repeats;backward!(arm,x,f,b);end
    nothing
end
function residual(B,x,b,tr=false)
    all(isfinite,x) || return Inf
    q=tr ? transpose(B)*x : B*x
    norm(q-b,Inf)/max(1.,opnorm(B,tr ? 1 : Inf)*norm(x,Inf),norm(b,Inf))
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
function metadata(::Val{:umf},f,B)
    L,V=f.L,f.U;s=f.Rs
    scale_max=maximum(abs(B.nzval[k]*s[B.rowval[k]]) for k in eachindex(B.nzval))
    growth=maximum(abs,V.nzval)/scale_max
    value(name)=f.info[getproperty(LS,name)+1]
    unit=value(:UMFPACK_SIZE_OF_UNIT)
    Dict("L_nnz"=>nnz(L),"U_nnz"=>nnz(V),"coupling_nnz"=>0,"growth"=>growth,
        "native_current_bytes"=>round(Int,unit*(value(:UMFPACK_NUMERIC_SIZE)+value(:UMFPACK_SYMBOLIC_SIZE))),
        "native_peak_bytes"=>round(Int,unit*value(:UMFPACK_PEAK_MEMORY)),
        "native_size_unit"=>unit,"control"=>copy(f.control),"julia_graph_bytes"=>Base.summarysize(f),
        "blocks"=>-1,"max_block"=>-1,"input_values_independent"=>!Base.mightalias(f.nzval,B.nzval))
end
function metadata(::Val{:klu},f,B)
    # Native factor stats before diagnostic extraction/sorting, outside all windows.
    c=f.common;native_current=Int(c.memusage);native_peak=Int(c.mempeak)
    L,V,C=f.L,f.U,f.F;s=f.Rs;p=f.p # five property extracts; F remains separate
    original_scale=similar(s)
    for k in eachindex(p);original_scale[p[k]]=s[k];end
    scale_max=maximum(abs(B.nzval[k]/original_scale[B.rowval[k]]) for k in eachindex(B.nzval))
    Dict("L_nnz"=>nnz(L),"U_nnz"=>nnz(V),"coupling_nnz"=>nnz(C),
        "growth"=>maximum(abs,V.nzval)/scale_max,"blocks"=>f.nblocks,"max_block"=>f.maxblock,
        "native_current_bytes"=>native_current,"native_peak_bytes"=>native_peak,
        "julia_graph_bytes"=>Base.summarysize(f),"input_values_independent"=>!Base.mightalias(f.nzval,B.nzval),
        "control"=>Dict("tol"=>c.tol,"btf"=>Int(c.btf),"ordering"=>Int(c.ordering),"scale"=>Int(c.scale),"maxwork"=>c.maxwork),
        "matching_work"=>c.work,"status"=>Int(c.status))
end
function assemble(A,basis)
    n,m=size(A);ptr=Int[1];rows=Int[];values=Float64[]
    for e in basis
        if e<=m
            for k in nzrange(A,e);push!(rows,A.rowval[k]);push!(values,A.nzval[k]);end
        else
            1<=e-m<=n || error("invalid artificial column");push!(rows,e-m);push!(values,-1.)
        end
        push!(ptr,length(rows)+1)
    end
    SparseMatrixCSC(n,n,ptr,rows,values)
end
function rhscolumn(A,e)
    n,m=size(A);b=zeros(n)
    if e<=m
        for k in nzrange(A,e);b[A.rowval[k]]=A.nzval[k];end
    else
        1<=e-m<=n || error("invalid artificial RHS");b[e-m]=-1.
    end
    b
end
function makecase(id,B,a,row;expected_blocks=0)
    n=size(B,1);b=[(-1.)^i*(1+mod(i,17))/16 for i in 1:n];u=zeros(n);u[row]=1.
    (id=id,B=B,a=a,b=b,u=u,expected_blocks=expected_blocks,hash=matrixhash(B),rhs_hash=hasharrays(a,b,u),
     tolerance=min(1e-10,128*n*eps(Float64)))
end
function cases()
    out=[]
    for e in TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
        e["structural_only"] && continue
        @test bytes2hex(open(sha256,e["path"]))==e["sha256"]
        d=deserialize(e["path"]);A=d.A;n,m=size(A);basis=copy(d.basis)
        @test A isa SparseMatrixCSC{Float64,Int} && all(isfinite,A.nzval)
        @test length(basis)==n && length(unique(basis))==n && length(d.steps)>=161
        @test d.input_sha256==e["input_sha256"]
        flags=falses(m+n);flags[basis].=true
        for t in 0:160
            if t>0
                j,k=d.steps[t];@test flags[basis[j]] && !flags[k]
                flags[basis[j]]=false;flags[k]=true;basis[j]=k
            end
            if t in (0,80,160)
                row,enter=d.steps[t+1]
                push!(out,makecase(e["id"]*"-B"*string(t),assemble(A,basis),rhscolumn(A,enter),row))
            end
        end
    end
    n=256
    # A cycle connects every vertex: known irreducible exact pattern.
    S=spdiagm(0=>fill(8.,n),1=>fill(-.25,n-1));S[n,1]=.125
    push!(out,makecase("irreducible-sparse256",S,ones(n),17;expected_blocks=1))
    H=sparse([i==j ? 8. : (1+mod(i*7+j*11,5))/4096 for i in 1:n,j in 1:n])
    push!(out,makecase("irreducible-dense256",H,ones(n),17;expected_blocks=1))
    T=spzeros(n,n)
    for block in 0:31,i in 1:8,j in 1:8
        T[8block+i,8block+j]=i==j ? 8. : (1+mod(i*3+j*5,5))/256
    end
    for j in 9:n;T[j-8,j]=-.125;end
    push!(out,makecase("coupled-blocks256",T,ones(n),17;expected_blocks=32))
    out
end
function qualify(arm,c)
    B=c.B;GC.gc();before=rss();f=makefactor(arm,B);COUNTS["builds"]+=1
    GC.gc();held=rss();meta=metadata(arm,f,B)
    x=zeros(size(B,1));y=similar(x);z=similar(x)
    forward!(arm,x,f,c.a);forward!(arm,y,f,c.b);backward!(arm,z,f,c.u)
    COUNTS["forward"]+=2;COUNTS["transpose"]+=1
    r=[residual(B,x,c.a),residual(B,y,c.b),residual(B,z,c.u,true)]
    encl=[enclosure(B,x,c.a,c.tolerance),enclosure(B,y,c.b,c.tolerance),enclosure(B,z,c.u,c.tolerance,true)]
    # Two known-point RHS additionally exercise forward/transpose semantics.
    point=[(-1.)^i*(1+mod(i,13))/16 for i in 1:size(B,1)]
    k1=B*point;k2=transpose(B)*point
    forward!(arm,x,f,k1);backward!(arm,y,f,k2);COUNTS["forward"]+=1;COUNTS["transpose"]+=1
    known=[norm(x-point,Inf)/max(1.,norm(point,Inf)),norm(y-point,Inf)/max(1.,norm(point,Inf))]
    ok=all(v->isfinite(v)&&v<=c.tolerance,r) && all(e->e.passed,encl) && all(v->isfinite(v)&&v<=1e-6,known) &&
       meta["growth"]<=1e8 && meta["L_nnz"]+meta["U_nnz"]+meta["coupling_nnz"]<=5_000_000 && meta["input_values_independent"]
    @test ok
    @test matrixhash(B)==c.hash && hasharrays(c.a,c.b,c.u)==c.rhs_hash
    if arm===Val(:klu) && c.expected_blocks>0
        @test meta["blocks"]==c.expected_blocks
        @test c.expected_blocks!=1 || (meta["max_block"]==size(B,1) && meta["coupling_nnz"]==0)
    end
    q=Dict("case"=>c.id,"arm"=>label(arm),"passed"=>ok,"residuals"=>r,"known_point_error"=>known,
        "directed"=>[Dict("passed"=>e.passed,"residual_upper"=>e.residual_upper,"allowed_lower"=>e.allowed_lower) for e in encl],
        "metadata"=>meta,"rss_before"=>before,"rss_factor_held"=>held)
    f=nothing;GC.gc();q["rss_after_release"]=rss()
    q
end
function sample(arm,c,repeats)
    GC.gc() # outside windows, before each whole factor+solve sample
    t=@timed makefactor(arm,c.B);f=t.value;COUNTS["builds"]+=1
    x=zeros(size(c.B,1));y=similar(x);z=similar(x)
    ft=@timed doforward(arm,f,x,y,c.a,c.b,repeats)
    bt=@timed dobackward(arm,f,z,c.u,repeats)
    COUNTS["forward"]+=2repeats;COUNTS["transpose"]+=repeats
    r=[residual(c.B,x,c.a),residual(c.B,y,c.b),residual(c.B,z,c.u,true)]
    @test all(v->isfinite(v)&&v<=c.tolerance,r)
    @test matrixhash(c.B)==c.hash && hasharrays(c.a,c.b,c.u)==c.rhs_hash
    Dict("factor"=>stat(t),"ftran"=>stat(ft),"btran"=>stat(bt),"residuals"=>r,
        "output_hash"=>hasharrays(x,y,z),"forward_calls"=>2repeats,"transpose_calls"=>repeats)
end
function ownership_tests()
    for arm in ARMS
        B=sparse([4. 1.;1. 3.]);f=makefactor(arm,B);COUNTS["builds"]+=1
        B.nzval .= 999.;x=zeros(2);forward!(arm,x,f,[1.,2.]);COUNTS["forward"]+=1
        @test isapprox(x,[1/11,7/11];rtol=1e-14,atol=1e-14)
        @test_throws SingularException makefactor(arm,sparse([1. 1.;1. 1.]))
        COUNTS["builds"]+=1
    end
end
function save(out,result)
    open(out,"w") do io;TOML.print(io,result);end
end
function main(out)
    @assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
    version=zeros(Cint,3);ccall((:klu_version,KLU.libklu),Cint,(Ptr{Cint},),version)
    @assert version==[2,3,5]
    result=Dict{String,Any}("scope"=>"fixed-basis backend comparison, not simplex/update speedup", "KLU_version"=>Int.(version),
        "qualification"=>Any[],"samples"=>Any[],"preparation"=>Any[],"counts"=>COUNTS)
    @testset "KLU versus UMFPACK on fixed saved bases" begin
        ownership_tests()
        pt=@timed cases();cs=pt.value;push!(result["preparation"],merge(stat(pt),Dict("stage"=>"load-and-assemble-all-bases")))
        @test length(cs)==12
        result["cases"]=[Dict("id"=>c.id,"n"=>size(c.B,1),"nnz"=>nnz(c.B),"matrix_sha256"=>c.hash,"rhs_sha256"=>c.rhs_hash,"tolerance"=>c.tolerance) for c in cs]
        for c in cs
            println("CASE ",c.id);flush(stdout)
            quals=[qualify(a,c) for a in ARMS];append!(result["qualification"],quals);save(out,result)
            all(q->q["passed"],quals) || continue
            # Two complete warm factor/solve pairs, then five alternating measured pairs.
            for round in 1:7
                order=isodd(round) ? ARMS : reverse(ARMS)
                for arm in order
                    v=sample(arm,c,round<=2 ? 8 : 32)
                    merge!(v,Dict("case"=>c.id,"arm"=>label(arm),"round"=>round,"measured"=>round>2))
                    push!(result["samples"],v)
                    if round>2
                        @test all(k->v[k]["compile_seconds"]==0 && v[k]["recompile_seconds"]==0,("factor","ftran","btran"))
                    end
                end
            end
            save(out,result)
        end
        result["loaded_libraries"]=[realpath(p) for p in Libdl.dllist() if any(s->occursin(s,basename(p)),("libklu.","libbtf.","libumfpack.","libamd.","libcolamd.","libsuitesparseconfig."))]
        expected=TOML.parsefile(joinpath(D,"library-pins.toml"))["libraries"]
        @test all(p->haskey(expected,p) && bytes2hex(open(sha256,p))==expected[p],result["loaded_libraries"])
        @test any(p->occursin("libklu",basename(p)),result["loaded_libraries"])
        result["completed"]=true;save(out,result)
    end
end
main(abspath(only(ARGS)))
