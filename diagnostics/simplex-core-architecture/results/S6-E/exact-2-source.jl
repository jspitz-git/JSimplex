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
# Counterfactual only: uniquely named copies, no production method overwrite.
const PHASE_SOURCE=read(joinpath(ROOT,"src/simplex_phase_one.jl"),String)
# Top-level documented functions are wrapped in Core.@doc; unwrap that node.
const NODES=map(Meta.parseall(PHASE_SOURCE).args) do ex
    ex isa Expr && ex.head==:macrocall && ex.args[end] isa Expr &&
        ex.args[end].head==:function ? ex.args[end] : ex
end
function function_name(ex)
    ex isa Expr && ex.head==:function || return nothing
    sig=ex.args[1]
    while sig isa Expr && sig.head in (:where, :(::));sig=sig.args[1];end
    sig isa Expr && sig.head==:call ? sig.args[1] : nothing
end
const INNER=deepcopy(only(filter(x->function_name(x)==:_remove_artificials!,NODES)))
const OUTER=deepcopy(only(filter(x->function_name(x)==:remove_artificials!,NODES)))
function rename!(ex)
    ex isa Expr || return ex
    for i in eachindex(ex.args)
        x=ex.args[i]
        ex.args[i]= x===:_remove_artificials! ? :_s6_exact_remove_artificials! :
                    x===:remove_artificials! ? :s6_exact_remove_artificials! :rename!(x)
    end
    ex
end
rename!(INNER);rename!(OUTER)
const INJECTIONS=Ref(0)
function inject!(ex)
    ex isa Expr || return
    for i in eachindex(ex.args)
        x=ex.args[i]
        if x isa Expr && x.head==:call && x.args[1]==:_checked_basis_solve! && :rho in x.args
            ex.args[i]=quote
                $x
                @assert row==1 && length(rho)==6
                rho .= [1.0,1.0,0.0,0.0,0.0,0.0]
                Bprobe=basis_matrix(phase)
                @assert transpose(Bprobe)*rho == unit
                qprobe=solve_quality!(SolveQualityScratch(eltype(rho),length(rho)),
                    Bprobe,rho,unit,policy;transposed=true)
                @assert qprobe.reliable && iszero(qprobe.absolute_error)
            end
            INJECTIONS[]+=1
        else
            inject!(x)
        end
    end
end
inject!(INNER);@assert INJECTIONS[]==1
const CLONE=string(INNER,"\n",OUTER)
@assert !ispath(only(ARGS)*".clone.jl")
write(only(ARGS)*".clone.jl",CLONE)
Core.eval(JS,INNER);Core.eval(JS,OUTER)
# Redirect only this diagnostic oracle's invocation; assertions are unchanged.
function redirect!(ex)
    ex isa Expr || return
    for i in eachindex(ex.args)
        ex.args[i]==:(JSimplex.remove_artificials!) && (ex.args[i]=:(JSimplex.s6_exact_remove_artificials!))
        redirect!(ex.args[i])
    end
end
redirect!(NODE)

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
    result=try JS.s6_exact_remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
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
    rho .= [1.0,1.0,0.0,0.0,0.0,0.0]
    B=JS._basis_matrix!(phase)
    @assert transpose(B)*rho == unit
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
        "counterfactual"=>true,"clone_sha256"=>bytes2hex(sha256(CLONE)),"pairs"=>records))
end
# Existing assertions, with only the removal call redirected to the private clone.
Core.eval(@__MODULE__,NODE)
