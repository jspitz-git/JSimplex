# Diagnostic-only fixed storage. Defined BEFORE loading the instrumented package.
module NativePivotIntegrationProbe
struct ProbeFailure <: Exception
    message::String
end
Base.showerror(io::IO,e::ProbeFailure)=print(io,e.message)
const MODES=(:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
const SYMBOLS=(:default,:threshold_one)
const IDS=ntuple(i->i==9 ? "recovery" : string(MODES[cld(i,2)],"/",SYMBOLS[isodd(i) ? 1 : 2]),9)
const active=Ref(0); const started=Ref(0); const failed=Ref(false)
const attempts=zeros(Int,4,9); const successes=zeros(Int,2,9); const empty_counts=zeros(Int,2,9)
const expected=zeros(UInt64,20,9); const last_controls=zeros(UInt64,20,9)
const finished=falses(9); const point=zeros(Float64,2,8); const objective=zeros(Float64,8)
const status=fill("",8); const has_point=falses(8); const has_objective=falses(8)
const PUBLIC_CAPS=(64,64,4096,4096); const RECOVERY_CAPS=(2,0,2,6)
function need(ok,message)
    ok && return nothing
    failed[]=true
    throw(ProbeFailure(message))
end
slot(kind)=kind===:construct ? 1 : kind===:refactor ? 2 : kind===:forward ? 3 : kind===:transpose ? 4 : 0
function begin_case!(id,symbol)
    need(!failed[] && active[]==0,"invalid or failed case state")
    i=started[]+1
    need(i<=9 && IDS[i]==id,"unexpected case order")
    want=i==9 || iseven(i) ? :threshold_one : :default
    need(symbol===want,"unexpected case policy")
    control=Main.SparseArrays.UMFPACK.get_umfpack_control(Float64,Int)
    if symbol===:threshold_one
        control[Main.SparseArrays.LibSuiteSparse.UMFPACK_PIVOT_TOLERANCE+1]=1.0
        control[Main.SparseArrays.LibSuiteSparse.UMFPACK_IRSTEP+1]=0.0
    end
    need(length(control)==20,"control length")
    for j in 1:20;expected[j,i]=reinterpret(UInt64,control[j]);end
    started[]=i;active[]=i
    return nothing
end
function enter!(kind)
    i=active[];k=slot(kind)
    need(!failed[] && 1<=i<=9 && k!=0,"backend entry outside active case")
    attempts[k,i]+=1 # includes the refused attempt, before the actual operation
    caps=i==9 ? RECOVERY_CAPS : PUBLIC_CAPS
    need(attempts[k,i]<=caps[k],"selected backend attempt cap")
    return nothing
end
function completed(kind,backend)
    i=active[];k=slot(kind)
    need(!failed[] && 1<=i<=9 && 1<=k<=2,"completion outside active case")
    symbol=i==9 || iseven(i) ? :threshold_one : :default
    need(backend.pivot_policy===Main.JSimplex._native_pivot_policy(symbol),"backend policy lost")
    successes[k,i]+=1
    need(successes[k,i]<=attempts[k,i],"completion exceeds attempts")
    if backend.factorization===nothing
        need(backend.dimension==0,"empty dimension")
        empty_counts[k,i]+=1
    else
        control=backend.factorization.control
        need(length(control)==20,"completed control length")
        for j in 1:20
            bits=reinterpret(UInt64,control[j]);last_controls[j,i]=bits
            need(bits==expected[j,i],"completed native control mismatch")
        end
    end
    return backend
end
function result!(r)
    i=active[];need(1<=i<=8,"public result outside case")
    status[i]=string(r.status)
    has_point[i]=r.primal!==nothing && length(r.primal)==2
    if has_point[i];point[1,i]=r.primal[1];point[2,i]=r.primal[2];end
    has_objective[i]=r.objective_value!==nothing
    has_objective[i] && (objective[i]=r.objective_value)
    return nothing
end
function end_case!()
    i=active[]
    if 1<=i<=9;finished[i]=true;end
    active[]=0
    return nothing
end
bits_token(x::UInt64)=string(x;base=16,pad=16)
bits_token(x::Float64)=bits_token(reinterpret(UInt64,x))
function snapshot()
    # Serialization outside all cases. No backend/owner references are retained.
    [Dict{String,Any}("id"=>IDS[i],"policy"=>(i==9 || iseven(i) ? "threshold_one" : "default"),
        "attempts"=>collect(attempts[:,i]),"successes"=>collect(successes[:,i]),
        "empty"=>collect(empty_counts[:,i]),"expected_controls"=>bits_token.(expected[:,i]),
        "last_controls"=>bits_token.(last_controls[:,i]),"finished"=>finished[i],
        "status"=>(i<=8 ? status[i] : "recovery"),
        "has_point"=>(i<=8 ? has_point[i] : false),
        "has_objective"=>(i<=8 ? has_objective[i] : false),
        "point"=>(i<=8 ? bits_token.(point[:,i]) : String[]),
        "objective"=>(i<=8 ? bits_token(objective[i]) : "")) for i in 1:started[]]
end
end
