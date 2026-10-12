using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const TESTFILE=joinpath(ROOT,"test/native_artificial_row_tests.jl")
const SOURCE=read(TESTFILE,String)
const TITLE="Artificial-row recovery respects budgets and preserves the original on cancellation"
# Load only the unchanged fixture definition. Preserve the original oracle node.
Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),TESTFILE)
const NODE=only(filter(x->x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@testset") && TITLE in x.args,Meta.parseall(SOURCE).args))
function snapshot(ws)
    Dict("basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),
      "primal"=>copy(ws.primal),"costs"=>copy(ws.costs),"prices"=>copy(ws.reduced_costs),
      "lower"=>string.(ws.lower),"upper"=>string.(ws.upper),
      "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations)
end
function observe(manager,mode;record_events=false)
    correcting=Ref(false);events=String[]
    # Both twins retain the original behavior-driving observer. Only passive
    # event recording differs; cancellation/exception semantics must be identical.
    diagnostics=JS.SimplexDiagnostics(;observer=(event,ws)->begin
        event==:correction_attempt && (correcting[]=true)
        record_events && push!(events,string(event))
    end)
    phase,mapping,original,policy=artificial_row_roundoff_fixture(Float64,manager;
        diagnostics,infeasible_original=mode==:point,max_refinements=mode==:budget ? 0 : 3,
        pivot_validation=mode==:checked,
        pivot_error_tolerance=mode==:pivot ? eps(Float64)^2 : sqrt(eps(Float64)))
    mode==:dual && (phase.options=JS._phase_options(phase.options,:dual))
    before=snapshot(original)
    failure=SingularException(927)
    stop=()->begin
        correcting[] && mode==:exception && throw(failure)
        correcting[] && mode==:cancel
    end
    result=try JS.remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
    after=snapshot(original)
    record=Dict("manager"=>string(manager),"mode"=>string(mode),
        "result"=>string(result),"same_callback_exception"=>result===failure,
        "correcting"=>correcting[],"before"=>before,"original"=>after,
        "phase"=>snapshot(phase),"events"=>events,
        "artificial_removed"=>JS.event_count(diagnostics,:artificial_removed),
        "numerical_state_unchanged"=>all(isequal(before[k],after[k]) for k in
             ("basis","states","primal","costs","prices","lower","upper")))
    # Post-state feasibility probe only; it cannot influence the recorded attempt.
    record["original_feasible"]=JS._original_primal_feasible(original,original.primal[1:6])
    return record
end
function initial_row_probe(manager,mode)
    # Independent fresh fixture, after both twins. Never modifies either attempt.
    phase,map,original,policy=artificial_row_roundoff_fixture(Float64,manager;
        infeasible_original=mode==:point,max_refinements=mode==:budget ? 0 : 3,
        pivot_validation=mode==:checked,
        pivot_error_tolerance=mode==:pivot ? eps(Float64)^2 : sqrt(eps(Float64)))
    mode==:dual && (phase.options=JS._phase_options(phase.options,:dual))
    unit=zeros(6);unit[1]=1;rho=zeros(6)
    JS._checked_basis_solve!(rho,phase,unit,()->false;transposed=true)
    B=JS._basis_matrix!(phase)
    q=JS.solve_quality!(JS._pivot_quality_buffers(phase).row,B,rho,unit,policy;transposed=true)
    Dict("rho"=>rho,"absolute_error"=>q.absolute_error,
        "relative_error"=>isnothing(q.relative_error) ? "nothing" : string(q.relative_error),
        "finite"=>q.finite,"reliable"=>q.reliable,
        "native_enabled"=>JS._native_phase_transfer_enabled(phase),
        "max_refinements"=>policy.max_refinements)
end
records=Dict[]
for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
    mode in (:budget,:checked,:dual,:cancel,:exception,:pivot,:point)
    control=observe(manager,mode)
    observed=observe(manager,mode;record_events=true)
    equal=all(isequal(control[k],observed[k]) for k in keys(control) if k!="events")
    @assert equal
    push!(records,Dict("control"=>control,"observed"=>observed,"equal"=>equal,
        "initial_row_probe"=>initial_row_probe(manager,mode)))
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
    TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),
        "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "pairs"=>records))
end
# Exact existing named oracle, without any AST mutation or softened assertion.
Core.eval(@__MODULE__,NODE)
