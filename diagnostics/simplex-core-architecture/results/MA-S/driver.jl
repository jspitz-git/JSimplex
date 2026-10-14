# MA-S UNEXECUTED guarded driver. All R sources remain unchanged.
const LOAD_START = time_ns()
using Test, TOML, LinearAlgebra
const RD = abspath(joinpath(@__DIR__, "../MA-R"))
include(joinpath(RD,"reference.jl"))
include(joinpath(RD,"tests.jl"))
const P = MADenseProbe
const TST = MADenseProbeTests
realpath(pathof(P.JSimplex)) == realpath(joinpath(@__DIR__,"../../../../src/JSimplex.jl")) || error("wrong JSimplex")
realpath(pathof(P.MA)) == realpath("/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl") || error("wrong MA")
const CASES = TOML.parsefile(joinpath(RD,"fixtures.toml"))["cost_cases"]
serialtokens(x) = [repr(v) for v in TST.tokens(x)]
function counts(ts)
    c=Test.get_test_counts(ts)
    Dict("pass"=>c.passes+c.cumulative_passes,"fail"=>c.fails+c.cumulative_fails,
         "error"=>c.errors+c.cumulative_errors,"broken"=>c.broken+c.cumulative_broken)
end
function red()
    !isdefined(P,:_dense_ma_eligible) && !isdefined(P,:candidate_forward!) && !isdefined(P,:candidate_transpose!) || error("candidate already loaded")
    caught=nothing
    try
        TST.route_red()
    catch e
        caught=e
    end
    caught isa Test.TestSetException || error("RED must be a TestSetException")
    c=caught
    c.pass==0 && c.fail==2 && c.error==0 && c.broken==0 && length(c.errors_and_fails)==2 && all(x isa Test.Fail for x in c.errors_and_fails) || error("wrong RED")
    Dict("pass"=>c.pass,"fail"=>c.fail,"error"=>c.error,"broken"=>c.broken,
         "missing_route_only"=>true,"failure_expressions"=>[string(x.orig_expr) for x in c.errors_and_fails])
end
@noinline function batch(f::F,x) where F
    for _ in 1:4
        f(x.dest,x.backend,x.rhs)
    end
    nothing
end
function window(f,x)
    t=@timed batch(f,x)
    Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
        "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function costs(index)
    records=Any[]
    for (ci,c) in enumerate(CASES)
        scalar=c["scalar"]=="BigFloat" ? BigFloat : c["scalar"]=="Float64" ? Float64 : Rational{BigInt}
        scoped=c["scoped"]=="none" ? nothing : RoundUp
        TST.context(c["bits"],RoundNearest,scoped) do
            x=TST.bundle(c["n"],c["layout"];T=scalar)
            a,b=deepcopy(x),deepcopy(x)
            xs=(a,b); zeroes=(copy(a.dest),copy(b.dest))
            snapshots=[(factor=TST.tokens(y.backend.factorization.factors),ipiv=copy(y.backend.factorization.ipiv),rhs=TST.tokens(y.rhs),owners=copy(vec(y.backend.factorization.factors)),rhsowners=collect(y.rhs)) for y in xs]
            P._dense_ma_eligible(b.dest,b.backend,b.rhs)===c["eligible"] || error("cost route")
            fs=c["direction"]=="forward" ? (P.reference_forward!,P.candidate_forward!) : (P.reference_transpose!,P.candidate_transpose!)
            ws=Any[]; expected=nothing
            for pair in 1:10
                order=iseven(index+ci+pair) ? (1,2) : (2,1)
                for (oi,side) in enumerate(order)
                    y=xs[side]; s=snapshots[side]
                    copyto!(y.dest,zeroes[side])
                    w=window(fs[side],y)
                    output=serialtokens(y.dest)
                    expected===nothing && (expected=output)
                    output==expected || error("window output mismatch")
                    F=y.backend.factorization
                    preserved=TST.tokens(F.factors)==s.factor && F.ipiv==s.ipiv && TST.tokens(y.rhs)==s.rhs && all(v===u for (v,u) in zip(F.factors,s.owners)) && all(v===u for (v,u) in zip(y.rhs,s.rhsowners))
                    preserved || error("window input changed")
                    merge!(w,Dict("side"=>side==1 ? "reference" : "candidate","pair"=>pair,"order"=>oi,
                        "phase"=>pair<=3 ? "warm" : "measured","output"=>output,"preserved"=>preserved,"calls"=>4))
                    push!(ws,w)
                end
            end
            push!(records,Dict("id"=>c["id"],"eligible"=>c["eligible"],"windows"=>ws,"expected"=>expected))
        end
    end
    records
end
function main()
    index=parse(Int,ARGS[1]);out=ARGS[2];index in 1:3 || error("bad index")
    ambient=precision(BigFloat);rnd=rounding(BigFloat);globalrnd=Base.MPFR.ROUNDING_MODE[]
    raw=Dict{String,Any}("index"=>index,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"errors"=>String[],"red"=>Dict{String,Any}(),"correctness"=>Any[],"costs"=>Any[],"counts"=>Dict{String,Any}())
    try
        if index==1
            ts=@testset "reference smoke" begin
                TST.reference_smoke()
            end
            raw["counts"]["smoke"]=counts(ts)
            raw["red"]=red()
        end
        started=time_ns()
        Base.include(P,joinpath(RD,"candidate.jl"))
        Base.include(P,joinpath(RD,"instrumented.jl"))
        raw["candidate_definition_seconds"]=(time_ns()-started)/1e9
        if index==1
            records=Ref{Any}()
            ts=@testset "complete MA-R correctness" begin
                records[]=TST.qualification()
            end
            raw["counts"]["qualification"]=counts(ts)
            raw["correctness"]=[Dict("id"=>r.id,"direction"=>r.direction,"eligible"=>r.eligible,"calls_per_side"=>r.calls_per_side,"exception"=>r.exception===nothing ? String[] : collect(r.exception),"output"=>[repr(v) for v in r.output]) for r in records[]]
        end
        raw["costs"]=costs(index)
        all(w["compile_seconds"]==0 && w["recompile_seconds"]==0 for c in raw["costs"] for w in c["windows"] if w["phase"]=="measured") || error("measured compilation")
    catch e
        push!(raw["errors"],sprint(showerror,e,catch_backtrace()))
    finally
        raw["ambient_restored"]=precision(BigFloat)==ambient && rounding(BigFloat)==rnd && Base.MPFR.ROUNDING_MODE[]==globalrnd
        raw["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if !isnothing(pathof(m)))
        path=joinpath(out,"raw.toml");ispath(path) && error("raw exists")
        open(path,"w") do io;TOML.print(io,raw);end
    end
    isempty(raw["errors"]) && raw["ambient_restored"] && length(raw["costs"])==52 || error("incomplete qualification")
    println("MA-S process $index complete")
end
main()
