# UNEXECUTED component preparation. No JSimplex import or method overwrite.
using SparseArrays, LinearAlgebra, TOML
const API=SparseArrays.UMFPACK
const CAPI=SparseArrays.LibSuiteSparse
const Native=API.UmfpackLU{Float64,Int64}
const PIVOT=CAPI.UMFPACK_PIVOT_TOLERANCE+1
const IR=CAPI.UMFPACK_IRSTEP+1
const SYMPIVOT=CAPI.UMFPACK_SYM_PIVOT_TOLERANCE+1
const STRATEGY=CAPI.UMFPACK_STRATEGY_USED+1
const INFO_SLOTS=(CAPI.UMFPACK_STATUS+1,CAPI.UMFPACK_IR_TAKEN+1,CAPI.UMFPACK_IR_ATTEMPTED+1,CAPI.UMFPACK_SOLVE_FLOPS+1)
need(x,s)=x || error(s)
token(x::Float64)=string(reinterpret(UInt64,x);base=16,pad=16)
number(s)=reinterpret(Float64,parse(UInt64,s;base=16))
function save(output,name,value)
    path=joinpath(output,name);need(!ispath(path),"Output exists")
    open(path,"w") do io;TOML.print(io,value);flush(io);end
end
mutable struct Counts
    fresh::Int;refactor::Int;copy::Int;ftran::Int;btran::Int;snapshot::Int
end
countdict(c)=Dict("fresh"=>c.fresh,"refactor"=>c.refactor,"copy"=>c.copy,"ftran"=>c.ftran,"btran"=>c.btran,"snapshot"=>c.snapshot)
function policy_controls(arm::Symbol)::Vector{Float64}
    arm in (:C,:P,:R) || throw(ArgumentError("Unknown fixed arm"))
    ctrl=API.get_umfpack_control(Float64,Int)
    need(length(ctrl)==20 && ctrl[PIVOT]==0.1 && ctrl[IR]==0.0,"Installed defaults changed")
    ctrl[PIVOT]=arm===:P ? 1.0 : 0.1
    ctrl[IR]=arm===:R ? 2.0 : 0.0
    ctrl
end
function fresh_factor(B::SparseMatrixCSC{Float64,Int},arm::Symbol)
    need(size(B,1)==size(B,2) && size(B,1)>0,"Only nonempty square inputs")
    ctrl=policy_controls(arm)
    F=lu(B;control=ctrl,check=true)
    F,ctrl
end
function newfactor(B,arm,c)
    c.fresh+=1
    fresh_factor(B,arm)
end
function solve_record!(x::Vector{Float64},F::Native,b::Vector{Float64},trans::Bool,c::Counts,info::Matrix{Float64},k::Int)
    need(length(x)==length(b)==size(F,1)==size(F,2),"Solve dimensions")
    need(!Base.mightalias(x,b),"Solve alias")
    if trans
        c.btran+=1;ldiv!(x,transpose(F),b)
    else
        c.ftran+=1;ldiv!(x,F,b)
    end
    @inbounds for j in 1:4;info[j,k]=F.info[INFO_SLOTS[j]];end
    nothing
end
function decoded(m)
    n=Int(m["n"]);need(n in (32,96),"Input dimension")
    SparseMatrixCSC(n,n,Int.(m["colptr"]),Int.(m["rowval"]),number.(m["nzval"]))
end
function ownstate(F,B,ctrl,expected)
    native_owned=!Base.mightalias(F.colptr,B.colptr) && !Base.mightalias(F.rowval,B.rowval) && !Base.mightalias(F.nzval,B.nzval)
    native_match=length(F.colptr)==length(B.colptr) && length(F.rowval)==length(B.rowval) && length(F.nzval)==length(B.nzval) && all(F.colptr[i]+1==B.colptr[i] for i in eachindex(B.colptr)) && all(F.rowval[i]+1==B.rowval[i] && token(F.nzval[i])==token(B.nzval[i]) for i in eachindex(B.nzval))
    Dict("native_owned"=>native_owned,"native_match"=>native_match,"control_private"=>!Base.mightalias(F.control,ctrl),"control_equal"=>token.(F.control)==expected,"control"=>token.(F.control),"strategy"=>F.info[STRATEGY],"sym_pivot"=>token(F.control[SYMPIVOT]),"Wi"=>length(F.workspace.Wi),"W"=>length(F.workspace.W))
end
function disjoint(A::Native,B::Native)
    A!==B && A.numeric!==B.numeric && A.symbolic!==B.symbolic && all(!Base.mightalias(a,b) for (a,b) in ((A.colptr,B.colptr),(A.rowval,B.rowval),(A.nzval,B.nzval),(A.control,B.control),(A.workspace.W,B.workspace.W),(A.workspace.Wi,B.workspace.Wi)))
end
function snapshot(F::Native,B,c)
    c.snapshot+=1
    lnz,unz,m,n,nzd=API.umf_lunz(F)
    need(m==n && n in (32,96) && n<=lnz<=n*(n+1)÷2 && n<=unz<=n*(n+1)÷2,"Factor fill")
    lp=Vector{Int64}(undef,n+1);lj=Vector{Int64}(undef,lnz);lx=Vector{Float64}(undef,lnz)
    up=Vector{Int64}(undef,n+1);ui=Vector{Int64}(undef,unz);ux=Vector{Float64}(undef,unz)
    p=Vector{Int64}(undef,n);q=Vector{Int64}(undef,n);rs=Vector{Float64}(undef,n);recip=Ref{Int64}(-1)
    status=API.umfpack_dl_get_numeric(lp,lj,lx,up,ui,ux,p,q,C_NULL,recip,rs,F.numeric)
    API.umferror(status)
    for v in (lp,lj,up,ui,p,q);v .+= 1;end
    Dict("n"=>n,"lnz"=>lnz,"unz"=>unz,"nzd"=>nzd,"status"=>status,"do_recip"=>recip[],"L"=>Dict("format"=>"csr","ptr"=>lp,"indices"=>lj,"values"=>token.(lx)),"U"=>Dict("format"=>"csc","ptr"=>up,"indices"=>ui,"values"=>token.(ux)),"p"=>p,"q"=>q,"Rs"=>token.(rs),"control"=>token.(F.control),"info"=>token.(F.info),"graph_bytes"=>Base.summarysize(F))
end
function life(output,arm,B0,B4,Z,b0,b4,c)
    F,ctrl=newfactor(B0,arm,c);expected=token.(F.control)
    initial=ownstate(F,B0,ctrl,expected)
    ctrl[PIVOT]=NaN
    poisoned=token.(F.control)==expected
    c.copy+=1;S=copy(F)
    copied=S!==F && S.numeric===F.numeric && S.symbolic===F.symbolic && S.colptr===F.colptr && S.rowval===F.rowval && S.nzval===F.nzval && S.control!==F.control && S.info!==F.info && S.lock!==F.lock && S.workspace.W!==F.workspace.W && S.workspace.Wi!==F.workspace.Wi
    owners=(F.numeric,F.symbolic,F.colptr,F.rowval,F.nzval,F.control,F.workspace.W,F.workspace.Wi)
    saved=(copy(F.colptr),copy(F.rowval),token.(F.nzval),expected)
    xs=[zeros(32) for _ in 1:14];info=zeros(4,14);k=0
    for A in (F,S)
        k+=1;solve_record!(xs[k],A,b0.a,false,c,info,k)
        k+=1;solve_record!(xs[k],A,b0.unit,true,c,info,k)
    end
    T,tc=newfactor(B0,arm,c);independent_T=disjoint(F,T)
    c.refactor+=1;lu!(T,B4;reuse_symbolic=false,check=true)
    first=ownstate(T,B4,tc,expected)
    k+=1;solve_record!(xs[k],T,b4.dse,false,c,info,k);k+=1;solve_record!(xs[k],T,b4.unit,true,c,info,k)
    c.refactor+=1;lu!(T,B4;reuse_symbolic=true,check=true)
    second=ownstate(T,B4,tc,expected)
    k+=1;solve_record!(xs[k],T,b4.dse,false,c,info,k);k+=1;solve_record!(xs[k],T,b4.unit,true,c,info,k)
    V,vc=newfactor(B4,arm,c);independent_V=disjoint(F,V) && disjoint(T,V)
    fresh=ownstate(V,B4,vc,expected)
    k+=1;solve_record!(xs[k],V,b4.dse,false,c,info,k);k+=1;solve_record!(xs[k],V,b4.unit,true,c,info,k)
    singular=false;cause="";status=0
    try
        c.refactor+=1;lu!(T,Z;reuse_symbolic=true,check=true)
    catch e
        cause=string(typeof(e));status=T.status;singular=e isa SingularException
        singular || rethrow()
    end
    T=nothing
    preserved=(F.numeric,F.symbolic,F.colptr,F.rowval,F.nzval,F.control,F.workspace.W,F.workspace.Wi)===owners && F.colptr==saved[1] && F.rowval==saved[2] && token.(F.nzval)==saved[3] && token.(F.control)==saved[4] && S.numeric===F.numeric && S.symbolic===F.symbolic && S.colptr===F.colptr && S.rowval===F.rowval && S.nzval===F.nzval && token.(S.control)==expected
    for A in (F,S)
        k+=1;solve_record!(xs[k],A,b0.a,false,c,info,k)
        k+=1;solve_record!(xs[k],A,b0.unit,true,c,info,k)
    end
    finalF=ownstate(F,B0,ctrl,expected);finalS=ownstate(S,B0,ctrl,expected)
    save(output,"lifecycle-$(arm).toml",Dict("arm"=>string(arm),"initial"=>initial,"first"=>first,"second"=>second,"fresh"=>fresh,"finalF"=>finalF,"finalS"=>finalS,"poisoned_private"=>poisoned,"copy_contract"=>copied,"independent_T"=>independent_T,"independent_V"=>independent_V,"preserved"=>preserved,"singular"=>singular,"cause"=>cause,"status"=>status,"outputs"=>[token.(x) for x in xs],"info"=>[token.(info[:,j]) for j in 1:14]))
    need(singular && poisoned && copied && independent_T && independent_V && preserved && k==14,"Lifecycle integrity")
    nothing
end
function triplets!(xs,info,F,b,c)
    for r in 0:15
        k=3r+1;solve_record!(xs[k],F,b.a,false,c,info,k)
        k+=1;solve_record!(xs[k],F,b.dse,false,c,info,k)
        k+=1;solve_record!(xs[k],F,b.unit,true,c,info,k)
    end
    nothing
end
metrics(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gctime"=>t.gctime,"compile_time"=>t.compile_time,"recompile_time"=>t.recompile_time)
function window(output,spec,B,b,xs,info,c)
    arm=Symbol(spec["arm"])
    build=@timed newfactor(B,arm,c)
    F,ctrl=build.value
    before=ownstate(F,B,ctrl,token.(ctrl))
    solve=@timed triplets!(xs,info,F,b,c)
    after=ownstate(F,B,ctrl,token.(ctrl))
    rec=Dict{String,Any}("schedule"=>spec,"construction"=>metrics(build),"solve"=>metrics(solve),"before"=>before,"after"=>after,"outputs"=>[token.(x) for x in xs],"info"=>[token.(info[:,j]) for j in 1:48])
    if spec["round"]==11;rec["factor"]=snapshot(F,B,c);end
    save(output,"window-$(lpad(spec["id"],3,'0')).toml",rec)
    if !spec["warm"];need(build.compile_time==build.recompile_time==solve.compile_time==solve.recompile_time==0,"Measured compilation contamination");end
    need(all(before[k] && after[k] for k in ("native_owned","native_match","control_private","control_equal")),"Window integrity")
    nothing
end
function unchanged(B,m,owners)
    B.colptr===owners[1] && B.rowval===owners[2] && B.nzval===owners[3] && B.colptr==m["colptr"] && B.rowval==m["rowval"] && token.(B.nzval)==m["nzval"]
end
function run_accuracy_probe(output::String,inputs::String)
    c=Counts(0,0,0,0,0,0);raw=Dict{String,Any}("completed"=>false,"fatal"=>"","inputs_unchanged"=>false)
    try
        need(Threads.nthreads()==1 && BLAS.get_num_threads()==1 && Int===Int64,"Threads/index")
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads();raw["index_bits"]=8sizeof(Int)
        raw["stdlib_paths"]=Dict("SparseArrays"=>pathof(SparseArrays),"LinearAlgebra"=>pathof(LinearAlgebra),"TOML"=>pathof(TOML))
        data=TOML.parsefile(inputs);fs=data["fixtures"];schedule=data["schedule"]
        need(length(fs)==4 && length(schedule)==132,"Fixed schedule")
        Bs=[decoded(f["matrix"]) for f in fs];bs=[(a=number.(f["rhs"]["a"]),dse=number.(f["rhs"]["dse"]),unit=number.(f["rhs"]["unit"])) for f in fs]
        owners=[(B.colptr,B.rowval,B.nzval,b.a,b.dse,b.unit) for (B,b) in zip(Bs,bs)]
        B0=decoded(data["lifecycle"]["matrix"]);Z=decoded(data["lifecycle"]["singular"]);b0=(a=number.(data["lifecycle"]["rhs"]["a"]),unit=number.(data["lifecycle"]["rhs"]["unit"]))
        own0=(B0.colptr,B0.rowval,B0.nzval,b0.a,b0.unit);ownZ=(Z.colptr,Z.rowval,Z.nzval)
        for arm in (:C,:P,:R);life(output,arm,B0,Bs[1],Z,b0,bs[1],c);end
        # Fixed diagnostic storage outside all cost regions. Retain all outputs.
        fi=[findfirst(f->f["name"]==s["fixture"],fs)::Int for s in schedule]
        outputs=[[zeros(size(Bs[i],1)) for _ in 1:48] for i in fi];infos=[zeros(4,48) for _ in schedule]
        for k in eachindex(schedule);window(output,schedule[k],Bs[fi[k]],bs[fi[k]],outputs[k],infos[k],c);end
        raw["inputs_unchanged"]=all(unchanged(Bs[i],fs[i]["matrix"],owners[i]) && all(getproperty(bs[i],key)===owners[i][j+3] && token.(getproperty(bs[i],key))==fs[i]["rhs"][string(key)] for (j,key) in enumerate((:a,:dse,:unit))) for i in 1:4) && unchanged(B0,data["lifecycle"]["matrix"],own0) && unchanged(Z,data["lifecycle"]["singular"],ownZ) && b0.a===own0[4] && b0.unit===own0[5] && token.(b0.a)==data["lifecycle"]["rhs"]["a"] && token.(b0.unit)==data["lifecycle"]["rhs"]["unit"]
        raw["completed"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"])
    finally
        raw["counts"]=countdict(c);save(output,"raw.toml",raw)
    end
    need(raw["completed"] && raw["inputs_unchanged"],"Incomplete component experiment")
    need(countdict(c)==Dict("fresh"=>141,"refactor"=>9,"copy"=>3,"ftran"=>4245,"btran"=>2133,"snapshot"=>12),"Call budget")
end
run_accuracy_probe(ARGS[1],ARGS[2])
