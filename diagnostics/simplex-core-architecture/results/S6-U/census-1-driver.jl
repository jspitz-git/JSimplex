using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/legacy_primal_direction_price_tests.jl")
const SOURCE=read(FILE,String)
const TITLE="A repeated price disagreement cannot renew the recovery budget"
const MARKER="@testset \""*TITLE*"\" begin"
const ORIGINAL=MARKER*first(split(split(SOURCE,MARKER;limit=2)[2],"\n@testset";limit=2))
const HELPER="function native_price_roundoff_fixture"*first(split(split(SOURCE,"function native_price_roundoff_fixture";limit=2)[2],"\n@testset";limit=2))
Base.include_string(@__MODULE__,HELPER,FILE)
function snapshot(ws)
    ws isa JS.SimplexWorkspace || return Dict("workspace"=>false,"type"=>string(typeof(ws)))
    Dict("workspace"=>true,"primal"=>copy(ws.primal),"costs"=>copy(ws.costs),
        "prices"=>copy(ws.reduced_costs),"rho"=>copy(ws.scratch.rho),
        "direction"=>copy(ws.scratch.row_solution),
        "states"=>string.(ws.basis.states),"basis"=>copy(ws.basis.basic_indices),
        "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
        "rejected_entering"=>copy(ws.scratch.rejected_entering),
        "selected_row"=>ws.scratch.selected_row,"selected_entering"=>ws.scratch.selected_entering,
        "updates"=>length(ws.factorization.updates))
end
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
const RECORDS=Dict[]
const PRECISION=precision(BigFloat)
const ROUNDING=rounding(BigFloat)
const OBSERVED=replace(ORIGINAL,
    "        diagnostics=JSimplex.SimplexDiagnostics(;observer=" => "        events=Dict[]\n        diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true,observer=",
    "            # Fault injection" => "            push!(events,Dict(\"event\"=>string(event),\"boundary\"=>\"before_original_callback\",\"state\"=>snapshot(ws)))\n            # Fault injection",
    "            event==:primal_prices_corrected && (ws.reduced_costs[7]=-1.0)" => "            event==:primal_prices_corrected && (ws.reduced_costs[7]=-1.0)\n            event==:primal_prices_corrected && push!(events,Dict(\"event\"=>string(event),\"boundary\"=>\"after_original_callback\",\"state\"=>snapshot(ws)))",
    "        result=JSimplex._primal_iteration!" => "        before=snapshot(ws)\n        initial_counts=copy(diagnostics.counts)\n        initial_kernels=copy(diagnostics.kernel_calls)\n        initial_event_count=length(events)\n        result=JSimplex._primal_iteration!",
    "        @test !isnothing(result)" => "        push!(RECORDS,Dict(\"manager\"=>string(manager),\"before\"=>before,\"after\"=>snapshot(ws),\"events\"=>events,\"initial_event_count\"=>initial_event_count,\"options\"=>fields(ws.options),\"policy\"=>fields(ws.progress.numerical_policy),\"A_rows\"=>[collect(ws.problem.A[i,:]) for i in axes(ws.problem.A,1)],\"status\"=>isnothing(result) ? \"nothing\" : string(result.status),\"result_type\"=>string(typeof(result)),\"message\"=>isnothing(result) ? \"nothing\" : result.message,\"counts\"=>Dict(string(k)=>v for (k,v) in diagnostics.counts),\"iteration_counts\"=>Dict(string(k)=>v-initial_counts[k] for (k,v) in diagnostics.counts),\"iteration_kernels\"=>Dict(string(k)=>v-initial_kernels[k] for (k,v) in diagnostics.kernel_calls)))\n        @test !isnothing(result)")
@assert OBSERVED!=ORIGINAL
@assert !ispath(only(ARGS))
try
    Base.include_string(@__MODULE__,OBSERVED,FILE)
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),
            "original_source"=>ORIGINAL,"helper_source"=>HELPER,"observed_source"=>OBSERVED,
            "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
            "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "globals_preserved"=>precision(BigFloat)==PRECISION && rounding(BigFloat)==ROUNDING,
            "records"=>RECORDS))
    end
end
