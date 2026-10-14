# MA-P throwaway exact RHS propagation probe; no production overwrite.
const LOAD_START=time_ns()
push!(LOAD_PATH,joinpath(@__DIR__,"env"))
using JSimplex, MutableArithmetics, SparseArrays, TOML
const MA=MutableArithmetics
const Q=Rational{BigInt}
const Bound=JSimplex.Bound
const bound_value=JSimplex.bound_value
const _exact_rational=JSimplex._exact_rational
const _represent_exact=JSimplex._represent_exact
const _shift_bound_exact=JSimplex._shift_bound_exact
realpath(pathof(JSimplex))==realpath(joinpath(@__DIR__,"../../../../src/JSimplex.jl")) || error("wrong source")
realpath(pathof(MA))==realpath("/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl") || error("wrong MA")
include("reference.jl");include("candidate.jl")
const FIXTURES=TOML.parsefile(joinpath(@__DIR__,"fixtures.toml"))["fixtures"]
function make_fixture(f)
    T=f["scalar"]=="Q" ? Q : f["scalar"]=="F64" ? Float64 : BigFloat
    bits=f["scalar"]=="BF512" ? 512 : 256
    setprecision(BigFloat,bits) do
        n=f["n"];m=f["layout"]=="dense" ? n : 2n
        rows=f["layout"]=="dense" ? collect(1:n) : collect(1:2:2n)
        coef=[T(T===Q ? ((big(2)^256+2i+1)//(2i+3)) :
              T===Float64 ? ((big(2)^12+2i+1)//8) : ((big(2)^120+2i+1)//(big(2)^20))) for i in 1:n]
        value=T(T===Q ? ((big(2)^160+3)//31) : T===Float64 ? ((big(2)^10+3)//16) : ((big(2)^110+3)//(big(2)^18)))
        lower=[Bound(T(T===Q ? -11//7 : -11//4)) for _ in 1:m]
        upper=[Bound(T(T===Q ? 13//7 : 13//4)) for _ in 1:m]
        mode=f["mode"]
        if mode=="unit"
            coef=[T(isodd(i) ? 1 : -1) for i in 1:n]
        elseif mode=="zero"
            value=T===Q ? zero(Q) : -zero(T)
        elseif mode=="equal"
            upper=copy(lower)
        elseif mode=="free"
            lower=[Bound{T}(nothing) for _ in 1:m];upper=copy(lower)
        elseif mode=="alias"
            coef=fill(value,n);lower=fill(Bound(value),m)
        elseif mode=="roundreject"
            coef=fill(one(T),n)
            value=T(T===Q ? 1//7 : big(1)//(big(2)^(T===Float64 ? 60 : bits+40)))
            lower=fill(Bound(one(T)),m);upper=fill(Bound(T(2)),m)
        end
        A=SparseMatrixCSC(m,1,[1,n+1],rows,coef)
        return (A,lower,upper,value)
    end
end
valtoken(x::Q)=string(x)
valtoken(x::BigFloat)=(string(Q(x)),precision(x),iszero(x)&&signbit(x))
valtoken(x::Float64)=bitstring(x)
btoken(x)=isfinite(x) ? (true,valtoken(bound_value(x))) : (false,)
function snapshot(args)
    A,l,u,v=args
    (copy(A.colptr),copy(A.rowval),valtoken.(A.nzval),btoken.(l),btoken.(u),valtoken(v))
end
function owners(args)
    A,l,u,v=args;out=Any[A.colptr,A.rowval,A.nzval,l,u]
    for x in (A.nzval...,v,(bound_value(b) for b in l if isfinite(b))...,(bound_value(b) for b in u if isfinite(b))...)
        if x isa Q;push!(out,numerator(x),denominator(x));elseif x isa BigFloat;push!(out,x);end
    end
    out
end
sig(out)=(out[1],[(i,btoken(l),btoken(u)) for (i,l,u) in out[2]])
function oracle(args)
    A,l,u,v=args;T=typeof(v);changes=Tuple{Int,Bound{T},Bound{T}}[]
    for k in eachindex(A.nzval)
        row=A.rowval[k];shift=Q(A.nzval[k])*Q(v)
        pair=map((l[row],u[row])) do b
            (!isfinite(b)||iszero(shift)) && return b
            q=Q(bound_value(b))-shift
            y=try T(q) catch e
                (e isa InexactError || e isa OverflowError || e isa DomainError) || rethrow()
                return nothing
            end
            isfinite(y) && Q(y)==q ? Bound(y) : nothing
        end
        any(isnothing,pair) && return false,changes
        push!(changes,(row,pair...))
    end
    true,changes
end
@noinline consume(out)=Int(out[1])+length(out[2])
@noinline function batch(fun,args,reps)
    s=0
    for _ in 1:reps;s+=consume(fun(args...));end
    s
end
function window(fun,args)
    t=@timed batch(fun,args,16)
    Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"checksum"=>t.value)
end
function save_new(path,data)
    ispath(path) && error("output exists")
    open(path,"w") do io;TOML.print(io,data);end
end
function main()
    index=parse(Int,ARGS[1]);out=ARGS[2];ambient=precision(BigFloat);rnd=rounding(BigFloat)
    raw=Dict{String,Any}("index"=>index,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"loaded_paths"=>Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if !isnothing(pathof(m))),"checks"=>Any[],"costs"=>Any[],"errors"=>String[])
    try
        if index==1
            for f in FIXTURES
                bits=f["scalar"]=="BF512" ? 512 : 256
                setprecision(BigFloat,bits) do
                    args=make_fixture(f);before=snapshot(args);own=owners(args);want=oracle(args)
                    ref=reference_rhs(args...);refok=snapshot(args)==before
                    got=candidate_rhs(args...);candok=snapshot(args)==before;after=owners(args)
                    saved=sig(got);candidate_rhs(args...)
                    flags=Dict("reference_oracle"=>sig(ref)==sig(want),"candidate_oracle"=>sig(got)==sig(want),"reference_preservation"=>refok,"candidate_preservation"=>candok && snapshot(args)==before,"input_owners"=>length(own)==length(after)&&all(a===b for (a,b) in zip(own,after)),"retained_outputs"=>sig(got)==saved,"zero_identity"=>f["mode"]!="zero"||all(l===args[2][i]&&u===args[3][i] for (i,l,u) in got[2]),"equal_sharing"=>f["mode"]!="equal"||all(l===u for (_,l,u) in got[2]),"precision"=>precision(BigFloat)==bits&&rounding(BigFloat)==rnd,"roundreject"=>f["mode"]!="roundreject"||f["scalar"]=="Q"||!got[1])
                    push!(raw["checks"],Dict("id"=>f["id"],"flags"=>flags));all(values(flags))||error("correctness "*f["id"])
                end
            end
            for T in (Q,BigFloat), zero_bound in (true,false)
                sc=make_scratch();shift=MA.buffered_operate_to!(sc[3],sc[1],*,Q(3),Q(1,2));b=Bound(T(zero_bound ? 0//1 : 5//4));before=btoken(b)
                got=private_shift(T,b,shift,sc);saved=isnothing(got) ? nothing : btoken(got)
                MA.operate!(zero,sc[1]);MA.operate!(zero,sc[2])
                flags=Dict("represented"=>!isnothing(got),"detached_scratch"=>!isnothing(got)&&btoken(got)==saved,"input_preserved"=>btoken(b)==before)
                push!(raw["checks"],Dict("id"=>"scratch-$(T)-$zero_bound","flags"=>flags));all(values(flags))||error("scratch alias")
            end
            q=Q(3,7);before=valtoken(q);MA.operate!(+,numerator(q),big(1));ok=valtoken(q)!=before
            push!(raw["checks"],Dict("id"=>"negative-snapshot","flags"=>Dict("mutation_detected"=>ok)));ok||error("snapshot insensitive")
        end
        cases=[f for f in FIXTURES if f["cost"]]
        for (ci,f) in enumerate(cases)
            setprecision(BigFloat,f["scalar"]=="BF512" ? 512 : 256) do
                args=make_fixture(f);before=snapshot(args);want=oracle(args);expected=16*consume(want);first=Any[];ws=Any[]
                for (side,fun) in (("reference",reference_rhs),("candidate",candidate_rhs))
                    start=time_ns();got=fun(args...);elapsed=(time_ns()-start)/1e9
                    sig(got)==sig(want)&&snapshot(args)==before||error("first mismatch")
                    push!(first,Dict("side"=>side,"seconds"=>elapsed))
                end
                for pair in 1:10
                    order=iseven(index+ci+pair) ? (("reference",reference_rhs),("candidate",candidate_rhs)) : (("candidate",candidate_rhs),("reference",reference_rhs))
                    for (oi,(side,fun)) in enumerate(order)
                        w=window(fun,args);merge!(w,Dict("side"=>side,"pair"=>pair,"order"=>oi,"phase"=>pair<=3 ? "warm" : "measured"));push!(ws,w)
                        w["checksum"]==expected&&snapshot(args)==before||error("window mismatch")
                    end
                end
                push!(raw["costs"],Dict("id"=>f["id"],"expected"=>expected,"first"=>first,"windows"=>ws,"preserved"=>true))
            end
        end
    catch e
        push!(raw["errors"],sprint(showerror,e,catch_backtrace()))
    finally
        raw["ambient_restored"]=precision(BigFloat)==ambient&&rounding(BigFloat)==rnd
        save_new(joinpath(out,"raw.toml"),raw)
    end
    isempty(raw["errors"])&&length(raw["costs"])==64&&raw["ambient_restored"]||error("incomplete")
    all(w["compile_seconds"]==0&&w["recompile_seconds"]==0 for c in raw["costs"] for w in c["windows"] if w["phase"]=="measured")||error("measured compilation")
    println("MA-P process $index complete")
end
main()
