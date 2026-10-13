# New bounded component comparison; no production method replacement.
using JSimplex, SparseArrays, LinearAlgebra, TOML
const J=JSimplex
const ROOT="/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl"
realpath(pathof(J))==realpath(joinpath(ROOT,"src/JSimplex.jl")) || error("wrong source")
Base.include(J,joinpath(@__DIR__,"candidate-methods.jl"))
function matrix(T,n,kind)
    b=spdiagm(-1=>fill(-one(T),n-1),0=>fill(T(5),n),1=>fill(T(2),n-1))
    if kind=="dense"
        b=fill(one(T),n,n)
        for i in 1:n;b[i,i]=T(n+2);end
        return b
    elseif kind=="storedzeros"
        return SparseMatrixCSC(n,n,collect(1:n:n*n+1),repeat(collect(1:n),n),vec(Matrix(b)))
    end
    return b
end
function signature(b)
    return (b.dimension,b.sparse_pivots,copy(b.row_order),copy(b.column_order),
        [(copy(x.indices),copy(x.values)) for x in b.lower],
        [(copy(x.indices),copy(x.values)) for x in b.upper],copy(b.diagonal),
        copy(b.core.factors),copy(b.core.p))
end
function solves_ok(b,B)
    T=eltype(B);e=ones(T,size(B,1));rhs=B*e;trhs=transpose(B)*e;x=similar(e);y=similar(e)
    J._backend_forward_solve!(x,b,rhs);J._backend_transpose_solve!(y,b,trhs)
    if T<:Rational;return x==e && y==e;end
    return all(abs(z-one(T))<=T(64)*eps(T) for z in x) && all(abs(z-one(T))<=T(64)*eps(T) for z in y)
end
function lifecycle(T,D,kind)
    large=matrix(T,24,"sparse");small=matrix(T,6,kind);lc=deepcopy(large);sc=deepcopy(small)
    r=J._construct_markowitz(large,nothing,D);c=J._s4ab_construct_markowitz(large,nothing,D)
    savedr=J._copy_backend(r);savedc=J._copy_backend(c)
    wr=r.workspace;wc=c.workspace;rr=copy(wr.rows);cr=copy(wc.rows)
    checks=Dict{String,Bool}();stages=Any[]
    for (i,B) in enumerate((large,small,small,large))
        if i>1;r=J._refactorize_backend(r,B);c=J._s4ab_refactorize_backend(c,B);end
        checks["stage$(i)_same_factor"]=isequal(signature(r),signature(c))
        checks["stage$(i)_reference_solves"]=solves_ok(r,B)
        checks["stage$(i)_candidate_solves"]=solves_ok(c,B)
        checks["stage$(i)_private_owners"]=r.workspace===wr && c.workspace===wc && wr!==wc && all(wr.rows[j]===rr[j] && wc.rows[j]===cr[j] && rr[j]!==cr[j] for j in eachindex(rr))
        push!(stages,Dict("dimension"=>size(B,1),"reference_workspace_graph"=>Base.summarysize(wr),"candidate_workspace_graph"=>Base.summarysize(wc),"row_capacity"=>length(wc.rows)))
    end
    checks["saved_reference"]=solves_ok(savedr,large);checks["saved_candidate"]=solves_ok(savedc,large)
    checks["inputs_preserved"]=isequal(large,lc) && isequal(small,sc)
    return Dict("type"=>string(T),"dictionary"=>(D<:Dict ? "Dict" : "OrderedDict"),"kind"=>kind,"checks"=>checks,"stages"=>stages)
end
mutable struct CountLengthDict{T} <: AbstractDict{Int,T}
    data::Dict{Int,T}
    reads::Int
end
CountLengthDict{T}() where T=CountLengthDict{T}(Dict{Int,T}(),0)
Base.length(d::CountLengthDict)=(d.reads+=1;length(d.data))
Base.iterate(d::CountLengthDict,args...)=iterate(d.data,args...)
Base.getindex(d::CountLengthDict,i)=d.data[i]
Base.setindex!(d::CountLengthDict,v,i)=(d.data[i]=v)
Base.haskey(d::CountLengthDict,i)=haskey(d.data,i)
Base.keys(d::CountLengthDict)=keys(d.data)
Base.values(d::CountLengthDict)=values(d.data)
Base.delete!(d::CountLengthDict,i)=(delete!(d.data,i);d)
Base.empty!(d::CountLengthDict)=(empty!(d.data);d.reads=0;d)
function work_case(n,H)
    counts=Any[];checks=Dict{String,Bool}()
    for (side,build) in (("reference",J._construct_markowitz),("candidate",J._s4ab_construct_markowitz))
        ws=J.MarkowitzWorkspace(Float64,CountLengthDict{Float64});J._reset_markowitz_workspace!(ws,H)
        owners=copy(ws.rows);ws.rows[end].data[H]=7.0;ws.columns[end].data[H]=7.0
        thrown=false
        try;build(spzeros(n,n),ws,CountLengthDict{Float64});catch e;thrown=e isa SingularException && e.info==1;end
        reads=[d.reads for d in ws.rows]
        expected=side=="reference" ? vcat(fill(2,n),fill(1,H-n)) : vcat(fill(1,n),zeros(Int,H-n))
        checks[side*"_counts"]=reads==expected
        checks[side*"_failure"]=thrown
        checks[side*"_clear_and_retain"]=length(ws.rows)==H && all(ws.rows[i]===owners[i] && isempty(ws.rows[i].data) && isempty(ws.columns[i].data) for i in 1:H)
        push!(counts,Dict("side"=>side,"row_reads"=>reads))
    end
    return Dict("n"=>n,"H"=>H,"checks"=>checks,"counts"=>counts)
end
@noinline function repeat_refactors!(holder,B,f::F,reps) where F
    for i in 1:reps;holder[]=f(holder[],B);end
    return nothing
end
function timed_call(holder,B,f)
    t=@timed repeat_refactors!(holder,B,f,4)
    return Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function cost_case(T,kind)
    H=kind=="retained" ? 256 : 32
    initial=matrix(T,H,"sparse");B=matrix(T,32,kind=="dense" ? "dense" : "sparse");original=deepcopy(B)
    D=J.OrderedCollections.OrderedDict{Int,T}
    r=Ref(J._construct_markowitz(initial,nothing,D));c=Ref(J._s4ab_construct_markowitz(initial,nothing,D))
    # Both output slots reach the same target shape before paired warmup.
    repeat_refactors!(r,B,J._refactorize_backend,2);repeat_refactors!(c,B,J._s4ab_refactorize_backend,2)
    windows=Any[];checks=Dict{String,Bool}()
    for pair in 1:10
        for side in (isodd(pair) ? ("reference","candidate") : ("candidate","reference"))
            t=side=="reference" ? timed_call(r,B,J._refactorize_backend) : timed_call(c,B,J._s4ab_refactorize_backend)
            t["pair"]=pair;t["side"]=side;t["phase"]=pair<=3 ? "warm" : "measured";t["repetitions"]=4
            push!(windows,t)
        end
        checks["pair$(pair)_same_factor"]=isequal(signature(r[]),signature(c[]))
    end
    checks["reference_solves"]=solves_ok(r[],B);checks["candidate_solves"]=solves_ok(c[],B)
    checks["input_preserved"]=isequal(B,original)
    checks["compile_zero"]=all(w["compile_seconds"]==0 && w["recompile_seconds"]==0 for w in windows if w["phase"]=="measured")
    return Dict("type"=>string(T),"kind"=>kind,"n"=>32,"H"=>H,"checks"=>checks,"windows"=>windows,"reference_graph"=>Base.summarysize(r[]),"candidate_graph"=>Base.summarysize(c[]))
end
function main(out)
    life=Any[];work=Any[];cost=Any[];errors=String[];p=precision(BigFloat);mode=rounding(BigFloat)
    try
        for n in (3,8),H in (n,64)
            x=work_case(n,H);push!(work,x);all(values(x["checks"])) || error("work oracle failed")
        end
        for T in (Float32,Float64,BigFloat,Rational{BigInt}),D in (Dict{Int,T},J.OrderedCollections.OrderedDict{Int,T}),kind in ("sparse","dense","storedzeros")
            x=lifecycle(T,D,kind);push!(life,x);all(values(x["checks"])) || error("lifecycle failed")
        end
        for T in (Float32,Float64,BigFloat,Rational{BigInt}),kind in ("sparse","retained","dense")
            x=cost_case(T,kind);push!(cost,x);all(values(x["checks"])) || error("cost correctness failed")
        end
    catch e;push!(errors,sprint(showerror,e,catch_backtrace()));end
    restored=precision(BigFloat)==p && rounding(BigFloat)==mode
    passed=isempty(errors) && restored && length(life)==24 && length(work)==4 && length(cost)==12
    raw=Dict("lifecycles"=>life,"work"=>work,"cost"=>cost,"errors"=>errors,"ambient_restored"=>restored,"all_passed"=>passed,"source"=>pathof(J),"Julia_version"=>string(VERSION))
    open(joinpath(out,"qualification.toml"),"w") do io;TOML.print(io,raw);end
    passed || error("qualification failed; preserve raw")
end
length(ARGS)==1 || error("output argument required")
main(ARGS[1])
