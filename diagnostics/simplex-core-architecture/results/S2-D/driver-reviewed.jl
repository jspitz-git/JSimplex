# UNEXECUTED; only a separately accepted immutable numerical allowance may launch.
using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const D=@__DIR__
const C=normpath(joinpath(D,"..","S2-C"))
const OVERLAY=joinpath(D,"overlay")
const OUT=only(ARGS)
mkdir(OUT)
realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src","JSimplex.jl")) || error("wrong loaded package")
include(joinpath(D,"reference-audit.jl"))
function save_raw(name,data)
    path=joinpath(OUT,name)
    ispath(path) && error("output exists")
    open(path,"w") do io
        TOML.print(io,data)
    end
end
function counts(ts)
    c=Test.get_test_counts(ts)
    return Dict("pass"=>c.passes+c.cumulative_passes,"fail"=>c.fails+c.cumulative_fails,
        "error"=>c.errors+c.cumulative_errors,"broken"=>c.broken+c.cumulative_broken)
end
const regression=@testset "S2-D frozen candidate regression" begin
    include(joinpath(C,"candidate-tests.jl"))
end
const regression_counts=counts(regression)
save_raw("regression.toml",Dict("counts"=>regression_counts,
    "children"=>[Dict("name"=>t.description,"counts"=>counts(t)) for t in regression.results if t isa Test.DefaultTestSet],
    "source"=>realpath(pathof(JSimplex)),"candidate_sha256"=>bytes2hex(sha256(read(joinpath(OVERLAY,"src","primal_updates.jl")))),
    "tests_sha256"=>bytes2hex(sha256(read(joinpath(C,"candidate-tests.jl"))))))
regression_counts==Dict("pass"=>655,"fail"=>0,"error"=>0,"broken"=>0) || error("regression counts differ")

bitsdecode(::Type{Float32},s)=reinterpret(Float32,parse(UInt32,s;base=16))
bitsdecode(::Type{Float64},s)=reinterpret(Float64,parse(UInt64,s;base=16))
function audit_window(f,ws,predicted)
    ok=true
    for _ in 1:16
        ok &= f(ws,predicted)
    end
    return ok
end
stats(t)=Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,
    "allocations"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,
    "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"ok"=>t.value)
function cost_fixture(f)
    T=f["scalar"]=="Float32" ? Float32 : Float64
    m,n=f["m"],f["n"]
    A=SparseMatrixCSC{T,Int}(m,n,Int.(f["colptr"]),Int.(f["rowval"]),bitsdecode.(T,f["nzval_bits"]))
    costs=bitsdecode.(T,f["cost_bits"])
    p=LinearProblem(A,costs;row_lower=zeros(T,m),row_upper=ones(T,m))
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false,basis_update=:pfi))
    predicted=copy(ws.reduced_costs)
    @assert ws.basis.basic_indices==collect(n+1:n+m)
    @assert all(iszero,ws.scratch.rho)
    @assert predicted==vcat(costs,zeros(T,m)) && ws.costs==predicted
    @assert bytes2hex(sha256(reinterpret(UInt8,ws.problem.A.nzval)))==f["nzval_sha256"]
    @assert realpath(String(which(JSimplex._primal_price_prediction_reliable,
        Tuple{typeof(ws),typeof(predicted)}).file))==realpath(joinpath(OVERLAY,"src","primal_updates.jl"))
    before=(copy(ws.scratch.rho),copy(predicted),copy(ws.costs),copy(ws.basis.basic_indices))
    samples=Dict{String,Any}[]
    for round in 1:12
        for side in (isodd(round) ? ("reference","candidate") : ("candidate","reference"))
            fn=side=="reference" ? s2d_reference_price_audit : JSimplex._primal_price_prediction_reliable
            GC.gc() # outside timed window on BOTH sides; no subtraction of GC time
            t=@timed audit_window(fn,ws,predicted)
            sample=stats(t);merge!(sample,Dict("fixture"=>f["id"],"round"=>round,
                "side"=>side,"measured"=>round>4,"calls"=>16))
            push!(samples,sample)
        end
    end
    return Dict("fixture"=>f["id"],"samples"=>samples,"inputs_preserved"=>before==(ws.scratch.rho,predicted,ws.costs,ws.basis.basic_indices),
        "m"=>m,"n"=>n,"nnz"=>nnz(A),"input_sha256"=>f["nzval_sha256"])
end
spec=TOML.parsefile(joinpath(D,"fixtures.toml"))
for f in spec["fixtures"]
    # Per-fixture raw is retained before later aggregate acceptance; no retry.
    save_raw(f["id"]*".toml",cost_fixture(f))
end
save_raw("complete.toml",Dict("fixtures"=>8,"windows"=>192,"cost_audits"=>3072,
    "regression_pass"=>655,"loaded_source"=>realpath(pathof(JSimplex)),"completed"=>true))
