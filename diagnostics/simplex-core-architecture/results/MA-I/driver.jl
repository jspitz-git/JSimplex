# UNEXECUTED MA-E driver. All output paths are fixed by sealed config.
using JSimplex, MutableArithmetics, LinearAlgebra, SparseArrays, Test, TOML, SHA
const cfg=TOML.parsefile(ARGS[1])
realpath(pathof(JSimplex))==realpath(joinpath(cfg["root"],"src/JSimplex.jl"))||error("loaded source")
realpath(pathof(MutableArithmetics))==realpath(cfg["ma_source"])||error("MA source")
bytes2hex(sha256(read(joinpath(cfg["root"],"src/markowitz_factorization.jl"))))==cfg["source_sha256"]||error("source hash")
include("kernels.jl")
const fixtures=TOML.parsefile(joinpath(@__DIR__,"fixtures.toml"))
const before_precision=precision(BigFloat)
const before_rounding=rounding(BigFloat)
const started=time_ns()
const raw=Dict{String,Any}("stage"=>cfg["stage"],"side"=>cfg["side"],"source"=>pathof(JSimplex),"version"=>string(VERSION),"records"=>Any[],"errors"=>String[])
function costcase(T,f)
    A,rhs=fixture(T,f);n=length(rhs)
    b,construction=measured(J.MarkowitzBackend,A)
    meta=metadata(b,f,T);initial=seed(b,rhs,f);w=copy(initial);out=zeros(T,n)
    target=cfg["side"]=="candidate" ? J._markowitz_upper_solve! : reference_upper!
    _,cold=measured(full_window!,out,b,rhs,1);first=encoded(out);retained=copy(out)
    _,steady=measured(full_window!,out,b,rhs,4);last=encoded(out)
    retained_ok=encoded(retained)==first
    _,uppercold=measured(upper_window!,target,w,b,initial,1);upperfirst=encoded(w);upperretained=copy(w)
    _,uppersteady=measured(upper_window!,target,w,b,initial,4);upperlast=encoded(w)
    rec=Dict{String,Any}("name"=>f["name"],"metadata"=>meta,"rhs"=>encoded(rhs),"seed"=>encoded(initial),"full_first"=>first,"full_last"=>last,"upper_first"=>upperfirst,"upper_last"=>upperlast,
      "retained_ok"=>retained_ok && encoded(upperretained)==upperfirst,"rhs_preserved"=>Q.(rhs)==qparse.(f["rhs"]),
      "construction"=>construction,"first_full"=>cold,"steady_full"=>steady,"first_upper"=>uppercold,"steady_upper"=>uppersteady,
      "backend_graph_bytes"=>Base.summarysize(b),"scratch_present"=>T in (BigFloat,Q))
    if T in (BigFloat,Q)
        private,t=measured(scratch,T);rec["scratch"]=t;rec["scratch_graph_bytes"]=Base.summarysize(private)
    end
    return rec
end
function qualificationcase(T,f)
    A,rhs=fixture(T,f);b=J.MarkowitzBackend(A);meta=metadata(b,f,T)
    predicted=seed(b,rhs,f);prefix=copy(reference_prefix!(b,rhs));prefix_record=encoded(prefix)
    # Dense-only has no upper rows; its allones reset is a deliberate zero-work control,
    # not a bitwise claim about the rounded dense LU prefix.
    seed_ok=f["family"]!="star" || encoded(predicted)==encoded(prefix)
    trace=Any[]
    for p in b.sparse_pivots:-1:1
        value=prefix[p];row=b.upper[p]
        for k in eachindex(row.indices);value-=row.values[k]*prefix[row.indices[k]];end
        prefix[p]=value/b.diagonal[p];push!(trace,Dict("pivot"=>p,"value"=>encoded(prefix[p:p])))
    end
    expected=similar(rhs)
    for i in eachindex(prefix);expected[b.column_order[i]]=prefix[i];end
    out=similar(rhs);J._backend_forward_solve!(out,b,rhs)
    return Dict("name"=>f["name"],"metadata"=>meta,"seed_ok"=>seed_ok,"prefix"=>prefix_record,"expected"=>encoded(expected),"actual"=>encoded(out),"trace"=>trace)
end
try
    if cfg["stage"] in ("red","qualification")
        include("test-collector.jl")
        ts=RecordedTests("MA-E")
        parent_testset=Test.get_testset()
        parent_depth=Test.get_testset_depth()
        try
            Test.@with_testset ts begin
                Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))
                if cfg["stage"] == "qualification"
                    Base.include(Main,joinpath(@__DIR__,"route-tests-instrumented.jl"))
                end
            end
        finally
            Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth || error("test scope restoration")
            raw["context_restored"]=Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth
            raw["tests"]=snapshot(ts);raw["counts"]=total(ts)
            if isdefined(Main,:MarkowitzMARoutingTests)
                raw["route_entries"]=copy(Main.MarkowitzMARoutingTests.ENTRY)
            end
            if isdefined(Main,:MarkowitzMAUpperTests)
                raw["compare_metrics"]=Main.MarkowitzMAUpperTests.MAE_COMPARE_METRICS
                raw["full_metrics"]=Main.MarkowitzMAUpperTests.MAE_FULL_METRICS
            end
        end
    end
    if cfg["stage"]!="red"
        for f in fixtures["fixtures"],label in fixtures["scalar_cases"]
            r=withscalar(label) do T
                cfg["stage"]=="qualification" ? qualificationcase(T,f) : costcase(T,f)
            end
            r["scalar"]=label;push!(raw["records"],r)
        end
    end
catch e
    push!(raw["errors"],sprint(showerror,e,catch_backtrace()))
end
raw["ambient_ok"]=precision(BigFloat)==before_precision && rounding(BigFloat)==before_rounding
raw["body_seconds"]=(time_ns()-started)/1e9
open(joinpath(cfg["output"],"raw.toml"),"w") do io;TOML.print(io,raw);end
# Test failures are preserved and enforced by the external auditor (RED expected).
exit(isempty(raw["errors"]) && raw["ambient_ok"] ? 0 : 1)
