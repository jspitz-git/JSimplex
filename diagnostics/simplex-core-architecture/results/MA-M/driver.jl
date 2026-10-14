# MA-M single frozen qualification, ordinary loading. No production overwrites.
const LOAD_START=time_ns()
push!(LOAD_PATH, joinpath(@__DIR__, "env"))
using JSimplex, MutableArithmetics, SparseArrays, TOML, Test
const MA=MutableArithmetics
const Q=Rational{BigInt}
const ExactValue=JSimplex.ExactValue
const ExactEndpoint=JSimplex.ExactEndpoint
const _exact_rational=JSimplex._exact_rational
const LinearProblem=JSimplex.LinearProblem
const bound_value=JSimplex.bound_value
realpath(pathof(JSimplex))==realpath(joinpath(@__DIR__,"../../../../src/JSimplex.jl")) || error("wrong JSimplex")
realpath(pathof(MA))==realpath("/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl") || error("wrong MA")
const L=joinpath(@__DIR__,"../MA-L")
for name in ("reference.jl","candidate.jl","test-helpers-reviewed.jl","candidate-trace.jl","fixtures.jl","extra-fixtures-reviewed.jl","tests-reviewed.jl")
    include(joinpath(L,name))
end
const ALL_FIXTURES=vcat(MAL_FIXTURES,MAL_EXTRA_FIXTURES)
# Captures real Test failures without aborting expected RED. No results discarded.
mutable struct Captured <: Test.AbstractTestSet
    description::String
    results::Vector{Any}
end
Captured(s;kwargs...)=Captured(s,Any[])
Test.record(t::Captured,r::Test.Result)=push!(t.results,r)
Test.record(t::Captured,r::Test.AbstractTestSet)=push!(t.results,r)
function Test.finish(t::Captured)
    Test.get_testset_depth()>0 && Test.record(Test.get_testset(),t)
    t
end
function test_records(t::Captured)
    out=Any[]
    for r in t.results
        if r isa Captured
            append!(out,test_records(r))
        else
            push!(out,Dict{String,Any}("type"=>string(nameof(typeof(r))),"expression"=>string(r.orig_expr)))
        end
    end
    out
end
function save_new(path,data)
    ispath(path) && error("output exists")
    open(path,"w") do io;TOML.print(io,data);end
end
@noinline function batch(f,args,reps)
    result=0
    for _ in 1:reps;result+=f(args...);end
    result
end
function timing(f,args,reps)
    t=@timed batch(f,args,reps)
    Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"true_count"=>t.value)
end
function main()
    length(ARGS)==2 || error("process index and output directory required")
    index=parse(Int,ARGS[1]);index in 1:3 || error("index")
    out=ARGS[2];ambient=precision(BigFloat);rnd=rounding(BigFloat)
    raw=Dict{String,Any}("index"=>index,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"costs"=>Any[],"errors"=>String[],"qualification_seconds"=>0.0,"first_calls_seconds"=>0.0,"cost_body_seconds"=>0.0)
    try
        if index==1
            start=time_ns()
            red=@testset Captured "original RED" begin;original_route_red(ALL_FIXTURES);end
            rr=test_records(red)
            save_new(joinpath(out,"red.toml"),Dict("records"=>rr,"seconds"=>(time_ns()-start)/1e9))
            count(r->r["type"]=="Pass",rr)==8 && count(r->r["type"]=="Fail",rr)==2 && length(rr)==10 || error("RED counts")
            all(r["type"]=="Pass" || (r["type"]=="Fail" && r["expression"]=="MAL_TRACE[].scratch == 1") for r in rr) || error("unexpected RED expression")
            green=@testset Captured "candidate GREEN" begin
                selection_boundaries(ALL_FIXTURES);private_leaf_ownership(ALL_FIXTURES)
                exact_bound_decisions(ALL_FIXTURES);fallback_precision(ALL_FIXTURES)
                tail_controls(ALL_FIXTURES);snapshot_negative_control(ALL_FIXTURES)
            end
            gr=test_records(green)
            save_new(joinpath(out,"green.toml"),Dict("records"=>gr,"seconds"=>(time_ns()-start)/1e9))
            length(gr)==3787 && all(r["type"]=="Pass" for r in gr) || error("GREEN failures")
            raw["qualification_seconds"]=(time_ns()-start)/1e9
        end
        cases=[f for f in ALL_FIXTURES if !isempty(f.cost)]
        length(cases)==76 || error("cost count")
        start=time_ns()
        for (ci,f) in enumerate(cases)
            args=make_fixture(f)
            setprecision(BigFloat,f.ambient) do
                fixture_matches(f,args) || error("constructed input mismatch")
                want=endpoint_oracle(args);want==f.expected || error("cost oracle mismatch")
                before=snapshot(args);checks=0
                first=Any[]
                for (side,fun) in (("reference",reference_bounds),("candidate",candidate_bounds))
                    t=time_ns();got=fun(args...);elapsed=(time_ns()-t)/1e9
                    got==want && preserved(before,snapshot(args)) || error("first call mismatch")
                    push!(first,Dict("side"=>side,"seconds"=>elapsed,"result"=>got));checks+=1
                    raw["first_calls_seconds"]+=elapsed
                end
                windows=Any[]
                for pair in 1:10
                    first_reference=iseven(index+ci+pair)
                    order=first_reference ? (("reference",reference_bounds),("candidate",candidate_bounds)) : (("candidate",candidate_bounds),("reference",reference_bounds))
                    for (orderindex,(side,fun)) in enumerate(order)
                        w=timing(fun,args,128)
                        merge!(w,Dict("phase"=>pair<=3 ? "warm" : "measured","pair"=>pair,"order"=>orderindex,"side"=>side))
                        push!(windows,w)
                        w["true_count"]==128*Int(want) && preserved(before,snapshot(args)) || error("window output/input mismatch")
                        checks+=1
                    end
                end
                push!(raw["costs"],Dict("id"=>f.id,"class"=>f.cost,"first"=>first,"windows"=>windows,"preservation_checks"=>checks,"expected"=>want))
            end
            precision(BigFloat)==ambient && rounding(BigFloat)==rnd || error("ambient mismatch")
        end
        raw["cost_body_seconds"]=(time_ns()-start)/1e9
    catch err
        push!(raw["errors"],sprint(showerror,err,catch_backtrace()))
    finally
        raw["ambient_restored"]=precision(BigFloat)==ambient && rounding(BigFloat)==rnd
        raw["trace_cleared"]=isnothing(MAL_TRACE[])
        save_new(joinpath(out,"raw.toml"),raw)
    end
    isempty(raw["errors"]) && length(raw["costs"])==76 && raw["ambient_restored"] && raw["trace_cleared"] || error("qualification incomplete")
    all(w["compile_seconds"]==0 && w["recompile_seconds"]==0 for c in raw["costs"] for w in c["windows"] if w["phase"]=="measured") || error("measured compilation")
    println("MA-M process $index complete: 76 cases, 1520 windows")
end
main()
