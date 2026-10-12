using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl
const JS=JSimplex
struct Timing
    seconds::Float64
    bytes::Int
    allocations::Int
    gc_seconds::Float64
    compile_seconds::Float64
    recompile_seconds::Float64
    valid::Bool
end
Timing()=Timing(0.,0,0,0.,0.,0.,false)
Timing(t)=Timing(t.time,t.bytes,Base.gc_alloc_count(t.gcstats),t.gctime,t.compile_time,t.recompile_time,true)
struct Inputs
    matrices::Vector{SparseMatrixCSC{Float64,Int}}
    bf::Vector{Vector{Float64}}
    bb::Vector{Vector{Float64}}
    incoming::Vector{Vector{Float64}}
end
mutable struct Life
    warm::Bool
    round::Int
    fixture::String
    candidate::Bool
    counts::Vector{Int} # constructor, refactor, update, prepared F, ordinary F, B
    outputs::Vector{Vector{Float64}}
    completed::Int
    timings::Vector{Timing} # outer, first refactor, second refactor
    controls::Vector{UInt64}
    pools::Matrix{Int}
    residuals::Vector{Float64}
    bounds::Vector{Float64}
    checks::Int
    gcpre::Int
    gcpost::Int
    done::Bool
end
Life(w,r,k,c)=Life(w,r,k,c,zeros(Int,6),[fill(NaN,48) for _ in 1:24],0,[Timing() for _ in 1:3],zeros(UInt64,SparseArrays.UMFPACK.UMFPACK_CONTROL),zeros(Int,4,2),fill(NaN,24),fill(NaN,24),0,0,0,false)
const lives=Life[]
const report=Dict{String,Any}("scope"=>"S4-Q fixed-history inclusive GC lifecycle; native retention OPEN","complete"=>false,"source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
bits(v)=string.(reinterpret(UInt64,v);base=16,pad=16)
frombits(v)=reinterpret.(Float64,parse.(UInt64,v;base=16))
function ensure(l::Life,v::Bool,msg::String)
    l.checks+=1
    v || error("S4-Q gate: "*msg)
    nothing
end
function statdict(t::Timing)
    Dict(string(n)=>getfield(t,n) for n in fieldnames(Timing))
end
function save()
    report["lifecycles"]=[Dict("warmup"=>l.warm,"round"=>l.round,"fixture"=>l.fixture,"candidate"=>l.candidate,"counts"=>l.counts,"completed_solves"=>l.completed,"timings"=>statdict.(l.timings),"control_bits"=>string.(l.controls;base=16,pad=16),"pool_records"=>[l.pools[:,i] for i in 1:2],"output_bits"=>[bits(l.outputs[i]) for i in 1:l.completed],"runtime_residuals"=>l.residuals[1:l.completed],"runtime_bounds"=>l.bounds[1:l.completed],"checks"=>l.checks,"gc_pre"=>l.gcpre,"gc_post"=>l.gcpost,"done"=>l.done) for l in lives]
    report["entries"]=Dict("constructor"=>sum(l.counts[1] for l in lives),"refactor"=>sum(l.counts[2] for l in lives),"update"=>sum(l.counts[3] for l in lives),"preparedF"=>sum(l.counts[4] for l in lives),"ordinaryF"=>sum(l.counts[5] for l in lives),"B"=>sum(l.counts[6] for l in lives),"gc_pre"=>sum(l.gcpre for l in lives),"gc_post"=>sum(l.gcpost for l in lives))
    open(ARGS[1],"w") do io;TOML.print(io,report);end
end
function owned(f,B)
    u=f.refactor_workspace
    all(!Base.mightalias(getfield(u,n),getfield(B,n)) for n in (:colptr,:rowval,:nzval))
end
function control!(l,f,initial::Bool)
    c=f.refactor_workspace.control
    ensure(l,length(c)==length(l.controls),"control dimension")
    for i in eachindex(c)
        b=reinterpret(UInt64,c[i])
        if initial;l.controls[i]=b;else;ensure(l,l.controls[i]==b,"control bits");end
    end
    ensure(l,c[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP]==0,"IRSTEP")
    nothing
end
function solve!(l,f,b,mode::Int)
    i=l.completed+1;z=l.outputs[i]
    ensure(l,!Base.mightalias(z,f.work) && !Base.mightalias(z,f.auxiliary),"output ownership")
    l.counts[mode]+=1
    if mode==4
        ensure(l,JS.forward_solve!(z,f,b)===z,"prepared return")
    elseif mode==5
        ensure(l,JS._ordinary_forward_solve!(z,f,b)===z,"ordinary return")
    else
        ensure(l,JS.transpose_solve!(z,f,b)===z,"transpose return")
    end
    l.completed=i
    nothing
end
function refcall!(::Val{false},f,B,l)
    l.counts[2]+=1
    ensure(l,JS.refactorize!(f,B)===f,"refactor return")
    nothing
end
function refcall!(::Val{true},f,B,l)
    l.counts[2]+=1
    ensure(l,JS._s4q_refactorize!(f,B)===f,"refactor return")
    nothing
end
function timedref!(route,f,B,l,slot)
    t=@timed refcall!(route,f,B,l)
    l.timings[slot]=Timing(t)
    ensure(l,t.value===nothing,"inner value")
    l.warm || ensure(l,t.compile_time==0 && t.recompile_time==0,"inner compilation")
    nothing
end
Base.@noinline function owned_history!(route::Val,data::Inputs,l::Life)
    l.counts[1]+=1
    f=JS.HuangfuHallFactorization(data.matrices[1])
    ensure(l,owned(f,data.matrices[1]),"constructor ownership")
    ensure(l,isempty(f.updates) && f.shared_update_count==0,"initial history")
    control!(l,f,true)
    solve!(l,f,data.bf[1],5);solve!(l,f,data.bb[1],6)
    columns=(3,17,31,31,17,3)
    for k in 1:6
        solve!(l,f,data.incoming[k],4)
        z=l.outputs[l.completed]
        ensure(l,f.prepared_valid && isequal(z,f.prepared_direction),"prepared direction")
        l.counts[3]+=1
        ensure(l,JS.replace_column!(f,z,columns[k])===f,"update return")
        ensure(l,!f.prepared_valid && length(f.updates)==mod(k-1,3)+1 && f.shared_update_count==0,"update history")
        solve!(l,f,data.bf[k+1],5);solve!(l,f,data.bb[k+1],6)
        if k==3 || k==6
            ensure(l,length(f.updates)==3,"retiring history")
            slot=div(k,3)+1
            timedref!(route,f,data.matrices[k+1],l,slot)
            ensure(l,isempty(f.updates) && !f.prepared_valid && f.shared_update_count==0,"published history")
            l.pools[1,slot-1]=length(f.u_pool.pairs);l.pools[2,slot-1]=f.u_pool.entries
            l.pools[3,slot-1]=length(f.v_pool.pairs);l.pools[4,slot-1]=f.v_pool.entries
            control!(l,f,false);ensure(l,owned(f,data.matrices[k+1]),"refactor ownership")
            solve!(l,f,data.bf[k+1],5);solve!(l,f,data.bb[k+1],6)
        end
    end
    ensure(l,Tuple(l.counts)==(1,2,6,6,9,9) && l.completed==24,"lifecycle budget")
    nothing
end
function timedlife!(route::Val,data::Inputs,l::Life)
    l.gcpre+=1;GC.gc(true)
    t=@timed begin
        owned_history!(route,data,l)
        l.gcpost+=1;GC.gc(true)
        nothing
    end
    l.timings[1]=Timing(t)
    ensure(l,t.value===nothing,"outer value")
    l.warm || ensure(l,t.compile_time==0 && t.recompile_time==0,"outer compilation")
    nothing
end
function verifyres!(l,i,M,b,scratch)
    z=l.outputs[i];mul!(scratch,M,z)
    for j in eachindex(scratch);scratch[j]-=b[j];end
    r=norm(scratch,Inf);v=64eps(Float64)*max(1,opnorm(M,Inf)*norm(z,Inf),norm(b,Inf))
    l.residuals[i]=r;l.bounds[i]=v
    ensure(l,all(isfinite,z) && isfinite(r) && isfinite(v) && r<=v,"runtime residual")
    nothing
end
function validate!(l,data,scratch)
    i=1;verifyres!(l,i,data.matrices[1],data.bf[1],scratch);i+=1
    verifyres!(l,i,transpose(data.matrices[1]),data.bb[1],scratch)
    for k in 1:6
        i+=1;verifyres!(l,i,data.matrices[k],data.incoming[k],scratch)
        i+=1;verifyres!(l,i,data.matrices[k+1],data.bf[k+1],scratch)
        i+=1;verifyres!(l,i,transpose(data.matrices[k+1]),data.bb[k+1],scratch)
        if k==3 || k==6
            i+=1;verifyres!(l,i,data.matrices[k+1],data.bf[k+1],scratch)
            i+=1;verifyres!(l,i,transpose(data.matrices[k+1]),data.bb[k+1],scratch)
        end
    end
    ensure(l,i==24,"residual count")
    nothing
end
function loadinput(raw,kind)
    ms=SparseMatrixCSC{Float64,Int}[];bf=Vector{Float64}[];bb=Vector{Float64}[];incoming=Vector{Float64}[]
    for k in 0:6
        s=raw[kind*string(k)]
        push!(ms,SparseMatrixCSC(48,48,Int.(s["colptr"]),Int.(s["rowval"]),frombits(s["nzval_bits"])))
        push!(bf,frombits(s["rhsF_bits"]));push!(bb,frombits(s["rhsB_bits"]))
    end
    for k in 1:6;push!(incoming,frombits(raw[kind*"incoming"*string(k)]["bits"]));end
    Inputs(ms,bf,bb,incoming)
end
function inputcheck(data,raw,kind)
    for k in 0:6
        s=raw[kind*string(k)];B=data.matrices[k+1]
        @assert B.colptr==s["colptr"] && B.rowval==s["rowval"] && bits(B.nzval)==s["nzval_bits"]
        @assert bits(data.bf[k+1])==s["rhsF_bits"] && bits(data.bb[k+1])==s["rhsB_bits"]
    end
    for k in 1:6;@assert bits(data.incoming[k])==raw[kind*"incoming"*string(k)]["bits"];end
    nothing
end
function main()
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    prec=precision(BigFloat);rnd=rounding(BigFloat)
    report["precision"]=prec;report["rounding"]=string(rnd)
    report["clone_sha256"]=bytes2hex(sha256(read(ARGS[3])));report["inputs_sha256"]=bytes2hex(sha256(read(ARGS[4])))
    libs=TOML.parsefile(ARGS[2])["native_libraries"]
    paths=unique(realpath.(filter(p->occursin("libumfpack",p),Libdl.dllist())))
    @assert length(paths)==1
    report["native_path"]=only(paths);report["native_sha256"]=bytes2hex(sha256(read(only(paths))))
    @assert get(libs,only(paths),"")==report["native_sha256"]
    raw=TOML.parsefile(ARGS[4]);data=[loadinput(raw,k) for k in ("sparse","sparse","dense","dense")]
    for fi in 1:4;inputcheck(data[fi],raw,fi<=2 ? "sparse" : "dense");end
    @assert all(!Base.mightalias(getfield(data[i].matrices[k],n),getfield(data[j].matrices[t],n)) for i in 1:4,j in 1:4,k in 1:7,t in 1:7,n in (:colptr,:rowval,:nzval) if (i,k)!=(j,t))
    @assert all(!Base.mightalias(a,b) for fi in (1,3) for (a,b) in zip(vcat(data[fi].bf,data[fi].bb,data[fi].incoming),vcat(data[fi+1].bf,data[fi+1].bb,data[fi+1].incoming)))
    for warm in (true,false),r in 1:(warm ? 2 : 8),kind in ("sparse","dense"),candidate in (isodd(r) ? (false,true) : (true,false))
        push!(lives,Life(warm,r,kind,candidate))
    end
    @assert length(lives)==40
    scratch=zeros(48)
    for (index,l) in enumerate(lives)
        report["active_lifecycle"]=index
        fi=(l.fixture=="sparse" ? 1 : 3)+(l.candidate ? 1 : 0)
        timedlife!(Val(l.candidate),data[fi],l)
        validate!(l,data[fi],scratch)
        for j in 1:4;inputcheck(data[j],raw,j<=2 ? "sparse" : "dense");end
        ensure(l,l.controls==lives[1].controls,"default controls equal")
        l.done=true
    end
    @assert precision(BigFloat)==prec && rounding(BigFloat)==rnd && Threads.nthreads()==BLAS.get_num_threads()==1
    report["complete"]=true;save();println("S4-Q complete: ",sum(l.checks for l in lives)," checks, 40 lifecycles, 960 solves")
end
Base.include(JS,ARGS[3])
try;main();catch e;report["error"]=sprint(showerror,e);save();rethrow();end
