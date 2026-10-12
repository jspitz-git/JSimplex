using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl
const JS=JSimplex
mutable struct Counts
    constructor::Int
    refactor::Int
    ftran::Int
    btran::Int
end
const counts=Counts(0,0,0,0)
const checks=Dict{String,Bool}()
const samples=Vector{Any}(undef,40)
const endpoints=Vector{Any}(undef,44)
const checkpoints=Vector{Any}(undef,3)
const setups=Vector{Any}(undef,4)
const used=zeros(Int,4) # samples, endpoints, checkpoints, setups
const report=Dict{String,Any}("scope"=>"S4-M bounded whole-HH refactor windows; native retention OPEN", "source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"precision"=>precision(BigFloat),"rounding"=>string(rounding(BigFloat)),"complete"=>false,"checks"=>checks)
bits(v)=string.(reinterpret(UInt64,v);base=16,pad=16)
frombits(v)=reinterpret.(Float64,parse.(UInt64,v;base=16))
function ck(k,v);checks[k]=v;v || error("S4-M gate: "*k);end
function save()
    report["entries"]=Dict("constructor"=>counts.constructor,"refactor"=>counts.refactor,"FTRAN"=>counts.ftran,"BTRAN"=>counts.btran)
    report["samples"]=samples[1:used[1]];report["endpoints"]=endpoints[1:used[2]]
    report["checkpoints"]=checkpoints[1:used[3]];report["setups"]=setups[1:used[4]]
    open(ARGS[1],"w") do io;TOML.print(io,report);end
end
stats(t)=Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function initial(B)
    counts.constructor+=1
    t=@timed JS.HuangfuHallFactorization(B)
    return t.value,stats(t)
end
function batch!(::Val{false},f,B)
    for _ in 1:16;counts.refactor+=1;JS.refactorize!(f,B);end
    nothing
end
function batch!(::Val{true},f,B)
    for _ in 1:16;counts.refactor+=1;JS._s4m_refactorize!(f,B);end
    nothing
end
function measured!(route::Val,f,B)
    t=@timed batch!(route,f,B)
    @assert t.value===nothing
    stats(t)
end
function nativeinfo(f)
    u=f.refactor_workspace
    names=("SIZE_OF_UNIT","SYMBOLIC_PEAK_MEMORY","SYMBOLIC_SIZE","NUMERIC_SIZE_ESTIMATE","PEAK_MEMORY_ESTIMATE","NUMERIC_SIZE","PEAK_MEMORY","VARIABLE_PEAK")
    offsets=(3,13,14,20,21,40,41,46)
    Dict{String,Any}("status"=>u.status,"sizes"=>Dict(names[i]=>u.info[offsets[i]+1] for i in eachindex(names)),"controls"=>bits(u.control))
end
function fingerprint(f)
    io=IOBuffer();b=f.base
    for M in (b.lower,b.upper);write(io,M.colptr);write(io,M.rowval);write(io,M.nzval);end
    for v in (b.rows,b.columns,b.scaling);write(io,v);end
    write(io,b.divide_scaling)
    bytes2hex(sha256(take!(io)))
end
function processmemory()
    names=("VmRSS","VmHWM","VmSize","VmPeak")
    Dict(k=>parse(Int,split(only(filter(l->startswith(l,k*":"),readlines("/proc/self/status"))))[2]) for k in names)
end
function owned(f,B)
    u=f.refactor_workspace
    all(!Base.mightalias(getfield(u,n),getfield(B,n)) && !Base.mightalias(getfield(f.base.lower,n),getfield(B,n)) && !Base.mightalias(getfield(f.base.upper,n),getfield(B,n)) for n in (:colptr,:rowval,:nzval))
end
function endpoint!(f,B,bf,bb,label,kind,side,phase,ctrl,ni)
    zf=zeros(96);zb=zeros(96)
    counts.ftran+=1;JS.forward_solve!(zf,f,bf)
    counts.btran+=1;JS.transpose_solve!(zb,f,bb)
    # Diagnostic arithmetic only; exact binary64 residuals are audited offline.
    rf=norm(B*zf-bf,Inf);rb=norm(transpose(B)*zb-bb,Inf)
    scale=opnorm(B,Inf);scalet=opnorm(transpose(B),Inf)
    boundf=64eps(Float64)*max(1,scale*norm(zf,Inf),norm(bf,Inf))
    boundb=64eps(Float64)*max(1,scalet*norm(zb,Inf),norm(bb,Inf))
    e=Dict{String,Any}("label"=>label,"kind"=>kind,"side"=>side,"phase"=>phase,"forward"=>zf,"transpose"=>zb,"fingerprint"=>fingerprint(f),"native"=>ni,"residualF"=>rf,"residualB"=>rb,"boundF"=>boundf,"boundB"=>boundb)
    used[2]+=1;endpoints[used[2]]=e
    ck(label*"_finite_residual",all(isfinite,zf)&&all(isfinite,zb)&&rf<=boundf&&rb<=boundb)
    ck(label*"_owned",owned(f,B))
    ck(label*"_control",bits(f.refactor_workspace.control)==ctrl && f.refactor_workspace.control[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP]==0)
    ck(label*"_empty_history",isempty(f.updates)&&f.shared_update_count==0&&isempty(f.u_pool.pairs)&&isempty(f.v_pool.pairs))
    nothing
end
function checkpoint!(factors,label)
    GC.gc(true)
    x=Dict("label"=>label,"julia_graph_bytes"=>Base.summarysize(factors),"native"=>[nativeinfo(f) for f in factors],"process_kib"=>processmemory())
    used[3]+=1;checkpoints[used[3]]=x
    nothing
end
function runbatch!(factors,matrices,rhs,controls,fi,phase,round,warm)
    kind=fi<=2 ? "sparse" : "dense";candidate=iseven(fi);side=candidate ? "candidate" : "reference"
    B=matrices[fi][phase+1];bf,bb=rhs[fi][phase+1]
    warm || GC.gc(true)
    s=measured!(Val(candidate),factors[fi],B)
    s["kind"]=kind;s["side"]=side;s["phase"]=phase;s["round"]=round;s["warmup"]=warm
    used[1]+=1;samples[used[1]]=s
    ni=nativeinfo(factors[fi])
    label=(warm ? "warm" : "round")*string(round)*"_"*kind*"_"*side
    warm || ck(label*"_compile_zero",s["compile_seconds"]==0 && s["recompile_seconds"]==0)
    endpoint!(factors[fi],B,bf,bb,label,kind,side,phase,controls[fi],ni)
    nothing
end
function lifetime(inputs)
    matrices=Vector{Vector{SparseMatrixCSC{Float64,Int}}}(undef,4)
    rhs=Vector{Vector{Tuple{Vector{Float64},Vector{Float64}}}}(undef,4)
    controls=Vector{Vector{String}}(undef,4)
    for fi in 1:4
        kind=fi<=2 ? "sparse" : "dense"
        matrices[fi]=SparseMatrixCSC{Float64,Int}[];rhs[fi]=Tuple{Vector{Float64},Vector{Float64}}[]
        for phase in 0:1
            v=inputs[kind*string(phase)]
            B=SparseMatrixCSC(96,96,Int.(v["colptr"]),Int.(v["rowval"]),frombits(v["nzval_bits"]))
            push!(matrices[fi],B);push!(rhs[fi],(frombits(v["rhs_forward_bits"]),frombits(v["rhs_transpose_bits"])))
            ck("input_$(fi)_$(phase)",bits(B.nzval)==v["nzval_bits"] && nnz(B)==v["nnz"] && all(isfinite,B.nzval))
        end
    end
    ck("side_inputs_distinct",all(!Base.mightalias(getfield(matrices[fi][p],n),getfield(matrices[fi+1][p],n)) for fi in (1,3),p in 1:2,n in (:colptr,:rowval,:nzval)))
    # All real constructors return the same concrete HH type; a local Any container
    # holds only current roots and never retains an old extracted/native owner.
    fs=Vector{Any}(undef,4)
    for fi in 1:4
        fs[fi],s=initial(matrices[fi][1]);s["factor"]=fi;used[4]+=1;setups[used[4]]=s
        controls[fi]=bits(fs[fi].refactor_workspace.control)
        bf,bb=rhs[fi][1];kind=fi<=2 ? "sparse" : "dense";side=iseven(fi) ? "candidate" : "reference"
        endpoint!(fs[fi],matrices[fi][1],bf,bb,"initial_"*string(fi),kind,side,0,controls[fi],nativeinfo(fs[fi]))
    end
    ck("all_default_controls_same",all(c==controls[1] for c in controls))
    for first in (1,3),phase in 0:1,fi in first:first+1
        runbatch!(fs,matrices,rhs,controls,fi,phase,phase+1,true)
    end
    checkpoint!(fs,"after_warmup")
    for round in 1:8
        phase=mod(div(round-1,2),2)
        for first in (1,3)
            order=isodd(round) ? (first,first+1) : (first+1,first)
            for fi in order;runbatch!(fs,matrices,rhs,controls,fi,phase,round,false);end
        end
        round in (4,8) && checkpoint!(fs,"after_round"*string(round))
    end
    for fi in 1:4,phase in 0:1
        kind=fi<=2 ? "sparse" : "dense";v=inputs[kind*string(phase)];B=matrices[fi][phase+1]
        ck("input_preserved_$(fi)_$(phase)",bits(B.nzval)==v["nzval_bits"] && B.colptr==v["colptr"] && B.rowval==v["rowval"])
    end
    report["input_storage"]=Dict("CSC_objects"=>8,"CSC_nzval_elements"=>4*(474+9216),"RHS_vectors"=>16,"RHS_elements"=>16*96)
    nothing
end
function main()
    ck("single_threads",Threads.nthreads()==BLAS.get_num_threads()==1)
    prec=precision(BigFloat);rnd=rounding(BigFloat)
    report["clone_sha256"]=bytes2hex(sha256(read(ARGS[3])))
    report["input_sha256"]=bytes2hex(sha256(read(ARGS[4])))
    libs=TOML.parsefile(ARGS[2])["native_libraries"];paths=unique(realpath.(filter(p->occursin("libumfpack",p),Libdl.dllist())))
    ck("one_native_library",length(paths)==1);report["native_path"]=only(paths);report["native_sha256"]=bytes2hex(sha256(read(only(paths))))
    ck("native_pinned",get(libs,only(paths),"")==report["native_sha256"])
    lifetime(TOML.parsefile(ARGS[4]))
    GC.gc(true);report["after_release_process_kib"]=processmemory()
    ck("budget",counts.constructor==4&&counts.refactor==640&&counts.ftran==44&&counts.btran==44&&used==[40,44,3,4])
    ck("ambient_preserved",precision(BigFloat)==prec&&rounding(BigFloat)==rnd&&Threads.nthreads()==BLAS.get_num_threads()==1)
    # Bit strings generated only after all measurement windows and root release.
    for e in endpoints;e["forward_bits"]=bits(pop!(e,"forward"));e["transpose_bits"]=bits(pop!(e,"transpose"));end
    report["complete"]=true;save();println("S4-M complete ",length(checks)," checks; 32 measured samples")
end
Base.include(JS,ARGS[3])
try;main();catch e;report["error"]=sprint(showerror,e);save();rethrow();end
