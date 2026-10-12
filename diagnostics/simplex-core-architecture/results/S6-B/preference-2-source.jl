using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const TESTFILE=joinpath(ROOT,"test/legacy_primal_preference_work_tests.jl")
const TITLE="Exhaustion after fresh pricing retains the refresh budget"
const SOURCE=read(TESTFILE,String)
const NODE=only(filter(x->x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@testset") && TITLE in x.args,Meta.parseall(SOURCE).args))
# Extract the unchanged setup and single iteration; only @test nodes are omitted.
const SETUP=Expr(:block,filter(x->!(x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@test")),NODE.args[end].args)...)
const BODY=filter(x->!(x isa LineNumberNode),SETUP.args)
const TERMINAL=findfirst(x->x isa Expr && x.head==:(=) && x.args[1]==:terminal,BODY)
@assert !isnothing(TERMINAL) && TERMINAL==length(BODY)
@eval function fixture(;observed=false)
    events=String[]
    $(BODY[1:TERMINAL-1]...)
    if observed
        ws.progress=JS.SimplexProgressContext(ws.problem;
            numerical_policy=ws.progress.numerical_policy,
            diagnostics=JS.SimplexDiagnostics(;observer=(event,w)->push!(events,string(event))))
    end
    $(BODY[TERMINAL])
    record=Dict("terminal"=>isnothing(terminal) ? "nothing" : string(terminal.status),
        "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
        "primal"=>copy(ws.primal),"costs"=>copy(ws.costs),
        "prices"=>copy(ws.reduced_costs),"basis"=>copy(ws.basis.basic_indices),
        "states"=>string.(ws.basis.states),"rejected"=>copy(ws.scratch.rejected_entering),
        "events"=>events)
    # These diagnostic probes run after the recorded work/state, not in the iteration.
    record["point_certified"]=JS._legacy_primal_point_certified(ws)
    record["original_feasible"]=JS._original_primal_feasible(ws.problem,
        ws.primal[1:length(ws.problem.objective)],ws.options.primal_tolerance)
    rhs=Vector(ws.problem.A[:,1]);x=similar(rhs)
    JS.forward_solve!(x,ws.factorization,rhs)
    record["post_ftran_residual"]=norm(JS.basis_matrix(ws)*x-rhs,Inf)
    return record
end
control=fixture();observed=fixture(;observed=true)
equal=all(isequal(control[k],observed[k]) for k in keys(control) if k!="events")
@assert equal
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("source"=>pathof(JS),"test_source_sha256"=>bytes2hex(sha256(SOURCE)),
    "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
    "control"=>control,"observed"=>observed,"twin_equal"=>equal))
end
# The exact existing testset is evaluated, with its original failing oracle.
Core.eval(@__MODULE__,NODE)
